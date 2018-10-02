import FreeCAD
import math
from pivy import coin

class TextureManager():
    def __init__(self):
        self.textureData = {
            'materials': {
            #     '<mat_name>': {
            #         'file': 'path_to_texture'
            #     }
            }
        }

        self.textureCache = {
            # '<file_name>': texture
        }

        self.texturedObjects = [
            #(object, (texture, transform), (originalTransparency, originalShapeColor))
        ]
    
    def textureObjects(self):
        FreeCAD.Console.PrintMessage('Texturing objects\n')

        for o in FreeCAD.ActiveDocument.Objects:
            if hasattr(o,'Shape'):
                if hasattr(o, 'Material') and o.Material is not None:
                    texture = self.getTextureForMaterial(o.Material)

                    if texture is not None:
                        originalTransparency = o.ViewObject.Transparency
                        originalShapeColor = o.ViewObject.ShapeColor

                        o.ViewObject.Transparency = 0
                        o.ViewObject.ShapeColor = (1.0, 1.0, 1.0)

                        texTransform = coin.SoTexture2Transform()
                        texTransform.rotation = math.radians(90)
                        
                        rootnode = o.ViewObject.RootNode
                        rootnode.insertChild(texture, 1)
                        rootnode.insertChild(texTransform, 1)


                        self.texturedObjects.append((o, (texture, texTransform), (originalTransparency, originalShapeColor)))


    
    def removeTextures(self):
        FreeCAD.Console.PrintMessage('Removing Textures\n')

        for o, coinData, originalViewData in self.texturedObjects:
            o.ViewObject.RootNode.removeChild(coinData[0])
            o.ViewObject.RootNode.removeChild(coinData[1])
            o.ViewObject.Transparency = originalViewData[0]
            o.ViewObject.ShapeColor = originalViewData[1]

        self.texturedObjects = []
    
    def getTextureForMaterial(self, material):
        materialName = material.Name

        if materialName in self.textureData['materials']:
            imageFile = self.textureData['materials'][materialName]['file']

            if imageFile not in self.textureCache:
                tex = coin.SoTexture2()
                tex.filename = imageFile

                self.textureCache[imageFile] = tex
            
            return self.textureCache[imageFile]

        return None