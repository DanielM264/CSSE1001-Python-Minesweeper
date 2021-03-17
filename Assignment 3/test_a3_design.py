"""
Tests for CSSE1001 / 7030 Assignment 3
"""

__author__ = "Steven Summers"

import functools
import inspect
import tkinter as tk
import _tkinter
import sys

from pathlib import Path

from testrunner import AttributeGuesser, OrderedTestCase, TestMaster, skipIfFailed

IMPORTED_MODULES = set(sys.modules)


class MockTk(tk.Tk):
    _called = 0

    def mainloop(self, n=0):
        MockTk._called += 1


tk.Tk = MockTk


class A3:
    BoardModel: ...
    BoardView: ...
    PokemonGame: ...
    StatusBar: ...
    ImageBoardView: ...


class TestA3(OrderedTestCase):
    a3: A3


class TestDesign(TestA3):
    def test_clean_import(self):
        """ test no prints on import """
        self.assertIsCleanImport(self.a3, msg="You should not be printing on import for a3.py")

    def test_classes_and_functions_defined(self):
        """ test all specified classes and functions defined correctly """
        a3 = AttributeGuesser.get_wrapped_object(self.a3)

        self.aggregate(self.assertDefined, a3, 'TASK_ONE')
        if self.aggregate(self.assertClassDefined, a3, 'BoardModel'):
            self.aggregate(self.assertFunctionDefined, a3.BoardModel, '__init__', 3)

        if self.aggregate(self.assertClassDefined, a3, 'BoardView'):
            self.aggregate(self.assertFunctionDefined, a3.BoardView, '__init__', 6)
            self.aggregate(self.assertIsSubclass, a3.BoardView, tk.Canvas, tag='BoardView.Canvas')

        if self.aggregate(self.assertClassDefined, a3, 'PokemonGame', tag='PokemonGame'):
            self.aggregate(self.assertFunctionDefined, a3.PokemonGame, '__init__', 5)

        if self.aggregate(self.assertDefined, a3, 'TASK_TWO'):
            if self.aggregate(self.assertClassDefined, a3, 'StatusBar'):
                self.aggregate(self.assertIsSubclass, a3.StatusBar, tk.Frame)

            if self.aggregate(self.assertClassDefined, a3, 'ImageBoardView'):
                self.aggregate(self.assertIsSubclass, a3.ImageBoardView, a3.BoardView)

        self.aggregate(self.assertFunctionDefined, a3, 'main', 0)
        self.aggregate_tests()

    def test_doc_strings(self):
        """ test all classes and functions have documentation strings """
        a3 = AttributeGuesser.get_wrapped_object(self.a3)
        ignored = frozenset(('__str__', '__repr__'))
        for func_name, func in inspect.getmembers(a3, predicate=inspect.isfunction):
            if not self._is_a3_object(func):
                continue

            self.aggregate(self.assertDocString, func)

        for cls_name, cls in inspect.getmembers(a3, predicate=inspect.isclass):
            if not self._is_a3_object(cls):
                continue

            self.aggregate(self.assertDocString, cls)
            defined = vars(cls)
            for func_name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
                if func_name not in ignored and func_name in defined:
                    self.aggregate(self.assertDocString, func)

        self.aggregate_tests()

    def _is_a3_object(self, obj):
        """ Check if the given object was defined in a3.py """
        try:
            file = inspect.getfile(obj)
            return file == self.a3.__file__
        except TypeError:  # caused by trying to get the file of a builtin
            return False

    def test_imports(self):
        """ test only single file """
        path = Path(__file__).parent.resolve()
        new_imports = [(name, Path(sys.modules[name].__file__).parent)
                       for name in sys.modules.keys() - IMPORTED_MODULES - {'a3'}
                       if hasattr(sys.modules[name], '__file__')]
        relative_imports = [name for name, p in new_imports if p == path]
        if relative_imports:
            self.fail(f'You have imported {", ".join(sorted(relative_imports))} '
                      'but you can only submit a single a3.py file.'
                      '\nIf you believe this is an error please contact a tutor either with a Piazza question '
                      'or in a practical.')


class TestTkinter(OrderedTestCase):
    def test_no_mainloop_on_import(self):
        """ test tkinter.Tk.mainloop was not called on import """
        if tk._default_root is not None and tk._default_root._called != 0:
            self.fail('tkinter.Tk.mainloop was called on import. You should have a `main` function for this')


class TestTkinterApp(OrderedTestCase):
    @staticmethod
    def _pump_tk_events(root: tk.Tk):
        while root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass

    @skipIfFailed(TestDesign, TestDesign.test_classes_and_functions_defined.__name__, tag='PokemonGame')
    @skipIfFailed(TestDesign, TestDesign.test_classes_and_functions_defined.__name__, tag='BoardView.Canvas')
    def test_board_view_bindings(self):
        """ test required Button 1, 2, 3 events have been bound """
        _new = self.a3.BoardView.__new__
        board_view: tk.Canvas = None

        @functools.wraps(_new)
        def _board_view_new_hook(cls_, *_args, **_kwargs):
            nonlocal board_view
            board_view = _new(cls_)
            return board_view

        self.a3.BoardView.__new__ = _board_view_new_hook

        root = tk.Tk()
        _app = self.a3.PokemonGame(root)
        if board_view is None:
            self.fail('BoardView has not been instantiated in PokemonGame')

        # self._pump_tk_events(root)
        expected = {'<Button-2>', '<Button-3>', '<Button-1>'}
        actual = set(board_view.bind())
        missing = expected - actual
        if missing:
            self.fail(f'The following events have not been bound {missing}')


def main():
    test_cases = [
        TestDesign,
        TestTkinter,
        TestTkinterApp
    ]

    master = TestMaster(max_diff=None,
                        suppress_stdout=True,
                        timeout=1,
                        include_no_print=True,
                        scripts=[
                            ('a3', 'a3.py')
                        ])
    master.run(test_cases)


if __name__ == '__main__':
    main()
