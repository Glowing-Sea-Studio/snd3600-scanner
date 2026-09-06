import unittest
import numpy as np
from snd3600_scanner.processing import auto_white_balance, apply_adjustments, generate_histogram

class TestProcessing(unittest.TestCase):
    def test_auto_white_balance(self):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        out = auto_white_balance(img)
        self.assertEqual(out.shape, (100, 100, 3))

    def test_apply_adjustments(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        params = {
            'zoom': 1.5,
            'rotation': 90,
            'flip_h': True,
            'flip_v': True,
            'exposure': 0.5,
            'contrast': 1.2,
            'brightness': 10,
            'temperature': -10,
            'tint': 15,
            'profile': 'Slide Film'
        }
        out = apply_adjustments(img, params)
        self.assertEqual(out.shape, (100, 100, 3))

    def test_generate_histogram(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        hist = generate_histogram(img, w=256, h=100)
        self.assertEqual(hist.shape, (100, 256, 3))

if __name__ == '__main__':
    unittest.main()
