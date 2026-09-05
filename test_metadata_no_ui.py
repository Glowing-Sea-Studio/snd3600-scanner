import os
import json
import piexif
import numpy as np
from PIL import Image

def test_exif_generation():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    pil_img = Image.fromarray(img)
    pil_img.save("test_out.jpg")

    meta_info = {"Software": "Test", "Cropped": True}
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: "SilverCrest",
            piexif.ImageIFD.ImageDescription: json.dumps(meta_info).encode("utf-8"),
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: "2023:01:01 12:00:00".encode("utf-8"),
        }
    }

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, "test_out.jpg")

    loaded = piexif.load("test_out.jpg")
    assert loaded["0th"][piexif.ImageIFD.Make] == b"SilverCrest"
    print("EXIF test OK")
    os.remove("test_out.jpg")

test_exif_generation()
