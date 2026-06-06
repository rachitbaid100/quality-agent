import unittest

from quality_agent.local_runtime import mlx_status


class LocalRuntimeTest(unittest.TestCase):
    def test_mlx_status_shape(self):
        status = mlx_status()

        self.assertEqual(status["backend"], "mlx")
        self.assertIn("available", status)


if __name__ == "__main__":
    unittest.main()
