import numpy as np
from snd3600_scanner.processing import apply_adjustments

frame = np.zeros((100, 100, 3), dtype=np.uint8)
params = {'crop_norm': [0.1, 0.1, 0.9, 0.9]}
out = apply_adjustments(frame, params, preview=False)
assert out.shape == (80, 80, 3)

out_preview = apply_adjustments(frame, params, preview=True)
assert out_preview.shape == (100, 100, 3)
print("Crop OK")
