import FreeCAD, FreeCADGui

def findSelectedTextureConfig(returnFreeCadObject=False):
    selection = FreeCADGui.Selection.getSelection()

    if len(selection) != 1:
        return None

    selectedObject = selection[0]

    if not hasattr(selectedObject, 'Proxy') or selectedObject.Proxy is None:
        return None

    if not hasattr(selectedObject.Proxy, 'isTextureConfig') or not selectedObject.Proxy.isTextureConfig:
        return None
  
    if returnFreeCadObject:
        return selection[0]
    else:
        return selection[0].Proxy

def findSelectedFaces():
    selection = FreeCADGui.Selection.getSelectionEx()

    selectedFaces = []

    for selectedObject in selection:
        subObjects = selectedObject.SubObjects

        for subObject in subObjects:
            if subObject.ShapeType == "Face":
                selectedFaces.append((selectedObject.Object.Name, subObject))
    
    return selectedFaces

def findSelectedFacesAsVectors():
    selectedFaces = findSelectedFaces()
    selectedFacesAsVectors = []

    for objectName, selectedFace in selectedFaces:
        vectors = [vertex.Point for vertex in selectedFace.Vertexes]

        selectedFacesAsVectors.append((objectName, vectors))

    return selectedFacesAsVectors
    

if __name__ == "__main__":
    print(findSelectedFacesAsVectors())

#https://forum.freecadweb.org/viewtopic.php?f=22&t=5591#p45315