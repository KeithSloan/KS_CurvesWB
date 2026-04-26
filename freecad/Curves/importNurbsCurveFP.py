# SPDX-License-Identifier: LGPL-2.1-or-later
# Shared FP/VP classes for editable NURBS curve objects.
# The GUI command lives in extractNurbsFP.py (Curves_ExtractNURBS).

__title__ = 'NURBS Curve FP'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'

import os
import FreeCAD
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


