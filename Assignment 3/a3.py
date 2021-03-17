import random
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename, askopenfilename
from PIL import Image, ImageTk
import random

###-PRESETS-###
NUMBERS = "012345678"
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT,
              f"{UP}-{LEFT}", f"{UP}-{RIGHT}",
              f"{DOWN}-{LEFT}", f"{DOWN}-{RIGHT}")
POKEMON = "P"
FLAG = "F"
UNEXPOSED = "~"

TASK_ONE = 1
TASK_TWO = 2
###-PRESETS-###

class BoardModel(object):
    """The BoardModel class handles the backend game code.
    This class is responsible for editing, updating and checking
    the game state/string. 
    """
    def __init__(self, grid_size, num_pokemon):
        """Constructs a board model for the given grid size and
        number of pokemon. This includes the initialization of the
        pokemon locations.

        Parameters:
            grid_size (int): the number of cells in each row and column.
            num_pokemon (int): the number of hidden pokemon.        
        """
        super().__init__()
        self._grid_size = grid_size
        self._num_pokemon = num_pokemon
        self._game = UNEXPOSED * (grid_size**2)
        self._pokemon_locations = self.generate_pokemons(grid_size, num_pokemon)

    def get_game(self):
        """Retrieves the game string.

        Returns:
            self._game (str): the game string.
        """
        return self._game

    def get_grid_size(self):
        """Retrieves the grid size.

        Returns:
            self._grid-size (int): the grid size.
        """
        return self._grid_size

    def get_num_pokemon(self):
        """Retrieves the number of pokemon hiden in the game.

        Returns:
            self._num_pokemon (int): the number of pokemon.
        """
        return self._num_pokemon

    def get_pokemon_locations(self):
        """Retrieves the locations of all pokemon in the game.

        Returns:
            self._pokemon_locations (tuple): a tuple containing all pokemon
            locations.
        """
        return self._pokemon_locations

    def generate_pokemons(self, grid_size, number_of_pokemons):
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

    def check_loss(self):
        """This function, when called, checks if the current state of the game
        represents a loss (e.g. if a pokemon is revealed).

        Returns:
            (bool): returns True if the game is lost.
        """
        self.loss = 0
        for value in self._game:
            if value == POKEMON:
                return 1

    def check_win(self):
        """This function, when called, checks if the current state of the game
        represents a win (e.g. if all pokemon are flagged and there are no
        unrevealed grass tiles).

        Returns:
            (bool): returns True if the game is won.
        """
        self.win = 0
        index = -1
        pokemon_caught = 0
        flag_count = 0 #No. flags in game string
        for value in self._game: #Iterates over all values in game string
            index += 1
            if value == FLAG: #Checks if the value at the specified index is flagged
                flag_count += 1
                if index in self._pokemon_locations: #Checks if the flag at the index is a valid pokemon location
                    pokemon_caught += 1

        if pokemon_caught == self._num_pokemon and flag_count == self._num_pokemon and UNEXPOSED not in self._game:
            return 1


    def index_to_position(self, index):
        """Using the specified index in the game string, this function calculates
        the tile position in the format (row, column).

        Parameters:
            index (int): the index in the game string.

        Returns:
            (row, col) (tuple): the position of the tile.
        """
        if index >= 0 and index < self._grid_size**2:
            row = index // self._grid_size
            col = index % self._grid_size
            return (row, col)

    def replace_character_at_index(self, character, index):
        """Replaces a character in the game string at the specified index.
    
        Parameters:
            index (int): Game string index.
            character (str): New character.
        Returns:
            (str): Updated game string.
        """
        game_string = list(self._game)
        game_string[index] = character
        new_game = ""
        
        for i in game_string:
            new_game += str(i)
            
        self._game = new_game

    def index_in_direction(self, index, direction): #Returns the index of the cell from the direction of the given index
        """Returns the index in the game string of the cell in the specified
        direction of the original index cell. Uses the DIRECTION variable in
        a1_support.py code.
        
        Parameters:
            index (int): Game string index.
            direction (str): Direction.
        Returns:
            (int): Game string index.
        """
        grid_size = self._grid_size
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
    
    def neighbour_directions(self, index): #Lists all indexes of all neighbouring cells
        """Lists the indexes of all neighbouring cells within the bounds of the
        game grid.
        
        Parameters:
            index (int): Game string index.
            grid_size (int): Size of the game.
        Returns:
            (list<int>): List of all neighbouring cells' indexes.
        """
        list1 = list()
        for direction in DIRECTIONS:
            output = self.index_in_direction(index, direction)
            if type(output) == int:
                list1.append(output)
        return list1

    def number_at_index(self, index): #Number to show when tile at index is revealed
        """Checks the surrounding cells against the pokemon locations and returns how many
        pokemon are in its' neighbour cells.

        Parameters:
            index (int): Game string index.
        Returns:
            (int): Number of pokemon in neighbouring cells.
        
        """
        number_at_cell = 0
        for i in self.neighbour_directions(index):
            if i in self._pokemon_locations:
                number_at_cell += 1
        return number_at_cell
        
    def big_fun_search(self, index):
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
        game = self._game
        grid_size = self._grid_size
        pokemon_locations = self._pokemon_locations
        queue = [index]
        discovered = [index]
            
        visible = []
        if game[index] == FLAG:
                return queue

        number = self.number_at_index(index)
        if number != 0:
                return queue

        while queue:
                node = queue.pop()
                for neighbour in self.neighbour_directions(node):
                        if neighbour in discovered or neighbour is None:
                                continue

                        discovered.append(neighbour)
                        if game[neighbour] != FLAG:
                                number = self.number_at_index(neighbour)
                                if number == 0:
                                        queue.append(neighbour)
                        visible.append(neighbour)
        return visible

