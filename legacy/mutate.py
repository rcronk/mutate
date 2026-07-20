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

# Operators that add or rearrange rather than remove. These are the only ones
# the 2016 mutator had, which is why genomes could only ever grow.
GROWTH_OPERATORS = ('prepend', 'append', 'insert', 'overwrite')
SPAN_OPERATORS = ('delete', 'duplicate')
ALL_OPERATORS = GROWTH_OPERATORS + SPAN_OPERATORS

# Default: all six operators, equally weighted.
DEFAULT_MUTATION_WEIGHTS = {name: 25 for name in ALL_OPERATORS}

# The 2016 operator set, kept so the historical experiments remain reproducible
# and so runs with and without indels can be compared directly. See issue #18.
LEGACY_MUTATION_WEIGHTS = {name: (25 if name in GROWTH_OPERATORS else 0)
                           for name in ALL_OPERATORS}

# Probability parameter for the geometric span length distribution used by
# delete and duplicate. Mean span length is 1/p, so 0.3 gives a mean of about
# 3.3 characters: usually short, occasionally longer. Lower it to make
# large-scale duplication reachable.
DEFAULT_SPAN_PROBABILITY = 0.3


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
    def _span_length(max_length, probability=DEFAULT_SPAN_PROBABILITY):
        """ Draws a span length from a geometric distribution, capped at
            max_length.  Mean is 1/probability.  Short spans dominate, but the
            tail is unbounded, so a low probability makes duplication of a whole
            block reachable without ever telling the mutator where blocks are.
        :param max_length: Longest span permitted, normally len(source)
        :param probability: Geometric parameter; mean span length is 1/p
        :return: An integer in [1, max_length]
        """
        if max_length <= 1:
            return max_length
        length = 1
        while length < max_length and random.random() > probability:
            length += 1
        return length

    @staticmethod
    def _apply_span_operator(source, defect, span_probability):
        """ Applies an operator that acts on a span of the existing source
            rather than splicing in a newly generated fragment.

            delete    removes a contiguous span.  The 2016 mutator had no way
                      to do this, so its genomes could only ever grow.
            duplicate copies a contiguous span and reinserts it at a random
                      position.  This is the mechanism proposed for the origin
                      of new genes (Ohno 1970); the position is random rather
                      than adjacent so the mutator is not told where meaningful
                      boundaries lie.
        :param source: The text to mutate
        :param defect: One of SPAN_OPERATORS
        :param span_probability: Geometric parameter for the span length
        :return: The mutated text
        """
        if len(source) == 0:
            return source
        span = Creature._span_length(len(source), span_probability)
        start = random.randint(0, len(source) - span)
        if defect == 'delete':
            return source[:start] + source[start + span:]
        copied = source[start:start + span]
        paste_at = random.randint(0, len(source))
        return source[:paste_at] + copied + source[paste_at:]

    @staticmethod
    def _apply_splice_operator(source, defect, use_keywords):
        """ Applies an operator that splices a newly generated fragment into
            the source.  These four are the entire 2016 operator set.

            Note that none of them can shorten the source, and that overwrite
            is not length-preserving: it replaces one character with a mutation
            string that may be a Python keyword of around six characters. That
            asymmetry is the reason the original runs accumulated junk.
        :param source: The text to mutate
        :param defect: One of GROWTH_OPERATORS
        :param use_keywords: Include Python keywords in the mutation alphabet
        :return: The mutated text
        """
        python_keywords = []
        if use_keywords:
            python_keywords = [' and ', ' del ', ' from ', ' not ', ' while ', ' as ', ' elif ',
                               ' global ', ' or ', ' with ', ' assert ', ' else ', ' if ',
                               ' pass ', ' yield ', ' break ', ' except ', ' import ', ' print ',
                               ' class ', ' exec ', ' in ', ' raise ', ' continue ', ' finally ',
                               ' is ', ' return ', ' def ', ' for ', ' lambda ', ' try ']

        mutation = random.choice(list(string.ascii_letters) +
                                 list(string.digits) +
                                 python_keywords +
                                 list('\n:=%%'))

        if len(source) == 0:
            return mutation
        if defect == 'prepend':
            return mutation + source
        if defect == 'append':
            return source + mutation
        location = random.randint(0, len(source) - 1)
        if defect == 'overwrite':
            return source[:location] + mutation + source[location + 1:]
        if defect == 'insert':
            return source[:location] + mutation + source[location:]
        raise ValueError(f'Invalid defect: {defect}')

    @staticmethod
    def _flawed_copy(source, mutation_weights=None, use_keywords=True,
                     span_probability=DEFAULT_SPAN_PROBABILITY):
        """ Copies source and returns it with flaws according to the weighted
            flaws passed in.
            source : list of characters
        """
        if mutation_weights is None:
            mutation_weights = DEFAULT_MUTATION_WEIGHTS

        unknown = set(mutation_weights) - set(ALL_OPERATORS)
        if unknown:
            raise ValueError(f'Unknown mutation operators: {sorted(unknown)}')
        if sum(mutation_weights.values()) <= 0:
            raise ValueError('At least one mutation operator must have a weight above zero.')

        defect = Creature._weighted_choice(
            [(name, weight) for name, weight in mutation_weights.items() if weight > 0])

        # delete and duplicate act on a span of the existing source rather than
        # splicing in a new fragment, so they are handled before a mutation
        # string is generated at all.
        if defect in SPAN_OPERATORS:
            return Creature._apply_span_operator(source, defect, span_probability)

        return Creature._apply_splice_operator(source, defect, use_keywords)

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

    def mutate(self, mutations, no_environment, use_keywords,
               mutation_weights=None, span_probability=DEFAULT_SPAN_PROBABILITY):
        """ mutate - mutates something mutations times
        :param mutations: times to mutate
        :param no_environment: Skip unit tests even if present
        :param use_keywords: Use python keywords as mutations or not
        :param mutation_weights: Operator weights; None means all six equally
        :param span_probability: Geometric parameter for delete/duplicate spans
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
            mutated_content = self._flawed_copy(self.creature_content,
                                                mutation_weights=mutation_weights,
                                                use_keywords=use_keywords,
                                                span_probability=span_probability)
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
    parser.add_argument("--legacy-operators",
                        help='Use only the 2016 operator set (prepend, append, insert, '
                             'overwrite).  Genomes can then only grow, which reproduces '
                             'the original behaviour.',
                        action="store_true")
    parser.add_argument("--span-probability",
                        help='Geometric parameter for delete/duplicate span length.  '
                             'Mean span is 1/p, so lower values make large-scale '
                             'duplication reachable.',
                        type=float, default=DEFAULT_SPAN_PROBABILITY)
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
    weights = LEGACY_MUTATION_WEIGHTS if args.legacy_operators else DEFAULT_MUTATION_WEIGHTS
    print(f'operators: {sorted(name for name, w in weights.items() if w > 0)}')
    creature.mutate(args.mutations, args.no_environment, args.no_keywords,
                    mutation_weights=weights, span_probability=args.span_probability)


if __name__ == "__main__":
    main(sys.argv[1:])
