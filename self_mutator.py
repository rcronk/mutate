""" mutate.py - a mutation algorithm. """

from __future__ import print_function

import argparse
import os
import random
import string
import subprocess
import time
import sys


class Creature(object):
    """ This is a creature that can duplicate itself with errors. """
    def __init__(self, identity):
        self._identity = identity
        self._age = 0
        self._fuel = 10
        self._alive = True

    def live(self, time):
        self._age += time
        self._fuel -= time
        if self._age >= 10:
            self.die('old_age')
        elif self._fuel <= 0:
            self.die('hunger')

    def die(self, reason):
        self._alive = False
        os.rename(self.filename, '%s.%s' % (self.filename, reason))
        print('dying because of %s' % reason)
        sys.exit(0)

    @property
    def filename(self):
        return __file__

    @property
    def identity(self):
        return self._identity

    @property
    def age(self):
        return self._age

    @property
    def fuel(self):
        return self._fuel

    @property
    def generation(self):
        return len(self._identity.split('.'))

    @property
    def can_reproduce(self):
        return 2 <= self.age <= 5

    @property
    def alive(self):
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

        defect = Creature._weighted_choice([('prepend', mutation_weights['prepend']),
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

    def save_mutant(self, creature_content):
        """ save_mutant: Saves new mutant content to file.
        :param creature_content: Text of file to be saved.
        :return: None
        """
        mutant_path_handle = open(self.mutant_path, 'w')
        mutant_path_handle.write(creature_content)
        mutant_path_handle.close()
        pyc_file = '__pycache__\\%s.cpython-35.pyc' % os.path.splitext(self.mutant_path)[0]
        if os.path.exists(pyc_file):
            os.unlink(pyc_file)

    def mutate(self, mutations, no_environment, use_keywords):
        """ mutate - mutates something mutations times
        :param mutations: times to mutate
        :param no_environment: Skip unit tests even if present
        :param use_keywords: Use python keywords as mutations or not
        :return: None
        """
        successful_mutations = 0
        failed_mutations = 0

        if not os.path.exists(self.test_path):
            no_environment = True

        if no_environment:
            cmd = self.mutant_path
        else:
            cmd = self.test_path

        self.save_mutant(self.creature_content)

        for i in range(mutations):
            print('Iteration: %d' % i)
            mutated_content = self._flawed_copy(self.creature_content, use_keywords=use_keywords)
            print('===== new mutant =====')
            print(mutated_content)
            print('===== new =====')
            self.save_mutant(mutated_content)

            if subprocess.call(['python', cmd]) == 0:
                successful_mutations += 1
                self.creature_content = mutated_content
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
    print('mutate %d.%d.%d' % (major, minor, micro))
    parser = argparse.ArgumentParser()
    parser.add_argument("mutations", help="Number of mutations", type=int)
    parser.add_argument("--seed", help="Random seed", type=float, default=time.time())
    parser.add_argument("--no-environment", help="Don't use the creature's environment.",
                        action="store_true")
    parser.add_argument("--no-keywords", help="Don't use python keywords as mutations.",
                        action="store_false")
    args = parser.parse_args(arguments)

    print('args: %s' % args)
    random.seed(args.seed)
    print('git: %s' % subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8'))
    if subprocess.call(['git', 'diff-index', '--quiet', 'HEAD', '--']) != 0:
        print('git detects uncommitted changes on top of the above id.')
        print('diff:')
        print(subprocess.check_output(['git', 'diff']).strip().decode('utf-8'))

    creature = Creature(args.creature)
    creature.mutate(args.mutations, args.no_environment, args.no_keywords)


if __name__ == "__main__":
    main(sys.argv[1:])
