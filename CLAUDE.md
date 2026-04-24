# Claude Code Instructions — KS_CurvesWB

## Project context

This is Keith Sloan's fork of [tomate44/CurvesWB](https://github.com/tomate44/CurvesWB), a FreeCAD
Python workbench for NURBS curves and surfaces.  The fork extends the workbench with commands that
convert externally-imported NURBS geometry into fully editable `Part::FeaturePython` objects.

Source lives at `/Users/ksloan/Workbenches/KS_CurvesWB/`.  The `freecad/Curves/` sub-package is
what FreeCAD loads.

## Deployment

The working copy **is** the installed copy — FreeCAD loads straight from
`/Users/ksloan/Workbenches/KS_CurvesWB/freecad/Curves/`.  There is no separate install step.
Edits take effect after restarting FreeCAD (or `importlib.reload` in the FreeCAD Python console).

## FeaturePython pattern

Every import command follows the same three-class pattern:

```
NurbsCurveFP / NurbsSurfaceFP   ← proxy: __init__ adds properties, execute rebuilds shape
NurbsCurveVP / NurbsSurfaceVP   ← view provider: icon, on-change display
ImportXxxCommand                ← GUI command: Activated, IsActive, GetResources
```

The proxy and view-provider classes for curves and surfaces are defined once in the shared modules
below, then imported by all other commands that need to create those objects.

### Shared FP modules

| Module | Classes | Purpose |
|---|---|---|
| `importNurbsCurveFP.py` | `NurbsCurveFP`, `NurbsCurveVP` | Editable BSpline curve FP |
| `importNurbsSurfaceFP.py` | `NurbsSurfaceFP`, `NurbsSurfaceVP` | Editable BSpline surface FP |

When a new command needs to create NurbsCurve or NurbsSurface objects, import from these modules:

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

## Registering a new command

1. Create `freecad/Curves/importXxxFP.py` following the three-class pattern.
2. Add `from . import importXxxFP` to `init_gui.py` `Initialize()`.
3. Add `"Curves_XxxCmd"` to the appropriate list (`curvelist`, `surflist`, or `misclist`).
4. Call `FreeCADGui.addCommand('Curves_XxxCmd', XxxCommand())` at the bottom of the module.

## Import commands (KS additions)

### `importNurbsCurveFP.py` — `Curves_ImportNurbsCurve`

Converts the first BSplineCurve edge in the selected object into an editable `NurbsCurveFP`.
Designed for curves imported via the ImportExport_3DM workbench.

### `importNurbsSurfaceFP.py` — `Curves_ImportNurbsSurface`

Converts the first BSplineSurface face in the selected object into an editable `NurbsSurfaceFP`.
Designed for surfaces imported via the ImportExport_3DM workbench.

### `importSverchokJSON.py` — `Curves_ImportSverchokJSON`

Reads a geomdl/Sverchok JSON file and creates `NurbsCurveFP` or `NurbsSurfaceFP` objects.
The JSON uses a full expanded knot vector; the importer converts it to unique-knots + multiplicities.

### `importSPStepFP.py` — `Curves_ImportSPStep`

Converts **all** NURBS faces and boundary curves from a selected STEP-imported shape into editable
Curves objects.  Designed for shapes produced by Surface Psycho's STEP exporter (objects labelled
"Open CASCADE STEP translator 7.9 1" in the model tree), but works on any `Part::Feature` that
contains `BSplineSurface` faces or `BSplineCurve` edges.

**What it does:**
- For every `BSplineSurface` face → creates a `NurbsSurfaceFP`.
- For every `BSplineCurve` boundary edge → creates a `NurbsCurveFP`.
- Non-NURBS geometry (planes, cones, lines, arcs) is silently skipped.
- The source object is hidden after conversion.

**Key helpers:**
```python
def _bspline_from_face(face):   # returns BSplineSurface or None (tries toBSpline())
def _bspline_from_edge(edge):   # returns BSplineCurve or None (tries toBSpline())
def _has_nurbs_content(obj):    # drives IsActive()
def _make_surface_feature(source_obj, face, doc):
def _make_curve_feature(source_obj, edge, doc):
```

## Surface Psycho (SP) → FreeCAD Curves pipeline

```
Surface Psycho NURBS patch  (Blender, /Users/ksloan/github/Bezier-quest/)
    ↓  File → Export STEP  (SP's built-in OCP exporter)
STEP file  (B_SPLINE_SURFACE_WITH_KNOTS + boundary curves)
    ↓  File → Import  (FreeCAD built-in STEP importer)
"Open CASCADE STEP translator 7.9 1"  (static Part::Feature in model tree)
    ↓  Select shape → Misc. → Import SP STEP Shape
NurbsSurfaceFP  +  NurbsCurveFP objects  (fully editable properties)
    ↓  Gordon surface / IsoCurve / blend surface / etc.
Parametric NURBS model in FreeCAD
```

SP STEP files typically produce:
- 1 × `NurbsSurface` per patch face
- 4 × `NurbsCurve` boundary edges per patch (ready for Gordon surface construction)

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
