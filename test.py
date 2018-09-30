import FreeCAD
import math
from os import path
from pivy import coin

filePath = path.join(path.dirname(path.realpath(__file__)), 'textures')
bricks = path.join(filePath, 'Bricks_Red.jpg')

tex = coin.SoTexture2()
tex.filename = bricks

transform = coin.SoTexture2Transform()
transform.rotation = math.radians(90)
#transform.scaleFactor = [0.8889, 0.8889]

print(bricks)

def textureObjects():
    for o in FreeCAD.ActiveDocument.Objects:
        if hasattr(o,'Shape'):
            if hasattr(o, 'IfcRole'):
                print 'got object %s' %(o)
                rootnode = o.ViewObject.RootNode
                rootnode.insertChild(transform, 1)
                rootnode.insertChild(tex, 1)


if __name__ == "__main__":
    textureObjects()
