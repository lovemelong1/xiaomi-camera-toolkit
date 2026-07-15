from pathlib import Path
from unittest import TestCase, main

from xiaomi_camera_toolkit.formats import parse_segment
from xiaomi_camera_toolkit.timelapse import weighted_targets


class FormatTests(TestCase):
    def test_flat_interval(self):
        segment = parse_segment(Path("/data/00_20260630000514_20260630001718.mp4"))
        self.assertIsNotNone(segment)
        self.assertEqual(segment.day, "20260630")
        self.assertEqual(segment.format_name, "flat_interval")

    def test_hourly_epoch(self):
        segment = parse_segment(Path("/data/2026032013/00M43S_1768395643.mp4"))
        self.assertIsNotNone(segment)
        self.assertEqual(segment.day, "20260320")
        self.assertEqual(segment.start.strftime("%H:%M:%S"), "13:00:43")
        self.assertEqual(segment.format_name, "hourly_epoch")

    def test_device_hourly_epoch(self):
        segment = parse_segment(Path("/data/607ea4aade93/2026032013/59M01S_1768395643.mp4"))
        self.assertIsNotNone(segment)
        self.assertEqual(segment.day, "20260320")
        self.assertEqual(segment.start.strftime("%H:%M:%S"), "13:59:01")

    def test_weighted_targets_cover_full_day(self):
        targets = weighted_targets("20260701", 30)
        self.assertEqual(len(targets), 30)
        self.assertLess(targets[0].hour, 6)
        self.assertGreaterEqual(targets[-1].hour, 18)


if __name__ == "__main__":
    main()
