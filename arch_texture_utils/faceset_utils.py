import FreeCAD, Part
import math
from functools import cmp_to_key
from pivy import coin
from itertools import groupby

DEBUG = True

globalX = FreeCAD.Vector(1, 0, 0)
globalY = FreeCAD.Vector(0, 1, 0)
globalZ = FreeCAD.Vector(0, 0, 1)

def toFreeCADVector(vector):
    return FreeCAD.Vector(vector[0], vector[1], vector[2])

def buildTriangle(vertices):
    v1 = vertices[0]['vector']
    v2 = vertices[1]['vector']
    v3 = vertices[2]['vector']

    e1 = Part.LineSegment(v1, v2)
    e2 = Part.LineSegment(v2, v3)
    e3 = Part.LineSegment(v3, v1)

    wire = Part.Wire([e1.toShape(), e2.toShape(), e3.toShape()])

    return Part.Face(wire)

def calculateNormal(face):
    uv = face.Surface.parameter(face.CenterOfMass)
    return face.normalAt(uv[0], uv[1])

def calculateTextureCoordinate(vector, boundingBox, scaleFactor, swapAxis=False):
    if swapAxis:
        vertexS = vector.z
        vertexT = vector.x

        sMax = boundingBox.ZMax
        tMax = boundingBox.XMax
    else:
        vertexS = vector.x
        vertexT = vector.z

        sMax = boundingBox.XMax
        tMax = boundingBox.ZMax
    
    scaleS = scaleFactor[0]
    scaleT = scaleFactor[1]

    s = vertexS / sMax
    t = vertexT / tMax

    return (s * scaleS, t * scaleT)

def extractOverrides(overrides):
    extractedOverrides = [None]

    if overrides is not None:
        if 'rotation' in overrides:
            # reverse the rotation. Because we rotate the face and not the image.
            # This means a positive face rotation will mean a negative image rotation
            # When reversing it we get the intended rotation
            extractedOverrides[0] = overrides['rotation'] * -1

    return tuple(extractedOverrides)

def vectorListEquals(vectors1, vectors2):
    if len(vectors1) != len(vectors2):
        return False
        
    for vector1 in vectors1:
        found = False
        
        for vector2 in vectors2:
            if vector1.isEqual(vector2, 0.01):
                found = True
                break
        
        if not found:
            return False
    
    return True

