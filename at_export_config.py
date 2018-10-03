import FreeCAD, FreeCADGui

from arch_texture_utils.resource_utils import iconPath
import arch_texture_utils.qtutils as qtutils
from arch_texture_utils.selection_utils import findSelectedTextureConfig

class ExportTextureConfigCommand:
    toolbarName = 'ArchTexture_Tools'
    commandName = 'Export_Config'

    def GetResources(self):
        return {'MenuText': "Export Texture Config",
                'ToolTip' : "Exports the configuration stored inside a TextureConfig object to a file"
                #'Pixmap': iconPath('ImportImage.svg')
                }

    def Activated(self):
        textureConfig = findSelectedTextureConfig()

        if textureConfig is None:
            qtutils.showInfo("No TextureConfig selected", "Select exactly one TextureConfig object to export its content")

            return
        
        selectedFile = qtutils.userSelectedFile('Export Location', qtutils.JSON_FILES, False)

        if selectedFile is None:
            return
        
        fileObject = open(selectedFile, 'w')

        textureConfig.export(fileObject)

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ExportTextureConfigCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(ExportTextureConfigCommand()) 