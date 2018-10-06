import FreeCAD
import math
from os import path
from pivy import coin
from itertools import groupby

filePath = path.join(path.dirname(path.realpath(__file__)), 'textures')
bricks = path.join(filePath, 'Bricks_Red.jpg')

tex = coin.SoTexture2()
tex.filename = bricks

transform = coin.SoTexture2Transform()
transform.rotation = math.radians(90)
#transform.scaleFactor = [0.8889, 0.8889]

# print(bricks)

# def textureObjects():
#     for o in FreeCAD.ActiveDocument.Objects:
#         if hasattr(o,'Shape'):
#             if hasattr(o, 'IfcRole'):
#                 print 'got object %s' %(o)
#                 rootnode = o.ViewObject.RootNode
#                 rootnode.insertChild(transform, 1)
#                 rootnode.insertChild(tex, 1)

class Face():
    def __init__(self):
        self.vertices = {}
    
    def addVertex(self, index, vect):
        self.vertices[index] = (index, vect.getValue())
    
    def print(self):
        for index, vertex in self.vertices.items():
            print('    %s:%s' % (index, vertex))

class FaceSet():
    def __init__(self):
        self.faces = []
    
    def addFace(self, faceCoordinates, vertices):
        face = Face()

        for coordinate in faceCoordinates:
            for index in coordinate:
                face.addVertex(index, vertices[index])
        
        self.faces.append(face)
    
    def print(self):
        for face in self.faces:
            print('Face:')
            face.print()
    
def printData():
    rootNode = FreeCAD.ActiveDocument.Wall.ViewObject.RootNode
    switch = findSwitch(rootNode)
    brep = findBrepFaceset(switch)
    vertexCoordinates = findVertexCoordinates(rootNode)

    print('brep: %s' % (brep.textureCoordIndex.getValues()))

    faceCoordinates = buildFaceCoordinates(brep)
    faceSet = buildFaceSet(faceCoordinates, vertexCoordinates)
    faceSet.print()

    # print(dir(brep.coordIndex))
    # print(len(brep.coordIndex))
    # printValues(brep.coordIndex)

    # print('partIndex')
    # printValues(brep.partIndex)

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

def buildFaceSet(faceCoordinateList, vertexCoordinates):
    faceSet = FaceSet()
    vertexValues = vertexCoordinates.point.getValues()

    for faceCoordinates in faceCoordinateList:
        faceSet.addFace(faceCoordinates, vertexValues)

    return faceSet

if __name__ == "__main__":
    # textureObjects()
    printData()
