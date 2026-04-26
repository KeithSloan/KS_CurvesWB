# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Extract NURBS'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'
__doc__ = '''Extract editable NURBS objects from any imported Part shape.

Select one or more Part objects (imported from STEP, 3DM, or any other
source) that contain BSplineSurface faces or BSplineCurve edges, then
activate this command.

For each BSplineSurface face  → a NurbsSurfaceFP is created.
For each BSplineCurve edge    → a NurbsCurveFP is created.
Non-NURBS geometry (planes, cones, lines, arcs) is silently skipped.
Each source object is hidden after conversion.

The resulting objects can be used directly with other Curves tools such
as Gordon surface, blend surface, and IsoCurve.'''

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import ICONPATH
from freecad.Curves.importNurbsCurveFP   import NurbsCurveFP,   NurbsCurveVP
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
    try:
        curve = edge.Curve
    except Exception:
        return None
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


def _make_surface_feature(source_obj, face, face_index, doc):
    """Create a NurbsSurfaceFP from *face* (at *face_index*) and add it to *doc*."""
    bs = _bspline_from_face(face)
    if bs is None:
        return None

    poles_2d   = bs.getPoles()
    weights_2d = bs.getWeights()
    nu = len(poles_2d)
    nv = len(poles_2d[0]) if poles_2d else 0

    fp = doc.addObject("Part::FeaturePython", "NurbsSurface")
    NurbsSurfaceFP(fp)
    NurbsSurfaceVP(fp.ViewObject)

    fp.Source    = source_obj
    fp.FaceIndex = face_index

    fp.NbPolesU  = nu
    fp.NbPolesV  = nv
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


class ExtractNurbsCommand:
    """Extract all NURBS geometry from selected Part shapes into editable Curves objects."""

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.PrintError("ExtractNURBS: no active document\n")
            return

        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("ExtractNURBS: select one or more Part shapes first\n")
            return

        total_surf  = 0
        total_curve = 0

        for obj in sel:
            if not hasattr(obj, 'Shape'):
                FreeCAD.Console.PrintWarning(
                    "ExtractNURBS: {} has no Shape, skipped\n".format(obj.Name))
                continue

            n_surf  = 0
            n_curve = 0

            for face_index, face in enumerate(obj.Shape.Faces):
                fp = _make_surface_feature(obj, face, face_index, doc)
                if fp is not None:
                    n_surf += 1

            for edge in obj.Shape.Edges:
                fp = _make_curve_feature(obj, edge, doc)
                if fp is not None:
                    n_curve += 1

            if n_surf > 0 or n_curve > 0:
                obj.ViewObject.Visibility = False
                FreeCAD.Console.PrintMessage(
                    "ExtractNURBS: {} → {} surface(s), {} curve(s)\n".format(
                        obj.Label, n_surf, n_curve))
            else:
                FreeCAD.Console.PrintWarning(
                    "ExtractNURBS: no NURBS geometry found in {}\n".format(obj.Name))

            total_surf  += n_surf
            total_curve += n_curve

        if total_surf > 0 or total_curve > 0:
            doc.recompute()
            FreeCAD.Console.PrintMessage(
                "ExtractNURBS: total {} surface(s), {} curve(s) created\n".format(
                    total_surf, total_curve))
        else:
            FreeCAD.Console.PrintError(
                "ExtractNURBS: no NURBS geometry found in selection\n")

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


FreeCADGui.addCommand('Curves_ExtractNURBS', ExtractNurbsCommand())
