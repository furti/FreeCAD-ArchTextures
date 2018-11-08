from collections import OrderedDict
import FreeCAD, FreeCADGui

class ArchTextureToolbarManager:
    Toolbars =  OrderedDict()

    def registerCommand(self, command):
        FreeCADGui.addCommand(command.commandName, command)
        self.Toolbars.setdefault(command.toolbarName, []).append(command)

toolbarManager = ArchTextureToolbarManager()

# import commands here
import create_config
import at_export_config
import at_import_config
import at_configure_faces
import at_create_environment_config