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

## Importing NURBS Geometry from Rhino (.3dm) Files

The workbench includes two commands for converting NURBS geometry imported via the
[ImportExport\_3DM](https://github.com/KeithSloan/ImportExport_3DM) workbench into
fully editable Curves workbench objects.

The ImportExport\_3DM workbench uses the **rhino3dm** Python library to read Rhino
`.3dm` files.  The imported objects can be viewed in FreeCAD but are static — their
NURBS data cannot be edited directly.  The commands below wrap the imported geometry
in a parametric `Part::FeaturePython` object whose control-point poles, weights, knots
and multiplicities are stored as editable properties, making them available to all
other Curves workbench tools.

Both commands are found in the **Misc.** toolbar and menu.

---

### Import NURBS Curve

**Command:** `Curves_ImportNurbsCurve`

Converts an imported NURBS curve into an editable Curves workbench BSpline curve object.

**Usage:**
1. Import a `.3dm` file containing NURBS curves using the ImportExport\_3DM workbench.
2. Select one or more of the imported curve objects in the 3D view or model tree.
3. Activate *Import NURBS Curve* from the **Misc.** menu or toolbar.

**What it does:**
- Finds the first Edge in the selected object that contains a `BSplineCurve`.
- Extracts the full NURBS description: poles (control points), weights, knot vector,
  knot multiplicities, degree, and periodic flag.
- Creates a new `Part::FeaturePython` object whose `execute()` method reconstructs the
  `BSplineCurve` from the stored properties.
- Hides the original imported object.

**Stored properties (all editable):**

| Property | Type | Description |
|---|---|---|
| `Source` | Link | Reference to the original imported object |
| `Poles` | VectorList | Control point positions |
| `Weights` | FloatList | Weight for each pole |
| `Knots` | FloatList | Knot parameter values |
| `Multiplicities` | IntegerList | Multiplicity of each knot |
| `Degree` | Integer | Polynomial degree of the curve |
| `Periodic` | Bool | Whether the curve is closed/periodic |

The resulting object shape is an `Edge`, so it can be used directly with any Curves
workbench tool that accepts an edge (join, extend, split, discretize, blend, etc.).

---

### Import NURBS Surface

**Command:** `Curves_ImportNurbsSurface`

Converts an imported NURBS surface into an editable Curves workbench BSpline surface object.

**Usage:**
1. Import a `.3dm` file containing NURBS surfaces using the ImportExport\_3DM workbench.
2. Select one or more of the imported surface objects in the 3D view or model tree.
3. Activate *Import NURBS Surface* from the **Misc.** menu or toolbar.

**What it does:**
- Finds the first Face in the selected object that contains a `BSplineSurface`.
- Extracts the full NURBS description: the U×V pole grid, weights, knot vectors and
  multiplicities for both parametric directions, degrees, and periodicity flags.
- Creates a new `Part::FeaturePython` object whose `execute()` method reconstructs the
  `BSplineSurface` from the stored properties.
- Hides the original imported object.

**Stored properties (all editable):**

| Property | Type | Description |
|---|---|---|
| `Source` | Link | Reference to the original imported object |
| `Poles` | VectorList | Control point positions, stored row-major (U × V) |
| `Weights` | FloatList | Weight for each pole, stored row-major |
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

The resulting object shape is a `Face`, so it can be used directly with any Curves
workbench tool that accepts a face (trim, iso-curve, zebra analysis, etc.).

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
  the same editable properties as the *Import NURBS Curve/Surface* commands
  above.

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
