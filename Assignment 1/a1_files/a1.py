from a1_support import *

#Game entity
def game_initialization(grid_size, number_of_pokemon):
    """This function is run on game start to create an unexposed game string with a length of
    grid_size ** 2.
    
    Parameters:
        grid_size (int): Size of game.
        number_of_pokemon (int): Total number of pokemon in the game.
    Returns:
        (str): Game string.
    """
    game_string_length = grid_size ** 2
    game = str(game_string_length * UNEXPOSED)
    return game

def display_game(game, grid_size):
    """Prints the game grid row-by-row. This is what the player will see.

    This function is broken down into two parts, the first row (containing the column headings) and
    all subsequent rows (containing the row heading followed by the grid cells).
    
    Parameters:
        game (str): Game string.
        grid_size (int): Size of game.
    Returns:
        Prints the game as a grid.
    """
    # Line 1 (grid_line1)
    count = 1
    grid_line1 = '  '
    while count <= grid_size:
        grid_line1 += WALL_VERTICAL
        grid_line1 += ' '
        grid_line1 += str(count)
        if count < 10:
            grid_line1 += ' '
        count += 1
    grid_line1 += WALL_VERTICAL
    print(grid_line1)

    # All other lines (grid_line)
    count2 = 0
    letter_count = 0
    game_count = 0
    while count2 <= (2 * grid_size):
        grid_line = ''
        if count2 % 2 == 0 or count2 == (2 * grid_size):
            grid_line = (len(grid_line1) + 1) * WALL_HORIZONTAL
        
        else:
            grid_line += ALPHA[letter_count]
            grid_line += ' '
            letter_count += 1
            cell_count = 0
            while cell_count < (grid_size):
                grid_line += WALL_VERTICAL
                grid_line += ' '
                grid_line += game[game_count]
                grid_line += ' '
                cell_count += 1
                game_count += 1
            grid_line += WALL_VERTICAL
        
        print(grid_line)
        count2 += 1

def parse_position(alphanumeric, grid_size):
    """Converts the alphanumerical value of a cell in the game grid to a tuple.
    The tuple is read as (vertical position, horizontal position).
    i.e. 'A1' returns (0, 0) and 'B3' returns (1, 2). A1 is the origin of all positions.
    
    Parameters:
        alphanumeric (str): The alphanumeric value assigned to a game cell.
        grid_size (int): Size of the game.
    Returns:
        (tuple<int, ...>): A tuple of the corresponding grid position.
    """
    #Preliminary input validation check
    if alphanumeric == '' or alphanumeric[1:3].isdigit() == 0 or len(alphanumeric) > 3:
        return

    #Variables
    fail_count = 0
    letter = int(ALPHA.find(alphanumeric[0]))
    number = int(alphanumeric[1:3]) - 1

    #Secondary validation checks
    if  letter >= grid_size or letter == -1:
        fail_count += 1
        
    elif number >= grid_size:
        fail_count += 1

    #Output
    elif fail_count == 0:    
        return (letter, number)

def position_to_index(position, grid_size):
    """Converts a position tuple into the game string index at that position.
    
    Parameters:
        position (tuple<int>): Grid position.
        grid_size (int): Size of the game.
    Returns:
        (int): Game string index at position.
    """
    index = 0
    letter = position[0]
    index += letter * grid_size
    number = position[1]
    index += number
    return index

def replace_character_at_index(game, index, character):
    """Replaces a character in the game string at the specified index.
    
    Parameters:
        game (str): Game string.
        index (int): Game string index.
        character (str): New character.
    Returns:
        (str): Updated game string.
    """
    x = list(game)
    x[index] = character
    new_game = ""
    for i in x:
        new_game += str(i)
    return new_game

