""" events.py - the record of what happened in a run.

Forked runs cannot be reproduced byte for byte: OS scheduling decides which
creature reaches the food pool first, so rerunning the same seed gives a
similar run, not the same one. Genetics are reproducible (see genome.py);
timing is not.

So rather than re-running to find out what happened, every run writes down what
happened as it goes. The log is append-only JSON lines, one event per line,
which survives a run being killed halfway through and can be read back without
spawning a single process.

That matters twice: analysis stops depending on luck, and phase 4 can animate a
run from its log rather than by re-running it.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


class EventLog:
    """ Append-only writer for one run's events. """

    def __init__(self, path):
        self.path = path
        self._handle = None

    def __enter__(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._handle = open(self.path, 'a', encoding='utf-8')  # pylint: disable=consider-using-with
        return self

    def __exit__(self, *_):
        self.close()
        return False

    def close(self):
        """ Closes the log. Safe to call more than once. """
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def _write(self, kind, tick, **fields):
        record = {'kind': kind, 'tick': tick}
        record.update(fields)
        self._handle.write(json.dumps(record, sort_keys=True) + '\n')
        self._handle.flush()

    def birth(self, *, tick, identity, generation, parent):
        """ Records a creature being born. """
        self._write('birth', tick, identity=identity, generation=generation,
                    parent=parent)

    def death(self, *, tick, identity, cause, age, generation):
        """ Records a creature dying, and why. """
        self._write('death', tick, identity=identity, cause=cause, age=age,
                    generation=generation)

    def birth_failed(self, *, tick, parent, reason):
        """ Records a birth that produced nothing.

            'unparseable' means the mutant could not be parsed, which is the
            measurement of how brittle the substrate is. 'capped' means the
            process ceiling was hit, which means the food parameters were wrong.
        """
        self._write('birth_failed', tick, parent=parent, reason=reason)

    def snapshot(self, *, tick, population, food, strategy=None):
        """ Records aggregate world state at the end of a tick.
        :param strategy: Optional dict of the living population's mean realised
            decision (mean_eat, breed_rate, mean_endowment), or None when nobody
            is alive to have a strategy. This is how we tell a population that
            evolves from one that merely persists.
        """
        self._write('snapshot', tick, population=population, food=food,
                    strategy=strategy)


def read(path):
    """ Reads a log back.

        A run killed mid-write leaves a truncated final line. That line is
        skipped rather than treated as fatal, so an interrupted run is still
        analysable.
    :param path: Path to an events.jsonl
    :return: List of event dicts
    """
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    return records


class Replay:
    """ Reconstructs a run from its log, without running anything. """

    def __init__(self, path):
        self.events = read(path)

    @property
    def population_over_time(self):
        """ :return: Population at the end of each tick """
        return [e['population'] for e in self.events if e['kind'] == 'snapshot']

    @property
    def food_over_time(self):
        """ :return: Food in the pool at the end of each tick """
        return [e['food'] for e in self.events if e['kind'] == 'snapshot']

    @property
    def strategy_over_time(self):
        """ The living population's mean realised strategy at each tick that had
            one. Skips ticks where nobody was alive.
        :return: List of strategy dicts in tick order
        """
        return [e['strategy'] for e in self.events
                if e['kind'] == 'snapshot' and e.get('strategy') is not None]

    @property
    def strategy_drift(self):
        """ How far the population's strategy moved from its first recorded value
            to its last. A population that only persists shows near-zero drift; a
            population that evolves shows the strategy shifting.
        :return: Per-field change (last minus first), or an empty dict if there
            is not enough data
        """
        history = self.strategy_over_time
        if len(history) < 2:
            return {}
        first, last = history[0], history[-1]
        return {key: last[key] - first[key] for key in first if key in last}

    @property
    def births(self):
        """ :return: How many creatures were born """
        return sum(1 for e in self.events if e['kind'] == 'birth')

    @property
    def failed_births(self):
        """ :return: How many births produced nothing """
        return sum(1 for e in self.events if e['kind'] == 'birth_failed')

    @property
    def birth_failure_rate(self):
        """ How often a birth produced nothing. With 'unparseable' as the usual
            reason, this is the substrate's brittleness measured in situ.
        :return: Failed births as a proportion of all attempts, or 0.0
        """
        attempts = self.births + self.failed_births
        return self.failed_births / attempts if attempts else 0.0

    @property
    def deaths(self):
        """ :return: Count of deaths by cause """
        counts = {}
        for event in self.events:
            if event['kind'] == 'death':
                counts[event['cause']] = counts.get(event['cause'], 0) + 1
        return counts

    @property
    def deepest_generation(self):
        """ :return: The furthest any lineage got from the founders """
        return max((e['generation'] for e in self.events
                    if e['kind'] in ('birth', 'death')), default=0)

    def living_at(self, tick):
        """ Who was alive at the end of a given tick.

            Phase 4 needs this to draw a frame without re-running the
            simulation.
        :param tick: The tick of interest
        :return: Set of creature identities
        """
        living = set()
        for event in self.events:
            if event['tick'] > tick:
                break
            if event['kind'] == 'birth':
                living.add(event['identity'])
            elif event['kind'] == 'death':
                living.discard(event['identity'])
        return living


def _git_sha():
    """ :return: Current commit SHA, or None outside a git checkout """
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=HERE,
            stderr=subprocess.DEVNULL).strip().decode('utf-8')
    except (subprocess.CalledProcessError, OSError):
        return None


# Seven run parameters plus the summary, all of which belong in the record.
def write_manifest(path, *, seed, ticks, founders,  # pylint: disable=too-many-arguments
                   regrowth, max_processes, timeout, summary):
    """ Records everything needed to set a run up again.
    :param path: Where to write manifest.json
    :param seed: Founder seed
    :param ticks: How many ticks were requested
    :param founders: Starting population
    :param regrowth: Food added per tick
    :param max_processes: The safety cap
    :param timeout: Seconds a creature gets to answer
    :param summary: Outcome counters from the run
    :return: The manifest dict that was written
    """
    manifest = {
        'seed': seed,
        'ticks': ticks,
        'founders': founders,
        'regrowth': regrowth,
        'max_processes': max_processes,
        'timeout': timeout,
        'git_sha': _git_sha(),
        'python_version': sys.version.split()[0],
        'summary': summary,
        'reproducibility': (
            'Genetics are reproducible: the same seed always produces the same '
            'genomes. Timing is not, because OS scheduling decides which '
            'creature reaches the food pool first. Rerunning these parameters '
            'gives a statistically similar run, not an identical one. Use '
            'events.jsonl for what actually happened.'),
    }
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write('\n')
    return manifest


def read_manifest(path):
    """ Reads a manifest back.
    :param path: Path to manifest.json
    :return: The manifest dict
    """
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)
