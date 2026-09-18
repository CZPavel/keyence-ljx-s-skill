#!/usr/bin/env python3
"""Read-only LJ-X8000 PFRF latency benchmark (standard library only)."""

from __future__ import annotations

import argparse
import csv
import math
import re
import select
import socket
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_IP = "192.168.10.10"
DEFAULT_PORT = 8500
DEFAULT_SWEEP = (10, 50, 100, 200, 500, 1000, 3200)
DEFAULT_CAMERA_SWEEP = (100, 200, 300, 500, 1000, 3200)
INVALID_PROFILE_VALUE = "-99999.9999"
PROFILE_VALUE_RE = re.compile(r"^[+-]?\d+\.\d{4}$")
ERROR_CODE_RE = re.compile(r"^\d{2}$")


class ProtocolError(ValueError):
    """The received frame does not match the documented PFRF response."""


class ControllerError(ProtocolError):
    """The controller returned an ER response."""


PFRF_ERROR_TEXT = {
    "03": "specified head is not connected, etc., or there is no profile that can be obtained",
    "22": "number of parameters or parameter is incorrect",
}


@dataclass(frozen=True)
class Timing:
    send_start_ns: int
    send_end_ns: int
    first_byte_ns: int | None
    response_complete_ns: int | None

    def first_byte_ms(self) -> float | None:
        if self.first_byte_ns is None:
            return None
        return (self.first_byte_ns - self.send_start_ns) / 1_000_000

    def complete_ms(self) -> float | None:
        if self.response_complete_ns is None:
            return None
        return (self.response_complete_ns - self.send_start_ns) / 1_000_000

    def transfer_ms(self) -> float | None:
        if self.first_byte_ns is None or self.response_complete_ns is None:
            return None
        return (self.response_complete_ns - self.first_byte_ns) / 1_000_000


@dataclass(frozen=True)
class Exchange:
    tx: bytes
    rx: bytes
    timing: Timing
    extra_after_frame: bytes = b""


@dataclass(frozen=True)
class ProfilePoint:
    index: int
    raw_z: str
    z: float | None
    dz: float | None = None
    d2z: float | None = None


@dataclass
class IterationResult:
    iteration: int
    status: str
    response_bytes: int
    first_byte_ms: float | None
    complete_ms: float | None
    transfer_ms: float | None
    error: str = ""
    points: list[ProfilePoint] | None = None
    scheduled_event_ns: int | None = None
    actual_event_ns: int | None = None
    timing: Timing | None = None
    deadline_ns: int | None = None
    previous_send_start_ns: int | None = None
    tx: bytes = b""
    rx: bytes = b""


def encode_pfrf(head: int, start_point: int, points: int, delimiter: bytes) -> bytes:
    if head not in (1, 2):
        raise ValueError("head must be 1 (Head A/Wide) or 2 (Head B)")
    if start_point < 0:
        raise ValueError("start-point must be >= 0")
    if not 1 <= points <= 6400:
        raise ValueError("points must be in the documented range 1..6400")
    return f"PFRF,{head},{start_point},{points}".encode("ascii") + delimiter


def encode_pfrf_form(head: int, form: str, delimiter: bytes) -> bytes:
    """Encode only one of the three documented PFRF diagnostic forms."""
    if head not in (1, 2):
        raise ValueError("head must be 1 (Head A/Wide) or 2 (Head B)")
    commands = {"h": f"PFRF,{head}", "h,t": f"PFRF,{head},1", "h,s,m": f"PFRF,{head},0,100"}
    try:
        return commands[form].encode("ascii") + delimiter
    except KeyError as exc:
        raise ValueError(f"unsupported PFRF diagnostic form: {form}") from exc


