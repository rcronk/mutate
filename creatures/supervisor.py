""" supervisor.py - forks creatures as real processes and runs the world.

Each creature is one forked process that lives its whole life, blocking briefly
each tick to be asked for a decision. One fork per creature, not per tick.

Reruns are deliberately not byte-identical: OS scheduling is nondeterministic
and the order creatures reach the food pool varies. Genetics are reproducible
(see genome.py), timing is not.

Forking is what makes a mutant survivable. A creature that crashes takes down
its own process and nothing else, and a creature that hangs can be killed. Both
are inevitable once source is being mutated, and neither is recoverable if
creatures run in the supervisor's own process.

The concurrency cap is a safety valve for the machine, not a rule of the world.
Food is the limiter (see test_ecology.py). If the cap is ever hit in a real
run, the food parameters were wrong and the results are contaminated by an
artificial ceiling, so it is counted and reported rather than passed over.
"""

import json
import os
import select
import signal
import socket
import sys

from creatures import genome, lifecycle

# How long a creature gets to answer before it is assumed hung. Generous by CPU
# standards: deciding is a single function call, so anything slower is looping.
DEFAULT_TIMEOUT = 0.5

# Safety valve only. Set well above the population the food supply can sustain.
DEFAULT_MAX_PROCESSES = 500

# Chance that a given offspring is mutated at all. Mutating every offspring is
# a rate of one mutation per genome per generation, which is far past the error
# threshold for this substrate: see the sweep recorded in the PR for #26.
DEFAULT_MUTATION_PROBABILITY = 0.1

CAUSES = ('starvation', 'old_age', 'crashed', 'timeout')


class Creature:  # pylint: disable=too-few-public-methods
    """ One living creature: its process, its pipe, and its engine state.

        A record binding a pid to a genome and its engine state; the behaviour
        lives on Supervisor, which owns every creature.
    """

    def __init__(self, pid, channel, gene, life, birth_index=0):
        self.pid = pid
        self.channel = channel
        self.gene = gene
        self.life = life
        self.births = birth_index

    def close(self):
        """ Closes this creature's end of the pipe. """
        try:
            self.channel.close()
        except OSError:
            pass


def _child_loop(channel, source):
    """ Runs inside the forked process for the whole of a creature's life.

        Reads one request per tick, answers with a decision, and exits when the
        supervisor closes the pipe or says to die. Any failure is reported as an
        error reply rather than a traceback, so the supervisor can record a
        cause of death instead of guessing from an exit code.
    :param channel: Socket to the supervisor
    :param source: This creature's genome source
    :return: Never; always exits the process
    """
    reader = channel.makefile('r')
    writer = channel.makefile('w')
    try:
        for line in reader:
            request = json.loads(line)
            if request.get('cmd') == 'die':
                break
            try:
                reply = genome.decide(source,
                                      age=request['age'],
                                      fuel=request['fuel'],
                                      max_fuel=request['max_fuel'],
                                      food_available=request['food_available'],
                                      population=request['population'])
            except genome.MisbehavingCreatureError as error:
                reply = {'error': str(error)}
            writer.write(json.dumps(reply) + '\n')
            writer.flush()
    except (OSError, ValueError):
        pass
    finally:
        os._exit(0)  # pylint: disable=protected-access


