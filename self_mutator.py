""" self_mutator.py - a mutation algorithm. """

from __future__ import print_function

import argparse
import os
import random
import string
import subprocess
import time
import sys
import ctypes
from ctypes import wintypes
import logging
import logging.handlers
import tempfile

import log_server

# From http://code.activestate.com/recipes/577794-win32-named-mutex-class-for-system-wide-mutex/
# Windows only - need a linux version of this.  Perhaps fnctl.flock?
# Named mutex handling (for Win32).
# Create ctypes wrapper for Win32 functions we need, with correct argument/return types
_CREATE_MUTEX = ctypes.windll.kernel32.CreateMutexA
_CREATE_MUTEX.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCSTR]
_CREATE_MUTEX.restype = wintypes.HANDLE

_WAIT_FOR_SINGLE_OBJECT = ctypes.windll.kernel32.WaitForSingleObject
_WAIT_FOR_SINGLE_OBJECT.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_WAIT_FOR_SINGLE_OBJECT.restype = wintypes.DWORD

_RELEASE_MUTEX = ctypes.windll.kernel32.ReleaseMutex
_RELEASE_MUTEX.argtypes = [wintypes.HANDLE]
_RELEASE_MUTEX.restype = wintypes.BOOL

_CLOSE_HANDLE = ctypes.windll.kernel32.CloseHandle
_CLOSE_HANDLE.argtypes = [wintypes.HANDLE]
_CLOSE_HANDLE.restype = wintypes.BOOL


