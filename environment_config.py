import FreeCAD, FreeCADGui
from pivy import coin
import math
import arch_texture_utils.py2_utils as py2_utils

GEOMETRY_COORDINATES = ['Radius', 'Length', 'Height']
TRANSFORM_PARAMETERS = ['ZOffset', 'Rotation']
ROTATION_VECTOR = coin.SbVec3f(0, 0, -1)

def noTexture(image):
    if image is None or image == '':
        return True
    
    return False

def containsNode(parent, node):
    childs = parent.getChildren()

    return node in childs

def addNode(parent, node):
    if not containsNode(parent, node):
        parent.addChild(node)

def removeNode(parent, node):
    if containsNode(parent, node):
        parent.removeChild(node)

class EnvironmentConfig():
    def __init__(self, obj):
        obj.Proxy = self

        self.isEnvironmentConfig = True

        obj.addProperty("App::PropertyLength", "Radius", "Geometry", "The Distance from the center of the coordinate system to the environment textures").Radius = 50000
        obj.addProperty("App::PropertyLength", "Length", "Geometry", "The overall Length of the environment panorama texture").Length = 150000
        obj.addProperty("App::PropertyLength", "Height", "Geometry", "The overall Height of the environment panorama texture").Height = 50000
        obj.addProperty("App::PropertyLength", "SkyOverlap", "Geometry", "The distance the sky overlaps with the panorama texture").SkyOverlap = 25000
        obj.addProperty("App::PropertyAngle", "Rotation", "Geometry", "The rotation for the environment").Rotation = 0
        obj.addProperty("App::PropertyDistance", "ZOffset", "Geometry", "The offset of the environment on the Z-Axis").ZOffset = -1
        
        obj.addProperty("App::PropertyFile", "PanoramaImage", "Texture", "The image of the panorama to show as environment texture").PanoramaImage = ''
        obj.addProperty("App::PropertyFile", "SkyImage", "Texture", "The image of the sky to show as environment texture").SkyImage = ''
        obj.addProperty("App::PropertyFile", "GroundImage", "Texture", "The image of the ground to show as environment texture").GroundImage = ''
    
    def execute(self, fp):
        pass
    
