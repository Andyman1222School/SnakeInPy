import copy
import curses
from curses import wrapper
import random
import time

WORLD_FOOD=1
FOOD_EXPIRE_MIN=25
FOOD_EXPIRE_MAX=100
WAIT=.05
WORLD_SIZE=(20,20)

class Directions:
	UP= "up"
	DOWN= "down"
	LEFT = "left"
	RIGHT = "right"

class Position:
	x = -1
	y = -1

	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __getitem__(self, key):
		if key==0:
			return self.x
		elif key==1:
			return self.y
		else:
			return None

	def __setitem__(self, key, value):
		if key==0:
			self.x = value
			return self.x
		elif key==1:
			self.y = value
			return self.y
		else:
			return None
		
	def __eq__(self, other):
		return other != None and isinstance(other, Position) and self.x == other.x and self.y == other.y

class SnakeGame:
	world_size = WORLD_SIZE
	object_list = dict()
	world_grid = None
	_highest_id = -1

	#to prevent collision issues, we add objects to add to this list and then add to the world
	#after all objects have been updated
	new_objects = []

	#similar to new_objects but for objects to destroy instead
	destroying_objects = []

	def __init__(self, world_size=WORLD_SIZE):
		self.world_size = world_size
		self.world_grid = [[None for i in range(world_size[0])] for i in range(world_size[1])]

	def add_object(self, object):
		if(object in self.object_list):
			return False
		self._highest_id+=1
		object.id = self._highest_id
		self.new_objects.append(object)

	def finish_add_objects(self):
		for o in self.new_objects:
			if(o.pos == None or (o.pos[0] > -1 and o.pos[0] < self.world_size[0]
			and o.pos[1] > -1 and o.pos[1] < self.world_size[1]
			and self.world_grid[o.pos[0]][o.pos[1]] == None)):
				if o.pos == None:
					o.pos = self.get_empty_pos()
				self.world_grid[o.pos[0]][o.pos[1]] = o
				o.on_add_to_world(self)
				self.object_list[o.id] = o
			else:
				o.destroy()
		self.new_objects.clear()

	
	def remove_object(self, object):
		if(not object.id in self.object_list.keys()):
			return
		self.destroying_objects.append(object)
		
		

	def finish_remove_objects(self):
		for o in self.destroying_objects:
			self.world_grid[o.pos[0]][o.pos[1]] = None
			if o.id in self.object_list.keys():
				del self.object_list[o.id]
		self.destroying_objects.clear()

	def pre_input_update(self):
		for x in self.object_list.values():
			x.pre_input_tick(self)

	def update_world(self):
		#move phase
		for x in self.object_list.values():
			x.move_tick(self)

		karr = list(self.object_list.keys())
		#check for collisions, slow style
		for x in range(len(karr)):
			for y in range(x+1, len(karr)):
				objx = self.object_list[karr[x]]
				objy = self.object_list[karr[y]]
				if(objx.pos == objy.pos):
					objx.on_collision(objy, self)
					objy.on_collision(objx, self)

		#delete objects that should be removed from collisions
		self.finish_remove_objects()

		#set all object's positions
		for x in self.object_list.values():
			self.set_object_to_pos(x)

		#update phase
		for x in self.object_list.values():
			x.post_collision_tick(self)



		#spawn phase
		self.finish_add_objects()

	#returns an Object as position pos, or None
	def get_thing_at_pos(self, pos: Position):
		return self.world_grid[pos.x][pos.y]

	#Set an object thing to its current position, returning
	#the Object at that position previously
	def set_object_to_pos(self, thing):
		if(thing.pos == None):
			thing.pos = self.get_empty_pos()
		oldObj = self.world_grid[thing.pos.x][thing.pos.y]
		if(oldObj != thing or thing.prev_pos != thing.pos):
			if(self.world_grid[thing.prev_pos.x][thing.prev_pos.y] == thing):
				self.world_grid[thing.prev_pos.x][thing.prev_pos.y] = None
			self.world_grid[thing.pos.x][thing.pos.y] = thing
		return oldObj
	
	#returns an empty position in the board.thing.pos == None
	#This assumes there is at least one empty position, and will
	#return (-1, -1) otherwise
	def get_empty_pos(self):
		origx = random.randint(0, self.world_size[0]-1)
		origy = random.randint(0, self.world_size[1]-1)
		pos = Position(origx, origy)
		while(self.get_thing_at_pos(pos) != None):
			pos.x+=1
			if(pos.x >= self.world_size[0]):
				pos.x = 0
				pos.y+=1
				if(pos.y >= self.world_size[1]):
					pos.y = 0
			if(pos.x == origx and pos.y == origy):
				return Position(-1, -1)
		return pos

	#prints the game world to curses
	def print_world(self, window):
		window.erase()
		for o in self.object_list.values():
			curses.init_pair(1, o.get_color(), curses.COLOR_BLACK)
			y = (self.world_size[1]-1)-o.pos.y
			x = o.pos.x
			window.addch(y+1, x+1, o.get_symbol(), curses.color_pair(1))
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
		window.refresh()