def flag_cell(game, index):
    """Uses the replace_character_at_index function to flag or unflag
    the specified index in the game string.
    
    Parameters:
        game (str): Game string.
        index (int): Game string index.
    Returns:
        (str): Updated game string.
    """
    if list(game)[index] == UNEXPOSED:
        game = replace_character_at_index(game, index, FLAG)
    elif list(game)[index] == FLAG:
        game = replace_character_at_index(game, index, UNEXPOSED)
    else:
        print(INVALID)
    return game

def index_in_direction(index, grid_size, direction):
    """Returns the index in the game string of the cell in the specified
    direction of the original index cell. Uses the DIRECTION variable in
    a1_support.py code.
    
    Parameters:
        index (int): Game string index.
        grid_size (int): Size of the game.
        direction (str): Direction.
    Returns:
        (int): Game string index.
    """
    if direction == DIRECTIONS[0] and index - grid_size >= 0: #UP
        index -= grid_size
        return index
    elif direction == DIRECTIONS[1] and index + grid_size <= (grid_size ** 2) - 1: #DOWN
        index += grid_size
        return index
    elif direction == DIRECTIONS[2] and index % grid_size != 0: #LEFT
        index -= 1
        return index
    elif direction == DIRECTIONS[3] and index % grid_size != grid_size - 1: #RIGHT
        index += 1
        return index
    elif direction == DIRECTIONS[4] and index - grid_size >= 0 and index % grid_size != 0: #UP-LEFT
        index = (index - grid_size) - 1
        return index
    elif direction == DIRECTIONS[5] and index - grid_size >= 0 and index % grid_size != grid_size - 1: #UP-RIGHT
        index = (index - grid_size) + 1
        return index
    elif direction == DIRECTIONS[6] and index + grid_size <= (grid_size ** 2) - 1 and index % grid_size != 0: #DOWN-LEFT
        index = (index + grid_size) - 1
        return index
    elif direction == DIRECTIONS[7] and index + grid_size <= (grid_size ** 2) - 1 and index % grid_size != grid_size - 1: #DOWN-RIGHT
        index = (index + grid_size) + 1
        return index

def neighbour_directions(index, grid_size):
    """Lists the indexes of all neighbouring cells within the bounds of the
    game grid.
    
    Parameters:
        index (int): Game string index.
        grid_size (int): Size of the game.
    Returns:
        (list<int>): List of all neighbouring cells' indexes.
    """
    list1 = list()
    for i in DIRECTIONS:
        output = index_in_direction(index, grid_size, i)
        if type(output) == int:
            list1.append(output)
    return list1

def number_at_cell(game, pokemon_locations, grid_size, index):
    """Checks the surrounding cells against the pokemon locations and returns how many
    pokemon are in its' neighbour cells.

    Parameters:
        game (str): Game string.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.
        grid_size (int): Size of the game.
        index (int): Game string index.
    Returns:
        (int): Number of pokemon in neighbouring cells.
    
    """
    number_at_cell = 0
    for i in neighbour_directions(index, grid_size):
        if i in pokemon_locations:
            number_at_cell += 1
    return number_at_cell

def check_win(game, pokemon_locations):
    """Checks the game string for the win conditions.
    Win Conditions:
        All pokemon locations are flagged
        All other cells are exposed (not flagged or '~')
    
    Parameters:
        game (str): Game string.
        pokemon_locations (tuple<int, ...>): Tuple of all Pokemon's locations.
    Returns:
        (bool): True if game is won, False if game is still in progress.
    """
    caught = 0
    unexposed_count = 0
    flag_count = 0
    for i in pokemon_locations: #Checks all pokemon are caught
        if game[i] == FLAG:
            caught += 1
    for i in game: #Checks no unexposed tiles
        if i == UNEXPOSED:
            unexposed_count += 1
    for i in game: #Check correct number of flags
        if i == FLAG:
            flag_count += 1
    if caught == len(pokemon_locations) and unexposed_count == 0 and flag_count == len(pokemon_locations):
        return bool(1)
    else:
        return bool(0)

