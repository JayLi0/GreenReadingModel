import csv
import math
import scipy.stats
import pandas as pd
import random
import copy

pd.set_option('mode.chained_assignment', None)

#Golf Ball Weighs = 45.93 g
#6.0 ft, CF = 0.8200 / 6.0 = 0.137 (Weber 6.0 ft: 0.164) 
#7.0 ft, CF = 0.8200 / 7.0 = 0.117 
#8.0 ft, CF = 0.8200 / 8.0 = 0.102 
#9.0 ft, CF = 0.8200 / 9.0 = 0.091 (Weber 8.5 ft: 0.116) 
#10.0 ft, CF = 0.8200 / 10.0 = 0.082 
#11.0 ft, CF = 0.8200 / 11.0 = 0.075 (Weber 11.0 ft: 0.089) 
#12.0 ft, CF = 0.8200 / 12.0 = 0.068 
#13.0 ft, CF = 0.8200 / 13.0 = 0.063 (Weber 12.5 ft: 0.079)
#Reference: https://www.physicsforums.com/threads/golf-ball-rolling-coefficient.205474/


#degrees -> percent slope == tan(degrees) * 100 = percent slope

G = 32.1741 # Force of Gravity in ft/s^2
FPS = 0.01 # How long each frame lasts
Per2Deg = 0.5729389025458341 # Percent to Degrees

#Distance Formula between two points
# a = [x1, y1]
# b = [x2, y2]
def distance(a, b):
	return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

# Object Green
class green:
	def __init__(self, size, slope, d, pin, gs):
		self.size = size
		self.map = [[(d, slope)] * size] * size
		self.pin = pin
		self.stimp = gs

	# Get the slope and direction of slope at a given point
	def getSlope(self, x, y):
		if (x >= self.size or y >= self.size or x < 0 or y < 0): return self.map[0][0]
		return self.map[math.floor(y)][math.floor(x)]

#Object Ball
class ball:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.speed = 0
		self.dir = 0

	# Set Initial Speed & Direction of Putt
	def hit(self, sp, line):
		self.speed = sp
		self.dir = line

	# Move Ball
	def move(self, slope, d, stimp):
		coF = 0.8200 / stimp
		
		# Save Current Location of Ball

		x0 = self.x
		y0 = self.y
		d0 = self.dir

		# Calculate Acceleration Forces Acting on the Ball
		# a1 = Force From the slope pushing it down the slope
		# a2 = Force of Friction
		a1 = G * math.sin(slope) * (FPS**2)
		a2 = G * coF * (FPS**2) * math.cos(slope)

		#Calculate new position of ball
		self.x += math.sin(self.dir) * (self.speed * FPS) + math.sin(d)*a1 + math.sin(self.dir - math.radians(180))*a2
		self.y += math.cos(self.dir) * (self.speed * FPS) + math.cos(d)*a1 + math.cos(self.dir - math.radians(180))*a2
		
		# Calculate change in position to calculate speed and direction
		dx = self.x - x0
		dy = self.y - y0
		self.speed = math.sqrt(dx**2 + dy**2) / FPS
		self.dir = math.atan(dx/dy)

		if self.speed < .01: self.speed = 0

	# Get Current Location of Ball
	def getLocation(self):
		return [self.x, self.y]

	# Get All Data of the Ball
	def getData(self):
		return {'X': self.x, 'Y' : self.y, 'Dir' : math.degrees(self.dir), 'Speed' : self.speed}

# Object Putt
class putt:
	def __init__(self, ball, green):
		self.ball = copy.deepcopy(ball)
		self.green = copy.deepcopy(green)

		# Dataframe of all past positions of the ball
		self.history = pd.DataFrame(columns = ['X', 'Y', 'Dir', 'Speed'])

		# Closest position of the ball to the hole
		self.closest2Hole = [copy.deepcopy(self.ball.x), copy.deepcopy(self.ball.y)]

		# Distance of the closest position to the hole
		self.closest2HoleDist = distance([self.ball.x, self.ball.y], self.green.pin)
		self.puttHit = False

	# Calculates the Closest to the Hole Between two Points
	def getClosest(self, p1, p2, hole):
		dx = (p2[0] - p1[0]) / 4
		dy = (p2[1] - p1[1]) / 4
		closestDist = distance(p2, hole)
		closestPoint = p2
		for i in range(1,5):
			pNext = [p2[0] - (dx * i), p2[1] - (dy * i)]
			dist = distance(pNext, hole)
			if closestDist > dist:
				closestDist = dist
				closestPoint = copy.deepcopy(pNext)
		return (closestDist, closestPoint)

	# Moves the position of the ball
	def move(self):
		loc = self.ball.getLocation()
		slo = self.green.getSlope(loc[0], loc[1])
		self.ball.move(slo[1], slo[0], self.green.stimp)

		newR = pd.DataFrame(self.ball.getData(), index=[0])

		self.history = pd.concat([self.history, newR], ignore_index = True)
		self.closest2HoleDist, self.closest2Hole = self.getClosest(self.closest2Hole, [self.ball.x, self.ball.y], self.green.pin)

	def rollPutt(self, iSpeed, iDir):
		self.ball.hit(iSpeed, math.radians(iDir))
		while (self.ball.speed > 0.02):
			self.move()
		self.puttHit = True

	# Gets Distance of Final Position From Hole
	def finishDist(self):
		assert(self.puttHit == True)
		final = [self.history.iloc[-1]['X'], self.history.iloc[-1]['Y']]
		return distance(final, self.green.pin)

	# Checks if putt was made and if the distance past was within the acceptable boundary
	def madePutt(self, ftPast):
		ftLeft = self.finishDist()
		if abs(ftLeft - ftPast) < 0.1 and self.closest2HoleDist < 0.05:
			return True
		else: return False

	# Function to determine the change in speed or direction in the putt.
	def adjustment(self, by0, ftPast):
		if self.green.pin[0] > self.closest2Hole[0]:
			dTheta = 0.018947
		elif self.green.pin[0] < self.closest2Hole[0]:
			dTheta = -0.010009
		else: dTheta = 0
		
		if self.history.iloc[-1]['Y'] < self.green.pin[1]:
			dSpeed = .5
		elif self.finishDist() < ftPast + .1: dSpeed = 0.018947
		elif self.finishDist() > ftPast - .1: dSpeed = -0.010009
		else: dSpeed = 0
		return {'dTheta' : dTheta, 'dSpeed' : dSpeed}

