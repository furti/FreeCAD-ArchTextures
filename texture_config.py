import FreeCAD, FreeCADGui
from pivy import coin

class TextureConfig():
    def __init__(self, obj):
        obj.Proxy = self
        # maybe add some properties later on
        # obj.addProperty("App::PropertyString","SomeProp","TextureConfig","Description").SomeProp=value
    
    def execute(self, fp):
        pass
    
    def __getstate__(self):
        '''Store the texture config inside the FreeCAD File'''
        return ()
    
    def __setstate__(self, state):
        '''Load the texture config from the FreeCAD File'''
        pass

class ViewProviderTextureConfig():
    def __init__(self, vobj):
        vobj.Proxy = self
    
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.TextureConfig = self.Object.Proxy

        self.coinNode = coin.SoGroup()
        vobj.addDisplayMode(self.coinNode, "Standard");
    
    def getDisplayModes(self,obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def updateData(self, fp, prop):
        pass

    def onChanged(self, vp, prop):
        pass

def createTextureConfig():
    textureConfigObject = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "TextureConfig")
    textureConfig = TextureConfig(textureConfigObject)
    ViewProviderTextureConfig(textureConfigObject.ViewObject)

if __name__ == "__main__":
    createTextureConfig()