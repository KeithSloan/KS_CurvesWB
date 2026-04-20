# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Import Sverchok NURBS JSON'
__author__ = 'Keith Sloan'
__license__ = 'LGPL 2.1'
__doc__ = '''Import a NURBS Curve or Surface from a Sverchok/geomdl JSON file.

The JSON may be a single object or a list of objects in geomdl exchange
format, as exported by Sverchok's "NURBS to JSON" node or the rw3dm tool.
Both NurbsCurve and NurbsSurface objects are supported; the type is detected
automatically from the presence of degree_u / degree_v keys.'''

import os
import json
from itertools import groupby

import FreeCAD
import FreeCADGui
from PySide import QtGui
from freecad.Curves import ICONPATH
from freecad.Curves.importNurbsCurveFP import NurbsCurveFP, NurbsCurveVP
from freecad.Curves.importNurbsSurfaceFP import NurbsSurfaceFP, NurbsSurfaceVP

TOOL_ICON = os.path.join(ICONPATH, 'editableSpline.svg')


def _kv_to_knots_mults(knotvector):
    """Convert a full knot vector to (knots, multiplicities) for OCCT."""
    result = [(k, sum(1 for _ in grp)) for k, grp in groupby(knotvector)]
    return [k for k, _ in result], [m for _, m in result]


def _load_curve(data, doc):
    degree = data['degree']
    pts = data['control_points']
    kv = data.get('knotvector') or data.get('knot_vector') or []
    weights = data.get('weights')
    closed = bool(data.get('closed', False))

    poles = [FreeCAD.Vector(p[0], p[1], p[2]) for p in pts]
    knots, mults = _kv_to_knots_mults(kv)
    if weights is None:
        weights = [1.0] * len(poles)

    fp = doc.addObject("Part::FeaturePython", "NurbsCurve")
    NurbsCurveFP(fp)
    NurbsCurveVP(fp.ViewObject)
    fp.Poles = poles
    fp.Weights = list(weights)
    fp.Knots = knots
    fp.Multiplicities = mults
    fp.Degree = degree
    fp.Periodic = closed
    return fp


def _load_surface(data, doc):
    degree_u = data['degree_u']
    degree_v = data['degree_v']
    kv_u = data.get('knotvector_u') or data.get('knot_vector_u') or []
    kv_v = data.get('knotvector_v') or data.get('knot_vector_v') or []
    pts = data['control_points']
    nu = data.get('size_u') or data.get('nb_poles_u')
    nv = data.get('size_v') or data.get('nb_poles_v')
    weights = data.get('weights')
    closed_u = bool(data.get('closed_u', False))
    closed_v = bool(data.get('closed_v', False))

    poles_flat = [FreeCAD.Vector(p[0], p[1], p[2]) for p in pts]

    if weights is None:
        weights_flat = [1.0] * len(poles_flat)
    elif isinstance(weights[0], (list, tuple)):
        weights_flat = [w for row in weights for w in row]
    else:
        weights_flat = list(weights)

    knots_u, mults_u = _kv_to_knots_mults(kv_u)
    knots_v, mults_v = _kv_to_knots_mults(kv_v)

    fp = doc.addObject("Part::FeaturePython", "NurbsSurface")
    NurbsSurfaceFP(fp)
    NurbsSurfaceVP(fp.ViewObject)
    fp.NbPolesU = nu
    fp.NbPolesV = nv
    fp.Poles = poles_flat
    fp.Weights = weights_flat
    fp.KnotsU = knots_u
    fp.KnotsV = knots_v
    fp.MultsU = mults_u
    fp.MultsV = mults_v
    fp.DegreeU = degree_u
    fp.DegreeV = degree_v
    fp.PeriodicU = closed_u
    fp.PeriodicV = closed_v
    return fp


def _is_surface(data):
    return 'degree_u' in data or 'degree_v' in data


class ImportSverchokJSONCommand:
    """Import NURBS Curve(s) or Surface(s) from a Sverchok/geomdl JSON file."""

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            doc = FreeCAD.newDocument()

        path, _ = QtGui.QFileDialog.getOpenFileName(
            None, "Open Sverchok NURBS JSON", "",
            "JSON files (*.json);;All files (*)"
        )
        if not path:
            return

        try:
            with open(path, 'r') as f:
                raw = json.load(f)
        except Exception as e:
            FreeCAD.Console.PrintError(
                "ImportSverchokJSON: cannot read {}: {}\n".format(path, e))
            return

        items = raw if isinstance(raw, list) else [raw]
        count = 0
        for item in items:
            try:
                if _is_surface(item):
                    _load_surface(item, doc)
                else:
                    _load_curve(item, doc)
                count += 1
            except Exception as e:
                FreeCAD.Console.PrintError(
                    "ImportSverchokJSON: failed to import item: {}\n".format(e))

        if count:
            doc.recompute()
            FreeCAD.Console.PrintMessage(
                "ImportSverchokJSON: imported {} object(s) from {}\n".format(
                    count, os.path.basename(path)))

    def IsActive(self):
        return True

    def GetResources(self):
        return {
            'Pixmap':   TOOL_ICON,
            'MenuText': __title__,
            'ToolTip':  "{}\n\n{}".format(__title__, __doc__),
        }


FreeCADGui.addCommand('Curves_ImportSverchokJSON', ImportSverchokJSONCommand())
