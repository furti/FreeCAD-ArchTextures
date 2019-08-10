import FreeCAD, FreeCADGui

from arch_texture_utils.resource_utils import iconPath, uiPath
import arch_texture_utils.qtutils as qtutils
from arch_texture_utils.selection_utils import findSelectedTextureConfig, findSelectedFacesAsVectors
from arch_texture_utils.faceset_utils import vectorListEquals

class FaceConfigPanel():
    def __init__(self, textureConfig, freecadObject):
        self.textureConfig = textureConfig
        self.freecadObject = freecadObject
        self.faceOverrides = textureConfig.textureManager.ensureFaceOverrides()

        self.form = FreeCADGui.PySideUic.loadUi(uiPath('face_config.ui'))
        self.rotationBox = self.form.RotationBox

        self.form.ApplyButton.clicked.connect(self.apply)

    def apply(self):
        selectedFaces = findSelectedFacesAsVectors()

        if len(selectedFaces) == 0:
            qtutils.showInfo("No Face selected", "Select at least one face to apply the configuration")
        else:
            for objectName, vectors in selectedFaces:
                faceOverride = self.ensureOverrideForFace(objectName, vectors)
                
                faceOverride['rotation'] = self.rotationBox.value()
        
        self.textureConfig.execute(self.freecadObject)
    
    def reject(self):
        FreeCADGui.Control.closeDialog()
    
    def getStandardButtons(self):
        return int(qtutils.QDialogButtonBox.Close)
    
    def ensureOverrideForFace(self, objectName, vectors):
        existingOverride = None

        for override in self.faceOverrides:
            if override['objectName'] == objectName and vectorListEquals(override['vertices'], vectors):
                existingOverride = override

                break
        
        if existingOverride is None:
            existingOverride = {
                'vertices': vectors,
                'objectName': objectName
            }

            self.faceOverrides.append(existingOverride)
        
        return existingOverride

class ConfigureFacesCommand:
    toolbarName = 'ArchTexture_Tools'
    commandName = 'Configure_Faces'

    def GetResources(self):
        return {'MenuText': "Configure Faces",
                'ToolTip' : "Override default mapping parameters for individual faces",
                'Pixmap': iconPath('ConfigureFaces.svg')
                }

    def Activated(self):
        textureConfig = findSelectedTextureConfig(returnFreeCadObject=True)

        if textureConfig is None:
            qtutils.showInfo("No TextureConfig selected", "Select exactly one TextureConfig object to export its content")

            return
        
        panel = FaceConfigPanel(textureConfig.Proxy, textureConfig)
        FreeCADGui.Control.showDialog(panel)
        
    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ConfigureFacesCommand()
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(ConfigureFacesCommand()) 