class NamedMutex(object):
    """A named, system-wide mutex that can be acquired and released."""

    def __init__(self, name, acquired=False):
        """Create named mutex with given name, also acquiring mutex if acquired is True.
        Mutex names are case sensitive, and a filename (with backslashes in it) is not a
        valid mutex name. Raises WindowsError on error.

        """
        self.name = name
        self.acquired = acquired
        ret = _CREATE_MUTEX(None, False, name)
        if not ret:
            raise ctypes.WinError()
        self.handle = ret
        if acquired:
            self.acquire()

    def acquire(self, timeout=None):
        """Acquire ownership of the mutex, returning True if acquired. If a timeout
        is specified, it will wait a maximum of timeout seconds to acquire the mutex,
        returning True if acquired, False on timeout. Raises WindowsError on error.

        """
        if timeout is None:
            # Wait forever (INFINITE)
            timeout = 0xFFFFFFFF
        else:
            timeout = int(round(timeout * 1000))
        ret = _WAIT_FOR_SINGLE_OBJECT(self.handle, timeout)
        if ret in (0, 0x80):
            # Note that this doesn't distinguish between normally acquired (0) and
            # acquired due to another owning process terminating without releasing (0x80)
            self.acquired = True
            return True
        elif ret == 0x102:
            # Timeout
            self.acquired = False
            return False
        else:
            # Waiting failed
            raise ctypes.WinError()

    def release(self):
        """Relase an acquired mutex. Raises WindowsError on error."""
        ret = _RELEASE_MUTEX(self.handle)
        if not ret:
            raise ctypes.WinError()
        self.acquired = False

    def close(self):
        """Close the mutex and release the handle."""
        if self.handle is None:
            # Already closed
            return
        ret = _CLOSE_HANDLE(self.handle)
        if not ret:
            raise ctypes.WinError()
        self.handle = None

    __del__ = close

    def __repr__(self):
        """Return the Python representation of this mutex."""
        return '{0}({1!r}, acquired={2})'.format(
            self.__class__.__name__, self.name, self.acquired)

    __str__ = __repr__

    # Make it a context manager so it can be used with the "with" statement
    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class SelfMutator(object):
    """ This is a creature that can duplicate itself with errors. """
    # pylint: disable=too-many-instance-attributes
    # Eight is fine here.

    reproduction_chance = .9    # Each year, we have this chance to have offspring
    hunger_energy = 5           # If our energy is below this, we're hungry and will search for food

    def __init__(self, identity, max_gen_depth, should_reproduce=True):
        self._identity = identity
        self.max_gen_depth = max_gen_depth
        print('max_depth: %d, current_gen_depth: %d', self.max_gen_depth, self.generation)
        if self.generation > self.max_gen_depth:
            raise Exception('Exiting: beyond max generation depth...')
        self._age = 0
        self._energy = 40
        self._alive = True
        self._should_reproduce = should_reproduce
        self.offspring_count = 0

    def live(self, time_to_live):
        """
        :param time_to_live: The number of units of time to live for.
        :return: None
        """
        maximum_age = 100  # Die of old age
        minimum_energy = 0  # If our energy gets below this, we die

        if time_to_live == 0:
            time_to_live = maximum_age

        for _ in range(time_to_live):
            if self.alive:
                if self._should_reproduce:  # If we're unit testing, don't sleep
                    time.sleep(0.25)
                self._age += 1
                self._energy -= 1
                logging.debug('I am %d years old.', self._age)
                if self._age >= maximum_age:
                    self.die('old_age')
                elif self._energy <= minimum_energy:
                    self.die('hunger')
                elif self.is_hungry:
                    logging.debug('I am hungry: %d', self.energy)
                    self.eat(SelfMutator.hunger_energy - self.energy)

                if self.can_reproduce:
                    if random.random() < SelfMutator.reproduction_chance:
                        self.reproduce()
                else:
                    if not self.is_hungry:
                        self.farm((self.energy - SelfMutator.hunger_energy) + 2)

    def reproduce(self):
        """ Copies this to a child with flawed copy
        :return: None
        """
        child = tempfile.NamedTemporaryFile('w',
                                            prefix=str(self.generation) + '-',
                                            suffix='.py',
                                            dir='.',
                                            delete=False)
        if self._should_reproduce:
            logging.info('Reproducing to %s...', child.name)
            with open(__file__) as original:
                child.write(self._flawed_copy(original.read()))
            child.close()
            detached_process = 0x00000008 # Windows only?
            self.farm(1 / SelfMutator.reproduction_chance)
            cmd = ['python', child.name, '--maxgen', self.max_gen_depth, '--id', '%s.%d' % (self.identity, self.offspring_count)]
            logging.info('executing %s', ' '.join(cmd))
            subprocess.Popen(cmd, close_fds=True, creationflags=detached_process)
            self.offspring_count += 1
        else:
            logging.debug('Would reproduce, but just testing...')

    def die(self, reason):
        """
        :param reason: The reason for the death (hunger, old age)
        :return: None
        """
        self._alive = False
        logging.error('dying because of %s', reason)
        # Communicate with child.py here?
        # sys.exit(0) # if not in a unit test

    @property
    def filename(self):
        """
        :return: The filename of this creature
        """
        return __file__

    @property
    def identity(self):
        """
        :return: UUID of this creature
        """
        return self._identity

    @property
    def age(self):
        """
        :return: Age of creature
        """
        return self._age

    @property
    def energy(self):
        """
        :return: Energy (amount of food in stomach, hunger)
        """
        return self._energy

    @energy.setter
    def energy(self, value):
        """
        :param value: Set the energy to this value
        :return: None
        """
        self._energy = value

    @property
    def can_farm(self):
        """
        :return: True if age < retirement age
        """
        retirement_age = 90  # Stop farming, just eat
        return self.age < retirement_age

    @property
    def generation(self):
        """
        :return: How many generations since first creature
        """
        return len(self._identity.split('.'))

    @property
    def can_reproduce(self):
        """
        :return: True if we can reproduce right now
        """
        start_reproducing = 18
        stop_reproducing = 40
        can = start_reproducing <= self.age <= stop_reproducing
        can = can and not self.is_hungry
        return can

    @property
    def is_hungry(self):
        """
        :return: True if hungry (energy is low)
        """
        return self.energy < SelfMutator.hunger_energy

    def eat(self, amount):
        """
        Causes creature to eat, increasing energy, reducing shared food supply.
        If others are at the pool, we fail to eat, nothing happens.
        :return: True if successful
        :param amount: Always positive - how much do we want to eat?  If not enough, nothing happens

        """
        if self.adjust_food_source(-amount):
            self.energy += amount
            logging.debug('ate %d', amount)
            return True
        else:
            logging.debug('failed to eat %d', amount)
            return False

    def farm(self, amount):
        """
        Add food to the pool - if others are at the pool, we fail to farm, nothing happens.
        It costs energy to successfully farm.
        :return: True if successful
        :param amount: Always positive - how much do we want to farm?

        """
        if self.can_farm:
            if self.adjust_food_source(amount):
                # self.energy -= amount
                logging.debug('farmed for %d', amount)
                return True
            else:
                logging.debug('failed to farm for %d', amount)
                return False
        else:
            logging.debug('cannot farm any more - too old?')

    @staticmethod
    def adjust_food_source(amount):
        """
        Adds or removes food from the global food pool.
        :param amount: Positive to add food (farming), negative to remove food (eating)
        :return:
        """
        food_path = 'food.txt'
        if amount < 0: # We try harder to eat than farm
            timeout = 0.50
        else:
            timeout = 0.25
        mutex = NamedMutex(b'self_mutator_lock')
        if mutex.acquire(timeout=timeout):
            logging.debug('acquired lock! amount: %d', amount)
            if os.path.exists(food_path):
                with open(food_path, 'r+') as food:
                    food.seek(0)
                    data = food.read()
                    logging.debug('data: %s', data)
                    if data.isnumeric():
                        available_food = int(data)
                        logging.debug('available_food: %s', available_food)
                    else:
                        logging.debug('not numeric')
                        available_food = 10
                    available_food += amount
                    if available_food >= 0:
                        data_to_write = str(available_food)
                        logging.debug('data_to_write: %s', data_to_write)
                        food.seek(0)
                        food.write(data_to_write)
                        food.truncate()
                        return True
                    else:
                        logging.debug('not enough food!')
                        return False
            else:
                logging.debug('%s did not exist, creating it with 10...', food_path)
                with open(food_path, 'w') as food:
                    food.write('10')
                return True
        else:
            logging.debug('failed to acquire lock!')
            return False

    @property
    def alive(self):
        """
        :return: True if alive
        """
        return self._alive and not os.path.exists('killall')

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

    @staticmethod
    def _flawed_copy(source, mutation_weights=None, use_keywords=True):
        """ Copies source and returns it with flaws according to the weighted
            flaws passed in.
            source : list of characters
        """
        if mutation_weights is None:
            mutation_weights = {'prepend':20, 'overwrite':20, 'insert':20, 'delete':20, 'append':20}

        defect = SelfMutator._weighted_choice([('prepend', mutation_weights['prepend']),
                                               ('overwrite', mutation_weights['overwrite']),
                                               ('insert', mutation_weights['insert']),
                                               ('delete', mutation_weights['delete']),
                                               ('append', mutation_weights['append'])])

        if use_keywords:
            python_keywords = [' and ', ' del ', ' from ', ' not ', ' while ', ' as ', ' elif ',
                               ' global ', ' or ', ' with ', ' assert ', ' else ', ' if ',
                               ' pass ', ' yield ', ' break ', ' except ', ' import ', ' print ',
                               ' class ', ' exec ', ' in ', ' raise ', ' continue ', ' finally ',
                               ' is ', ' return ', ' def ', ' for ', ' lambda ', ' try ']
        else:
            python_keywords = []

        mutation = random.choice(list(string.ascii_letters) +
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
            elif defect in ('overwrite', 'insert', 'delete'):
                mutation_location = random.randint(0, len(source) - 1)
                if defect == 'overwrite':
                    source = source[:mutation_location] + mutation + source[mutation_location + 1:]
                elif defect == 'insert':
                    source = source[:mutation_location] + mutation + source[mutation_location:]
                elif defect == 'delete':
                    source = source[:mutation_location] + source[mutation_location + 1:]
                else:
                    raise Exception('Unsupported defect type: %s' % defect)
            else:
                raise 'Invalid defect: %s' % defect
        return source


def setup_logging(identity):
    """
    Set up logging
    :return: None
    """
    if len(identity.split('.')) == 1:
        print('Setting up ')
        thread1 = log_server.LogServerThread(1, "LogServerThread", 1)
        thread1.start()

    # set up client logging - this should be done for everyone
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)
    socket_handler = logging.handlers.SocketHandler('localhost',
                                                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    # don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    root_logger.addHandler(socket_handler)

    # Now, we can log to the root logger, or any other logger. First the root...
    logging.debug('Logging for %s initialized.', identity)


def main(arguments):
    """ Entry point for command line. """
    major = 0
    minor = 1
    micro = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help="Unique identifier for this creature (x.y.z...)", type=str,
                        default='')
    parser.add_argument("--seed", help="Random seed", type=float, default=time.time())
    parser.add_argument("--maxgen", help="Maximum generations", type=int, default=3)
    parser.add_argument("--reproduce", help="Reproduce normally, default", dest='reproduce',
                        action='store_true')
    parser.add_argument("--no-reproduce", help="Do not actually reproduce (for testing)",
                        dest='reproduce', action='store_false')
    parser.set_defaults(reproduce=True)
    args = parser.parse_args(arguments)

    setup_logging(args.id)
    logging.info('self_mutator %d.%d.%d', major, minor, micro)

    logging.info('args: %s', args)
    random.seed(args.seed)

    creature = SelfMutator(args.id, args.maxgen, should_reproduce=args.reproduce)
    creature.live(0)


if __name__ == "__main__":
    main(sys.argv[1:])
