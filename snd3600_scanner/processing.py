import cv2
import numpy as np

def auto_white_balance(rgb):
    # Calculate min/max values on the center of the image to ignore film borders
    h, w = rgb.shape[:2]
    crop_y1, crop_y2 = int(h * 0.15), int(h * 0.85)
    crop_x1, crop_x2 = int(w * 0.15), int(w * 0.85)
    center = rgb[crop_y1:crop_y2, crop_x1:crop_x2]

    out = np.zeros_like(rgb)
    for i in range(3):
        channel = rgb[:, :, i]
        center_channel = center[:, :, i]

        # Use 1st and 99th percentiles to ignore extreme values
        lo = np.percentile(center_channel, 1.0)
        hi = np.percentile(center_channel, 99.0)

        if hi > lo:
            # Linear stretch applied to the whole image
            stretched = (channel - lo) * (255.0 / (hi - lo))
            out[:, :, i] = np.clip(stretched, 0, 255)
        else:
            out[:, :, i] = channel
    return out

def apply_adjustments(frame, params):
    """
    Applies zoom, rotation, flip, color conversion, white balance, exposure, contrast, brightness.
    Returns RGB image.
    """
    img = frame.copy()

    z = params.get('zoom', 1.0)
    if z > 1.0:
        h, w = img.shape[:2]
        new_h, new_w = int(h / z), int(w / z)
        y1 = (h - new_h) // 2
        x1 = (w - new_w) // 2
        img = img[y1:y1+new_h, x1:x1+new_w]
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)

    rotation = params.get('rotation', 0)
    if rotation == 90:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rotation == 270:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if params.get('flip_h', False):
        img = cv2.flip(img, 1)
    if params.get('flip_v', False):
        img = cv2.flip(img, 0)

    # Inversion
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)

    # Check profile
    profile = params.get('profile', 'Default')
    if profile != 'Default' and not params.get('is_positive', False):
        # We might have specific base masks here, for now just invert
        pass

    rgb = 255.0 - rgb

    if params.get('auto_color', True):
        rgb = auto_white_balance(rgb)

    # Temperature and Tint (White Balance)
    temp = params.get('temperature', 0.0) # -100 to 100
    tint = params.get('tint', 0.0)        # -100 to 100

    if temp != 0 or tint != 0:
        # Simple WB adjustment
        # Temp: negative = bluer, positive = redder/warmer
        # Tint: negative = greener, positive = magenter
        # Scale to manageable multiplier
        r_mult = 1.0 + (temp / 200.0) + (tint / 200.0)
        g_mult = 1.0 - (tint / 200.0)
        b_mult = 1.0 - (temp / 200.0)

        rgb[:,:,0] *= r_mult
        rgb[:,:,1] *= g_mult
        rgb[:,:,2] *= b_mult

    # Exposure in photographic stops.
    rgb *= 2.0 ** params.get('exposure', 0.0)
    rgb = (rgb - 128.0) * params.get('contrast', 1.0) + 128.0
    rgb += params.get('brightness', 0.0)

    # Profile color adjustments
    if profile == 'B&W':
        gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB).astype(np.float32)
    elif profile == 'Fuji Superia':
        # Slightly enhanced greens and reds
        rgb[:,:,1] *= 1.05
        rgb[:,:,0] *= 1.02
    elif profile == 'Kodak Gold':
        # Warmer tones
        rgb[:,:,0] *= 1.08
        rgb[:,:,1] *= 1.02
        rgb[:,:,2] *= 0.95
    elif profile == 'Portra':
        # Lower contrast, warmer skin tones (simplified)
        rgb = (rgb - 128.0) * 0.9 + 128.0
        rgb[:,:,0] *= 1.02
    elif profile == 'Slide Film':
        # High contrast, saturated
        rgb = (rgb - 128.0) * 1.15 + 128.0
        # Saturation boost (RGB -> HSV -> RGB)
        hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:,:,1] *= 1.2
        hsv[:,:,1] = np.clip(hsv[:,:,1], 0, 255)
        rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    return rgb

def generate_histogram(rgb_img, w=256, h=100):
    hist_img = np.zeros((h, w, 3), dtype=np.uint8)
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)] # R, G, B

    for i, col in enumerate(colors):
        hist = cv2.calcHist([rgb_img], [i], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, h, cv2.NORM_MINMAX)
        for x in range(256):
            val = int(hist[x][0]) if hist[x].ndim > 0 else int(hist[x])
            cv2.line(hist_img, (x, h), (x, h - val), col, 1)

    # Draw clipping warnings
    # Count pixels near 0 and 255
    clip_black = np.sum(rgb_img < 5) / rgb_img.size
    clip_white = np.sum(rgb_img > 250) / rgb_img.size

    if clip_black > 0.01:
        cv2.line(hist_img, (0, 0), (0, h), (0, 255, 255), 2) # Yellow warning for shadow clipping
    if clip_white > 0.01:
        cv2.line(hist_img, (w-1, 0), (w-1, h), (0, 255, 255), 2) # Yellow warning for highlight clipping

    return hist_img
