import random

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT,
              f"{UP}-{LEFT}", f"{UP}-{RIGHT}",
              f"{DOWN}-{LEFT}", f"{DOWN}-{RIGHT}")
WALL_VERTICAL = "|"
WALL_HORIZONTAL = "-"
POKEMON = "☺"
FLAG = "♥"
UNEXPOSED = "~"
EXPOSED = "0"
INVALID = "That ain't a valid action buddy."
HELP_TEXT = """h - Help.
<Uppercase Letter><number> - Selecting a cell (e.g. 'A1')
f <Uppercase Letter><number> - Placing flag at cell (e.g. 'f A1')
:) - Restart game.
q - Quit.
"""


def generate_pokemons(grid_size, number_of_pokemons):
    """Pokemons will be generated and given a random index within the game.

    Parameters:
        grid_size (int): The grid size of the game.
        number_of_pokemons (int): The number of pokemons that the game will have.

    Returns:
        (tuple<int>): A tuple containing  indexes where the pokemons are
        created for the game string.
    """
    cell_count = grid_size ** 2
    pokemon_locations = ()

    for _ in range(number_of_pokemons):
        if len(pokemon_locations) >= cell_count:
            break
        index = random.randint(0, cell_count-1)

        while index in pokemon_locations:
            index = random.randint(0, cell_count-1)

        pokemon_locations += (index,)

    return pokemon_locations
