import FreeCAD
import math
from functools import cmp_to_key
from pivy import coin
from itertools import groupby

def compareVectors(vertex1, vertex2):
    vect1 = vertex1['vector']
    vect2 = vertex2['vector']

    xDiff = vect1[0] - vect2[0]
    yDiff = vect1[1] - vect2[1]
    zDiff = vect1[2] - vect2[2]

    if zDiff != 0:
        return zDiff
    
    if yDiff != 0:
        return yDiff
    
    return xDiff

class Face():
    def __init__(self):
        self.indices = []
        self.vertices = []
    
    def addVertex(self, index, vect):
        if index not in self.indices:
            self.indices.append(index)

            self.vertices.append({
                'index': index,
                'vector': vect.getValue()
            })

            self.length = 0
            self.height = 0
    
    def appendTextureCoordinates(self, textureCoords, realSize):
        scaleFactor = self.calculateScaleFactor(realSize)

        self.appendCoordinate(textureCoords, self.vertices[0], 0, 0)
        self.appendCoordinate(textureCoords, self.vertices[1], scaleFactor[0], 0)
        self.appendCoordinate(textureCoords, self.vertices[2], 0, scaleFactor[1])
        self.appendCoordinate(textureCoords, self.vertices[3], scaleFactor[0], scaleFactor[1])
    
    def calculateScaleFactor(self, realSize):
        tScale = 1
        sScale = 1

        if realSize is not None:
            realS = realSize['s']

            if realS > 0:
                sScale = self.length / realS
            
            realT = realSize['t']

            if realT > 0:
                tScale = self.height / realT

        print('%s, %s' % (sScale, tScale))

        return [sScale, tScale]
    
    def appendCoordinate(self, textureCoords, vertex, s, t):
        textureCoords.point.set1Value(vertex['index'], s, t)

    def finishFace(self):
        '''Will sort the list so that the vertices are ordered. For a face made up of four vertices 
        we end up with a order of [bottom left, bottom right, top left, top right'''

        self.vertices.sort(key=cmp_to_key(compareVectors))

        bottomLeft = self.vertices[0]['vector']
        bottomRight = self.vertices[1]['vector']
        topLeft = self.vertices[2]['vector']
        topRight = self.vertices[3]['vector']

        bottomLeftVect = FreeCAD.Vector(bottomLeft[0], bottomLeft[1], bottomLeft[2])
        bottomRightVect = FreeCAD.Vector(bottomRight[0], bottomRight[1], bottomRight[2])
        topLeftVect = FreeCAD.Vector(topLeft[0], topLeft[1], topLeft[2])

        self.length = bottomLeftVect.distanceToPoint(bottomRightVect)
        self.height = bottomLeftVect.distanceToPoint(topLeftVect)
    
    def print(self):
        for vertex in self.vertices:
            print('    %s' % (vertex, ))

class FaceSet():
    def __init__(self):
        self.faces = []
    
    def addFace(self, faceCoordinates, vertices):
        face = Face()

        for coordinate in faceCoordinates:
            for index in coordinate:
                face.addVertex(index, vertices[index])
        
        face.finishFace()

        self.faces.append(face)
    
    def calculateTextureCoordinates(self, realSize):
        textureCoords = coin.SoTextureCoordinate2()

        for face in self.faces:
            face.appendTextureCoordinates(textureCoords, realSize)

        return textureCoords
    
    def print(self):
        for face in self.faces:
            print('Face:')
            face.print()
    
def findVertexCoordinates(node):
     for child in node.getChildren():
        if child.getTypeId().getName() == 'Coordinate3':
            return child

def findSwitch(node):
    for child in node.getChildren():
        if child.getTypeId().getName() == 'Switch':
            return child

def findBrepFaceset(node):
    children = node.getChildren()

    if children is None or children.getLength() == 0:
        return None
    
    for child in children:
        if child.getTypeId().getName() == 'SoBrepFaceSet':
            return child
        
        brep = findBrepFaceset(child)

        if brep is not None:
            return brep

def buildFaceCoordinates(brep):
    triangles = []
    faces = []

    groups = groupby(brep.coordIndex, lambda coord: coord == -1)
    triangles = [tuple(group) for k, group in groups if not k]

    nextTriangle = 0

    for triangleCount in brep.partIndex:
        faces.append(triangles[nextTriangle:nextTriangle + triangleCount])
        nextTriangle += triangleCount

    return faces

def buildFaceSet(brep, vertexCoordinates):
    faceSet = FaceSet()
    
    faceCoordinateList = buildFaceCoordinates(brep)
    vertexValues = vertexCoordinates.point.getValues()

    for faceCoordinates in faceCoordinateList:
        faceSet.addFace(faceCoordinates, vertexValues)

    return faceSet


if __name__ == "__main__":
    rootNode = FreeCAD.ActiveDocument.Wall.ViewObject.RootNode
    switch = findSwitch(rootNode)
    brep = findBrepFaceset(switch)
    vertexCoordinates = findVertexCoordinates(rootNode)
    
    faceSet = buildFaceSet(brep, vertexCoordinates)
    faceSet.print()

    print(faceSet.calculateTextureCoordinates({'s': 1680, 't': 1440}))
