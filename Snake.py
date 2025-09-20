import copy
try:
	import curses
	from curses import wrapper
except:
	import UniCurses as curses
	from curses import wrapper
import random

import time

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
	WorldSize = (20, 20)
	ObjectList = dict()
	WorldGrid = None
	highestId = -1

	#to prevent collision issues, we add objects to add to this list and then add to the world
	#after all objects have been updated
	newObjects = []

	def __init__(self, WorldSize=(20,20)):
		self.WorldSize = WorldSize
		self.WorldGrid = [[None for i in range(WorldSize[0])] for i in range(WorldSize[1])]

	def addObject(self, object):
		if(object.targetWorld != None):
			return False
		self.highestId+=1
		object.id = self.highestId
		object.targetWorld = self
		self.newObjects.append(object)

	def FinishAddObjects(self):
		for o in self.newObjects:
			if(o.pos == None or (o.pos[0] > -1 and o.pos[0] < self.WorldSize[0]
			and o.pos[1] > -1 and o.pos[1] < self.WorldSize[1]
			and self.WorldGrid[o.pos[0]][o.pos[1]] == None)):
				if o.pos == None:
					o.pos = self.getEmptyPos()
				self.WorldGrid[o.pos[0]][o.pos[1]] = o
				o.onAddToWorld(self)
				self.ObjectList[o.id] = o
			else:
				o.Destroy()
		self.newObjects.clear()

	
	def removeObject(self, Object):
		if(not Object.id in self.ObjectList.keys()):
			return
		del self.ObjectList[Object.id]
		self.WorldGrid[Object.pos[0]][Object.pos[1]] = None
		Object.targetWorld = None

	def UpdateWorld(self):
		#move phase
		for x in self.ObjectList.values():
			x.MoveTick(self)

		karr = list(self.ObjectList.keys())
		#check for collisions, slow style
		for x in range(len(karr)):
			for y in range(x+1, len(karr)):
				objx = self.ObjectList[karr[x]]
				objy = self.ObjectList[karr[y]]
				if(objx.pos == objy.pos):
					objx.OnCollision(objy, self)
					objy.OnCollision(objx, self)

		#set all object's positions
		for x in self.ObjectList.values():
			self.setObjectToPos(x)

		#update phase
		for x in self.ObjectList.values():
			x.PostCollisionTick(self)

		#spawn phase
		self.FinishAddObjects()

	#returns an Object as position pos, or None
	def GetThingAtPos(self, pos: Position):
		return self.WorldGrid[pos.x][pos.y]

	#Set an object thing to its current position, returning
	#the Object at that position previously
	def setObjectToPos(self, thing):
		if(thing.pos == None):
			thing.pos = self.getEmptyPos()
		oldObj = self.WorldGrid[thing.pos.x][thing.pos.y]
		if(oldObj != thing or thing.prevPos != thing.pos):
			if(self.WorldGrid[thing.prevPos.x][thing.prevPos.y] == thing):
				self.WorldGrid[thing.prevPos.x][thing.prevPos.y] = None
			self.WorldGrid[thing.pos.x][thing.pos.y] = thing
		return oldObj
	
	#returns an empty position in the board.thing.pos == None
	#This assumes there is at least one empty position, and will
	#return (-1, -1) otherwise
	def getEmptyPos(self):
		origx = random.randint(0, self.WorldSize[0]-1)
		origy = random.randint(0, self.WorldSize[1]-1)
		pos = Position(origx, origy)
		while(self.GetThingAtPos(pos) != None):
			pos.x+=1
			if(pos.x >= self.WorldSize[0]):
				pos.x = 0
				pos.y+=1
				if(pos.y >= self.WorldSize[1]):
					pos.y = 0
			if(pos.x == origx and pos.y == origy):
				return Position(-1, -1)
		return pos

	#prints the game world to curses
	def printWorld(self, window):
		window.erase()
		for o in self.ObjectList.values():
			curses.init_pair(1, o.getColor(), curses.COLOR_BLACK)
			y = (self.WorldSize[1]-1)-o.pos.y
			x = o.pos.x
			window.addch(y, x, o.getSymbol(), curses.color_pair(1))
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
		window.refresh()


