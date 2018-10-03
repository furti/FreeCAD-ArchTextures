import FreeCAD
import math
import json
from pivy import coin

class TextureManager():
    def __init__(self, fileObject=None):
        if fileObject is None:
            self.textureData = {
                'materials': {
                #     '<mat_name>': {
                #         'file': 'path_to_texture',
                #         'realSize': None | {
                #              'length': <length_in_mm>,
                #              'height': <height_in_mm>
                #          }
                #     }
                }
            }
        else:
            try:
                self.textureData = json.load(fileObject, encoding='utf-8')
            finally:
                fileObject.close()

        self.textureCache = {
            # '<file_name>': texture
        }

        self.texturedObjects = [
            #(object, (texture, transform), (originalTransparency, originalShapeColor))
        ]

    def export(self, fileObject):
        try:
            json.dump(self.textureData, fileObject, sort_keys=True, indent=4, ensure_ascii=False)
        finally:
            fileObject.close()

    def textureObjects(self):
        # Make sure that no old textures are left. Otherwise we could end up with duplicate textures
        self.removeTextures()

        FreeCAD.Console.PrintMessage('Texturing objects\n')

        for o in FreeCAD.ActiveDocument.Objects:
            if hasattr(o,'Shape'):
                if hasattr(o, 'Material') and o.Material is not None:
                    texture, textureConfig = self.getTextureForMaterial(o.Material)

                    if texture is not None:
                        originalTransparency = o.ViewObject.Transparency
                        originalShapeColor = o.ViewObject.ShapeColor

                        o.ViewObject.Transparency = 0
                        o.ViewObject.ShapeColor = (1.0, 1.0, 1.0)

                        texTransform = self.getTextureTransform(o, textureConfig)
                        
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
            materialConfig = self.textureData['materials'][materialName]

            imageFile = materialConfig['file']

            if imageFile not in self.textureCache:
                tex = coin.SoTexture2()
                tex.filename = imageFile
                # Maybe we can use this instead of setting the color of the shape to black?
                # Will result in white borders instead of black ones. Like the black ones more.
                # tex.model = coin.SoMultiTextureImageElement.REPLACE

                self.textureCache[imageFile] = tex
            
            return (self.textureCache[imageFile], materialConfig)

        return None
    
    def getTextureTransform(self, o, materialConfig):
        textureTransform = coin.SoTexture2Transform()
        textureTransform.rotation = math.radians(90)

        if materialConfig['realSize'] is not None:
            textureTransform.scaleFactor = self.calculateScale(o, materialConfig['realSize'])

        return textureTransform
    
    def calculateScale(self, o, sizeConfig):
        yScale = 1
        xScale = 1

        xValue = None
        yValue = None

        if hasattr(o, 'Length'):
            xValue = o.Length.Value
        
        if hasattr(o, 'Height'):
            yValue = o.Height.Value
        
        realLength = sizeConfig['length']

        if xValue is not None and realLength > 0:
            xScale = xValue / realLength
        
        realHeight = sizeConfig['height']

        if yValue is not None and realHeight > 0:
            yScale = yValue / realHeight

        print('%s, %s' % (xScale, yScale))

        return [yScale, xScale]

if __name__ == "__main__":
    from os import path

    if FreeCAD.ActiveDocument is None:
        showInfo('No Document', 'Create a document to continue.')
    else:
        configFile = path.join(path.dirname(path.realpath(__file__)), 'textures',FreeCAD.ActiveDocument.Name + '.json')
        
        TextureManager(open(configFile, 'r')).textureObjects()