import FreeCAD
import FreeCADGui
from pivy import coin

import arch_texture_utils.faceset_utils as faceset_utils

class Light():
    def __init__(self, obj):
        obj.Proxy = self

        self.setProperties(obj)
    
    def setProperties(self, obj):
        pl = obj.PropertiesList

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

        self.setProperties(vobj)
 
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

        # Setting properties does not work here as the pl is not filled yet :/

        sceneGraph = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()

        self.switch = coin.SoSwitch()
        self.geometryNode = coin.SoSeparator()
        self.transform = coin.SoTransform()
        self.material = coin.SoMaterial()
        self.coinLight = self.createLightInstance()
        actualGeometry = self.createGeometry()

        self.geometryNode.addChild(self.transform)
        self.geometryNode.addChild(self.material)

        if actualGeometry is not None:
            self.geometryNode.addChild(actualGeometry)
        
        sceneGraph.insertChild(self.coinLight, 1)

        self.switch.addChild(self.geometryNode)

        vobj.addDisplayMode(self.switch, "Light")

        self.updateLightVisibility()
        self.updateDirection()
        self.updateColor()
        self.updateIntensity()
        # self.updateGeometryVisibility()
    
    def setProperties(self, vobj):
        pl = vobj.PropertiesList

        if not 'ShowGeometry' in pl:
            vobj.addProperty("App::PropertyBool", "ShowGeometry", "Light", 
                            "Show the light as geometry in the 3D View").ShowGeometry = True

    def createLightInstance(self):
        raise NotImplementedError()
    
    def createGeometry(self):
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
        elif prop == 'Location':
            self.updateLocation()
 
    def onChanged(self, vp, prop):
        if prop == 'Visibility':
            self.updateLightVisibility()
        elif prop == 'ShowGeometry':
            self.updateGeometryVisibility()

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
    
    def updateLocation(self):
        if hasattr(self.Object, 'Location'):
            location = self.Object.Location
            coinVector = coin.SbVec3f(location.x, location.y, location.z)

            self.coinLight.location.setValue(coinVector)

            self.updateGeometryLocation(coinVector)
    
    def updateDirection(self):
        if hasattr(self.Object, 'HorizontalRotation') and hasattr(self.Object, 'VerticalRotation'):
            horizontalRotation = self.Object.HorizontalRotation
            verticalRotation = self.Object.VerticalRotation

            # Defaults to south to north
            direction = FreeCAD.Vector(0, 1, 0)

            # Negative Z because we want the light to follow the real sun path from East to west.
            rotateZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, -1), horizontalRotation)

            # Negative X because a positive rotation should let the light point downwards
            rotateX = FreeCAD.Rotation(FreeCAD.Vector(-1, 0, 0), verticalRotation)

            rotation = rotateZ.multiply(rotateX)

            direction = rotateZ.multVec(direction)
            direction = rotateX.multVec(direction)

            coinVector = coin.SbVec3f(direction.x, direction.y, direction.z)

            self.coinLight.direction.setValue(coinVector)

            self.updateGeometryDirection(rotation)

            #print('h: %s, v: %s, d: %s' % (horizontalRotation, verticalRotation, direction))
    
    def updateLightVisibility(self):
        self.coinLight.on.setValue(self.ViewObject.Visibility)
    
    def updateColor(self):
        color = self.Object.Color

        r = color[0]
        g = color[1]
        b = color[2]

        coinColor = coin.SbColor(r, g, b)

        self.coinLight.color.setValue(coinColor)
        self.material.diffuseColor.setValue(coinColor)
    
    def updateIntensity(self):
        self.coinLight.intensity.setValue(self.Object.Intensity)
    
    def updateGeometryLocation(self, coinVector):
        self.transform.translation.setValue(coinVector)
    
    def updateGeometryDirection(self, rotation):
        # Nothing to do right now. Subclasses override this
        pass
    
    def updateGeometryVisibility(self):
        if not hasattr(self, 'switch') or self.switch is None:
            return
        
        if self.ViewObject.ShowGeometry:
            self.switch.whichChild.setValue(0)
        else:
            self.switch.whichChild.setValue(coin.SO_SWITCH_NONE)

def createDirectionalLight():
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "DirectionalLight")
    light = DirectionalLight(obj)
    ViewProviderDirectionalLight(obj.ViewObject)

    return obj

if __name__ == "__main__":
    createDirectionalLight()