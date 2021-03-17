from a1_support import *


def display_game(game, grid_size):
    """ Print the game (i.e. string) with the given size of the game

    Parameters:
        game (str): The string representation of the game
        grid_size (int): The grid size of the game.
    """
    row_separator = '\n' + WALL_HORIZONTAL * (grid_size + 1) * 4

    # column headings
    first_row = f"  {WALL_VERTICAL}"
    for i in range(1, grid_size + 1):
        # python magic: string format alignment
        first_row += f" {i:<2}{WALL_VERTICAL}"

    game_board = first_row + row_separator

    # Game Grid
    for i in range(grid_size):
        row = f"{ALPHA[i]} "
        for j in range(grid_size):
            char = game[position_to_index((i, j), grid_size)]
            row += f"{WALL_VERTICAL} {char} "

        game_board += "\n" + row + WALL_VERTICAL
        game_board += row_separator

    print(game_board)


def parse_position(action, grid_size):
    """resolve the action into its corresponding position.

    This function should return None if the action is not the correct format.
    i.e it's not a capital letter followed by a number (e.g. A1).

    Parameters:
        action (str): The string containing the row (Cap) and column.
        grid_size (int): Size of game.

    Returns:
        (tuple<int, int>) : The row, column position of a cell in the game.

        None if the action is invalid.

    """
    if len(action) < 2:
        return None

    row, column = action[0], action[1:]

    if not column.isdigit():
        return None

    x = ALPHA.find(row)
    y = int(column) - 1
    
    if x == -1 or not 0 <= y < grid_size:
        return None

    return x, y


def position_to_index(position, grid_size):
    """Convert the row, column coordinate in the grid to the game strings index.

    Parameters:
        position (tuple<int, int>): The row, column position of a cell.
        grid_size (int): The grid size of the game.

    Returns:
        (int): The index of the cell in the game string.
    """
    x, y = position
    return x * grid_size + y


def replace_character_at_index(game, index, character):
    """A specified index in the game string at the specified index is replaced by
    a new character.
    Parameters:
        game (str): The game string.
        index (int): The index in the game string where the character is replaced.
        character (str): The new character that will be replacing the old character.

    Returns:
        (str): The updated game string.
    """
    return game[:index] + character + game[index + 1:]


def flag_cell(game, index):
    """Toggle Flag on or off at selected index. If the selected index is already
        revealed, the game would return with no changes.

        Parameters:
            game (str): The game string.
            index (int): The index in the game string where a flag is placed.
        Returns
            (str): The updated game string.
    """
    if game[index] == FLAG:
        game = replace_character_at_index(game, index, UNEXPOSED)

    elif game[index] == UNEXPOSED:
        game = replace_character_at_index(game, index, FLAG)

    return game


def index_in_direction(index, grid_size, direction):
    """The index in the game string is updated by determining the
    adjacent cell given the direction.
    The index of the adjacent cell in the game is then calculated and returned.

    For example:
      | 1 | 2 | 3 |
    A | i | j | k |
    B | l | m | n |
    C | o | p | q |

    The index of m is 4 in the game string.
    if the direction specified is "up" then:
    the updated position corresponds with j which has the index of 1 in the game string.

    Parameters:
        index (int): The index in the game string.
        grid_size (int): The grid size of the game.
        direction (str): The direction of the adjacent cell.

    Returns:
        (int): The index in the game string corresponding to the new cell position
        in the game.

        None for invalid direction.
    """
    # convert index to row, col coordinate
    col = index % grid_size
    row = index // grid_size
    if RIGHT in direction:
        col += 1
    elif LEFT in direction:
        col -= 1
    # Notice the use of if, not elif here
    if UP in direction:
        row -= 1
    elif DOWN in direction:
        row += 1
    if not (0 <= col < grid_size and 0 <= row < grid_size):
        return None
    return position_to_index((row, col), grid_size)


def neighbour_directions(index, grid_size):
    """Seek out all direction that has a neighbouring cell.

    Parameters:
        index (int): The index in the game string.
        grid_size (int): The grid size of the game.

    Returns:
        (list<int>): A list of index that has a neighbouring cell.
    """
    neighbours = []
    for direction in DIRECTIONS:
        neighbour = index_in_direction(index, grid_size, direction)
        if neighbour is not None:
            neighbours.append(neighbour)

    return neighbours


