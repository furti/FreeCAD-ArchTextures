import FreeCAD
import FreeCADGui
from pivy import coin

class Light():
    def __init__(self, obj):
        obj.Proxy = self

        self.setProperties(obj)
    
    def setProperties(self, obj):
        pl = obj.PropertiesList

        if not 'HorizontalRotation' in pl:
            obj.addProperty("App::PropertyAngle", "HorizontalRotation", "Light",
                            "The horizontal rotation around the origin. Zero means a light pointing from south to north.").HorizontalRotation = 0
        
        if not 'VerticalRotation' in pl:
            obj.addProperty("App::PropertyAngle", "VerticalRotation", "Light", 
                            "The up and downward rotation").VerticalRotation = 45
        
        if not 'Color' in pl:
            obj.addProperty("App::PropertyColor", "Color", "Light", 
                            "The color of the light").Color = (1.0, 0.94, 0.91)
        
        if not 'Intensity' in pl:
            obj.addProperty("App::PropertyFloatConstraint", "Intensity", "Light", 
                            "The intensity of the light").Intensity = (1.0, 0.0, 1.0, 0.1)



    def onDocumentRestored(self, obj):
        self.setProperties(obj)

    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None

    def execute(self, ob):
        pass
    
class ViewProviderLight:
    def __init__(self, vobj):
        vobj.Proxy = self
 
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        
        sceneGraph = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()

        self.geometryNode = coin.SoSeparator()
        
        self.coinLight = self.createLightInstance()
        sceneGraph.insertChild(self.coinLight, 1)

        # self.coords = coin.SoCoordinate3()
        # self.coords.point.set1Value(0, 0, 0, -1)
        # self.coords.point.set1Value(1, 1, 0, -1)
        # self.coords.point.set1Value(2, 1, 1, -1)
        # self.coords.point.set1Value(3, 0, 1, -1)

        # textureCoords = coin.SoTextureCoordinate2()
        # textureCoords.point.set1Value(0, 0, 0)
        # textureCoords.point.set1Value(1, 1, 0)
        # textureCoords.point.set1Value(2, 1, 1)
        # textureCoords.point.set1Value(3, 0, 1)

        # faceset = coin.SoFaceSet()
        # faceset.numVertices.set1Value(0, 4)

        # # This makes it possible to select the object in the 3D View
        # selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        # selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        # selectionNode.objectName.setValue(self.Object.Name)
        # selectionNode.subElementName.setValue("Face")
        # selectionNode.addChild(faceset)

        # self.texture = coin.SoTexture2()

        # self.imageNode.addChild(self.coords)
        # self.imageNode.addChild(textureCoords)
        # self.imageNode.addChild(self.texture)
        # self.imageNode.addChild(selectionNode)

        vobj.addDisplayMode(self.geometryNode, "Light")

        self.updateLightVisibility()
        self.updateDirection()
        self.updateColor()
        self.updateIntensity()

    def createLightInstance(self):
        raise NotImplementedError()

    def getDisplayModes(self,obj):
        '''Return a list of display modes.'''
        
        return ["Light"]
 
    def getDefaultDisplayMode(self):
        '''Return the name of the default display mode. It must be defined in getDisplayModes.'''
       
        return "Light"

    def updateData(self, fp, prop):
        if prop in ['HorizontalRotation', 'VerticalRotation']:
            self.updateDirection()
        elif prop == 'Color':
            self.updateColor()
        elif prop == 'Intensity':
            self.updateIntensity()
 
    def onChanged(self, vp, prop):
        if prop == 'Visibility':
            self.updateLightVisibility()

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
    
    def updateDirection(self):
        horizontalRotation = self.Object.HorizontalRotation
        verticalRotation = self.Object.VerticalRotation

        # Defaults to south to north
        direction = FreeCAD.Vector(0, 1, 0)

        # Negative Z because we want the light to follow the real sun path from East to west.
        rotateZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, -1), horizontalRotation)

        # Negative X because a positive rotation should let the light point downwards
        rotateX = FreeCAD.Rotation(FreeCAD.Vector(-1, 0, 0), verticalRotation)

        direction = rotateZ.multVec(direction)
        direction = rotateX.multVec(direction)

        self.coinLight.direction.setValue(coin.SbVec3f(direction.x, direction.y, direction.z))

        #print('h: %s, v: %s, d: %s' % (horizontalRotation, verticalRotation, direction))
    
    def updateLightVisibility(self):
        self.coinLight.on.setValue(self.ViewObject.Visibility)
    
    def updateColor(self):
        color = self.Object.Color

        r = color[0]
        g = color[1]
        b = color[2]

        self.coinLight.color.setValue(coin.SbColor(r, g, b))
    
    def updateIntensity(self):
        self.coinLight.intensity.setValue(self.Object.Intensity)

 

def createDirectionalLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DirectionalLight")
    light = DirectionalLight(obj)
    ViewProviderDirectionalLight(obj.ViewObject)

    return obj

if __name__ == "__main__":
    createDirectionalLight()