class Face():
    def __init__(self, faceCoordinates):
        self.faceCoordinates = faceCoordinates
        self.indices = []
        self.vertices = []
        self.originalVertices = []

        if DEBUG:
            self.atOriginVertices = []
            self.rotatedVertices = []
            self.positiveAxisVertices = []
            self.positiveTransform = None
    
    def getNumberOfVertices(self):
        return len(self.vertices)
    
    def addVertex(self, index, vect):
        if index not in self.indices:
            self.indices.append(index)

            self.originalVertices.append({
                'index': index,
                'vector': vect
            })
            
            self.vertices.append({
                'index': index,
                'vector': vect
            })

            self.length = 0
            self.height = 0
    
    def matches(self, vectors):
        ownVectors = [ownVertex['vector'] for ownVertex in self.originalVertices]

        return vectorListEquals(ownVectors, vectors)

    def calculateTextureCoordinates(self, realSize, vertexOffset):
        coordinates = []
        coordinateIndices = []

        axisSwapped = self.shouldSwapAxis(realSize)
        scaleFactor = self.calculateScaleFactor(realSize, axisSwapped)

        for vertex in self.vertices:
            s, t = calculateTextureCoordinate(vertex['vector'], self.boundingBox, scaleFactor, axisSwapped)
            coordinates.append((s, t))
            coordinateIndices.append(vertex['index'])

        faceCoordinateIndices = self.calculateFaceCoordinateIndices(coordinates, coordinateIndices, vertexOffset)

        return (coordinates, coordinateIndices, faceCoordinateIndices)
    
    def calculateFaceCoordinateIndices(self, coordinates, coordinateIndices, vertexOffset):
        '''
            The face stores a faceCoordiantes list that holds a list of vertex indices
            where each entry forms a triangle of the face
                faceCoordinates = [(0, 1, 2), (3, 2, 1)]
            
            The coordinates hold all the uv mapping coordinates for this face. One for each vertex
                coordinates = [(0,0), (0,1), (1, 1), (1,0)]
            
            The coordinateIndices map the coordinates to a vertex index.
                coordinateIndices = [1, 2, 3, 0]
            
            The vertexOffset is the offset of this faces vertexes in the global vertex list of the object this
            face belongs to. This is simply added to the indices in the result. Otherwhise the second face would
            also produces indices starting from zero, where it should produce indices starting from e.g. 4. 
                vertexOffset = 0
            
            In our example the coordinate (0,0) maps to the vertex 1, (0,1) to vertex 2, (1,1) to 3 and (1,0) to 0

            This method now builds uv coordinates for each triangle. To do so it looks up every faceCoordinate
            and maps the vertex index of the face coordinate to the uv coordinate in the coordinateIndices.
                result = [(3, 0, 1), (2, 1, 0)]
        '''
        faceCoordinateIndices = []

        for face in self.faceCoordinates:
            faceIndices = []

            for faceIndex in list(face):
                coordinateIndexLocation = coordinateIndices.index(faceIndex)

                faceIndices.append(coordinateIndexLocation + vertexOffset)
            
            faceCoordinateIndices.append(tuple(faceIndices))

        return faceCoordinateIndices
    
    def calculateScaleFactor(self, realSize, axisSwapped=False):
        tScale = 1
        sScale = 1

        if axisSwapped:
            s = self.height
            t = self.length
        else:
            s = self.length
            t = self.height

        if realSize is not None:
            realS = realSize['s']

            if realS > 0:
                sScale = s / realS
            
            realT = realSize['t']

            if realT > 0:
                tScale = t / realT

        return [sScale, tScale]
    
    def shouldSwapAxis(self, realSize):
        longestTextureAxis = 's'
        longestFaceAxis = 's'

        if realSize is not None:
            if realSize['t'] > realSize['s']:
                longestAxis = 't'
        
        if self.height > self.length:
            longestFaceAxis = 't'

        shouldSwap = longestTextureAxis != longestFaceAxis

        return shouldSwap
    
    def finishFace(self, overrides=None):
        # The first three vertices form the first triangle.
        # We use this information to get the normal and the offset from the origin
        # of the whole face

        if DEBUG:
            self.overrides = overrides

        # Calculations based on http://www.meshola.com/Articles/converting-between-coordinate-systems
        textureRotation, = extractOverrides(overrides)

        offsetVector = self.vertices[0]['vector']
        self.moveToOrigin(offsetVector)

        originTriangle = buildTriangle(self.vertices)
        matrix = self.calculateRotationMatrix(originTriangle)

        self.rotate(matrix)
        self.moveToPositiveAxis()

        self.boundingBox = self.calculateBoundBox()
        self.length = self.boundingBox.XLength
        self.height = self.boundingBox.ZLength

        if textureRotation is not None:
            self.rotateAroundYAxis(textureRotation)

    def normalizeTransform(self, transform):
        '''
        Lets say we have a object with a Vertex at (0,0,0) and a Placement of x=0,y=0,z=1000.
        Now when we select a face and check the vertices we get a point at (0,0,1000) because there is a placement applied.
        But in the Coin3D scene graph the vertex is still at (0,0,0) because FreeCAD applies a transform node with the translation of (0,0,1000). So the vertices are rendered at the right place, but we can't map selected faces to scene graph faces for face overrides anymore.
        To account for that we add the transform node to each vertex so we have the same values as FreeCAD.
        '''
        if transform is None:
            return
        
        translation = transform.translation.getValue().getValue()
        translationVector = FreeCAD.Vector(translation[0], translation[1], translation[2])

        for vertex in self.originalVertices:
            if DEBUG:
                self.positiveAxisVertices.append({
                    'index': vertex['index'],
                    'vector': vertex['vector']
                })

            v = vertex['vector']
            vertex['vector'] = v.add(translationVector)

    def rotateAroundYAxis(self, angle):
        rotation = FreeCAD.Rotation(globalY, angle)

        for vertex in self.vertices:
            if DEBUG:
                self.positiveAxisVertices.append({
                    'index': vertex['index'],
                    'vector': vertex['vector']
                })

            v = vertex['vector']
            vertex['vector'] = rotation.multVec(v)

    def calculateBoundBox(self):
        xValues = [vertex['vector'][0] for vertex in self.vertices]
        yValues = [vertex['vector'][1] for vertex in self.vertices]
        zValues = [vertex['vector'][2] for vertex in self.vertices]

        xMin = min(xValues)
        yMin = min(yValues)
        zMin = min(zValues)
        xMax = max(xValues)
        yMax = max(yValues)
        zMax = max(zValues)

        return FreeCAD.BoundBox(xMin, yMin, zMin, xMax, yMax, zMax)

    def moveToPositiveAxis(self):
        '''Move the face to the positive x and z values'''
        
        boundingBox = self.calculateBoundBox()

        xMin = boundingBox.XMin
        zMin = boundingBox.ZMin

        transformVector = FreeCAD.Vector()

        if xMin < 0:
            transformVector.x = xMin * -1
        
        if zMin < 0:
            transformVector.z = zMin * -1

        if transformVector.Length == 0:
            # No transformations needed
            return

        if DEBUG:
            self.positiveTransform = (xMin, zMin, transformVector)

        for vertex in self.vertices:
            if DEBUG:
                self.rotatedVertices.append({
                    'index': vertex['index'],
                    'vector': vertex['vector']
                })

            v = vertex['vector']
            vertex['vector'] = v.add(transformVector)

    def calculateRotationMatrix(self, triangle):
         # The face normal should point toward the front view
        localY = calculateNormal(triangle)
        # as the first point is now in the origin, find the second point.
        # Should not be the diagonal point of the triangle.
        localX = FreeCAD.Vector(self.findLocalXAxis())
        # last axis is the cross product of the other two
        localZ = localY.cross(localX)

        # normalize the vectors. Otherwise we will scale our rotated triangle.
        normalizedX = localX.normalize()
        normalizedY = localY.normalize()
        normalizedZ = localZ.normalize()

        return FreeCAD.Matrix(normalizedX.dot(globalX), normalizedX.dot(globalY), normalizedX.dot(globalZ), 0,
                              normalizedY.dot(globalX), normalizedY.dot(globalY), normalizedY.dot(globalZ), 0,
                              normalizedZ.dot(globalX), normalizedZ.dot(globalY), normalizedZ.dot(globalZ), 0,
                              0, 0, 0, 1)


    def moveToOrigin(self, offsetVector):
        '''To move the face to the origin we simply subtract the first vertex from every vertex.'''
        for vertex in self.vertices:
            v = vertex['vector']
            vertex['vector'] = v.sub(offsetVector)
    
    def rotate(self, matrix):
        for vertex in self.vertices:
            if DEBUG:
                self.atOriginVertices.append({
                    'index': vertex['index'],
                    'vector': vertex['vector']
                })

            v = vertex['vector']
            vertex['vector'] = matrix.multiply(v)
    
    def findLocalXAxis(self):
        origin = self.vertices[0]['vector']
        v1 = self.vertices[1]['vector']
        v2 = self.vertices[2]['vector']

        distanceToV1 = origin.distanceToPoint(v1)
        distanceToV2 = origin.distanceToPoint(v2)

        if distanceToV1 < distanceToV2:
            return v1
        
        return v2

    def printData(self, realSize=None):
        if DEBUG:
            print('   atOriginVertices:')
            for vertex in self.atOriginVertices:
                print('    %s' % (vertex, ))

            print('   rotatedVertices:')
            for vertex in self.rotatedVertices:
                print('    %s' % (vertex, ))
            
            print('   positiveAxisVertices:')
            for vertex in self.positiveAxisVertices:
                print('    %s' % (vertex, ))

            print('   vertices:')
            for vertex in self.vertices:
                print('    %s' % (vertex, ))
            
            print('    positiveTransform: %s' % (self.positiveTransform, ))
            print('    swapAxis: %s' % (self.shouldSwapAxis(realSize), ))
            print('    overrides: %s' % (self.overrides, ))

        textureCoords = coin.SoTextureCoordinate2()
        self.appendTextureCoordinates(textureCoords, realSize)

        normalizedCoords = coin.SoTextureCoordinate2()
        self.appendTextureCoordinates(normalizedCoords, None)

        print('   originalVertices:')
        for vertex in self.originalVertices:
            normalizedIndexCoords = normalizedCoords.point.getValues()[vertex['index']].getValue()
            indexCoords = textureCoords.point.getValues()[vertex['index']].getValue()

            print('    %s' % ({
                'index': vertex['index'],
                'vector': vertex['vector'],
                'normalizedCoords': normalizedIndexCoords,
                'coords': indexCoords
            }, ))
 
        print('    length: %s, height: %s' % (self.length, self.height))
        print('    scaleFactor: %s' % (self.calculateScaleFactor(realSize), ))
        print('    textureRotation: %s' % (self.calculateScaleFactor(realSize), ))