def big_fun_search(game, grid_size, pokemon_locations, index):
 	"""Searching adjacent cells to see if there are any Pokemon"s present.

 	Using some sick algorithms.

 	Find all cells which should be revealed when a cell is selected.

 	For cells which have a zero value (i.e. no neighbouring pokemons) all the cell"s
 	neighbours are revealed. If one of the neighbouring cells is also zero then
 	all of that cell"s neighbours are also revealed. This repeats until no
 	zero value neighbours exist.

 	For cells which have a non-zero value (i.e. cells with neightbour pokemons), only
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
 			if neighbour in discovered or neighbour is None:
 				continue

 			discovered.append(neighbour)
 			if game[neighbour] != FLAG:
 				number = number_at_cell(game, pokemon_locations, grid_size, neighbour)
 				if number == 0:
 					queue.append(neighbour)
 			visible.append(neighbour)
 	return visible


def main():
    """This is the main game code. At game start it asks for the inputs grid_size and number_of_pokemon
    to generate the pokemon_locations tuple. Then, while the check_win function does not return that the
    game has been won, the display_game is called to create a GUI for the user and user input is requested.
    A series of if and elif statements handle the user input. Once the game is won, the secondary loss
    function is checked and if it returns false the final game is displayed along with 'You won.'.

    This function has no parameters and handles the entire game code.
    """
    loss = 0
    grid_size = int(input("Please input the size of the grid: "))
    number_of_pokemon = int(input("Please input the number of pokemons: "))
    game = game_initialization(grid_size, number_of_pokemon)
    pokemon_locations = generate_pokemons(grid_size, number_of_pokemon)
    while check_win(game, pokemon_locations) == 0:
        restart = 0
        display = display_game(game, grid_size)
        print()
        user_action = str(input('Please input action: '))
        if user_action == 'q':
            confirmation_check = input('You sure about that buddy? (y/n): ')
            if confirmation_check in ('y', 'yes', 'Y', 'Yes', 'YES'):
                loss = 1
                print('Catch you on the flip side.')
                break
            elif confirmation_check in ('n', 'no', 'N', 'No', 'NO'):
                print("Let's keep going.")
            else:
                print(INVALID)
                
        elif user_action == ':)':
            print("It's rewind time.")
            game = game_initialization(grid_size, number_of_pokemon)
            pokemon_locations = generate_pokemons(grid_size, number_of_pokemon)
            
        elif user_action =='h':
            print(HELP_TEXT)

        elif user_action[0:2] == 'f ':
            position = parse_position(user_action[2:5], grid_size)
            if position == None:
                print(INVALID)
            else:
                index = position_to_index(position, grid_size)
                game = flag_cell(game, index)
                
        elif user_action == '':
            print(INVALID)

        elif user_action[0] in ALPHA and user_action[1] != ' ' and (user_action[1]).isdigit() == 1:
            position = parse_position(user_action, grid_size)
            index = position_to_index(position, grid_size)
            if game[index] == UNEXPOSED:
                if index in pokemon_locations:
                    for i in pokemon_locations:
                        game = replace_character_at_index(game, i, POKEMON)
                    display_game(game, grid_size)
                    print('You have scared away all the pokemons.')
                    loss = 1
                    break
                else:
                    character = number_at_cell(game, pokemon_locations, grid_size, index)
                    if character == 0:
                        game = replace_character_at_index(game, index, character)
                        for i in big_fun_search(game, grid_size, pokemon_locations, index):
                            if game[i] == FLAG:
                                pass
                            else:
                                character = number_at_cell(game, pokemon_locations, grid_size, i)
                                game = replace_character_at_index(game, i, character)
                        
                    else:
                        game = replace_character_at_index(game, index, character)
        else:
            print(INVALID)
    if loss == 1:
        pass
    else:
        display_game(game, grid_size)
        print('You win.')
if __name__ == "__main__":
    main()

