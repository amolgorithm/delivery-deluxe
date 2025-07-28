"""
-Name: Amol Sriprasadh
-Date started: May 7, 2025
-Date completed: May 9, 2025
-Game title: Delivery Deluxe (GTA 5.5)
-Brief description: This module provides classes and functions for generating a grid-based map
for the driving simulation game, Delivery Deluxe, resembling a Manhattan-style grid.
"""
import random
import string


"""
Alphabet letters represent delivery locations.
'+' represents a fuel stop (gas station).
'$' represents the starting location.
'@' represents the ending location.
'?' represents a mystery location that can offer a gift.
"""

class ManhattanGrid:
	"""
	Represents a grid-based map with buildings and roads, structured like a Manhattan grid.

	This class manages the placement of buildings, roads, and special locations
	within a 2D grid, and provides methods for accessing and manipulating grid elements.
	"""
	def __init__(self, buildings_rows, buildings_cols, default_building_label, default_road_label):
		"""
		Initializes the ManhattanGrid.

		The grid is internally represented by two 2D lists: one for buildings
		and one for road intersections.

		Parameters:
		 - buildings_rows (int): The number of rows for the building grid.
		 - buildings_cols (int): The number of columns for the building grid.
		 - default_building_label (str): The default character label for empty building cells.
		 - default_road_label (str): The default character label for road intersection cells.
		Returns: None
		"""
		# Full grid is expanded to hold roads in between
		self.rows = buildings_rows
		self.cols = buildings_cols
		self.buildings_grid = [[default_building_label for j in range(self.cols)] for i in range(self.rows)]
		self.road_isx_grid = [[default_road_label for j in range(self.cols - 1)] for i in range(self.rows - 1)]
		self.streets = []
	
	def __getitem__(self, pos):
		"""
		Allows accessing a building cell's label using grid[row, col] syntax.

		Parameters:
		 - pos (tuple): A tuple (row, col) representing the coordinates of the building cell.
		Returns:
		 - str: The label of the building at the specified position.
		"""
		row, col = pos
		return self.buildings_grid[row][col]
		
	def __setitem__(self, pos, label):
		"""
		Allows setting a building cell's label using grid[row, col] = label syntax.

		Parameters:
		 - pos (tuple): A tuple (row, col) representing the coordinates of the building cell.
		 - label (str): The new label (character) to set for the building cell.
		Returns: None
		"""
		row, col = pos
		self.buildings_grid[row][col] = label
		
	def roadisx_get(self, row, col):
		"""
		Retrieves the label of a road intersection cell.

		Parameters:
		 - row (int): The row index of the intersection.
		 - col (int): The column index of the intersection.
		Returns:
		 - str: The label of the road intersection at the specified position.
		"""
		return self.road_isx_grid[row][col]
	
	def roadisx_set(self, row, col, label):
		"""
		Sets the label of a road intersection cell.

		Parameters:
		 - row (int): The row index of the intersection.
		 - col (int): The column index of the intersection.
		 - label (str): The new label (character) to set for the road intersection.
		Returns:
		 - str: The updated label of the road intersection.
		"""
		self.road_isx_grid[row][col] = label
		return self.road_isx_grid[row][col]

	def show(self):
		"""
		Prints a visual representation of the grid to the console.

		Displays both the building grid and the road intersection grid,
		along with their associated street indices for debugging or overview.
		Returns: None
		"""
		isx_to_street_index = {}
		# Populate a dictionary mapping intersection coordinates to their street index
		for idx, street in enumerate(self.streets):
			for (r, c) in street:
				isx_to_street_index[(r, c)] = idx

		for i in range(self.rows):
			# Print building row.
			print(' '.join(self.buildings_grid[i]))

			# Print intersections and street indices
			if i < self.rows - 1:
				row_display = []
				for j in range(self.cols - 1):
					isx_label = self.road_isx_grid[i][j]
					# get street index for the current intersection
					street_index = self.get_street_idx((i, j))
					row_display.append(f"{isx_label}{street_index}")
				print(' ' + ' '.join(row_display))
	
	def get_streets(self):
		"""
		Returns the list of generated street segments.

		Returns:
		 - list: A list where each element is a street, and each street is a list of (row, col) tuples
				 representing the intersections that form that street.
		"""
		return self.streets
		
	def get_street_idx(self, pos):
		"""
		Retrieves the index of the street that a given intersection belongs to.

		Parameters:
		 - pos (tuple): A tuple (row, col) representing the coordinates of the intersection.
		Returns:
		 - int or None: The integer index of the street, or None if the position is not part of any street.
		"""
		isx_to_street_index = {}
		# Create a mapping from intersection (row, col) to its street index
		for idx, street in enumerate(self.streets):
			for (r, c) in street:
				isx_to_street_index[(r, c)] = idx
		
		return isx_to_street_index.get(pos)
	
	def set_streets(self):
		"""
		Generates a Manhattan-style grid of horizontal streets.

		This method populates the `road_isx_grid` with roads (represented by '.')
		by creating horizontal streets, one for each row of intersections.
		It marks these roads on the grid and stores them internally.

		Returns:
		 - list: The list of generated street segments.
		"""
		rows, cols = self.rows - 1, self.cols - 1
		unvisited = {(r, c) for r in range(rows) for c in range(cols)} # Set of all intersection points
		streets = []

		# Start with a random initial point in the unvisited set
		start_pos = random.choice(list(unvisited))
		street = [start_pos]
		unvisited.remove(start_pos)

		horizontal_streets = []
		
		# Create horizontal streets: one row at a time
		for row in range(rows):
			street = []
			for col in range(cols):
				pos = (row, col)
				street.append(pos)
				unvisited.discard(pos) # Remove from unvisited set as it's part of a street
			horizontal_streets.append(street)


		# Add streets to the grid
		streets.extend(horizontal_streets)
		
		# Mark streets on the grid with the default road label ('.')
		for street in streets:
			for pos in street:
				self.roadisx_set(pos[0], pos[1], '.')
		
		# Store the created streets in the instance variable
		self.streets = streets
		return streets