class FaceSet():
    def __init__(self):
        self.faces = []
    
    def addFace(self, faceCoordinates, vertices, faceOverrides=None, transform=None):
        '''
        Add a face to the faceset

        faceCoordinates: a list of faces of the object. Each face is a list of tuples where a tuple is a triangle. [[(0, 1, 2), (1, 2, 3)], ...
        vertices: a list of all vertices of the object
        '''
        face = Face(faceCoordinates)

        for coordinate in faceCoordinates:
            for index in coordinate:
                face.addVertex(index, vertices[index])
        

        face.normalizeTransform(transform)
        face.finishFace(findOverridesForFace(face, faceOverrides))

        self.faces.append(face)
    
    def calculateSoTextureCoordinates(self, realSize):
        soTextureCoordinates = coin.SoTextureCoordinate2()

        coordinateData = self.calculateTextureCoordinates(realSize)

        textureCoordinates = coordinateData[0]
        textureCoordinateIndices = coordinateData[1]

        for listIndex, coordinate in enumerate(textureCoordinates):
            coordinateIndex = textureCoordinateIndices[listIndex]
            s, t = coordinate

            soTextureCoordinates.point.set1Value(coordinateIndex, s, t)

        return soTextureCoordinates
    
    def calculateTextureCoordinates(self, realSize):
        textureCoordinates = []
        textureCoordinateIndices = []
        textureFaceCoordinateIndices = []

        vertexOffset = 0

        for face in self.faces:
            coordinateData = face.calculateTextureCoordinates(realSize, vertexOffset)

            coordinates = coordinateData[0]
            coordinateIndices = coordinateData[1]
            faceCoordinateIndices = coordinateData[2]

            textureCoordinates.extend(coordinates)
            textureCoordinateIndices.extend(coordinateIndices)
            textureFaceCoordinateIndices.extend(faceCoordinateIndices)

            vertexOffset += face.getNumberOfVertices()

        return (textureCoordinates, textureCoordinateIndices, textureFaceCoordinateIndices)
    
    def printData(self, realSize=None, faceNumber=None):
        if faceNumber is not None:
            print('Face:')
            self.faces[faceNumber].printData(realSize)
        else:
            for face in self.faces:
                print('Face:')
                face.printData(realSize)
    
