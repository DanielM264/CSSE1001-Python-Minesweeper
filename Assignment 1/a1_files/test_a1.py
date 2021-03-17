"""
Tests for CSSE1001 / 7030 Assignment 1
"""

__author__ = "Steven Summers"

import random
import inspect
from pathlib import Path
from typing import Tuple, List

from testrunner import AttributeGuesser, OrderedTestCase, RedirectStdIO, TestMaster, skipIfFailed


Position = Tuple[int, int]
Locations = Tuple[int, ...]
SEED = 1001


class A1:
    """ Just used for type hints """

    @staticmethod
    def display_game(game: str, grid_size: int):
        pass

    @staticmethod
    def parse_position(action: str, grid_size: int) -> Position:
        pass

    @staticmethod
    def position_to_index(position: Position, grid_size: int) -> int:
        pass

    @staticmethod
    def replace_character_at_index(game: str, index: int, character: str) -> str:
        pass

    @staticmethod
    def flag_cell(game: str, index: int) -> str:
        pass

    @staticmethod
    def index_in_direction(index: int, grid_size: int, direction: str) -> int:
        pass

    @staticmethod
    def neighbour_directions(index: int, grid_size: int) -> List[int]:
        pass

    @staticmethod
    def number_at_cell(game: str, pokemon_locations: Locations, grid_size: int, index: int) -> int:
        pass

    @staticmethod
    def check_win(game: str, pokemon_locations: Locations) -> bool:
        pass

    @staticmethod
    def main():
        pass


class TestA1(OrderedTestCase):
    """ Base for all a1 test cases """

    a1: A1
    a1_support: ...


class TestDesign(TestA1):
    """ Checks A1 design compliance """

    def test_clean_import(self):
        """ test no prints on import """
        self.assertIsCleanImport(self.a1, msg="You should not be printing on import for a1.py")

    def test_functions_defined(self):
        """ test all functions are defined correctly """
        a1 = AttributeGuesser.get_wrapped_object(self.a1)
        for func_name, func in inspect.getmembers(A1, predicate=inspect.isfunction):
            num_params = len(inspect.signature(func).parameters)
            self.aggregate(self.assertFunctionDefined, a1, func_name, num_params, tag=func_name)

        self.aggregate_tests()

    def test_doc_strings(self):
        """ test all functions have documentation strings """
        a1 = AttributeGuesser.get_wrapped_object(self.a1)
        for attr_name, _ in inspect.getmembers(a1, predicate=inspect.isfunction):
            self.aggregate(self.assertDocString, a1, attr_name)

        self.aggregate_tests()


class TestFunctionality(TestA1):
    """ Base for all A1 functionality tests """

    game = '~~~~~~~~~'
    grid_size = 3
    TEST_DATA = Path(__file__).parent / 'test_data'

    def get_pokemon_locations(self, grid_size: int, number_of_pokemon: int):
        """ helper method for getting seeded pokemon locations """
        random.seed(SEED)
        return self.a1_support.generate_pokemons(grid_size, number_of_pokemon)

    def load_test_data(self, filename: str):
        """ load test data from file """
        with open(self.TEST_DATA / filename, encoding='utf8') as file:
            return file.read()

    def write_test_data(self, filename: str, output: str):
        """ write test data to file """
        with open(self.TEST_DATA / filename, 'w', encoding='utf8') as file:
            file.write(output)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.display_game.__name__)
class TestDisplayGame(TestFunctionality):
    """ Tests display game """

    def test_simple_game(self):
        """ test display game """
        with RedirectStdIO(stdout=True) as stdio:
            result = self.a1.display_game(self.game, self.grid_size)

        expected = self.load_test_data("display_game_simple.out")
        self.assertMultiLineEqual(stdio.stdout, expected)
        self.assertIsNone(result, msg="display_game should not return a non None value")

    def test_with_symbols(self):
        """ test display with symbols """
        game = "☺♥1♥31110"
        with RedirectStdIO(stdout=True) as stdio:
            result = self.a1.display_game(game, 3)

        expected = self.load_test_data("display_game_symbols.out")
        self.assertMultiLineEqual(stdio.stdout, expected)
        self.assertIsNone(result, msg="display_game should not return a non None value")

    def test_full_game(self):
        """ test display large game """
        game = self.load_test_data("display_game_full.in")
        with RedirectStdIO(stdout=True) as stdio:
            result = self.a1.display_game(game, 26)

        expected = self.load_test_data("display_game_full.out")
        self.assertMultiLineEqual(stdio.stdout, expected)
        self.assertIsNone(result, msg="display_game should not return a non None value")


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.parse_position.__name__)
class TestParsePosition(TestFunctionality):
    """ Tests parse_position """

    def test_parse_valid(self):
        """ test parse valid """
        result = self.a1.parse_position('B2', 4)
        self.assertEqual(result, (1, 1))

    def test_parse_multi_digit(self):
        """ test parse valid multiple digits """
        result = self.a1.parse_position('B12', 15)
        self.assertEqual(result, (1, 11))

    def test_parse_invalid_lowercase(self):
        """ test parse invalid lowercase """
        result = self.a1.parse_position("b2", 4)
        self.assertIsNone(result)

    def test_parse_invalid_non_alpha(self):
        """ test parse invalid no letter """
        result = self.a1.parse_position("22", 4)
        self.assertIsNone(result)

    def test_parse_invalid_non_digit(self):
        """ test parse invalid no digit """
        result = self.a1.parse_position("BC", 4)
        self.assertIsNone(result)

    def test_parse_invalid_out_of_range(self):
        """ test parse invalid out of range """
        result = self.a1.parse_position("B8", 4)
        self.assertIsNone(result)

    def test_parse_invalid_empty(self):
        """ test parse empty """
        result = self.a1.parse_position("", 4)
        self.assertIsNone(result)

    def test_parse_invalid_short(self):
        """ test parse short input """
        result = self.a1.parse_position("B", 4)
        self.assertIsNone(result)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.position_to_index.__name__)