class PokemonGame(object):
    """This is the controller class for the pokemon game. This class is responsible
    for the interaction between the visible interface and the back end game state.
    """
    def __init__(self, master, grid_size=10, num_pokemon=15, task=TASK_TWO):
        """Constructs a game for the given grid size, number of pokemon and task in
        the specified master window.

        Parameters:
            master (str): the window in which to display the game (typically, root).
            grid_size (int): the size of the game.
            num_pokemon (int): the number of hidden pokemon.
            task (str): the specified task number.
        """
        super().__init__()
        self._master = master
        self._grid_size = grid_size
        self._num_pokemon = num_pokemon
        self._task = task

        #Window Configuration
        self._master.title("Pokemon: Got2 Find Them All!")

        self._title = tk.Label(master, text = "Pokemon: Got 2 Find Them All!", bg="#d46e69", fg="white")
        self._title.config(font=("Comic Sans MS", 16, "bold"))
        self._title.pack(side = tk.TOP, anchor=tk.N, fill=tk.X)

        #Game Initialisation
        self.board_model = BoardModel(grid_size, num_pokemon)
        
        if task == 1:
            self.board_view = BoardView(master, grid_size)
            self.board_view.draw_board(self.board_model.get_game())
        
        elif task == 2:
            self.board_view = ImageBoardView(master, grid_size)
            self.board_view.draw_board(self.board_model.get_game())
            self.status_bar = StatusBar(master, num_pokemon, self.board_model.get_game())
            self.status_bar.pack(side=tk.TOP, anchor=tk.N)
            FileMenu(master)
            
        #Bindings
        self.board_view.bind('<Button-3>', self.right_click)
        self.board_view.bind('<Button-2>', self.right_click)
        self.board_view.bind("<Button-1>", self.left_click)
        

    def check_game_state(self):
        """This function is called on every left or right click to check the game
        state and if a win or loss has occurred, create the necessary end of game
        popup window.
        """
        self._game_state = ""
        win = self.board_model.check_win()
        loss = self.board_model.check_loss()
        
        if win == 1:
            self._game_state = "You won!"

        elif loss == 1:
            self._game_state = "You lose."
        
        if self._game_state != "":
            self.end = tk.Tk()
            self.end.title("Game over")
            self.end.geometry("400x125")
            label1 = tk.Label(self.end, text=f"{self._game_state}", pady=5)
            label1.config(font=12)
            label1.pack()

            label2 = tk.Label(self.end, text="Would you like to play again?", pady=10)
            label2.config(font=10)
            label2.pack()

            button1 = tk.Button(self.end, text="Yes", command=self.restart)
            button1.pack(side=tk.LEFT, anchor=tk.N, ipadx=20, pady=10, expand=1)

            button1 = tk.Button(self.end, text="No", command=self.exit)
            button1.pack(side=tk.LEFT, anchor=tk.N, ipadx=20, pady=10, expand=1)            

    def left_click(self, e):
        """This function handles the left click event. When called, this function
        updates the game board with the new game string and calls for the GUI to
        be updated.

        Parameters:
            e (tuple): the coordinates of the mouse when pressed.
        """
        game = self.board_model.get_game()
        position = self.board_view.pixel_to_position((e.x, e.y))
        index = round(position[0]*self._grid_size + position[1])

        if game[index] == UNEXPOSED: #If tall grass
            if index in self.board_model.get_pokemon_locations(): #If pokemon
                for instance in self.board_model.get_pokemon_locations():
                    self.board_model.replace_character_at_index(POKEMON, instance)

            else:
                number = self.board_model.number_at_index(index)
                self.board_model.replace_character_at_index(number, index)
                
                if number == 0:
                    visible = self.board_model.big_fun_search(index)
                    
                    for instance in visible:
                        number = self.board_model.number_at_index(instance)
                        self.board_model.replace_character_at_index(number, instance)
        
        self.board_view.draw_board(self.board_model.get_game())
        self.check_game_state()

    def right_click(self, e):
        """This function handles the right click event. When called, this function
        updates the game board with the new game string and calls for the GUI to
        be updated.

        Parameters:
            e (tuple): the coordinates of the mouse when pressed.
        """
        position = self.board_view.pixel_to_position((e.x, e.y))
        index = round(position[0]*self._grid_size + position[1])
        flag_count = 0

        for instance in self.board_model.get_game():
            if instance == FLAG:
                flag_count += 1

        if self.board_model.get_game()[index] == UNEXPOSED and flag_count < self._num_pokemon:
            self.board_model.replace_character_at_index(FLAG, index)
            
        elif self.board_model.get_game()[index] == FLAG:
            self.board_model.replace_character_at_index(UNEXPOSED, index)
            
        self.board_view.draw_board(self.board_model.get_game())
        self.check_game_state()
        
        if self._task == 2:
            self.status_bar.update_num_catches(self.board_model.get_game())

    def restart(self):
        """This function handles the restarting of the game by closing all windows and
        calling the main() function.
        """
        self.end.destroy()
        root.destroy()
        main()

    def exit(self):
        """This function handles the exiting of the game by closing all windows.
        """
        exit()