class Object:
	pos = Position(-1, -1)
	prev_pos = Position(-1, -1)
	id=-1
	target_world = None

	updated = False

	def __init__(self, pos: Position=None):
		self.pos = pos

	#called on all objects before processing input
	def pre_input_tick(self, target_world: SnakeGame):
		pass

	#script called upon being added to a world, after targetWold is set
	def on_add_to_world(self, target_world: SnakeGame):
		self.prev_pos = copy.deepcopy(self.pos)

	#tick for updating the position of the object
	def move_tick(self, target_world: SnakeGame):
		self.updated = False
		pass

	#tick for updating the world to the new position after checking for collisions
	def post_collision_tick(self, target_world: SnakeGame):
		if(target_world != None):
			target_world.set_object_to_pos(self)
		self.updated = True

	#Called between move_tick and post_collision_tick depending on the Object's implementation.
	#Note that collision call order not guaranteed.
	#By default, destroys the object
	def on_collision(self, target, target_world: SnakeGame):
		self.destroy(target_world)

	#destroys this object, removing it from the world
	def destroy(self, target_world: SnakeGame=None):
		if(target_world != None):
			target_world.remove_object(self)

	#what to print on the window,
	#also sets color
	def get_symbol(self):
		return " "
	
	#returns a color which to use to print (foreground only)
	def get_color(self):
		return curses.COLOR_WHITE


class Food(Object):

	#number of ticks before the food destroys itself, set to -1 for unlimited, 1 to survive only one tick
	#If respawnable is true, food will change position instead of getting destoryed
	num_ticks = -1

	min_ticks = -1
	max_ticks = -1

	respawnable = False

	def __init__(self, respawnable=False, min_ticks = FOOD_EXPIRE_MIN, max_ticks = FOOD_EXPIRE_MAX, pos = None):
		super().__init__(pos)
		self.min_ticks = min_ticks
		self.max_ticks = max_ticks
		self.num_ticks = random.randint(min_ticks, max_ticks)
		self.respawnable = respawnable

	def move_tick(self, target_world: SnakeGame):
		if self.num_ticks > 0:
			self.num_ticks -= 1
			if self.num_ticks == 0:
				self.destroy(target_world)

	def destroy(self, target_world = None):
		if(self.respawnable and target_world != None):
			self.pos = None
			self.num_ticks = random.randint(self.min_ticks, self.max_ticks)
		else:
			return super().destroy(target_world)

	def get_symbol(self):
		return "#"

