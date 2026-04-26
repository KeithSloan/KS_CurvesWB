# SPDX-License-Identifier: LGPL-2.1-or-later
# Shared FP/VP classes for editable NURBS surface objects.
# The GUI command lives in extractNurbsFP.py (Curves_ExtractNURBS).

__title__ = 'NURBS Surface FP'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'

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
    """Return (face, index) of the first Face with a BSplineSurface in *obj*.Shape, or (None, -1)."""
    if not hasattr(obj, 'Shape'):
        return None, -1
    for i, face in enumerate(obj.Shape.Faces):
        if _bspline_from_face(face) is not None:
            return face, i
    return None, -1


class NurbsSurfaceFP:
    """Parametric wrapper around an imported NURBS surface."""

    def __init__(self, obj):
        obj.addProperty("App::PropertyLink",        "Source",    "NurbsSurface", "Source object containing the NURBS surface")
        obj.addProperty("App::PropertyInteger",     "FaceIndex", "NurbsSurface", "Index of the source face in Source.Shape.Faces (-1 = unknown)")
        obj.addProperty("App::PropertyVectorList",  "Poles",     "NurbsSurface", "Control point poles (row-major, U × V)")
        obj.addProperty("App::PropertyFloatList",   "Weights",   "NurbsSurface", "Pole weights (row-major, U × V)")
        obj.addProperty("App::PropertyFloatList",   "KnotsU",    "NurbsSurface", "Knot values in U direction")
        obj.addProperty("App::PropertyFloatList",   "KnotsV",    "NurbsSurface", "Knot values in V direction")
        obj.addProperty("App::PropertyIntegerList", "MultsU",    "NurbsSurface", "Knot multiplicities in U direction")
        obj.addProperty("App::PropertyIntegerList", "MultsV",    "NurbsSurface", "Knot multiplicities in V direction")
        obj.addProperty("App::PropertyInteger",     "DegreeU",   "NurbsSurface", "Surface degree in U direction")
        obj.addProperty("App::PropertyInteger",     "DegreeV",   "NurbsSurface", "Surface degree in V direction")
        obj.addProperty("App::PropertyInteger",     "NbPolesU",  "NurbsSurface", "Number of poles in U direction")
        obj.addProperty("App::PropertyInteger",     "NbPolesV",  "NurbsSurface", "Number of poles in V direction")
        obj.addProperty("App::PropertyBool",        "PeriodicU", "NurbsSurface", "Periodic in U direction")
        obj.addProperty("App::PropertyBool",        "PeriodicV", "NurbsSurface", "Periodic in V direction")
        obj.FaceIndex = -1
        obj.Proxy = self

    def _build_bspline(self, obj):
        """Reconstruct a Part.BSplineSurface from stored properties."""
        nu       = int(obj.NbPolesU)
        nv       = int(obj.NbPolesV)
        flat_poles   = list(obj.Poles)
        flat_weights = list(obj.Weights)
        mults_u  = list(obj.MultsU)
        mults_v  = list(obj.MultsV)
        knots_u  = list(obj.KnotsU)
        knots_v  = list(obj.KnotsV)
        period_u = bool(obj.PeriodicU)
        period_v = bool(obj.PeriodicV)
        deg_u    = int(obj.DegreeU)
        deg_v    = int(obj.DegreeV)

        poles_2d   = [flat_poles[i * nv:(i + 1) * nv]   for i in range(nu)]
        weights_2d = [flat_weights[i * nv:(i + 1) * nv] for i in range(nu)] if flat_weights else None

        bs = Part.BSplineSurface()
        bs.buildFromPolesMultsKnots(
            poles_2d,
            mults_u, mults_v,
            knots_u, knots_v,
            period_u, period_v,
            deg_u, deg_v,
            weights_2d,
        )
        return bs

    def execute(self, obj):
        try:
            face_index = int(obj.FaceIndex) if hasattr(obj, 'FaceIndex') else -1
            source = obj.Source if hasattr(obj, 'Source') else None

            if (face_index >= 0
                    and source is not None
                    and hasattr(source, 'Shape')
                    and face_index < len(source.Shape.Faces)):
                # Use the source face directly: it carries the correct trim wire
                # (pcurves) that bounds the surface to the intended region.
                # The rebuilt BSplineSurface from stored poles has identical
                # parameterisation, so the source trim is geometrically valid.
                # TODO: when interactive pole editing is implemented, rebuild a
                # properly trimmed face by combining _build_bspline(obj) with the
                # boundary wire from the linked NurbyCurve FPs instead.
                obj.Shape = source.Shape.Faces[face_index].copy()
            else:
                # Fallback: untrimmed surface (correct geometry, no trim boundary)
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


