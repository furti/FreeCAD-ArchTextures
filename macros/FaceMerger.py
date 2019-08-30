# This macro copies the selected faces and adds a material object to the copies.
# This is especially useful when you want to texture different parts of a solid with different textures
import FreeCAD
import FreeCADGui
import Part

def getSelectedFaces():
	sel = FreeCADGui.Selection.getSelectionEx()
	
	if len(sel) == 0:
		return None

	faces = []

	for selectedObject  in sel:
		if selectedObject.HasSubObjects:	
			for subObject in selectedObject.SubObjects:
				if hasattr(subObject, 'Faces') and subObject.Faces is not None:
					faces.extend(subObject.Faces)
	
	return faces

def mergeFaces(faces, normal):
	mergedFace = faces[0].copy()

	if len(faces) > 1:
		for face in faces[1:]:
			mergedFace = mergedFace.fuse(face)

	extrude = mergedFace.extrude(normal)
	
	return extrude.removeSplitter()

def showFace(face):
	obj = FreeCAD.ActiveDocument.addObject("Part::Feature", "FaceCopy")
	obj.Shape = face
	#obj.Placement.move(normal.normalize())
	obj.ViewObject.ShapeColor = (0.667,0.000,0.000)

	obj.addProperty('App::PropertyLink', 'Material', 'Base', 'Material for the object')


# main
faces = getSelectedFaces()

if faces is None or len(faces) == 0:
	print('Select at least one face')
else:
	newFace = mergeFaces(faces, faces[0].normalAt(0.5, 0.5))
	showFace(newFace)		
	FreeCAD.ActiveDocument.recompute()