class ViewProviderEnvironmentConfig():
    def __init__(self, vobj):
        vobj.Proxy = self
    
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

        self.transformNode = coin.SoTransform()
        
        self.coinNode = coin.SoSeparator()
        self.coinNode.addChild(self.transformNode)

        self.panoramaNode = self.setupPanoramaNode()
        self.skyNode = self.setupSkyNode()
        self.groundNode = self.setupGroundNode()

        self.updatePanoramaCoordinates()
        self.updateSkyCoordinates()
        self.updateGroundCoordinates()

        self.updateTransformNode()
        self.updateNodeVisibility()

        vobj.addDisplayMode(self.coinNode, "Standard")
    
    def updateNodeVisibility(self):
        if noTexture(self.Object.PanoramaImage):
            removeNode(self.coinNode, self.panoramaNode)
        else:
            addNode(self.coinNode, self.panoramaNode)
        
        if noTexture(self.Object.SkyImage):
            removeNode(self.coinNode, self.skyNode)
        else:
            addNode(self.coinNode, self.skyNode)
        
        if noTexture(self.Object.GroundImage):
            removeNode(self.coinNode, self.groundNode)
        else:
            addNode(self.coinNode, self.groundNode)

    def updateTransformNode(self):
        rotation = math.radians(self.Object.Rotation.Value)
        translation = coin.SoSFVec3f()
        translation.setValue(coin.SbVec3f(0, 0, self.Object.ZOffset.Value))

        self.transformNode.rotation.setValue(ROTATION_VECTOR, rotation)
        self.transformNode.translation.setValue(translation)

    def setupPanoramaNode(self):
        panoramaNode = coin.SoSeparator()

        self.panoramaCoordinates = coin.SoCoordinate3()

        textureCoordinates = coin.SoTextureCoordinate2()

        oneThird = 1/3
        twoThirds = 2 * oneThird

        #left face
        textureCoordinates.point.set1Value(0, 0, 0)
        textureCoordinates.point.set1Value(1, oneThird, 0)
        textureCoordinates.point.set1Value(2, oneThird, 1)
        textureCoordinates.point.set1Value(3, 0, 1)
        
        textureCoordinates.point.set1Value(4, oneThird, 0)
        textureCoordinates.point.set1Value(5, twoThirds, 0)
        textureCoordinates.point.set1Value(6, twoThirds, 1)
        textureCoordinates.point.set1Value(7, oneThird, 1)

        textureCoordinates.point.set1Value(8, twoThirds, 0)
        textureCoordinates.point.set1Value(9, 1, 0)
        textureCoordinates.point.set1Value(10, 1, 1)
        textureCoordinates.point.set1Value(11, twoThirds, 1)

        self.panoramaTexture = coin.SoTexture2()
        self.panoramaTexture.filename = py2_utils.textureFileString(self.Object.PanoramaImage)
        self.panoramaTexture.model = coin.SoMultiTextureImageElement.REPLACE

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)
        faceset.numVertices.set1Value(1, 4)
        faceset.numVertices.set1Value(2, 4)

        panoramaNode.addChild(self.panoramaCoordinates)
        panoramaNode.addChild(textureCoordinates)
        panoramaNode.addChild(self.panoramaTexture)
        panoramaNode.addChild(faceset)

        return panoramaNode
    
    def setupSkyNode(self):
        skyNode = coin.SoSeparator()

        self.skyCoordinates = coin.SoCoordinate3()

        self.skyTexture = coin.SoTexture2()
        self.skyTexture.filename = py2_utils.textureFileString(self.Object.SkyImage)
        self.skyTexture.model = coin.SoMultiTextureImageElement.REPLACE

        self.skyTextureCoordinates = coin.SoTextureCoordinate2()

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)
        faceset.numVertices.set1Value(1, 4)
        faceset.numVertices.set1Value(2, 4)
        faceset.numVertices.set1Value(3, 4)
        faceset.numVertices.set1Value(4, 3)
        faceset.numVertices.set1Value(5, 4)

        skyNode.addChild(self.skyCoordinates)
        skyNode.addChild(self.skyTextureCoordinates)
        skyNode.addChild(self.skyTexture)
        skyNode.addChild(faceset)

        return skyNode
    
    def setupGroundNode(self):
        groundNode = coin.SoSeparator()

        self.groundCoordinates = coin.SoCoordinate3()

        self.groundTexture = coin.SoTexture2()
        self.groundTexture.filename = py2_utils.textureFileString(self.Object.GroundImage)
        self.groundTexture.model = coin.SoMultiTextureImageElement.REPLACE

        groundTextureCoordinates = coin.SoTextureCoordinate2()
        groundTextureCoordinates.point.set1Value(0, 0, 0)
        groundTextureCoordinates.point.set1Value(1, 1, 0)
        groundTextureCoordinates.point.set1Value(2, 1, 1)
        groundTextureCoordinates.point.set1Value(3, 0, 1)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)

        groundNode.addChild(self.groundCoordinates)
        groundNode.addChild(groundTextureCoordinates)
        groundNode.addChild(self.groundTexture)
        groundNode.addChild(faceset)

        return groundNode

    def calculateCoordinateBounds(self, radius, length):
        lengthThirds = length / 3 # the panorama consists of 3 planes

        alpha = self.calculateAlpha(radius, lengthThirds)
        connectionPointX = math.sin(alpha) * radius
        connectionPointY = math.cos(alpha) * radius

        leftX = -connectionPointX
        middleX = -connectionPointY
        rightX = middleX + lengthThirds
        
        backY = connectionPointX
        middleY = connectionPointY
        frontY = middleY - lengthThirds

        return (leftX, middleX, rightX, backY, middleY, frontY)

    def updatePanoramaCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value
        height = self.Object.Height.Value

        panoramaCoordinates = self.panoramaCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(radius, length)

        # left face of panorama
        panoramaCoordinates.point.set1Value(0, leftX, frontY, 0)
        panoramaCoordinates.point.set1Value(1, leftX, middleY, 0)
        panoramaCoordinates.point.set1Value(2, leftX, middleY, height)
        panoramaCoordinates.point.set1Value(3, leftX, frontY, height)

        # Center face of panorama
        panoramaCoordinates.point.set1Value(4, leftX, middleY, 0)
        panoramaCoordinates.point.set1Value(5, middleX, backY, 0)
        panoramaCoordinates.point.set1Value(6, middleX, backY, height)
        panoramaCoordinates.point.set1Value(7, leftX, middleY, height)

        # back face of panorama
        panoramaCoordinates.point.set1Value(8, middleX, backY, 0)
        panoramaCoordinates.point.set1Value(9, rightX, backY, 0)
        panoramaCoordinates.point.set1Value(10, rightX, backY, height)
        panoramaCoordinates.point.set1Value(11, middleX, backY, height)
    
    def updateSkyCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value
        height = self.Object.Height.Value
        skyOverlap = self.Object.SkyOverlap.Value
        skyOffset = 1000 # sky is 1 meter behind the panorama

        skyCoordinates = self.skyCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(radius + skyOffset, length + skyOffset)

        alpha = math.radians(45)
        a = leftX if leftX >= 0 else leftX * -1
        c = a / math.sin(alpha)
        topZOffset = a / math.tan(alpha)
        topZ = height + topZOffset

        self.fullSkyLength = skyOverlap + c
        
        # left face of sky
        skyCoordinates.point.set1Value(0, leftX, frontY, height - skyOverlap)
        skyCoordinates.point.set1Value(1, leftX, middleY, height - skyOverlap)
        skyCoordinates.point.set1Value(2, leftX, middleY, height)
        skyCoordinates.point.set1Value(3, leftX, frontY, height)

        # Center face of sky
        skyCoordinates.point.set1Value(4, leftX, middleY, height - skyOverlap)
        skyCoordinates.point.set1Value(5, middleX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(6, middleX, backY, height)
        skyCoordinates.point.set1Value(7, leftX, middleY, height)

        # back face of sky
        skyCoordinates.point.set1Value(8, middleX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(9, rightX, backY, height - skyOverlap)
        skyCoordinates.point.set1Value(10, rightX, backY, height)
        skyCoordinates.point.set1Value(11, middleX, backY, height)

        # left top face
        skyCoordinates.point.set1Value(12, leftX, frontY, height)
        skyCoordinates.point.set1Value(13, leftX, middleY, height)
        skyCoordinates.point.set1Value(14, 0, 0, topZ)
        skyCoordinates.point.set1Value(15, 0, frontY, topZ)

        # middle top face
        skyCoordinates.point.set1Value(16, leftX, middleY, height)
        skyCoordinates.point.set1Value(17, middleX, backY, height)
        skyCoordinates.point.set1Value(18, 0, 0, topZ)

        # back top face
        skyCoordinates.point.set1Value(19, middleX, backY, height)
        skyCoordinates.point.set1Value(20, rightX, backY, height)
        skyCoordinates.point.set1Value(21, rightX, 0, topZ)
        skyCoordinates.point.set1Value(22, 0, 0, topZ)

        self.updateSkyTextureCoordinates()
    
    def updateGroundCoordinates(self):
        radius = self.Object.Radius.Value
        length = self.Object.Length.Value

        groundCoordinates = self.groundCoordinates

        leftX, middleX, rightX, backY, middleY, frontY = self.calculateCoordinateBounds(radius, length)

        groundCoordinates.point.set1Value(0, leftX, frontY, 0)
        groundCoordinates.point.set1Value(1, rightX, frontY, 0)
        groundCoordinates.point.set1Value(2, rightX, backY, 0)
        groundCoordinates.point.set1Value(3, leftX, backY, 0)

    def calculateAlpha(self, radius, lengthThirds):
        # lets calculate alpha1. Then we only have to subtract it from 135 degrees and have our final alpha

        halfLength = lengthThirds / 2
        alpha1 = math.acos(halfLength / radius)
        alpha = math.radians(135) - alpha1

        return alpha

    def updateSkyTextureCoordinates(self):
        textureOverlapRatio = self.calculateSkyOverlapRatio()

        oneThird = 1/3
        twoThirds = oneThird * 2

        # left face
        self.skyTextureCoordinates.point.set1Value(0, 0, 0)
        self.skyTextureCoordinates.point.set1Value(1, oneThird, 0)
        self.skyTextureCoordinates.point.set1Value(2, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(3, 0, textureOverlapRatio)

        # middle face
        self.skyTextureCoordinates.point.set1Value(4, oneThird, 0)
        self.skyTextureCoordinates.point.set1Value(5, twoThirds, 0)
        self.skyTextureCoordinates.point.set1Value(6, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(7, oneThird, textureOverlapRatio)

        # back face
        self.skyTextureCoordinates.point.set1Value(8, twoThirds, 0)
        self.skyTextureCoordinates.point.set1Value(9, 1, 0)
        self.skyTextureCoordinates.point.set1Value(10, 1, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(11, twoThirds, textureOverlapRatio)

        # left top face
        self.skyTextureCoordinates.point.set1Value(12, 0, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(13, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(14, 0.5, 1)
        self.skyTextureCoordinates.point.set1Value(15, 0, 1)

        # middle top face
        self.skyTextureCoordinates.point.set1Value(16, oneThird, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(17, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(18, 0.5, 1)

        # # back top face
        self.skyTextureCoordinates.point.set1Value(19, twoThirds, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(20, 1, textureOverlapRatio)
        self.skyTextureCoordinates.point.set1Value(21, 1, 1)
        self.skyTextureCoordinates.point.set1Value(22, 0.5, 1)
    
    def calculateSkyOverlapRatio(self):
        return 1 / (self.fullSkyLength / self.Object.SkyOverlap.Value)

    def onChanged(self, vp, prop):
        pass
    
    def doubleClicked(self, vobj):
        pass

    def getDisplayModes(self,obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def updateData(self, fp, prop):
        if prop in GEOMETRY_COORDINATES:
            self.updatePanoramaCoordinates()
            self.updateSkyCoordinates()
            self.updateGroundCoordinates()
        elif prop in TRANSFORM_PARAMETERS:
            self.updateTransformNode()
        elif prop == 'PanoramaImage':
            self.panoramaTexture.filename = py2_utils.textureFileString(self.Object.PanoramaImage)
            self.updateNodeVisibility()
        elif prop == 'SkyImage':
            self.skyTexture.filename = py2_utils.textureFileString(self.Object.SkyImage)
            self.updateNodeVisibility()
        elif prop == 'GroundImage':
            self.groundTexture.filename = py2_utils.textureFileString(self.Object.GroundImage)
            self.updateNodeVisibility()
    
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def createEnvironmentConfig():
    environmentConfigObject = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "EnvironmentConfig")
    environmentConfig = EnvironmentConfig(environmentConfigObject)
    ViewProviderEnvironmentConfig(environmentConfigObject.ViewObject)

    return environmentConfigObject

if __name__ == "__main__":
    environmentConfigObject = createEnvironmentConfig()

    environmentConfigObject.PanoramaImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/Panorama_wood_transparency.png'
    environmentConfigObject.SkyImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/sky.jpg'
    environmentConfigObject.GroundImage = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/panorama/grass.jpg'