def findVertexCoordinates(node):
     for child in node.getChildren():
        if child.getTypeId().getName() == 'Coordinate3':
            return child

def findSwitch(node):
    for child in node.getChildren():
        if child.getTypeId().getName() == 'Switch':
            return child

def findShadedNode(node):
    children = node.getChildren()

    if children is None or children.getLength() == 0:
        return None
    
    for child in children:
        if child.getTypeId().getName() == 'SoBrepFaceSet':
            return node
        
        shadedNode = findShadedNode(child)

        if shadedNode is not None:
            return shadedNode

def findBrepFaceset(node):
    children = node.getChildren()

    if children is None or children.getLength() == 0:
        return None
    
    for child in children:
        if child.getTypeId().getName() == 'SoBrepFaceSet':
            return child
    
    return None

def findMaterial(node):
    children = node.getChildren()

    if children is None or children.getLength() == 0:
        return None
    
    for child in children:
        if child.getTypeId().getName() == 'Material':
            return child
    
    return None

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

def findOverridesForFace(face, faceOverrides=None):
    if faceOverrides is None:
        return  None
    
    for faceOverride in faceOverrides:
        if face.matches(faceOverride['vertices']):
            return faceOverride
    
    return None

def buildFaceSet(brep, vertexCoordinates, faceOverrides=None, transform=None):
    faceSet = FaceSet()
    
    faceCoordinateList = buildFaceCoordinates(brep)
    vertexValues = [toFreeCADVector(vertex.getValue()) for vertex in vertexCoordinates.point.getValues()]

    for faceCoordinates in faceCoordinateList:
        faceSet.addFace(faceCoordinates, vertexValues, faceOverrides, transform)

    return faceSet

