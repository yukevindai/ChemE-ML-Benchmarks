"""Reproduce checked-in CSV snapshots and official SciSplit assignments.

Run from the repository root after installing .[dev]. Supply downloaded UCI ZIPs;
normal benchmark execution never downloads or changes data.
"""
import argparse
import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from cheme_benchmarks.common import canonical, csv_bytes, digest, write_json
from cheme_benchmarks.prepare import inspect, partition_record
from cheme_benchmarks.spec import load_data, validate_spec


def emit(root, slug, title, domain, data_kind, frame, numeric, categorical, target, units, source,
         unit_description, rationale, supports, limitations, split_config, accepted=None):
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=False)
    raw = csv_bytes(frame)
    (directory / "data.csv").write_bytes(raw)
    spec = {"schema_version": "1.0", "id": slug, "version": "1.0.0", "title": title, "domain": domain,
            "data_kind": data_kind, "task": "regression", "protocol": "cheme-tabular-v1",
            "data": {"path": "data.csv", "sha256": digest(raw), "row_id": "row_id", "rows": len(frame)},
            "features": {"numeric": numeric, "categorical": categorical}, "target": target, "units": units,
            "source": source, "independence": {"columns": ["group_id"], "unit": unit_description,
                "status": "synthetic" if data_kind == "synthetic" else "proxy", "rationale": rationale},
            "generalization": {"supports": supports, "does_not_establish": "Independent laboratory, publication, apparatus, chemistry-family or deployment transfer beyond the declared holdout."},
            "limitations": limitations, "split": dict(split_config, group_columns=["group_id"], target_column=target,
                diagnostics={"numeric_columns": numeric + [target]}),
            "partitions": {"path": "partitions.json", "sha256": "0" * 64},
            "audit": {"feature_columns": numeric + categorical, "target_column": target, "numeric_columns": numeric + [target],
                "duplicate_columns": numeric + categorical + [target], "provenance_columns": ["source_id", "group_id"]},
            "accepted_warnings": accepted or {}, "model_seeds": [0, 1, 2], "primary_metric": "group_mae"}
    data = load_data(spec, raw)
    # Domain-defined validity rules, not data-derived clipping or learned thresholds.
    spec["audit"]["bounds"] = {col: [0, None] for col in numeric if col != "angle"}
    if target not in {"sound_pressure", "objective"}:
        spec["audit"]["bounds"][target] = [0, 1] if target in {"retention", "conversion", "purity"} else [0, None]
    frozen, _ = partition_record(spec, data)
    write_json(directory / "partitions.json", frozen)
    spec["partitions"]["sha256"] = digest((directory / "partitions.json").read_bytes())
    validate_spec(spec)
    inspect(spec, data, frozen)
    write_json(directory / "benchmark.json", spec)
    lines = [f"# {title}", "", f"**{data_kind.upper()} DATA — version 1.0.0**", "", f"Domain: {domain}. Task: predict `{target}` ({units[target]}). Rows: {len(frame)}.", "",
        "## Source and curation", "", source["citation"], "", f"Source: {source['url']}", "", f"License: {source['license']}. Retrieved: {source['retrieved']}.", "",
        source["transformations"], "", f"Data SHA-256: `{digest(raw)}`", "", "## Independent unit", "", unit_description, "", rationale, "",
        "## Generalization", "", supports, "", spec["generalization"]["does_not_establish"], "", "## Features and units", "",
        "| Variable | Role | Unit |", "| --- | --- | --- |"]
    lines += [f"| {col} | numeric feature | {units[col]} |" for col in numeric]
    lines += [f"| {col} | categorical feature | category |" for col in categorical]
    lines += [f"| {target} | target | {units[target]} |", "", "Identifiers and source metadata are excluded from model features.", "",
        "## Evaluation", "", "Official assignments are frozen in partitions.json and regenerated with pinned SciSplit for verification. Preprocessing fits on training rows only. Validation selects fixed-grid hyperparameters; test evaluates the selected model without refitting. Primary metric: equal-group MAE. Report all model seeds 0, 1, and 2.", "",
        "## Limitations", ""]
    lines += ["- " + value for value in limitations]
    if accepted:
        lines += ["", "## Accepted Auditor warnings", ""] + [f"- `{k}`: {v}" for k, v in accepted.items()]
    (directory / "CARD.md").write_bytes(("\n".join(lines) + "\n").encode())
    print(slug, len(frame), "rows", {part: sum(a["partition"] == part for a in frozen["assignments"]) for part in ("train", "validation", "test")})


