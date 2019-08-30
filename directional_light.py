import FreeCAD
import FreeCADGui
from pivy import coin
import light

class DirectionalLight(light.Light):
    def __init__(self, obj):
        super().__init__(obj)
    
    def setProperties(self, obj):
        super().setProperties(obj)
        
        self.type = 'DirectionalLight'
    
class ViewProviderDirectionalLight(light.ViewProviderLight):
    def __init__(self, vobj):
        super().__init__(vobj)

    def createLightInstance(self):
        return coin.SoDirectionalLight()

def createDirectionalLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DirectionalLight")
    light = DirectionalLight(obj)
    ViewProviderDirectionalLight(obj.ViewObject)


    return obj

if __name__ == "__main__":
    createDirectionalLight()