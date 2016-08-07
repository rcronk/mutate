import time
import random
import string
import subprocess
import argparse
import os


def flawed_copy(source, prepend=25, overwrite=25, insert=25, append=25):
    """ Copies source and returns it with flaws according to the weighted
        flaws passed in.
        source : list of characters
    """
    defect = weighted_choice([('prepend', prepend),
                              ('overwrite', overwrite),
                              ('insert', insert),
                              ('append', append)])

    mutation = random.SystemRandom().choice(string.ascii_letters + string.digits + '\n:=%%')

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

def weighted_choice(choices):
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


def make_environment_path(creature):
    assert(os.path.sep not in creature)
    return 'test_%s' % creature


def make_mutant_path(creature):
    assert(os.path.sep not in creature)
    return 'mutated_%s' % creature


def load_creature(creature_path):
    fp = open(creature_path)
    creature_content = fp.read()
    fp.close()
    return creature_content


def save_creature(creature_path, creature_content):
    fp = open(creature_path, 'w')
    fp.write(creature_content)
    fp.close()


def mutate(creature, mutations, no_environment):
    successful_mutations = 0
    failed_mutations = 0
    seed = time.time()
    print('seed: %f' % seed)
    random.seed(seed)

    mutated_creature = make_mutant_path(creature)
    creature_environment = make_environment_path(creature)
    if not os.path.exists(creature_environment):
        no_environment = True

    creature_content = load_creature(creature)
    save_creature(mutated_creature, creature_content)

    for mutation in range(mutations):
        mutated_content = flawed_copy(creature_content)
        print('===== new mutant =====')
        print(mutated_content)
        print('===== new =====')
        save_creature(mutated_creature, mutated_content)

        if no_environment:
            cmd = mutated_creature
        else:
            cmd = creature_environment

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

    save_creature(mutated_creature, creature_content)

    print('Successful mutations: %d' % successful_mutations)
    print('Failed mutations: %d' % failed_mutations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("creature", help="Path to the creature to mutate.  Mutated creature will be saved as mutated_<original_name>.py")
    parser.add_argument("mutations", help="Number of mutations", type=int)
    parser.add_argument("--no-environment", help="Don't use the creature's environment.", action="store_true")
    args = parser.parse_args()
    mutate(args.creature, args.mutations, args.no_environment)
