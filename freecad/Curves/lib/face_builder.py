from typing import overload
import FreeCAD
import Part


def face_validate(face):
    if face.isValid():
        return face
    print("face is not valid.")
    face.validate()
    if face.isValid():
        print("Validation success.")
    else:
        print("Validation failed.")
    return face


def shapefix_builder(surface, wires=[], tol=1e-7):
    """
    Create a face with with surface and wires
    It uses Part.Shapefix.Face tool.
    new_face = shapefix_builder(face, surface=[], tol=1e-7)
    """
    ffix = Part.ShapeFix.Face(surface, tol)
    for w in wires:
        ffix.add(w)
    ffix.perform()
    if ffix.fixOrientation():
        print("shapefix_builder fixOrientation")
    if ffix.fixMissingSeam():
        print("shapefix_builder fixMissingSeam")
    return face_validate(ffix.face())


def change_surface(surface, face, tol=1e-7):
    """
    Create a face with a new surface support
    new_face = change_surface(surface, face, tol=1e-7)
    """
    return shapefix_builder(surface, face.Wires, tol)



