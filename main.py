from gui import InvoiceMergerGUI
import tkinter as tk
from utils.logger import setup_logging

def main():
    setup_logging()
    root = tk.Tk()
    app = InvoiceMergerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()