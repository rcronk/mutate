""" cell.py - a cell run by a pool of proteins.

The cell owns state a protein cannot mutate away: its energy, its age, and the
rules of metabolism and death. The proteins own behaviour: each tick they run in
random order and their combined effect feeds the cell and decides whether it
divides. This split matters for the same reason it did in the creatures work: if
proteins owned the death rules, evolution would delete them.

The API a protein may call is small and generic: read `energy` and `registers`,
`eat` food from the environment, write `registers`, and `divide`. A protein
cannot set its own energy or cancel its own death directly.
"""

STARTING_ENERGY = 20
MAX_ENERGY = 60
METABOLIC_COST = 1
MAX_AGE = 60
DIVISION_THRESHOLD = 25
DIVISION_COST = 10
REGISTERS = 4


class Cell:
    """ A living cell: a protein pool plus engine-owned state. """

    def __init__(self, proteins, *, energy=STARTING_ENERGY):
        self.proteins = list(proteins)
        self.energy = energy
        self.age = 0
        self.alive = True
        self.registers = [0] * REGISTERS
        self._wants_division = False

    # --- API proteins may call ---

    def eat(self, env, amount):
        """ Takes up to `amount` food from the environment, turning it to energy.
        :return: Energy actually gained
        """
        wanted = max(0, int(amount))
        gained = env.request(min(wanted, MAX_ENERGY - self.energy))
        self.energy += gained
        return gained

    def divide(self):
        """ Requests division; granted after the tick if energy allows. """
        self._wants_division = True

    # --- engine-owned, proteins cannot reach these ---

    def metabolize(self):
        """ Pays the per-tick energy cost, ages, and checks for death. """
        self.energy -= METABOLIC_COST
        self.age += 1
        if self.energy <= 0 or self.age >= MAX_AGE:
            self.alive = False

    def spawn_daughter(self, mutate=None):
        """ If division was requested and affordable, produces a daughter.

            The daughter inherits a copy of the pool (optionally mutated) and an
            endowment of energy, both paid for by the parent.
        :param mutate: Optional callable from a protein list to a new one
        :return: A new Cell, or None
        """
        if not (self._wants_division and self.energy > DIVISION_THRESHOLD):
            self._wants_division = False
            return None
        self._wants_division = False
        self.energy -= DIVISION_COST
        endowment = self.energy // 2
        self.energy -= endowment
        proteins = list(self.proteins)
        if mutate is not None:
            proteins = mutate(proteins)
        return Cell(proteins, energy=endowment)

    def dump(self):
        """ :return: The pool as readable source, so a run can be inspected """
        return '\n'.join(protein.source.strip() for protein in self.proteins)
