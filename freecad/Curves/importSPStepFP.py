# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Import SP STEP Shape'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'
__doc__ = '''Convert all NURBS faces and boundary curves from a selected
imported STEP shape into editable Curves workbench objects.

Designed for shapes produced by Surface Psycho's STEP exporter
("Open CASCADE STEP translator" objects in the model tree), but works on
any Part shape containing BSplineSurface faces or BSplineCurve edges.

For each BSplineSurface face a NurbsSurfaceFP is created; for each
BSplineCurve boundary edge a NurbsCurveFP is created.  Non-BSpline
surfaces and curves (planes, lines, circles) are skipped.  The source
object is hidden after conversion.

The resulting objects can be used directly with other Curves tools such
as Gordon surface, blend surface, and IsoCurve.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH
from freecad.Curves.importNurbsCurveFP import NurbsCurveFP, NurbsCurveVP
from freecad.Curves.importNurbsSurfaceFP import NurbsSurfaceFP, NurbsSurfaceVP

TOOL_ICON = os.path.join(ICONPATH, 'surfEdit.svg')


def _bspline_from_face(face):
    """Return the BSplineSurface from *face*, converting if possible, else None."""
    surf = face.Surface
    if isinstance(surf, Part.BSplineSurface):
        return surf
    try:
        return surf.toBSpline()
    except Exception:
        return None


def _bspline_from_edge(edge):
    """Return the BSplineCurve from *edge*, converting if possible, else None."""
    curve = edge.Curve
    if isinstance(curve, Part.BSplineCurve):
        return curve
    try:
        return curve.toBSpline(edge.FirstParameter, edge.LastParameter)
    except Exception:
        return None


def _has_nurbs_content(obj):
    """Return True if *obj* has any BSplineSurface faces or BSplineCurve edges."""
    if not hasattr(obj, 'Shape'):
        return False
    for face in obj.Shape.Faces:
        if _bspline_from_face(face) is not None:
            return True
    for edge in obj.Shape.Edges:
        if _bspline_from_edge(edge) is not None:
            return True
    return False


def _make_surface_feature(source_obj, face, doc):
    """Create a NurbsSurfaceFP from *face* and add it to *doc*."""
    bs = _bspline_from_face(face)
    if bs is None:
        return None

    fp = doc.addObject("Part::FeaturePython", "NurbsSurface")
    NurbsSurfaceFP(fp)
    NurbsSurfaceVP(fp.ViewObject)

    fp.Source = source_obj

    poles_2d   = bs.getPoles()
    weights_2d = bs.getWeights()

    fp.NbPolesU  = len(poles_2d)
    fp.NbPolesV  = len(poles_2d[0]) if poles_2d else 0
    fp.Poles     = [p for row in poles_2d   for p in row]
    fp.Weights   = [w for row in weights_2d for w in row]
    fp.KnotsU    = bs.getUKnots()
    fp.KnotsV    = bs.getVKnots()
    fp.MultsU    = bs.getUMultiplicities()
    fp.MultsV    = bs.getVMultiplicities()
    fp.DegreeU   = bs.UDegree
    fp.DegreeV   = bs.VDegree
    fp.PeriodicU = bs.isUPeriodic()
    fp.PeriodicV = bs.isVPeriodic()
    return fp


def _make_curve_feature(source_obj, edge, doc):
    """Create a NurbsCurveFP from *edge* and add it to *doc*."""
    bs = _bspline_from_edge(edge)
    if bs is None:
        return None

    fp = doc.addObject("Part::FeaturePython", "NurbsCurve")
    NurbsCurveFP(fp)
    NurbsCurveVP(fp.ViewObject)

    fp.Source         = source_obj
    fp.Poles          = bs.getPoles()
    fp.Weights        = bs.getWeights()
    fp.Knots          = bs.getKnots()
    fp.Multiplicities = bs.getMultiplicities()
    fp.Degree         = bs.Degree
    fp.Periodic       = bs.isPeriodic()
    return fp


class ImportSPStepCommand:
    """Convert all NURBS geometry in a selected STEP shape into editable Curves objects."""

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.PrintError("ImportSPStep: no active document\n")
            return

        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("ImportSPStep: select a STEP-imported shape first\n")
            return

        total_surf = 0
        total_curve = 0

        for obj in sel:
            if not hasattr(obj, 'Shape'):
                FreeCAD.Console.PrintWarning(
                    "ImportSPStep: {} has no Shape, skipped\n".format(obj.Name))
                continue

            n_surf = n_curve = 0

            for face in obj.Shape.Faces:
                fp = _make_surface_feature(obj, face, doc)
                if fp is not None:
                    n_surf += 1
                else:
                    FreeCAD.Console.PrintWarning(
                        "ImportSPStep: non-NURBS face in {} skipped\n".format(obj.Name))

            for edge in obj.Shape.Edges:
                fp = _make_curve_feature(obj, edge, doc)
                if fp is not None:
                    n_curve += 1

            if n_surf > 0 or n_curve > 0:
                obj.ViewObject.Visibility = False
                FreeCAD.Console.PrintMessage(
                    "ImportSPStep: {} → {} surface(s), {} curve(s)\n".format(
                        obj.Label, n_surf, n_curve))

            total_surf  += n_surf
            total_curve += n_curve

        if total_surf > 0 or total_curve > 0:
            doc.recompute()
            FreeCAD.Console.PrintMessage(
                "ImportSPStep: total {} surface(s), {} curve(s) created\n".format(
                    total_surf, total_curve))
        else:
            FreeCAD.Console.PrintError(
                "ImportSPStep: no NURBS geometry found in selection\n")

    def IsActive(self):
        if not FreeCAD.ActiveDocument:
            return False
        for obj in FreeCADGui.Selection.getSelection():
            if _has_nurbs_content(obj):
                return True
        return False

    def GetResources(self):
        return {
            'Pixmap':   TOOL_ICON,
            'MenuText': __title__,
            'ToolTip':  "{}\n\n{}".format(__title__, __doc__),
        }


FreeCADGui.addCommand('Curves_ImportSPStep', ImportSPStepCommand())
