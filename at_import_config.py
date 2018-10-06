import FreeCAD, FreeCADGui

import texture_config
from arch_texture_utils.resource_utils import iconPath
import arch_texture_utils.qtutils as qtutils

class ImportTextureConfigCommand:
    toolbarName = 'ArchTexture_Tools'
    commandName = 'Import_Config'

    def GetResources(self):
        return {'MenuText': "Import Texture Config",
                'ToolTip' : "Import a new TextureConfig object from a JSOn File",
                'Pixmap': iconPath('ImportConfig.svg')
                }

    def Activated(self):
        selectedFile = qtutils.userSelectedFile('Config File', qtutils.JSON_FILES)

        if selectedFile is None:
            return
        
        fileObject = open(selectedFile, 'r')

        texture_config.createTextureConfig(fileObject)

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ImportTextureConfigCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(ImportTextureConfigCommand()) 