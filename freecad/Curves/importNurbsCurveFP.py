# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Import NURBS Curve'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'
__doc__ = '''Convert an imported NURBS curve (e.g. from a .3dm file) into a
Curves workbench editable BSpline curve object.

Select an object whose shape is an Edge containing a BSplineCurve, then
activate this command.  The source object is hidden and replaced by a
parametric Curves object whose poles, weights, knots and multiplicities
can be edited.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'editableSpline.svg')


def _bspline_from_edge(edge):
    """Return the BSplineCurve geometry from *edge*, or None."""
    try:
        curve = edge.Curve
    except Exception:
        return None  # undefined/unsupported curve type (e.g. seam or degenerate edge)
    if isinstance(curve, Part.BSplineCurve):
        return curve
    # Try to convert lines/arcs to BSpline as a fallback
    try:
        return curve.toBSpline(edge.FirstParameter, edge.LastParameter)
    except Exception:
        return None


def _find_bspline_edge(obj):
    """Return the first Edge with a BSplineCurve found in *obj*.Shape, or None."""
    if not hasattr(obj, 'Shape'):
        return None
    shape = obj.Shape
    for edge in shape.Edges:
        bs = _bspline_from_edge(edge)
        if bs is not None:
            return edge
    return None


class NurbsCurveFP:
    """Parametric wrapper around an imported NURBS curve."""

    def __init__(self, obj):
        obj.addProperty("App::PropertyLink",        "Source",         "NurbsCurve", "Source object containing the NURBS curve")
        obj.addProperty("App::PropertyVectorList",  "Poles",          "NurbsCurve", "Control point poles")
        obj.addProperty("App::PropertyFloatList",   "Weights",        "NurbsCurve", "Pole weights")
        obj.addProperty("App::PropertyFloatList",   "Knots",          "NurbsCurve", "Knot values")
        obj.addProperty("App::PropertyIntegerList", "Multiplicities", "NurbsCurve", "Knot multiplicities")
        obj.addProperty("App::PropertyInteger",     "Degree",         "NurbsCurve", "Curve degree")
        obj.addProperty("App::PropertyBool",        "Periodic",       "NurbsCurve", "Periodic curve")
        obj.Proxy = self

    def _build_bspline(self, obj):
        bs = Part.BSplineCurve()
        bs.buildFromPolesMultsKnots(
            obj.Poles,
            obj.Multiplicities,
            obj.Knots,
            obj.Periodic,
            obj.Degree,
            obj.Weights if obj.Weights else None,
        )
        return bs

    def execute(self, obj):
        try:
            bs = self._build_bspline(obj)
            obj.Shape = bs.toShape()
        except Exception as e:
            FreeCAD.Console.PrintError("NurbsCurveFP.execute: {}\n".format(e))

    def onChanged(self, obj, prop):
        pass


class NurbsCurveVP:
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


class ImportNurbsCurveCommand:
    """Convert a selected NURBS curve import into an editable Curves object."""

    def makeFeature(self, source_obj, edge):
        bs = _bspline_from_edge(edge)
        if bs is None:
            FreeCAD.Console.PrintError("ImportNurbsCurve: could not extract BSplineCurve\n")
            return

        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "NurbsCurve")
        NurbsCurveFP(fp)
        NurbsCurveVP(fp.ViewObject)

        fp.Source         = source_obj
        fp.Poles          = bs.getPoles()
        fp.Weights        = bs.getWeights()
        fp.Knots          = bs.getKnots()
        fp.Multiplicities = bs.getMultiplicities()
        fp.Degree         = bs.Degree
        fp.Periodic       = bs.isPeriodic()

        source_obj.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("ImportNurbsCurve: select a NURBS curve object first\n")
            return
        found = False
        for obj in sel:
            edge = _find_bspline_edge(obj)
            if edge is not None:
                self.makeFeature(obj, edge)
                found = True
            else:
                FreeCAD.Console.PrintWarning("ImportNurbsCurve: {} has no BSplineCurve edge, skipped\n".format(obj.Name))
        if not found:
            FreeCAD.Console.PrintError("ImportNurbsCurve: no suitable NURBS curve found in selection\n")

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        for obj in FreeCADGui.Selection.getSelection():
            if _find_bspline_edge(obj) is not None:
                return True
        return False

    def GetResources(self):
        return {
            'Pixmap':   TOOL_ICON,
            'MenuText': __title__,
            'ToolTip':  "{}\n\n{}".format(__title__, __doc__),
        }


FreeCADGui.addCommand('Curves_ImportNurbsCurve', ImportNurbsCurveCommand())
