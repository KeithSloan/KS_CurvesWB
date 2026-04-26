# Claude Code Instructions — KS_CurvesWB

## Project context

This is Keith Sloan's fork of [tomate44/CurvesWB](https://github.com/tomate44/CurvesWB), a FreeCAD
Python workbench for NURBS curves and surfaces.  The fork extends the workbench with commands that
extract externally-imported NURBS geometry into fully editable `Part::FeaturePython` objects.

Source lives at `/Users/ksloan/Workbenches/KS_CurvesWB/`.  The `freecad/Curves/` sub-package is
what FreeCAD loads.

## Deployment

The working copy **is** the installed copy — FreeCAD loads straight from
`/Users/ksloan/Workbenches/KS_CurvesWB/freecad/Curves/`.  There is no separate install step.
Edits take effect after restarting FreeCAD (or `importlib.reload` in the FreeCAD Python console).

## FeaturePython pattern

Every command follows the same three-class pattern:

```
NurbsCurveFP / NurbsSurfaceFP   ← proxy: __init__ adds properties, execute rebuilds shape
NurbsCurveVP / NurbsSurfaceVP   ← view provider: icon, on-change display
XxxCommand                      ← GUI command: Activated, IsActive, GetResources
```

The proxy and view-provider classes for curves and surfaces are defined once in the shared modules
below, then imported by all commands that need to create those objects.

### Shared FP modules

| Module | Classes | Purpose |
|---|---|---|
| `importNurbsCurveFP.py` | `NurbsCurveFP`, `NurbsCurveVP` | Editable BSpline curve FP |
| `importNurbsSurfaceFP.py` | `NurbsSurfaceFP`, `NurbsSurfaceVP` | Editable BSpline surface FP |

These modules contain **only** the FP/VP classes — no GUI commands.  The command lives in
`extractNurbsFP.py`.  Import from these modules whenever creating NURBS FP objects:

```python
from freecad.Curves.importNurbsCurveFP   import NurbsCurveFP, NurbsCurveVP
from freecad.Curves.importNurbsSurfaceFP import NurbsSurfaceFP, NurbsSurfaceVP
```

### NurbsCurveFP properties

| Property | Type | Set from OCCT |
|---|---|---|
| `Source` | Link | source object reference |
| `Poles` | VectorList | `bs.getPoles()` |
| `Weights` | FloatList | `bs.getWeights()` |
| `Knots` | FloatList | `bs.getKnots()` |
| `Multiplicities` | IntegerList | `bs.getMultiplicities()` |
| `Degree` | Integer | `bs.Degree` |
| `Periodic` | Bool | `bs.isPeriodic()` |

### NurbsSurfaceFP properties

| Property | Type | Set from OCCT |
|---|---|---|
| `Source` | Link | source object reference |
| `FaceIndex` | Integer | index into `Source.Shape.Faces` (−1 = unknown) |
| `Poles` | VectorList | flat row-major from `bs.getPoles()` |
| `Weights` | FloatList | flat row-major from `bs.getWeights()` |
| `NbPolesU` | Integer | `len(poles_2d)` |
| `NbPolesV` | Integer | `len(poles_2d[0])` |
| `KnotsU` | FloatList | `bs.getUKnots()` |
| `KnotsV` | FloatList | `bs.getVKnots()` |
| `MultsU` | IntegerList | `bs.getUMultiplicities()` |
| `MultsV` | IntegerList | `bs.getVMultiplicities()` |
| `DegreeU` | Integer | `bs.UDegree` |
| `DegreeV` | Integer | `bs.VDegree` |
| `PeriodicU` | Bool | `bs.isUPeriodic()` |
| `PeriodicV` | Bool | `bs.isVPeriodic()` |

Poles and Weights are stored **flat row-major** (U-row outer):
```python
fp.Poles   = [p for row in poles_2d   for p in row]
fp.Weights = [w for row in weights_2d for w in row]
```

### NurbsSurfaceFP.execute — shape and the FaceIndex fix

**Critical:** `execute` does NOT call `bs.toShape()` for the displayed shape.  Instead it uses
`source.Shape.Faces[FaceIndex].copy()`.

**Why:** A BSplineSurface extracted from a STEP or 3DM face is the *untrimmed* underlying surface.
Its 3D extent over the full UV parameter domain [0,1]×[0,1] is larger than the original trimmed
face and the surface interior can fold or protrude well outside the intended trim region —
producing triangular spike artefacts when displayed.  The source face already carries the correct
trim wire (OCC pcurves), which correctly clips the surface to the intended 3D region.  Because the
rebuilt BSplineSurface has an identical parameterisation (same poles, knots, weights, degrees),
the source face's trim wire is geometrically valid for the rebuilt surface.

