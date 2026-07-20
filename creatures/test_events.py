"""Tests for the event log, run manifest, and replay.

Written before the implementation.

Forked runs cannot be reproduced byte for byte, because OS scheduling decides
who reaches the food pool first. So instead of re-running to find out what
happened, every run records what happened. The log is the record; replay reads
it back without spawning a single process.

That matters twice over: analysis stops depending on luck, and phase 4 can
animate a run without re-running it.
"""

import json
import os
import shutil
import tempfile
import unittest

from creatures import events


class EventTestCase(unittest.TestCase):
    """Shared setup: every test writes into a throwaway directory."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='mutate-events-')
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.path = os.path.join(self.root, 'events.jsonl')


class TestWriting(EventTestCase):

    def test_events_are_written_one_per_line(self):
        with events.EventLog(self.path) as log:
            log.birth(tick=1, identity='0.1', generation=2, parent='0')
            log.death(tick=2, identity='0.1', cause='old_age', age=12, generation=2)
        with open(self.path, encoding='utf-8') as handle:
            lines = handle.read().splitlines()
        self.assertEqual(2, len(lines))
        for line in lines:
            json.loads(line)

    def test_events_keep_their_order(self):
        with events.EventLog(self.path) as log:
            for tick in range(5):
                log.birth(tick=tick, identity=str(tick), generation=1, parent=None)
        ticks = [e['tick'] for e in events.read(self.path)]
        self.assertEqual([0, 1, 2, 3, 4], ticks)

    def test_every_event_records_its_kind_and_tick(self):
        with events.EventLog(self.path) as log:
            log.birth(tick=1, identity='0.1', generation=2, parent='0')
            log.death(tick=1, identity='0', cause='crashed', age=3, generation=1)
            log.birth_failed(tick=1, parent='0', reason='unparseable')
            log.snapshot(tick=1, population=5, food=100)
        kinds = [e['kind'] for e in events.read(self.path)]
        self.assertEqual(['birth', 'death', 'birth_failed', 'snapshot'], kinds)
        for event in events.read(self.path):
            self.assertIn('tick', event)

    def test_log_is_append_only_across_reopens(self):
        with events.EventLog(self.path) as log:
            log.snapshot(tick=1, population=1, food=1)
        with events.EventLog(self.path) as log:
            log.snapshot(tick=2, population=2, food=2)
        self.assertEqual(2, len(list(events.read(self.path))))

    def test_reading_a_missing_log_gives_nothing(self):
        self.assertEqual([], list(events.read(os.path.join(self.root, 'nope.jsonl'))))

    def test_a_truncated_final_line_is_skipped_not_fatal(self):
        """A run killed mid-write must still be analysable."""
        with events.EventLog(self.path) as log:
            log.snapshot(tick=1, population=1, food=1)
        with open(self.path, 'a', encoding='utf-8') as handle:
            handle.write('{"kind": "snapshot", "tick": 2, "popula')
        self.assertEqual(1, len(list(events.read(self.path))))


class TestReplay(EventTestCase):
    """Reconstructing a run from its log, with no processes involved."""

    def write_run(self):
        """Writes a small three-tick run to replay."""
        with events.EventLog(self.path) as log:
            log.birth(tick=0, identity='0', generation=1, parent=None)
            log.birth(tick=0, identity='1', generation=1, parent=None)
            log.snapshot(tick=0, population=2, food=100)
            log.birth(tick=1, identity='0.0', generation=2, parent='0')
            log.snapshot(tick=1, population=3, food=90)
            log.death(tick=2, identity='1', cause='crashed', age=2, generation=1)
            log.birth_failed(tick=2, parent='0', reason='unparseable')
            log.snapshot(tick=2, population=2, food=85)

    def test_population_over_time_is_recovered(self):
        self.write_run()
        replay = events.Replay(self.path)
        self.assertEqual([2, 3, 2], replay.population_over_time)

    def test_food_over_time_is_recovered(self):
        self.write_run()
        self.assertEqual([100, 90, 85], events.Replay(self.path).food_over_time)

    def test_causes_of_death_are_counted(self):
        self.write_run()
        self.assertEqual({'crashed': 1}, events.Replay(self.path).deaths)

    def test_births_and_failed_births_are_counted(self):
        self.write_run()
        replay = events.Replay(self.path)
        self.assertEqual(3, replay.births)
        self.assertEqual(1, replay.failed_births)

    def test_deepest_generation_is_recovered(self):
        self.write_run()
        self.assertEqual(2, events.Replay(self.path).deepest_generation)

    def test_birth_failure_rate_is_reported(self):
        """The measurement that matters: how brittle the substrate is."""
        self.write_run()
        replay = events.Replay(self.path)
        self.assertAlmostEqual(1 / 4, replay.birth_failure_rate, places=5)

    def test_living_at_a_tick_is_recoverable(self):
        """Phase 4 needs to know who was alive when, without re-running."""
        self.write_run()
        replay = events.Replay(self.path)
        self.assertEqual({'0', '1'}, replay.living_at(0))
        self.assertEqual({'0', '1', '0.0'}, replay.living_at(1))
        self.assertEqual({'0', '0.0'}, replay.living_at(2))

    def test_replaying_an_empty_log_does_not_crash(self):
        replay = events.Replay(self.path)
        self.assertEqual([], replay.population_over_time)
        self.assertEqual(0, replay.births)


class TestManifest(EventTestCase):

    def test_records_everything_needed_to_rerun(self):
        path = os.path.join(self.root, 'manifest.json')
        events.write_manifest(path, seed=42, ticks=50, founders=10,
                              regrowth=400, max_processes=500, timeout=0.5,
                              summary={'births': 3})
        with open(path, encoding='utf-8') as handle:
            manifest = json.load(handle)
        for field in ('seed', 'ticks', 'founders', 'regrowth', 'max_processes',
                      'timeout', 'git_sha', 'python_version', 'summary'):
            self.assertIn(field, manifest, f'manifest is missing {field}')
        self.assertEqual(42, manifest['seed'])

    def test_records_that_timing_is_not_reproducible(self):
        """A reader must not assume a rerun gives identical results, because
        process scheduling decides who eats first."""
        path = os.path.join(self.root, 'manifest.json')
        events.write_manifest(path, seed=1, ticks=1, founders=1, regrowth=1,
                              max_processes=1, timeout=0.5, summary={})
        with open(path, encoding='utf-8') as handle:
            self.assertIn('reproducibility', json.load(handle))

    def test_a_manifest_round_trips(self):
        path = os.path.join(self.root, 'manifest.json')
        events.write_manifest(path, seed=7, ticks=3, founders=2, regrowth=9,
                              max_processes=11, timeout=0.25, summary={})
        loaded = events.read_manifest(path)
        self.assertEqual(7, loaded['seed'])
        self.assertEqual(11, loaded['max_processes'])


if __name__ == '__main__':
    unittest.main()
