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

        #rectangle
        coords.point.set1Value(0, 0, 0, 0)
        coords.point.set1Value(1, 10000, 0, 0)
        coords.point.set1Value(2, 10000, 0, 10000)
        coords.point.set1Value(3, 0, 0, 10000)

        #triangles
        coords.point.set1Value(4, 0, 0, 0)
        coords.point.set1Value(5, 0, 0, 10000)
        coords.point.set1Value(6, 5000, 5000, 5000)

        coords.point.set1Value(7, 0, 0, 0)
        coords.point.set1Value(8, 10000, 0, 0)
        coords.point.set1Value(9, 5000, 5000, 5000)

        coords.point.set1Value(10, 10000, 0, 0)
        coords.point.set1Value(12, 5000, 5000, 5000)
        coords.point.set1Value(11, 10000, 0, 10000)

        coords.point.set1Value(13, 10000, 0, 10000)
        coords.point.set1Value(14, 5000, 5000, 5000)
        coords.point.set1Value(15, 0, 0, 10000)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)
        faceset.numVertices.set1Value(1, 3)
        faceset.numVertices.set1Value(2, 3)
        faceset.numVertices.set1Value(3, 3)
        faceset.numVertices.set1Value(4, 3)

        node.addChild(coords)
        node.addChild(faceset)

        return node
    
    def updateGeometryDirection(self, rotation):
        location = rotation.multVec(FreeCAD.Vector(0, -100000, 0))
        # At first we set the location
        self.updateGeometryLocation(coin.SbVec3f(location.x, location.y, location.z))

        axis = rotation.Axis

        self.transform.rotation.setValue(coin.SbVec3f(axis.x, axis.y, axis.z), rotation.Angle)

def createDirectionalLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DirectionalLight")
    light = DirectionalLight(obj)
    ViewProviderDirectionalLight(obj.ViewObject)


    return obj

if __name__ == "__main__":
    createDirectionalLight()