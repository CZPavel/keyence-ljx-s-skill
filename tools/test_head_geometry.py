"""Focused checks for the source-grounded head geometry helper."""
from head_geometry import assess

result = assess("LJ-X8900", 350)
assert result["z_span_feasible"] is True
assert result["remaining_z_margin_mm"] == 450
assert result["physical_distance_envelope_mm"] == {"nearest": 580, "farthest": 1380, "status": "DERIVED_FROM_DIRECT_REFERENCE_AND_Z_BOUNDS"}
assert result["intermediate_x_width"] == "NOT_DEFINED_NO_INTERPOLATION"
assert assess("LJ-X8900", 801)["z_span_feasible"] is False
print("head_geometry: ok")
