import FreeCAD
from os import path

resources_path = path.join(path.dirname(path.realpath(__file__)), '..', 'Resources')
icons_path = path.join(resources_path, 'Icons')
ui_path = path.join(resources_path, 'UI')

FreeCAD.Console.PrintMessage(resources_path)

def iconPath(name):
    f = path.join(icons_path, name)

    return f

def uiPath(name):
    f = path.join(ui_path, name)

    return f