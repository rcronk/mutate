""" run.py - runs a creature population and records what happened.

    python -m creatures.run --seed 1 --ticks 100
    python -m creatures.run --replay results/creatures/seed-1

Each run gets a directory under results/creatures/, keyed by seed, holding a
manifest and an append-only event log.

Rerunning a seed does not reproduce the run. Genetics are reproducible, but OS
scheduling decides which creature reaches the food pool first, so a rerun is
statistically similar rather than identical. That is why the log exists: to
replay a run, read its log rather than running it again.
"""

import argparse
import os
import shutil
import sys
import time

from creatures import events, supervisor

DEFAULT_RESULTS_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'creatures')


def run_directory(results_root, seed):
    """ :return: Where a run with this seed is recorded """
    return os.path.join(results_root, f'seed-{seed}')


# Seven independent run parameters, all of which an experiment varies.
def run(*, seed=1, ticks=100, founders=10,  # pylint: disable=too-many-arguments
        regrowth=400, max_processes=supervisor.DEFAULT_MAX_PROCESSES,
        timeout=supervisor.DEFAULT_TIMEOUT, results_root=DEFAULT_RESULTS_ROOT,
        quiet=False):
    """ Runs a population and records it.
    :return: The run directory
    """
    directory = run_directory(results_root, seed)
    if os.path.isdir(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

    started = time.monotonic()
    with events.EventLog(os.path.join(directory, 'events.jsonl')) as log:
        with supervisor.Supervisor(regrowth=regrowth, max_processes=max_processes,
                                   timeout=timeout, log=log) as sup:
            sup.start(founders=founders, seed=seed)
            for _ in range(ticks):
                sup.tick()
                if not sup.living:
                    break
            summary = sup.summary()

    summary['wall_seconds'] = round(time.monotonic() - started, 2)
    events.write_manifest(os.path.join(directory, 'manifest.json'),
                          seed=seed, ticks=ticks, founders=founders,
                          regrowth=regrowth, max_processes=max_processes,
                          timeout=timeout, summary=summary)
    if not quiet:
        _report(directory, summary)
    return directory


def _report(directory, summary):
    """ Prints a short account of a completed run. """
    print(f'run written to {directory}')
    print(f'  ticks {summary["ticks"]}, survivors {summary["living"]}, '
          f'births {summary["births"]}, {summary["wall_seconds"]}s')
    causes = ', '.join(f'{c} {n}' for c, n in summary['deaths'].items() if n)
    print(f'  deaths: {causes or "none"}')
    if summary['cap_hits']:
        print(f'  WARNING: process cap hit {summary["cap_hits"]} times. The food '
              f'parameters were wrong, so this population was limited by an '
              f'artificial ceiling rather than by food.')


def summarize(directory):
    """ Reads a recorded run back and describes it, without running anything.
    :param directory: A run directory
    :return: 0 on success, 1 if there is nothing there
    """
    log_path = os.path.join(directory, 'events.jsonl')
    if not os.path.isfile(log_path):
        print(f'no event log in {directory}')
        return 1

    replay = events.Replay(log_path)
    population = replay.population_over_time
    print(f'replayed {directory}, no processes started')
    print(f'  ticks recorded     {len(population)}')
    if population:
        print(f'  population         start {population[0]}, '
              f'peak {max(population)}, end {population[-1]}')
    print(f'  births             {replay.births}')
    print(f'  failed births      {replay.failed_births} '
          f'({replay.birth_failure_rate:.1%} of attempts)')
    print(f'  deepest generation {replay.deepest_generation}')
    causes = ', '.join(f'{c} {n}' for c, n in sorted(replay.deaths.items()))
    print(f'  deaths             {causes or "none"}')

    strategy = replay.strategy_over_time
    if strategy:
        final = strategy[-1]
        print(f'  genetic divergence {final.get("genetic_divergence", 0):.1%} '
              f'of the living population is no longer the ancestor')
        drift = replay.strategy_drift
        if drift:
            moved = ', '.join(f'{k} {v:+.2f}' for k, v in sorted(drift.items()))
            print(f'  strategy drift     {moved}')
            print('  (realised-strategy drift mixes genetic change with the age '
                  'distribution;\n   genetic divergence is the cleaner evolution signal)')
    return 0


def main(arguments):
    """ Entry point for the command line. """
    parser = argparse.ArgumentParser(
        description='Run a creature population, or replay a recorded run.')
    parser.add_argument('--replay', metavar='DIR',
                        help='Replay a recorded run instead of running one.')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--ticks', type=int, default=100)
    parser.add_argument('--founders', type=int, default=10)
    parser.add_argument('--regrowth', type=int, default=400)
    parser.add_argument('--max-processes', type=int,
                        default=supervisor.DEFAULT_MAX_PROCESSES)
    parser.add_argument('--timeout', type=float, default=supervisor.DEFAULT_TIMEOUT)
    parser.add_argument('--results-root', default=DEFAULT_RESULTS_ROOT)
    args = parser.parse_args(arguments)

    if args.replay:
        return summarize(args.replay)

    run(seed=args.seed, ticks=args.ticks, founders=args.founders,
        regrowth=args.regrowth, max_processes=args.max_processes,
        timeout=args.timeout, results_root=args.results_root)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
