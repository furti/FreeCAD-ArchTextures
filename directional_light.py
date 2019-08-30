import FreeCAD
import FreeCADGui
from pivy import coin
import light

class DirectionalLight(light.Light):
    def __init__(self, obj):
        super().__init__(obj)
    
    def setProperties(self, obj):
        super().setProperties(obj)

        pl = obj.PropertiesList
        
        if not 'HorizontalRotation' in pl:
            obj.addProperty("App::PropertyAngle", "HorizontalRotation", "Light",
                            "The horizontal rotation around the origin. Zero means a light pointing from south to north.").HorizontalRotation = 0
        
        if not 'VerticalRotation' in pl:
            obj.addProperty("App::PropertyAngle", "VerticalRotation", "Light", 
                            "The up and downward rotation").VerticalRotation = 45
                            
        self.type = 'DirectionalLight'
    
class ViewProviderDirectionalLight(light.ViewProviderLight):
    def __init__(self, vobj):
        super().__init__(vobj)

    def createLightInstance(self):
        return coin.SoDirectionalLight()
    
    def createGeometry(self):
        node = coin.SoSeparator()

        coords = coin.SoCoordinate3()
        coords.point.set1Value(0, 0, 0, 0)
        coords.point.set1Value(1, 50, 0, 0)
        coords.point.set1Value(2, 50, 50, 0)
        coords.point.set1Value(3, 0, 50, 0)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)

        node.addChild(coords)
        node.addChild(faceset)

        return node

def createDirectionalLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DirectionalLight")
    light = DirectionalLight(obj)
    ViewProviderDirectionalLight(obj.ViewObject)


    return obj

if __name__ == "__main__":
    createDirectionalLight()