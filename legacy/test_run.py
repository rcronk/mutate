"""Tests for the experiment runner.

Written before the implementation. The problem being solved: every experiment
writes a file named `mutated_<name>.py` and its test file imports that module by
name, so two runs in the same directory clobber each other and a run clobbers
the committed 2016 artifacts. Each run therefore gets an isolated working
directory, keyed by experiment and seed.
"""

import json
import os
import shutil
import tempfile
import unittest

import run


class RunnerTestCase(unittest.TestCase):
    """Shared setup: every test writes into a throwaway results root."""

    def setUp(self):
        self.results_root = tempfile.mkdtemp(prefix='mutate-test-')
        self.addCleanup(shutil.rmtree, self.results_root, ignore_errors=True)

    def go(self, experiment='beak', seed=1, generations=5, **kwargs):
        return run.run_experiment(experiment, seed=seed, generations=generations,
                                  results_root=self.results_root, quiet=True, **kwargs)


class TestDiscovery(RunnerTestCase):

    def test_lists_the_seven_original_experiments(self):
        found = set(run.available_experiments())
        expected = {'abiogenesis', 'beak', 'body_plans', 'english',
                    'hello_world_tested', 'hello_world_untested',
                    'multiple_functions'}
        self.assertEqual(expected, found)

    def test_knows_which_experiments_have_a_selector(self):
        """abiogenesis and hello_world_untested have no test file, so the only
        selector is 'does it execute'."""
        self.assertTrue(run.has_selector('beak'))
        self.assertTrue(run.has_selector('body_plans'))
        self.assertFalse(run.has_selector('abiogenesis'))
        self.assertFalse(run.has_selector('hello_world_untested'))

    def test_unknown_experiment_is_rejected(self):
        with self.assertRaises(ValueError):
            self.go(experiment='does_not_exist')


class TestRunLayout(RunnerTestCase):

    def test_creates_directory_keyed_by_experiment_and_seed(self):
        result = self.go(experiment='beak', seed=1234)
        expected = os.path.join(self.results_root, 'beak', 'seed-1234')
        self.assertEqual(expected, result.directory)
        self.assertTrue(os.path.isdir(expected))

    def test_writes_the_expected_files(self):
        result = self.go()
        for name in ('manifest.json', 'start.py', 'end.py', 'diff.txt'):
            self.assertTrue(os.path.isfile(os.path.join(result.directory, name)),
                            f'{name} was not written')

    def test_start_py_is_the_unmutated_original(self):
        result = self.go(experiment='beak')
        with open(os.path.join(result.directory, 'start.py'), encoding='utf-8') as handle:
            start = handle.read()
        with open(os.path.join(run.HERE, 'beak.py'), encoding='utf-8') as handle:
            original = handle.read()
        self.assertEqual(original, start)

    def test_rerunning_the_same_seed_overwrites_rather_than_accumulates(self):
        first = self.go(seed=7)
        second = self.go(seed=7)
        self.assertEqual(first.directory, second.directory)
        self.assertEqual(1, len(os.listdir(os.path.join(self.results_root, 'beak'))))

    def test_different_seeds_get_different_directories(self):
        first = self.go(seed=1)
        second = self.go(seed=2)
        self.assertNotEqual(first.directory, second.directory)
        self.assertEqual(2, len(os.listdir(os.path.join(self.results_root, 'beak'))))


class TestIsolation(RunnerTestCase):
    """The reason run directories exist at all."""

    def test_does_not_touch_the_2016_artifacts(self):
        artifact = os.path.join(run.HERE, 'artifacts-2016', 'mutated_beak.py')
        with open(artifact, encoding='utf-8') as handle:
            before = handle.read()
        self.go(experiment='beak', generations=10)
        with open(artifact, encoding='utf-8') as handle:
            self.assertEqual(before, handle.read())

    def test_does_not_write_into_the_source_directory(self):
        before = set(os.listdir(run.HERE))
        self.go(experiment='beak', generations=10)
        self.assertEqual(before, set(os.listdir(run.HERE)))


class TestManifest(RunnerTestCase):

    def load(self, result):
        with open(os.path.join(result.directory, 'manifest.json'), encoding='utf-8') as handle:
            return json.load(handle)

    def test_records_everything_needed_to_reproduce_the_run(self):
        manifest = self.load(self.go(experiment='beak', seed=42, generations=8))
        for field in ('experiment', 'seed', 'generations', 'operator_weights',
                      'span_probability', 'use_keywords', 'selector',
                      'python_version', 'git_sha', 'successful_mutations',
                      'failed_mutations', 'start_bytes', 'end_bytes'):
            self.assertIn(field, manifest, f'manifest is missing {field}')
        self.assertEqual('beak', manifest['experiment'])
        self.assertEqual(42, manifest['seed'])
        self.assertEqual(8, manifest['generations'])

    def test_records_pylint_version_because_it_is_a_selector(self):
        """pylint acts as a selector in two experiments, so its version is part
        of the experimental setup and must be recorded."""
        manifest = self.load(self.go(experiment='beak'))
        self.assertIn('pylint_version', manifest)

    def test_accepted_and_rejected_sum_to_generations(self):
        manifest = self.load(self.go(generations=12))
        self.assertEqual(12, manifest['successful_mutations'] + manifest['failed_mutations'])

    def test_records_which_operator_set_was_used(self):
        default = self.load(self.go(seed=1))
        legacy = self.load(self.go(seed=2, legacy_operators=True))
        self.assertGreater(default['operator_weights']['delete'], 0)
        self.assertEqual(0, legacy['operator_weights']['delete'])
        self.assertEqual(0, legacy['operator_weights']['duplicate'])


class TestReproducibility(RunnerTestCase):
    """The whole point of the runner."""

    def read_end(self, result):
        with open(os.path.join(result.directory, 'end.py'), encoding='utf-8') as handle:
            return handle.read()

    def test_same_seed_gives_identical_output(self):
        first = self.read_end(self.go(experiment='body_plans', seed=5, generations=15))
        shutil.rmtree(self.results_root, ignore_errors=True)
        second = self.read_end(self.go(experiment='body_plans', seed=5, generations=15))
        self.assertEqual(first, second)

    def test_different_seed_gives_different_output(self):
        first = self.read_end(self.go(experiment='body_plans', seed=5, generations=25))
        second = self.read_end(self.go(experiment='body_plans', seed=6, generations=25))
        self.assertNotEqual(first, second)

    def test_result_reports_the_directory_and_counts(self):
        result = self.go(generations=6)
        self.assertEqual(6, result.successful_mutations + result.failed_mutations)
        self.assertTrue(os.path.isdir(result.directory))


class TestSelectorBehaviour(RunnerTestCase):

    def test_untested_experiment_runs_without_a_test_file(self):
        result = self.go(experiment='hello_world_untested', generations=6)
        self.assertEqual(6, result.successful_mutations + result.failed_mutations)

    def test_abiogenesis_starts_empty(self):
        result = self.go(experiment='abiogenesis', generations=5)
        with open(os.path.join(result.directory, 'start.py'), encoding='utf-8') as handle:
            self.assertEqual('', handle.read())


if __name__ == '__main__':
    unittest.main()
