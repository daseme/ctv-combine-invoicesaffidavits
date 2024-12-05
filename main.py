from gui import ModernInvoiceMergerGUI
from ttkthemes import ThemedTk
import tkinter as tk
from utils.logger import setup_logging

def main():
    setup_logging()
    root = ThemedTk(theme="arc")
    app = ModernInvoiceMergerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()