def number_at_cell(game, pokemon_locations, grid_size, index):
    """Calculates what number should be displayed at that specific index in the game.

    Parameters:
        game (str): Game string.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.
        grid_size (int): Size of game.
        index (int): Index of the currently selected cell

    Returns:
        (int): Number to be displayed at the given index in the game string.
    """
    if game[index] != UNEXPOSED:
        return int(game[index])

    number = 0
    for neighbour in neighbour_directions(index, grid_size):
        if neighbour in pokemon_locations:
            number += 1

    return number
    # Alternatively
    # return len(set(pokemon_locations) & set(neighbour_directions(index, grid_size)))


def check_win(game, pokemon_locations):
    """Checking if the player has won the game.

    Parameters:
        game (str): Game string.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.

    Returns:
        (bool): True if the player has won the game, false if not.

    """
    return UNEXPOSED not in game and game.count(FLAG) == len(pokemon_locations)


def reveal_cells(game, grid_size, pokemon_locations, index):
    """Reveals all neighbouring cells at index and repeats for all
    cells that had a 0.

    Does not reveal flagged cells or cells with Pokemon.

    Parameters:
        game (str): Game string.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.
        grid_size (int): Size of game.
        index (int): Index of the currently selected cell

    Returns:
        (str): The updated game string
    """
    number = number_at_cell(game, pokemon_locations, grid_size, index)
    game = replace_character_at_index(game, index, str(number))
    clear = big_fun_search(game, grid_size, pokemon_locations, index)
    for i in clear:
        if game[i] != FLAG:
            number = number_at_cell(game, pokemon_locations, grid_size, i)
            game = replace_character_at_index(game, i, str(number))

    return game


def main():
    """
    Handles player interaction.
    """
    grid_size = int(input("Please input the size of the grid: "))
    number_of_pokemons = int(input("Please input the number of pokemons: "))

    game = UNEXPOSED * grid_size ** 2
    pokemon_locations = generate_pokemons(grid_size, number_of_pokemons)

    while True:
        display_game(game, grid_size)
        
        if check_win(game, pokemon_locations):
            print("You win.")
            break
        
        action = input("\nPlease input action: ")

        if action == "h":
            print(HELP_TEXT)

        elif action == "q":
            response = input("You sure about that buddy? (y/n): ")
            if response == "y":
                print("Catch you on the flip side.")
                break
            elif response == "n":
                print("Let's keep going.")
            else:
                print(INVALID)

        elif action == ":)":
            print("It's rewind time.")
            game = UNEXPOSED * grid_size ** 2
            pokemon_locations = generate_pokemons(grid_size, number_of_pokemons)

        elif action.startswith("f "):
            position = parse_position(action[2:], grid_size)
            if position is None:
                print(INVALID)
                continue
            game = flag_cell(game, position_to_index(position, grid_size))

        else:
            position = parse_position(action, grid_size)
            if position is None:
                print(INVALID)
                continue

            index = position_to_index(position, grid_size)
            if game[index] == FLAG:
                continue
            
            if index in pokemon_locations:
                for i in pokemon_locations:
                    game = replace_character_at_index(game, i, POKEMON)
                display_game(game, grid_size)
                print("You have scared away all the pokemons.")
                break

            game = reveal_cells(game, grid_size, pokemon_locations, index)


def big_fun_search(game, grid_size, pokemon_locations, index):
    """Searching adjacent cells to see if there are any Pokemon"s present.

    Using some sick algorithms.

    Find all cells which should be revealed when a cell is selected.

    For cells which have a zero value (i.e. no neighbouring pokemons) all the cell"s
    neighbours are revealed. If one of the neighbouring cells is also zero then
    all of that cell"s neighbours are also revealed. This repeats until no
    zero value neighbours exist.

    For cells which have a non-zero value (i.e. cells with neighbour pokemons), only
    the cell itself is revealed.

    Parameters:
        game (str): Game string.
        grid_size (int): Size of game.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.
        index (int): Index of the currently selected cell

    Returns:
        (list<int>): List of cells to turn visible.
    """
    queue = [index]
    discovered = [index]
    visible = []

    if game[index] == FLAG:
        return queue

    number = number_at_cell(game, pokemon_locations, grid_size, index)
    if number != 0:
        return queue

    while queue:
        node = queue.pop()
        for neighbour in neighbour_directions(node, grid_size):
            if neighbour in discovered:
                continue

            discovered.append(neighbour)
            if game[neighbour] != FLAG:
                number = number_at_cell(game, pokemon_locations, grid_size, neighbour)
                if number == 0:
                    queue.append(neighbour)
            visible.append(neighbour)
    return visible


if __name__ == "__main__":
    main()
