import unittest
import types
import sys

if "ttkbootstrap" not in sys.modules:
    class _FakeStyle:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def configure(self, *args, **kwargs) -> None:
            pass

    sys.modules["ttkbootstrap"] = types.SimpleNamespace(Style=_FakeStyle)

from color_picker import (
    barycentric_weights,
    hsv_triangle_vertices,
    point_from_barycentric,
    sv_from_barycentric,
    weights_from_sv,
)


class TestHsvWheelMath(unittest.TestCase):
    def test_weights_and_sv_round_trip(self) -> None:
        for s, v in ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (0.5, 0.75), (0.8, 0.42)):
            weights = weights_from_sv(s, v)
            mapped_s, mapped_v = sv_from_barycentric(weights)
            self.assertAlmostEqual(mapped_s, s, places=5)
            self.assertAlmostEqual(mapped_v, v, places=5)

    def test_barycentric_point_round_trip(self) -> None:
        vertices = hsv_triangle_vertices(120.0, 120.0, 88.0, 210.0)
        expected_weights = weights_from_sv(0.62, 0.81)
        point = point_from_barycentric(vertices, expected_weights)
        recovered = barycentric_weights(point, vertices)
        for i in range(3):
            self.assertAlmostEqual(recovered[i], expected_weights[i], places=4)
        mapped_s, mapped_v = sv_from_barycentric(recovered)
        self.assertAlmostEqual(mapped_s, 0.62, places=4)
        self.assertAlmostEqual(mapped_v, 0.81, places=4)


if __name__ == "__main__":
    unittest.main()
