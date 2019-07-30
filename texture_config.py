import FreeCAD, FreeCADGui
import re
from pivy import coin
from texture_manager import TextureManager
from arch_texture_utils.resource_utils import uiPath
from arch_texture_utils.qtutils import QComboBox, QTableWidgetItem, QDoubleSpinBox, userSelectedFile, IMAGE_FILES, showInfo

from PySide2.QtWidgets import QGroupBox
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QFormLayout
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QWidget


MAT_NAME_REGEX = re.compile(r'.* \((.*)\)')

def noneWhenEmpty(value):
    if value == None or value.strip() == '':
        return None
    
    return value

    
class MaterialConfigWidget(QGroupBox):
    def __init__(self, panel, index, materialName, textureFile, bumpMapFile, realSize):
        super().__init__()

        self.panel = panel
        self.index = index

        self.materialBox = self.createMaterialBox(materialName)
        self.textureFileEdit, self.textureFileWidget = self.createFileSelect(textureFile)
        self.bumpMapFileEdit, self.bumpMapFileWidget = self.createFileSelect(bumpMapFile)
        self.lengthEdit, self.heightEdit = self.createSizeEdit(realSize)
        self.removeButton = QPushButton('Remove')

        self.removeButton.clicked.connect(self.remove)

        self.initUi()

    def initUi(self):
        self.layout = QFormLayout()

        self.layout.addRow('Material', self.materialBox)
        self.layout.addRow('Texture', self.textureFileWidget)
        self.layout.addRow('BumpMap', self.bumpMapFileWidget)
        self.layout.addRow('Length', self.lengthEdit)
        self.layout.addRow('Height', self.heightEdit)
        self.layout.addRow(' ', self.removeButton)

        self.setLayout(self.layout)

    def getMaterialName(self):
        comboBox = self.materialBox

        return MAT_NAME_REGEX.findall(comboBox.currentText())[0]

    def getTextureFile(self):
        return noneWhenEmpty(self.textureFileEdit.text())

    def getBumpMapFile(self):
        return noneWhenEmpty(self.bumpMapFileEdit.text())

    def getLength(self):
        return self.lengthEdit.value()

    def getHeight(self):
        return self.heightEdit.value()

    def remove(self):
        self.panel.removeRow(self)
    
    def createMaterialBox(self, materialName=None):
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
    
    def createSizeEdit(self, realSize=None):
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
    
    def createFileSelect(self, file):
        edit = QLineEdit(file)
        button = QPushButton('...')
        button.setMaximumWidth(30)

        widget = QWidget()
        layout = QHBoxLayout()

        layout.addWidget(edit)
        layout.addWidget(button)

        widget.setLayout(layout)

        button.clicked.connect(lambda: self.chooseFile(edit))


        return (edit, widget)
    
    def findMaterials(self):
        materials = FreeCAD.ActiveDocument.findObjects('App::MaterialObjectPython')

        return ['%s (%s)' % (mat.Label, mat.Name) for mat in materials]
    
    def chooseFile(self, edit):
        selectedFile = userSelectedFile('Select texture', IMAGE_FILES)

        if selectedFile is None or selectedFile == '':
            return
        
        edit.setText(selectedFile)


class TextureConfigPanel():
    def __init__(self, textureConfig, freecadObject):
        self.textureConfig = textureConfig
        self.freecadObject = freecadObject
        self.textureManager = textureConfig.textureManager
        self.entries = []

        self.form = FreeCADGui.PySideUic.loadUi(uiPath('texture_config.ui'))

        self.form.Title.setText('%s Config' % (freecadObject.Label))
        self.scrollAreaWidget = self.form.ScrollArea.widget()

        self.form.AddMaterialButton.clicked.connect(self.addRow)

        self.setupRows()

    def setupRows(self):
        for materialName, entryConfig in self.textureManager.textureData['materials'].items():
            bumpMap = None

            if 'bumpMap' in entryConfig:
                bumpMap = entryConfig['bumpMap']

            self.addRow(materialName, entryConfig['file'], bumpMap, entryConfig['realSize'])

    def addRow(self, materialName = None, textureFile = None, bumpMapFile = None, realSize = None):
        widget = MaterialConfigWidget(self, len(self.entries), materialName, textureFile, bumpMapFile, realSize)

        self.entries.append(widget)

        self.scrollAreaWidget.layout().addWidget(widget)
    
    def removeRow(self, widget):
        self.entries.pop(widget.index)
        layoutItem = self.scrollAreaWidget.layout().takeAt(widget.index)

        layoutItem.widget().deleteLater()

    def accept(self):
        self.saveIntoConfig()

        FreeCADGui.Control.closeDialog()

        self.textureConfig.execute(self.freecadObject)

    def reject(self):
        FreeCADGui.Control.closeDialog()
    
    def saveIntoConfig(self):
        config = self.textureManager.textureData['materials']

        config.clear()

        for entry in self.entries:
            materialName = entry.getMaterialName()

            config[materialName] = {
                'file': entry.getTextureFile(),
                'bumpMap': entry.getBumpMapFile(),
                'realSize': {
                    's': entry.getLength(),
                    't': entry.getHeight()
                }
            }

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

        if isinstance(textureData, dict):
            # older versions stored the texture data directly
            self.textureManager.textureData = state[0]
        else:
            # newer version store a json string
            self.textureManager.deserializeTextureData(textureData)

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