class Snake(Object):
	parent_snake = None #if None, this is the head of the snake
	child_snake = None
	color = curses.COLOR_WHITE
	dir = Directions.RIGHT
	default_length = 2
	head_symbol="@"

	prev_dir = Directions.RIGHT
	
	def __init__(self, pos: Position = None, color=curses.COLOR_WHITE, defaultLength = 3):
		super().__init__(pos)
		self.color = color
		self.default_length = defaultLength

	def __delattr__(self, name):
		return super().__delattr__(name)

	def __len__(self):
		if(self.child_snake == None):
			return 1
		return 1+len(self.child_snake)

	def pre_input_tick(self, target_world):
		if(self.parent_snake == None):
			self.prev_dir = copy.deepcopy(self.dir)
			self.prev_pos = copy.deepcopy(self.pos)
		
		else:
			self.prev_pos = copy.deepcopy(self.pos)
			self.prev_dir = copy.deepcopy(self.dir)

		if(self.child_snake != None):
			self.child_snake.pre_input_tick(target_world)

	def get_symbol(self):
		if(self.parent_snake == None):
			return self.head_symbol
		else:
			dir1 = self.parent_snake.dir
			dir2 = self.parent_snake.prev_dir
			dir3 = self.prev_dir
			if(dir1 == dir2): #no change in dir
				if(dir2 == Directions.UP or dir2 == Directions.DOWN):
					return "|"
				else:
					return "-"
			else: #change in dir
				if((dir1 == Directions.UP and dir2 == Directions.LEFT)
	   				or (dir1 == Directions.DOWN and dir2 == Directions.RIGHT)
					or (dir1 == Directions.LEFT and dir2 == Directions.UP)
	   				or (dir1 == Directions.RIGHT and dir2 == Directions.DOWN)):
					return "\\"
				else:
					return "/"
				

	def get_color(self):
		return self.color

	def set_parent(self, parent):
		self.color = parent.color
		self.parent_snake = parent
		parent.child_snake = self
	
	def on_add_to_world(self, target_world: SnakeGame):
		super().on_add_to_world(target_world)
		if(self.child_snake != None):
			target_world.add_object(self.child_snake)

	#input_tick updates the direction
	def input_tick(self, input):
		if(self.parent_snake == None):
			if(self.dir != Directions.DOWN and (input == "w" or input == curses.KEY_UP)): #up
				self.dir = Directions.UP
			elif(self.dir != Directions.RIGHT and (input == "a" or input == curses.KEY_LEFT)): #left
				self.dir = Directions.LEFT
			elif(self.dir != Directions.UP and (input == "s" or input == curses.KEY_DOWN)): #down
				self.dir = Directions.DOWN
			elif(self.dir != Directions.LEFT and (input == "d" or input == curses.KEY_RIGHT)): #right
				self.dir = Directions.RIGHT

	def add_snake(self, target_world: SnakeGame):
		if(self.child_snake is None):
			self.child_snake = Snake(self.prev_pos)
			self.child_snake.set_parent(self)
			target_world.add_object(self.child_snake)
		else:
			self.child_snake.add_snake(target_world)

	#deletes a snake, optionally turning it into food
	def eliminate(self, target_world: SnakeGame, replace_with_food = True):
		if(self.parent_snake == None):
			self._on_eliminate(target_world, replace_with_food)
			self.pos = None
	
	def _on_eliminate(self, target_world: SnakeGame, replace_with_food = True):
		if(self.parent_snake != None):
			self.destroy(target_world, False)
		if(replace_with_food):
			target_world.add_object(Food(pos=self.pos))
		if(self.child_snake != None):
			self.child_snake._on_eliminate(target_world, replace_with_food)

	#move_tick updates our position
	def move_tick(self, target_world: SnakeGame):
		if(self.parent_snake == None):
			if self.dir == Directions.UP:
				self.pos.y += 1
				self.pos.y %= target_world.world_size[1]
			elif self.dir == Directions.DOWN:
				self.pos.y -= 1
				if(self.pos.y < 0):
					self.pos.y = target_world.world_size[1]-1
			elif self.dir == Directions.LEFT:
				self.pos.x -= 1
				if(self.pos.x < 0):
					self.pos.x = target_world.world_size[0]-1
			elif self.dir == Directions.RIGHT:
				self.pos.x += 1
				self.pos.x %= target_world.world_size[0]
		else:
			self.dir = self.parent_snake.prev_dir
			self.pos = self.parent_snake.prev_pos

		if(self.child_snake != None):
			self.child_snake.move_tick(target_world)

	def on_collision(self, target: Object, target_world: SnakeGame):
		#only head snake
		if(self.parent_snake == None):
			if(isinstance(target, Snake)):
				if(self.parent_snake == None):
					self.eliminate(target_world)
			elif(isinstance(target, Food)):
				self.add_snake(target_world)
			else:
				return

	#post_collision_tick checks 
	def post_collision_tick(self, target_world):
		if(self.parent_snake == None and len(self) < self.default_length and self.pos != self.prev_pos):
			self.add_snake(target_world)
		super().post_collision_tick(target_world)


	def destroy(self, target_world: SnakeGame=None, destroy_child = True):
		super().destroy(target_world)
		if(self.child_snake != None and destroy_child):
			self.child_snake.destroy()
			self.child_snake = None
		if(self.parent_snake != None and self.parent_snake.child_snake == self):
			self.parent_snake.child_snake = None

def main(stdscr):
	curses.noecho()
	curses.cbreak()
	stdscr.nodelay(True)
	stdscr.keypad(True)
	try:
		curses.curs_set(False)
		curses.clear()
	except:
		pass
	game = SnakeGame()
	own_snake = Snake()
	game.add_object(own_snake)
	for s in range(WORLD_FOOD):
		game.add_object(Food(True))
	curses.resize_term(game.world_size[1]+2, game.world_size[0]+3)
	
	try:
		esc_press=False
		while not esc_press:
			game.pre_input_update()
			try: #in a try-catch because getkey will throw an error if no key inputted
				k = stdscr.getkey()
				esc_press = k == "KEY_BACKSPACE"
				own_snake.input_tick(k)
			except:
				pass
			game.update_world()
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
			time.sleep(WAIT)
			game.print_world(stdscr)
			for i in range(1, game.world_size[1]+1):
				stdscr.addch(i, game.world_size[0]+1, ":")
				stdscr.addch(i, 0, ":")
			for i in range(0, game.world_size[0]+2):
				stdscr.addch(game.world_size[1]+1, i, ".")
				stdscr.addch(0, i, ".")
			if curses.is_term_resized(game.world_size[1]+2, game.world_size[0]+3):
				curses.resize_term(game.world_size[1]+2, game.world_size[0]+3)
				stdscr.refresh()
	except KeyboardInterrupt:
		pass
	finally:
		curses.nocbreak()
		stdscr.keypad(False)
		curses.echo()
		#curses.endwin()
		try:
			curses.curs_set(True)
		except:
			pass

wrapper(main)