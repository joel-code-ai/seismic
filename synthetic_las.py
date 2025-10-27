#!/usr/bin/env python3
import numpy as np
import lasio
from datetime import date


def generate_synthetic_curves(
    n_points=2001,
    start_md=1000.0,
    stop_md=2000.0,
    null_value=-999.25,
    seed=42,
):
    rng = np.random.default_rng(seed)
    depth = np.round(np.linspace(start_md, stop_md, n_points), 3)

    gr = 80 + 15 * np.sin(depth / 20.0) + rng.normal(0, 5, n_points)
    rhob = 2.35 + 0.05 * np.sin(depth / 50.0) + rng.normal(0, 0.02, n_points)
    nphi = 0.30 + 0.05 * np.cos(depth / 30.0) + rng.normal(0, 0.01, n_points)

    # Introduce some nulls
    idx = rng.choice(n_points, size=30, replace=False)
    gr[idx[:10]] = null_value
    rhob[idx[10:20]] = null_value
    nphi[idx[20:]] = null_value

    return depth, {"GR": gr, "RHOB": rhob, "NPHI": nphi}, null_value


def build_las(depth, curves_dict, null_value):
    las = lasio.LASFile()
    # Version/Well headers
    las.version.VERS.value = 2.0
    las.version.WRAP.value = "NO"

    las.well.WELL.value = "SYN-1"
    las.well.COMP.value = "ExampleCo"
    las.well.FLD.value = "Synthetic"
    las.well.SRVC.value = "lasio"
    las.well.DATE.value = str(date.today())
    las.well.NULL.value = null_value
    las.well.STRT.value = float(depth[0])
    las.well.STOP.value = float(depth[-1])
    step = float(np.round(depth[1] - depth[0], 6)) if len(depth) > 1 else 0.0
    las.well.STEP.value = step

    # Curves
    las.append_curve("DEPT", depth, unit="m", descr="Measured Depth")
    las.append_curve("GR", curves_dict["GR"], unit="API", descr="Gamma Ray")
    las.append_curve("RHOB", curves_dict["RHOB"], unit="g/cc", descr="Bulk Density")
    las.append_curve("NPHI", curves_dict["NPHI"], unit="v/v", descr="Neutron Porosity")
    return las


def save_las(las, path="synthetic.las"):
    las.write(path, version=2.0)
    return path


def read_with_lasio(path="synthetic.las"):
    return lasio.read(path)


def main():
    depth, curves, null_value = generate_synthetic_curves()
    las = build_las(depth, curves, null_value)
    out = save_las(las, "/workspace/synthetic.las")
    print(f"Wrote {out} with {len(depth)} rows and curves: {list(las.keys())}")

    las_r = read_with_lasio(out)
    print(f"Read curves: {list(las_r.keys())}")
    print(f"WELL name: {las_r.well.WELL.value}, NULL: {las_r.well.NULL.value}")

    try:
        df = las_r.df()
        print(df.head(5))
        print(df.describe(include="all"))
    except Exception as e:
        print(f"DataFrame conversion failed: {e}")
        for c in las_r.curves:
            print(f"{c.mnemonic}: {c.data.shape}")


if __name__ == "__main__":
    main()
