""" run.py - runs a legacy mutation experiment reproducibly.

Each run gets its own working directory under results/, keyed by experiment and
seed. That isolation matters: every experiment writes a file named
mutated_<name>.py and its test file imports that module by name, so two runs
sharing a directory would clobber each other, and a run in legacy/ would
overwrite the 2016 artifacts preserved in artifacts-2016/.

Rerunning the same seed overwrites its directory rather than accumulating, so
identical inputs produce exactly one result directory.
"""

import argparse
import dataclasses
import difflib
import json
import os
import random
import shutil
import subprocess
import sys

import mutate

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS_ROOT = os.path.join(os.path.dirname(HERE), 'results')

# Files in this directory that are not mutation experiments. Anything added
# here that is tooling rather than an experiment must be listed, otherwise it
# gets mutated. test_run.py asserts the exact expected set, so a new tool fails
# the suite loudly rather than silently becoming an experiment.
#
# self_mutator.py is the abandoned 2017 self-replication attempt. It does not
# run at all (see legacy/README.md section D) and is the starting point for
# phase 2 of the roadmap rather than something to mutate.
_NOT_EXPERIMENTS = {'mutate.py', 'run.py', 'summarize.py', 'self_mutator.py'}


@dataclasses.dataclass
class RunResult:
    """ What a completed run produced. """
    experiment: str
    seed: int
    directory: str
    successful_mutations: int
    failed_mutations: int


def available_experiments():
    """ Lists the experiments in this directory.
    :return: Sorted list of experiment names, without the .py suffix
    """
    names = []
    for entry in os.listdir(HERE):
        if not entry.endswith('.py') or entry in _NOT_EXPERIMENTS:
            continue
        if entry.startswith('test_'):
            continue
        names.append(entry[:-len('.py')])
    return sorted(names)


def has_selector(experiment):
    """ Reports whether an experiment has a unit test acting as its selector.

        Without one the only selector is 'does the file execute without
        error', which is what made the abiogenesis and untested hello world
        runs so permissive.
    :param experiment: Experiment name
    :return: True if a test file exists
    """
    return os.path.isfile(os.path.join(HERE, f'test_{experiment}.py'))


def _pylint_version():
    """ pylint acts as a selector in two experiments, so its version is part of
        the experimental setup and is recorded with every run.
    :return: Version string, or None if pylint is not installed
    """
    try:
        import pylint  # pylint: disable=import-outside-toplevel
        return pylint.__version__
    except ImportError:
        return None


def _git_sha():
    """ :return: Current commit SHA, or None outside a git checkout """
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=HERE,
            stderr=subprocess.DEVNULL).strip().decode('utf-8')
    except (subprocess.CalledProcessError, OSError):
        return None


def run_key(seed, *, legacy_operators=False,
            span_probability=mutate.DEFAULT_SPAN_PROBABILITY, use_keywords=True):
    """ Builds the directory name for a run.

        Keyed by seed alone in the common case, so the tree stays readable, but
        any setting that changes what the experiment does is appended. Without
        that, a comparison run at the same seed silently overwrites the run it
        is being compared against.
    :param seed: Random seed
    :param legacy_operators: Whether the 2016 operator set was used
    :param span_probability: Geometric parameter for delete/duplicate spans
    :param use_keywords: Whether Python keywords are in the mutation alphabet
    :return: Directory name
    """
    key = f'seed-{seed}'
    if legacy_operators:
        key += '-legacy'
    if span_probability != mutate.DEFAULT_SPAN_PROBABILITY:
        key += f'-span{span_probability:g}'
    if not use_keywords:
        key += '-nokeywords'
    return key


def _prepare_directory(experiment, key, results_root):
    """ Creates a clean working directory and copies the experiment into it.
    :param experiment: Experiment name
    :param key: Directory name from run_key()
    :param results_root: Root directory for all results
    :return: Path to the prepared working directory
    """
    directory = os.path.join(results_root, experiment, key)
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

    shutil.copy(os.path.join(HERE, f'{experiment}.py'), directory)
    if has_selector(experiment):
        shutil.copy(os.path.join(HERE, f'test_{experiment}.py'), directory)
    return directory


