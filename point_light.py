import FreeCAD
import FreeCADGui
from pivy import coin

import light
from arch_texture_utils.resource_utils import iconPath


class PointLight(light.Light):
    DEFAULT_RADIUS = 50.0
    DEFAULT_POWER = 60.0

    def __init__(self, obj):
        super().__init__(obj)

    def setProperties(self, obj):
        super().setProperties(obj)

        pl = obj.PropertiesList

        if not 'Location' in pl:
            obj.addProperty("App::PropertyVector", "Location", "Light",
                            "The position of the light in the scene.").Location = FreeCAD.Vector(0, -1, 0)

        if not 'Radius' in pl:
            obj.addProperty("App::PropertyLength", "Radius", "PointLight","The radius of the point light representation.")
            obj.Radius = PointLight.DEFAULT_RADIUS

        if not 'RenderingPower' in pl:
            obj.addProperty("App::PropertyFloat", "RenderingPower", "Light", "The power of the light for rendering.") # TODO Should be App::PropertyPower when this type is created
            obj.RenderingPower = PointLight.DEFAULT_POWER

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
        sphere.radius.setValue(PointLight.DEFAULT_RADIUS)
        return sphere

    def updateRadius(self):
        if hasattr(self,"actualGeometry") and hasattr(self.Object,"Radius"):
            self.actualGeometry.radius.setValue(float(self.Object.Radius))

    def updateData(self, fp, prop):
        if prop == 'Radius':
            self.updateRadius()
        else:
            super().updateData(fp,prop)

    def getIcon(self):
        return iconPath("PointLight.svg")

def createPointLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "PointLight")
    light = PointLight(obj)
    ViewProviderPointLight(obj.ViewObject)


    return obj

if __name__ == "__main__":
    createPointLight()
