import time
import random
import string
import subprocess
import argparse
import os
import py_compile
import zipfile


class Creature(object):
    def __init__(self, path_to_creature):
        self.path_to_creature = path_to_creature
        self.make_mutant_path()
        self.make_test_path()

    def weighted_choice(self, choices):
        """ Picks a choice at random but with weight
            choices: list of tuples in the form (choice, weight)
            choice:  list
            weight:  any integer that represents a weight for this choice
        """
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for c, w in choices:
            if upto + w >= r:
                return c
            upto += w

    def flawed_copy(self, source, prepend=25, overwrite=25, insert=25, append=25):
        """ Copies source and returns it with flaws according to the weighted
            flaws passed in.
            source : list of characters
        """
        defect = self.weighted_choice([('prepend', prepend),
                                  ('overwrite', overwrite),
                                  ('insert', insert),
                                  ('append', append)])

        python_keywords = [' and ', ' del ', ' from ', ' not ', ' while ', ' as ', ' elif ', ' global ', ' or ', ' with ',
                           ' assert ', ' else ', ' if ', ' pass ', ' yield ', ' break ', ' except ', ' import ', ' print ',
                           ' class ', ' exec ', ' in ', ' raise ', ' continue ', ' finally ', ' is ', ' return ', ' def ',
                           ' for ', ' lambda ', ' try ']

        mutation = random.SystemRandom().choice(list(string.ascii_letters) +
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
                    source = source[:mutation_location] + mutation + source[mutation_location+1:]
                else:
                    source = source[:mutation_location] + mutation + source[mutation_location:]
            else:
                raise ('Invalid defect: %s' % defect)
        return source

    def make_test_path(self):
        assert(os.path.sep not in self.path_to_creature)
        self.test_path = 'test_%s' % self.path_to_creature

    def make_mutant_path(self):
        assert(os.path.sep not in self.path_to_creature)
        self.mutant_path = 'mutated_%s' % self.path_to_creature

    def load(self, creature_path):
        fp = open(creature_path)
        creature_content = fp.read()
        fp.close()
        return creature_content

    def save_mutant(self, creature_content):
        fp = open(self.mutant_path, 'w')
        fp.write(creature_content)
        fp.close()

    def mutate(self, mutations, no_environment):
        successful_mutations = 0
        failed_mutations = 0
        seed = time.time()
        print('seed: %f' % seed)
        random.seed(seed)

        if not os.path.exists(self.test_path):
            no_environment = True

        if no_environment:
            cmd = self.mutant_path
        else:
            cmd = self.test_path

        creature_content = self.load(self.path_to_creature)
        self.save_mutant(creature_content)

        for mutation in range(mutations):
            mutated_content = self.flawed_copy(creature_content)
            print('===== new mutant =====')
            print(mutated_content)
            print('===== new =====')
            self.save_mutant(mutated_content)

            py_compile.compile(cmd) # Sometimes there seems to be a race that causes quick changes not to be compiled
            if subprocess.call(['python', cmd]) == 0:
                successful_mutations += 1
                creature_content = mutated_content
                print('===== succeeded - new creature =====')
                print(creature_content)
                print('===== succeeded =====')
            else:
                failed_mutations += 1
                print('===== failed - reverting to this =====')
                print(creature_content)
                print('===== failed =====')

        self.save_mutant(creature_content)

        print('Successful mutations: %d' % successful_mutations)
        print('Failed mutations: %d' % failed_mutations)


def setup():
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
        else:
            print('For spell checking, we need %s from'
                  'http://www-01.sil.org/linguistics/wordlists/english/wordlist/wordsEn.zip in the current directory.'
                  'Did not find this file.' % zip_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("creature", help="Path to the creature to mutate.  Mutated creature will be saved as mutated_<original_name>.py")
    parser.add_argument("mutations", help="Number of mutations", type=int)
    parser.add_argument("--no-environment", help="Don't use the creature's environment.", action="store_true")
    args = parser.parse_args()
    setup()
    creature = Creature(args.creature)
    creature.mutate(args.mutations, args.no_environment)