class TestPositionToIndex(TestFunctionality):
    """ Tests position_to_index """

    def test_0_0_4(self):
        """ test position=(0, 0), grid_size=4 """
        result = self.a1.position_to_index((0, 0), 4)
        self.assertEqual(result, 0)

    def test_1_0_4(self):
        """ test position=(1, 0), grid_size=4 """
        result = self.a1.position_to_index((1, 0), 4)
        self.assertEqual(result, 4)

    def test_2_3_4(self):
        """ test position=(2, 3), grid_size=4 """
        result = self.a1.position_to_index((2, 3), 4)
        self.assertEqual(result, 11)

    def test_5_6_15(self):
        """ test position=(5, 6), grid_size=15 """
        result = self.a1.position_to_index((5, 6), 15)
        self.assertEqual(result, 81)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.replace_character_at_index.__name__)
class TestReplaceCharacterAtIndex(TestFunctionality):
    """ Tests replace_character_at_index """

    def test_replace_start(self):
        """ test replace starting character """
        result = self.a1.replace_character_at_index(self.game, 0, 's')
        self.assertEqual(result, "s~~~~~~~~")

    def test_replace_middle(self):
        """ test replace middle character """
        result = self.a1.replace_character_at_index(self.game, 4, 's')
        self.assertEqual(result, "~~~~s~~~~")

    def test_replace_end(self):
        """ test replace end character """
        result = self.a1.replace_character_at_index(self.game, 8, 's')
        self.assertEqual(result, "~~~~~~~~s")


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.flag_cell.__name__)
class TestFlagCell(TestFunctionality):
    """ Tests flag_cell """

    flag1 = "~~~~♥~~~~"
    flag2 = "~~~~♥~♥~~"

    def test_set_flag(self):
        """ test set flag """
        result = self.a1.flag_cell(self.game, 4)
        self.assertEqual(result, self.flag1)

    def test_unset_flag(self):
        """ test un-set flag """
        result = self.a1.flag_cell(self.flag1, 4)
        self.assertEqual(result, self.game)

    def test_set_second_flag(self):
        """ test settings another flag """
        result = self.a1.flag_cell(self.flag1, 6)
        self.assertEqual(result, self.flag2)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.index_in_direction.__name__)