```python
# execute — correct pattern
obj.Shape = source.Shape.Faces[int(obj.FaceIndex)].copy()

# Fallback when FaceIndex is unavailable (untrimmed, may show artefacts)
bs = self._build_bspline(obj)
obj.Shape = bs.toShape()
```

**Confirmed non-issues during debugging:**
- `obj.Placement` is identity — placement is not the cause of any shape discrepancy.
- All NURBS properties (poles, knots, weights) round-trip correctly through FP storage.
- `bs.toShape().BoundBox` is correct before assignment; `obj.Shape.BoundBox` reads smaller
  because FreeCAD measures the bounding box of the outer wire only, not the full surface interior.
  This is a FreeCAD measurement quirk, not a data error.

**TODO (future work):** When interactive pole editing is implemented, `execute` should rebuild a
properly trimmed face by combining `_build_bspline(obj)` with the boundary wire from the linked
NurbyCurve FPs, rather than copying the (now stale) source face.

## Registering a new command

1. Create `freecad/Curves/xxxFP.py` following the three-class pattern.
2. Add `from . import xxxFP` to `init_gui.py` `Initialize()`.
3. Add `"Curves_XxxCmd"` to the appropriate list (`curvelist`, `surflist`, or `misclist`).
4. Call `FreeCADGui.addCommand('Curves_XxxCmd', XxxCommand())` at the bottom of the module.

## KS commands (Misc. menu)

### `extractNurbsFP.py` — `Curves_ExtractNURBS`

Extracts **all** editable NURBS objects from any selected Part shape.  Works on shapes imported
from STEP, 3DM, or any other source.

- For every `BSplineSurface` face → creates a `NurbsSurfaceFP` (with `FaceIndex` set).
- For every `BSplineCurve` edge  → creates a `NurbsCurveFP`.
- Non-NURBS geometry (planes, cones, lines, arcs) is silently skipped.
- Each source object is hidden after conversion.

**Key helpers:**
```python
def _bspline_from_face(face):                          # BSplineSurface or None
def _bspline_from_edge(edge):                          # BSplineCurve or None
def _has_nurbs_content(obj):                           # drives IsActive()
def _make_surface_feature(source_obj, face, face_index, doc):
def _make_curve_feature(source_obj, edge, doc):
```

This single command replaces the four retired commands: Import NURBS Curve, Import NURBS Surface,
Import SP STEP Shape, and Import 3DM Shape.

### `importSverchokJSON.py` — `Curves_ImportSverchokJSON`

Reads a geomdl/Sverchok JSON file and creates `NurbsCurveFP` or `NurbsSurfaceFP` objects.
The JSON uses a full expanded knot vector; the importer converts it to unique-knots + multiplicities.
This is a true file import (from disk) so "Import" is the correct term here.

## Surface Psycho (SP) → FreeCAD Curves pipeline

```
Surface Psycho NURBS patch  (Blender, /Users/ksloan/github/Bezier-quest/)
    ↓  File → Export STEP  (SP's built-in OCP exporter)
STEP file  (B_SPLINE_SURFACE_WITH_KNOTS + boundary curves)
    ↓  File → Import  (FreeCAD built-in STEP importer)
"Open CASCADE STEP translator 7.9 x"  (static Part::Feature in model tree)
    ↓  Select shape → Misc. → Extract NURBS
NurbsSurfaceFP  +  NurbyCurveFP objects  (fully editable properties)
    ↓  Gordon surface / IsoCurve / blend surface / etc.
Parametric NURBS model in FreeCAD
```

SP STEP files typically produce:
- 1 × `NurbsSurface` per patch face
- 4 × `NurbyCurve` boundary edges per patch (ready for Gordon surface construction)

## Related external repos

| Repo | Path | Purpose |
|---|---|---|
| ImportExport_3DM | `/Users/ksloan/Workbenches/ImportExport_3DM/` | FreeCAD importer for `.3dm` files |
| Blender_Export_3DM | `/Users/ksloan/github/Blender_Export_3DM/` | Blender exporter to `.3dm` |
| Surface Psycho add-on | `/Users/ksloan/github/Blender_Addons/SurfacePsycho/` | SP internals reference |
| Bezier-quest | `/Users/ksloan/github/Bezier-quest/` | SP demo/test blend files |

## Blender installation convention

After installing Blender, the user renames `/Applications/Blender.app` to
`/Applications/Blender_x.y.z.app`.  Always use the versioned path in shell commands.