def manhattan(p1, p2):
	"""
	Calculates the Manhattan distance (L1 distance) between two points.

	The Manhattan distance is the sum of the absolute differences of their coordinates.
	It represents the distance a taxi would travel in a grid-like city.

	Parameters:
	 - p1 (tuple): The coordinates of the first point (row, col).
	 - p2 (tuple): The coordinates of the second point (row, col).
	Returns:
	 - int: The Manhattan distance between p1 and p2.
	"""
	return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def generate_map(rows, cols, num_locations, road_types):
	"""
	Generates a game map with a Manhattan-style grid, including special locations and roads.

	This function creates a `ManhattanGrid` instance, places an end location,
	multiple fuel stops, and a specified number of delivery locations. It then
	sets up the streets and assigns random road types (with associated speeds)
	to them.

	Parameters:
	 - rows (int): The number of rows for the building grid.
	 - cols (int): The number of columns for the building grid.
	 - num_locations (int): The number of unique delivery locations (A-Z) to place.
	 - road_types (dict): A dictionary mapping road character labels to their associated speed/cost.
	Returns:
	 - ManhattanGrid: An initialized and populated `ManhattanGrid` object representing the game map.
	"""
	# Initialize the grid with default building and road labels.
	grid = ManhattanGrid(rows, cols, '#', next(iter(road_types)))

	# Helper function to place a label at a random, empty building spot
	def place_label(label):
		"""
		Places a given label at a random, unoccupied building cell on the grid.

		Parameters:
		 - label (str): The character label to place (e.g., '@', '+', 'A').
		Returns: None
		"""
		while True:
			x, y = random.randint(0, cols - 1), random.randint(0, rows - 1)
			if grid[y, x] == '#': # Check if the spot is empty
				grid[y, x] = label
				break

	# Place special fixed locations
	place_label('+')  # Place multiple fuel stops
	place_label('+')
	place_label('+')
	place_label('+')

	# Place delivery locations (A, B, C, ..., Z)
	for i in range(num_locations):
		label = string.ascii_uppercase[i] # Get uppercase letter
		place_label(label) # Place the delivery label
		
	# Generate the main street layout
	grid.set_streets()
	
	# Assign random road types to the generated streets
	for street in grid.get_streets():
		road_type = random.choice(list(road_types.keys())) # Choose a random road type
		# Apply the chosen road type to all intersections in the current street
		for isx in street:
			grid.roadisx_set(isx[0], isx[1], road_type)

	return grid
