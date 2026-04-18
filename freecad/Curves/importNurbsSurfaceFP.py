# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Import NURBS Surface'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'
__doc__ = '''Convert an imported NURBS surface (e.g. from a .3dm file) into a
Curves workbench editable BSpline surface object.

Select an object whose shape is a Face containing a BSplineSurface, then
activate this command.  The source object is hidden and replaced by a
parametric Curves object whose poles, weights, knots and multiplicities
can be edited.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'surfEdit.svg')


def _bspline_from_face(face):
    """Return the BSplineSurface geometry from *face*, or None."""
    surface = face.Surface
    if isinstance(surface, Part.BSplineSurface):
        return surface
    try:
        return surface.toBSpline()
    except Exception:
        return None


def _find_bspline_face(obj):
    """Return the first Face with a BSplineSurface found in *obj*.Shape, or None."""
    if not hasattr(obj, 'Shape'):
        return None
    for face in obj.Shape.Faces:
        bs = _bspline_from_face(face)
        if bs is not None:
            return face
    return None


class NurbsSurfaceFP:
    """Parametric wrapper around an imported NURBS surface."""

    def __init__(self, obj):
        obj.addProperty("App::PropertyLink",        "Source",   "NurbsSurface", "Source object containing the NURBS surface")
        obj.addProperty("App::PropertyVectorList",  "Poles",    "NurbsSurface", "Control point poles (row-major, U × V)")
        obj.addProperty("App::PropertyFloatList",   "Weights",  "NurbsSurface", "Pole weights (row-major, U × V)")
        obj.addProperty("App::PropertyFloatList",   "KnotsU",   "NurbsSurface", "Knot values in U direction")
        obj.addProperty("App::PropertyFloatList",   "KnotsV",   "NurbsSurface", "Knot values in V direction")
        obj.addProperty("App::PropertyIntegerList", "MultsU",   "NurbsSurface", "Knot multiplicities in U direction")
        obj.addProperty("App::PropertyIntegerList", "MultsV",   "NurbsSurface", "Knot multiplicities in V direction")
        obj.addProperty("App::PropertyInteger",     "DegreeU",  "NurbsSurface", "Surface degree in U direction")
        obj.addProperty("App::PropertyInteger",     "DegreeV",  "NurbsSurface", "Surface degree in V direction")
        obj.addProperty("App::PropertyInteger",     "NbPolesU", "NurbsSurface", "Number of poles in U direction")
        obj.addProperty("App::PropertyInteger",     "NbPolesV", "NurbsSurface", "Number of poles in V direction")
        obj.addProperty("App::PropertyBool",        "PeriodicU","NurbsSurface", "Periodic in U direction")
        obj.addProperty("App::PropertyBool",        "PeriodicV","NurbsSurface", "Periodic in V direction")
        obj.Proxy = self

    def _build_bspline(self, obj):
        nu = obj.NbPolesU
        nv = obj.NbPolesV
        flat_poles   = obj.Poles
        flat_weights = obj.Weights

        poles_2d   = [flat_poles[i * nv:(i + 1) * nv]   for i in range(nu)]
        weights_2d = [flat_weights[i * nv:(i + 1) * nv] for i in range(nu)] if flat_weights else None

        bs = Part.BSplineSurface()
        bs.buildFromPolesMultsKnots(
            poles_2d,
            obj.MultsU,
            obj.MultsV,
            obj.KnotsU,
            obj.KnotsV,
            obj.PeriodicU,
            obj.PeriodicV,
            obj.DegreeU,
            obj.DegreeV,
            weights_2d,
        )
        return bs

    def execute(self, obj):
        try:
            bs = self._build_bspline(obj)
            obj.Shape = bs.toShape()
        except Exception as e:
            FreeCAD.Console.PrintError("NurbsSurfaceFP.execute: {}\n".format(e))

    def onChanged(self, obj, prop):
        pass


class NurbsSurfaceVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None
    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None


class ImportNurbsSurfaceCommand:
    """Convert a selected NURBS surface import into an editable Curves object."""

    def makeFeature(self, source_obj, face):
        bs = _bspline_from_face(face)
        if bs is None:
            FreeCAD.Console.PrintError("ImportNurbsSurface: could not extract BSplineSurface\n")
            return

        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "NurbsSurface")
        NurbsSurfaceFP(fp)
        NurbsSurfaceVP(fp.ViewObject)

        fp.Source = source_obj

        poles_2d   = bs.getPoles()    # list of lists of Vector
        weights_2d = bs.getWeights()  # list of lists of float

        fp.NbPolesU = len(poles_2d)
        fp.NbPolesV = len(poles_2d[0]) if poles_2d else 0

        fp.Poles    = [p for row in poles_2d   for p in row]
        fp.Weights  = [w for row in weights_2d for w in row]

        fp.KnotsU   = bs.getUKnots()
        fp.KnotsV   = bs.getVKnots()
        fp.MultsU   = bs.getUMultiplicities()
        fp.MultsV   = bs.getVMultiplicities()
        fp.DegreeU  = bs.UDegree
        fp.DegreeV  = bs.VDegree
        fp.PeriodicU = bs.isUPeriodic()
        fp.PeriodicV = bs.isVPeriodic()

        source_obj.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("ImportNurbsSurface: select a NURBS surface object first\n")
            return
        found = False
        for obj in sel:
            face = _find_bspline_face(obj)
            if face is not None:
                self.makeFeature(obj, face)
                found = True
            else:
                FreeCAD.Console.PrintWarning("ImportNurbsSurface: {} has no BSplineSurface face, skipped\n".format(obj.Name))
        if not found:
            FreeCAD.Console.PrintError("ImportNurbsSurface: no suitable NURBS surface found in selection\n")

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        for obj in FreeCADGui.Selection.getSelection():
            if _find_bspline_face(obj) is not None:
                return True
        return False

    def GetResources(self):
        return {
            'Pixmap':   TOOL_ICON,
            'MenuText': __title__,
            'ToolTip':  "{}\n\n{}".format(__title__, __doc__),
        }


FreeCADGui.addCommand('Curves_ImportNurbsSurface', ImportNurbsSurfaceCommand())
