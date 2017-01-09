""" mutate.py - a mutation algorithm. """

from __future__ import print_function

import argparse
import os
import random
import string
import subprocess
import time
import sys


class SelfReplicator(object):
    """ This is a creature that can duplicate itself with errors. """
    maximum_age = 100               # Die of old age
    start_reproducing = 20      # Can reproduce starting at this age
    stop_reproducing = 40       # Stop reproducing at this age
    reproduction_chance = 0.25  # Each year, we have this chance to have offspring
    minimum_energy = 0          # If our energy gets below this, we die
    hunger_energy = 5           # If our energy is below this, we're hungry and will search for food
    maximum_energy = 10         # If our energy is at this level, we cannot eat more

    def __init__(self, identity):
        self._identity = identity
        self._age = 0
        self._energy = SelfReplicator.maximum_energy
        self._alive = True
        self.offspring_count = 0

    def live(self, time_to_live):
        """
        :param time_to_live: The number of units of time to live for.
        :return: None
        """
        for _ in range(time_to_live):
            if self.alive:
                self._age += 1
                self._energy -= 1
                print('I am %d years old.' % self._age)
                if self._age >= SelfReplicator.maximum_age:
                    self.die('old_age')
                elif self._energy <= SelfReplicator.minimum_energy:
                    self.die('hunger')
                elif self.is_hungry:
                    print('I am hungry: %d' % self.energy)
                    self.eat()
                elif self.can_reproduce:  # If hungry, won't reproduce
                    if random.random() > SelfReplicator.reproduction_chance:
                        self.reproduce()
                elif self.is_hungry:
                    # try to eat, maybe get food, maybe not
                    pass
            else:
                print('I am dead.')
                return

    def reproduce(self):
        print('I will reproduce here.')
        our_basename, our_extension = os.path.splitext(__file__)
        child_name = '%s.%d%s' % (our_basename, self.offspring_count, our_extension)
        child = open(child_name, 'w')
        with open(__file__) as original:
            data = original.read(1)
            child.write(data)
        self.offspring_count += 1
        # Make the flawed copy here
        # Run pylint against the copy before spawning it (or just let it spawn?)
        # Spawn the flawed copy here

    def die(self, reason):
        """
        :param reason: The reason for the death (hunger, old age)
        :return: None
        """
        self._alive = False
        print('dying because of %s' % reason)
        # Communicate with mutate.py here
        # sys.exit(0) # if not in a unit test

    @property
    def filename(self):
        """
        :return: The filename of this creature
        """
        return __file__

    @property
    def identity(self):
        """
        :return: UUID of this creature
        """
        return self._identity

    @property
    def age(self):
        """
        :return: Age of creature
        """
        return self._age

    @property
    def energy(self):
        """
        :return: Energy (amount of food in stomach, hunger)
        """
        return self._energy

    @energy.setter
    def energy(self, value):
        """
        :param value: Set the energy to this value
        :return: None
        """
        self._energy = value

    @property
    def generation(self):
        """
        :return: How many generations since first creature
        """
        return len(self._identity.split('.'))

    @property
    def can_reproduce(self):
        """
        :return: True if we can reproduce right now
        """
        return SelfReplicator.start_reproducing <= self.age <= SelfReplicator.stop_reproducing

    @property
    def is_hungry(self):
        """
        :return: True if hungry (energy is low)
        """
        return self.energy < SelfReplicator.hunger_energy

    def eat(self):
        """
        :return: Causes creature to eat, increasig energy, reducing shared food supply
        """
        # Later on, we'll get food from a shared scarce resource, this is just a stub
        if random.random() > 0.5:
            self.energy += 3

    @property
    def alive(self):
        """
        :return: True if alive
        """
        return self._alive

    @staticmethod
    def _weighted_choice(choices):
        """ Picks a choice at random but with weight
            choices: list of tuples in the form (choice, weight)
            choice:  list
            weight:  any integer that represents a weight for this choice
        """
        total = sum(w for c, w in choices)
        rand_num = random.uniform(0, total)
        upto = 0
        for choice, weight in choices:
            if upto + weight >= rand_num:
                return choice
            upto += weight

    @staticmethod
    def _flawed_copy(source, mutation_weights=None, use_keywords=True):
        """ Copies source and returns it with flaws according to the weighted
            flaws passed in.
            source : list of characters
        """
        if mutation_weights is None:
            mutation_weights = {'prepend':25, 'overwrite':25, 'insert':25, 'append':25}

        defect = SelfReplicator._weighted_choice([('prepend', mutation_weights['prepend']),
                                                  ('overwrite', mutation_weights['overwrite']),
                                                  ('insert', mutation_weights['insert']),
                                                  ('append', mutation_weights['append'])])

        if use_keywords:
            python_keywords = [' and ', ' del ', ' from ', ' not ', ' while ', ' as ', ' elif ',
                               ' global ', ' or ', ' with ', ' assert ', ' else ', ' if ',
                               ' pass ', ' yield ', ' break ', ' except ', ' import ', ' print ',
                               ' class ', ' exec ', ' in ', ' raise ', ' continue ', ' finally ',
                               ' is ', ' return ', ' def ', ' for ', ' lambda ', ' try ']
        else:
            python_keywords = []

        mutation = random.choice(list(string.ascii_letters) +
                                 list(string.digits) +
                                 python_keywords +
                                 list('\n:=%%'))

        if len(source) == 0:
            source = mutation
        else:
            if defect == 'prepend':
                source = mutation + source
            elif defect == 'append':
                source = source + mutation
            elif defect in ('overwrite', 'insert'):
                mutation_location = random.randint(0, len(source) - 1)
                if defect == 'overwrite':
                    source = source[:mutation_location] + mutation + source[mutation_location + 1:]
                else:
                    source = source[:mutation_location] + mutation + source[mutation_location:]
            else:
                raise 'Invalid defect: %s' % defect
        return source

    def mutate(self, mutations, use_keywords):
        """ mutate - mutates something mutations times
        :param mutations: times to mutate
        :param no_environment: Skip unit tests even if present
        :param use_keywords: Use python keywords as mutations or not
        :return: None
        """
        successful_mutations = 0
        failed_mutations = 0

        cmd = self.filename

