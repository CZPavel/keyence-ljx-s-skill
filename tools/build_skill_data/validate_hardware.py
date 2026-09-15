"""Validate source-backed LJ-X Series head normalization."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "skill_data"
MODELS = ["LJ-X8020", "LJ-X8030", "LJ-X8060", "LJ-X8070", "LJ-X8080", "LJ-X8100", "LJ-X8200", "LJ-X8300", "LJ-X8400", "LJ-X8900"]

def main() -> None:
    errors, warnings = [], []
    heads = json.loads((OUT / "hardware" / "head_specifications.yaml").read_text(encoding="utf-8"))["heads"]
    conditions = {x["condition_id"] for x in json.loads((OUT / "hardware" / "head_spec_conditions.yaml").read_text(encoding="utf-8"))["conditions"]}
    source = json.loads((OUT / "evidence" / "manual_source_blocks" / "MSB-LJX8000-379-X8900-SPECS.json").read_text(encoding="utf-8"))
    if source.get("model_columns") != MODELS or not source.get("visual_verified"):
        errors.append("source table model columns are not visually verified")
    if [x["model"] for x in heads] != MODELS or len({x["head_id"] for x in heads}) != 10:
        errors.append("canonical head IDs/models do not exactly match the ten source columns")
    for head in heads:
        geo = head["optical_geometry"]
        for key in ("reference_distance", "z_range", "x_range_at_near", "x_range_at_reference", "x_range_at_far"):
            value = geo.get(key, {})
            if not isinstance(value.get("value"), (int, float)) or value.get("unit") != "mm" or not value.get("evidence"):
                errors.append(f"{head['model']}: missing direct dimensional {key}")
        bounds = geo.get("measurement_distance_range", {})
        low, high = bounds.get("lower_z_relative", {}), bounds.get("upper_z_relative", {})
        if not all(isinstance(x.get("value"), (int, float)) and x.get("unit") == "mm" and x.get("evidence") for x in (low, high)):
            errors.append(f"{head['model']}: invalid direct Z bounds")
        elif geo["z_range"]["value"] != high["value"] - low["value"]:
            errors.append(f"{head['model']}: inconsistent Z full scale")
        if "relative to reference distance" not in geo.get("z_coordinate_convention", {}).get("source_mapping", ""):
            errors.append(f"{head['model']}: missing Z convention")
        sampling = head["sampling"]
        if sampling.get("profile_points", {}).get("value") != 3200 or not sampling["profile_points"].get("evidence"):
            errors.append(f"{head['model']}: profile point count lacks shared-table evidence")
        if sampling.get("profile_data_interval", {}).get("condition_ref") not in conditions:
            errors.append(f"{head['model']}: profile interval condition missing")
        for key in ("repeatability_z", "repeatability_x"):
            item = head["metrology"].get(key, {})
            if item.get("condition_ref") not in conditions or item.get("unit") != "um" or not item.get("evidence"):
                errors.append(f"{head['model']}: {key} lacks scoped direct evidence")
    envelopes = {x["head_id"]: x for x in json.loads((OUT / "hardware" / "installation_envelopes.yaml").read_text(encoding="utf-8"))["envelopes"]}
    for head in heads:
        env = envelopes.get(head["head_id"])
        if not env:
            errors.append(f"{head['model']}: missing installation envelope")
            continue
        geo = head["optical_geometry"]
        ref = geo["reference_distance"]["value"]
        low = geo["measurement_distance_range"]["lower_z_relative"]["value"]
        high = geo["measurement_distance_range"]["upper_z_relative"]["value"]
        if env.get("interpolation_policy") != "NOT_DEFINED": errors.append(f"{head['model']}: unsupported interpolation")
        for key, expected in (("nearest_surface_distance", ref + min(low, high)), ("farthest_surface_distance", ref + max(low, high))):
            item = env.get(key, {})
            if item.get("knowledge_status") != "DERIVED" or item.get("value") != expected:
                errors.append(f"{head['model']}: invalid derived {key}")
    x8900 = next((x for x in heads if x["model"] == "LJ-X8900"), None)
    if not x8900 or (x8900["optical_geometry"]["reference_distance"]["value"], x8900["optical_geometry"]["z_range"]["value"], x8900["optical_geometry"]["x_range_at_reference"]["value"]) != (980, 800, 510):
        errors.append("LJ-X8900 regression")
    relationships = json.loads((OUT / "hardware" / "controller_head_compatibility.yaml").read_text(encoding="utf-8"))["relationships"]
    if len(relationships) != 10 or {x["head"] for x in relationships} != {x["head_id"] for x in heads}:
        errors.append("compatibility records are not limited to canonical head IDs")
    if any(x["relation"] in {"COMPATIBLE", "NOT_COMPATIBLE"} and not x.get("direct_evidence") for x in relationships):
        errors.append("asserted compatibility lacks direct evidence")
    (OUT / "validation_hardware.md").write_text(f"# Hardware validation\n\nErrors: {len(errors)}. Warnings: {len(warnings)}. Heads with direct geometry: {len(heads)}.\n", encoding="utf-8")
    print(json.dumps({"errors": errors, "warnings": warnings, "heads": len(heads)}))
    if errors: raise SystemExit(1)

if __name__ == "__main__": main()
