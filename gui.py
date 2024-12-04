import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pdf_processor import PDFProcessor
import threading
import queue

class InvoiceMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice & Affidavit Merger")
        self.root.geometry("600x400")
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Welcome to Invoice & Affidavit Merger!", 
                 font=('Helvetica', 14, 'bold')).grid(row=0, column=0, pady=10)
        
        ttk.Label(main_frame, text="This tool will help you combine your invoice and affidavit PDFs.",
                 wraplength=500).grid(row=1, column=0, pady=5)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=2, column=0, pady=20)
        
        self.folder_path = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=50).grid(row=0, column=0, padx=5)
        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=1)
        
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=3, column=0, pady=10)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to process files...")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=4, column=0, pady=5)
        
        self.process_button = ttk.Button(main_frame, text="Process Files", 
                                       command=self.process_files)
        self.process_button.grid(row=5, column=0, pady=20)
        
        self.ignore_mismatch_var = tk.BooleanVar()
        self.ignore_mismatch_checkbox = ttk.Checkbutton(main_frame, variable=self.ignore_mismatch_var, text="Ignore document mismatch")
        self.ignore_mismatch_checkbox.grid(row=6, column=0, pady=10)
        
        ttk.Button(main_frame, text="Help", command=self.show_help).grid(row=7, column=0)
        
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            
    def process_files(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first!")
            return
            
        self.process_button.configure(state='disabled')
        self.status_var.set("Processing... Please wait...")
        self.progress['value'] = 0
        
        self.queue = queue.Queue()
        threading.Thread(target=self._process_thread, daemon=True).start()
        self.root.after(100, self.check_queue)
        
    def _process_thread(self):
        try:
            processor = PDFProcessor(self.folder_path.get())
            stats = processor.process_pdfs()
            
            success_message = (
                f"Processing complete!\n\n"
                f"Found {stats['invoice_count']} invoices and {stats['affidavit_count']} affidavits\n"
                f"Successfully created {stats['processed_count']} merged files"
            )
            self.queue.put(("success", success_message))
            
        except ValueError as e:
            if "Document count mismatch" in str(e):
                if self.ignore_mismatch_var.get():
                    self.queue.put(("success", str(e) + "\nProcessing continues despite mismatch."))
                else:
                    self.queue.put(("error", str(e)))
            else:
                self.queue.put(("error", str(e)))
        except Exception as e:
            self.queue.put(("error", str(e)))
            
    def check_queue(self):
        try:
            msg_type, message = self.queue.get_nowait()
            if msg_type == "success":
                messagebox.showinfo("Success", message)
                self.status_var.set("Ready for next batch...")
            else:
                messagebox.showerror("Error", message)
                self.status_var.set("Error occurred. Please try again.")
            
            self.progress['value'] = 100
            self.process_button.configure(state='normal')
        except queue.Empty:
            self.progress['value'] += 1
            if self.progress['value'] < 90:
                self.root.after(100, self.check_queue)
                    
    def show_help(self):
        help_text = """
        How to use this tool:

        1. Click 'Select Folder' and choose the folder containing your PDFs
        2. Make sure your PDFs have 'invoice' and 'affidavit' in their names
        3. Click 'Process Files' and wait for completion
        4. Find your combined PDFs in the output folder

        If there is a mismatch between the number of invoices and affidavits, you can choose to ignore it and continue processing.

        Need help? Contact IT Support at ext. 1234
        """
        messagebox.showinfo("Help", help_text)

def main():
    root = tk.Tk()
    app = InvoiceMergerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()