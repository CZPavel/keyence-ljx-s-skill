import unittest

from ljx_pfrf_benchmark import (
    ControllerError,
    ProtocolError,
    add_differences,
    encode_pfrf,
    encode_pfrf_form,
    parse_pfrf,
    IterationResult,
    Timing,
    deadline_margin_ms,
    event_to_complete_ms,
    profile_preview,
)


class ProtocolTests(unittest.TestCase):
    def test_encode_range_request(self):
        self.assertEqual(encode_pfrf(1, 400, 1000, b"\r"), b"PFRF,1,400,1000\r")

    def test_encode_documented_diagnostic_forms(self):
        self.assertEqual(encode_pfrf_form(1, "h", b"\r"), b"PFRF,1\r")
        self.assertEqual(encode_pfrf_form(1, "h,t", b"\r"), b"PFRF,1,1\r")
        self.assertEqual(encode_pfrf_form(1, "h,s,m", b"\r"), b"PFRF,1,0,100\r")

    def test_parse_and_differences(self):
        points = parse_pfrf(b"PFRF,4,1.0000,2.5000,-99999.9999,5.0000", 4)
        self.assertEqual([p.z for p in points], [1.0, 2.5, None, 5.0])
        self.assertEqual(points[0].dz, 1.5)
        self.assertIsNone(points[1].dz)
        self.assertIsNone(points[0].d2z)

    def test_second_difference(self):
        points = parse_pfrf(b"PFRF,4,1.0000,2.0000,4.0000,7.0000", 4)
        self.assertEqual([p.dz for p in points], [1.0, 2.0, 3.0, None])
        self.assertEqual([p.d2z for p in points], [1.0, 1.0, None, None])

    def test_reject_async_or_unrelated_frame(self):
        with self.assertRaisesRegex(ProtocolError, "asynchronous"):
            parse_pfrf(b"1,OK,12.3", 1)

    def test_reject_wrong_count(self):
        with self.assertRaises(ProtocolError):
            parse_pfrf(b"PFRF,2,1.0000", 2)

    def test_accept_fewer_points_at_profile_end(self):
        points = parse_pfrf(b"PFRF,1,1.0000", 2)
        self.assertEqual(len(points), 1)

    def test_controller_error(self):
        with self.assertRaises(ControllerError):
            parse_pfrf(b"ER,PFRF,02", 10)

    def test_error_03_parses_as_controller_error(self):
        with self.assertRaisesRegex(ControllerError, "03"):
            parse_pfrf(b"ER,PFRF,03", 6400)

    def test_large_profile_preview_is_short(self):
        points = parse_pfrf(b"PFRF,7," + b",".join(f"+{i}.0000".encode() for i in range(7)), 7)
        self.assertEqual(
            profile_preview(points),
            (["+0.0000", "+1.0000", "+2.0000", "+3.0000", "+4.0000"],
             ["+2.0000", "+3.0000", "+4.0000", "+5.0000", "+6.0000"]),
        )

    def test_reject_non_decimal_error_code(self):
        with self.assertRaises(ProtocolError):
            parse_pfrf(b"ER,PFRF,xx", 10)

    def test_reject_noncanonical_profile_number(self):
        for value in (b"1e3", b"1.23456", b"1234567.0000"):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                parse_pfrf(b"PFRF,1," + value, 1)

    def test_profile_index_includes_start_point(self):
        points = parse_pfrf(b"PFRF,2,1.0000,2.0000", 2, start_point=400)
        self.assertEqual([p.index for p in points], [400, 401])

    def test_camera_event_metrics(self):
        timing = Timing(1_010_000, 1_020_000, 1_030_000, 1_050_000)
        result = IterationResult(1, "success", 10, 0.02, 0.04, 0.02,
                                 actual_event_ns=1_000_000, timing=timing,
                                 deadline_ns=1_100_000)
        self.assertEqual(event_to_complete_ms(result), 0.05)
        self.assertEqual(deadline_margin_ms(result), 0.05)


if __name__ == "__main__":
    unittest.main()
