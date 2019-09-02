import FreeCAD, FreeCADGui

import texture_config
from arch_texture_utils.resource_utils import iconPath

import point_light
import directional_light

class CreatePointLightCommand:
    toolbarName = 'Light_Tools'
    commandName = 'Create_PointLight'

    def GetResources(self):
        return {'MenuText': "Create Pointlight",
                'ToolTip' : "Create a new point light in the scene",
                'Pixmap': iconPath('CreatePointLight.svg')
                }

    def Activated(self):
        point_light.createPointLight()

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None

class CreateDirectionalLightCommand:
    toolbarName = 'Light_Tools'
    commandName = 'Create_DirectionalLight'

    def GetResources(self):
        return {'MenuText': "Create Directionallight",
                'ToolTip' : "Create a new Directional light in the scene",
                'Pixmap': iconPath('CreateDirectionalLight.svg')
                }

    def Activated(self):
        directional_light.createDirectionalLight()

    def IsActive(self):
        """If there is no active document we can't do anything."""
        return not FreeCAD.ActiveDocument is None


if __name__ == "__main__":
    command = CreatePointLightCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        import arch_texture_utils.qtutils as qtutils
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import archtexture_toolbars
    archtexture_toolbars.toolbarManager.registerCommand(CreatePointLightCommand())
    archtexture_toolbars.toolbarManager.registerCommand(CreateDirectionalLightCommand())