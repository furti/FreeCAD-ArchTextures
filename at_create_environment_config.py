import FreeCAD, FreeCADGui

import environment_config
from arch_texture_utils.resource_utils import iconPath
import arch_texture_utils.qtutils as qtutils

class CreateEnvironmentConfigCommand:
    toolbarName = 'ArchTexture_Environment_Tools'
    commandName = 'Create_Environment_Config'

    def GetResources(self):
        return {'MenuText': "Create Environent Config",
                'ToolTip' : "Create a new EnvironmentConfig object to store environment textures",
                'Pixmap': iconPath('CreateEnvironmentConfig.svg')
                }

    def Activated(self):
        environment_config.createEnvironmentConfig()

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = CreateEnvironmentConfigCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(CreateEnvironmentConfigCommand()) 