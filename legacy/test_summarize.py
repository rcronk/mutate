"""Tests for the results summarizer.

The point of this tool is that the numbers in legacy/README.md are generated
from run manifests rather than typed by hand, so a claim in the writeup can
always be traced back to a run directory and a seed.
"""

import json
import os
import shutil
import tempfile
import unittest

import summarize


def write_manifest(root, experiment, key, **fields):
    """Creates a fake run directory with a manifest."""
    directory = os.path.join(root, experiment, key)
    os.makedirs(directory, exist_ok=True)
    manifest = {
        'experiment': experiment,
        'seed': fields.get('seed', 1),
        'generations': fields.get('generations', 100),
        'operator_weights': fields.get('operator_weights',
                                       {'delete': 25, 'duplicate': 25}),
        'span_probability': 0.3,
        'use_keywords': True,
        'selector': fields.get('selector', f'test_{experiment}.py'),
        'python_version': '3.10.12',
        'pylint_version': '4.0.6',
        'git_sha': 'abc123',
        'successful_mutations': fields.get('successful', 10),
        'failed_mutations': fields.get('generations', 100) - fields.get('successful', 10),
        'start_bytes': fields.get('start_bytes', 100),
        'end_bytes': fields.get('end_bytes', 120),
    }
    with open(os.path.join(directory, 'manifest.json'), 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle)
    return directory


class SummarizeTestCase(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='mutate-summary-')
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)


class TestLoading(SummarizeTestCase):

    def test_finds_every_manifest(self):
        write_manifest(self.root, 'beak', 'seed-1', seed=1)
        write_manifest(self.root, 'beak', 'seed-2', seed=2)
        write_manifest(self.root, 'english', 'seed-1', seed=1)
        self.assertEqual(3, len(summarize.load_runs(self.root)))

    def test_ignores_directories_without_a_manifest(self):
        write_manifest(self.root, 'beak', 'seed-1')
        os.makedirs(os.path.join(self.root, 'beak', 'not-a-run'))
        self.assertEqual(1, len(summarize.load_runs(self.root)))

    def test_missing_root_gives_no_runs(self):
        self.assertEqual([], summarize.load_runs(os.path.join(self.root, 'nope')))


class TestGrouping(SummarizeTestCase):

    def test_separates_operator_sets(self):
        """Legacy and default runs of the same experiment are different
        conditions and must not be averaged together."""
        write_manifest(self.root, 'beak', 'seed-1', seed=1)
        write_manifest(self.root, 'beak', 'seed-1-legacy', seed=1,
                       operator_weights={'delete': 0, 'duplicate': 0})
        groups = summarize.group_runs(summarize.load_runs(self.root))
        self.assertEqual(2, len(groups))
        self.assertEqual({('beak', 'all six'), ('beak', '2016 set')},
                         {(g.experiment, g.operators) for g in groups})

    def test_averages_across_seeds(self):
        for seed, successful in ((1, 10), (2, 20), (3, 30)):
            write_manifest(self.root, 'beak', f'seed-{seed}',
                           seed=seed, successful=successful, generations=100)
        group = summarize.group_runs(summarize.load_runs(self.root))[0]
        self.assertEqual(3, group.replicates)
        self.assertAlmostEqual(20.0, group.mean_accepted, places=5)

    def test_reports_the_range_across_seeds(self):
        for seed, successful in ((1, 5), (2, 25)):
            write_manifest(self.root, 'beak', f'seed-{seed}',
                           seed=seed, successful=successful)
        group = summarize.group_runs(summarize.load_runs(self.root))[0]
        self.assertEqual(5, group.min_accepted)
        self.assertEqual(25, group.max_accepted)

    def test_reports_mean_size_change(self):
        write_manifest(self.root, 'beak', 'seed-1', seed=1,
                       start_bytes=100, end_bytes=150)
        write_manifest(self.root, 'beak', 'seed-2', seed=2,
                       start_bytes=100, end_bytes=250)
        group = summarize.group_runs(summarize.load_runs(self.root))[0]
        self.assertAlmostEqual(100.0, group.mean_start_bytes, places=5)
        self.assertAlmostEqual(200.0, group.mean_end_bytes, places=5)

    def test_acceptance_rate_is_a_proportion_of_generations(self):
        write_manifest(self.root, 'beak', 'seed-1', successful=25, generations=100)
        group = summarize.group_runs(summarize.load_runs(self.root))[0]
        self.assertAlmostEqual(0.25, group.acceptance_rate, places=5)


class TestMarkdown(SummarizeTestCase):

    def test_renders_a_table_with_one_row_per_group(self):
        write_manifest(self.root, 'beak', 'seed-1', seed=1)
        write_manifest(self.root, 'english', 'seed-1', seed=1)
        table = summarize.to_markdown(summarize.group_runs(summarize.load_runs(self.root)))
        self.assertIn('| beak', table)
        self.assertIn('| english', table)
        self.assertIn('---', table)

    def test_names_the_selector(self):
        write_manifest(self.root, 'abiogenesis', 'seed-1', selector='execution only')
        table = summarize.to_markdown(summarize.group_runs(summarize.load_runs(self.root)))
        self.assertIn('execution only', table)

    def test_empty_results_render_without_crashing(self):
        self.assertIsInstance(summarize.to_markdown([]), str)


if __name__ == '__main__':
    unittest.main()
