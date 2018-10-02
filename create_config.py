import FreeCAD, FreeCADGui

import texture_config
from arch_texture_utils.resource_utils import iconPath
import arch_texture_utils.qtutils as qtutils

class CreateTextureConfigCommand:
    toolbarName = 'ArchTexture_Tools'
    commandName = 'Create_Config'

    def GetResources(self):
        return {'MenuText': "Create Texture Config",
                'ToolTip' : "Create a new TextureConfig object to store Textures"
                #'Pixmap': iconPath('ImportImage.svg')
                }

    def Activated(self):
        texture_config.createTextureConfig()

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = CreateTextureConfigCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(CreateTextureConfigCommand()) 