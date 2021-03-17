__author__ = 'Steven Summers'
__version__ = ''

import argparse
import ctypes
import difflib
import importlib.util
import inspect
import io
import json
import re
import sys
import textwrap
import threading
import traceback
import unittest

from bdb import Bdb
from collections import OrderedDict
from enum import Enum, unique
from functools import wraps
from pathlib import Path
from timeit import default_timer as timer
from types import FunctionType, ModuleType, TracebackType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union


# GLOBALS TO EXCLUDE FILES IN TRACEBACK
__TEST_RUNNER = True

__all__ = [
    'AttributeGuesser',
    'OrderedTestCase',
    'RedirectStdIO',
    'TestCase',
    'TestMaster',
    'TestOutcome',
    'skipIfFailed',
    'timeout'
]

# DEFAULTS
DEFAULT_TIMEOUT = 0

# CONSTANTS
DIFF_OMITTED = '\nDiff is {} characters long. Set TestMaster(max_diff=None) to see it.'
DUPLICATE_MSG = 'AS ABOVE'
CLOSE_MATCH_CUTOFF = 0.8
TAB_SIZE = 4
BLOCK_WIDTH = 80
BLOCK_TEMPLATE = """\
/{0}\\
|{{:^{1}}}|
\\{0}/\
""".format('-' * (BLOCK_WIDTH - 2), BLOCK_WIDTH - 2)


class TestTimeout(Exception):
    pass


@unique
class TestOutcome(Enum):
    PASS = '+'
    FAIL = '-'
    SKIP = '?'


def skipIfFailed(test_case: Type[unittest.TestCase] = None, test_name: str = None, tag: str = None):
    """
    skipIfFail decorator allows you to skip entire TestCases or specific test
    cases if not all tests pass for a TestCase, or if a specific test case fails
    (skipped counts as a fail).

    At least one test method of TestCase1 needs to fail to skip
    @skipIfFailed(TestCase1)

    Skip if 'test_method' of TestCase1 failed
    @skipIfFailed(TestCase1, 'test_method')

    Skip if 'test_method' failed
    Can only be applied to method with class class containing a method
    named 'test_method'
    @skipIfFailed(test_name='test_method')
    """
    if test_case is None and test_name is None:
        raise RuntimeError("test_case and test_name for skipIfFailed can't both be None")

    if test_case is not None and test_name is not None and not hasattr(test_case, test_name):
        raise AttributeError(f'{test_case.__name__} has no method {test_name}')

    if tag is not None and test_name is None:
        raise RuntimeError("test_name must be specified if tag is provided for skipIfFailed")

    def decorator(obj: Union[Type[TestCase], Callable]):
        if hasattr(obj, '__skip_test__'):
            obj.__skip_test__ = obj.__skip_test__.copy()
            obj.__skip_test__.append((test_case, test_name, tag))
        else:
            obj.__skip_test__ = [(test_case, test_name, tag)]
        if not inspect.isfunction(obj):
            return obj

        @wraps(obj)
        def wrapper(*args, **kwargs):
            return obj(*args, **kwargs)

        return wrapper

    return decorator


def import_module(path: str) -> Tuple[Optional[ModuleType], Optional[Tuple[Type, Exception, TracebackType]]]:
    """
    Dynamically import the Python file (.py) at 'path' the
    """
    name = Path(path).stem
    if name in sys.modules:
        return sys.modules[name], None

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise ValueError(f'The path {path} is invalid. It should be a Python (.py) file path.')

    module = importlib.util.module_from_spec(spec)
    with RedirectStdIO(stdin=True, stdout=True) as stdio:
        try:
            spec.loader.exec_module(module)
            setattr(module, '__TEST_RUNNER_CLEAN_IMPORT', stdio.stdout == '')
            sys.modules[name] = module
            return module, None
        except:
            return None, sys.exc_info()


