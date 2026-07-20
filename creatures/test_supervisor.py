"""Tests for the forked supervisor.

Written before the implementation.

Each creature is a real OS process that lives its whole life, blocking briefly
each tick to be asked for a decision. One fork per creature, not per tick.

Byte-identical reruns are explicitly not a goal, because process scheduling is
nondeterministic. Genetics are reproducible; timing is not.

The parts most worth testing are the ones that stalled this work in 2017: the
concurrency cap, orphaned processes, and creatures that never answer. A mutant
containing `while True` is not hypothetical, it is inevitable.
"""

import os
import signal
import time
import unittest

from creatures import genome, lifecycle, supervisor


def alive(pid):
    """:return: True if the process exists and has not been reaped."""
    try:
        finished, _ = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return False
    return finished == 0


class SupervisorTestCase(unittest.TestCase):
    """Every test tears its processes down, so a failure cannot leak children."""

    def setUp(self):
        self.supervisors = []

    def tearDown(self):
        for sup in self.supervisors:
            sup.shutdown()

    def make(self, **kwargs):
        kwargs.setdefault('regrowth', 400)
        kwargs.setdefault('max_processes', 50)
        sup = supervisor.Supervisor(**kwargs)
        self.supervisors.append(sup)
        return sup


class TestSpawning(SupervisorTestCase):

    def test_spawning_creates_a_real_process(self):
        sup = self.make()
        creature = sup.spawn(genome.Genome.founder(seed=1))
        self.assertNotEqual(os.getpid(), creature.pid)
        self.assertTrue(alive(creature.pid))

    def test_founders_are_spawned_on_start(self):
        sup = self.make()
        sup.start(founders=3, seed=1)
        self.assertEqual(3, len(sup.living))

    def test_a_creature_answers_a_tick(self):
        sup = self.make()
        creature = sup.spawn(genome.Genome.founder(seed=1))
        decision = sup.ask(creature)
        self.assertIn('eat', decision)
        self.assertIn('reproduce', decision)

    def test_shutdown_leaves_no_processes_behind(self):
        sup = self.make()
        sup.start(founders=5, seed=1)
        pids = [c.pid for c in sup.living]
        sup.shutdown()
        time.sleep(0.2)
        for pid in pids:
            with self.subTest(pid=pid):
                self.assertFalse(alive(pid), 'orphaned process left running')


class TestTicking(SupervisorTestCase):

    def test_a_tick_ages_every_creature(self):
        sup = self.make()
        sup.start(founders=3, seed=1)
        sup.tick()
        for creature in sup.living:
            self.assertEqual(1, creature.life.age)

    def test_food_is_consumed_from_the_shared_pool(self):
        sup = self.make(regrowth=0, food=100)
        sup.start(founders=3, seed=1)
        sup.tick()
        self.assertLess(sup.world.food, 100)

    def test_creatures_die_and_are_reaped(self):
        sup = self.make(max_age=2)
        sup.start(founders=3, seed=1)
        pids = [c.pid for c in sup.living]
        for _ in range(3):
            sup.tick()
        self.assertEqual(0, len(sup.living))
        time.sleep(0.2)
        for pid in pids:
            with self.subTest(pid=pid):
                self.assertFalse(alive(pid))

    def test_deaths_are_recorded_with_a_cause(self):
        sup = self.make(max_age=2)
        sup.start(founders=3, seed=1)
        for _ in range(3):
            sup.tick()
        self.assertEqual(3, sup.deaths['old_age'])

    def test_population_reproduces(self):
        sup = self.make()
        sup.start(founders=5, seed=1)
        for _ in range(6):
            sup.tick()
        self.assertGreater(sup.births, 0)


