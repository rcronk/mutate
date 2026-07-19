""" mutate.py - a mutation algorithm. """

import argparse
import importlib.util
import os
import random
import string
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


class Creature:
    """ This is a creature that can duplicate itself with errors. """
    def __init__(self, path_to_creature):
        assert os.path.sep not in path_to_creature
        self.path_to_creature = path_to_creature
        self.test_path = f'test_{self.path_to_creature}'
        self.mutant_path = f'mutated_{self.path_to_creature}'

        with open(self.path_to_creature, encoding='utf-8') as creature_file:
            self.creature_content = creature_file.read()

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
        # Floating point rounding can leave rand_num fractionally above the
        # accumulated total, which previously fell off the end and returned None.
        return choices[-1][0]

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
                raise ValueError(f'Invalid defect: {defect}')
        return source

    def save_mutant(self, creature_content):
        """ save_mutant: Saves new mutant content to file.
        :param creature_content: Text of file to be saved.
        :return: None
        """
        with open(self.mutant_path, 'w', encoding='utf-8') as mutant_path_handle:
            mutant_path_handle.write(creature_content)
        # Stale bytecode would otherwise be reused, so the mutant that runs would
        # not be the mutant just written. The original hardcoded a Windows path
        # for Python 3.5, which silently did nothing on any other platform.
        pyc_file = importlib.util.cache_from_source(self.mutant_path)
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
            print(f'Iteration: {i}')
            mutated_content = self._flawed_copy(self.creature_content, use_keywords=use_keywords)
            print('===== new mutant =====')
            print(mutated_content)
            print('===== new =====')
            self.save_mutant(mutated_content)

            if subprocess.call([sys.executable, cmd]) == 0:
                successful_mutations += 1
                self.creature_content = mutated_content
                print('===== succeeded - new creature =====')
                print(self.creature_content)
                print('===== succeeded =====')
#                if subprocess.call(['python', cmd]) != 0:
#                    raise Exception('Succeeded creature failed!!!')
            else:
                failed_mutations += 1
                print('===== failed - reverting to this =====')
                print(self.creature_content)
                print('===== failed =====')
                self.save_mutant(self.creature_content)
                print('===== testing reverted creature =====')
#                if subprocess.call(['python', cmd]) != 0:
#                    raise Exception('Reverted creature failed!!!')

        self.save_mutant(self.creature_content)

        print(f'Successful mutations: {successful_mutations}')
        print(f'Failed mutations: {failed_mutations}')


class Dictionary:  # pylint: disable=too-few-public-methods
    """ This is a simple dictionary. """
    def __init__(self):
        """ Set up the dictionary.
            :return: None
        """
        # Make sure we have our spelling list extracted. Note the capitalisation:
        # the archive contains 'wordsEn.txt', and the original code looked for
        # 'wordsEN.txt', which only worked because Windows filenames are
        # case-insensitive. On Linux it extracted the zip and then failed to find
        # what it had just extracted, on every single run.
        txt_name = os.path.join(HERE, 'wordsEn.txt')
        if not os.path.exists(txt_name):
            zip_name = os.path.join(HERE, 'wordsEn.zip')
            if os.path.exists(zip_name):
                if zipfile.is_zipfile(zip_name):
                    with zipfile.ZipFile(zip_name) as zip_file:
                        zip_file.extractall(HERE)
                else:
                    print(f'It appears that {zip_name} is not a valid zip file.')
                    raise ValueError('Dictionary zip file invalid.')
            else:
                print(f'For spell checking, we need {zip_name} from '
                      'http://www-01.sil.org/linguistics/wordlists/english/wordlist/'
                      'wordsEn.zip.  Did not find this file.')
                raise FileNotFoundError('Dictionary zip file missing.')
        with open(txt_name, encoding='utf-8') as word_file:
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


def main(arguments):
    """ Entry point for command line. """
    major = 0
    minor = 0
    micro = 2
    print(f'mutate {major}.{minor}.{micro}')
    parser = argparse.ArgumentParser()
    parser.add_argument("creature",
                        help='Path to the creature to mutate.  Mutated creature will be saved as'
                             ' mutated_<original_name>.py')
    parser.add_argument("mutations", help="Number of mutations", type=int)
    parser.add_argument("--seed", help="Random seed", type=float, default=time.time())
    parser.add_argument("--no-environment", help="Don't use the creature's environment.",
                        action="store_true")
    parser.add_argument("--no-keywords", help="Don't use python keywords as mutations.",
                        action="store_false")
    args = parser.parse_args(arguments)

    print(f'args: {args}')
    random.seed(args.seed)
    git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8')
    print(f'git: {git_sha}')
    if subprocess.call(['git', 'diff-index', '--quiet', 'HEAD', '--']) != 0:
        print('git detects uncommitted changes on top of the above id.')
        print('diff:')
        print(subprocess.check_output(['git', 'diff']).strip().decode('utf-8'))

    creature = Creature(args.creature)
    creature.mutate(args.mutations, args.no_environment, args.no_keywords)


if __name__ == "__main__":
    main(sys.argv[1:])