def parse_pfrf(frame: bytes, requested_points: int, start_point: int = 0) -> list[ProfilePoint]:
    try:
        text = frame.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ProtocolError("response is not ASCII") from exc
    fields = text.split(",")
    if fields[0] == "ER":
        if len(fields) == 3 and fields[1] == "PFRF" and ERROR_CODE_RE.fullmatch(fields[2]):
            detail = PFRF_ERROR_TEXT.get(fields[2], "documented PFRF error")
            raise ControllerError(f"controller error for PFRF {fields[2]}: {detail}")
        raise ProtocolError(f"malformed or unrelated error response: {text!r}")
    if len(fields) < 2 or fields[0] != "PFRF":
        raise ProtocolError(f"unexpected frame (possible asynchronous output): {text!r}")
    try:
        declared = int(fields[1], 10)
    except ValueError as exc:
        raise ProtocolError("PFRF point count is not ASCII decimal") from exc
    values = fields[2:]
    if declared != len(values):
        raise ProtocolError(f"declared {declared} points but received {len(values)} values")
    if not 1 <= declared <= requested_points:
        raise ProtocolError(
            f"requested at most {requested_points} points but response declares {declared}"
        )

    points: list[ProfilePoint] = []
    for offset, raw in enumerate(values):
        index = start_point + offset
        if raw == INVALID_PROFILE_VALUE:
            z = None
        else:
            if len(raw) > 11 or not PROFILE_VALUE_RE.fullmatch(raw):
                raise ProtocolError(
                    f"profile value {index} violates documented decimal grammar: {raw!r}"
                )
            try:
                z = float(raw)
            except ValueError as exc:
                raise ProtocolError(f"profile value {index} is not documented decimal ASCII: {raw!r}") from exc
            if not math.isfinite(z):
                raise ProtocolError(f"profile value {index} is non-finite: {raw!r}")
        points.append(ProfilePoint(index=index, raw_z=raw, z=z))
    return add_differences(points)


def add_differences(points: Sequence[ProfilePoint]) -> list[ProfilePoint]:
    dz: list[float | None] = [None] * len(points)
    d2z: list[float | None] = [None] * len(points)
    for i in range(len(points) - 1):
        if points[i].z is not None and points[i + 1].z is not None:
            dz[i] = points[i + 1].z - points[i].z
    for i in range(len(points) - 2):
        if dz[i] is not None and dz[i + 1] is not None:
            d2z[i] = dz[i + 1] - dz[i]
    return [ProfilePoint(p.index, p.raw_z, p.z, dz[i], d2z[i]) for i, p in enumerate(points)]


