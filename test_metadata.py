import os
import time
from tkinter import Tk, BooleanVar, StringVar, DoubleVar, IntVar
from snd3600_scanner.ui import ScannerApp
import numpy as np

# We'll just instantiate the app and mock camera logic
root = Tk()
app = ScannerApp(root)
app.output_dir.set(os.getcwd())
app.session_prefix.set("test_session")
app.format_var.set("JPEG")

# mock the frame
app.latest_frame = np.zeros((100, 100, 3), dtype=np.uint8)
app.running = True

# We mock piexif to prevent real writing and failing on missing camera
import unittest.mock
with unittest.mock.patch('snd3600_scanner.ui.Camera.grab_and_read', return_value=(True, app.latest_frame)):
    app.capture()

files = os.listdir(os.getcwd())
found = any(f.startswith("test_session_") and f.endswith(".jpeg") for f in files)
print(f"File generation: {'OK' if found else 'FAIL'}")

if found:
    for f in files:
        if f.startswith("test_session_"):
            os.remove(f)