def _test_wrapper(test_func):
    """
    Runs the given test_func with a trace from TimeoutDetector
    exiting with TestTimeout exception if the test_func runs longer
    than the interval specified by the __time__ attribute
    """

    @wraps(test_func)
    def wrapper(self):
        interval = getattr(test_func, '__timeout__', 0) or \
                   getattr(self.__class__, '__timeout__', 0) or \
                   TestCase.timeout_interval

        error = None
        if interval <= 0:
            try:
                test_func(self)
            except (EOFError, SystemExit) as err:
                error = err
        else:
            with TimeoutDetector(interval):
                try:
                    test_func(self)
                except (TestTimeout, EOFError, SystemExit) as err:
                    error = err

            if isinstance(error, TestTimeout):
                self.skipTest(f'Function ran longer than {interval} second(s)')

        if isinstance(error, EOFError):
            raise EOFError("Got unexpected 'input' call").with_traceback(error.__traceback__)
        if isinstance(error, SystemExit):
            raise RuntimeError(
                "You should not be using exit, quit or sys.exit").with_traceback(error.__traceback__)

        return None

    return wrapper


def timeout(seconds: float = 0):
    """
    Decorator to apply __timeout__ attribute to a test method or TestCase
    """

    def timeout_decorator(test_obj):
        test_obj.__timeout__ = seconds
        return test_obj

    return timeout_decorator


def get_object_name(obj):
    return getattr(obj, '__qualname__', None) or getattr(obj, '__name__', None) or obj.__class__.__name__


class CachedIO(io.StringIO):
    """ Writes all read values and write values to stream """

    __slots__ = ['_stream']

    def __init__(self, stream):
        super().__init__()
        self._stream = stream

    def set_value(self, string):
        """ Set value to self without writing to stream """
        self.seek(0)
        self.truncate()
        super().write(string)
        self.seek(0)

    def write(self, s: str):
        res = super().write(s)
        self._stream.write(s)
        return res

    def readline(self, size: int = -1):
        res = super().readline(size)
        self._stream.write(res)
        return res


class RedirectStdIO:
    """
    Context manager to send stdin input and capture stdout and stderr

    Usage:
        with RedirectStdIO(stdin=True, stdout=True) as stdio:
            stdio.set_stdin('World!\n')
            inp = input('Hello')

        stdio.stdout == 'Hello'
        inp == 'World'
    """

    __slots__ = ['_sys_stdin', '_sys_stdout', '_sys_stderr',
                 '_stdin_stream', '_stdout_stream', '_stderr_stream',
                 '_stdinout_stream']

    def __init__(self, *, stdin: bool = False, stdout: bool = False,
                 stderr: bool = False, stdinout: bool = False):
        self._sys_stdin = None
        self._sys_stdout = None
        self._sys_stderr = None

        if stdinout:
            self._stdinout_stream = io.StringIO()
            self._stdin_stream = CachedIO(self._stdinout_stream)
            self._stdout_stream = CachedIO(self._stdinout_stream)

        else:
            self._stdinout_stream = None
            self._stdin_stream = io.StringIO() if stdin else None
            self._stdout_stream = io.StringIO() if stdout else None

        self._stderr_stream = io.StringIO() if stderr else None

    def __enter__(self):
        if self._stdin_stream is not None:
            self._sys_stdin = sys.stdin
            sys.stdin = self._stdin_stream

        if self._stdout_stream is not None:
            self._sys_stdout = sys.stdout
            sys.stdout = self._stdout_stream

        if self._stderr_stream is not None:
            self._sys_stderr = sys.stderr
            sys.stderr = self._stderr_stream

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._sys_stdin is not None:
            sys.stdin = self._sys_stdin

        if self._sys_stdout is not None:
            sys.stdout = self._sys_stdout

        if self._sys_stderr is not None:
            sys.stderr = self._sys_stderr

    @staticmethod
    def _read_stream(stream: io.StringIO) -> str:
        if stream is None:
            raise RuntimeError(
                'Attempt to read from a stream that has not been enabled')
        return stream.getvalue()

    @property
    def stdin(self):
        if self._stdin_stream is None:
            raise RuntimeError(
                f'stdin has not been set in {self.__class__.__name__}.__init__')
        pos = self._stdin_stream.tell()
        value = self._stdin_stream.read()
        self._stdin_stream.seek(pos)
        return value

    @stdin.setter
    def stdin(self, value: str):
        if self._stdin_stream is None:
            raise RuntimeError(
                f'stdin has not been set in {self.__class__.__name__}.__init__')

        if self._stdinout_stream is None:
            self._stdin_stream.seek(0)
            self._stdin_stream.truncate()
            self._stdin_stream.write(value)
            self._stdin_stream.seek(0)
        else:
            self._stdin_stream.set_value(value)

    @property
    def stdout(self) -> str:
        return self._read_stream(self._stdout_stream)

    @property
    def stderr(self) -> str:
        return self._read_stream(self._stderr_stream)

    @property
    def stdinout(self):
        return self._read_stream(self._stdinout_stream)


