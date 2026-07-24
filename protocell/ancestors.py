""" ancestors.py - the two starting pools.

Two seeds, so we can later watch both directions. The working pool lives and
divides; the question for it is whether it degrades. The minimal pool cannot feed
itself and dies; the question for it is whether anything ever builds it up.

The proteins are deliberately plain and readable. They use only the generic cell
API (eat, divide, energy, registers), nothing task-specific.
"""

from protocell.protein import Protein

# Eat from the environment, more when low on energy; a crude metabolism.
_METABOLISM = '''
def protein(cell, env):
    hunger = 40 - cell.energy
    cell.eat(env, 3 + max(0, hunger) // 4)
'''

# Divide once there is energy to spare.
_DIVISION = '''
def protein(cell, env):
    if cell.energy > 30:
        cell.divide()
'''

# Does nothing useful: the cell that carries only this cannot feed and starves.
_INERT = '''
def protein(cell, env):
    cell.registers[0] = cell.registers[0]
'''


def working_pool():
    """ :return: A pool that sustains and divides a cell """
    return [Protein(_METABOLISM), Protein(_DIVISION)]


def minimal_pool():
    """ :return: A pool too poor to keep a cell alive """
    return [Protein(_INERT)]
