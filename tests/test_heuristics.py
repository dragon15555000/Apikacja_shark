import unittest

from app.utils.logic import (
    build_signature,
    normalize_gpu_string,
    normalize_viewport,
    find_top_3_matches,
)


class HeuristicsTests(unittest.TestCase):
    def test_normalize_gpu_string_removes_noise(self):
        self.assertEqual(
            normalize_gpu_string("Adreno (TM) 740 @ 680 MHz"),
            "adreno 740 680 mhz",
        )

    def test_normalize_viewport_rounds_near_integer(self):
        width, height = normalize_viewport(393.00001, 852)
        self.assertEqual(width, 393)
        self.assertEqual(height, 852)

    def test_build_signature_uses_normalized_viewport(self):
        signature = build_signature(393.00001, 852, 3.0, -1, 60, "apple gpu", "hash")
        self.assertTrue(signature.startswith("393_852_3.0_-1_60_"))

    def test_ios_collision_prefers_base_for_60hz(self):
        results = find_top_3_matches(
            393,
            852,
            60,
            "Apple GPU",
            3.0,
            -1,
            -1,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        )
        self.assertTrue(results)
        self.assertEqual(results[0]["model"], "iPhone 16")

    def test_ios_collision_prefers_pro_for_120hz(self):
        results = find_top_3_matches(
            393,
            852,
            120,
            "Apple GPU",
            3.0,
            -1,
            -1,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        )
        self.assertTrue(results)
        self.assertIn("Pro", results[0]["model"])


if __name__ == "__main__":
    unittest.main()