class TestIndexInDirection(TestFunctionality):
    """ Tests index_in_direction """

    def test_left(self):
        """ test index to LEFT """
        result = self.a1.index_in_direction(6, 4, self.a1_support.LEFT)
        self.assertEqual(result, 5)

    def test_left_none(self):
        """ test no index to LEFT """
        result = self.a1.index_in_direction(8, 4, self.a1_support.LEFT)
        self.assertIsNone(result)

    def test_left_none_2(self):
        """ test no index to LEFT from start """
        result = self.a1.index_in_direction(0, 4, self.a1_support.LEFT)
        self.assertIsNone(result)

    def test_right(self):
        """ test index to RIGHT """
        result = self.a1.index_in_direction(6, 4, self.a1_support.RIGHT)
        self.assertEqual(result, 7)

    def test_right_none(self):
        """ test no index to RIGHT """
        result = self.a1.index_in_direction(7, 4, self.a1_support.RIGHT)
        self.assertIsNone(result)

    def test_right_none_2(self):
        """ test no index to RIGHT from end """
        result = self.a1.index_in_direction(15, 4, self.a1_support.RIGHT)
        self.assertIsNone(result)

    def test_up(self):
        """ test index to UP """
        result = self.a1.index_in_direction(6, 4, self.a1_support.UP)
        self.assertEqual(result, 2)

    def test_up_none(self):
        """ test no index to UP """
        result = self.a1.index_in_direction(2, 4, self.a1_support.UP)
        self.assertIsNone(result)

    def test_down(self):
        """ test index to DOWN """
        result = self.a1.index_in_direction(6, 4, self.a1_support.DOWN)
        self.assertEqual(result, 10)

    def test_down_none(self):
        """ test no index to DOWN """
        result = self.a1.index_in_direction(14, 4, self.a1_support.DOWN)
        self.assertIsNone(result)

    def test_up_left(self):
        """ test index to UP-LEFT """
        result = self.a1.index_in_direction(5, 4, f"{self.a1_support.UP}-{self.a1_support.LEFT}")
        self.assertEqual(result, 0)

    def test_up_left_none(self):
        """ test no index to UP-LEFT """
        result = self.a1.index_in_direction(4, 4, f"{self.a1_support.UP}-{self.a1_support.LEFT}")
        self.assertIsNone(result)

    def test_up_right(self):
        """ test index to UP-RIGHT """
        result = self.a1.index_in_direction(6, 4, f"{self.a1_support.UP}-{self.a1_support.RIGHT}")
        self.assertEqual(result, 3)

    def test_up_right_none(self):
        """ test no index to UP-RIGHT """
        result = self.a1.index_in_direction(7, 4, f"{self.a1_support.UP}-{self.a1_support.RIGHT}")
        self.assertIsNone(result)

    def test_down_left(self):
        """ test index to DOWN-LEFT """
        result = self.a1.index_in_direction(5, 4, f"{self.a1_support.DOWN}-{self.a1_support.LEFT}")
        self.assertEqual(result, 8)

    def test_down_left_none(self):
        """ test no index to DOWN-LEFT """
        result = self.a1.index_in_direction(4, 4, f"{self.a1_support.DOWN}-{self.a1_support.LEFT}")
        self.assertIsNone(result)

    def test_down_right(self):
        """ test index to DOWN-RIGHT """
        result = self.a1.index_in_direction(5, 4, f"{self.a1_support.DOWN}-{self.a1_support.RIGHT}")
        self.assertEqual(result, 10)

    def test_down_right_none(self):
        """ test no index to DOWN-RIGHT """
        result = self.a1.index_in_direction(7, 4, f"{self.a1_support.DOWN}-{self.a1_support.RIGHT}")
        self.assertIsNone(result)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.neighbour_directions.__name__)
class TestNeighbourDirections(TestFunctionality):
    """ Tests neighbour_directions """

    def test_top_left_corner(self):
        """ test neighbours from top left """
        result = self.a1.neighbour_directions(0, 4)
        expected = [4, 1, 5]
        self.assertListSimilar(result, expected)

    def test_top_right_corner(self):
        """ test neighbours from top right """
        result = self.a1.neighbour_directions(3, 4)
        expected = [2, 7, 6]
        self.assertListSimilar(result, expected)

    def test_bottom_left_corner(self):
        """ test neighbours from bottom left """
        result = self.a1.neighbour_directions(12, 4)
        expected = [8, 13, 9]
        self.assertListSimilar(result, expected)

    def test_bottom_right_corner(self):
        """ test neighbours from bottom right """
        result = self.a1.neighbour_directions(15, 4)
        expected = [11, 14, 10]
        self.assertListSimilar(result, expected)

    def test_middle(self):
        """ test neighbours from middle """
        result = self.a1.neighbour_directions(12, 5)
        expected = [6, 7, 8, 11, 13, 16, 17, 18]
        self.assertListSimilar(result, expected)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.number_at_cell.__name__)
class TestNumberAtCell(TestFunctionality):
    """ Tests number_at_cell """

    def test_has_neighbours(self):
        """ test with pokemon neighbours """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        result = self.a1.number_at_cell(self.game, pokemon_locations, self.grid_size, 4)
        self.assertEqual(result, 3)

    def test_has_no_neighbours(self):
        """ test with no pokemon neighbours """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        result = self.a1.number_at_cell(self.game, pokemon_locations, self.grid_size, 8)
        self.assertEqual(result, 0)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.check_win.__name__)
