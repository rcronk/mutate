""" mutate.py - a mutation algorithm. """

from __future__ import print_function

import argparse
import os
import random
import string
import subprocess
import time
import zipfile


class Creature(object):
    """ This is a creature that can duplicate itself with errors. """
    def __init__(self, path_to_creature):
        assert os.path.sep not in path_to_creature
        self.path_to_creature = path_to_creature
        self.test_path = 'test_%s' % self.path_to_creature
        self.mutant_path = 'mutated_%s' % self.path_to_creature

        creature_file = open(self.path_to_creature)
        self.creature_content = creature_file.read()
        creature_file.close()

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
                if subprocess.call(['python', cmd]) != 0:
                    raise Exception('Succeeded creature failed!!!')
            else:
                failed_mutations += 1
                print('===== failed - reverting to this =====')
                print(self.creature_content)
                print('===== failed =====')
                self.save_mutant(self.creature_content)
                print('===== testing reverted creature =====')
                if subprocess.call(['python', cmd]) != 0:
                    raise Exception('Reverted creature failed!!!')

        self.save_mutant(self.creature_content)

        print('Successful mutations: %d' % successful_mutations)
        print('Failed mutations: %d' % failed_mutations)


class Dictionary(object):
    def __init__(self):
        """ Set up the dictionary.
            :return: None
        """
        # Make sure we have our spelling list extracted
        txt_name = 'wordsEN.txt'
        if not os.path.exists(txt_name):
            zip_name = 'wordsEn.zip'
            if os.path.exists(zip_name):
                if zipfile.is_zipfile(zip_name):
                    with zipfile.ZipFile(zip_name) as zip_file:
                        zip_file.extractall()
                else:
                    print('It appears that %s is not a valid zip file.' % zip_name)
                    raise Exception('Dictionary zip file invalid.')
            else:
                print('For spell checking, we need %s from'
                      'http://www-01.sil.org/linguistics/wordlists/english/wordlist/wordsEn.zip'
                      'in the current directory.  Did not find this file.' % zip_name)
                raise Exception('Dictionary zip file missing.')
        with open(txt_name) as word_file:
            self.all_words = [x.strip() for x in word_file]

    def spelled_correctly(self, sentence):
        """ spelled_correctly - Spell check
        :param sentence: The sentence to be checked
        :return: Returns True if all words are correctly spelled
        """
        for word in sentence.split():
            clean_word = word.strip(',. ;:').lower()
            if clean_word not in self.all_words:
                return False
        return True


# This particular ugliness (having this as a global) is to make the loading of the dictionary only happen once across
# all mutations which speeds things up.
DICTIONARY = Dictionary()


if __name__ == "__main__":
    MAJOR = 0
    MINOR = 0
    MICRO = 2
    print('mutate %d.%d.%d' % (MAJOR, MINOR, MICRO))
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("creature",
                        help='Path to the creature to mutate.  Mutated creature will be saved as'
                             ' mutated_<original_name>.py')
    PARSER.add_argument("mutations", help="Number of mutations", type=int)
    PARSER.add_argument("--seed", help="Random seed", type=float, default=time.time())
    PARSER.add_argument("--no-environment", help="Don't use the creature's environment.",
                        action="store_true")
    PARSER.add_argument("--no-keywords", help="Don't use python keywords as mutations.",
                        action="store_false")
    ARGS = PARSER.parse_args()

    print('args: %s' % ARGS)
    random.seed(ARGS.seed)
    print('git: %s' % subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8'))
    if subprocess.call(['git', 'diff-index', '--quiet', 'HEAD', '--']) != 0:
        print('git detects uncommitted changes on top of the above id.')
        print('diff:')
        print(subprocess.check_output(['git', 'diff']).strip().decode('utf-8'))

    CREATURE = Creature(ARGS.creature)
    CREATURE.mutate(ARGS.mutations, ARGS.no_environment, ARGS.no_keywords)