class BoardView(tk.Canvas):
    """This is the class that controls the GUI when task=TASK_ONE. This class is
    responsible for updating the GUI and calculating the bounding box, center
    pixel and the position of tiles. This class inherits from tk.Canvas.
    """
    def __init__(self, master, grid_size, board_width=600, *args, **kwargs):
        """Constructs a board view using the given grid size, board width,
        args and kwargs for the master window.

        Parameters:
            master (str): the window in which to display the game (typically, root).
            grid_size (int): the size of the game.
            board_width (int): the board width.
        """
        super().__init__(master, width=board_width, height=board_width, borderwidth=0, highlightthickness=0, *args, **kwargs)
        self._master = master
        self._grid_size = grid_size
        self._board_width = board_width

    def draw_board(self, board):
        """This function refreshes the board view and draws the game using the
        specified board (game string).

        Parameters:
            board (str): the game string.
        """
        self.delete("all")
        width = self._board_width
        grid_size = self._grid_size
        game = board
        
        row_count = -1
        game_count = 0
        index = 0
        
        while row_count < grid_size - 1:
            col_count = 0
            row_count += 1
            
            while col_count < grid_size:
                    instance = game[index]
                    index += 1
                    game_count += 1

                    x1 = col_count*(width/grid_size)
                    x2 = (col_count+1)*(width/grid_size)
                    y1 = row_count*(width/grid_size)
                    y2 = (row_count+1)*(width/grid_size)

                    if instance == UNEXPOSED:
                        colour = "dark green"

                    elif instance == POKEMON:
                        colour = "yellow" 

                    elif instance == FLAG:
                        colour = "red"

                    elif instance in NUMBERS:
                        colour = "light green"

                    self.create_rectangle(x1, y1, x2, y2, fill=colour)
                    col_count += 1

                    if instance in NUMBERS:
                        self.create_text(x2-(width/grid_size)/2, y1+(width/grid_size)/2, text=instance)
        self.pack(side=tk.TOP, anchor=tk.N)

    def get_bbox(self, pixel):
        """This function calculates the bounding box of tile at the specified
        pixel coordinates. 

        Parameters:
            pixel (tuple): a tuple containing the pixel coordinates.

        Returns:
            (x1, y1, x2, y2) (tuple): a tuple containing the bounding box.
        """
        width = self._board_width
        grid_size = self._grid_size
        x, y = pixel
        x1 = (x//(width/grid_size))*(width/grid_size)
        x2 = x1+(width/grid_size)
        y1 = (y//(width/grid_size))*(width/grid_size)
        y2 = y1+(width/grid_size)
        return (x1, y1, x2, y2)

    def position_to_pixel(self, position):
        """This function calculates the center pixel of the tile at the
        given position.

        Parameters:
            position (tuple): a tuple containing the position of the tile (row, column).

        Returns:
            (x, y) (tuple): the center pixel of the specified tile.
        """
        width = self._board_width
        grid_size = self._grid_size
        row, col = position
        x = (col*(width/grid_size))+(width/grid_size)/2
        y = (row*(width/grid_size))+(width/grid_size)/2
        return (x, y)

    def pixel_to_position(self, pixel):
        """This function calculates the position of the tile at the given
        pixel coordinates.

        Parameters:
            pixel (tuple): a tuple containing the pixel coordinates.

        Returns:
            position (tuple): a tuple containing the position (row, column).
        """
        width = self._board_width
        grid_size = self._grid_size
        x, y = pixel
        position = (y//(width/grid_size)), (x//(width/grid_size))
        return position


class StatusBar(tk.Frame):
    """This class is responsible for updating, modifying and drawing the status bar
    when task=TASK_TWO. This class inherits from tk.Frame.
    """
    def __init__(self, master, num_pokemon, game):
        """Constructs a status bar with the given number of pokemon and game string
        in the specified master window.

        Parameters:
            master (str): the master window.
            num_pokemon (int): then number of pokemon in the game.
            game (str): the game string.
        """
        super().__init__(master, width=600, height=70, bg="white")
        
        self._master = master
        self._num_pokemon = num_pokemon
        self._game = game
        self._time = -1

        #Image Referencing
        images_open = [
            Image.open(r"images\clock.png"),
            Image.open(r"images\empty_pokeball.png")
            ]
        
        self._images = [
            ImageTk.PhotoImage(images_open[0]),
            ImageTk.PhotoImage(images_open[1])
            ]

        #Defining Variable to display on Status Bar
        num_catches = 0
        for instance in game:
            if instance == FLAG:
                num_catches += 1

        num_pokeballs_left = num_pokemon - num_catches

        #Labels
        pokeball = tk.Label(self, image=self._images[1], borderwidth=0)
        pokeball.place(x=75, y=8)
        
        attempted_catches = tk.Label(self, text=f"{num_catches} attempted catches", bg="white")
        attempted_catches.place(x=130, y=15)

        pokeballs_left = tk.Label(self, text=f"{num_pokeballs_left} pokeballs left", bg="white")
        pokeballs_left.place(x=130, y=32)
        
        clock = tk.Label(self, image=self._images[0], borderwidth=0)
        clock.place(x=250, y=10)

        time_elapsed_label = tk.Label(self, text="Time elapsed", bg="white")
        time_elapsed_label.place(x=310, y=15)

        #Buttons
        new_game = tk.Button(self, text="New game", command=self.new_game)
        new_game.place(x=450, y=8)

        restart_game = tk.Button(self, text="Restart game", command=self.restart_game)
        restart_game.place(x=443, y=37)

        self.update()

    def update(self):
        """This function updates the status bar timer and redraws it.
        This function is repeated every 1000ms to ensure the timer is
        up do date every second.
        """
        self._time += 1

        minutes = self._time//60
        seconds = self._time%60
            
        time_elapsed = tk.Label(self, text=f"{minutes}m {seconds}s", bg="white")
        time_elapsed.place(x=325, y=32)
            
        self.after(1000, self.update)

    def update_num_catches(self, game):
        """This function updates the number of attempted catches and pokeballs
        left and redraws them into the status bar.

        Parameters:
            game (str): the game string.
        """
        num_catches = 0
        for instance in game:
            if instance == FLAG:
                num_catches += 1

        num_pokeballs_left = self._num_pokemon - num_catches
        
        attempted_catches = tk.Label(self, text=f"{num_catches} attempted catches", bg="white")
        attempted_catches.place(x=130, y=15)

        pokeballs_left = tk.Label(self, text=f"{num_pokeballs_left} pokeballs left", bg="white")
        pokeballs_left.place(x=130, y=32)

    def new_game(self):
        """This function handles the event of a new game by closing the root
        window and restarting main()        
        """
        root.destroy()
        main()

    def restart_game(self):
        """This function handles restarting the game with the same pokemon
        locations.        
        """
        self._time = -1
        pokemongame.board_model._game = UNEXPOSED * pokemongame._grid_size**2
        pokemongame.board_view.draw_board(pokemongame.board_model.get_game())        

class ImageBoardView(BoardView):
    """This class is responsible for drawing the game board when
    task=TASK_TWO. This includes drawing, modifying and updating the
    board GUI. This class inherits from BoardView.
    """
    def __init__(self, master, grid_size, board_width=600):
        """Constructs a board GUI with the given grid size and board width
        in the specified master window.

        Parameters:
            master (str): the master window (typically root).
            grid_size (int): the size of the grid.
            board_width (int): the board width in pixels.
        """
        super().__init__(master, grid_size)
        self._master = master
        self._grid_size = grid_size
        self._board_width = board_width       

    def draw_board(self, board):
        """This functions draws the board GUI from the given board (game string).

        Parameters:
            board (str): the game string.        
        """
        #Variables
        width = self._board_width
        grid_size = self._grid_size
        game = board
        
        pixels_x = int(width/grid_size)
        pixels_y = pixels_x
        
        #Image Referencing
        self._images = [
            ImageTk.PhotoImage(Image.open(r"images\pokeball.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\unrevealed.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\charizard.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\cyndaquil.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\pikachu.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\psyduck.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\togepi.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\pokemon_sprites\umbreon.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\zero_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\one_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\two_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\three_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\four_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\five_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\six_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\seven_adjacent.png").resize((pixels_x, pixels_y))),
            ImageTk.PhotoImage(Image.open(r"images\eight_adjacent.png").resize((pixels_x, pixels_y)))
            ]
        
        #Logic
        row_count = -1
        index = 0
        while row_count < grid_size - 1:
            col_count = -1
            row_count += 1
            
            while col_count < grid_size - 1:
                    instance = game[index]
                    index += 1
                    col_count += 1
                    
                    x1, y1 = self.position_to_pixel((row_count, col_count))

                    if instance == UNEXPOSED:
                        self.create_image(x1, y1, image=self._images[1])

                    elif instance == POKEMON:
                        random_index = random.randint(2, 7)
                        self.create_image(x1, y1, image=self._images[random_index])

                    elif instance == FLAG:
                        self.create_image(x1, y1, image=self._images[0])

                    elif instance in NUMBERS:
                        number_index = int(instance) + 8
                        self.create_image(x1, y1, image=self._images[number_index])
                        
        self.pack(side=tk.TOP, anchor=tk.N)    
                    
        
    def get_bbox(self, pixel):
        """This function calculates the bounding box of tile at the specified
        pixel coordinates. 

        Parameters:
            pixel (tuple): a tuple containing the pixel coordinates.

        Returns:
            (x1, y1, x2, y2) (tuple): a tuple containing the bounding box.
        """
        width = self._board_width
        grid_size = self._grid_size
        x, y = pixel
        x1 = (x//(width/grid_size))*(width/grid_size)
        x2 = x1+(width/grid_size)
        y1 = (y//(width/grid_size))*(width/grid_size)
        y2 = y1+(width/grid_size)
        return (x1, y1, x2, y2)

    def position_to_pixel(self, position):
        """This function calculates the center pixel of the tile at the
        given position.

        Parameters:
            position (tuple): a tuple containing the position of the tile (row, column).

        Returns:
            (x, y) (tuple): the center pixel of the specified tile.
        """
        width = self._board_width
        grid_size = self._grid_size
        row, col = position
        x = (col*(width/grid_size))+(width/grid_size)/2
        y = (row*(width/grid_size))+(width/grid_size)/2
        return (x, y)

    def pixel_to_position(self, pixel):
        """This function calculates the position of the tile at the given
        pixel coordinates.

        Parameters:
            pixel (tuple): a tuple containing the pixel coordinates.

        Returns:
            position (tuple): a tuple containing the position (row, column).
        """
        width = self._board_width
        grid_size = self._grid_size
        x, y = pixel
        position = (y//(width/grid_size)), (x//(width/grid_size))
        return position

class FileMenu(object):
    """This class is responsible for the file menu which holds the options
    to save, load, restart, quit and create a new game.
    """
    def __init__(self, master):
        """Constructs a file menu in the specified master window.

        Parameters:
            master (str): the master window (typically root).
        """
        self._master = master

        menubar = tk.Menu(self._master)
        self._master.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        
        filemenu.add_command(label="Save game", command=self.save_game)
        filemenu.add_command(label="Load game", command=self.load_game)
        filemenu.add_command(label="Restart game", command=self.restart_game)
        filemenu.add_command(label="New game", command=self.new_game)
        filemenu.add_command(label="Quit", command=self.quit)

    def save_game(self):
        """This function controls saving the game to the specified directory
        and file name using the asksaveasfilename commmand.
        """
        save_data = []
        save_data.append(pokemongame.board_model.get_game())
        save_data.append(str(pokemongame.board_model.get_pokemon_locations()))
        save_data.append(str(pokemongame.status_bar._time))

        save_file = (asksaveasfilename(defaultextension=".txt",
                                      filetypes=[("All files", "*.*")],
                                      initialfile="save_file.txt"))
        if save_file != "":
            file = open(save_file, mode="w")
            file.write(str(save_data))

    def load_game(self):
        """This function controls loading the game from the specified directory
        and file name using the askopenfilename commmand.
        """
        file_dir = askopenfilename()
        if file_dir != "":
            load_data = open(file_dir, "r")
            data = load_data.read()
            data_split = data.split("', '")

            game_string = data_split[0][2::]
            pokemon_locations_raw = data_split[1][1:-1].split(", ")
            pokemongame.status_bar._time = int(data_split[2][0:-2])
            
            pokemon_locations = ()
            for instance in pokemon_locations_raw:
                pokemon_locations += (int(instance),)

            pokemongame.board_model._pokemon_locations = pokemon_locations
            pokemongame.board_model._game = game_string        

            pokemongame.board_view.draw_board(pokemongame.board_model.get_game())
            pokemongame.check_game_state()

    def restart_game(self):
        """This function handles restarting the game with the same pokemon
        locations.        
        """
        pokemongame.status_bar._time = -1
        pokemongame.board_model._game = UNEXPOSED * pokemongame._grid_size**2
        pokemongame.board_view.draw_board(pokemongame.board_model.get_game())

    def new_game(self):
        """This function handles the event of a new game by closing the root
        window and restarting main()        
        """
        root.destroy()
        main()
    
    def quit(self):
        """This function, when called, quits the game.
        """
        exit()

def main():
    """Main holds the code to run at startup and when the
    program is called to restart. This code creates the root
    window for the tkinter package. Both root and pokemongame
    are global to allow nested functions to access the
    required parameters.
    """
    global root
    global pokemongame
    root = tk.Tk()
    pokemongame = PokemonGame(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