class TestMisbehavingCreatures(SupervisorTestCase):
    """The failure modes that only appear once mutants are running."""

    def test_a_creature_that_crashes_is_killed_and_recorded(self):
        sup = self.make()
        broken = genome.Genome('def act(age, fuel, max_fuel):\n    raise ValueError("x")\n',
                               seed=1, identity='0', generation=1)
        creature = sup.spawn(broken)
        sup.tick()
        self.assertEqual(1, sup.deaths['crashed'])
        time.sleep(0.2)
        self.assertFalse(alive(creature.pid))

    def test_a_creature_that_hangs_is_killed_and_recorded_as_timeout(self):
        """A mutant containing `while True` is inevitable. It must not stall
        the whole run, and it must be distinguishable from a crash."""
        sup = self.make(timeout=0.25)
        hung = genome.Genome('def act(age, fuel, max_fuel):\n'
                             '    while True:\n        pass\n',
                             seed=1, identity='0', generation=1)
        creature = sup.spawn(hung)
        started = time.monotonic()
        sup.tick()
        elapsed = time.monotonic() - started

        self.assertEqual(1, sup.deaths['timeout'])
        self.assertLess(elapsed, 5.0, 'the tick stalled instead of timing out')
        time.sleep(0.2)
        self.assertFalse(alive(creature.pid), 'hung process was not killed')

    def test_a_timeout_is_not_counted_as_a_crash(self):
        sup = self.make(timeout=0.25)
        sup.spawn(genome.Genome('def act(age, fuel, max_fuel):\n'
                                '    while True:\n        pass\n',
                                seed=1, identity='0', generation=1))
        sup.tick()
        self.assertEqual(0, sup.deaths['crashed'])

    def test_one_bad_creature_does_not_kill_the_others(self):
        """Process isolation is the whole reason for forking."""
        sup = self.make(timeout=0.25)
        sup.start(founders=3, seed=1)
        sup.spawn(genome.Genome('def act(age, fuel, max_fuel):\n'
                                '    while True:\n        pass\n',
                                seed=99, identity='x', generation=1))
        sup.tick()
        self.assertEqual(3, len(sup.living))


class TestConcurrencyCap(SupervisorTestCase):
    """The cap is a safety valve for the machine, not an ecological rule.
    Food is the limiter (see test_ecology.py)."""

    def test_the_cap_is_never_exceeded(self):
        sup = self.make(max_processes=8)
        sup.start(founders=5, seed=1)
        for _ in range(10):
            sup.tick()
            self.assertLessEqual(len(sup.living), 8)

    def test_hitting_the_cap_is_recorded_as_a_warning(self):
        """If this ever fires in a real run the food parameters were wrong and
        the results are contaminated by an artificial ceiling."""
        sup = self.make(max_processes=6)
        sup.start(founders=5, seed=1)
        for _ in range(10):
            sup.tick()
        self.assertGreater(sup.cap_hits, 0)

    def test_a_generous_cap_is_never_hit(self):
        sup = self.make(max_processes=500, regrowth=100)
        sup.start(founders=5, seed=1)
        for _ in range(10):
            sup.tick()
        self.assertEqual(0, sup.cap_hits)


class TestCleanShutdown(SupervisorTestCase):

    def test_shutdown_is_idempotent(self):
        sup = self.make()
        sup.start(founders=3, seed=1)
        sup.shutdown()
        sup.shutdown()

    def test_shutdown_works_from_a_context_manager(self):
        with supervisor.Supervisor(regrowth=400, max_processes=50) as sup:
            sup.start(founders=3, seed=1)
            pids = [c.pid for c in sup.living]
        time.sleep(0.2)
        for pid in pids:
            with self.subTest(pid=pid):
                self.assertFalse(alive(pid))

    def test_children_survive_a_signal_to_the_group_being_handled(self):
        """Children must not be killable out from under the supervisor by a
        stray signal to the process group, and must still be reapable."""
        sup = self.make()
        sup.start(founders=2, seed=1)
        for creature in sup.living:
            os.kill(creature.pid, signal.SIGTERM)
        time.sleep(0.2)
        sup.tick()
        self.assertEqual(0, len(sup.living))


class TestWorldWiring(SupervisorTestCase):

    def test_world_regrows_each_tick(self):
        sup = self.make(regrowth=50, food=0)
        sup.start(founders=0, seed=1)
        sup.tick()
        self.assertEqual(50, sup.world.food)

    def test_lifecycle_parameters_reach_the_creatures(self):
        sup = self.make(max_age=99)
        sup.start(founders=1, seed=1)
        self.assertEqual(99, sup.living[0].life.max_age)

    def test_world_is_a_lifecycle_world(self):
        self.assertIsInstance(self.make().world, lifecycle.World)


if __name__ == '__main__':
    unittest.main()
