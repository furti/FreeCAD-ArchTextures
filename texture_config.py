import FreeCAD, FreeCADGui
import re
from pivy import coin
from texture_manager import TextureManager
from arch_texture_utils.resource_utils import uiPath
from arch_texture_utils.qtutils import QComboBox, QTableWidgetItem, QDoubleSpinBox, userSelectedFile, IMAGE_FILES, showInfo

MAT_NAME_REGEX = re.compile(r'.* \((.*)\)')

class TextureConfigTable():
    def __init__(self, config, qtTable):
        self.config = config
        self.qtTable = qtTable

        self.qtTable.itemDoubleClicked.connect(self.doubleClicked)

        self.setupTable()
    
    def setupTable(self):
        for name, entryConfig in self.config.items():
            self.addRow(name, entryConfig['file'], entryConfig['realSize'])

    def addRow(self, name=None, textureFile=None, realSize=None):
        rowPosition = self.qtTable.rowCount()
        self.qtTable.insertRow(rowPosition)

        comboBox = self.materialBox(name)
        fileEdit = self.fileInput(textureFile)
        lengthEdit, heightEdit = self.sizeEdit(realSize)

        self.qtTable.setCellWidget(rowPosition, 0, comboBox)
        self.qtTable.setItem(rowPosition, 1, fileEdit)
        self.qtTable.setCellWidget(rowPosition, 2, lengthEdit)
        self.qtTable.setCellWidget(rowPosition, 3, heightEdit)
    
    def removeRow(self):
        selectionModel = self.qtTable.selectionModel()

        if selectionModel.hasSelection():
            for selection in selectionModel.selectedRows():
                FreeCAD.Console.PrintMessage(selection.row())
                self.qtTable.removeRow(selection.row())
    
    def saveIntoConfig(self):
        self.config.clear()

        for row in range(self.qtTable.rowCount()):
            comboBox = self.qtTable.cellWidget(row, 0)
            fileBox = self.qtTable.item(row, 1)
            lengthEdit = self.qtTable.cellWidget(row, 2)
            heightEdit = self.qtTable.cellWidget(row, 3)

            materialName = MAT_NAME_REGEX.findall(comboBox.currentText())[0]

            self.config[materialName] = {
                'file': fileBox.text(),
                'realSize': {
                    's': lengthEdit.value(),
                    't': heightEdit.value()
                }
            }
    
    def materialBox(self, materialName=None):
        materialBox = QComboBox()

        materials = self.findMaterials()
        materialBox.addItems(materials)

        if materialName is not None:
            boxEntry = [mat for mat in materials if mat.find('(%s)' % (materialName, )) > -1]

            if len(boxEntry) == 1:
                index = materialBox.findText(boxEntry[0])
            else:
                index = -1

            if index != -1:
                FreeCAD.Console.PrintMessage('Found Matname: %s\n' % (materialName,))
                materialBox.setCurrentIndex(index)

        return materialBox
    
    def fileInput(self, file=None):
        fileInput = QTableWidgetItem(file)

        return fileInput
    
    def sizeEdit(self, realSize=None):
        lengthEdit = QDoubleSpinBox()
        heightEdit = QDoubleSpinBox()

        lengthEdit.setSuffix('mm')
        heightEdit.setSuffix('mm')

        lengthEdit.setMinimum(0)
        heightEdit.setMinimum(0)

        lengthEdit.setMaximum(100000)
        heightEdit.setMaximum(100000)

        if realSize is not None:
            lengthEdit.setValue(realSize['s'])
        
        if realSize is not None:
            heightEdit.setValue(realSize['t'])

        return (lengthEdit, heightEdit)
    
    def doubleClicked(self, item):
        selectedFile = userSelectedFile('Select texture', IMAGE_FILES)

        if selectedFile is None or selectedFile == '':
            return
        
        item.setText(selectedFile)
    
    def findMaterials(self):
        materials = FreeCAD.ActiveDocument.findObjects('App::MaterialObjectPython')

        return ['%s (%s)' % (mat.Label, mat.Name) for mat in materials]

class TextureConfigPanel():
    def __init__(self, textureConfig, freecadObject):
        self.textureConfig = textureConfig
        self.freecadObject = freecadObject
        self.textureManager = textureConfig.textureManager

        self.form = FreeCADGui.PySideUic.loadUi(uiPath('texture_config.ui'))

        self.materialTable = TextureConfigTable(self.textureManager.textureData['materials'], self.form.MaterialTable)
        self.form.AddMaterialButton.clicked.connect(self.materialTable.addRow)
        self.form.RemoveMaterialButton.clicked.connect(self.materialTable.removeRow)

    def accept(self):
        self.materialTable.saveIntoConfig()

        FreeCADGui.Control.closeDialog()

        self.textureConfig.execute(self.freecadObject)

    def reject(self):
        FreeCADGui.Control.closeDialog()

class TextureConfig():
    def __init__(self, obj, fileObject=None):
        obj.Proxy = self
        
        self.textureManager = TextureManager(fileObject)
        self.showTextures = True

        self.execute(obj)

        self.isTextureConfig = True
    
    def execute(self, fp):
        if self.showTextures:
            self.textureManager.textureObjects()
        else:
            self.textureManager.removeTextures()
    
    def export(self, fileObject):
        self.textureManager.export(fileObject)

    def __getstate__(self):
        '''Store the texture config inside the FreeCAD File'''
        return (self.textureManager.serializeTextureData(),)
    
    def __setstate__(self, state):
        '''Load the texture config from the FreeCAD File'''
        
        self.textureManager = TextureManager()

        textureData = state[0]

        if isinstance(textureData, str):
            # newer version store a json string
            self.textureManager.deserializeTextureData(textureData)
        else:
            # older versions stored the texture data directly
            self.textureManager.textureData = state[0]

        self.isTextureConfig = True

        return None

class ViewProviderTextureConfig():
    def __init__(self, vobj):
        vobj.Proxy = self
    
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.textureConfig = self.Object.Proxy

        self.textureConfig.showTextures = vobj.Visibility

        self.coinNode = coin.SoGroup()
        vobj.addDisplayMode(self.coinNode, "Standard");
        vobj.Visibility = False
    
    def onChanged(self, vp, prop):
        if prop == 'Visibility':
            self.textureConfig.showTextures = vp.Visibility
            self.textureConfig.execute(self.Object)
    
    def doubleClicked(self, vobj):
        return self.setEdit(vobj, 0)

    def setEdit(self, vobj, mode):
        if mode == 0:
            panel = TextureConfigPanel(self.textureConfig, self.Object)
            FreeCADGui.Control.showDialog(panel)

            return True
        
        return False

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return False

    def getDisplayModes(self,obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def updateData(self, fp, prop):
        pass
    
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def createTextureConfig(fileObject=None):
    textureConfigObject = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "TextureConfig")
    textureConfig = TextureConfig(textureConfigObject, fileObject)
    ViewProviderTextureConfig(textureConfigObject.ViewObject)

if __name__ == "__main__":
    from os import path

    if FreeCAD.ActiveDocument is None:
        showInfo('No Document', 'Create a document to continue.')
    else:
        configFile = path.join(path.dirname(path.realpath(__file__)), 'textures',FreeCAD.ActiveDocument.Name + '.json')
        
        createTextureConfig(open(configFile, 'r'))