class RecursionDetector(Bdb):
    __slots__ = ['_stack']

    def __init__(self, *args):
        super().__init__(*args)
        self._stack = set()

    def do_clear(self, arg):
        pass

    def user_call(self, frame, argument_list):
        code = frame.f_code
        if code in self._stack:
            raise RecursionError
        self._stack.add(code)

    def user_return(self, frame, return_value):
        self._stack.remove(frame.f_code)


class TimeoutDetector:
    __slots__ = ['_interval', '_target_id', '_timer']

    def __init__(self, interval):
        self._interval = interval
        self._target_id = threading.current_thread().ident
        self._timer = threading.Timer(self._interval, self.stop)

    def __enter__(self):
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._timer.cancel()
        if exc_type is not TestTimeout:
            self._timer.cancel()

        return False

    def stop(self):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self._target_id),
                                                         ctypes.py_object(TestTimeout))
        if ret == 0:
            raise ValueError("Invalid thread ID {}".format(self._target_id))
        elif ret > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self._target_id), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


class AttributeGuesser:
    """
    Wrapper class for objects to return the attribute with the
    closest matching name. If fail is True then a TestCase.failureException
    is raised if no possible match is found.
    """

    __slots__ = ['__object', '__cache', '__fail']

    def __init__(self, obj: Any, fail: bool = True):
        """
        Parameters:
            obj: Object to wrap for guessing attributes of
            fail: if attribute can't be found
                raise exception iff True otherwise return None
        """
        if isinstance(obj, AttributeGuesser):
            obj = obj.__object
        self.__object = obj
        self.__cache = {}
        self.__fail = fail

    @classmethod
    def get_wrapped_object(cls, attr_guesser):
        if not isinstance(attr_guesser, AttributeGuesser):
            raise ValueError('attr_guesser must be an instance of AttributeGuesser')
        return object.__getattribute__(attr_guesser, '_AttributeGuesser__object')

    def __guess_attribute(self, obj: Any, name: str):
        attributes = dict(inspect.getmembers(obj))
        matches = difflib.get_close_matches(name, attributes, n=1)
        if not matches:
            if self.__fail:
                raise AttributeError(
                    f"Found no close match for '{get_object_name(obj)}.{name}'")
            return None
        return attributes[matches[0]]

    def __getattribute__(self, key: str):
        if key in ('_AttributeGuesser__object', '_AttributeGuesser__cache',
                   '_AttributeGuesser__guess_attribute', '_AttributeGuesser__fail'):
            return object.__getattribute__(self, key)
        return getattr(object.__getattribute__(self, '_AttributeGuesser__object'), key)

    def __getattr__(self, key: str):
        cache = self.__cache
        if key in cache:
            return cache[key]

        attr = self.__guess_attribute(self.__object, key)
        cache[key] = attr
        return attr

    def __setattr__(self, key: str, value: Any):
        if key in ('_AttributeGuesser__object', '_AttributeGuesser__cache',
                   '_AttributeGuesser__fail'):
            return object.__setattr__(self, key, value)
        return setattr(self.__object, key, value)

    def __repr__(self):
        return f'AttributeGuesser({self.__object!r})'


class TestLoader(unittest.TestLoader):
    """ Custom loader class to specify TestCase case order """

    def getTestCaseNames(self, testCaseClass: Type['TestCase']):
        """
        Override for unittest.TestLoad.getTestCaseNames
        Return a sorted sequence of method names found within testCaseClass
        """
        if issubclass(testCaseClass, OrderedTestCase):
            return testCaseClass.member_names
        return super().getTestCaseNames(testCaseClass)

    def loadTestCases(self, test_cases: List) -> unittest.TestSuite:
        """
        Params:
            test_cases List[Union[unittest.TestCase, Type[unittest.TestCase]]]
        """
        suite = unittest.TestSuite()

        for test_case in test_cases:
            if isinstance(test_case, unittest.TestCase):
                suite.addTest(test_case)
            else:
                suite.addTests(self.loadTestsFromTestCase(test_case))
        return suite


