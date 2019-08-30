import FreeCAD
import FreeCADGui
from pivy import coin
import light

class PointLight(light.Light):
    def __init__(self, obj):
        super().__init__(obj)
    
    def setProperties(self, obj):
        super().setProperties(obj)

        pl = obj.PropertiesList

        if not 'Location' in pl:
            obj.addProperty("App::PropertyVector", "Location", "Light",
                            "The position of the light in the scene.").Location = FreeCAD.Vector(0, -1, 0)
            
        
        self.type = 'PointLight'
    
class ViewProviderPointLight(light.ViewProviderLight):
    def __init__(self, vobj):
        super().__init__(vobj)
    
    def attach(self, vobj):
        super().attach(vobj)

        self.updateLocation()

    def createLightInstance(self):
        return coin.SoPointLight()
    
    def createGeometry(self):
        sphere = coin.SoSphere()
        sphere.radius.setValue(50.0)

        return sphere
    
def createPointLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "PointLight")
    light = PointLight(obj)
    ViewProviderPointLight(obj.ViewObject)


    return obj

if __name__ == "__main__":
    createPointLight()