# Eight keyword-only knobs, each of which a caller legitimately varies per run.
# Bundling them into a config object would add indirection without removing a
# decision, so the limit is waived rather than worked around.
def run_experiment(experiment, *, seed, generations,  # pylint: disable=too-many-arguments
                   results_root=DEFAULT_RESULTS_ROOT, legacy_operators=False,
                   span_probability=mutate.DEFAULT_SPAN_PROBABILITY,
                   use_keywords=True, quiet=False):
    """ Runs one experiment and records everything needed to reproduce it.
    :param experiment: Experiment name, from available_experiments()
    :param seed: Random seed; the same seed reproduces the same result
    :param generations: Number of mutation attempts
    :param results_root: Root directory for results
    :param legacy_operators: Use only the 2016 operator set
    :param span_probability: Geometric parameter for delete/duplicate spans
    :param use_keywords: Include Python keywords in the mutation alphabet
    :param quiet: Suppress the per-generation trace
    :return: A RunResult
    """
    if experiment not in available_experiments():
        raise ValueError(
            f'Unknown experiment {experiment!r}. '
            f'Available: {", ".join(available_experiments())}')

    directory = _prepare_directory(
        experiment,
        run_key(seed, legacy_operators=legacy_operators,
                span_probability=span_probability, use_keywords=use_keywords),
        results_root)
    weights = (mutate.LEGACY_MUTATION_WEIGHTS if legacy_operators
               else mutate.DEFAULT_MUTATION_WEIGHTS)

    creature = mutate.Creature(f'{experiment}.py', work_dir=directory)
    start_content = creature.creature_content

    random.seed(seed)
    successful, failed = creature.mutate(
        generations, False, use_keywords,
        mutation_weights=weights, span_probability=span_probability, quiet=quiet)
    end_content = creature.creature_content

    _write_outputs(directory, experiment, start_content, end_content)
    _write_manifest(directory, {
        'experiment': experiment,
        'seed': seed,
        'generations': generations,
        'operator_weights': dict(weights),
        'span_probability': span_probability,
        'use_keywords': use_keywords,
        'selector': f'test_{experiment}.py' if has_selector(experiment) else 'execution only',
        'python_version': sys.version.split()[0],
        'pylint_version': _pylint_version(),
        'git_sha': _git_sha(),
        'successful_mutations': successful,
        'failed_mutations': failed,
        'start_bytes': len(start_content),
        'end_bytes': len(end_content),
    })
    return RunResult(experiment, seed, directory, successful, failed)


def _write_manifest(directory, manifest):
    """ Records everything needed to reproduce a run. """
    with open(os.path.join(directory, 'manifest.json'), 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write('\n')


def _write_outputs(directory, experiment, start_content, end_content):
    """ Writes the before, after, and diff for a completed run. """
    with open(os.path.join(directory, 'start.py'), 'w', encoding='utf-8') as handle:
        handle.write(start_content)
    with open(os.path.join(directory, 'end.py'), 'w', encoding='utf-8') as handle:
        handle.write(end_content)
    diff = difflib.unified_diff(
        start_content.splitlines(keepends=True),
        end_content.splitlines(keepends=True),
        fromfile=f'{experiment}.py (start)',
        tofile=f'{experiment}.py (end)')
    with open(os.path.join(directory, 'diff.txt'), 'w', encoding='utf-8') as handle:
        handle.writelines(diff)


def main(arguments):
    """ Entry point for the command line. """
    parser = argparse.ArgumentParser(
        description='Run a legacy mutation experiment reproducibly.')
    parser.add_argument('experiment', nargs='?',
                        help=f'One of: {", ".join(available_experiments())}')
    parser.add_argument('--all', action='store_true',
                        help='Run every experiment with the same settings.')
    parser.add_argument('--list', action='store_true',
                        help='List the available experiments and exit.')
    parser.add_argument('--seed', type=int, default=1,
                        help='Random seed. The same seed reproduces the same result.')
    parser.add_argument('--generations', type=int, default=1000,
                        help='Number of mutation attempts.')
    parser.add_argument('--results-root', default=DEFAULT_RESULTS_ROOT,
                        help='Where to write results.')
    parser.add_argument('--legacy-operators', action='store_true',
                        help='Use only the 2016 operator set, so genomes can only grow.')
    parser.add_argument('--span-probability', type=float,
                        default=mutate.DEFAULT_SPAN_PROBABILITY,
                        help='Geometric parameter for delete/duplicate span length.')
    parser.add_argument('--no-keywords', dest='use_keywords', action='store_false',
                        help="Don't use python keywords as mutations.")
    parser.add_argument('--verbose', action='store_true',
                        help='Print every generation rather than a summary.')
    args = parser.parse_args(arguments)

    if args.list:
        for name in available_experiments():
            selector = f'test_{name}.py' if has_selector(name) else 'execution only'
            print(f'{name:24} selector: {selector}')
        return 0

    if not args.all and not args.experiment:
        parser.error('give an experiment name, or --all, or --list')

    targets = available_experiments() if args.all else [args.experiment]
    for name in targets:
        result = run_experiment(
            name, seed=args.seed, generations=args.generations,
            results_root=args.results_root,
            legacy_operators=args.legacy_operators,
            span_probability=args.span_probability,
            use_keywords=args.use_keywords,
            quiet=not args.verbose)
        print(f'{result.experiment:24} '
              f'accepted {result.successful_mutations:5} / {args.generations:<5} '
              f'-> {result.directory}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
