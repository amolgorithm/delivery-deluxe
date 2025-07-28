"""
-Name: Amol Sriprasadh
-Date started: May 7, 2025
-Date completed: June 11, 2025
-Game title: Delivery Deluxe (GTA 5.5)
-Brief description: Delivery Deluxe is a 3D driving simulation game where players navigate a city to
 pick up and deliver packages within a time limit, managing fuel and avoiding fines. The game features
 a dynamic day-night cycle, a customizable garage for vehicle selection and color customization, and an
 interactive minimap. Players earn money for successful deliveries, which can be used to refuel. The game
 ends if the player runs out of fuel or fails too many deliveries. More detailed explanations of game
 objectives and rules are mentioned on the README file.
"""
import random
from math import *
from queue import PriorityQueue
from direct.actor.Actor import Actor
from direct.showbase import Audio3DManager
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.task import Task
from panda3d.core import *
from panda3d.bullet import *
import grid_map

loadPrcFileData("", "load-file-type p3assimp")		   # Use glTF loader
loadPrcFileData("", "basic-shaders-only #f")		   # Enable advanced shaders
loadPrcFileData("", "materials-enable true")		   # Enable PBR materials
loadPrcFileData("", "gl-coordinate-system default")				   # Match GLTF axis
loadPrcFileData("", "win-size 1000 750")						   # Set window dimensions
loadPrcFileData("", "window-title Delivery Deluxe (GTA 5.5)")   # Set window title

MINIMAP_MASK = BitMask32.bit(1)

ROWS = 20
COLUMNS = 20
NUM_LOCATIONS = 10
ROAD_TYPES = {
	'.': 15,
	':': 25,
	';': 35,
	',': 50,
	'*': 70,
	'%': 100
}

g_map = grid_map.generate_map(ROWS, COLUMNS, NUM_LOCATIONS, ROAD_TYPES)


