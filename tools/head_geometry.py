"""Read-only helper for the normalized LJ-X head geometry table.

It reports documented envelope values only; it never interpolates an X width.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "skill_data" / "hardware" / "head_specifications.yaml"
ENVELOPES = ROOT / "skill_data" / "hardware" / "installation_envelopes.yaml"


def assess(head_model: str, required_z_span_mm: float | None = None) -> dict:
    heads = json.loads(SPECS.read_text(encoding="utf-8"))["heads"]
    head = next((item for item in heads if item["model"] == head_model), None)
    if head is None:
        raise ValueError(f"Unknown normalized head: {head_model}")
    envelope = next(item for item in json.loads(ENVELOPES.read_text(encoding="utf-8"))["envelopes"] if item["head_id"] == head["head_id"])
    geometry = head["optical_geometry"]
    result = {
        "head": head_model,
        "reference_distance_mm": geometry["reference_distance"]["value"],
        "physical_distance_envelope_mm": {
            "nearest": envelope["nearest_surface_distance"]["value"],
            "farthest": envelope["farthest_surface_distance"]["value"],
            "status": "DERIVED_FROM_DIRECT_REFERENCE_AND_Z_BOUNDS",
        },
        "z_full_range_mm": geometry["z_range"]["value"],
        "documented_x_widths_mm": {
            "near": geometry["x_range_at_near"]["value"],
            "reference": geometry["x_range_at_reference"]["value"],
            "far": geometry["x_range_at_far"]["value"],
        },
        "intermediate_x_width": "NOT_DEFINED_NO_INTERPOLATION",
    }
    if required_z_span_mm is not None:
        result["required_z_span_mm"] = required_z_span_mm
        result["z_span_feasible"] = required_z_span_mm <= result["z_full_range_mm"]
        result["remaining_z_margin_mm"] = result["z_full_range_mm"] - required_z_span_mm
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect only the normalized, source-backed LJ-X head envelope.")
    parser.add_argument("--head", required=True, help="For example LJ-X8900")
    parser.add_argument("--required-z-span-mm", type=float)
    args = parser.parse_args()
    print(json.dumps(assess(args.head, args.required_z_span_mm), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
