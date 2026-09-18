# Communication and control

Use canonical command, communication, signal, and workflow records under `skill_data/operations`, `skill_data/communication`, and `skill_data/workflows`. Distinguish request/response, profile data, measurement results, physical I/O, and fieldbus data. For a command, resolve token first; do not search the raw corpus before checking its status and family applicability.

For LJ-X8000 3D result integration, resolve `dataflow ljx8000-result-correlation`. It identifies documented result-context fields such as Number of Measurement, Execute No., Program No., and configured externally specified strings. Keep the asynchronous shared-connection parser contract marked unresolved; do not infer framing or silently treat skipped-tool output as a valid result.
