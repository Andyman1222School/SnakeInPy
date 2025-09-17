import copy
import curses
from curses import wrapper

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

class SnakeGame:
	WorldSize = (100, 100)
	ObjectList = dict()
	WorldGrid = None
	highestId = -1

	def __init__(self, WorldSize=(100,100)):
		self.WorldSize = WorldSize
		self.WorldGrid = [[None]*WorldSize[0]]*WorldSize[1]

	def addObject(self, object):
		if(object.targetWorld != None):
			return False
		if(object.pos[0] > -1 and object.pos[0] < self.WorldSize[0]
		and object.pos[1] > -1 and object.pos[1] < self.WorldSize[1]
		and self.WorldGrid[object.pos[0]][object.pos[1]] == None):
			self.highestId+=1
			object.id = self.highestId
			self.ObjectList[object.id] = object
			object.onAddToWorld()
			return True
		return False

	def UpdateWorld(self, input=None):
		#move phase
		for x in self.ObjectList.values:
			x.MoveTick()

		#update phase
		for x in self.ObjectList.values:
			x.UpdateTick()

	#returns an Object as position pos, or None
	def GetThingAtPos(self, pos: Position):
		return self.WorldGrid[pos.x][pos.y]

	#Set an object thing to its current position, returning
	#the Object at that position previously
	def setObjectToPos(self, thing):
		oldObj = self.WorldGrid[thing.pos.x][thing.pos.y]
		self.WorldGrid[thing.pos.x][thing.pos.y] = thing
		self.WorldGrid[thing.prevPos.x][thing.prevPos.y] = None
		return oldObj

class Object:
	pos = Position(-1, -1)
	prevPos = Position(-1, -1)
	id=-1
	targetWorld = None

	def __init__(self, pos, targetWorld: SnakeGame):
		self.pos = pos
		self.id=targetWorld.GetNewId()
		self.targetWorld = targetWorld
		self.targetWorld.addObject(self)
	
	def onAddToWorld(self):
		pass

	def MoveTick(self):
		pass

	def UpdateTick(self):
		pass

	#Called in UpdateTick depending on the Object's implementation.
	#Note that collision call order not guaranteed.
	def OnCollision(self, target):
		pass


class Food(Object):
	pass		

class Snake(Object):
	parentSnake = None #if None, this is the head of the snake
	childSnake = None
	color = curses.COLOR_WHITE
	dir = Directions.RIGHT

	prevDir = Directions.RIGHT
	
	def __init__(self, pos, color=curses.COLOR_WHITE):
		super().__init__(self, pos)
		self.color = color

	def __init__(self, pos, parent):
		self.__init__(self, pos, parent.color)
		self.parentSnake = parent
		parent.childSnake = self
	
	def onAddToWorld(self):
		super().onAddToWorld()
		if(self.childSnake != None):
			self.targetWorld.addObject(self.childSnake)

	#InputTick updates the direction
	def InputTick(self, input):
		if(self.parentSnake == None):
			self.prevDir = self.dir
			self.dir = input

	#MoveTick updates our position
	def MoveTick(self):
		self.prevPos = copy.deepcopy(self.pos)
		if(self.parentSnake == None):
			if self.dir == Directions.UP:
				self.pos.y += 1
				self.pos.y %= self.targetWorld.WorldSize[1]
			elif self.dir == Directions.DOWN:
				self.pos.y -= 1
				if(self.pos.y < 0):
					self.pos.y = self.targetWorld.WorldSize[1]-1
			elif self.dir == Directions.LEFT:
				self.pos.x -= 1
				if(self.pos.x < 0):
					self.pos.x = self.targetWorld.WorldSize[0]-1
			elif self.dir == Directions.RIGHT:
				self.pos.x += 1
				self.pos.x %= self.targetWorld.WorldSize[0]
	
	

	#updateChain is called from the parent to update a child
	def updateChain(self, newPos):
		if(self.parentSnake != None):
			prevPos = self.pos
			self.pos = newPos

			if(self.childSnake != None):
				self.childSnake.updateChain(prevPos)

	def OnCollision(self, target: Object):
		super().OnCollision(target)
		if(isinstance(target, Snake)):
		elif(isinstance(target, Food)):

		else:
			return



	#UpdateTick checks 
	def UpdateTick(self):
		if(self.parentSnake == None):
			item = self.targetWorld.GetThingAtPos(self.pos)
			if(item == None):
				self.targetWorld.setObjectToPos(self)

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()

def main(stdscr):
	game = SnakeGame()

wrapper(main)