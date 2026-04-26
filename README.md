## FreeCAD Curves and Surfaces WorkBench 
![Curves Workbench](https://github.com/tomate44/CurvesWB/raw/main/docs/pics/CurvesWB.jpg)

This is a python workbench for [FreeCAD](https://www.freecad.org), with a collection of tools, mainly for NURBS curves and surfaces.  
This workbench is developed for FreeCAD main develoment branch.

## Important Notes  
* This workbench is EXPERIMENTAL and should NOT be used for any serious work.
* This workbench is not suitable for beginners. A good knowledge of FreeCAD is needed.
* This workbench is essentially my personal playground for experimenting with geometric algorithms.

## Installation 
There are 2 methods to install Curves WB:

#### Automatic (recommended)
For FreeCAD version 0.17 or higher it's preferred to install this workbench with the [FreeCAD's addon manager](https://wiki.freecad.org/Std_AddonMgr) under the label **Curves**.

#### Manual
<details>
<summary>Expand this section for instructions on Manual install</summary>

- Move to the location of your personal FreeCAD folder 
    - On Linux it is usually `/home/username/.local/share/FreeCAD/`
    - On Windows it is `%APPDATA%\FreeCAD\Mod\` which is usually `C:\Users\username\Appdata\Roaming\FreeCAD\`
    - On macOS it is usually `/Users/username/Library/Preferences/FreeCAD/`
- Move to the Mod folder : `cd ./Mod` (create the `Mod/` folder beforehand if it doesn't exist)
- `git clone https://github.com/tomate44/CurvesWB`
- Start FreeCAD

</details><br/>

## Documentation
The Curves workbench documentation can be found on the [FreeCAD wiki](https://wiki.freecad.org/Curves_Workbench).

## Feedback  
The main and recommended channel for discussion, feedback, suggestions, and patches is the following discussion of FreeCAD's forum : [Curves workbench](https://forum.freecad.org/viewtopic.php?f=8&t=22675)

## Contributing
#### Reporting issues
Issues should first be reported in the [FreeCAD forum discussion](https://forum.freecad.org/viewtopic.php?f=8&t=22675). A minimal FreeCAD file demonstrating the bug should be attached.  
Issues reported in Github may be unnoticed. A minimal FreeCAD file demonstrating the bug should be attached to the issue report, with *.FCStd extension renamed to *.zip

#### Contributing code
Code contribution is NOT encouraged and should first be discussed in [FreeCAD forum discussion](https://forum.freecad.org/viewtopic.php?f=8&t=22675).

#### Contributing documentation
The workbench documention is not extensive.  
Contributing documentation on [FreeCAD wiki](https://wiki.freecad.org/Curves_Workbench) is welcome.

## KS Extensions: Extracting and Importing NURBS Geometry

This fork adds commands for converting externally-imported NURBS geometry into fully
editable `Part::FeaturePython` objects.  The resulting objects store all NURBS data
(poles, weights, knots, multiplicities, degree, periodicity) as editable properties,
making them available to all other Curves workbench tools.

All commands are found in the **Misc.** toolbar and menu.

---

### Extract NURBS

**Command:** `Curves_ExtractNURBS`

Extracts **all** editable NURBS objects from any selected Part shape — whether
imported from STEP, Rhino `.3dm` (via
[ImportExport\_3DM](https://github.com/KeithSloan/ImportExport_3DM)), or any other
source.

**Usage:**
1. Import a shape into FreeCAD (STEP, 3DM, etc.).
2. Select one or more of the imported objects in the 3D view or model tree.
3. Activate *Extract NURBS* from the **Misc.** menu or toolbar.

The command is only enabled when the selection contains at least one object with
`BSplineSurface` faces or `BSplineCurve` edges.

**What it does:**
- For every `BSplineSurface` face → creates a `NurbsSurface` `Part::FeaturePython`
  object with `FaceIndex` set so `execute()` copies the correctly-trimmed source face.
- For every `BSplineCurve` edge → creates a `NurbsCurve` `Part::FeaturePython` object.
- Non-NURBS geometry (planes, cones, lines, arcs) is silently skipped.
- Each source object is hidden after conversion.

**NurbsCurve stored properties (all editable):**

| Property | Type | Description |
|---|---|---|
| `Source` | Link | Reference to the original imported object |
| `Poles` | VectorList | Control point positions |
| `Weights` | FloatList | Weight for each pole |
| `Knots` | FloatList | Knot parameter values |
| `Multiplicities` | IntegerList | Multiplicity of each knot |
| `Degree` | Integer | Polynomial degree of the curve |
| `Periodic` | Bool | Whether the curve is closed/periodic |

The resulting object shape is an `Edge`, usable with any Curves tool that accepts an
edge (join, extend, split, discretize, blend, etc.).

**NurbsSurface stored properties (all editable):**

| Property | Type | Description |
|---|---|---|
| `Source` | Link | Reference to the original imported object |
| `FaceIndex` | Integer | Index into `Source.Shape.Faces` |
| `Poles` | VectorList | Control point grid, stored flat row-major (U × V) |
| `Weights` | FloatList | Weight for each pole, stored flat row-major |
| `NbPolesU` | Integer | Number of poles in the U direction |
| `NbPolesV` | Integer | Number of poles in the V direction |
| `KnotsU` | FloatList | Knot parameter values in U |
| `KnotsV` | FloatList | Knot parameter values in V |
| `MultsU` | IntegerList | Knot multiplicities in U |
| `MultsV` | IntegerList | Knot multiplicities in V |
| `DegreeU` | Integer | Polynomial degree in U |
| `DegreeV` | Integer | Polynomial degree in V |
| `PeriodicU` | Bool | Whether the surface is periodic in U |
| `PeriodicV` | Bool | Whether the surface is periodic in V |

The resulting object shape is a `Face`, usable with any Curves tool that accepts a
face (trim, iso-curve, zebra analysis, etc.).  `execute()` uses
`source.Shape.Faces[FaceIndex].copy()` rather than converting the stored NURBS data
back to an untrimmed shape, so the original trim boundary is preserved correctly.

---

### Import Sverchok NURBS JSON

**Command:** `Curves_ImportSverchokJSON`

Imports NURBS Curves and/or Surfaces from a JSON file exported by Blender's
[Sverchok](https://github.com/nortikin/sverchok) addon ("NURBS to JSON" node)
or any tool that writes the [geomdl/rw3dm](https://github.com/orbingol/rw3dm)
exchange format.

**Usage:**
1. In Blender with Sverchok, connect a NURBS Curve or Surface node to a
   "NURBS to JSON" node and export the `.json` file.
2. In FreeCAD, activate *Import Sverchok NURBS JSON* from the **Misc.** menu
   or toolbar.
3. A file dialog opens — select the `.json` file.

**What it does:**
- Reads the JSON file, which may contain a single object or a list of objects.
- Detects curves (have a `degree` key) vs surfaces (have `degree_u`/`degree_v`
  keys) automatically.
- Converts the full geomdl knot vector to the unique-knots + multiplicities
  format required by OCCT.
- Creates a `NurbsCurve` or `NurbsSurface` `Part::FeaturePython` object with
  the same editable properties as those produced by *Extract NURBS* above.

**JSON format (geomdl/Sverchok):**

*Curve:*
```json
{
  "degree": 3,
  "knotvector": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
  "control_points": [[x, y, z], ...],
  "weights": [1.0, ...],
  "closed": false
}
```

*Surface:*
```json
{
  "degree_u": 3, "degree_v": 3,
  "knotvector_u": [...], "knotvector_v": [...],
  "size_u": 4, "size_v": 4,
  "control_points": [[x, y, z], ...],
  "weights": [1.0, ...]
}
```

Both `weights` and `closed`/`closed_u`/`closed_v` are optional (defaults: all
weights 1.0, non-periodic).

---

## License  
CurvesWB is released under the LGPL2.1+ license. See [LICENSE](https://github.com/tomate44/CurvesWB/blob/main/LICENSES/LGPL-2.1.txt).
