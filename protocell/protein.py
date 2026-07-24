""" protein.py - one protein: a function that acts on a cell.

A protein is Python source defining `protein(cell, env)`. It reads and writes the
cell's state (energy, registers) and the environment (food), the way a real
protein reads and changes the chemistry around it. What it can do is deliberately
generic: eat, divide, and compute with the cell's registers. Nothing task-
specific is handed to it.

A protein that cannot be compiled, or does not define `protein`, is *misfolded*:
it is inert and never runs. A protein that raises while running simply has no
effect that tick, the way a protein can fail on some substrates and not others.
Neither can crash the cell, so mutation is survivable at the pool level.
"""

import ast
import contextlib
import io


class Protein:  # pylint: disable=too-few-public-methods
    """ A callable built from source, or inert if the source does not fold. """

    def __init__(self, source):
        self.source = source
        self._function = None
        self.folded = self._fold()

    def _fold(self):
        """ Compiles the source once. :return: True if it yields protein() """
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                namespace = {}
                exec(compile(ast.parse(self.source), '<protein>', 'exec'),  # pylint: disable=exec-used
                     namespace)
        except Exception:  # pylint: disable=broad-except
            return False
        function = namespace.get('protein')
        if not callable(function):
            return False
        self._function = function
        return True

    def execute(self, cell, env):
        """ Runs the protein on a cell and environment.

            A misfolded protein does nothing. A runtime error is swallowed: the
            protein simply had no effect this tick.
        :return: None
        """
        if not self.folded:
            return
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self._function(cell, env)
        except Exception:  # pylint: disable=broad-except
            pass