class FramedTransport:
    def __init__(self, ip: str, port: int, timeout: float, response_delimiter: bytes):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.delimiter = response_delimiter
        self.sock: socket.socket | None = None
        self.pending = bytearray()

    def __enter__(self) -> "FramedTransport":
        self.sock = socket.create_connection((self.ip, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        return self

    def __exit__(self, *_: object) -> None:
        if self.sock is not None:
            self.sock.close()

    def _socket(self) -> socket.socket:
        if self.sock is None:
            raise RuntimeError("transport is not connected")
        return self.sock

    def detect_unsolicited(self) -> bytes:
        sock = self._socket()
        captured = bytes(self.pending)
        self.pending.clear()
        while True:
            readable, _, _ = select.select([sock], [], [], 0)
            if not readable:
                break
            chunk = sock.recv(65536)
            if not chunk:
                raise ConnectionError("controller closed the TCP connection")
            captured += chunk
        return captured

    def exchange(self, request: bytes) -> Exchange:
        unsolicited = self.detect_unsolicited()
        if unsolicited:
            raise ProtocolError(
                "unsolicited bytes were present before request (possible asynchronous result): "
                + unsolicited.hex(" ")
            )
        sock = self._socket()
        send_start = time.perf_counter_ns()
        sock.sendall(request)
        send_end = time.perf_counter_ns()
        first_byte: int | None = None
        response = bytearray()
        complete: int | None = None
        extra = b""
        while True:
            chunk = sock.recv(65536)
            now = time.perf_counter_ns()
            if not chunk:
                raise ConnectionError("controller closed the TCP connection before delimiter")
            if first_byte is None:
                first_byte = now
            response.extend(chunk)
            marker = response.find(self.delimiter)
            if marker >= 0:
                complete = now
                frame_end = marker + len(self.delimiter)
                extra = bytes(response[frame_end:])
                frame = bytes(response[:marker])
                if extra:
                    self.pending.extend(extra)
                return Exchange(
                    request,
                    frame,
                    Timing(send_start, send_end, first_byte, complete),
                    extra,
                )


def percentile(values: Sequence[float], percent: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percent / 100
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def ascii_repr(data: bytes) -> str:
    return "".join(chr(b) if 32 <= b <= 126 else f"\\x{b:02x}" for b in data)


def profile_preview(points: Sequence[ProfilePoint], count: int = 5) -> tuple[list[str], list[str]]:
    values = [p.raw_z for p in points]
    return values[:count], values[-count:]


def diagnose_pfrf(args: argparse.Namespace) -> int:
    tx_delimiter = delimiter_bytes(args.tx_delimiter or args.delimiter)
    rx_delimiter = delimiter_bytes(args.rx_delimiter or args.delimiter)
    forms = (("PFRF,h", "h"), ("PFRF,h,t", "h,t"), ("PFRF,h,s,m", "h,s,m"))
    outcomes: list[str] = []
    print("\n## LJ-X8000 PFRF availability diagnosis (READ_ONLY)\n")
    with FramedTransport(args.ip, args.port, args.timeout, rx_delimiter) as transport:
        for number, (label, form) in enumerate(forms, 1):
            request = encode_pfrf_form(args.head, form, tx_delimiter)
            print(f"\nTEST {number}/3\nRequest form: {label}")
            exchange: Exchange | None = None
            try:
                exchange = transport.exchange(request)
                print_raw(exchange, number)
                if exchange.extra_after_frame:
                    raise ProtocolError("Possible asynchronous result output detected. Extra bytes followed first frame.")
                decoded = parse_pfrf(exchange.rx, 6400, 0)
                first, last = profile_preview(decoded)
                print("Parsed result: SUCCESS")
                print(f"Reported point count: {len(decoded)}")
                print(f"Received point count: {len(decoded)}")
                print(f"First 5 values: {first}")
                print(f"Last 5 values:  {last}")
                outcomes.append("success")
            except ControllerError as exc:
                code = exchange.rx.decode("ascii").split(",")[2] if exchange else "unknown"
                if exchange:
                    print_raw(exchange, number)
                print("Parsed result: ERROR")
                print(f"Error code: {code}")
                print(f"Canonical meaning: {PFRF_ERROR_TEXT.get(code, 'documented PFRF error')}")
                outcomes.append(f"error:{code}")
            except socket.timeout:
                print("Parsed result: TIMEOUT")
                outcomes.append("timeout")
                break
            except (ProtocolError, ConnectionError, OSError) as exc:
                if exchange:
                    print_raw(exchange, number)
                print(f"Parsed result: INVALID\n{exc}")
                outcomes.append("invalid")
                break
    print("\nDiagnostic summary:")
    for i, value in enumerate(outcomes, 1): print(f"  TEST {i}: {value}")
    if outcomes == ["error:03"] * 3:
        print("Head 1/profile is not obtainable through PFRF in the current controller state/configuration, despite a visible RUN profile.")
    elif outcomes and outcomes[0] == "success" and any(x != "success" for x in outcomes[1:]):
        print("Profile is obtainable for Head 1. Failure is specific to the requested PFRF form/parameters.")
    return 0 if outcomes and all(x == "success" for x in outcomes) else 1


def print_raw(exchange: Exchange, number: int, result: IterationResult | None = None) -> None:
    def bounded(data: bytes, limit: int = 160) -> str:
        if len(data) <= limit:
            return ascii_repr(data)
        half = limit // 2
        return f"{ascii_repr(data[:half])} ... [truncated {len(data) - 2 * half} bytes] ... {ascii_repr(data[-half:])}"
    def bounded_hex(data: bytes, limit: int = 160) -> str:
        if len(data) <= limit:
            return data.hex(" ")
        half = limit // 2
        return f"{data[:half].hex(' ')} ... [truncated {len(data) - 2 * half} bytes] ... {data[-half:].hex(' ')}"
    print(f"\n--- RAW exchange {number} ---")
    print(f"TX ASCII: {ascii_repr(exchange.tx)}")
    print(f"TX HEX:   {exchange.tx.hex(' ')}")
    print(f"RX ASCII: {bounded(exchange.rx)}")
    print(f"RX HEX:   {bounded_hex(exchange.rx)}")
    print(f"RX byte count: {len(exchange.rx)}")
    if result and result.actual_event_ns is not None:
        print(f"Camera frame index: {result.iteration}")
        print(f"Scheduled event ns: {result.scheduled_event_ns}")
        print(f"Actual event ns:    {result.actual_event_ns}")
    print(f"Time to first byte: {exchange.timing.first_byte_ms():.3f} ms")
    print(f"Time to complete:   {exchange.timing.complete_ms():.3f} ms")
    if result and result.actual_event_ns is not None:
        print(f"Camera event -> complete data: {event_to_complete_ms(result):.3f} ms")
        print(f"Deadline margin: {deadline_margin_ms(result):.3f} ms")
    if exchange.extra_after_frame:
        print(f"WARNING: {len(exchange.extra_after_frame)} extra byte(s) followed the first frame")
        print(f"EXTRA HEX: {exchange.extra_after_frame.hex(' ')}")


def wait_until(target_ns: int) -> int:
    while True:
        now = time.perf_counter_ns()
        remaining = target_ns - now
        if remaining <= 0:
            return now
        time.sleep(min(remaining / 1_000_000_000, 0.001))


def event_to_complete_ms(r: IterationResult) -> float | None:
    if r.actual_event_ns is None or r.timing is None or r.timing.response_complete_ns is None:
        return None
    return (r.timing.response_complete_ns - r.actual_event_ns) / 1_000_000


def deadline_margin_ms(r: IterationResult) -> float | None:
    if r.deadline_ns is None or r.timing is None or r.timing.response_complete_ns is None:
        return None
    return (r.deadline_ns - r.timing.response_complete_ns) / 1_000_000


def run_size(args: argparse.Namespace, points: int, raw: bool = False) -> list[IterationResult]:
    tx_delimiter = delimiter_bytes(args.tx_delimiter or args.delimiter)
    rx_delimiter = delimiter_bytes(args.rx_delimiter or args.delimiter)
    request = encode_pfrf(args.head, args.start_point, points, tx_delimiter)
    count = min(args.iterations, args.raw_count) if raw else args.iterations
    results: list[IterationResult] = []
    with FramedTransport(args.ip, args.port, args.timeout, rx_delimiter) as transport:
        period_ns = int(1_000_000_000 / args.camera_fps) if args.camera_fps else None
        def do_cycle(iteration: int, scheduled: int | None, previous: int | None) -> IterationResult:
            actual = wait_until(scheduled) if scheduled is not None else None
            deadline = scheduled + period_ns if scheduled is not None and period_ns else None
            exchange: Exchange | None = None
            try:
                exchange = transport.exchange(request)
                r = IterationResult(iteration, "success", len(exchange.rx) + len(rx_delimiter),
                    exchange.timing.first_byte_ms(), exchange.timing.complete_ms(), exchange.timing.transfer_ms(),
                    points=parse_pfrf(exchange.rx, points, args.start_point), scheduled_event_ns=scheduled,
                    actual_event_ns=actual, timing=exchange.timing, deadline_ns=deadline,
                    previous_send_start_ns=previous, tx=exchange.tx, rx=exchange.rx)
                if exchange.extra_after_frame:
                    raise ProtocolError("additional bytes followed response delimiter; stream may be multiplexed")
                return r
            except socket.timeout:
                return IterationResult(iteration, "timeout", 0, None, None, None, "socket timeout", scheduled_event_ns=scheduled, actual_event_ns=actual, deadline_ns=deadline, previous_send_start_ns=previous)
            except ControllerError as exc:
                return result_from_failed_exchange(iteration, "controller_error", exc, exchange, rx_delimiter, scheduled, actual, deadline, previous)
            except (ProtocolError, ConnectionError, OSError) as exc:
                message = str(exc)
                if "unsolicited bytes" in message:
                    message = "Possible asynchronous result output detected. " + message
                return result_from_failed_exchange(iteration, "invalid", ProtocolError(message), exchange, rx_delimiter, scheduled, actual, deadline, previous)

        # Warm-up uses the same event cadence but is deliberately not reported.
        warm_start = time.perf_counter_ns()
        previous_send: int | None = None
        for n in range(args.warmup):
            warm = do_cycle(-(n + 1), warm_start + n * period_ns if period_ns else None, previous_send)
            if warm.timing:
                previous_send = warm.timing.send_start_ns
            if warm.status != "success":
                return [warm]
        start = time.perf_counter_ns()
        for iteration in range(1, count + 1):
            r = do_cycle(iteration, start + (iteration - 1) * period_ns if period_ns else None, previous_send)
            results.append(r)
            if raw and r.timing:
                print_raw(Exchange(r.tx, r.rx, r.timing), iteration, r)
            if args.verbose and results[-1].complete_ms is not None:
                print(f"{points} points #{iteration}: {results[-1].complete_ms:.3f} ms, {results[-1].response_bytes} B")
            if r.timing:
                previous_send = r.timing.send_start_ns
            if r.status != "success":
                break
            if args.delay > 0 and iteration < count:
                time.sleep(args.delay)
    return results


def result_from_failed_exchange(
    iteration: int,
    status: str,
    error: Exception,
    exchange: Exchange | None,
    delimiter: bytes,
    scheduled: int | None = None, actual: int | None = None, deadline: int | None = None, previous: int | None = None,
) -> IterationResult:
    if exchange is None:
        return IterationResult(iteration, status, 0, None, None, None, str(error), scheduled_event_ns=scheduled, actual_event_ns=actual, deadline_ns=deadline, previous_send_start_ns=previous)
    return IterationResult(
        iteration,
        status,
        len(exchange.rx) + len(delimiter),
        exchange.timing.first_byte_ms(),
        exchange.timing.complete_ms(),
        exchange.timing.transfer_ms(),
        str(error),
        scheduled_event_ns=scheduled, actual_event_ns=actual, timing=exchange.timing,
        deadline_ns=deadline, previous_send_start_ns=previous, tx=exchange.tx, rx=exchange.rx,
    )


def summarize(results: Sequence[IterationResult], elapsed_s: float) -> dict[str, float | int]:
    good = [r for r in results if r.status == "success" and r.complete_ms is not None]
    latency = [r.complete_ms for r in good if r.complete_ms is not None]
    sizes = [r.response_bytes for r in good]
    event_data = [event_to_complete_ms(r) for r in good if event_to_complete_ms(r) is not None]
    margins = [deadline_margin_ms(r) for r in good if deadline_margin_ms(r) is not None]
    return {
        "successful": len(good),
        "attempted": len(results),
        "failed": len(results) - len(good),
        "timeouts": sum(r.status == "timeout" for r in results),
        "invalid": sum(r.status == "invalid" for r in results),
        "min_ms": min(latency, default=math.nan),
        "mean_ms": statistics.fmean(latency) if latency else math.nan,
        "median_ms": statistics.median(latency) if latency else math.nan,
        "p90_ms": percentile(latency, 90),
        "p95_ms": percentile(latency, 95),
        "p99_ms": percentile(latency, 99),
        "max_ms": max(latency, default=math.nan),
        "requests_per_sec": len(good) / elapsed_s if elapsed_s > 0 else math.nan,
        "response_bytes": statistics.fmean(sizes) if sizes else math.nan,
        "throughput_kbps": sum(sizes) / elapsed_s / 1000 if elapsed_s > 0 else math.nan,
        "mean_event_to_data_ms": statistics.fmean(event_data) if event_data else math.nan,
        "min_event_to_data_ms": min(event_data, default=math.nan),
        "median_event_to_data_ms": statistics.median(event_data) if event_data else math.nan,
        "p90_event_to_data_ms": percentile(event_data, 90),
        "p95_event_to_data_ms": percentile(event_data, 95),
        "p99_event_to_data_ms": percentile(event_data, 99),
        "max_event_to_data_ms": max(event_data, default=math.nan),
        "min_deadline_margin_ms": min(margins, default=math.nan),
        "mean_deadline_margin_ms": statistics.fmean(margins) if margins else math.nan,
        "missed_deadlines": sum(m < 0 for m in margins),
    }


def print_summary(args: argparse.Namespace, points: int, summary: dict[str, float | int]) -> None:
    print("\n## LJ-X8000 PFRF benchmark\n")
    print(f"Controller:        {args.ip}:{args.port}")
    print(f"Points/request:    {points}")
    planned = min(args.iterations, args.raw_count) if args.raw else args.iterations
    print(f"Planned:           {planned}")
    print(f"Attempted:         {summary['attempted']}")
    print(f"Successful:        {summary['successful']}")
    print(f"Failed:            {summary['failed']}")
    print(f"Timeouts:          {summary['timeouts']}")
    print(f"Invalid responses: {summary['invalid']}")
    print("\nLatency (request send start -> complete response delimiter):")
    for label, key in (("Min", "min_ms"), ("Mean", "mean_ms"), ("Median", "median_ms"),
                       ("P90", "p90_ms"), ("P95", "p95_ms"), ("P99", "p99_ms"), ("Max", "max_ms")):
        print(f"{label + ':':18}{summary[key]:.3f} ms")
    print(f"\nWall-clock rate:   {summary['requests_per_sec']:.2f} successful requests/s")
    print(f"Response size:     {summary['response_bytes']:.1f} bytes/request")
    print(f"Throughput:        {summary['throughput_kbps']:.2f} kB/s")
    if args.camera_fps:
        print("\nCamera event -> complete PFRF data (host-event correlated):")
        for label, key in (("Min", "min_event_to_data_ms"), ("Mean", "mean_event_to_data_ms"),
                           ("Median", "median_event_to_data_ms"), ("P90", "p90_event_to_data_ms"),
                           ("P95", "p95_event_to_data_ms"), ("P99", "p99_event_to_data_ms"),
                           ("Max", "max_event_to_data_ms")):
            print(f"{label + ':':18}{summary[key]:.3f} ms")
        print(f"Minimum deadline margin: {summary['min_deadline_margin_ms']:.3f} ms")
        print(f"Mean deadline margin:    {summary['mean_deadline_margin_ms']:.3f} ms")
        print(f"Missed deadlines:        {summary['missed_deadlines']}")


def write_iteration_csv(path: Path, points: int, results: Sequence[IterationResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("points", "frame_index", "status", "scheduled_event_ns", "actual_event_ns", "request_send_start_ns", "request_send_end_ns", "first_byte_ns", "response_complete_ns", "scheduler_jitter_ms", "event_to_send_ms", "request_to_first_byte_ms", "request_to_complete_ms", "response_transfer_ms", "event_to_profile_available_ms", "deadline_margin_ms", "inter_request_period_ms", "response_bytes", "error"))
        for r in results:
            t=r.timing; event_send=(t.send_start_ns-r.actual_event_ns)/1e6 if t and r.actual_event_ns else None; jitter=(r.actual_event_ns-r.scheduled_event_ns)/1e6 if r.actual_event_ns and r.scheduled_event_ns else None; inter=(t.send_start_ns-r.previous_send_start_ns)/1e6 if t and r.previous_send_start_ns else None
            writer.writerow((points,r.iteration,r.status,r.scheduled_event_ns,r.actual_event_ns,t.send_start_ns if t else None,t.send_end_ns if t else None,t.first_byte_ns if t else None,t.response_complete_ns if t else None,jitter,event_send,r.first_byte_ms,r.complete_ms,r.transfer_ms,event_to_complete_ms(r),deadline_margin_ms(r),inter,r.response_bytes,r.error))


def write_profile_csv(path: Path, results: Sequence[IterationResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("camera_frame", "scheduled_timestamp_ns", "request_timestamp_ns", "response_timestamp_ns", "profile_index", "raw_z", "z", "dz", "d2z"))
        for r in results:
            if not r.points or not r.timing: continue
            for p in r.points:
                writer.writerow((r.iteration,r.scheduled_event_ns,r.timing.send_start_ns,r.timing.response_complete_ns,p.index,p.raw_z,"NaN" if p.z is None else p.z,"NaN" if p.dz is None else p.dz,"NaN" if p.d2z is None else p.d2z))


def delimiter_bytes(name: str) -> bytes:
    return {"cr": b"\r", "crlf": b"\r\n", "lf": b"\n"}[name]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Operational warning: PFRF does not change configuration, but each call temporarily "
            "stops current measurement. With Continuous Trigger, use 500 Hz or lower."
        ),
    )
    parser.add_argument("--ip", default=DEFAULT_IP)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--head", type=int, choices=(1, 2), default=1)
    parser.add_argument("--start-point", type=int, default=0)
    parser.add_argument("--points", type=int, default=100)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--delay", type=float, default=0.0, help="seconds between requests")
    parser.add_argument("--camera-fps", type=float, help="absolute monotonic simulated camera event rate")
    parser.add_argument("--warmup", type=int, default=10, help="unreported cycles before measurements")
    parser.add_argument("--delimiter", choices=("cr", "crlf", "lf"), default="cr",
                        help="common TX/RX delimiter (controller default: cr)")
    parser.add_argument("--tx-delimiter", choices=("cr", "crlf", "lf"),
                        help="override request delimiter for controller All mode")
    parser.add_argument("--rx-delimiter", choices=("cr", "crlf", "lf"),
                        help="override response delimiter for controller All mode")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--raw-count", type=int, default=3)
    parser.add_argument("--csv", type=Path, help="iteration CSV, or sweep summary CSV with --sweep")
    parser.add_argument("--profile-csv", type=Path, help="decoded final successful profile and dZ/d2Z")
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--camera-sweep", action="store_true", help="100..3200 points at --camera-fps cadence")
    parser.add_argument("--diagnose-pfrf", action="store_true", help="send PFRF,h; PFRF,h,t; PFRF,h,s,m once each")
    parser.add_argument("--verbose", action="store_true")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not 1 <= args.port <= 65535:
        raise ValueError("port must be 1..65535")
    if args.start_point < 0:
        raise ValueError("start-point must be >= 0")
    if not 1 <= args.points <= 6400:
        raise ValueError("points must be 1..6400")
    if args.iterations < 1 or args.raw_count < 1 or args.warmup < 0:
        raise ValueError("iterations/raw-count must be >= 1 and warmup must be >= 0")
    if args.timeout <= 0 or args.delay < 0:
        raise ValueError("timeout must be > 0 and delay must be >= 0")
    if args.camera_fps is not None and args.camera_fps <= 0:
        raise ValueError("camera-fps must be > 0")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
    except ValueError as exc:
        parser.error(str(exc))

    if (args.sweep or args.camera_sweep) and args.raw:
        parser.error("--raw cannot be used with a sweep")
    if args.sweep and args.camera_sweep:
        parser.error("--sweep and --camera-sweep are mutually exclusive")
    if args.camera_sweep and args.camera_fps is None:
        parser.error("--camera-sweep requires --camera-fps")
    if args.diagnose_pfrf and (args.sweep or args.camera_sweep or args.camera_fps):
        parser.error("--diagnose-pfrf cannot be combined with camera scheduling or sweeps")
    print(
        "WARNING: PFRF is configuration-read-only but temporarily stops current measurement; "
        "Continuous Trigger must be <=500 Hz.",
        file=sys.stderr,
    )
    if args.diagnose_pfrf:
        try:
            return diagnose_pfrf(args)
        except (ConnectionError, OSError) as exc:
            print(f"Connection failed for {args.ip}:{args.port}: {exc}", file=sys.stderr)
            return 2
    sizes = DEFAULT_CAMERA_SWEEP if args.camera_sweep else (DEFAULT_SWEEP if args.sweep else (args.points,))
    sweep_rows: list[dict[str, float | int]] = []
    all_results: list[tuple[int, list[IterationResult]]] = []
    exit_code = 0
    for points in sizes:
        started = time.perf_counter_ns()
        try:
            results = run_size(args, points, raw=args.raw)
        except (ConnectionError, OSError) as exc:
            print(f"Connection failed for {args.ip}:{args.port}: {exc}", file=sys.stderr)
            return 2
        elapsed_s = (time.perf_counter_ns() - started) / 1_000_000_000
        summary = summarize(results, elapsed_s)
        print_summary(args, points, summary)
        for failed in (r for r in results if r.status != "success"):
            print(f"Request {failed.iteration}: {failed.status}: {failed.error}", file=sys.stderr)
        sweep_rows.append({"points": points, **summary})
        all_results.append((points, results))
        if summary["failed"]:
            exit_code = 1
            if args.sweep or args.camera_sweep:
                print("Sweep stopped after failure to avoid sending further ambiguous requests.", file=sys.stderr)
                break

    if args.csv:
        if args.sweep or args.camera_sweep:
            with args.csv.open("w", newline="", encoding="utf-8") as handle:
                fields = ("points", "attempted", "successful", "failed", "timeouts", "invalid",
                          "mean_ms", "median_ms", "p95_ms", "p99_ms", "max_ms",
                          "requests_per_sec", "response_bytes", "failure_status",
                          "failure_first_byte_ms", "failure_complete_ms",
                          "failure_transfer_ms", "failure_response_bytes", "error",
                          "min_event_to_data_ms", "mean_event_to_data_ms", "median_event_to_data_ms",
                          "p90_event_to_data_ms", "p95_event_to_data_ms", "p99_event_to_data_ms",
                          "max_event_to_data_ms", "min_deadline_margin_ms", "mean_deadline_margin_ms", "missed_deadlines")
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for row, (_, results) in zip(sweep_rows, all_results):
                    failed = next((r for r in results if r.status != "success"), None)
                    writer.writerow({
                        **row,
                        "failure_status": failed.status if failed else "",
                        "failure_first_byte_ms": failed.first_byte_ms if failed else "",
                        "failure_complete_ms": failed.complete_ms if failed else "",
                        "failure_transfer_ms": failed.transfer_ms if failed else "",
                        "failure_response_bytes": failed.response_bytes if failed else "",
                        "error": failed.error if failed else "",
                    })
        else:
            write_iteration_csv(args.csv, all_results[0][0], all_results[0][1])

    if args.profile_csv:
        all_profile_results = [r for _, results in all_results for r in results if r.points]
        if all_profile_results:
            write_profile_csv(args.profile_csv, all_profile_results)
        else:
            print("Profile CSV was not written: no valid decoded profile.", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