# Function to Calculate Aim Point in Inches Based on Angle of Initial Putt and Putt Length
def getAimpoint(iDir, puttLength):
	return round(abs(math.tan(math.radians(iDir))*abs(puttLength)) * 12, 4)

# Function to brute force finding the initial speed and direction of a putt
# Returns the Aim Point, Initial Direction, and Initial Speed
def findLine (puttLen, slope, gs, slopeDir, ftLeft):
	g = green(50, math.radians(slope * Per2Deg), math.radians(slopeDir), [25, 25], gs)
	b = ball(25, 25 - puttLen)
	by0 = 25 - puttLen
	make = False
	iSpeed = abs(b.y - g.pin[1]) * (0.75)
	sideSlope = math.sin(math.radians(slopeDir)) * slope
	iDir = -1 * math.degrees(math.atan(((.05 * puttLen * sideSlope * gs))/(puttLen*12)))
	count = 0

	while make == False:
		p = putt(b, g)
		p.rollPutt(iSpeed, iDir)
		make = p.madePutt(ftLeft)
		adj = p.adjustment(by0, ftLeft)
		iDir += adj['dTheta']
		iSpeed += adj['dSpeed']
		count += 1
	puttLen = distance([b.x, b.y], g.pin)
	return (getAimpoint(iDir, puttLen), iDir, iSpeed)

# Function Used to Generate Data to Analyze
# Creates a csv of initial conditions and the resulting aim point
def testMakeSpeedDif():
	res = pd.DataFrame()
	for puttLen in range(3,15):
		for sideSlope in [1, 1.5, 2, 2.5]:
			for gs in [10, 11, 12, 13]:
				for slopeDir in [90]:
					for ftPast in [1.25]:
						newR = pd.DataFrame({
							'Putt Length' : puttLen,
							'Green Speed' : gs,
							'Slope (%)' : sideSlope,
							'Slope Direction' : slopeDir,
							'Feet Past Hole' : ftPast,
							'Aim Point' : findLine(puttLen, sideSlope, gs, slopeDir, ftPast)[0]
						}, index = [0])
						print ((puttLen, sideSlope, gs, slopeDir, ftPast))
						res = pd.concat([res, newR], ignore_index = True).reset_index(drop = True)
	res.to_csv('Test.csv')

# Translate Two Slope Readings into one with the direction of the slope for testing purposes
def SideUpDownToSlopeDir(sideSlope, updown):
	try:
		angle = math.degrees(math.atan(sideSlope/updown))
		if angle > 0: angle = 180 - angle
		else: angle = abs(angle)
	except:
		angle = 90

	percent_slope = sideSlope / math.sin(math.radians(angle))
	deg_slope = math.degrees(math.atan(percent_slope / 100))

	percent_slope = round(percent_slope, 2)
	angle = round(angle, 0)
	return (percent_slope, angle)

# Test Cases

def printTestCaseResults(sol, res):
	print("----------------")
	print(str(sol) + "  |  " + str(res))

def testCases():
	printTestCaseResults("1.7", findLine(8, 0.5, 8, 90, 1.25))
	printTestCaseResults("5.2", findLine(8, 1.5, 8, 90, 1.25))
	printTestCaseResults("10", findLine(9, 2.5, 8, 90, 1.25))
	printTestCaseResults("10", findLine(7, 2.5, 10.6, 90, 1.25))
	printTestCaseResults("1.6", findLine(3, 1.5, 10.6, 90, 1.25))

	printTestCaseResults("0", findLine(9, 0, 8, 90, 1.25))
	printTestCaseResults("0", findLine(9, 2.5, 8, 0, 1.25))
	printTestCaseResults("0", findLine(9, 2.5, 8, 180, 1.25))

	
	slope, angle = SideUpDownToSlopeDir(0.8, 0.5)
	printTestCaseResults("4", findLine(9, slope, 10, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(1.5, 1.1)
	printTestCaseResults("10", findLine(14, slope, 8.3, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(3.0, -0.9)
	printTestCaseResults("15.1", findLine(7.5, slope, 12, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(2.9, -0.2)
	printTestCaseResults("8.8", findLine(6, slope, 10, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(1.9, -0.8)
	printTestCaseResults("15", findLine(12, slope, 10.7, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(3.2, -0.9)
	printTestCaseResults("23", findLine(11, slope, 11, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(0.9, 1.9)
	printTestCaseResults("6.2", findLine(12, slope, 10.5, angle, 1.25))

	slope, angle = SideUpDownToSlopeDir(2, -1.0)
	printTestCaseResults("10", findLine(9, slope, 10, angle, 1.25))