def empirical(root, downloads):
    archive = (downloads / "concrete.zip").read_bytes()
    with ZipFile(io.BytesIO(archive)) as z:
        frame = pd.read_excel(io.BytesIO(z.read("Concrete_Data.xls")))
    cols = ["cement", "slag", "fly_ash", "water", "superplasticizer", "coarse_aggregate", "fine_aggregate", "age", "strength"]
    frame.columns = cols
    numeric, target = cols[:-1], cols[-1]
    frame["group_id"] = ["recipe_" + digest(canonical([float(x) for x in row])) for row in frame[cols[:7]].itertuples(index=False, name=None)]
    frame["row_id"] = [f"uci165-{i + 1:04}" for i in range(len(frame))]
    frame["source_id"] = "10.24432/C5PK67"
    source = {"url": "https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength",
              "citation": "Yeh, I. (1998). Concrete Compressive Strength. UCI Machine Learning Repository. DOI: 10.24432/C5PK67.",
              "license": "CC-BY-4.0", "retrieved": "2026-09-07", "raw_sha256": digest(archive),
              "transformations": "Converted Concrete_Data.xls to UTF-8 CSV, renamed columns, retained all 1030 rows and numerical values, added source row IDs and SHA-256 recipe keys from the seven supplied ingredient quantities. No deduplication, imputation, target transformation, or unit conversion."}
    emit(root, "concrete-strength", "Concrete strength under composition holdout", "materials", "empirical", frame, numeric, [], target,
         {**{c: "kg/m^3" for c in cols[:7]}, "age": "day", "strength": "MPa"}, source,
         "Experimental unit should be an independently prepared/cured specimen or batch; original batch/specimen IDs are absent. The operational grouping proxy is the exact seven-component recipe, shared across curing ages.",
         "All observations with the same declared recipe stay together. This avoids testing the same recipe at another age, but does not establish independent experiments or resolve rounded near-identical recipes.",
         "Prediction for held-out exact concrete compositions within this source collection, conditional on supplied age and ingredients.",
         ["Batch, laboratory, study and specimen identities are unavailable; grouping is a conservative composition proxy, not documented experimental independence.",
          "Exact duplicate published records are retained; their experimental meaning is unknown. Equal-group metrics reduce between-recipe row-count weighting, but duplicates still affect within-recipe errors.",
          "Exact composition holdout does not ensure chemical distance, multivariate extrapolation, or transfer to new cement sources."],
         {"strategy": "composition", "columns": cols[:7], "validation_size": 0.2, "test_size": 0.2, "seed": 42},
         {"duplicate_samples": "Retain published observations because replicate/duplicate identities are not documented; composition grouping prevents these exact repeated records crossing partitions."})
    archive = (downloads / "airfoil.zip").read_bytes()
    with ZipFile(io.BytesIO(archive)) as z:
        frame = pd.read_csv(io.BytesIO(z.read("airfoil_self_noise.dat")), sep=r"\s+", header=None)
    cols = ["frequency", "angle", "chord", "velocity", "displacement_thickness", "sound_pressure"]
    frame.columns = cols
    numeric, target = cols[:-1], cols[-1]
    frame["group_id"] = ["condition_" + digest(canonical([float(x) for x in row])) for row in frame[cols[1:5]].itertuples(index=False, name=None)]
    frame["row_id"] = [f"uci291-{i + 1:04}" for i in range(len(frame))]
    frame["source_id"] = "10.24432/C5VW2C"
    source = {"url": "https://archive.ics.uci.edu/dataset/291/airfoil+self+noise",
              "citation": "Brooks, T., Pope, D., and Marcolini, M. (1989). Airfoil Self-Noise. UCI Machine Learning Repository. DOI: 10.24432/C5VW2C.",
              "license": "CC-BY-4.0", "retrieved": "2026-09-07", "raw_sha256": digest(archive),
              "transformations": "Converted the whitespace-delimited source file to CSV, renamed columns, retained all 1503 rows and numerical values, added row IDs and condition keys from angle/chord/velocity/displacement thickness. No feature/target scaling, row deletion, or unit conversion."}
    emit(root, "airfoil-noise", "Airfoil noise under chord-length extrapolation", "transport", "empirical", frame, numeric, [], target,
         dict(zip(cols, ["Hz", "degree", "m", "m/s", "m", "dB"])), source,
         "Experimental unit should be an independently acquired wind-tunnel condition/run, not each frequency-bin measurement. Run IDs are absent; supplied angle/chord/velocity/displacement-thickness tuples form the operational condition proxy.",
         "All frequency observations sharing a condition stay together. Chord extrapolation also keeps an entire nominal chord level in one partition.",
         "Prediction at chord lengths >0.2286 m, with validation at (0.1524,0.2286] m and training <=0.1524 m, within the supplied NACA 0012 collection.",
         ["No documented run, specimen, laboratory or publication IDs; condition groups cannot certify independent experimental replicates.",
          "NACA 0012 geometry family, source apparatus, span and observer settings limit transfer; this does not test arbitrary airfoils or transport laws.",
          "Target is the source's scaled sound-pressure value in dB, not an unscaled acoustic pressure or sound-power estimate."],
         {"strategy": "extrapolation", "columns": ["chord"], "threshold": 0.2286, "validation_threshold": 0.1524})


