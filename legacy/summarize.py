""" summarize.py - turns run manifests into a results table.

The numbers quoted in legacy/README.md come from here rather than being typed by
hand, so every claim in the writeup traces back to a run directory and a seed.

    python legacy/summarize.py
    python legacy/summarize.py --results-root results --markdown
"""

import argparse
import dataclasses
import json
import os
import statistics
import sys

DEFAULT_RESULTS_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')


@dataclasses.dataclass
class Group:  # pylint: disable=too-many-instance-attributes
    """ One experimental condition, averaged over its seeds.

        This is a plain record of measured values, so the attribute count
        reflects how many things a run reports rather than any design problem.
    """
    experiment: str
    operators: str
    selector: str
    replicates: int
    generations: int
    mean_accepted: float
    min_accepted: int
    max_accepted: int
    mean_start_bytes: float
    mean_end_bytes: float

    @property
    def acceptance_rate(self):
        """ :return: Accepted mutations as a proportion of attempts """
        return self.mean_accepted / self.generations if self.generations else 0.0

    @property
    def growth(self):
        """ :return: End size as a multiple of start size, or None if empty """
        if not self.mean_start_bytes:
            return None
        return self.mean_end_bytes / self.mean_start_bytes


def load_runs(results_root=DEFAULT_RESULTS_ROOT):
    """ Reads every manifest under the results root.
    :param results_root: Directory containing per-experiment result folders
    :return: List of manifest dicts
    """
    runs = []
    if not os.path.isdir(results_root):
        return runs
    for experiment in sorted(os.listdir(results_root)):
        experiment_dir = os.path.join(results_root, experiment)
        if not os.path.isdir(experiment_dir):
            continue
        for entry in sorted(os.listdir(experiment_dir)):
            manifest_path = os.path.join(experiment_dir, entry, 'manifest.json')
            if not os.path.isfile(manifest_path):
                continue
            with open(manifest_path, encoding='utf-8') as handle:
                runs.append(json.load(handle))
    return runs


def _operator_label(manifest):
    """ Names the operator set so conditions are not averaged together.

        A run using the 2016 set is a different experiment from one that can
        delete and duplicate, even at the same seed.
    :param manifest: A run manifest
    :return: Human-readable label
    """
    weights = manifest.get('operator_weights', {})
    indels_enabled = weights.get('delete', 0) or weights.get('duplicate', 0)
    return 'all six' if indels_enabled else '2016 set'


def group_runs(runs):
    """ Groups runs by experiment and operator set, averaging across seeds.
    :param runs: Manifest dicts from load_runs()
    :return: Sorted list of Group
    """
    buckets = {}
    for manifest in runs:
        key = (manifest['experiment'], _operator_label(manifest))
        buckets.setdefault(key, []).append(manifest)

    groups = []
    for (experiment, operators), members in sorted(buckets.items()):
        accepted = [m['successful_mutations'] for m in members]
        groups.append(Group(
            experiment=experiment,
            operators=operators,
            selector=members[0].get('selector', 'unknown'),
            replicates=len(members),
            generations=members[0].get('generations', 0),
            mean_accepted=statistics.mean(accepted),
            min_accepted=min(accepted),
            max_accepted=max(accepted),
            mean_start_bytes=statistics.mean(m['start_bytes'] for m in members),
            mean_end_bytes=statistics.mean(m['end_bytes'] for m in members),
        ))
    return groups


def to_markdown(groups):
    """ Renders groups as a markdown table.
    :param groups: List of Group
    :return: Markdown string
    """
    if not groups:
        return '_No runs found._\n'

    lines = [
        '| experiment | operators | selector | seeds | accepted / 1000 | range | bytes |',
        '|---|---|---|---|---|---|---|',
    ]
    for group in groups:
        accepted = f'{group.mean_accepted:.0f} ({group.acceptance_rate:.1%})'
        span = f'{group.min_accepted}-{group.max_accepted}'
        size = f'{group.mean_start_bytes:.0f} to {group.mean_end_bytes:.0f}'
        if group.growth is not None and group.growth != 1:
            size += f' ({group.growth:.1f}x)'
        lines.append(f'| {group.experiment} | {group.operators} | {group.selector} '
                     f'| {group.replicates} | {accepted} | {span} | {size} |')
    return '\n'.join(lines) + '\n'


def main(arguments):
    """ Entry point for the command line. """
    parser = argparse.ArgumentParser(description='Summarize mutation experiment runs.')
    parser.add_argument('--results-root', default=DEFAULT_RESULTS_ROOT,
                        help='Directory containing results.')
    parser.add_argument('--markdown', action='store_true',
                        help='Emit a markdown table for pasting into the writeup.')
    args = parser.parse_args(arguments)

    groups = group_runs(load_runs(args.results_root))
    if args.markdown:
        print(to_markdown(groups), end='')
        return 0

    if not groups:
        print('No runs found. Try: python legacy/run.py --all --seed 1')
        return 1
    for group in groups:
        print(f'{group.experiment:22} {group.operators:9} '
              f'seeds={group.replicates} '
              f'accepted={group.mean_accepted:7.1f}/{group.generations} '
              f'({group.acceptance_rate:6.1%}) '
              f'range={group.min_accepted}-{group.max_accepted} '
              f'bytes={group.mean_start_bytes:.0f}->{group.mean_end_bytes:.0f}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