class Supervisor:  # pylint: disable=too-many-instance-attributes
    """ Owns the world, the population, and every creature process.

        The attribute count reflects how many independent things a run tracks:
        world parameters, the population, and four separate tallies.
    """

    # Nine world parameters, all of which an experiment legitimately varies.
    def __init__(self, *, regrowth=200, food=None,  # pylint: disable=too-many-arguments
                 max_processes=DEFAULT_MAX_PROCESSES,
                 timeout=DEFAULT_TIMEOUT, max_age=lifecycle.DEFAULT_MAX_AGE,
                 max_fuel=lifecycle.DEFAULT_MAX_FUEL,
                 starting_fuel=lifecycle.DEFAULT_FUEL,
                 reproduction_cost=lifecycle.DEFAULT_REPRODUCTION_COST,
                 mutation_probability=DEFAULT_MUTATION_PROBABILITY, log=None):
        self.world = lifecycle.World(
            food=regrowth * 5 if food is None else food, regrowth=regrowth)
        self.max_processes = max_processes
        self.timeout = timeout
        self.max_age = max_age
        self.max_fuel = max_fuel
        self.starting_fuel = starting_fuel
        self.reproduction_cost = reproduction_cost
        self.mutation_probability = mutation_probability

        # Optional EventLog. Forked runs cannot be replayed by re-running, so
        # what happened is written down as it happens.
        self.log = log
        self.living = []
        self.deaths = dict.fromkeys(CAUSES, 0)
        self.births = 0
        self.cap_hits = 0
        self.ticks = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.shutdown()
        return False

    def _new_life(self, starting_fuel=None):
        return lifecycle.Lifecycle(
            fuel=self.starting_fuel if starting_fuel is None else starting_fuel,
            max_fuel=self.max_fuel, max_age=self.max_age,
            reproduction_cost=self.reproduction_cost)

    def spawn(self, gene, starting_fuel=None):
        """ Forks a new creature process.
        :param gene: The Genome the creature will run
        :param starting_fuel: Fuel the creature begins with. None means the
            world default; a newborn instead starts with what its parent endowed
            it, which can be nothing.
        :return: The Creature, already added to the living population
        """
        parent_end, child_end = socket.socketpair()
        pid = os.fork()
        if pid == 0:
            parent_end.close()
            _child_loop(child_end, gene.source)
        child_end.close()
        creature = Creature(pid, parent_end, gene, self._new_life(starting_fuel))
        self.living.append(creature)
        if self.log is not None:
            parent = gene.identity.rsplit('.', 1)[0] if '.' in gene.identity else None
            self.log.birth(tick=self.ticks, identity=gene.identity,
                           generation=gene.generation, parent=parent)
        return creature

    def start(self, founders, seed):
        """ Spawns the founding population.
        :param founders: How many founders to create
        :param seed: Founder seed; each founder gets seed + its index
        :return: None
        """
        # Founder seeds are derived, not seed + index. Adding the index made
        # consecutive run seeds share almost all their founders: seeds 1 and 2
        # differed in one founder out of twenty, so different runs produced
        # near-identical results.
        for index in range(founders):
            self.spawn(genome.Genome.founder(seed=genome.derive_seed(seed, index),
                                             identity=str(index)))

    # Seven ways a creature can fail to answer usefully, each needing its own
    # early exit. Collapsing them would only hide which one happened.
    def ask(self, creature):  # pylint: disable=too-many-return-statements
        """ Asks one creature for its decision, enforcing the timeout.
        :param creature: The Creature to ask
        :return: A decision dict, or None if it crashed, hung or went silent
        """
        request = json.dumps({'cmd': 'tick',
                              'age': creature.life.age,
                              'fuel': creature.life.fuel,
                              'max_fuel': creature.life.max_fuel,
                              'food_available': self.world.food,
                              'population': len(self.living)}) + '\n'
        try:
            creature.channel.sendall(request.encode('utf-8'))
        except OSError:
            return None

        # poll() rather than select(): select() is limited to FD_SETSIZE (1024)
        # file descriptors and raises "filedescriptor out of range" once the
        # population grows past it. Each living creature holds a socket, so that
        # ceiling is reachable in a normal run.
        poller = select.poll()
        poller.register(creature.channel, select.POLLIN)
        if not poller.poll(self.timeout * 1000):
            return 'timeout'
        try:
            raw = creature.channel.recv(65536)
        except OSError:
            return None
        if not raw:
            return None
        try:
            reply = json.loads(raw.decode('utf-8').splitlines()[0])
        except (ValueError, IndexError):
            return None
        if 'error' in reply:
            return None
        return reply

    def _kill(self, creature, cause):
        """ Ends a creature: records the cause, kills the process, reaps it. """
        self.deaths[cause] += 1
        if self.log is not None:
            self.log.death(tick=self.ticks, identity=creature.gene.identity,
                           cause=cause, age=creature.life.age,
                           generation=creature.gene.generation)
        creature.close()
        try:
            os.kill(creature.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(creature.pid, 0)
        except ChildProcessError:
            pass

    def tick(self):
        """ Advances the world one tick.

            Food regrows, then every creature is asked in turn what it wants.
            Creatures are served in the order they are asked, so a creature can
            go hungry because others reached the pool first.
        :return: None
        """
        self.ticks += 1
        self.world.tick()
        newborns = []
        decisions = []

        for creature in list(self.living):
            decision = self.ask(creature)
            if decision == 'timeout':
                self.living.remove(creature)
                self._kill(creature, 'timeout')
                continue
            if decision is None:
                self.living.remove(creature)
                self._kill(creature, 'crashed')
                continue

            decisions.append(decision)
            creature.life.eat(self.world.request(decision['eat']))
            if decision['reproduce'] and creature.life.can_reproduce:
                # Newborns are not spawned until the end of the tick, so they
                # must be counted against the cap here or several births in one
                # tick can each pass the check and collectively overshoot it.
                newborns.append(self._breed(creature, decision['endowment'],
                                            pending=len(newborns)))
            creature.life.tick()
            if not creature.life.alive:
                self.living.remove(creature)
                self._kill(creature, creature.life.cause_of_death)

        for gene, endowment in filter(None, newborns):
            self.spawn(gene, starting_fuel=endowment)

        if self.log is not None:
            self.log.snapshot(tick=self.ticks, population=len(self.living),
                              food=self.world.food,
                              strategy=self._strategy(decisions))

    def _strategy(self, decisions):
        """ Summarises what the population wanted and what it is made of.

            Two kinds of measurement, deliberately separated. The realised means
            (eat, breed rate, endowment) mix genetic change with demography: a
            shifting age distribution changes which decisions get made even if no
            gene changes. The genetic divergence, the fraction of living
            creatures that are no longer the unmutated ancestor, is a cleaner
            signal of actual evolution, since it does not depend on age.
        :param decisions: The decision dicts collected this tick
        :return: A strategy dict, or None if nobody is alive
        """
        if not decisions and not self.living:
            return None
        summary = {
            'genetic_divergence': (
                sum(1 for c in self.living if c.gene.source != genome.ANCESTOR_SOURCE)
                / len(self.living)) if self.living else 0.0,
        }
        if decisions:
            count = len(decisions)
            summary.update(
                mean_eat=sum(d['eat'] for d in decisions) / count,
                breed_rate=sum(1 for d in decisions if d['reproduce']) / count,
                mean_endowment=sum(d['endowment'] for d in decisions) / count)
        return summary

    def _breed(self, creature, endowment, pending):
        """ Attempts one birth, respecting the process cap.

            The parent pays two things: the flat reproduction cost, which gates
            fertility, and the endowment it chose to transfer to the child. The
            endowment is limited to what the parent has left after the flat cost,
            since a creature cannot give away fuel it does not have. The child
            starts with exactly that endowment, which may be zero.
        :param creature: The parent
        :param endowment: Fuel the parent wants to give the child
        :param pending: Births already agreed this tick but not yet spawned
        :return: (child Genome, fuel the child starts with), or None if the
            birth failed or was capped
        """
        if len(self.living) + pending >= self.max_processes:
            self.cap_hits += 1
            if self.log is not None:
                self.log.birth_failed(tick=self.ticks,
                                      parent=creature.gene.identity, reason='capped')
            return None
        child = creature.gene.child(birth_index=creature.births,
                                    mutation_probability=self.mutation_probability)
        creature.births += 1
        creature.life.pay_for_reproduction()
        if child is None:
            if self.log is not None:
                self.log.birth_failed(tick=self.ticks,
                                      parent=creature.gene.identity,
                                      reason='unparseable')
            return None
        affordable = max(0, min(endowment, creature.life.fuel))
        creature.life.fuel -= affordable
        self.births += 1
        return child, affordable

    def shutdown(self):
        """ Kills and reaps every remaining creature. Safe to call twice.
        :return: None
        """
        for creature in self.living:
            creature.close()
            try:
                os.kill(creature.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
        for creature in self.living:
            try:
                os.waitpid(creature.pid, 0)
            except (ChildProcessError, OSError):
                pass
        self.living = []

    def summary(self):
        """ :return: A dict describing how the run went """
        return {'ticks': self.ticks, 'living': len(self.living),
                'births': self.births, 'deaths': dict(self.deaths),
                'cap_hits': self.cap_hits, 'food': self.world.food}


def main(arguments):
    """ Entry point for the command line. """
    import argparse  # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser(description='Run a population of forked creatures.')
    parser.add_argument('--ticks', type=int, default=50)
    parser.add_argument('--founders', type=int, default=10)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--regrowth', type=int, default=400)
    parser.add_argument('--max-processes', type=int, default=DEFAULT_MAX_PROCESSES)
    args = parser.parse_args(arguments)

    with Supervisor(regrowth=args.regrowth, max_processes=args.max_processes) as sup:
        sup.start(founders=args.founders, seed=args.seed)
        for tick in range(args.ticks):
            sup.tick()
            print(f'tick {tick:4}  living {len(sup.living):4}  food {sup.world.food:6}')
            if not sup.living:
                print('extinct')
                break
        print(sup.summary())
        if sup.cap_hits:
            print(f'WARNING: process cap hit {sup.cap_hits} times. Food parameters '
                  f'were wrong and these results are capped by an artificial ceiling.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
