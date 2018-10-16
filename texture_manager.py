import FreeCAD
# import math
import json
from pivy import coin
import arch_texture_utils.faceset_utils as faceset_utils

class TextureManager():
    def __init__(self, fileObject=None):
        if fileObject is None:
            self.textureData = {
                'materials': {
                #     '<mat_name>': {
                #         'file': 'path_to_texture',
                #         'bumpMap': None | 'path_to_texture',
                #         'realSize': None | {
                #              's': <length_in_mm>,
                #              't': <height_in_mm>
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
            #(object, ((texture, textureUnit), textureCoordinates, (bumpMap, textureUnit)))
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
            if self.isTexturable(o):
                texture, textureConfig = self.getTextureForMaterial(o.Material)

                if texture is not None:
                    print('Texturing %s' % (o.Label,))

                    originalTransparency = o.ViewObject.Transparency
                    originalShapeColor = o.ViewObject.ShapeColor

                    rootnode = o.ViewObject.RootNode
                    switch = faceset_utils.findSwitch(rootnode)
                    brep = faceset_utils.findBrepFaceset(switch)
                    vertexCoordinates = faceset_utils.findVertexCoordinates(rootnode)
                    faceSet = faceset_utils.buildFaceSet(brep, vertexCoordinates)
                    textureCoords = faceSet.calculateTextureCoordinates(textureConfig['realSize'])

                    bumpMap = self.generateBumpMap(textureConfig)

                    # faceSet.printData()

                    self.setupTextureCoordinateIndex(brep)

                    textureUnit = coin.SoTextureUnit()
                    textureUnit.value = 0

                    if bumpMap is None:
                        rootnode.insertChild(texture, 1)
                        rootnode.insertChild(textureCoords, 1)
                        rootnode.insertChild(textureUnit, 1)

                    bumpMapData = None

                    if bumpMap is not None:
                        bumpCoordinates = coin.SoBumpMapCoordinate()
                        bumpCoordinates.point.setValues(0, len(textureCoords.point.getValues()), textureCoords.point.getValues())
                        # bumpMapUnit = coin.SoTextureUnit()
                        # bumpMapUnit.value = 0
                        # bumpMapUnit.mappingMethod = coin.SoTextureUnit.BUMP_MAPPING

                        # bumpMapData = (bumpMap, bumpMapUnit)
                        # bumpMapData = (bumpMap)

                        rootnode.insertChild(bumpMap, 1)
                        # rootnode.insertChild(textureCoords, 1)
                        # rootnode.insertChild(bumpMapUnit, 1)
                    
                    self.texturedObjects.append((o, ((texture, textureUnit), textureCoords, bumpMapData)))
    
    def removeTextures(self):
        FreeCAD.Console.PrintMessage('Removing Textures\n')

        for o, coinData in self.texturedObjects:
            o.ViewObject.RootNode.removeChild(coinData[0][0])
            o.ViewObject.RootNode.removeChild(coinData[0][1])
            o.ViewObject.RootNode.removeChild(coinData[1])

            if coinData[2] is not None:
                o.ViewObject.RootNode.removeChild(coinData[2][0])
                o.ViewObject.RootNode.removeChild(coinData[2][1])

        self.texturedObjects = []
    
    def isTexturable(self, o):
        return hasattr(o,'Shape') and hasattr(o, 'Material') and o.Material is not None and o.ViewObject.Visibility

    def setupTextureCoordinateIndex(self, brep):
        coordinateIndex = brep.coordIndex.getValues()

        brep.textureCoordIndex.setValues(0, len(coordinateIndex), coordinateIndex)
    
    def getTextureForMaterial(self, material):
        materialName = material.Name

        if materialName in self.textureData['materials']:
            materialConfig = self.textureData['materials'][materialName]

            imageFile = materialConfig['file']

            texture = self.getOrCreateTexture(imageFile)

            return (texture, materialConfig)

        return (None, None)
    
    def generateBumpMap(self, textureConfig):
        if 'bumpMap' not in textureConfig or textureConfig['bumpMap'] is None:
            return None
        
        bumpMap = coin.SoBumpMap()
        bumpMap.filename = textureConfig['bumpMap']

        return bumpMap

        # return self.getOrCreateTexture(textureConfig['bumpMap'])
    
    def getOrCreateTexture(self, imageFile):
        if imageFile not in self.textureCache:
            tex = coin.SoTexture2()
            tex.filename = imageFile
            tex.model = coin.SoMultiTextureImageElement.REPLACE

            self.textureCache[imageFile] = tex
        
        return self.textureCache[imageFile]

    
if __name__ == "__main__":
    from os import path

    if FreeCAD.ActiveDocument is None:
        showInfo('No Document', 'Create a document to continue.')
    else:
        configFile = path.join(path.dirname(path.realpath(__file__)), 'textures',FreeCAD.ActiveDocument.Name + '.json')
        
        TextureManager(open(configFile, 'r')).textureObjects()