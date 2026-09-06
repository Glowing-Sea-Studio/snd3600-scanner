import tkinter as tk
from .ui import ScannerApp

def main():
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.1)
    except Exception:
        pass
    app = ScannerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
