#!/usr/bin/python
execfile('cities/ixps.py')
execfile('cities/attackers.py')

names = set()

def newUniqueName(curName):
	if curName not in names: return curName
	for i in range(1000):
		if curName + str(i) not in names: return curName + str(i)
	return curName + random.randint(1001, 10000)

def fixNodes(nodeList):
	for node in nodeList:
		node['name'] = newUniqueName(node['name'])
		names.add(node['name'])
		node['lat'] = float(node['lat'])
		node['lng'] = float(node['lng'])


fixNodes(ixps)
fixNodes(attackers)

def printEdgeNoLoop(name1, name2, indent, level = None):
	if (name1 == name2): return
	if level != None:
		print '%s{"left":"%s", "right": "%s", "level":%d},' % (indent, name1,  name2, level)
	else:
		print '%s{"left":"%s", "right": "%s"},' % (indent, name1,  name2)

class QuadTree:
	def __init__(self, nodes, limit, key, altKey):
		self.allNodes = sorted(nodes, key=lambda k:k[key])
		self.root = None
		if (len(nodes) <= limit):
			self.left = self.right = None
		else:
			splitIndex = len(nodes) >> 1
			self.left = QuadTree(self.allNodes[:splitIndex], limit, altKey, key)
			self.right = QuadTree(self.allNodes[splitIndex:], limit, altKey, key)
			if (splitIndex > 0):
				self.left.root = self.allNodes[splitIndex - 1]
			if (splitIndex < len(self.allNodes)):
				self.right.root = self.allNodes[splitIndex]
	def printEdges(self, rootNodeName, level, indent):
		if (self.left != None and self.left.root != None): 
			printEdgeNoLoop(self.left.root['name'], rootNodeName,indent,level)
			self.left.printEdges(self.left.root['name'], level + 1, indent)
		if (self.right != None and self.right.root != None): 
			printEdgeNoLoop(self.right.root['name'], rootNodeName,indent,level)
			self.right.printEdges(self.right.root['name'], level + 1, indent)
	def printEdgesTop(self, indent):
		self.left.printEdges(self.left.root['name'], 1, indent)
		self.right.printEdges(self.right.root['name'], 1, indent)
		printEdgeNoLoop(self.right.root['name'], self.right.root['name'],indent,0)
		
	def printEdgesToRoot(self, indent):
		if self.root == None: return
		nodes = set([node['name'] for node in self.allNodes])
		rootName = self.root['name']
		nodes.remove(rootName)
		for nodeName in nodes:
			print '%s{"left":"%s", "right": "%s"},' % (indent, rootName, nodeName)
	def printAllEdgesToRoot(self, indent):
		if (self.allNodes == None): return
		if (self.left == None):
			self.printEdgesToRoot(indent)
		else:
			self.left.printEdgesToRoot(indent)
			if self.right != None:
				self.right.printEdgesToRoot(indent)

	def getAllEdgeRoots(self):
		if(self.left == None and self.right == None):
			return [self.root['name']]
		else:
			result = []
			if (self.left):
				result = self.left.getAllEdgeRoots()
			if (self.right):
				return result + self.right.getAllEdgeRoots()
			else: return result

	def returnLeaves(self):
		if(self.left == None and self.right == None):
			return [self.allNodes]
		elif (self.left == None):
			return self.right.returnLeaves()
		elif (self.right == None):
			return self.left.returnLeaves()
		else:
			return self.left.returnLeaves() + self.right.returnLeaves()



def genBackbone():
	qt = QuadTree(ixps, 1, 'lat', 'lng')
	print 'backbone = ['
	qt.printEdgesTop("   ")
	print ']'

def genEdge():
	qt = QuadTree(attackers, 50, 'lat', 'lng')
	print 'edges = ['
	qt.printAllEdgesToRoot("    ")
	print "]"
	edgeRoots = qt.getAllEdgeRoots()
	ixpNames = [node['name'] for node in ixps]
	if len(edgeRoots) < len(ixpNames):
		ixpNames=ixpNames[:len(edgeRoots)]
	while len(edgeRoots) > len(ixpNames): ixpNames = ixpNames + ixpNames
	edgeRoots = edgeRoots[:len(ixpNames)]
	print 'access=['
	for i in range(len(edgeRoots)):
		printEdgeNoLoop(edgeRoots[i], ixpNames[i],'    ')
	print ']'
	subNets = qt.returnLeaves()
	for i in range(len(subNets)):
		for attacker in subNets[i]:
			attacker['subnet'] = i

def printIXPs():
	print 'ixps = ['
	for node in ixps:
		print '    {"name": "%s", "lat":%.2f, "lng":%.2f},' % (node['name'], node['lat'], node['lng'])
	print ']'


def printAttackers():
	print 'attackers=['
	for node in attackers:
		print '    {"name": "%s", "lat":%.2f, "lng":%.2f, "subnet": %d},' % (node['name'], node['lat'], node['lng'], node['subnet'])
	print ']'


print '# -*- coding: utf-8 -*-'
genBackbone()
genEdge()
printIXPs()
printAttackers()