#        self.save_mutant(self.creature_content)

        for i in range(mutations):
            print('Iteration: %d' % i)
#            mutated_content = self._flawed_copy(self.creature_content, use_keywords=use_keywords)
            print('===== new mutant =====')
            print(mutated_content)
            print('===== new =====')
#            self.save_mutant(mutated_content)

            if subprocess.call(['python', cmd]) == 0:
                successful_mutations += 1
#                self.creature_content = mutated_content
                print('===== succeeded - new creature =====')
                print(self.creature_content)
                print('===== succeeded =====')
            else:
                failed_mutations += 1
                print('===== failed - reverting to this =====')
                print(self.creature_content)
                print('===== failed =====')
                self.save_mutant(self.creature_content)
                print('===== testing reverted creature =====')

        self.save_mutant(self.creature_content)

        print('Successful mutations: %d' % successful_mutations)
        print('Failed mutations: %d' % failed_mutations)


def main(arguments):
    """ Entry point for command line. """
    major = 0
    minor = 0
    micro = 2
    print('self_mutator %d.%d.%d' % (major, minor, micro))
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="Unique identifier for this creature (x.y.z...)", type=str)
    parser.add_argument("--seed", help="Random seed", type=float, default=time.time())
    args = parser.parse_args(arguments)

    print('args: %s' % args)
    random.seed(args.seed)

    creature = SelfReplicator(args.id)
    creature.live(SelfReplicator.maximum_age)


if __name__ == "__main__":
    main(sys.argv[1:])