class MyApp(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)
		
		# Game state control
		self.game_state = "start"  # can be: start, garage, game, win, loss
		self.ui_elements = []	  # for UI cleanup
		self.garage_elements = []  # garage-specific elements
		self.game_elements = []	# game-specific elements
		
		# Initialize game variables with default values
		self.init_game_variables()
		
		# Start with the start screen
		self.switch_screen("start")
		
		# Setup audio manager (used across all screens)
		self.audio3d = Audio3DManager.Audio3DManager(self.sfxManagerList[0], self.camera)
		
		# BG Music (plays across all screens)
		self.music = self.loader.loadSfx("./assets/sfx/bgm.mp3")
		self.music.setLoop(True)
		self.music.setVolume(0.05)
		self.music.play()
		
		# Day-night cycle (only active in game)
		self.time_of_day = 0.3
		self.time_direction = 1
		
		# Accept escape key to quit from any screen
		self.accept("escape", self.user_exit)
	
	# =============================================
	# Core Game Initialization and State Management
	# =============================================
	
	def init_game_variables(self):
		"""
		Initializes or resets all dynamic game variables to their default values.
		This method is called at the start of the application and when a new game
		is initiated (e.g., after a win/loss screen). It sets up physics,
		vehicle properties, NPC data, and core game metrics.
		
		Params: None
		Returns: None
		"""

		# Physics world (only created when entering game)
		self.world = None
		
		# Vehicle properties
		self.chassisNP = None
		self.vehicle_models = [{    # Properties/stats for every single vehicle model from which the user can choose.
									"file_path": "./assets/models/cars/porsche.glb",
									"model_scale": 130,
									"name": "Porsche 992",
									"tier": "D",
									"mass": 800.0,
									"acceleration": 5.0,
									"handling_coeff": 0.6,
									"fuel_consumption": 0.002
								},
								{
									"file_path": "./assets/models/cars/mazda.glb",
									"model_scale": 1.3,
									"name": "Mclaren Furai",
									"tier": "C",
									"mass": 600.0,
									"acceleration": 7.0,
									"handling_coeff": 0.7,
									"fuel_consumption": 0.002
								},
								{
									"file_path": "./assets/models/cars/mclaren.glb",
									"model_scale": 1.1,
									"name": "Mclaren Gold",
									"tier": "B",
									"mass": 800.0,
									"acceleration": 6.0,
									"handling_coeff": 0.8,
									"fuel_consumption": 0.0015
								},
								{
									"file_path": "./assets/models/cars/mercedes.glb",
									"model_scale": 1.5,
									"name": "Mercedes AMG One",
									"tier": "A",
									"mass": 850.0,
									"acceleration": 7.0,
									"handling_coeff": 0.9,
									"fuel_consumption": 0.001
								},
								{
									"file_path": "./assets/models/cars/corvette.glb",
									"model_scale": 1.1,
									"name": "Corvette C9",
									"tier": "S",
									"mass": 900.0,
									"acceleration": 7.5,
									"handling_coeff": 0.9,
									"fuel_consumption": 0.0007
								},
								{
									"file_path": "./assets/models/cars/lamborghini.glb",
									"model_scale": 1.2,
									"name": "Lamborghini Aventador",
									"tier": "S",
									"mass": 850.0,
									"acceleration": 8.0,
									"handling_coeff": 1.0,
									"fuel_consumption": 0.0007
								}
						]
		self.vehicle_model_idx = 0
		self.vehicle_color = Vec4(1, 1, 1, 1)  # Default white
		
		# NPC variables
		self.npcs = []  # List to store NPCs
		self.npc_collision_group = 2  # Collision group for NPCs
		self.last_fine_time = 0  # To prevent rapid fines
		
		# Game state
		self.fuel_level = 100.0
		self.money = 30
		self.delivery_target = None
		self.delivery_time_left = 0
		self.delivery_reward = 0
		self.total_delivery_count = 0
		self.successful_delivery_count = 0
		self.delivery_scores = []
		self.speeding_timer = 0.0
		
		# Camera
		self.cameraTarget = Point3(0, 0, 0)
		self.zoom_distance = 24
		self.camera_heading = 0.0
		self.is_rotating = False
		
		# Mouse
		self.is_dragging = False
		self.last_mouse_pos = None
		
		# Controls
		self.key_map = {
			"forward": False, 
			"backward": False, 
			"left": False, 
			"right": False,
			"brake": False,
			"escape": False,
		}
		
		# Minimap
		self.minimap_root = None
		self.minimap_zoom_coeff = 1
		
		# Autopilot control
		self.autopilot_used = False
		self.autopilot_button = None
		
		# UI elements
		self.ui_bg = None
		self.ui_text = None
		self.delivery_text = None
		self.delivery_timer = None
		self.del_wins_text = None
		self.del_losses_text = None
		self.speedometer_dial = None
		self.needle_pivot = None
		self.speedometer_needle = None
		self.fuelguage_dial = None
		self.fgneedle_pivot = None
		self.fuelguage_needle = None
		self.money_bar = None
		self.money_text = None
		self.speeding_box = None
		self.speeding_text = None
		self._show_warning_timer = 0.0
		self._is_flashing_on = True
	
	def setup_controls(self):
		"""
		Configures keyboard and mouse controls based on the current game state.
		This function clears all previous key bindings and sets up new ones relevant
		to the active screen (start, garage, game, win/loss).
		
		Params: None
		Returns: None
		"""
		
		# Clear all existing key bindings
		self.ignoreAll()
		
		# Common controls
		self.accept("escape", self.user_exit)
		
		if self.game_state == "start":
			self.accept("mouse1", self.start_button_click)
			
			
		elif self.game_state == "game":
			# Mouse controls
			self.accept("wheel_up", self.zoom_in)
			self.accept("wheel_down", self.zoom_out)
			
			# Movement keys
			self.accept("arrow_up", self.set_key, ["forward", True])
			self.accept("arrow_up-up", self.set_key, ["forward", False])
			self.accept("arrow_down", self.set_key, ["backward", True])
			self.accept("arrow_down-up", self.set_key, ["backward", False])
			self.accept("arrow_left", self.set_key, ["left", True])
			self.accept("arrow_left-up", self.set_key, ["left", False])
			self.accept("arrow_right", self.set_key, ["right", True])
			self.accept("arrow_right-up", self.set_key, ["right", False])
			self.accept("space", self.set_key, ["brake", True])
			self.accept("space-up", self.set_key, ["brake", False])
			self.accept("escape", self.set_key, ["escape", True])
			
			# Gameplay keys
			self.accept("z", self.minimap_zoom, [1])
			self.accept("x", self.minimap_zoom, [-1])
			self.accept("c", self.refuel, [g_map])
			self.accept("v", self.complete_delivery)
			
		elif self.game_state in ["win", "loss"]:
			self.accept("mouse1", self.restart_game)
	
	def set_key(self, key, value):
		"""
		Sets the state of a specific key in the key_map.
		This method is used as a callback for Panda3D's event system
		to update the internal state of keyboard inputs.

		Params:
		 - key (str): The name of the key to set (e.g., "forward", "brake").
		 - value (bool): The new state of the key (True for pressed, False for released).
		Returns: None
		"""
		
		if key in self.key_map:
			self.key_map[key] = value
	
	def switch_screen(self, new_state):
		"""
		Transitions the game to a new screen state by cleaning up resources from
		the previous screen, sets up the new screen's visual elements, and configures its specific controls.

		Params:
		 - new_state (str): The name of the new game state to switch to
							("start", "garage", "game", "win", "loss").
		Returns: None
		"""
		self.game_state = new_state
		
		# Setup new state
		if new_state == "start":
			self.cleanup_previous_state()  # Clean up previous state
			self.show_start_screen()
			self.setup_controls()  # Setup controls for new state
		elif new_state == "garage":
			self.cleanup_previous_state()  # Clean up previous state
			self.show_garage_screen()
			self.setup_controls()  # Setup controls for new state
		elif new_state == "game":
			self.cleanup_previous_state()  # Clean up previous state
			self.start_gameplay()
			self.setup_controls()  # Setup controls for new state
		elif new_state == "win":
			self.show_end_screen(True)
		elif new_state == "loss":
			self.show_end_screen(False)
	
	def cleanup_previous_state(self):
		"""
		Cleans up all active UI elements, tasks, physics world, and 3D nodes
		from the previous game state to prepare for a new screen.
		This prevents memory leaks and ensures a clean transition between screens.
		
		Params: None
		Returns: None
		"""
		# Remove all UI elements
		for element in self.ui_elements + self.garage_elements + self.game_elements:
			element.destroy()
		self.ui_elements.clear()
		self.garage_elements.clear()
		self.game_elements.clear()
		
		# Stop all tasks
		self.taskMgr.remove("rotateGarageCar")
		self.taskMgr.remove("update")
		self.taskMgr.remove("updateCamera")
		self.taskMgr.remove("updateMinimap")
		self.taskMgr.remove("updateDashboard")
		self.taskMgr.remove("handleSpeeding")
		self.taskMgr.remove("updateDelivery")
		self.taskMgr.remove("UpdateLightingTask")
		
		# Clean up physics world if it exists
		if hasattr(self, 'world') and self.world:
			self.world = None
		
		# Hide everything
		self.render.hide()
		self.camera.hide()
		
		# Clean up garage if it exists
		if hasattr(self, 'garage_render'):
			self.garage_render.removeNode()
			del self.garage_render
		
		# Clean up vehicle if it exists
		if hasattr(self, 'chassisNP') and self.chassisNP:
			self.chassisNP.removeNode()
			self.chassisNP = None
			
		# Remove NPCs
		if hasattr(self, "npcs") and self.npcs:
			for npc in self.npcs:
				npc['node'].removeNode()
				npc['actor'].cleanup()
			self.npcs = []
	
	def user_exit(self):
		"""
		Handles the user-initiated exit sequence.
		Performs necessary cleanup of all game resources before
		terminating the Panda3D application.
		
		Params: None
		Returns: None
		"""
		self.cleanup_previous_state()
		base.userExit()
	
	# =============================================
	# Start Screen Methods
	# =============================================
	
	def show_start_screen(self):
		"""
		Displays the 2D start screen with a background image, game title,
		a "Start Game" button (which allows the user to progress to the garage screen), and game instructions.
		
		Params: None
		Returns: None
		"""
		
		# Setup 2D background
		bg = OnscreenImage(
			image="./assets/images/start_bg.jpg", 
			pos=(0, 0, 0), 
			scale=(1.4, 1, 1))
		
		# Title text
		title = OnscreenText(
			text="Delivery Deluxe (GTA V.V)",
			pos=(0, 0.5),
			scale=0.15,
			fg=(1, 1, 1, 1),
			shadow=(0, 0, 0, 0.5),
			align=TextNode.ACenter,
			font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
		)
		
		# Start button
		start_btn = DirectButton(
			text="Start Game",
			scale=0.1,
			pos=(0, 0, -0.1),
			command=self.switch_screen,
			extraArgs=["garage"],
			frameColor=(0.2, 0.6, 0.2, 1),
			text_fg=(1, 1, 1, 1),
			text_scale=0.8,
			relief=DGG.RAISED
		)
		
		# Instructions
		instructions = OnscreenText(
			text="Use arrow keys to drive\nSpace to manual brake\nV to complete delivery\nC to refuel at gas stations\nUse Z and X to zoom the minimap\nUse ESC to escape autopilot",
			pos=(0, -0.5),
			scale=0.05,
			fg=(1, 1, 1, 1),
			align=TextNode.ACenter
		)
		
		# Store UI elements for cleanup
		self.ui_elements.extend([bg, title, start_btn, instructions])
		
		# Hide the 3D camera/render
		self.render.hide()
		self.camera.hide()
	
	def start_button_click(self):
		"""
		Callback function for the "Start Game" button on the start screen.
		Transitions the game state from "start" to "garage".
		
		Params: None
		Returns: None
		"""
		if self.game_state == "start":
			self.switch_screen("garage")
	
	# =============================================
	# Garage Screen Methods
	# =============================================
	
	def show_garage_screen(self):
		"""
		Displays the 3D garage environment where players can customize their car.
		Sets up the garage environment, loads the selected car model,
		add the customization UI, and positions the camera for the garage view.
		
		Params: None
		Returns: None
		"""
		
		# Create a separate render for the garage
		self.garage_render = self.render.attachNewNode("garage_render")
		self.garage_render.show()
		
		# Setup garage environment
		self.setup_garage_environment()
		
		# Add the car model for display
		self.setup_garage_car()
		
		# Add garage UI
		self.setup_garage_ui()
		
		# Position camera for garage view
		self.camera.setPos(0, 30, 1)
		self.camera.lookAt(0, 0, 5)
		self.camera.show()
		
		# Start rotating the car
		self.taskMgr.add(self.rotate_garage_car, "rotateGarageCar")
	
	def setup_garage_environment(self):
		"""
		Setup the garage environment (walls, garage background, floor, etc.)
		
		Params: None
		Returns: None
		"""
		
		self.render.show()
		
		# Load garage floor
		floor = self.loader.loadModel("./assets/models/ground/ground.egg")
		floor.reparentTo(self.garage_render)
		floor.setScale(3)
		floor.setPos(-8, 42, -2)
		floor.setColor(0.3, 0.3, 0.3, 1)
		
		garage = self.loader.loadModel("./assets/models/garage/garage.glb")
		garage.setShaderAuto()
		garage.reparentTo(self.garage_render)
		garage.setScale(3.5)
		garage.setPos(0, 15, -1.5)
		garage.setHpr(-145, 0, 0)
		
		# Add some lighting
		ambient_light = AmbientLight("garage_ambient")
		ambient_light.setColor((0.6, 0.6, 0.6, 1))
		ambient_np = self.garage_render.attachNewNode(ambient_light)
		self.garage_render.setLight(ambient_np)
		
		directional_light = DirectionalLight("garage_directional")
		directional_light.setColor((0.8, 0.8, 0.8, 1))
		directional_np = self.garage_render.attachNewNode(directional_light)
		directional_np.setHpr(-45, -45, 0)
		self.garage_render.setLight(directional_np)
	
	def setup_garage_car(self):
		"""
		Setup the car model and appropriate lighting in the garage.
		
		Params: None
		Returns: None
		"""
		
		self.garage_car = self.loader.loadModel(self.vehicle_models[self.vehicle_model_idx]["file_path"])
		self.garage_car.setShaderAuto()
		self.garage_car.reparentTo(self.garage_render)
		self.garage_car.setScale(self.vehicle_models[self.vehicle_model_idx]["model_scale"])
		self.garage_car.setPos(0, 12, -1.3)
		self.garage_car.setColorScale(self.vehicle_color)
		
		# Improved lighting setup
		self.garage_render.clearLight()
		
		# Main key light (bright and warm)
		key_light = Spotlight("key_light")
		key_light.setColor((1, 1, 0.9, 1))
		key_light_np = self.garage_render.attachNewNode(key_light)
		key_light_np.setPos(-5, 5, 10)  # Better positioned
		key_light_np.lookAt(self.garage_car)
		
		# Fill light (soft and cool)
		fill_light = Spotlight("fill_light")
		fill_light.setColor((0.4, 0.4, 0.6, 1))
		fill_light_np = self.garage_render.attachNewNode(fill_light)
		fill_light_np.setPos(5, 5, 5)
		fill_light_np.lookAt(self.garage_car)
		
		# Ambient light (base illumination)
		ambient_light = AmbientLight("ambient_light")
		ambient_light.setColor((0.4, 0.4, 0.4, 1))
		ambient_np = self.garage_render.attachNewNode(ambient_light)
		
		# Apply all lights
		self.garage_render.setLight(key_light_np)
		self.garage_render.setLight(fill_light_np)
		self.garage_render.setLight(ambient_np)
	
	def setup_garage_ui(self):
		"""
		Setup the garage user interface, which provides the color grid customization, ability to switch car model, and the car stats (e.g. acceleration).
		
		Params: None
		Returns: None
		"""

		# Title
		title = OnscreenText(
			text="GARAGE",
			pos=(0, 0.85),
			scale=0.08,
			fg=(1, 1, 1, 1),
			align=TextNode.ACenter,
			font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
		)

		# Generate 50 colors in rainbow order
		rainbow_colors = []
		rainbow_count = 25

		for i in range(rainbow_count):
			# Creating colors in rainbow sequence (red to violet)
			hue = i / rainbow_count
			saturation = 0.9
			value = 0.9
			
			# Convert HSV to RGB
			if saturation == 0.0:
				rgb = (value, value, value)
			else:
				h_i = int(hue * 6.0)
				f = hue * 6.0 - h_i
				p = value * (1.0 - saturation)
				q = value * (1.0 - saturation * f)
				t = value * (1.0 - saturation * (1.0 - f))
				h_i = h_i % 6
				
				if h_i == 0: rgb = (value, t, p)
				elif h_i == 1: rgb = (q, value, p)
				elif h_i == 2: rgb = (p, value, t)
				elif h_i == 3: rgb = (p, q, value)
				elif h_i == 4: rgb = (t, p, value)
				else: rgb = (value, p, q)
			
			rainbow_colors.append((rgb[0], rgb[1], rgb[2], 1))

		# create color buttons in a grid
		color_buttons = []
		button_size = 0.03
		start_x = -0.85
		start_y = -0.62
		spacing = 0.07
		
		self.saturation_buttons = []
		self.color_outlines = []
		self.saturation_outlines = []
		self.selected_hue = 0  # Track selected hue for saturation updates
		
		for i, color in enumerate(rainbow_colors):
			row = i // (rainbow_count)
			col = i % (rainbow_count)
			x = start_x + col * spacing
			y = start_y - row * spacing
			
			outline = DirectFrame(
				frameSize=(-button_size*1.2, button_size*1.2, -button_size*1.2, button_size*1.1),
				pos=(x, 0, y),
				frameColor=(1, 1, 1, 0),
				state=DGG.NORMAL
			)
			self.color_outlines.append(outline)
			
			btn = DirectButton(
				frameSize=(-button_size, button_size, -button_size, button_size),
				pos=(x, 0, y),
				frameColor=color,
				command=self.change_car_color,
				extraArgs=[color, i, False, rainbow_count],  # False = rainbow button
				pressEffect=1
			)
			color_buttons.append(btn)

		# Create saturation buttons row
		saturation_row_y = start_y - 1.5 * spacing
		saturation_count = rainbow_count

		for i in range(saturation_count):
			x = start_x + i * spacing
			
			outline = DirectFrame(
				frameSize=(-button_size*1.2, button_size*1.2, -button_size*1.2, button_size*1.1),
				pos=(x, 0, saturation_row_y),
				frameColor=(1, 1, 1, 0),
				state=DGG.NORMAL
			)
			self.saturation_outlines.append(outline)
			
			btn = DirectButton(
				frameSize=(-button_size, button_size, -button_size, button_size),
				pos=(x, 0, saturation_row_y),
				frameColor=(1, 1, 1, 1),  # Initial white color
				command=self.change_car_color,
				extraArgs=[(1, 1, 1, 1), i, True, rainbow_count],  # True = saturation button
				pressEffect=1
			)
			self.saturation_buttons.append(btn)

		# Initialize saturation buttons with first color's shades
		hue = 0 / rainbow_count
		for i, btn in enumerate(self.saturation_buttons):
			pos = i / (saturation_count - 1)
			
			if pos < 0.5:
				saturation = pos * 2
				value = 1.0
			else:
				saturation = 1.0
				value = 1.0 - (pos - 0.5) * 2
			
			# Convert HSV to RGB
			h_i = int(hue * 6.0)
			f = hue * 6.0 - h_i
			p = value * (1.0 - saturation)
			q = value * (1.0 - saturation * f)
			t = value * (1.0 - saturation * (1.0 - f))
			h_i = h_i % 6
			
			if h_i == 0: rgb = (value, t, p)
			elif h_i == 1: rgb = (q, value, p)
			elif h_i == 2: rgb = (p, value, t)
			elif h_i == 3: rgb = (p, q, value)
			elif h_i == 4: rgb = (t, p, value)
			else: rgb = (value, p, q)
			
			btn['frameColor'] = (rgb[0], rgb[1], rgb[2], 1)
			btn['extraArgs'][0] = (rgb[0], rgb[1], rgb[2], 1)
		
		# Specs Box - Top Left
		specs_bg = DirectFrame(
			frameSize=(-0.55, 0.4, -0.75, -0.1),
			pos=(-0.7, 0, 0.95),
			frameColor=(0, 0, 0, 0.9),
			state=DGG.NORMAL
		)

		# Specs Title
		self.specs_title = OnscreenText(
			text=f"{self.vehicle_models[self.vehicle_model_idx]['name']} ({self.vehicle_models[self.vehicle_model_idx]['tier']} tier)",
			pos=(-1.2, 0.76),
			scale=0.06,
			fg=(1, 1, 1, 1),
			align=TextNode.ALeft,
			font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
		)

		# These will be updated when vehicle changes
		self.spec_bars = {}
		self.spec_labels = {}
		stats = [
			("mass", (1, 0.8, 0.2, 1)),  # (stat_name, (r, g, b, a))
			("acceleration", (0.2, 0.8, 1, 1)),
			("handling_coeff", (0.4, 1, 0.4, 1)),
			("fuel_consumption", (1, 0.5, 0.2, 1)),
		]

		for i, (stat, color) in enumerate(stats):
			# Bar background (gray)
			bar_bg = DirectFrame(
				frameSize=(-0.4, 0.4, -0.015, 0.015),
				pos=(-0.8, 0, 0.64 - i*0.12),
				frameColor=(0.3, 0.3, 0.3, 1)
			)

			# Colored bar (value will be updated)
			bar = DirectFrame(
				frameSize=(-0.4, 0.4, -0.015, 0.015),
				pos=(-0.8, 0, 0.64 - i*0.12),
				frameColor=color
			)
			self.spec_bars[stat] = bar
			
			# Stat label
			label = OnscreenText(
				text=stat.replace("_", " ").upper(),
				pos=(-1.2, 0.67 - i*0.12),
				scale=0.04,
				fg=(1, 1, 1, 1),
				align=TextNode.ALeft,
				font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
			)
			self.spec_labels[stat] = label
			
			self.garage_elements.extend([bar_bg, bar, label])

		# Store UI elements
		self.garage_elements.extend([
			specs_bg, self.specs_title,
			*self.spec_labels.values(),
			*self.spec_bars.values()
		])

		# Initial update
		self.update_vehicle_specs()
			
		# Translucent black buttons behind arrows
		left_nav_btn = DirectButton(
			text="<",
			scale=0.2,
			pos=(-1.15, 0, -0.1),
			frameColor=(0, 0, 0, 0.9),
			text_fg=(1, 1, 1, 1),
			text_scale=0.7,
			text_align=TextNode.ACenter,
			text_pos=(0, -0.2),
			text_font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf"),
			relief=DGG.FLAT,
			frameSize=(-0.6, 0.6, -0.6, 0.6),
			command=self.choose_vehicle_model,
			extraArgs=[-1],
			pressEffect=0,
		)

		right_nav_btn = DirectButton(
			text=">", 
			scale=0.2,
			pos=(1.15, 0, -0.1),
			frameColor=(0, 0, 0, 0.9),
			text_fg=(1, 1, 1, 1),
			text_scale=0.7,
			text_align=TextNode.ACenter,
			text_pos=(0, -0.2),
			text_font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf"),
			relief=DGG.FLAT,
			frameSize=(-0.6, 0.6, -0.6, 0.6),
			command=self.choose_vehicle_model,
			extraArgs=[1],
			pressEffect=0,
		)
		
		# Play button
		play_btn = DirectButton(
			text="Start Delivery!",
			scale=0.1,
			pos=(0.9, 0, -0.9),
			frameColor=(0.2, 0.6, 0.2, 1),
			text_fg=(1, 1, 1, 1),
			command=self.switch_screen,
			extraArgs=["game"]
		)

		# Store UI elements
		self.garage_elements.extend([title, play_btn, left_nav_btn, right_nav_btn] + color_buttons + self.color_outlines + self.saturation_buttons + self.saturation_outlines)
	
	def change_car_color(self, color, index, is_saturation_button, rainbow_count):
		"""
		Handle color change of the car display model in the garag,  and update selection outline accordingly.
		Params:
		 - color (tuple[float, float, float, float]): The RGBA color tuple (0.0-1.0 for each component)
														to apply to the car.
		 - index (int): The index of the clicked button within its respective list
						(color_outlines or saturation_outlines).
		 - is_saturation_button (bool): True if the clicked button is from the saturation row,
									   False if it's from the main rainbow color grid.
		 - rainbow_count (int): The total number of hue buttons (used for calculating hue value).
		Returns: None
		"""
		
		self.vehicle_color = Vec4(color)
		
		# Hide all outlines first
		for outline in self.color_outlines + self.saturation_outlines:
			outline['frameColor'] = (1, 1, 1, 0)
		
		# Show the appropriate outline
		if is_saturation_button:
			self.saturation_outlines[index]['frameColor'] = (1, 1, 1, 1)
		else:
			self.color_outlines[index]['frameColor'] = (1, 1, 1, 1)
			self.selected_hue = index / rainbow_count
			
			for i, btn in enumerate(self.saturation_buttons):
				pos = i / (rainbow_count - 1)
				
				if pos < 0.5:
					saturation = pos * 2
					value = 1.0
				else:
					saturation = 1.0
					value = 1.0 - (pos - 0.5) * 2
				
				# Convert HSV to RGB
				if saturation == 0.0:
					rgb = (value, value, value)
				else:
					h_i = int(self.selected_hue * 6.0)
					f = self.selected_hue * 6.0 - h_i
					p = value * (1.0 - saturation)
					q = value * (1.0 - saturation * f)
					t = value * (1.0 - saturation * (1.0 - f))
					h_i = h_i % 6
					
					if h_i == 0: rgb = (value, t, p)
					elif h_i == 1: rgb = (q, value, p)
					elif h_i == 2: rgb = (p, value, t)
					elif h_i == 3: rgb = (p, q, value)
					elif h_i == 4: rgb = (t, p, value)
					else: rgb = (value, p, q)
				
				new_color = (rgb[0], rgb[1], rgb[2], 1)
				btn['frameColor'] = new_color
				btn['extraArgs'][0] = new_color
		
		# Apply color to car model
		if hasattr(self, 'garage_car') and self.garage_car:
			self.garage_car.setColor(color)
			
	def update_vehicle_specs(self):
		"""
		Update the specs display with current vehicle stats.
		
		Params: None
		Returns: None
		"""
		
		vehicle = self.vehicle_models[self.vehicle_model_idx]
		
		stat_ranges = {
			"mass": {"min": 500.0, "max": 905.0},
			"acceleration": {"min": 3.5, "max": 8.1},
			"handling_coeff": {"min": 0.4, "max": 1.01},
			"fuel_consumption": {"min": 0.00065, "max": 0.003},
		}

		for stat, bar in self.spec_bars.items():
			value = vehicle[stat]
			stat_min = stat_ranges[stat]["min"]
			stat_max = stat_ranges[stat]["max"]
			
			# Calculate normalized value (0-1)
			if stat != "fuel_consumption":
				normalized = (value - stat_min) / (stat_max - stat_min)
			else:
				# for fuel consumption, lower is better (reverse the scale)
				normalized = (stat_max - value) / (stat_max - stat_min)
			
			normalized = max(0.0, min(1.0, normalized))
			
			# Update bar width
			bar['frameSize'] = (-0.4, -0.4 + 0.8*normalized, -0.015, 0.015)
			
			# Update label text
			if stat == 'handling_coeff':
				display_text = f"{stat.replace('_', ' ').upper()}: {value:.2f}"
			else:
				display_text = f"{stat.replace('_', ' ').upper()}: {value}"
			
			self.spec_labels[stat].setText(display_text)
		
		self.specs_title.setText(f"{self.vehicle_models[self.vehicle_model_idx]['name']} ({self.vehicle_models[self.vehicle_model_idx]['tier']} tier)")
		
		
	def choose_vehicle_model(self, direction):
		"""
		Cycles through the available vehicle models in the garage.
		Updates the displayed car model in the 3D environment and
		refreshes the vehicle specifications displayed in the UI.

		Params:
		 - direction (int): An integer indicating the direction to cycle:
							1 for next model, -1 for previous model.
		Returns: None
		"""
		
		self.vehicle_model_idx += direction
		
		if self.vehicle_model_idx >= len(self.vehicle_models):
			self.vehicle_model_idx = 0
		
		if hasattr(self, 'garage_car') and self.garage_car:
			new_car = self.loader.loadModel(self.vehicle_models[self.vehicle_model_idx]["file_path"])
			new_car.reparentTo(self.garage_render)
			new_car.clearTransform()
			new_car.setScale(self.vehicle_models[self.vehicle_model_idx]["model_scale"])
			new_car.setPos(0, 12, -1.3)
			new_car.setColorScale(self.vehicle_color)
			new_car.setShaderAuto()  # Enable proper shading
			
			self.garage_car.removeNode()
			self.garage_car = new_car
			
			self.update_vehicle_specs()
			
	
	def rotate_garage_car(self, task):
		"""
		Task to rotate the car in garage
		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		"""
		
		if self.game_state != "garage":
			return Task.done
		
		self.garage_car.setColorScale(self.vehicle_color)
		
		dt = globalClock.getDt()
		self.garage_car.setH(self.garage_car.getH() + 20 * dt)
		return Task.cont
	
	# =============================================
	# Gameplay Screen Methods
	# =============================================
	
	def start_gameplay(self):		
		"""
		Initialize and start the actual game section by setting up the environment, city scene, npcs, vehicle, roads, and camera.
		
		Params: None
		Returns: None
		"""
		
		# Setup physics world
		self.world = BulletWorld()
		self.world.setGravity(Vec3(0, 0, -9.81))
		
		# Setup game environment
		self.setup_game_environment()
		
		# Setup NPCs
		self.setup_npcs(2 * ROWS)  # Create NPCs
		
		# Setup vehicle
		self.setup_vehicle()
		
		# Setup camera
		self.cameraTarget = Point3(0, 0, 0)
		self.camera.setPos(self.cameraTarget + Vec3(0, -15, 8))
		self.camera.lookAt(self.cameraTarget + Vec3(0, 5, 5))
		
		# Setup UI
		self.create_minimap()
		self.create_dashboard()
		
		# Start delivery system
		self.start_new_delivery()
		
		# Start game tasks
		self.taskMgr.add(self.update, "update")
		self.taskMgr.add(self.update_camera, "updateCamera")
		self.taskMgr.add(self.update_minimap, "updateMinimap")
		self.taskMgr.add(self.update_dashboard, "updateDashboard")
		self.taskMgr.add(self.handle_speeding, "handleSpeeding")
		self.taskMgr.add(self.update_delivery, "updateDelivery")
		self.taskMgr.add(self.update_lighting_task, "UpdateLightingTask")
		
		# Show the 3D world
		self.render.show()
		self.camera.show()
	
	def setup_game_environment(self):
		"""
		Setup the game environment (buildings, roads, etc.)
		
		Params: None
		Returns: None
		"""
		
		# Add ground plane
		self.add_ground()
		
		# Load and position ground model
		self.scene = self.loader.loadModel("./assets/models/ground/ground.egg")
		self.scene.reparentTo(self.render)
		self.scene.setScale(3)
		self.scene.setPos(-8, 42, 0)
		
		# Setup road system
		self.road_offset_start_x = -8
		self.road_offset_start_y = -34
		self.buildings_spacing = 60
		self.closest_buildings = []
		self.add_building_grid(g_map, self.buildings_spacing)
		
		# Add lighting
		self.add_light_scene()
	
	def add_ground(self):
		"""
		Add physics ground plane.
		
		Params: None
		Returns: None
		"""
		
		shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
		ground_np = self.render.attachNewNode(BulletRigidBodyNode('Ground'))
		ground_np.node().addShape(shape)
		ground_np.setPos(0, 0, 1)
		ground_np.node().setMass(0)
		self.world.attachRigidBody(ground_np.node())
		
	
	def setup_vehicle(self):
		"""
		Setup the player's vehicle, its headlights, its collision solid, and its car marker on the minimap, for gameplay.
		
		Params: None
		Returns: None
		"""
		
		# Physics setup
		shape = BulletBoxShape(Vec3(0.7, 1.5, 0.5))
		ts = TransformState.makePos(Point3(0, 0, 0.5))
		
		self.chassisNP = self.render.attachNewNode(BulletRigidBodyNode('Vehicle'))
		self.chassisNP.node().addShape(shape, ts)
		self.chassisNP.setPos(0, -5, 1.0)
		self.chassisNP.node().setMass(self.vehicle_models[self.vehicle_model_idx]["mass"])
		self.chassisNP.node().setDeactivationEnabled(False)
		self.world.attachRigidBody(self.chassisNP.node())
		
		# Visual model
		car_model = self.loader.loadModel(self.vehicle_models[self.vehicle_model_idx]["file_path"])
		car_model.clearModelNodes()
		car_model.flattenStrong()
		car_model.setShaderAuto()
		car_model.reparentTo(self.chassisNP)
		car_model.setScale(self.vehicle_models[self.vehicle_model_idx]["model_scale"])
		car_model.setHpr(0, 0, 0)
		car_model.setZ(0.5)
		car_model.setColorScale(self.vehicle_color)
		
		# Car marker for minimap
		arrow_tx = self.loader.loadTexture("./assets/images/arrow.png")
		cm = CardMaker("car_marker")
		cm.setFrame(-0.5, 0.5, -0.5, 0.5)
		self.car_marker = self.chassisNP.attachNewNode(cm.generate())
		self.car_marker.setScale(15)
		self.car_marker.setTransparency(TransparencyAttrib.MAlpha)
		self.car_marker.setPos(0, 0, 100)
		self.car_marker.setHpr(90, -90, 0)
		self.car_marker.setLightOff()
		self.car_marker.setShaderOff()
		self.car_marker.setTexture(arrow_tx, 1)
		
		# Headlights
		self.headlightL = Spotlight("headlightL")
		self.headlightR = Spotlight("headlightR")
		
		# Configure the light beam
		for headlight in [self.headlightL, self.headlightR]:
			headlight.setColor((1.0, 1.0, 0.9, 1))
			lens = PerspectiveLens()
			lens.setFov(90)
			lens.setNearFar(0.1, 50)
			headlight.setLens(lens)
		
		# Attach to the car
		self.headlightLNP = self.chassisNP.attachNewNode(self.headlightL)
		self.headlightRNP = self.chassisNP.attachNewNode(self.headlightR)
		
		# Position headlights at front of car
		self.headlightLNP.setPos(0.25, 1.2, 0.6)
		self.headlightRNP.setPos(-0.25, 1.2, 0.6)
		self.headlightLNP.setHpr(0, -5, 0)
		self.headlightRNP.setHpr(0, -5, 0)
		
		# Add to render so the lights affect scene
		self.render.setLight(self.headlightLNP)
		self.render.setLight(self.headlightRNP)
		
	def setup_npcs(self, count):
		"""
		Create rows of walking NPCs with collision physics.
		
		Params:
		 - count (int): The number of NPCs to attempt to create.
		Returns: None
		"""
		
		# Clear existing NPCs
		for npc in self.npcs:
			npc['node'].removeNode()
		self.npcs = []
		
		for i in range(ROWS - 1):
			for j in range(COLUMNS - 1):
				x = self.road_offset_start_x + j * self.buildings_spacing
				y = self.road_offset_start_y + i * self.buildings_spacing
				
				if count >= 0:
					# Use built-in panda actor with walk animation
					actor = Actor("panda", {"walk": "panda-walk"})   # Using built-in panda models because couldn't find an .egg model with a human
					actor.setScale(0.25)
					actor.reparentTo(self.render)
					actor.loop("walk")  # Loop walking animation

					# Position and rotate them
					actor.setPos(x, y, 0.5)
					actor.setH(180)

					# Physics body
					shape = BulletCapsuleShape(0.3, 1, 1)
					np_node = BulletRigidBodyNode(f'NPC_{i}')
					np_node.addShape(shape)
					np_node.setMass(1.0)
					np_node.setDeactivationEnabled(False)

					np_np = self.render.attachNewNode(np_node)
					np_np.setPos(actor.getPos())
					self.world.attachRigidBody(np_node)

					# Store NPC data
					self.npcs.append({
						'actor': actor,
						'node': np_np,
						'speed': random.uniform(6.5, 10.5),
						'direction': random.choice([0, 90, 180, 270]),
						'change_dir_timer': random.uniform(20, 30)
					})
					
					count -= 1
				else:
					break

		for i in range(count):
			pass
	
	
	def add_building_grid(self, grid, spacing):
		"""
		Add buildings to the game world based on grid
		Params:
		 - grid (ManhattanGrid): Two 2D list representing the game map grid; One list represents
							       the buildings, and the other represents the road intersections in between the buildings.
								   Alphabet letters represent delivery houses,
								   '+' for gas stations, and 'H' for regular buildings.
		 - spacing (float): The distance in 3D world units between the center
							of adjacent grid cells.
		Returns: None
		"""
		
		buildings = [
			("building_clusters/1.egg", 0.4, 90), 
			("building_clusters/2.egg", 0.4, 0), 
			("building_clusters/3.egg", 0.4, 0), 
			("building_clusters/4.egg", 0.4, 0)
		]
		delivery_house = ("townhouse1/townhouse1.glb", 25, 0)
		gas_station = ("rest_station/rest_station.egg", 0.04, 180)
		start_x = -37
		start_y = -37

		for i in range(ROWS):
			for j in range(COLUMNS):
				if grid[i, j].isalpha():
					chosen = delivery_house
				elif grid[i, j] == "+":
					chosen = gas_station
				else:
					chosen = random.choice(buildings)

				model_path = "assets/models/" + chosen[0]
				scale = chosen[1]
				h = chosen[2]

				dummy = NodePath("dummy")
				building_model = self.loader.loadModel(model_path)
				building_model.reparentTo(dummy)
				building_model.setScale(scale)
				building_model.setH(h)
				building_model.setShaderAuto()

				# Tight bounds
				dummy.flattenStrong()  # Apply transforms
				min_bound, max_bound = dummy.getTightBounds()
				size = (max_bound - min_bound) * 0.5  # half extents
				center = (min_bound + max_bound) * 0.5
				# Bullet collision
				shape = BulletBoxShape(size)
				
				x = start_x + j * spacing
				y = start_y + i * spacing

				building_node = BulletRigidBodyNode(f"Building_{i}_{j}")
				building_node.setMass(0)
				building_node.addShape(shape, TransformState.makePos(center))

				building_np = self.render.attachNewNode(building_node)
				building_np.setPos(x, y, 0)
				building_np.setH(h)
				
				# Set a gas icon marker for the gas stations in the minimap
				if grid[i, j] == "+":
					gas_tx = loader.loadTexture("./assets/images/gas_icon.png")
					cm = CardMaker("gas_marker")
					cm.setFrame(-0.5, 0.5, -0.5, 0.5)
					self.gas_marker = building_np.attachNewNode(cm.generate())
					self.gas_marker.setScale(20)
					self.gas_marker.setTransparency(TransparencyAttrib.MAlpha)
					self.gas_marker.setPos(0, 0, 100) # Position it such that above the station building
					self.gas_marker.setHpr(180, -90, 0)
					self.gas_marker.setLightOff()
					self.gas_marker.setShaderOff()
					self.gas_marker.setTexture(gas_tx, 1)
				
				self.world.attachRigidBody(building_node)
				building_model.reparentTo(building_np)
				self.game_elements.append(building_np)
				
		self.add_roads(grid, spacing)
	
	def add_roads(self, grid, spacing):
		"""
		Add roads to the game world
		Params:
		 - grid (ManhattanGrid): Two 2D list representing the game map grid; One list represents the buildings,
								 and the other represents the road intersections in between the buildings.
								 Alphabet letters represent delivery houses, '+' for gas stations, and 'H' for regular buildings.
		 - spacing (float): The distance in 3D world units between grid cells.
		Returns: None
		"""
		
		# Load and prepare intersection model
		intersection_model = self.loader.loadModel("./assets/models/roads_pack/intersection.glb")
		intersection_model.clearModelNodes()
		intersection_model.flattenStrong()
		intersection_model.setShaderAuto()

		# Load and prepare streetlight model
		streetlight_model = self.loader.loadModel("./assets/models/streetlight/streetlight.glb")
		streetlight_model.clearModelNodes()
		streetlight_model.flattenStrong()
		streetlight_model.setShaderAuto()

		# For batching roads
		road_rbc = RigidBodyCombiner("road_combiner")
		road_rbc_np = NodePath(road_rbc)
		road_parent = NodePath("combined_roads")
		road_parent.reparentTo(road_rbc_np)
		road_rbc_np.setTag("minimap_road", "1")

		# For batching streetlights
		light_rbc = RigidBodyCombiner("light_combiner")
		light_rbc_np = NodePath(light_rbc)
		light_parent = NodePath("combined_lights")
		light_parent.reparentTo(light_rbc_np)
		
		for i in range(ROWS - 1):
			for j in range(COLUMNS - 1):
				x = self.road_offset_start_x + j * spacing
				y = self.road_offset_start_y + i * spacing

				intersection = intersection_model.copyTo(road_parent)
				intersection.setPos(x, y, 0)
				intersection.setScale(1.1)
				
				if i % 2 == 0 and j % 2 == 0:
					# Add streetlight beside the road
					streetlight = streetlight_model.copyTo(light_parent)
					streetlight.setPos(x + 12, y + 5, 0)  # Offset to side
					streetlight.setHpr(-90, 0, 0)
					streetlight.setScale(1.5)

					spotlight = Spotlight(f"streetlight-{i}-{j}")
					spotlight.setColor((1.0, 1.0, 0.9, 1))  # Warm light tone

					lens = PerspectiveLens()
					lens.setFov(110)   # Widness angle
					lens.setNearFar(0.1, 50)
					spotlight.setLens(lens)

					spotlight_np = streetlight.attachNewNode(spotlight)
					spotlight_np.setPos(0, 0, 4.5)	  # Position light at top of lamp post
					spotlight_np.setHpr(0, -90, 0)	  # Aim it straight downward

					self.render.setLight(spotlight_np)
					
		# Attach batched nodes
		road_rbc_np.reparentTo(self.render)
		road_rbc.collect()
		light_rbc_np.reparentTo(self.render)
		light_rbc.collect()
		
		self.game_elements.extend([road_rbc, light_rbc])
	
	def add_light_scene(self):
		"""
		Sets up the primary lighting for the game world.
		This includes configuring a directional light to simulate sunlight,
		an ambient light for overall scene illumination, and setting the
		initial background color (sky).
		
		Params: None
		Returns: None
		"""
		
		# Start with daylight background
		self.setBackgroundColor(0.53, 0.81, 0.92, 1)  # Light blue sky (day)

		# Directional sunlight
		self.sun_light = DirectionalLight("sun_light")
		self.sun_np = self.render.attachNewNode(self.sun_light)
		self.sun_np.setHpr(-45, -45, 0)  # Overhead at start
		self.render.setLight(self.sun_np)

		# Ambient light
		self.ambient_light = AmbientLight("ambient_light")
		self.ambient_np = self.render.attachNewNode(self.ambient_light)
		self.render.setLight(self.ambient_np)
	
	def create_minimap(self):
		"""
		Create the minimap display. The minimap uses a separate camera with an
		orthographic lens to render a top-down view of a specific subset of the 3D scene (masked elements).
		
		Params: None
		Returns: None
		"""
		
		self.minimap_root = NodePath("minimap_root")
		self.minimap_root.setPos(0, 0, 200)
		self.minimap_root.setHpr(0, -90, 0)
		
		self.minimap_zoom_coeff = 1
		
		lens = OrthographicLens()
		lens.setFilmSize(150 * self.minimap_zoom_coeff, 150 * self.minimap_zoom_coeff)
		lens.setNearFar(10, 1000)
		minimap_cam = Camera("minimap_cam", lens)
		self.minimap_np = self.minimap_root.attachNewNode(minimap_cam)
		self.minimap_np.node().setScene(self.render)
		self.minimap_np.node().setCameraMask(MINIMAP_MASK)

		dr = self.win.makeDisplayRegion(0.75, 0.98, 0.75, 0.98)
		dr.setCamera(self.minimap_np)
		dr.setClearColorActive(True)
		dr.setClearColor((0.2, 0.2, 0.2, 1))
		
		self.game_elements.extend([self.minimap_np])
	
	def create_dashboard(self):
		"""
		Create the dashboard UI
		This includes the road information, delivery mission details (target, timer, rewards),
		delivery success/failure counts, speedometer, fuel gauge, money display,
		autopilot button, and speeding warning pop-ups.
		
		Params: None
		Returns: None
		"""
		
		### Road Dash Section ###
		cm = CardMaker("info_bg")
		cm.setFrame(-1.3, -0.9, -0.95, 0.95)  # (left, right, bottom, top) in aspect2d coords
		bold_font = loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
		self.ui_bg = aspect2d.attachNewNode(cm.generate())
		self.ui_bg.setColor(0.1, 0.1, 0.1, 1)
		
		# Add dark grey text on top
		self.ui_text = OnscreenText(
			text="",
			pos=(-1.1, 0.65),			# (x, y) in aspect2d coords
			fg=(0.8, 0.8, 0.8, 1),
			scale=0.055,
			align=TextNode.ACenter,
			mayChange=True
		)
		
		### Delivery Section ###
		# Shows the user's current delivery mission (address and reward)
		self.delivery_text = OnscreenText(
			text="",
			pos=(-1.1, 0.40),			# (x, y) in aspect2d coords
			fg=(0.8, 0.8, 0.8, 1),
			scale=0.045,
			align=TextNode.ACenter,
			mayChange=True
		)
		
		# Shows countdown for current delivery
		self.delivery_timer = OnscreenText(
			text="",
			pos=(-1.1, 0.12),
			fg=(0.8, 0.8, 0.8, 1),
			scale=0.055,
			align=TextNode.ACenter,
			font=bold_font,
			mayChange=True
		)
		
		# Shows the user's no. of successful deliveries
		self.del_wins_text = OnscreenText(
			text="",
			pos=(-1.15, 0.0),
			fg=(0.2, 0.7, 0.4, 1),
			scale=0.05,
			align=TextNode.ARight,
			font=bold_font,
			mayChange=True
		)
		
		# Shows the user's no. of failed deliveries
		self.del_losses_text = OnscreenText(
			text="",
			pos=(-1.08, 0.0),
			fg=(0.7, 0.2, 0.2, 1),
			scale=0.05,
			align=TextNode.ALeft,
			font=bold_font,
			mayChange=True
		)
		
		### Speedometer Section ###
		# Dial background and pivot node for needle rotation
		self.speedometer_dial = OnscreenImage(image="./assets/images/speedometer/dial.jpg", pos=(-1.1, 0.35, -0.7), scale=0.2)
		self.needle_pivot = NodePath("needle_pivot")
		self.needle_pivot.reparentTo(aspect2d)  # Parent to aspect2d for 2D GUI
		self.needle_pivot.setPos(-1.1, 0.35, -0.7)  # Same position as dial
		
		# Load needle image as child of pivot
		self.speedometer_needle = OnscreenImage(image="./assets/images/speedometer/needle.png", pos=(0, 0, 0), scale=0.2)
		self.speedometer_needle.setTransparency(True)
		self.speedometer_needle.reparentTo(self.needle_pivot)
		self.speedometer_needle.setPos(0, 0, -0.1)
		
		### Fuel System Section ###
		# Dial background and pivot node for needle rotation
		self.fuelguage_dial = OnscreenImage(image="./assets/images/fuel_gauge/dial.png", pos=(-1.1, 0.35, -0.3), scale=0.2)
		self.fgneedle_pivot = NodePath("needle_pivot")
		self.fgneedle_pivot.reparentTo(aspect2d)  # Parent to aspect2d for 2D GUI
		self.fgneedle_pivot.setPos(-1.1, 0.35, -0.37)  # Same position as dial
		
		# Load needle image as child of pivot
		self.fuelguage_needle = OnscreenImage(image="./assets/images/fuel_gauge/needle.png", pos=(0, 0, 0), scale=0.16)
		self.fuelguage_needle.setTransparency(True)
		self.fuelguage_needle.reparentTo(self.fgneedle_pivot)
		self.fuelguage_needle.setPos(0, 0, -0.1)
		
		### Money Section ###
		self.money_bar = OnscreenImage(image="./assets/images/money_bar.png", pos=(-1.1, 0.35, 0.85), scale=(0.2, 0.1, 0.07))
		self.money_text = OnscreenText(
			text=f"${self.money:.2f}",
			pos=(-1.2, 0.83),
			fg=(0.3, 0.1, 0.0, 1),
			scale=0.055,
			align=TextNode.ALeft,
			font=bold_font,
			mayChange=True
		)
		
		
		### Autopilot Control Section ###
		self.autopilot_button = DirectButton(
			text="Use Autopilot ($40)",
			scale=0.05,
			pos=(1.0, 0, -0.9),
			frameColor=(1, 0, 0, 1),
			text_fg=(1, 1, 1, 1),
			command=self.activate_autopilot_assist
		)
		
		### Overspeeding Section ###
		# Create the red rectangle using CardMaker
		cm = CardMaker('speeding_warning')
		cm.setFrame(-0.7, 0.7, -0.2, 0.2)  # left, right, bottom, top
		self.speeding_box = aspect2d.attachNewNode(cm.generate())
		self.speeding_box.setColor(1, 0, 0, 0.5)  # Red with 50% transparency
		self.speeding_box.setTransparency(True)
		self.speeding_box.hide()

		# Create the warning text
		self.speeding_text = OnscreenText(
			text="OVERSPEEDING!\n$5 Fine Issued\nBe careful driver!",
			pos=(0, 0.04),  # Center
			scale=0.07,
			fg=(1, 1, 1, 1),
			align=TextNode.ACenter,
			mayChange=True
		)
		self.speeding_text.hide()
		
		self.game_elements.extend([self.speeding_box, self.speeding_text, self.autopilot_button, self.money_text, self.money_bar, self.fuelguage_needle, self.fuelguage_dial, self.ui_bg, self.ui_text, self.delivery_text, self.delivery_timer, self.del_wins_text, self.del_losses_text])
	
	def start_new_delivery(self):
		"""
		Start a new delivery mission.

		Selects a random delivery target location from the available grid cells,
		calculates the time allotted for the delivery based on distance,
		and determines the reward for successful completion.
		It also increments the total delivery count.
		
		Params: None
		Returns: None
		"""

		delivery_points = [(i, j) for i in range(ROWS-1) for j in range(COLUMNS-1) if g_map[i, j].isalpha()]
		self.delivery_target = random.choice(delivery_points)
		
		car_pos = self.chassisNP.getPos()
		col = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
		row = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)
		dist_factor = sqrt((self.delivery_target[0] - row)**2 + (self.delivery_target[1] - col)**2)
		max_dist_factor = sqrt(ROWS**2 + COLUMNS**2) 
		
		self.delivery_time_given = 45 + 75 * dist_factor/max_dist_factor # seconds
		self.delivery_time_left = self.delivery_time_given
		self.delivery_reward = random.choice([20, 30, 40])
		self.total_delivery_count += 1
	
	def complete_delivery(self):
		"""
		Complete the current delivery if at target location.

		Checks if the player's vehicle is at or near the delivery target location.
		If successful, money and successful delivery count are updated,
		and a new delivery is started. If at the wrong location, a warning is shown.
		Checks for game win condition (5 successful deliveries).
		
		Params: None
		Returns: None
		"""
		
		row, col = self.delivery_target
		car_pos = self.chassisNP.getPos()
		c = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
		r = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)

		if (r, c) == (row, col) or (r, c) == (row - 1, col) or (r, c) == (row, col - 1) or (r, c) == (row + 1, col) or (r, c) == (row, col + 1):
			if self.successful_delivery_count >= 4:
				loss_reason = None
				self.switch_screen("win")
				return
			self.money += self.delivery_reward
			self.successful_delivery_count += 1
			rating_score = self.delivery_time_left / (0.4*self.delivery_time_given) * 5
			if rating_score > 5: rating_score = 5
			self.delivery_scores.append(rating_score)
			
			# Show delivery success alert
			self._show_warning_timer = 4.0
			self.speeding_box.setColor(0, 1, 0, 0.5)
			self.speeding_box.show()
			self.speeding_text.setText(f"DELIVERY SUCCESS!\n${self.delivery_reward} earned\nCustomer rated you {rating_score:.1f} STARS")
			self.speeding_text.show()
			self._is_flashing_on = False
			
			self.start_new_delivery()
		else:
			# Alert that wrong location
			self._show_warning_timer = 3.0
			self.speeding_box.setColor(1, 0, 0, 0.5)
			self.speeding_box.show()
			self.speeding_text.setText("WRONG LOCATION!\nTry Again!\nCustomer's waiting...")
			self.speeding_text.show()
			self._is_flashing_on = True
	
	def refuel(self, grid):
		"""
		Refuel the vehicle at gas stations.

		Calculates the fuel cost based on the amount needed and deducts it from money.
		If the player doesn't have enough money, fuels based on remaining money.
		Displays a success or insufficient funds message.

		Params:
		 - grid (ManhattanGrid): The 2D grid map, used to identify gas station locations.
		Returns: None
		"""
		
		car_pos = self.chassisNP.getPos()
		col = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
		row = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)
		
		if '+' in (grid[row-1, col-1], grid[row-1, col], grid[row-1, col+1], grid[row, col-1], grid[row, col], grid[row, col+1]):
			fuel_price = 20 * (100.0 - self.fuel_level) / 100
			if self.money < fuel_price:   # if player lacks enough money, then refueling amount is based on remaining money.
				# Show refueling failure alert
				increaseable_fuel =  100.0 - 100 * fuel_price / 20
				fuel_price = self.money
				self.money = 0
				self.fuel_level += increaseable_fuel
			else:
				self.money -= fuel_price
				self.fuel_level = 100.0
				
			# Show refueling success alert
			self._show_warning_timer = 3.0
			self.speeding_box.setColor(0, 1, 0, 0.5)
			self.speeding_box.show()
			self.speeding_text.setText(f"SUCCESSFULLY REFUELED!\n${fuel_price:.2f} spent.\nCarry on!")
			self.speeding_text.show()
			self._is_flashing_on = False
			
	# Autopilot Assist Method
	def activate_autopilot_assist(self):
		"""
		Activates the autopilot assistance feature.

		If the autopilot has not been used yet and the player has enough money ($40),
		it deducts the cost, sets the autopilot status, updates the UI button,
		finds the shortest time path to the delivery target using Dijkstra's algorithm,
		and starts the autopilot driving task.
		
		Params: None
		Returns: None
		"""
		
		# Unable for user to use autopilot feature if they dont have at least $40 (price).
		if self.autopilot_used or self.money < 40:
			return

		self.money -= 40
		self.autopilot_used = True
		
		# Disable the autopilot option when clicked (one-time use)
		if self.autopilot_button:
			self.autopilot_button['frameColor'] = (0.5, 0.5, 0.5, 1)
			self.autopilot_button['text'] = "Autopilot Used"
			self.autopilot_button['state'] = DGG.DISABLED
		
		
		def find_shortest_time_path(car_pos, goal):
			"""
			Finds the shortest time path from the car's current grid position to a goal grid position
			using Dijkstra's algorithm.

			Params:
			 - car_pos (Point3): The current 3D position of the car.
			 - goal (tuple[int, int]): The (row, column) coordinates of the target destination.

			Returns:
			 - list[tuple[int, int]]: A list of (row, column) tuples representing the path
										from start to goal, or an empty list if no path is found.
			"""
			col = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
			row = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)
			start = (row, col)

			visited = set()  # To track visited positions thus far
			pq = PriorityQueue()
			pq.put((0, start, []))

			while not pq.empty():
				time_cost, current, path = pq.get()
				if current in visited:
					continue
				visited.add(current)
				
				if current == goal:
					return path + [current]

				r, c = current
				for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
					nr, nc = r + dr, c + dc
					if 0 <= nr < ROWS - 1 and 0 <= nc < COLUMNS - 1:
						ch = g_map.roadisx_get(nr, nc)
						if ch and ch in ROAD_TYPES:
							speed = ROAD_TYPES[ch]
							time = 1 / speed  # inverse of speed
							pq.put((time_cost + time, (nr, nc), path + [current]))
			return []

		# Pathfinding
		path = find_shortest_time_path(self.chassisNP.getPos(), self.delivery_target)
		
		if path:
			self.auto_drive_path = path
			self.taskMgr.add(self.autopilot_drive_task, "autopilotDriveTask")
			
	
	# =============================================
	# Gameplay Task Methods
	# =============================================
	
	def update(self, task):
		"""
		Main game update task, called every frame during gameplay.

		This method handles the physics simulation, vehicle movement based on player input,
		NPC movement and direction changes, and checks for car-NPC collisions to apply fines.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		 
		"""
		if self.game_state != 'game':
			return Task.cont
		
		dt = globalClock.getDt()
		self.world.doPhysics(dt, 10, 1.0 / 180.0)
		
				
		# Handle car movement
		force = self.vehicle_models[self.vehicle_model_idx]["mass"] * self.vehicle_models[self.vehicle_model_idx]["acceleration"]
		max_turn = 30 + 25 * self.vehicle_models[self.vehicle_model_idx]["handling_coeff"]
		velocity = self.chassisNP.node().getLinearVelocity()
		speed = velocity.length()
		forward = self.chassisNP.getQuat().getForward()

		if self.key_map["forward"]:
			self.chassisNP.node().applyCentralForce(forward * force)
		elif self.key_map["backward"]:
			self.chassisNP.node().applyCentralForce(-forward * force)
		elif self.key_map["brake"]:
			brake_strength = 0.1 * self.vehicle_models[self.vehicle_model_idx]["handling_coeff"]
			self.chassisNP.node().setLinearVelocity(velocity * (1 - brake_strength))

		if speed > 1.0:
			turn = max_turn * dt
			if self.key_map["left"]:
				self.chassisNP.setH(self.chassisNP.getH() + turn)
			elif self.key_map["right"]:
				self.chassisNP.setH(self.chassisNP.getH() - turn)
				
				
		# Update NPCs
		for npc in self.npcs:
			# Change direction occasionally
			npc['change_dir_timer'] -= dt
			if npc['change_dir_timer'] <= 0:
				npc['direction'] = random.uniform(0, 360)
				npc['change_dir_timer'] = random.uniform(2, 5)
			
			# Move NPC
			rad = radians(npc['direction'])
			move_vec = Vec3(sin(rad), cos(rad), 0) * npc['speed']
			npc['node'].node().setLinearVelocity(move_vec)
			
			# Update actor position and rotation to match physics
			npc['actor'].setPos(npc['node'].getPos())
			npc['actor'].setH(npc['direction'] + 180)  # Face direction of movement
			
			# Simple animation
			if hasattr(npc['actor'], 'loop'):
				npc['actor'].loop('walk')
				
		# Check for car-NPC collisions
		current_time = globalClock.getFrameTime()
		if current_time - self.last_fine_time > 3.0:  # Limit to 1 fine per 3 seconds.
			car_node = self.chassisNP.node()
			for npc in self.npcs:
				result = self.world.contactTestPair(car_node, npc['node'].node())
				if result.getNumContacts() > 0:
					self.money -= 20  # Fine for hitting pedestrian
					self.last_fine_time = current_time
					
					# Show hit warning
					self._show_warning_timer = 2.0
					self.speeding_box.setColor(1, 0, 0, 0.5)
					self.speeding_box.show()
					self.speeding_text.setText("PEDESTRIAN HIT!\n$20 Fine Issued\nGeez.. who gave you a license!")
					self.speeding_text.show()
					self._is_flashing_on = True
					break
		
		return Task.cont
	
	
	def update_camera(self, task):
		"""
		Update camera position and orientation

		The camera follows the car with a smooth lerp, and its heading can be
		adjusted by mouse drag or automatic rotation. It also handles zooming in/out.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task.
		"""
		dt = globalClock.getDt()

		if self.mouseWatcherNode.hasMouse() and self.is_dragging and self.last_mouse_pos is not None:
			current_mouse = self.mouseWatcherNode.getMouse()
			current_pos = Vec2(current_mouse.getX(), current_mouse.getY())
			delta = current_pos - self.last_mouse_pos
			pan_speed = self.zoom_distance * 0.5
			self.cameraTarget.setY(self.cameraTarget.getY() - delta.getY() * pan_speed)
			self.last_mouse_pos = current_pos

		pos_lerp = 0.1
		rot_lerp = 0.04

		car_pos = self.chassisNP.getPos()
		car_h = self.chassisNP.getH()

		self.cameraTarget.setX(self.cameraTarget.getX() + (car_pos.getX() - self.cameraTarget.getX()) * pos_lerp)
		self.cameraTarget.setY(self.cameraTarget.getY() + (car_pos.getY() - self.cameraTarget.getY()) * pos_lerp)

		diff = (car_h - self.camera_heading + 180) % 360 - 180
		self.camera_heading += diff * rot_lerp
		self.camera_heading %= 360

		if self.is_rotating:
			self.camera_heading += 30 * dt
			self.camera_heading %= 360

		angle_rad = radians(self.camera_heading)
		offset_x = sin(angle_rad) * self.zoom_distance
		offset_y = -cos(angle_rad) * self.zoom_distance
		offset_z = self.zoom_distance * 0.25

		cam_pos = self.cameraTarget + Vec3(offset_x, offset_y, offset_z)
		self.camera.setPos(cam_pos)
		self.camera.lookAt(self.cameraTarget + Vec3(0, 5, 4))

		return Task.cont
	
	def update_minimap(self, task):
		"""
		Update minimap position and zoom

		The minimap camera is positioned directly above the player's car,
		and its film size (zoom) is adjusted based on the zoom coefficient.
		The position update is performed every few frames for performance.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task.
		"""
		car_pos = self.chassisNP.getPos()
		self.minimap_root.setPos(car_pos.getX(), car_pos.getY(), 200)
		self.minimap_np.node().getLens().setFilmSize(150*self.minimap_zoom_coeff, 150*self.minimap_zoom_coeff)
		
		self.minimap_frame_count = getattr(self, "minimap_frame_count", 0)
		self.minimap_frame_count += 1

		if self.minimap_frame_count % 3 == 0:  # every 3 frames
			car_pos = self.chassisNP.getPos()
			self.minimap_root.setPos(car_pos.getX(), car_pos.getY(), 200)
			
		return Task.cont
	
	def update_dashboard(self, task):
		"""
		Update dashboard information

		This includes displaying current road information (street name, speed limit),
		delivery mission details (target, time left, reward), delivery statistics,
		current speed on the speedometer, fuel level on the gauge, and money.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		"""
		if self.game_state != "game":
			return Task.cont
		
		car_pos = self.chassisNP.getPos()
		col = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
		row = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)
		
		def ordinal(n):
			"""
			Convert number to ordinal (1st, 2nd, etc.)
			Params:
			 - n (int): The integer to convert.
			Returns:
			 - str: The ordinal string (e.g., "1st", "2nd").
			"""
			if 11 <= (n % 100) <= 13:
				suffix = 'th'
			else:
				suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
			return str(n) + suffix
		
		street_info = "1755 Merivale Rd\n\nINF SPEED"
		
		if 0 <= row < ROWS - 1 and 0 <= col < COLUMNS - 1: 
			street_num = g_map.get_street_idx((row, col)) + 1
			street_speedlim = ROAD_TYPES[g_map.roadisx_get(row, col)]
			self.ui_text.setText(f"{ordinal(street_num)} Avenue\n\nSpeed Limit:\n{street_speedlim} kmph")
			
		if self.delivery_target:
			r, c = self.delivery_target
			
			if 0 <= r < ROWS - 1 and 0 <= c < COLUMNS - 1: 
				code = g_map[row, col]
				street_name = f"{r+c+r*c+1}{code} {ordinal(g_map.get_street_idx((r, c)) + 1)} Avenue"
			else:
				street_name = f"{r+c+r*c+1}E Merivale Rd."
			
			self.delivery_text.setText(
				f"\n\nMission Delivery:\n"
				f"{street_name}\n"
				f"Reward: ${self.delivery_reward}\n"
			)
			self.delivery_timer.setText(f"Time Left: {int(self.delivery_time_left)} s")
		
		self.del_wins_text.setText(f"{self.successful_delivery_count} DEL")
		self.del_losses_text.setText(f"{self.total_delivery_count - 1 - self.successful_delivery_count} FAIL")
		
		# Speedometer:
		velocity = self.chassisNP.node().getLinearVelocity()
		speed = velocity.length()
		angle = speed * 3 + 15
		self.needle_pivot.setR(angle)	# Rotate pivot (needle rotates around pivot)
		
		# Fuel consumption
		base_consumption = 2 * self.vehicle_models[self.vehicle_model_idx]["fuel_consumption"]
		fuel_used = speed * self.vehicle_models[self.vehicle_model_idx]["fuel_consumption"] + base_consumption
		self.fuel_level = max(0, self.fuel_level - fuel_used)

		# If out of fuel, stop car by preventing movement
		if self.fuel_level <= 0:
			self.key_map["forward"] = False
			self.key_map["backward"] = False
			
		# Fuel Guage:
		min_angle, max_angle = (90, 270)
		angle = max_angle - (1 - self.fuel_level/100) * (max_angle-min_angle)
		self.fgneedle_pivot.setR(angle)	# Rotate pivot (needle rotates around pivot)
		
		# Money display
		self.money_text.setText(f"${self.money:.2f}")
		
		return Task.cont
	
	def handle_speeding(self, task):
		"""
		Handle speeding fines and warnings

		Checks the car's current speed against the road's speed limit.
		If speeding continuously for 3 seconds, a fine is applied, and a
		flashing warning box is displayed on screen.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		"""
		
		if self.game_state != "game":
			return Task.cont
		
		car_velocity = self.chassisNP.node().getLinearVelocity()
		car_speed = car_velocity.length()

		car_pos = self.chassisNP.getPos()
		col = round((car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing)
		row = round((car_pos.getY() - self.road_offset_start_y) / self.buildings_spacing)

		dt = globalClock.getDt()

		if not hasattr(self, 'speeding_timer'):
			self.speeding_timer = 0.0

		if 0 <= row < ROWS - 1 and 0 <= col < COLUMNS - 1:
			street_speedlim = ROAD_TYPES[g_map.roadisx_get(row, col)]

			if car_speed > street_speedlim:
				self.speeding_timer += dt

				if self.speeding_timer >= 3.0:
					self.money -= 5
					self.speeding_timer = 0.0

					# Trigger warning box and timer
					self._show_warning_timer = 3.0  # Show for 3 seconds
					self.speeding_text.setText("OVERSPEEDING!\n$5 Fine Issued")
					self.speeding_box.setColor(1, 0, 0, 0.5)
					self.speeding_box.show()
					self.speeding_text.show()
					self._is_flashing_on = True
			else:
				self.speeding_timer = 0.0

		# Flash the warning box and text
		if self._show_warning_timer > 0:
			self._show_warning_timer -= dt

			# Toggle flash on/off every 0.5 seconds
			if int(self._show_warning_timer * 2) % 2 == 0:
				if not self._is_flashing_on:
					self.speeding_box.show()
					self.speeding_text.show()
					self._is_flashing_on = True
			else:
				if self._is_flashing_on:
					self.speeding_box.hide()
					self.speeding_text.hide()
					self._is_flashing_on = False
		else:
			self.speeding_box.hide()
			self.speeding_text.hide()

		return Task.cont
	
	def update_delivery(self, task):
		"""
		Update delivery timer and check for failure

		If the timer runs out, the delivery is considered failed and a new one starts.
		Also checks overall game loss conditions (out of fuel, too many failures, bankrupt).

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		"""
		if self.game_state != "game":
			return Task.cont
		
		dt = globalClock.getDt()
		self.delivery_time_left -= dt
		
		# player loses if they deplete fuel, accumulate 4 failures, or go bankrupt (lose all of their money and more)
		if self.fuel_level <= 0 or self.total_delivery_count - self.successful_delivery_count >= 4 or self.money < 0:
			self.switch_screen("loss")
			self.loss_reason = "Ran out of fuel!"
			return Task.done
		if self.total_delivery_count - self.successful_delivery_count >= 4:
			self.switch_screen("loss")
			self.loss_reason = "Too many delivery failures!"
			return Task.done
		if self.money < 0:
			self.switch_screen("loss")
			self.loss_reason = "You went bankrupt!"
			return Task.done
			
		
		if self.delivery_time_left <= 0:
			self.delivery_scores.append(0)
			self.start_new_delivery()			
			# Show delivery failure alert
			self._show_warning_timer = 3.0
			self.speeding_box.setColor(1, 0, 0, 0.5)
			self.speeding_box.show()
			self.speeding_text.setText("DELIVERY FAILED!\n$0 earned\n0 STARS RATING")
			self.speeding_text.show()
			self._is_flashing_on = False

		return Task.cont
	
	def update_lighting_task(self, task):
		"""
		Update day-night cycle lighting

		Gradually changes the color and intensity of directional and ambient lights,
		as well as the background (sky) color, based on the `time_of_day` variable.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task.
		"""
		
		def lerp_vec4(a, b, t):
			"""
			Linearly interpolates between two Vec4 colors.

			Params:
			 - a (Vec4): The starting color vector.
			 - b (Vec4): The ending color vector.
			 - t (float): The interpolation factor (0.0 to 1.0).

			Returns:
			 - Vec4: The interpolated color vector.
			"""
			return a * (1 - t) + b * t
		
		self.time_of_day += globalClock.getDt() * 0.005 * self.time_direction
		if self.time_of_day >= 1.0:
			self.time_of_day = 1.0
			self.time_direction = -1
		elif self.time_of_day <= 0.0:
			self.time_of_day = 0.0
			self.time_direction = 1

		t = self.time_of_day

		# Key colors for sun, ambient, sky at important times
		night_sun = Vec4(0.0, 0.05, 0.05, 1)
		night_ambient = Vec4(0.1, 0.05, 0.05, 1)
		night_sky = Vec4(0.05, 0.05, 0.1, 1)

		sunrise_sun = Vec4(1.0, 0.5, 0.2, 1)
		sunrise_ambient = Vec4(0.3, 0.2, 0.2, 1)
		sunrise_sky = Vec4(0.53, 0.81, 0.92, 1)

		day_sun = Vec4(1.2, 1.2, 1.0, 1)
		day_ambient = Vec4(0.3, 0.3, 0.3, 1)
		day_sky = Vec4(0.53, 0.81, 0.92, 1)

		sunset_sun = Vec4(1.0, 0.5, 0.2, 1)
		sunset_ambient = Vec4(0.3, 0.2, 0.2, 1)
		sunset_sky = Vec4(1.0, 0.5, 0.2, 1)

		if t < 0.25:
			# night -> sunrise
			local_t = t / 0.25
			sun_color = lerp_vec4(night_sun, sunrise_sun, local_t)
			ambient_color = lerp_vec4(night_ambient, sunrise_ambient, local_t)
			sky_color = lerp_vec4(night_sky, sunrise_sky, local_t)

		elif t < 0.5:
			# sunrise -> day
			local_t = (t - 0.25) / (0.5 - 0.25)
			sun_color = lerp_vec4(sunrise_sun, day_sun, local_t)
			ambient_color = lerp_vec4(sunrise_ambient, day_ambient, local_t)
			sky_color = lerp_vec4(sunrise_sky, day_sky, local_t)

		elif t < 0.75:
			# day -> sunset
			local_t = (t - 0.5) / (0.75 - 0.5)
			sun_color = lerp_vec4(day_sun, sunset_sun, local_t)
			ambient_color = lerp_vec4(day_ambient, sunset_ambient, local_t)
			sky_color = lerp_vec4(day_sky, sunset_sky, local_t)

		else:
			# sunset -> night (wrap around)
			local_t = (t - 0.75) / (1.0 - 0.75)
			sun_color = lerp_vec4(sunset_sun, night_sun, local_t)
			ambient_color = lerp_vec4(sunset_ambient, night_ambient, local_t)
			sky_color = lerp_vec4(sunset_sky, night_sky, local_t)

		# Apply lighting
		self.sun_light.setColor(sun_color)
		self.ambient_light.setColor(ambient_color)
		self.setBackgroundColor(sky_color)

		# Update sun angle
		angle = (self.time_of_day - 0.25) * 360
		self.sun_np.setHpr(angle, -30, 0)

		return Task.cont
	
	# Autopilot drive task		
	def autopilot_drive_task(self, task):
		"""
		Panda3D task for controlling the car using autopilot.

		This task guides the car along a pre-calculated path to the delivery target.
		It calculates the required turning direction to align with the next path segment
		and applies force to move the car while respecting speed limits.
		The autopilot can be interrupted by the 'escape' key.

		Params:
		 - task (Task.Task): The Panda3D task object.
		Returns:
		 - int: Task.cont to continue the task, Task.done to stop it.
		"""
		
		if not hasattr(self, 'auto_drive_path') or not self.auto_drive_path:
			return Task.done
			
		if self.key_map["escape"]:
			print("Autopilot interrupted by Escape key.")
			self.chassisNP.node().setLinearVelocity(Vec3(0, 0, 0))  # stop car movement
			self.key_map["escape"] = False  # reset key state
			return Task.done

		car_pos = self.chassisNP.getPos()
		gx = (car_pos.getX() - self.road_offset_start_x) / self.buildings_spacing
		gy = (car_pos.getY() - self.road_offset_start_y * 0.36) / self.buildings_spacing
		col = int(gx)
		row = int(gy)
		current_grid = (row, col)
		print(current_grid)

		#Skip current point if reached
		if current_grid == self.auto_drive_path[0]:
			self.auto_drive_path.pop(0)
			if not self.auto_drive_path:
				self.chassisNP.node().setLinearVelocity(Vec3(0, 0, 0))
				return Task.done

		if not self.auto_drive_path:
			self.chassisNP.node().setLinearVelocity(Vec3(0, 0, 0))
			return Task.done

		next_cell = self.auto_drive_path[0]
		dx = next_cell[1] - current_grid[1]
		dy = next_cell[0] - current_grid[0]

		# Determine required heading (grid-based)
		if dx == 1: desired_h = 270       # right (east)
		elif dx == -1: desired_h = 90  # left (west)
		elif dy == -1: desired_h = 180   # down (south)
		elif dy == 1: desired_h = 0   # up (north)
		else:
			return Task.cont  # Invalid move
		
		current_h = self.chassisNP.getH()
		angle_diff = (desired_h - current_h + 180) % 360 - 180

		turn_speed = 100 * globalClock.getDt()
		
		
		if 0 <= row < ROWS - 1 and 0 <= col < COLUMNS - 1:
			street_speedlim = ROAD_TYPES[g_map.roadisx_get(row, col)]
			current_velocity = self.chassisNP.node().getLinearVelocity()
			current_speed = current_velocity.length()

			# Only apply force if under speed limit
			if current_speed < street_speedlim:
				force = self.vehicle_models[self.vehicle_model_idx]["mass"] * self.vehicle_models[self.vehicle_model_idx]["acceleration"]
				forward = self.chassisNP.getQuat().getForward()
				self.chassisNP.node().applyCentralForce(forward * force)
			else:
				self.chassisNP.node().setLinearVelocity(current_velocity.normalized() * street_speedlim)

		# If not aligned, rotate in place and brake
		if abs(angle_diff) > 1:
			self.chassisNP.node().setLinearVelocity(Vec3(0, 0, 0))  # Full stop to turn
			if angle_diff > 0:
				self.chassisNP.setH(current_h + min(turn_speed, angle_diff))
			else:
				self.chassisNP.setH(current_h + max(-turn_speed, angle_diff))

		return Task.cont

	
	# =============================================
	# Input Handling Methods
	# =============================================

	def zoom_in(self):
		"""
		Zoom camera in.

		Zooms the camera in by decreasing its distance to the target.
		Clamped to a minimum zoom distance of 5 units.
		Params: None
		Returns: None
		"""
		self.zoom_distance = max(5, self.zoom_distance - 2)

	def zoom_out(self):
		"""
		Zoom camera out

		Zooms the camera out by increasing its distance from the target.
		Clamped to a maximum zoom distance of 100 units.
		
		Params: None
		Returns: None
		"""
		self.zoom_distance = min(100, self.zoom_distance + 2)

	def start_rotation(self):
		"""
		Start automatic camera rotation
		Params: None
		Returns: None
		"""
		self.is_rotating = True

	def stop_rotation(self):
		"""
		Stop automatic camera rotation
		Params: None
		Returns: None
		"""
		self.is_rotating = False
		
	def minimap_zoom(self, direction):
		"""
		Zoom minimap in/out

		Adjusts the zoom level of the minimap.

		Params:
		 - direction (int): The direction of zoom: 1 to zoom in, -1 to zoom out.
							Increases/decreases the zoom coefficient by 10%.
		Returns: None
		"""
		self.minimap_zoom_coeff *= 1 + (0.1 * direction)  # 30% increase or decrease in minimap zoom
	
	# =============================================
	# End Screen Methods
	# =============================================
	
	def show_end_screen(self, win, loss_reason=None):
		"""
		Show win/loss screen

		Displays the end screen, showing whether the player won or lost,
		along with game statistics.

		Params:
		 - win (bool): True if the player won, False if the player lost.
		 - loss_reason (str, optional): A string explaining the reason for loss.
										Defaults to None if the game was won.
		Returns: None
		"""
		
		# Background
		trans_bg = DirectFrame(
			frameSize=(-1.4, 1.4, -1, 1),
			frameColor=(0, 0, 0, 0.5)
		)
		
		bg_color = (0.2, 0.6, 0.2, 1) if win else (0.6, 0.2, 0.2, 1)
		bg = DirectFrame(
			frameSize=(-1, 1, -1, 1),
			frameColor=bg_color
		)
		
		# Result text
		result_text = "SUCCESS!" if win else "GAME OVER!"
		text = OnscreenText(
			text=result_text,
			pos=(0, 0.3),
			scale=0.15,
			fg=(1, 1, 1, 1),
			align=TextNode.ACenter,
			font=loader.loadFont("./assets/fonts/OpenSans_Condensed-ExtraBold.ttf")
		)
		
		# Stats
		reason_text = reason + '\n' if loss_reason else ''
		stats_text = f"{reason_text}Deliveries Completed: {self.successful_delivery_count}\nTotal Deliveries: {self.total_delivery_count}\nMoney Earned: ${self.money:.2f}\nRating Score: {(sum(self.delivery_scores) / len(self.delivery_scores)):.1f} stars\n"
		stats = OnscreenText(
			text=stats_text,
			pos=(0, -0.1),
			scale=0.08,
			fg=(1, 1, 1, 1),
			align=TextNode.ACenter
		)
		
		# Store UI elements
		self.ui_elements.extend([bg, text, stats])
		
		# Hide 3D world
		self.render.hide()
		self.camera.hide()
	

app = MyApp()
app.run()
