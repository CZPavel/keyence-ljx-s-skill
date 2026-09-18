# LJ-X8000 PFRF protocol contract

Scope: LJ-X8000, 2D mode, Ethernet Non-Procedural communication. The target
LJ-X8900 head is compatible with this controller, but the repository has no
firmware-specific compatibility statement for controller firmware 2.3.0001.

## Contract

| Item | Contract | Evidence status | Canonical source |
|---|---|---|---|
| Transport | TCP, configurable Non-Procedural port; documented default `8500` | OFFICIAL_EXACT | `skill_data/communication/ethernet_nonprocedural.yaml`, manual block `MSB-LJX8000-202-NETWORK`, 2D manual p. 202 / printed 8-2 |
| Terminator | Configured delimiter: CR by default, CR+LF, or `All` with per-function delimiters | OFFICIAL_EXACT | same network record |
| Request forms | `PFRF,h`, `PFRF,h,t`, or `PFRF,h,s,m` followed by configured delimiter | OFFICIAL_EXACT | `skill_data/operations/command_reference.yaml`, manual block `MSB-LJX8000-231-PFRF`, 2D manual p. 231 / printed 9-9 |
| `h` | `1` = Head A or Wide; `2` = Head B | OFFICIAL_EXACT | PFRF record |
| `t` | thinning: `1` = 1/2, `2` = 1/4, `3` = 1/8 | OFFICIAL_EXACT | PFRF record |
| `s` | zero-based start position; left edge is `0` | OFFICIAL_EXACT | PFRF record |
| `m` | requested data-point count, `1..6400`; excess beyond available data is limited to the maximum obtainable points | OFFICIAL_EXACT | PFRF record |
| Parameter encoding | command and parameters are comma-separated ASCII; numeric examples/grammar are decimal, not binary fields | OFFICIAL_EXACT | PFRF request/response grammar |
| Normal response | `PFRF,n,pppp,pppp,...` followed by configured delimiter | OFFICIAL_EXACT | PFRF record |
| `n` | maximum number of acquired profile points returned in this response | OFFICIAL_EXACT | PFRF record |
| `pppp` | comma-separated ASCII actual-size profile value: up to 11 characters, sign/integer/decimal/fraction, integer zero suppression, four decimal places | OFFICIAL_EXACT | PFRF record |
| Binary/endian | Not applicable to this PFRF response: documented data are ASCII decimal | OFFICIAL_EXACT | PFRF response grammar |
| Invalid point | exact text `-99999.9999` | OFFICIAL_EXACT | PFRF record |
| Error response | `ER,**,nn`; `**` is received command and `nn` is a two-digit error code. For PFRF, `03` means “the specified head is not connected, etc., or there is no profile that can be obtained”; `22` means incorrect parameter count/value. | OFFICIAL_EXACT | PFRF source block `MSB-LJX8000-231-PFRF`, 2D manual p. 231 / printed 9-9 |
| Returned range | `PFRF,h,s,m` selects start and count; response may contain fewer than `m` only where the maximum obtainable count limits it | OFFICIAL_EXACT | PFRF parameter contract |
| Repeatability/safety | Canonical safety class is `READ_ONLY`; it does not change configuration. Execution temporarily stops current measurement. Continuous Trigger must be 500 Hz or lower to prevent background-buffer overflow. | OFFICIAL_EXACT | PFRF record and `skill_data/workflows/operational_workflows.yaml` |
| Firmware 2.3.0001 | No PFRF firmware-specific applicability record is present | UNRESOLVED | canonical PFRF record has family but no firmware range |

`RM` (read Run/Setup state) and `PR` (read active SD/program) are documented
READ_ONLY prechecks. The benchmark deliberately does not send them by default:
on a shared stream each extra request adds another opportunity for ambiguous
asynchronous output, and they are not required to encode PFRF.

## Conservative framing and asynchronous output

The controller separately configures asynchronous measurement-result output on
Ethernet Non-Procedural communication. The canonical workflow explicitly leaves
the exact correlation/interleaving contract between command responses and
asynchronous result output unresolved.

Therefore the benchmark:

1. uses the explicitly selected controller delimiter rather than TCP packet
   boundaries (with separate TX/RX delimiter options for `All` mode);
2. checks for unsolicited bytes before every request;
3. accepts only a first frame whose grammar begins with `PFRF` (or the exact
   PFRF error form);
4. rejects extra bytes received after the first delimiter in the same read;
5. stops after the first ambiguous, invalid, timeout, or controller-error frame.

This is a valid narrow PFRF line parser when the stream is not multiplexed. It is
not a general parser/correlator for a connection carrying asynchronous result
output. Use `--raw` first and disable or isolate asynchronous result output in the
controller configuration through the normal engineering process if captures
show multiplexing; this tool never changes that setting.

## Camera-event correlation

`--camera-fps` is a **DERIVED** PC-side simulator. It creates absolute,
monotonic host event targets from `time.perf_counter_ns()`; it neither triggers
the LJ-X nor changes its Continuous Trigger configuration. The resulting metric
`event_to_profile_available_ms` means *host camera event to complete arrival of
the latest profile returned by PFRF after that event*.

PFRF supplies no documented profile counter, acquisition timestamp, or other
identifier that links its returned profile to a particular camera event.
Therefore the real profile age and the exact relation to camera exposure remain
**UNRESOLVED**: this is host-event correlation, not verified camera/LJ-X
synchronization.

## Profile conversion and differences

The documented PFRF values are already actual-size decimal values, so the tool
preserves the exact `raw_z` text and parses `z` as a Python float only for local
calculation. It applies no invented scale factor. Invalid points become `NaN` in
CSV. `dZ[i]` and `d2Z[i]` are emitted only when every operand is valid, preventing
a derivative from bridging a missing point.

## Timing interpretation

All timestamps use `time.perf_counter_ns()`. `first_byte` is recorded on the
first successful `recv`; `response_complete` is recorded when the configured
delimiter is present. Consequently completion is exact only with respect to the
selected delimiter and the conservative one-frame contract above. TCP packet
arrival boundaries are never treated as message boundaries.