def synthetic(root):
    # These intentionally simplified equations are software fixtures, not validated constitutive models.
    cases = [
        ("battery-retention", "batteries", "cycle", "rate", "retention", "dimensionless", "dimensionless", "dimensionless", (10, 1000), (0.2, 3), lambda a,x,z: np.exp(-0.0005*a*x*z)),
        ("battery-life", "batteries", "rate", "temperature", "life", "dimensionless", "K", "dimensionless", (0.2,3), (280,330), lambda a,x,z: 1500/(a*x)*(300/z)),
        ("electrolyte-conductivity", "electrolytes", "concentration", "temperature", "conductivity", "mol/L", "K", "mS/cm", (0.1,2), (280,340), lambda a,x,z: a*10*x*np.exp(-(x-1.1)**2)*(z/298)),
        ("adsorption-isotherm", "adsorption", "pressure", "temperature", "uptake", "bar", "K", "mmol/g", (0.01,10), (280,350), lambda a,x,z: a*5*x*np.exp(1000*(1/z-1/298))/(1+x*np.exp(1000*(1/z-1/298)))),
        ("catalyst-conversion", "catalysis", "residence_time", "temperature", "conversion", "s", "K", "dimensionless", (0.1,10), (300,450), lambda a,x,z: 1-np.exp(-0.1*a*x*np.exp(-2500*(1/z-1/350)))),
        ("separation-purity", "separations", "feed_fraction", "stages", "purity", "dimensionless", "dimensionless", "dimensionless", (0.05,0.8), (1,8), lambda a,x,z: (1+a/4)**z*x/(1-x+(1+a/4)**z*x)),
        ("gas-volume", "thermodynamics", "temperature", "pressure", "molar_volume", "K", "Pa", "m^3/mol", (280,500), (1e5,1e6), lambda a,x,z: a*8.314462618*x/z),
        ("pipe-flow", "transport", "viscosity", "pressure_gradient", "flow", "Pa*s", "Pa/m", "m^3/s", (0.001,0.02), (100,10000), lambda a,x,z: np.pi*(a*0.001)**4*z/(8*x)),
        ("porous-modulus", "materials", "porosity", "temperature", "modulus", "dimensionless", "K", "GPa", (0.05,0.7), (280,400), lambda a,x,z: a*50*(1-x)**2*(1-0.0001*(z-298))),
        ("process-response", "process_optimization", "temperature", "residence_time", "objective", "K", "s", "dimensionless", (300,420), (0.1,5), lambda a,x,z: a*np.exp(-((x-350)/40)**2)*(1-np.exp(-z))-0.001*(x-298)),
    ]
    for index, (slug, domain, xname, zname, target, xu, zu, yu, xr, zr, formula) in enumerate(cases):
        rng = np.random.default_rng(100 + index)
        family = np.repeat(np.linspace(0.6, 1.6, 20), 5)
        x, z = rng.uniform(*xr, 100), rng.uniform(*zr, 100)
        frame = pd.DataFrame({"row_id": [f"{slug}-{i:03}" for i in range(100)],
            "group_id": [f"family-{i//5:02}" for i in range(100)], "family_parameter": family,
            xname: x, zname: z, "class": [f"class-{i//5%3}" for i in range(100)], target: formula(family,x,z), "source_id": "synthetic:" + slug})
        source = {"url": "https://github.com/yukevindai/ChemE-ML-Benchmarks/blob/feat/benchmark-suite/scripts/curate.py",
                  "citation": "ChemE ML Benchmarks contributors (2026), deterministic synthetic software fixture.",
                  "license": "MIT", "retrieved": "2026-09-07", "raw_sha256": digest(csv_bytes(frame)),
                  "transformations": f"Generated with NumPy seed {100+index}; 20 mathematical families, five draws each. Explicit toy equation is in scripts/curate.py. No measurements or empirical uncertainty; class is a synthetic categorical nuisance feature."}
        emit(root, "synthetic-" + slug, "SYNTHETIC: " + slug.replace("-", " "), domain, "synthetic", frame,
             ["family_parameter", xname, zname], ["class"], target, {"family_parameter": "dimensionless", xname: xu, zname: zu, target: yu}, source,
             "One generated mathematical parameter family (five related design points), not an experimental unit.",
             "The family ID is held intact to test the grouping mechanism. The family parameter is a declared numerical input, not an inferred sample identifier.",
             "Software behavior on held-out toy parameter values only; no real-world scientific performance claim.",
             ["Synthetic fixture, not experimental data and not eligible for an empirical leaderboard.",
              "Toy equations omit mechanisms, measurement error, confounding, and realistic source heterogeneity.",
              "Good performance cannot establish validity for the named chemical-engineering application."],
             {"strategy": "composition", "columns": ["family_parameter"], "validation_size": 0.2, "test_size": 0.2, "seed": 42},
             {"target_proxy": "Toy analytical dependence may cause strong feature-target correlation; formula inputs are explicitly declared and available at prediction time."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("benchmarks"))
    args = parser.parse_args()
    empirical(args.output, args.downloads)
    synthetic(args.output)