class Object:
	pos = Position(-1, -1)
	prevPos = Position(-1, -1)
	id=-1
	targetWorld = None

	updated = False

	def __init__(self, pos: Position=None):
		self.pos = pos
	
	#script called upon being added to a world, after targetWold is set
	def onAddToWorld(self, targetWorld: SnakeGame):
		self.prevPos = copy.deepcopy(self.pos)

	#tick for updating the position of the object
	def MoveTick(self, targetWorld: SnakeGame):
		self.updated = False
		pass

	#tick which checks for collisions and updates the world's grid
	def UpdateTick(self, targetWorld: SnakeGame):
		targetWorld.setObjectToPos(self)

	#tick for updating the world to the new position and checking for collisions
	def PostCollisionTick(self, targetWorld: SnakeGame):
		if(targetWorld != None):
			targetWorld.setObjectToPos(self)
		self.updated = True

	#Called between MoveTick and PostCollisionTick depending on the Object's implementation.
	#Note that collision call order not guaranteed.
	#By default, destroys the object
	def OnCollision(self, target, targetWorld: SnakeGame):
		self.Destroy(targetWorld)

	#destroys this object, removing it from the world
	def Destroy(self, targetWorld: SnakeGame=None):
		if(targetWorld != None):
			targetWorld.removeObject(self)

	#what to print on the window,
	#also sets color
	def getSymbol(self):
		return " "
	
	#returns a color which to use to print (foreground only)
	def getColor(self):
		return curses.COLOR_WHITE


class Food(Object):
	respawnableFood = False

	def __init__(self, respawnable = False, pos = None):
		super().__init__(pos)
		self.respawnableFood = respawnable

	def OnCollision(self, target, targetWorld):
		if(self.respawnableFood and targetWorld != None):
			self.pos = None
		else:
			return super().OnCollision(target, targetWorld)

	def getSymbol(self):
		return "#"

