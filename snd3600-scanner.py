#!/usr/bin/env python3
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageTk


APP = "SND 3600 Scanner"
DEFAULT_DEVICE = "/dev/video0"
DEFAULT_SIZE = (2592, 1944)


class ScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP)
        self.root.geometry("1200x820")
        self.root.minsize(900, 650)

        self.device = DEFAULT_DEVICE
        self.cap = None
        self.running = False
        self.latest = None
        self.display_image = None
        self.tk_image = None

        self.rotation = 0
        self.flip_h = tk.BooleanVar(value=False)
        self.flip_v = tk.BooleanVar(value=False)
        self.auto_color = tk.BooleanVar(value=True)
        self.save_negative = tk.BooleanVar(value=True)
        self.output_dir = tk.StringVar(
            value=str(Path.home() / "Images" / "Scanner-diapos")
        )
        self.format_var = tk.StringVar(value="JPEG")
        self.quality = tk.IntVar(value=95)
        self.exposure = tk.DoubleVar(value=0.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.brightness = tk.DoubleVar(value=0.0)
        self.zoom = tk.DoubleVar(value=1.0)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh_devices()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        self.preview = tk.Label(
            left, text="Connexion au SND 3600 A2…",
            bg="#151515", fg="white", anchor="center"
        )
        self.preview.pack(fill="both", expand=True)

        right = ttk.Frame(main, width=300)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        ttk.Label(right, text="SND 3600 A2", font=("TkDefaultFont", 16, "bold")).pack(
            anchor="w", pady=(0, 12)
        )

        ttk.Label(right, text="Périphérique").pack(anchor="w")
        dev_frame = ttk.Frame(right)
        dev_frame.pack(fill="x", pady=(0, 8))
        self.device_var = tk.StringVar(value=self.device)
        self.device_cb = ttk.Combobox(dev_frame, textvariable=self.device_var, state="readonly", width=12)
        self.device_cb.pack(side="left", fill="x", expand=True)
        self.device_cb.bind("<<ComboboxSelected>>", lambda e: self.change_device())
        ttk.Button(dev_frame, text="⟳", width=3, command=self.refresh_devices).pack(side="right", padx=(4, 0))
        
        ttk.Label(right, text="Résolution").pack(anchor="w")
        self.resolution = ttk.Combobox(
            right, values=["2592 × 1944", "2048 × 1536", "1600 × 1200"],
            state="readonly"
        )
        self.resolution.current(0)
        self.resolution.pack(fill="x", pady=(0, 12))
        self.resolution.bind("<<ComboboxSelected>>", self.change_resolution)

        ttk.Checkbutton(
            right, text="Négatif couleur / correction auto",
            variable=self.auto_color
        ).pack(anchor="w", pady=4)

        exp_frame = ttk.Frame(right)
        exp_frame.pack(fill="x", pady=(12, 0))
        ttk.Label(exp_frame, text="Exposition").pack(side="left")
        self.exposure_label = ttk.Label(exp_frame, text="0.00")
        self.exposure_label.pack(side="right")
        exp_slider_frame = ttk.Frame(right)
        exp_slider_frame.pack(fill="x")
        ttk.Button(exp_slider_frame, text="-", width=2, command=lambda: self.exposure.set(max(-3.0, self.exposure.get() - 0.1))).pack(side="left")
        ttk.Scale(exp_slider_frame, from_=-3.0, to=3.0, variable=self.exposure, command=lambda v: self.exposure_label.config(text=f"{float(v):.2f}")).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(exp_slider_frame, text="+", width=2, command=lambda: self.exposure.set(min(3.0, self.exposure.get() + 0.1))).pack(side="right")

        cont_frame = ttk.Frame(right)
        cont_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(cont_frame, text="Contraste").pack(side="left")
        self.contrast_label = ttk.Label(cont_frame, text="1.00")
        self.contrast_label.pack(side="right")
        cont_slider_frame = ttk.Frame(right)
        cont_slider_frame.pack(fill="x")
        ttk.Button(cont_slider_frame, text="-", width=2, command=lambda: self.contrast.set(max(0.1, self.contrast.get() - 0.1))).pack(side="left")
        ttk.Scale(cont_slider_frame, from_=0.1, to=3.0, variable=self.contrast, command=lambda v: self.contrast_label.config(text=f"{float(v):.2f}")).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(cont_slider_frame, text="+", width=2, command=lambda: self.contrast.set(min(3.0, self.contrast.get() + 0.1))).pack(side="right")

        bright_frame = ttk.Frame(right)
        bright_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(bright_frame, text="Luminosité").pack(side="left")
        self.brightness_label = ttk.Label(bright_frame, text="0.0")
        self.brightness_label.pack(side="right")
        bright_slider_frame = ttk.Frame(right)
        bright_slider_frame.pack(fill="x")
        ttk.Button(bright_slider_frame, text="-", width=2, command=lambda: self.brightness.set(max(-100.0, self.brightness.get() - 5.0))).pack(side="left")
        ttk.Scale(bright_slider_frame, from_=-100.0, to=100.0, variable=self.brightness, command=lambda v: self.brightness_label.config(text=f"{float(v):.1f}")).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(bright_slider_frame, text="+", width=2, command=lambda: self.brightness.set(min(100.0, self.brightness.get() + 5.0))).pack(side="right")

        zoom_frame = ttk.Frame(right)
        zoom_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(zoom_frame, text="Recadrage (Zoom)").pack(side="left")
        self.zoom_label = ttk.Label(zoom_frame, text="1.00x")
        self.zoom_label.pack(side="right")
        zoom_slider_frame = ttk.Frame(right)
        zoom_slider_frame.pack(fill="x")
        ttk.Button(zoom_slider_frame, text="-", width=2, command=lambda: self.zoom.set(max(1.0, self.zoom.get() - 0.05))).pack(side="left")
        ttk.Scale(zoom_slider_frame, from_=1.0, to=3.0, variable=self.zoom, command=lambda v: self.zoom_label.config(text=f"{float(v):.2f}x")).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(zoom_slider_frame, text="+", width=2, command=lambda: self.zoom.set(min(3.0, self.zoom.get() + 0.05))).pack(side="right")

        ttk.Label(right, text="Orientation").pack(anchor="w", pady=(12, 4))
        rot = ttk.Frame(right)
        rot.pack(fill="x", pady=0)
        ttk.Button(rot, text="↺ 90°", command=lambda: self.rotate(-90)).pack(
            side="left", fill="x", expand=True, padx=(0, 2)
        )
        ttk.Button(rot, text="90° ↻", command=lambda: self.rotate(90)).pack(
            side="left", fill="x", expand=True, padx=(2, 0)
        )
        
        flip_frame = ttk.Frame(right)
        flip_frame.pack(fill="x", pady=(4, 14))
        ttk.Checkbutton(flip_frame, text="Miroir ↔", variable=self.flip_h).pack(side="left", expand=True, anchor="center")
        ttk.Checkbutton(flip_frame, text="Miroir ↕", variable=self.flip_v).pack(side="left", expand=True, anchor="center")

        ttk.Separator(right).pack(fill="x", pady=8)

        ttk.Button(
            right, text="📷  NUMÉRISER", command=self.capture,
        ).pack(fill="x", ipady=8, pady=6)

        ttk.Checkbutton(
            right, text="Conserver le négatif original",
            variable=self.save_negative
        ).pack(anchor="w", pady=4)

        ttk.Label(right, text="Format de sortie").pack(anchor="w", pady=(12, 0))
        ttk.Combobox(
            right, textvariable=self.format_var,
            values=["JPEG", "PNG", "TIFF"], state="readonly"
        ).pack(fill="x")

        ttk.Label(right, text="Dossier").pack(anchor="w", pady=(12, 0))
        folder = ttk.Frame(right)
        folder.pack(fill="x")
        ttk.Entry(folder, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(folder, text="…", width=3, command=self.choose_folder).pack(side="right")

        self.status = ttk.Label(right, text="Initialisation…", wraplength=280)
        self.status.pack(anchor="w", pady=16)

        ttk.Label(
            right,
            text="V1 : acquisition UVC/V4L2 à 2592×1944, inversion couleur et correction automatique.",
            wraplength=280, foreground="#666666"
        ).pack(anchor="w", side="bottom", pady=8)

    def refresh_devices(self):
        import glob
        devices = sorted(glob.glob("/dev/video*"))
        if not devices:
            devices = ["/dev/video0"]
        self.device_cb['values'] = devices
        if self.device not in devices:
            self.device = devices[0]
            self.device_var.set(self.device)
        self.start_camera()

    def change_device(self):
        self.device = self.device_var.get()
        self.start_camera()

    def start_camera(self):
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.status.config(text=f"Impossible d'ouvrir {self.device}")
            self.preview.config(text="Scanner introuvable")
            return

        self.set_size(2592, 1944)
        self.running = True
        self.status.config(text="Scanner connecté — aperçu en direct")
        self.update_preview()

    def set_size(self, w, h):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))

    def change_resolution(self, _event=None):
        text = self.resolution.get()
        w, h = [int(x.strip()) for x in text.replace("×", "x").split("x")]
        self.set_size(w, h)

    def update_preview(self):
        if not self.running or self.cap is None:
            return

        ok, frame = self.cap.read()
        if ok:
            self.latest = frame
            preview = self.process(frame, preview=True)
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

            # Keep UI responsive by scaling only for display.
            h, w = preview.shape[:2]
            max_w, max_h = 850, 760
            scale = min(max_w / w, max_h / h, 1.0)
            if scale != 1.0:
                preview = cv2.resize(
                    preview, (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA
                )

            pil = Image.fromarray(preview)
            self.tk_image = ImageTk.PhotoImage(pil)
            self.preview.config(image=self.tk_image, text="")
        else:
            self.status.config(text="Lecture vidéo impossible")

        self.root.after(120, self.update_preview)

    def process(self, frame, preview=False):
        img = frame.copy()

        # Application du zoom / recadrage
        z = self.zoom.get()
        if z > 1.0:
            h, w = img.shape[:2]
            new_h, new_w = int(h / z), int(w / z)
            y1 = (h - new_h) // 2
            x1 = (w - new_w) // 2
            img = img[y1:y1+new_h, x1:x1+new_w]
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)

        # Rotation is applied before display/export.
        if self.rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif self.rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if self.flip_h.get():
            img = cv2.flip(img, 1)
        if self.flip_v.get():
            img = cv2.flip(img, 0)

        # The camera delivers a colour negative. Start with channel inversion.
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        rgb = 255.0 - rgb

        if self.auto_color.get():
            rgb = self.auto_white_balance(rgb)

        # Exposure in photographic stops.
        rgb *= 2.0 ** float(self.exposure.get())
        rgb = (rgb - 128.0) * float(self.contrast.get()) + 128.0
        rgb += float(self.brightness.get())
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    @staticmethod
    def auto_white_balance(rgb):
        # Les pellicules négatives couleur ont un "masque orange" (film de base).
        # Une simple inversion mathématique donne une image très bleue/cyan et délavée.
        # Cette méthode analyse chaque canal de couleur (Rouge, Vert, Bleu) séparément
        # et étire son histogramme (les valeurs sombres deviennent noires, les claires blanches).
        # Cela supprime la dominante de couleur et restaure le contraste naturel.
        
        # On calcule les valeurs min/max sur le centre de l'image pour ignorer les bords du film
        h, w = rgb.shape[:2]
        crop_y1, crop_y2 = int(h * 0.15), int(h * 0.85)
        crop_x1, crop_x2 = int(w * 0.15), int(w * 0.85)
        center = rgb[crop_y1:crop_y2, crop_x1:crop_x2]
        
        out = np.zeros_like(rgb)
        for i in range(3):
            channel = rgb[:, :, i]
            center_channel = center[:, :, i]
            
            # On utilise les centiles 1% et 99% du centre pour ignorer les valeurs extrêmes
            lo = np.percentile(center_channel, 1.0)
            hi = np.percentile(center_channel, 99.0)
            
            if hi > lo:
                # Étirement linéaire appliqué à toute l'image
                stretched = (channel - lo) * (255.0 / (hi - lo))
                out[:, :, i] = np.clip(stretched, 0, 255)
            else:
                out[:, :, i] = channel
        return out

    def rotate(self, degrees):
        self.rotation = (self.rotation + degrees) % 360

    def capture(self):
        if self.cap is None or self.latest is None:
            messagebox.showerror(APP, "Le scanner n'est pas disponible.")
            return

        # Grab a fresh frame at full configured resolution.
        self.cap.grab()
        ok, frame = self.cap.read()
        if not ok:
            messagebox.showerror(APP, "Impossible de capturer une image.")
            return

        outdir = Path(self.output_dir.get()).expanduser()
        outdir.mkdir(parents=True, exist_ok=True)

        stamp = time.strftime("%Y%m%d_%H%M%S")
        ext = self.format_var.get().lower()
        positive = self.process(frame, preview=False)

        positive_path = outdir / f"scan_{stamp}.{ext}"
        if ext == "jpeg":
            cv2.imwrite(str(positive_path), positive, [cv2.IMWRITE_JPEG_QUALITY, self.quality.get()])
        elif ext == "png":
            cv2.imwrite(str(positive_path), positive, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        else:
            cv2.imwrite(str(positive_path), positive)

        negative_path = None
        if self.save_negative.get():
            negative_path = outdir / f"scan_{stamp}_negative.png"
            cv2.imwrite(str(negative_path), frame)

        msg = f"Enregistré : {positive_path}"
        if negative_path:
            msg += f"\nNégatif : {negative_path}"
        self.status.config(text=msg)
        messagebox.showinfo(APP, msg)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def close(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.1)
    except Exception:
        pass
    app = ScannerApp(root)
    root.mainloop()
