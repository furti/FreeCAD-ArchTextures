import FreeCAD, FreeCADGui

class ArchTextureWorkbench (FreeCADGui.Workbench):
    "Texture Architectural objects in FreeCAD"

    MenuText = "Arch Texture"
    ToolTip = "Texture architectural objects"

    def __init__(self):
        from arch_texture_utils.resource_utils import iconPath
        self.__class__.Icon = iconPath("Workbench.svg")
        

    def Initialize(self):
        pass
        # Initialize the module
        import archtexture_toolbars

        for name,commands in archtexture_toolbars.toolbarManager.Toolbars.items():
            self.appendToolbar(name,[command.commandName for command in commands])

#    def Activated(self):

#   def Deactivated(self):

FreeCADGui.addWorkbench(ArchTextureWorkbench())