class Snake(Object):
	parentSnake = None #if None, this is the head of the snake
	childSnake = None
	color = curses.COLOR_WHITE
	dir = Directions.RIGHT
	defaultLength = 3

	prevDir = Directions.RIGHT
	
	def __init__(self, pos: Position = None, color=curses.COLOR_WHITE, defaultLength = 3):
		super().__init__(pos)
		self.color = color
		self.defaultLength = defaultLength

	def __delattr__(self, name):
		return super().__delattr__(name)

	def __len__(self):
		if(self.childSnake == None):
			return 1
		return len(self.childSnake)

	def getSymbol(self):
		if(self.parentSnake == None):
			return "@"
		else:
			if(self.parentSnake.pos[0] == self.pos[0]):
				if(self.childSnake != None and self.childSnake.pos[0] != self.pos[0]):
					if(self.childSnake.pos[0] < self.pos[0]):
						return "/"
					else:
						return "\\"
				else:
					return "|"
			else:
				return "-"

	def getColor(self):
		return self.color

	def setParent(self, parent):
		self.color = parent.color
		self.parentSnake = parent
		parent.childSnake = self
	
	def onAddToWorld(self, targetWorld: SnakeGame):
		super().onAddToWorld(targetWorld)
		if(self.childSnake != None):
			targetWorld.addObject(self.childSnake)

	#InputTick updates the direction
	def InputTick(self, input):
		if(self.parentSnake == None):
			self.prevDir = copy.deepcopy(self.dir)
			if(self.dir != Directions.DOWN and (input == "w" or input == curses.KEY_UP)): #up
				self.dir = Directions.UP
			elif(self.dir != Directions.RIGHT and (input == "a" or input == curses.KEY_LEFT)): #left
				self.dir = Directions.LEFT
			elif(self.dir != Directions.UP and (input == "s" or input == curses.KEY_DOWN)): #down
				self.dir = Directions.DOWN
			elif(self.dir != Directions.LEFT and (input == "d" or input == curses.KEY_RIGHT)): #right
				self.dir = Directions.RIGHT

	def AddSnake(self, targetWorld: SnakeGame):
		if(self.childSnake is None):
			self.childSnake = Snake(self.prevPos)
			self.childSnake.setParent(self)
			targetWorld.addObject(self.childSnake)
		else:
			self.childSnake.AddSnake(targetWorld)

	#deletes a snake, optionally turning it into food
	def Eliminate(self, targetWorld: SnakeGame, replaceWithFood = True):
		if(self.parentSnake == None):
			self.pos = None
		else:
			targetWorld.removeObject(self)
		if(replaceWithFood):
			Food(targetWorld, pos=self.prevPos)

	#MoveTick updates our position
	def MoveTick(self, targetWorld: SnakeGame):
		self.prevPos = copy.deepcopy(self.pos)
		if(self.parentSnake == None):
			if(self.parentSnake != None):
				self.prevDir = self.dir
				self.dir = self.parentSnake.prevDir
			if self.dir == Directions.UP:
				self.pos.y += 1
				self.pos.y %= targetWorld.WorldSize[1]
			elif self.dir == Directions.DOWN:
				self.pos.y -= 1
				if(self.pos.y < 0):
					self.pos.y = targetWorld.WorldSize[1]-1
			elif self.dir == Directions.LEFT:
				self.pos.x -= 1
				if(self.pos.x < 0):
					self.pos.x = targetWorld.WorldSize[0]-1
			elif self.dir == Directions.RIGHT:
				self.pos.x += 1
				self.pos.x %= targetWorld.WorldSize[0]
			if(self.childSnake != None):
				self.childSnake.updateChain(self.prevPos, self.prevDir)

	#updateChain is called from the parent to update a child
	def updateChain(self, newPos, newDir):
		if(self.parentSnake != None):
			self.prevPos = copy.deepcopy(self.pos)
			self.pos = newPos
			self.prevDir = copy.deepcopy(self.dir)
			self.dir = newDir

			if(self.childSnake != None):
				self.childSnake.updateChain(self.prevPos, self.prevDir)

	def OnCollision(self, target: Object, targetWorld: SnakeGame):
		#only head snake
		if(self.parentSnake == None):
			if(isinstance(target, Snake)):
				if(self.parentSnake == None):
					self.Eliminate()
			elif(isinstance(target, Food)):
				self.AddSnake(targetWorld)
			else:
				return

	def UpdateTick(self, targetWorld: SnakeGame, isChild=False):
		if(not isChild and self.parentSnake == None):
			item = targetWorld.GetThingAtPos(self.pos)
			if(item != None):
				self.OnCollision(item)
			super().PostCollisionTick()
		elif(isChild):
			super().PostCollisionTick()
		return super().UpdateTick(targetWorld)

	#PostCollisionTick checks 
	def PostCollisionTick(self, targetWorld):
		if(len(self) < self.defaultLength and self.pos != self.prevPos):
			self.AddSnake(targetWorld)
		super().PostCollisionTick(targetWorld)


	def Destroy(self, targetWorld: SnakeGame=None):
		super().Destroy(targetWorld)
		if(self.childSnake != None):
			self.childSnake.Destroy()
			self.childSnake = None
		if(self.parentSnake != None and self.parentSnake.childSnake == self):
			self.parentSnake.childSnake = None

WORLD_FOOD=1
WAIT=.1

def main(stdscr):
	curses.noecho()
	curses.cbreak()
	stdscr.nodelay(True)
	stdscr.keypad(True)
	curses.curs_set(False)
	game = SnakeGame()
	ownSnake = Snake()
	game.addObject(ownSnake)
	for s in range(WORLD_FOOD):
		game.addObject(Food(True))
	curses.resizeterm(game.WorldSize[1], game.WorldSize[0])
	try:
		while True:
			try: #in a try-catch because getkey will throw an error if no key inputted
				ownSnake.InputTick(stdscr.getkey())
			except:
				pass
			game.UpdateWorld()
			time.sleep(WAIT)
			game.printWorld(stdscr)
			if curses.is_term_resized(game.WorldSize[1], game.WorldSize[0]):
				curses.resizeterm(game.WorldSize[1], game.WorldSize[0])
				stdscr.refresh()
	except KeyboardInterrupt:
		pass
	finally:
		curses.nocbreak()
		stdscr.keypad(False)
		curses.echo()
		#curses.endwin()
		curses.curs_set(True)

wrapper(main)