class TestCheckWin(TestFunctionality):
    """ Tests check_win """
    def test_new_game(self):
        """ test all exposed """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        result = self.a1.check_win(self.game, pokemon_locations)
        self.assertIs(result, False)

    def test_completed_game(self):
        """ test winning state """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        game = "♥♥1♥31110"
        result = self.a1.check_win(game, pokemon_locations)
        self.assertIs(result, True)

    def test_all_flags(self):
        """ test all flagged """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        game = "♥♥♥♥♥♥♥♥♥"
        result = self.a1.check_win(game, pokemon_locations)
        self.assertIs(result, False)

    def test_flagged_not_exposed(self):
        """ test flagged but not exposed """
        # (0, 3, 1)
        pokemon_locations = self.get_pokemon_locations(self.grid_size, 3)
        game = "♥♥~♥~~~~~"
        result = self.a1.check_win(game, pokemon_locations)
        self.assertIs(result, False)


@skipIfFailed(TestDesign, TestDesign.test_functions_defined.__name__, tag=A1.main.__name__)
class TestMain(TestFunctionality):
    """ Tests main """

    def _run_main(self, file_in: str, file_out: str, stop_early: bool):
        """ runs the main function and captures output """
        data_in = self.load_test_data(file_in)

        error = None
        result = None
        with RedirectStdIO(stdinout=True) as stdio:
            stdio.stdin = data_in
            try:
                result = self.a1.main()
            except EOFError as err:
                error = err

        # self.write_test_data(file_out, stdio.stdinout)
        expected = self.load_test_data(file_out)
        if error is not None and not stop_early:
            last_output = "\n\n".join(stdio.stdinout.rsplit("\n\n")[-2:])
            raise AssertionError(
                f'Your program is asking for too much input\nEOFError: {error}\n\n{last_output}'
            ).with_traceback(error.__traceback__)

        return expected, result, stdio

    def assertMain(self, file_in: str, file_out: str, stop_early: bool = True):
        """ assert the main function ran correctly """
        expected, result, stdio = self._run_main(file_in, file_out, stop_early=stop_early)
        self.assertMultiLineEqual(stdio.stdinout, expected)
        if stdio.stdin != '':
            self.fail(msg="Not all input was read")
        self.assertIsNone(result, msg="main function should not return a non None value")

    def setUp(self):
        random.seed(SEED)

    def test_help(self):
        """ test show help """
        self.assertMain("main_help.in", "main_help.out")

    def test_quit_yes(self):
        """ test quit - yes """
        self.assertMain("main_quit_yes.in", "main_quit_yes.out", stop_early=False)

    def test_quit_no(self):
        """ test quit - no """
        self.assertMain("main_quit_no.in", "main_quit_no.out")

    def test_game_over(self):
        """ test game over """
        self.assertMain("main_game_over.in", "main_game_over.out", stop_early=False)

    def test_game_over_2(self):
        """ test game over preserving game """
        self.assertMain("main_game_over_2.in", "main_game_over_2.out", stop_early=False)

    def test_invalid_action_1(self):
        """ test invalid action """
        self.assertMain("main_invalid_action_1.in", "main_invalid_action_1.out")

    def test_invalid_action_2(self):
        """ test blank line for action """
        self.assertMain("main_invalid_action_2.in", "main_invalid_action_2.out")

    def test_invalid_action_3(self):
        """ test invalid flag input """
        self.assertMain("main_invalid_action_3.in", "main_invalid_action_3.out")

    def test_invalid_action_4(self):
        """ test bad response for quit """
        self.assertMain("main_invalid_action_4.in", "main_invalid_action_4.out")

    def test_exposed_flagged(self):
        """ test can't expose flagged cell """
        self.assertMain("main_exposed_flagged.in", "main_exposed_flagged.out")

    def test_exposed_exposed(self):
        """ test expose exposed """
        self.assertMain("main_exposed_exposed.in", "main_exposed_exposed.out")

    def test_exposed_flagged_neighbour(self):
        """ test should not expose a neighbour if flagged """
        self.assertMain("main_expose_flagged_neighbour.in", "main_expose_flagged_neighbour.out")

    def test_reset(self):
        """ test reset game state and pokemon positions """
        self.assertMain("main_reset.in", "main_reset.out")

    def test_game_win(self):
        """ test game win """
        self.assertMain("main_game_win.in", "main_game_win.out", stop_early=False)


def main():
    """ run tests """
    test_cases = [
        TestDesign,
        TestDisplayGame,
        TestParsePosition,
        TestPositionToIndex,
        TestReplaceCharacterAtIndex,
        TestFlagCell,
        TestIndexInDirection,
        TestNeighbourDirections,
        TestNumberAtCell,
        TestCheckWin,
        TestMain
    ]

    master = TestMaster(max_diff=None,
                        suppress_stdout=True,
                        # ignore_import_fails=True,
                        timeout=1,
                        include_no_print=True,
                        scripts=[
                            ('a1', 'a1.py'),
                            ('a1_support', 'a1_support.py')
                        ])
    master.run(test_cases)


if __name__ == '__main__':
    main()