class _TestCaseMeta(type):
    """
    MetaClass to decorate all test methods with _timeout_wrapper and
    track test method definition order.
    """

    def __new__(mcs, name, bases, namespace):
        member_names = []
        prefix = TestLoader.testMethodPrefix
        for key, value in namespace.items():
            if key.startswith(prefix) and callable(value):
                member_names.append(key)
                namespace[key] = _test_wrapper(value)

        result = super().__new__(mcs, name, bases, namespace)
        result.member_names = member_names
        return result

    def __getattr__(cls, item):
        if item not in cls._modules:
            raise AttributeError(f"type object '{cls.__name__}'' has no attribute '{item}'")
        return cls._modules[item]


class TestCase(unittest.TestCase, metaclass=_TestCaseMeta):
    """
    Extends the unittest.TestCase defining additional assert methods.
    """
    timeout_interval = DEFAULT_TIMEOUT
    member_names: List[str]
    _modules: Dict[str, ModuleType] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aggregated_tests: List[Tuple[Optional[Exception], Optional[str]]] = []

    def __getattr__(self, item):
        if item in self._modules:
            return self._modules[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    @classmethod
    def register_module(cls, name: str, module: ModuleType):
        cls._modules[name] = module

    def assertIsCleanImport(self, module, msg=None):
        if not getattr(module, '__TEST_RUNNER_CLEAN_IMPORT', True):
            self.fail(msg)

    def assertMultiLineEqual(self, first: str, second: str, msg: Optional[str] = None, strip: bool = False):
        """
        unittest.TestCase.assertMultiLineEqual with strip keyword arg,
        if True then string is split on newlines with trailing
        whitespace striped and rejoined before
        """
        if strip:
            first = '\n'.join(s.rstrip() for s in first.splitlines()) + '\n'
            second = '\n'.join(s.rstrip() for s in second.splitlines()) + '\n'

        super().assertMultiLineEqual(first, second, msg=msg)

    def assertDefined(self, obj: Union[ModuleType, Type], name: str):
        if obj is None:
            self.fail(msg=f"Got 'None' when checking if '{name}' was defined for a type")
        obj_name = get_object_name(obj)
        if not hasattr(obj, name):
            self.fail(msg=f"'{obj_name}.{name}' is not defined correctly or not implemented")

    def assertFunctionDefined(self, obj: Union[ModuleType, Type], function_name: str, params: int):
        self.assertDefined(obj, function_name)
        obj_name = get_object_name(obj)
        func = getattr(obj, function_name)
        if not inspect.isfunction(func):
            if inspect.ismethoddescriptor(func):
                self.fail(msg=f"{obj_name}.{function_name} needs to be implemented")
            self.fail(msg=f"{obj_name}.{function_name} should be a function")
        num_params = len(inspect.signature(func).parameters)
        self.assertEqual(num_params, params,
                         msg=(f"'{function_name}' does not have the correct number of parameters, "
                              f"expected {params} found {num_params}"))

    def assertClassDefined(self, module: ModuleType, class_name: str):
        self.assertDefined(module, class_name)
        class_ = getattr(module, class_name)
        self.assertIs(inspect.isclass(class_), True, msg=f"{class_name} should be a class")

    def assertIsSubclass(self, sub_class: Type, parent_class: Type):
        self.assertIs(issubclass(sub_class, parent_class), True,
                      msg=f"'{sub_class}' is not a subclass of '{parent_class}'")

    def assertDocString(self, obj: Union[Type, Callable], name: str = None):
        if name is not None:
            # self.assertDefined(obj, name)
            obj = getattr(obj, name)

        if obj is None:
            self.fail(msg=f"Got 'None' when checking if docstring was defined for a type")

        # used over inspect.getdoc to require a doc string rather than inheriting it
        doc = getattr(obj, '__doc__', None)
        if doc is None or doc == '':
            self.fail(msg=f"Documentation string is required for '{obj.__qualname__}'")

    def assertListSimilar(self, actual: List, expected: List):
        # Try if sortable
        # try:
        #     s1 = sorted(actual)
        #     s2 = sorted(expected)
        #     self.assertListEqual(s1, s2)
        #     return
        # except TypeError:
        #     pass
        if type(actual) is not type(expected):
            self.fail(f"Got type '{type(actual).__name__}' expected type '{type(expected).__name__}'")

        # Fallback
        unexpected = list(actual)
        missing = []
        for elem in expected:
            try:
                unexpected.remove(elem)
            except ValueError:
                missing.append(elem)

        if unexpected or missing:
            msg = f'Lists are not similar\n\nActual: {actual}\nExpected: {expected}'
            if missing:
                msg += f"\nMissing: {missing}"
            if unexpected:
                msg += f"\nUnexpected: {unexpected}"
            self.fail(msg=msg)

    def assertIsNotRecursive(self, func, *args, **kwargs):
        detector = RecursionDetector()
        is_recursive = False
        try:
            detector.set_trace()
            func(*args, **kwargs)
        except RecursionError:
            is_recursive = True
        finally:
            sys.settrace(None)

        if is_recursive:
            self.fail(msg=f"{get_object_name(func)} should not be recursive")

    def aggregate(self, test_func: Callable, *args, tag: str = None, **kwargs):
        try:
            test_func(*args, **kwargs)
            self.aggregated_tests.append((None, tag))
            return True
        except (self.failureException, unittest.SkipTest) as failure:
            self.aggregated_tests.append((failure, tag))
            return False

    def aggregate_tests(self):
        """
        Must be called when done with the AggregateTestCase to propagate
        the failures. This is not in __exit__ due to hiding relevant traceback
        levels the exception message ends up pointing to the last line.
        """
        msg = ''
        for error, tag, in self.aggregated_tests:
            if error:
                msg += '\n' + textwrap.indent(str(error), ' ' * TAB_SIZE) + \
                       (f' :: {tag}' if tag is not None else '')

        if msg:
            self.fail(msg=msg)

    def subTest(self, *, name, **params):
        return super().subTest(name=name, **params)

    def _truncateMessage(self, message, diff):
        """
        override unittest.TestCase._truncateMessage to use DIFF_OMITTED message
        """
        max_diff = self.maxDiff
        if max_diff is None or len(diff) <= max_diff:
            return message + diff
        return message + DIFF_OMITTED.format(len(diff))

    @property
    def name(self) -> str:
        return self._testMethodName

    @property
    def description(self) -> str:
        short_desc = self.shortDescription()
        return short_desc if short_desc else self.name


class OrderedTestCase(TestCase):
    """ TestCase with the description property reflecting the test number """

    @property
    def description(self):
        return f'{self.member_names.index(self.name) + 1}. {super().description}'


class TestResult(unittest.TestResult):
    """
    TestResult stores the result of each test in the order they were executed
    """
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super().__init__(stream, descriptions, verbosity)
        self._start = 0
        self._stop = 0
        # TestCaseClassName  TestCaseName
        self.results: Dict[str, Dict[str, Tuple[TestCase, TestOutcome]]] = OrderedDict()

    def startTestRun(self):
        self._start = timer()
        super().startTestRun()

    def stopTestRun(self):
        self._stop = timer()
        super().stopTestRun()

    @property
    def run_time(self):
        return self._stop - self._start

    def startTest(self, test: TestCase):
        test_cls_name = test.__class__.__name__
        if test_cls_name not in self.results:
            self.results[test_cls_name] = OrderedDict()

        test_method = getattr(test.__class__, test.name)
        self._apply_skip(test, test.__class__)
        self._apply_skip(test, test_method)

        super().startTest(test)

    def _apply_skip(self, test: TestCase, test_item: Union[Type[TestCase], FunctionType]):
        """
        Applies the unittest attributes used for skipping tests if the
        __skip_test__ attribute has been applied to either the test class or
        method using the skipIfFailed decorator.
        """
        skip_test = getattr(test_item, '__skip_test__', None)
        if skip_test is None:
            return

        for test_cls, test_name, tag in skip_test:
            if test_cls is None:  # if none then decorator was applied to current TestCase
                # Set type of current TestCase and check if test method is defined
                test_cls = test.__class__
                if not hasattr(test_cls, test_name):
                    raise AttributeError(f'{test_cls.__name__} has no method {test_name}')

            test_cls_name = test_cls.__name__

            if not self.check_outcome(test, test_cls_name, test_name, tag):
                # set attributes unittest looks for if a test is marked to skip
                if test_name is None:
                    test_item.__unittest_skip__ = True
                    test_item.__unittest_skip_why__ = f'Skipped due to failing/skipping a test from {test_cls_name}'
                else:
                    test_item.__unittest_skip__ = True
                    tag_msg = f" with tag '{tag}'" if tag is not None else ''
                    test_item.__unittest_skip_why__ = f'Skipped due to failing/skipping {test_cls_name}.{test_name}{tag_msg}'

                break
        # set custom attribute to None since __unittest_skip__ has been applied
        test_item.__skip_test = None

    def check_outcome(self, test, test_cls_name, test_name, tag):
        # Check if TestCase has been run
        test_results = self.results.get(test_cls_name)
        if test_results is None:
            raise RuntimeError(
                f"Can't check to skip {test.__class__.__name__}.{test.name} if {test_cls_name} has not run")

        # Check if test for TestCase has been run
        if test_name is not None and test_name not in test_results:
            raise RuntimeError(f"Can't check to skip {test.__class__.__name__}.{test.name} '"
                               f"if {test_cls_name}.{test_name} has not run")

        if test_name is not None:
            test_case, outcome = test_results[test_name]
            if tag is None:
                return outcome == TestOutcome.PASS

            for err, tag_ in test_case.aggregated_tests:
                if tag_ == tag:
                    return not err  # None or Exception

        elif test_name is None and any(outcome != TestOutcome.PASS for _, outcome in test_results.values()):
            return False

        return True

    def addSubTest(self, test: TestCase, subtest, err):
        raise NotImplementedError("Subtests are not supported")

    def add_outcome(self, test: TestCase, outcome: TestOutcome):
        self.results[test.__class__.__name__][test.name] = (test, outcome)

    def addSuccess(self, test: TestCase):
        self.add_outcome(test, TestOutcome.PASS)
        super().addSuccess(test)

    @unittest.result.failfast
    def addFailure(self, test: TestCase, err: Tuple[Type[BaseException], BaseException, TracebackType]):
        self.add_outcome(test, TestOutcome.FAIL)
        super().addFailure(test, err)

    @unittest.result.failfast
    def addError(self, test: TestCase, err: Tuple[Type[Exception], BaseException, TracebackType]):
        self.add_outcome(test, TestOutcome.FAIL)
        super().addError(test, err)

    def addSkip(self, test: TestCase, reason: str):
        self.add_outcome(test, TestOutcome.SKIP)
        super().addSkip(test, reason)

    def _is_relevant_tb_level(self, tb):
        """
        Override which is used with unittest.TestResult._exc_info_to_string to
        determine what levels of a traceback to skip when formatting the error.
        """
        return '__TEST_RUNNER' in tb.tb_frame.f_globals or super()._is_relevant_tb_level(tb)

    def to_dict(self):
        return {
            test_cls:
                {name: outcome.value for name, (test, outcome) in res.items()}
            for test_cls, res in self.results.items()
        }


class TestNoPrint(TestCase):
    def __init__(self, stdio: RedirectStdIO):
        super().__init__()
        self._stdio = stdio

    def runTest(self):
        """ check for no unexpected prints """
        self.assertEqual(self._stdio.stdout, '')


class TestMaster:
    """
    Core driving class which creates the TestSuite from the provided TestCases
    """
    separator1 = '=' * BLOCK_WIDTH
    separator2 = '-' * BLOCK_WIDTH
    indent = ' ' * TAB_SIZE
    _remove_path = re.compile(r'File ".*[\\/]([^\\/]+.py)"')
    _remove_importlib = re.compile(
        r'(^\s*File \".*importlib.*\".+?(?=\s{2}File \"))', flags=re.DOTALL | re.MULTILINE)

    def __init__(self,
                 max_diff: int = None,
                 suppress_stdout: bool = True,
                 timeout: float = DEFAULT_TIMEOUT,
                 output_json: bool = False,
                 hide_paths: bool = True,
                 ignore_import_fails: bool = False,
                 include_no_print: bool = False,
                 scripts: List[Tuple[str, str]] = ()):
        """
        Parameters:
            max_diff: Determines the maximum length of diffs output by assert
                methods that report diffs on failure. Set to None for no max
            suppress_stdout: If True all uncaught stdout output is suppressed
            timeout: global timeout value in seconds, if a timeout > 0 is
                specified then the tests are run in killable threads.
            output_json: outputs text summary if True else in json format.
            hide_paths: if True file paths in traceback messages for failures
                are removed to only contain the filename.
            ignore_import_fails: If set to True not tests will run if any module
                being imported with 'scripts' fails to import correctly.
                Otherwise all tests will run.
            include_no_print: iff True adds a test for uncaught prints during
                tests. Requires suppress_stdout to be set as well.
            scripts: list of tuples, these tuples are a pair of module name and
                module path that gets imported using 'path' with the __name__
                attribute of the module set to 'name'. On successful import a
                __TEST_RUNNER_CLEAN_IMPORT attribute is set on the module True
                if nothing was output to stdout otherwise False.
        """
        # argparse setup
        parser = argparse.ArgumentParser()
        parser.add_argument("-j", "--json",
                            help="Whether or not to display output in JSON format.",
                            action='store_true',
                            default=output_json)
        parser.add_argument("-d", "--diff",
                            help="The maximum number of characters in a diff",
                            action="store",
                            default=max_diff,
                            type=int)
        parser.add_argument("-t", "--timeout",
                            help="The maximum time a test is allowed to run before being killed",
                            action="store",
                            default=timeout,
                            type=float)
        parser.add_argument('-p', '--paths', nargs="+")
        parser.add_argument('-s', '--scripts', nargs="+")
        parser.add_argument("--hide-tb-paths",
                            help="Hide paths from traceback output.",
                            action="store_true",
                            default=hide_paths)
        parser.add_argument("--show-tb-duplicates",
                            help="Remove duplicates from test output.",
                            action="store_true",
                            default=False)
        parser.add_argument("--ignore-import-fails",
                            help="Continue tests even if an import fails",
                            action="store_true",
                            default=ignore_import_fails)
        parser.add_argument("--include-no-print",
                            help="Adds test case for unexpected prints in functions",
                            action="store_true",
                            default=include_no_print)
        parser.add_argument("--suppress-stdout",
                            help="Suppresses uncaught stdout output while running tests",
                            action="store_true",
                            default=suppress_stdout)
        self._args = args = parser.parse_args()

        TestCase.maxDiff = args.diff
        TestCase.timeout_interval = args.timeout

        if args.scripts or args.paths:
            if len(args.scripts or ()) != len(args.paths or ()):
                parser.error("must have equal number of values for 'imports' and 'paths'")
            scripts = zip(args.scripts, args.paths)

        self._import_errors = []
        # import scripts
        for name, path in scripts:
            name = name.strip()
            module, error = import_module(path)
            if module is not None:
                module: ModuleType = AttributeGuesser(module)
            TestCase.register_module(name, module)
            if error:
                self._import_errors.append((path, self.format_error(path, error)))
                if not self._args.ignore_import_fails:
                    break

    @staticmethod
    def _add_flavour(flavour: str, test_results: List[Tuple[TestCase, str]]):
        return [(flavour, test, msg) for test, msg in test_results]

    def print_results(self, failed_tests: List[Tuple[str, TestCase, str]], result: TestResult):
        # print summary
        print(BLOCK_TEMPLATE.format('Summary of Results'))
        for test_cls, test_cases in result.results.items():
            passes = sum(outcome == TestOutcome.PASS
                         for _, outcome in test_cases.values())
            print(f'{test_cls}: {passes}/{len(test_cases)}')
            for _test_name, (test, outcome) in test_cases.items():
                print(f'{self.indent}{outcome.value} {test.description}')

        # failed imports
        if self._import_errors:
            print(self.separator2)
            print(BLOCK_TEMPLATE.format('Failed Imports'))
            for path, (err_type, _, err_msg) in self._import_errors:
                print(self.separator1)
                print(f'REASON: {err_type.upper()} ({path})')
                print(self.separator2)
                print(textwrap.indent(err_msg, self.indent))

        # print fails
        if failed_tests:
            print(self.separator2)
            print(BLOCK_TEMPLATE.format('Failed/Skipped Tests'))
            prev = None
            for flavour, test, msg in failed_tests:
                if self._args.show_tb_duplicates:
                    self.print_error(flavour, test, msg.strip())
                else:
                    self.print_error(flavour, test, DUPLICATE_MSG if msg == prev else msg.strip())
                    prev = msg

    def print_error(self, flavour: str, test: TestCase, msg: str):
        print(self.separator1)
        print(f'{flavour}: {test.__class__.__name__} {test.description}')
        print(self.separator2)
        if self._args.hide_tb_paths:
            msg = self._remove_path.sub(r'File "\1"', msg)
        print(textwrap.indent(msg, self.indent))
        print()

    def format_error(self, name: str, exc_info) -> Tuple[str, str, str]:
        exc_type, exc_value, exc_traceback = exc_info
        if exc_type is ImportError:
            msg = f"Tests not run due to {name} file not found"
            err_type = 'import'
        elif exc_type is SyntaxError:
            msg = "Tests not run due to syntax error"
            err_type = 'syntax'
        elif exc_type is EOFError:
            msg = "Tests not run due to unexpectedly waiting for input"
            err_type = 'eof'
        elif exc_type is IndentationError:
            msg = "Tests not run due to indentation error"
            err_type = 'indentation'
        else:
            msg = "Tests not run due to arbitrary exception"
            err_type = 'exception'

        err_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        err_msg = self._remove_importlib.sub('', err_msg)
        if self._args.hide_tb_paths:
            err_msg = self._remove_path.sub(r'File "\1"', err_msg)

        return err_type, msg, err_msg

    def output_results(self, all_tests: List[TestCase], result: TestResult):
        runtime = result.run_time
        total = result.testsRun
        fails, skips = len(result.failures) + len(result.errors), len(result.skipped)
        passed = total - fails - skips

        if self._args.json:
            errors = []
            for _, (err_type, msg, err_msg) in self._import_errors:
                errors.append(dict(error=err_type, error_message=f'{msg}\n{err_msg}'))
            data = dict(total=total, failed=fails, skipped=skips, passed=passed,
                        time=runtime, results=result.to_dict(), errors=errors)
            json.dump(data, sys.stdout, indent=4)
        else:
            # Join the lists sorted by the test order
            failed_tests = sorted(
                self._add_flavour('FAIL', result.failures) +
                self._add_flavour('ERROR', result.errors) +
                self._add_flavour('SKIP', result.skipped),
                key=lambda t: all_tests.index(t[1]))
            self.print_results(failed_tests, result)
            print(self.separator2)
            print(f'Ran {total} tests in {runtime:.3f} seconds with '
                  f'{passed} passed/{skips} skipped/{fails} failed.')

    def run(self, test_cases: List[Union[TestCase, Type[TestCase]]]) -> Optional[TestResult]:
        if not self._args.ignore_import_fails and self._import_errors:
            _, (err_type, msg, err_msg) = self._import_errors[0]
            if self._args.json:
                data = dict(error=err_type, error_message=f'{msg}\n{err_msg}')
                json.dump(data, sys.stdout, indent=4)
            else:
                print(BLOCK_TEMPLATE.format(msg))
                print(err_msg)

            return None

        suite = TestLoader().loadTestCases(test_cases)

        # redirect stderr to hide unittest output
        with RedirectStdIO(stdin=True,
                           stdout=self._args.suppress_stdout,
                           stderr=True) as stdio:
            runner = unittest.TextTestRunner(stream=None,
                                             verbosity=0,
                                             resultclass=TestResult)
            if self._args.include_no_print:
                if not self._args.suppress_stdout:
                    raise RuntimeError("Can't test for no print without suppressing stdout")
                suite.addTest(TestNoPrint(stdio))

            all_tests = list(suite)
            result = runner.run(suite)

        self.output_results(all_tests, result)
        return result
