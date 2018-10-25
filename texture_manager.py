import FreeCAD
import math
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
            #(object, shadedNode, (texture, transform))
        ]

    def export(self, fileObject):
        try:
            json.dump(self.textureData, fileObject, sort_keys=True, indent=4, ensure_ascii=False)
        finally:
            fileObject.close()

    def textureObjects(self, debug=False):
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
                    shadedNode = faceset_utils.findShadedNode(switch)
                    brep = faceset_utils.findBrepFaceset(shadedNode)
                    vertexCoordinates = faceset_utils.findVertexCoordinates(rootnode)
                    faceSet = faceset_utils.buildFaceSet(brep, vertexCoordinates)
                    textureCoords = faceSet.calculateTextureCoordinates(textureConfig['realSize'])

                    if debug:
                        faceSet.printData(textureConfig['realSize'], 4)

                    self.setupTextureCoordinateIndex(brep)

                    shadedNode.insertChild(texture, 1)
                    shadedNode.insertChild(textureCoords, 1)

                    self.texturedObjects.append((o, shadedNode, (texture, textureCoords)))
    
    def removeTextures(self):
        FreeCAD.Console.PrintMessage('Removing Textures\n')

        for o, shadedNode, coinData in self.texturedObjects:
            shadedNode.removeChild(coinData[0])
            shadedNode.removeChild(coinData[1])

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

            if imageFile not in self.textureCache:
                tex = coin.SoTexture2()
                tex.filename = imageFile
                # Maybe we can use this instead of setting the color of the shape to black?
                # Will result in white borders instead of black ones. Like the black ones more.
                tex.model = coin.SoMultiTextureImageElement.REPLACE

                self.textureCache[imageFile] = tex
            
            return (self.textureCache[imageFile], materialConfig)

        return (None, None)
    
if __name__ == "__main__":
    from os import path

    if FreeCAD.ActiveDocument is None:
        showInfo('No Document', 'Create a document to continue.')
    else:
        configFile = path.join(path.dirname(path.realpath(__file__)), 'textures',FreeCAD.ActiveDocument.Name + '.json')
        
        TextureManager(open(configFile, 'r')).textureObjects(debug = False)