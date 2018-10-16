import FreeCAD
from pivy import coin
from itertools import groupby

def deletePlane():
    activeDoc = FreeCAD.ActiveDocument

    if hasattr(activeDoc, 'Rectangle'):
        activeDoc.removeObject(activeDoc.Rectangle.Label)

def createPlane():
    pl = FreeCAD.Placement()
    pl.Rotation.Q = (0.7071067811865475,-2.164890140588733e-17,0.0,0.7071067811865476)
    pl.Base = FreeCAD.Vector(0.0,0.0,0.0)
    rec = Draft.makeRectangle(length=1000.0000000000001,height=1000.0000000000001,placement=pl,face=True,support=None)
    Draft.autogroup(rec)

def setupTextureCoordinateIndex(brep):
    coordinateIndex = brep.coordIndex.getValues()

    brep.textureCoordIndex.setValues(0, len(coordinateIndex), coordinateIndex)

def buildTextureCoords():
    textureCoords = coin.SoTextureCoordinate2()

    textureCoords.point.set1Value(0, 0, 0)
    textureCoords.point.set1Value(1, 1, 0)
    textureCoords.point.set1Value(2, 1, 1)
    textureCoords.point.set1Value(3, 0, 1)

    textureCoords.point.set1Value(4, 0, 1)
    textureCoords.point.set1Value(5, 0, 0)
    textureCoords.point.set1Value(6, 1, 0)
    textureCoords.point.set1Value(7, 1, 1)

    return textureCoords

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
            return (child, node)
        
        brep = findBrepFaceset(child)

        if brep is not None:
            return brep

def buildTexture():
    tex = coin.SoTexture2()
    tex.filename = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/Bricks_Brown/Bricks_Brown_Albedo.tif'
    # tex.model = coin.SoMultiTextureImageElement.REPLACE

    return tex

def buildBumpMap():
    bumpMap = coin.SoBumpMap()
    bumpMap.filename = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/Bricks_Brown/Bricks_Brown_normal.tif'

    return bumpMap

def buildBumpMapTexture():
    tex = coin.SoTexture2()
    tex.filename = 'C:/Meine Daten/freecad/workbenches/FreeCAD-ArchTextures/textures/Bricks_Brown/Bricks_Brown_normal.tif'
    # tex.model = coin.SoMultiTextureImageElement.REPLACE

    return tex

def buildBumpMapCoords():
    coords = coin.SoBumpMapCoordinate()

    coords.point.set1Value(0, 0, 0)
    coords.point.set1Value(1, 1, 0)
    coords.point.set1Value(2, 1, 1)
    coords.point.set1Value(3, 0, 1)

    coords.point.set1Value(4, 0, 1)
    coords.point.set1Value(5, 0, 0)
    coords.point.set1Value(6, 1, 0)
    coords.point.set1Value(7, 1, 1)

    return coords

class TestObject():
    def __init__(self, obj):
        obj.Proxy = self

class ViewProviderTestObject():
    def __init__(self, vobj):
        vobj.Proxy = self
    
    def attach(self, vobj):
        self.imageNode = coin.SoSeparator()

        self.coords = coin.SoCoordinate3()
        self.coords.point.set1Value(0, 0, 0, 0)
        self.coords.point.set1Value(1, 1000, 0, 0)
        self.coords.point.set1Value(2, 1000, 1000, 0)
        self.coords.point.set1Value(3, 0, 1000, 0)

        textureCoords = coin.SoTextureCoordinate2()
        textureCoords.point.set1Value(0, 0, 0)
        textureCoords.point.set1Value(1, 1, 0)
        textureCoords.point.set1Value(2, 1, 1)
        textureCoords.point.set1Value(3, 0, 1)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)

        texture = buildTexture()
        bumpMap = buildBumpMap()
        bumpMapTexture = buildBumpMapTexture()

        textureUnit = coin.SoTextureUnit()
        textureUnit.value = 0
        textureUnit.mapMethod = coin.SoTextureUnit.BUMP_MAPPING

        self.imageNode.addChild(self.coords)
        self.imageNode.addChild(textureUnit)
        self.imageNode.addChild(textureCoords)
        self.imageNode.addChild(bumpMapTexture)
        # self.imageNode.addChild(texture)
        self.imageNode.addChild(faceset)

        vobj.addDisplayMode(self.imageNode, "Image")
    
    def getDisplayModes(self,obj):
        return ["Image"]

    def getDefaultDisplayMode(self):
        return "Image"

if __name__ == '__main__':
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython")
    image = TestObject(a)
    ViewProviderTestObject(a.ViewObject)

    # deletePlane()
    # createPlane()

    # rectangle = FreeCAD.ActiveDocument.Rectangle
    # rootNode = rectangle.ViewObject.RootNode

    # switch = findSwitch(rootNode)
    # brep, shaded = findBrepFaceset(switch)

    # setupTextureCoordinateIndex(brep)

    # textureCoords = buildTextureCoords()
    # texture = buildTexture()

    # bumpMap = buildBumpMap()
    # bumpMapCoordinates = buildBumpMapCoords()


    
    # shaded.insertChild(bumpMap, 1)
    # shaded.insertChild(texture, 1)
    # shaded.insertChild(textureCoords, 1)
    # shaded.insertChild(bumpMapCoordinates, 1)
    