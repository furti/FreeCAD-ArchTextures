import FreeCAD
import math
import json
from pivy import coin
import arch_texture_utils.faceset_utils as faceset_utils
import arch_texture_utils.py2_utils as py2_utils


class TextureConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FreeCAD.Vector):
            return [obj.x, obj.y, obj.z]

        return json.JSONEncoder.default(self, obj)


class TextureConfigDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if 'vertices' in dct:
            vectors = [FreeCAD.Vector(vertices[0], vertices[1], vertices[2])
                       for vertices in dct['vertices']]

            dct['vertices'] = vectors

        return dct


class TextureManager():
    def __init__(self, fileObject=None):
        if fileObject is None:
            self.textureData = {
                'materials': {
                    #     '<mat_name>': {
                    #         'file': 'path_to_texture',
                    #         'bumpMap': 'path_to_texture',
                    #         'realSize': None | {
                    #              's': <length_in_mm>,
                    #              't': <height_in_mm>
                    #          }
                    #     }
                },
                'faceOverrides': [
                    #    {
                    #       'vertices': [],
                    #       'objectName': '<name_of_object_the_face_belongs_to>',
                    #       'rotation': <rotation_in_degrees>
                    #    }
                ]
            }
        else:
            try:
                self.textureData = json.load(
                    fileObject, encoding='utf-8', cls=TextureConfigDecoder)
            finally:
                fileObject.close()

        self.textureCache = {
            # '<file_name>': texture
        }

        self.bumpMapCache = {
            # '<file_name>': bumpmap
        }

        self.texturedObjects = [
            #(object, shadedNode, (textureUnit, texture, transform), (material, originalDiffuseColor))
        ]

    def export(self, fileObject):
        try:
            json.dump(self.textureData, fileObject, sort_keys=True,
                      indent=4, ensure_ascii=False, cls=TextureConfigEncoder)
        finally:
            fileObject.close()

    def serializeTextureData(self):
        return json.dumps(self.textureData, sort_keys=True, indent=4, ensure_ascii=False, cls=TextureConfigEncoder)

    def deserializeTextureData(self, textureDataAsString):
        self.textureData = json.loads(
            textureDataAsString, encoding='utf-8', cls=TextureConfigDecoder)

    def textureObjects(self, debug=False):
        # Make sure that no old textures are left. Otherwise we could end up with duplicate textures
        self.removeTextures()

        FreeCAD.Console.PrintMessage('Texturing objects\n')

        for o in FreeCAD.ActiveDocument.Objects:
            if self.isTexturable(o):
                # Test Script for bump mapping is here: https://forum.freecadweb.org/viewtopic.php?f=10&t=37255&p=319329#p319329
                texture, bumpMap, textureConfig = self.getTextureForMaterial(
                    o.Material)

                if texture is not None:
                    print('Texturing %s' % (o.Label,))

                    textureUnit = None
                    rootnode = o.ViewObject.RootNode
                    switch = faceset_utils.findSwitch(rootnode)
                    shadedNode = faceset_utils.findShadedNode(switch)

                    if shadedNode is None:
                        print('Object %s has no shaded node. Skipping...' % (o.Label,))
                        continue

                    brep = faceset_utils.findBrepFaceset(shadedNode)
                    material = faceset_utils.findMaterial(shadedNode)
                    vertexCoordinates = faceset_utils.findVertexCoordinates(
                        rootnode)
                    transform = faceset_utils.findTransform(rootnode)

                    originalDiffuseColor = self.updateMaterialColors(material)

                    faceSet = faceset_utils.buildFaceSet(
                        brep, vertexCoordinates, self.getFaceOverrides(), transform)
                    textureCoords = faceSet.calculateTextureCoordinates(
                        textureConfig['realSize'])

                    if debug:
                        faceSet.printData(textureConfig['realSize'], 4)

                    self.setupTextureCoordinateIndex(brep)

                    shadedNode.insertChild(texture, 1)
                    shadedNode.insertChild(textureCoords, 1)

                    # Only add the texture unit when the bump map is set
                    # Otherwise the default is OK
                    if bumpMap is not None:
                        textureUnit = coin.SoTextureUnit()
                        textureUnit.unit.setValue(1)
                        shadedNode.insertChild(textureUnit, 1)

                    if bumpMap is not None:
                        # Bump map coordinates do not work, we have to use texture coordinates
                        # Skipping the coordinates also ends in an access violation
                        shadedNode.insertChild(textureCoords, 1)
                        shadedNode.insertChild(bumpMap, 1)

                    if hasattr(o.ViewObject, 'updateVBO'):
                        o.ViewObject.updateVBO()
                    else:
                        # trick to update VBO
                        d = getattr(o.ViewObject, 'Deviation', None)
                        if d is not None:
                            o.ViewObject.Deviation = d + 0.1
                            o.ViewObject.Deviation = d

                    self.texturedObjects.append(
                        (o, shadedNode, (textureUnit, texture, textureCoords, bumpMap), (material, originalDiffuseColor)))

    def updateMaterialColors(self, material):
        originalDiffuseColor = coin.SoMFColor()
        originalDiffuseColor.copyFrom(material.diffuseColor)

        material.diffuseColor.setValue(1.0, 1.0, 1.0)

        return originalDiffuseColor

    def ensureFaceOverrides(self):
        if 'faceOverrides' not in self.textureData:
            self.textureData['faceOverrides'] = []

        return self.textureData['faceOverrides']

    def getFaceOverrides(self):
        if 'faceOverrides' in self.textureData:
            return self.textureData['faceOverrides']
        else:
            return None

    def removeTextures(self):
        FreeCAD.Console.PrintMessage('Removing Textures\n')

        for o, shadedNode, coinData, materialData in self.texturedObjects:
            if coinData[0] is not None:
                shadedNode.removeChild(coinData[0])

            if coinData[1] is not None:
                shadedNode.removeChild(coinData[1])

            if coinData[2] is not None:
                shadedNode.removeChild(coinData[2])
            
            if coinData[3] is not None:
                shadedNode.removeChild(coinData[3])
                # When a bump map is set, the texture coordinate is added twice. So remove it again
                shadedNode.removeChild(coinData[2])


            material = materialData[0]

            material.diffuseColor.deleteValues(0)
            material.diffuseColor.setValues(
                0, len(materialData[1]), materialData[1])

        self.texturedObjects = []

    def isTexturable(self, o):
        if not hasattr(o, 'Shape') or o.Shape is None or o.Shape.isNull():
            return False
        
        if not hasattr(o, 'Material') or o.Material is None:
            return False

        return o.ViewObject.Visibility

    def setupTextureCoordinateIndex(self, brep):
        coordinateIndex = brep.coordIndex.getValues()

        brep.textureCoordIndex.setValues(
            0, len(coordinateIndex), coordinateIndex)

    def getTextureForMaterial(self, material):
        materialName = material.Name

        if materialName in self.textureData['materials']:
            materialConfig = self.textureData['materials'][materialName]

            imageFile = py2_utils.textureFileString(materialConfig['file'])
            bumpMapFile = None
            bumpMap = None

            if 'bumpMap' in materialConfig:
                bumpMapFile = py2_utils.textureFileString(
                    materialConfig['bumpMap'])

            if imageFile not in self.textureCache:
                tex = coin.SoTexture2()
                tex.filename = imageFile

                self.textureCache[imageFile] = tex

            if bumpMapFile is not None:
                if bumpMapFile not in self.bumpMapCache:
                    bumpMap = coin.SoBumpMap()

                    bumpMap.filename.setValue(bumpMapFile)

                    self.bumpMapCache[bumpMapFile] = bumpMap

                bumpMap = self.bumpMapCache[bumpMapFile]

            texture = self.textureCache[imageFile]

            return (texture, bumpMap, materialConfig)

        return (None, None, None)


if __name__ == "__main__":
    from os import path
    import arch_texture_utils.qtutils as qtutils

    if FreeCAD.ActiveDocument is None:
        qtutils.showInfo('No Document', 'Create a document to continue.')
    else:
        configFile = path.join(path.dirname(path.realpath(
            __file__)), 'textures', FreeCAD.ActiveDocument.Name + '.json')

        TextureManager(open(configFile, 'r')).textureObjects(debug=False)