def buildFaceSetForMesh(mesh, faceOverrides=None):
    faceSet = FaceSet()

    vertexValues = mesh.Topology[0]
    faceCoordinateList = groupFacetsByNormal(mesh.Facets)

    for faceCoordinates in faceCoordinateList:
        faceSet.addFace(faceCoordinates, vertexValues, faceOverrides)

    return faceSet

def groupFacetsByNormal(facets):
    groupsWithNormals = []

    for facet in facets:
        group = findFacetGroup(groupsWithNormals, facet)

        if group is None:
            group = []

            groupsWithNormals.append((FreeCAD.Vector(facet.Normal), group))
        
        group.append(facet.PointIndices)

    return [group[1] for group in groupsWithNormals]

def findFacetGroup(groupsWithNormals, facet):
    for group in groupsWithNormals:
        if group[0].isEqual(facet.Normal, 0.0001):
            return group[1]

    return None

def findTransform(node):
    children = node.getChildren()

    if children is None or children.getLength() == 0:
        return None
    
    for child in children:
        if child.getTypeId().getName() == 'Transform':
            return child
    
    return None

if __name__ == "__main__":
    def printValues(l):
        values = []

        for index, e in enumerate(l):
            print('%s: %s' % (index, e.getValue()))
    
    testOverrides = [
        {
            'objectName': 'Wall',
            'vertices': [
                FreeCAD.Vector(-4100.0, -100.00000000000026, 0.0),
                FreeCAD.Vector(-4100.0, -100.00000000000026, 500.0),
                FreeCAD.Vector(-4100.0, 99.99999999999974, 0.0),
                FreeCAD.Vector(-4100.0, 99.99999999999974, 500.0)
            ],
            'rotation': 90
        },
        {
            'objectName': 'Roof',
            'rotation': 20.0,
            'vertices': [
                FreeCAD.Vector(4100.0, 5100.0, 2970.7106781186544),
                FreeCAD.Vector(2000.0, 3000.0, 5070.710678118655),
                FreeCAD.Vector(4100.0, -99.99999999999955, 2970.7106781186544),
                FreeCAD.Vector(2000.0, 2000.0, 5070.710678118654),
                FreeCAD.Vector(1999.9999999999998, 2500.0, 5070.710678118654)
            ]
        }
    ]
    
    # rootNode = FreeCAD.ActiveDocument.Roof.ViewObject.RootNode
    # switch = findSwitch(rootNode)
    # shadedNode = findShadedNode(switch)
    # brep = findBrepFaceset(shadedNode)
    # vertexCoordinates = findVertexCoordinates(rootNode)
    # transform = findTransform(rootNode)

    # faceSet = buildFaceSet(brep, vertexCoordinates, testOverrides, transform)
    # faceSet.printData({'s': 1680, 't': 1440})
    # # printValues(textureCoords.point.getValues())

    import MeshPart
    box = FreeCAD.ActiveDocument.Box
    
    mesh = MeshPart.meshFromShape(Shape=box.Shape,
                                    LinearDeflection=0.1,
                                    AngularDeflection=0.523599,
                                    Relative=False)

    faceSet = buildFaceSetForMesh(mesh)
    print(faceSet.calculateTextureCoordinates(None))
    print(faceSet.calculateSoTextureCoordinates(None))