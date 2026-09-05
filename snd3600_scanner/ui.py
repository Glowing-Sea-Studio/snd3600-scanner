import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import time
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import sv_ttk

from .camera import Camera
from .processing import apply_adjustments, generate_histogram
from .profiles import get_default_profiles, load_profiles, save_profile

APP = "SND 3600 Scanner"

class ScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP)
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        sv_ttk.set_theme("dark")

        self.camera = Camera()
        self.running = False
        self.latest_frame = None

        self.batch_running = False
        self.batch_timer = None

        self._init_vars()
        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh_devices()

        self._setup_hotkeys()

    def _init_vars(self):
        self.device_var = tk.StringVar(value="/dev/video0")
        self.resolution = tk.StringVar(value="2592 × 1944")

        self.rotation = 0
        self.flip_h = tk.BooleanVar(value=False)
        self.flip_v = tk.BooleanVar(value=False)

        self.auto_color = tk.BooleanVar(value=True)
        self.profile_var = tk.StringVar(value="Default")

        self.exposure = tk.DoubleVar(value=0.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.brightness = tk.DoubleVar(value=0.0)
        self.temperature = tk.DoubleVar(value=0.0)
        self.tint = tk.DoubleVar(value=0.0)
        self.zoom = tk.DoubleVar(value=1.0)

        self.save_negative = tk.BooleanVar(value=True)
        self.output_dir = tk.StringVar(value=str(Path.home() / "Images" / "Scanner-diapos"))
        self.format_var = tk.StringVar(value="JPEG")
        self.quality = tk.IntVar(value=95)

        self.batch_interval = tk.IntVar(value=5)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        # Left panel: Preview + Histogram
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        self.preview = tk.Label(left, text="Connexion au SND 3600 A2…", bg="#151515", fg="white", anchor="center")
        self.preview.pack(fill="both", expand=True)

        self.hist_label = tk.Label(left, bg="#151515")
        self.hist_label.pack(fill="x", pady=(10, 0))

        # Right panel: Controls
        right = ttk.Frame(main, width=350)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        ttk.Label(right, text="SND 3600 Scanner Pro", font=("TkDefaultFont", 18, "bold")).pack(anchor="w", pady=(0, 12))

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Basic
        tab_basic = ttk.Frame(notebook, padding=10)
        notebook.add(tab_basic, text="Basic")
        self._build_basic_tab(tab_basic)

        # Tab 2: Advanced
        tab_adv = ttk.Frame(notebook, padding=10)
        notebook.add(tab_adv, text="Advanced")
        self._build_advanced_tab(tab_adv)

        # Tab 3: Workflow
        tab_workflow = ttk.Frame(notebook, padding=10)
        notebook.add(tab_workflow, text="Workflow")
        self._build_workflow_tab(tab_workflow)

        # Action area
        action_frame = ttk.Frame(right)
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="📷  NUMÉRISER (Space)", command=self.capture, style="Accent.TButton").pack(fill="x", ipady=8)

        self.status = ttk.Label(right, text="Initialisation…", wraplength=320)
        self.status.pack(anchor="w", pady=5)

    def _build_basic_tab(self, parent):
        ttk.Label(parent, text="Périphérique").pack(anchor="w", pady=(0,2))
        dev_frame = ttk.Frame(parent)
        dev_frame.pack(fill="x", pady=(0, 10))
        self.device_cb = ttk.Combobox(dev_frame, textvariable=self.device_var, state="readonly")
        self.device_cb.pack(side="left", fill="x", expand=True)
        self.device_cb.bind("<<ComboboxSelected>>", lambda e: self.change_device())
        ttk.Button(dev_frame, text="⟳", width=3, command=self.refresh_devices).pack(side="right", padx=(4, 0))

        ttk.Label(parent, text="Profil Couleur").pack(anchor="w")
        profiles = get_default_profiles() + list(load_profiles().keys())
        self.profile_cb = ttk.Combobox(parent, textvariable=self.profile_var, values=profiles, state="readonly")
        self.profile_cb.pack(fill="x", pady=(0, 10))
        self.profile_cb.bind("<<ComboboxSelected>>", self.on_profile_selected)

        ttk.Checkbutton(parent, text="Correction auto (Négatif)", variable=self.auto_color).pack(anchor="w", pady=(0, 10))

        self._add_slider(parent, "Exposition", self.exposure, -3.0, 3.0, "0.2f", 0.1)
        self._add_slider(parent, "Contraste", self.contrast, 0.1, 3.0, "0.2f", 0.1)
        self._add_slider(parent, "Luminosité", self.brightness, -100.0, 100.0, "0.1f", 5.0)
        self._add_slider(parent, "Recadrage (Zoom)", self.zoom, 1.0, 3.0, "0.2fx", 0.05)

        ttk.Label(parent, text="Orientation").pack(anchor="w", pady=(10, 4))
        rot = ttk.Frame(parent)
        rot.pack(fill="x")
        ttk.Button(rot, text="↺ 90°", command=lambda: self.rotate(-90)).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(rot, text="90° ↻", command=lambda: self.rotate(90)).pack(side="left", fill="x", expand=True, padx=(2, 0))

        flip_frame = ttk.Frame(parent)
        flip_frame.pack(fill="x", pady=(4, 10))
        ttk.Checkbutton(flip_frame, text="Miroir ↔", variable=self.flip_h).pack(side="left", expand=True)
        ttk.Checkbutton(flip_frame, text="Miroir ↕", variable=self.flip_v).pack(side="left", expand=True)

    def _build_advanced_tab(self, parent):
        ttk.Label(parent, text="Balance des blancs").pack(anchor="w", pady=(0, 10))
        self._add_slider(parent, "Température", self.temperature, -100.0, 100.0, "0.1f", 5.0)
        self._add_slider(parent, "Teinte", self.tint, -100.0, 100.0, "0.1f", 5.0)

        ttk.Separator(parent).pack(fill="x", pady=15)
        ttk.Label(parent, text="Gestion des profils").pack(anchor="w", pady=(0, 5))

        prof_frame = ttk.Frame(parent)
        prof_frame.pack(fill="x")
        ttk.Button(prof_frame, text="Sauvegarder Profil", command=self.save_current_profile).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(prof_frame, text="Réinitialiser", command=self.reset_adjustments).pack(side="left", fill="x", expand=True, padx=(2, 0))

    def _build_workflow_tab(self, parent):
        ttk.Label(parent, text="Dossier de sortie").pack(anchor="w", pady=(0, 2))
        folder = ttk.Frame(parent)
        folder.pack(fill="x", pady=(0, 10))
        ttk.Entry(folder, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(folder, text="…", width=3, command=self.choose_folder).pack(side="right", padx=(4,0))

        ttk.Label(parent, text="Format").pack(anchor="w")
        ttk.Combobox(parent, textvariable=self.format_var, values=["JPEG", "PNG", "TIFF"], state="readonly").pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(parent, text="Conserver le négatif original", variable=self.save_negative).pack(anchor="w", pady=(0, 15))

        ttk.Label(parent, text="Mode Batch").pack(anchor="w", pady=(0, 5))
        batch_f = ttk.Frame(parent)
        batch_f.pack(fill="x", pady=(0, 10))
        ttk.Label(batch_f, text="Intervalle (s):").pack(side="left")
        ttk.Spinbox(batch_f, from_=2, to=60, textvariable=self.batch_interval, width=5).pack(side="left", padx=5)
        self.batch_btn = ttk.Button(batch_f, text="Démarrer Batch", command=self.toggle_batch)
        self.batch_btn.pack(side="right")

    def _add_slider(self, parent, label_text, var, vmin, vmax, fmt, step):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text=label_text).pack(side="left")
        val_label = ttk.Label(frame, text=f"{var.get():{fmt}}")
        val_label.pack(side="right")

        s_frame = ttk.Frame(parent)
        s_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(s_frame, text="-", width=2, command=lambda: var.set(max(vmin, var.get() - step))).pack(side="left")
        scale = ttk.Scale(s_frame, from_=vmin, to=vmax, variable=var, command=lambda v: val_label.config(text=f"{float(v):{fmt}}"))
        scale.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(s_frame, text="+", width=2, command=lambda: var.set(min(vmax, var.get() + step))).pack(side="right")

    def _setup_hotkeys(self):
        self.root.bind("<space>", lambda e: self.capture())
        self.root.bind("<Left>", lambda e: self.exposure.set(max(-3.0, self.exposure.get() - 0.1)))
        self.root.bind("<Right>", lambda e: self.exposure.set(min(3.0, self.exposure.get() + 0.1)))
        self.root.bind("<Up>", lambda e: self.contrast.set(min(3.0, self.contrast.get() + 0.1)))
        self.root.bind("<Down>", lambda e: self.contrast.set(max(0.1, self.contrast.get() - 0.1)))

    def refresh_devices(self):
        devices = self.camera.get_devices()
        self.device_cb['values'] = devices
        if self.device_var.get() not in devices:
            self.device_var.set(devices[0])
        self.change_device()

    def change_device(self):
        dev = self.device_var.get()
        self.camera.device = dev
        if self.camera.start():
            self.running = True
            self.status.config(text="Scanner connecté — aperçu en direct")
            self.update_preview()
        else:
            self.status.config(text=f"Impossible d'ouvrir {dev}")
            self.preview.config(text="Scanner introuvable")

    def get_params(self):
        return {
            'zoom': self.zoom.get(),
            'rotation': self.rotation,
            'flip_h': self.flip_h.get(),
            'flip_v': self.flip_v.get(),
            'auto_color': self.auto_color.get(),
            'exposure': self.exposure.get(),
            'contrast': self.contrast.get(),
            'brightness': self.brightness.get(),
            'temperature': self.temperature.get(),
            'tint': self.tint.get(),
            'profile': self.profile_var.get()
        }

    def reset_adjustments(self):
        self.exposure.set(0.0)
        self.contrast.set(1.0)
        self.brightness.set(0.0)
        self.temperature.set(0.0)
        self.tint.set(0.0)
        self.zoom.set(1.0)
        self.rotation = 0
        self.flip_h.set(False)
        self.flip_v.set(False)
        self.auto_color.set(True)
        self.profile_var.set("Default")

    def on_profile_selected(self, event=None):
        profile_name = self.profile_var.get()
        if profile_name in get_default_profiles():
            # For built-in profiles, we just set the profile name and let processing.py handle it.
            # We don't overwrite user adjustments.
            pass
        else:
            profiles = load_profiles()
            if profile_name in profiles:
                params = profiles[profile_name]
                if 'zoom' in params: self.zoom.set(params['zoom'])
                if 'rotation' in params: self.rotation = params['rotation']
                if 'flip_h' in params: self.flip_h.set(params['flip_h'])
                if 'flip_v' in params: self.flip_v.set(params['flip_v'])
                if 'auto_color' in params: self.auto_color.set(params['auto_color'])
                if 'exposure' in params: self.exposure.set(params['exposure'])
                if 'contrast' in params: self.contrast.set(params['contrast'])
                if 'brightness' in params: self.brightness.set(params['brightness'])
                if 'temperature' in params: self.temperature.set(params['temperature'])
                if 'tint' in params: self.tint.set(params['tint'])

    def save_current_profile(self):
        name = tk.simpledialog.askstring("Profil", "Nom du profil:", parent=self.root)
        if name:
            save_profile(name, self.get_params())
            profiles = get_default_profiles() + list(load_profiles().keys())
            self.profile_cb['values'] = profiles
            self.profile_var.set(name)
            messagebox.showinfo(APP, f"Profil '{name}' sauvegardé.")

    def rotate(self, degrees):
        self.rotation = (self.rotation + degrees) % 360

    def update_preview(self):
        if not self.running:
            return

        ok, frame = self.camera.read()
        if ok:
            self.latest_frame = frame
            params = self.get_params()
            processed = apply_adjustments(frame, params)

            # Histogram
            hist_img = generate_histogram(processed, w=256, h=60)
            hist_pil = Image.fromarray(hist_img)
            self.tk_hist = ImageTk.PhotoImage(hist_pil)
            self.hist_label.config(image=self.tk_hist)

            # Preview scaling
            h, w = processed.shape[:2]
            max_w, max_h = 1000, 800
            scale = min(max_w / w, max_h / h, 1.0)
            if scale != 1.0:
                processed = cv2.resize(processed, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            pil = Image.fromarray(processed)
            self.tk_image = ImageTk.PhotoImage(pil)
            self.preview.config(image=self.tk_image, text="")
        else:
            self.status.config(text="Lecture vidéo impossible")

        self.root.after(100, self.update_preview)

    def capture(self):
        if not self.running or self.latest_frame is None:
            messagebox.showerror(APP, "Le scanner n'est pas disponible.")
            return

        ok, frame = self.camera.grab_and_read()
        if not ok:
            frame = self.latest_frame # fallback

        outdir = Path(self.output_dir.get()).expanduser()
        outdir.mkdir(parents=True, exist_ok=True)

        stamp = time.strftime("%Y%m%d_%H%M%S")
        ext = self.format_var.get().lower()
        positive = apply_adjustments(frame, self.get_params())
        positive_bgr = cv2.cvtColor(positive, cv2.COLOR_RGB2BGR)

        positive_path = outdir / f"scan_{stamp}.{ext}"
        if ext == "jpeg":
            cv2.imwrite(str(positive_path), positive_bgr, [cv2.IMWRITE_JPEG_QUALITY, self.quality.get()])
        elif ext == "png":
            cv2.imwrite(str(positive_path), positive_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        else:
            cv2.imwrite(str(positive_path), positive_bgr)

        negative_path = None
        if self.save_negative.get():
            negative_path = outdir / f"scan_{stamp}_negative.png"
            cv2.imwrite(str(negative_path), frame)

        msg = f"Enregistré : {positive_path}"
        self.status.config(text=msg)

        # Flash effect
        self.preview.config(bg="white")
        self.root.after(100, lambda: self.preview.config(bg="#151515"))

    def toggle_batch(self):
        if self.batch_running:
            self.batch_running = False
            self.batch_btn.config(text="Démarrer Batch")
            if self.batch_timer:
                self.root.after_cancel(self.batch_timer)
            self.status.config(text="Mode Batch arrêté.")
        else:
            self.batch_running = True
            self.batch_btn.config(text="Arrêter Batch")
            self._batch_step()

    def _batch_step(self):
        if not self.batch_running:
            return
        self.capture()
        self.status.config(text=f"Batch: {time.strftime('%H:%M:%S')} (Prochain dans {self.batch_interval.get()}s)")
        self.batch_timer = self.root.after(self.batch_interval.get() * 1000, self._batch_step)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def close(self):
        self.running = False
        if self.batch_timer:
            self.root.after_cancel(self.batch_timer)
        self.camera.release()
        self.root.destroy()
