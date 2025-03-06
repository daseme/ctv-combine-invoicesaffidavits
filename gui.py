# gui.py
import os, time, json, threading, queue, re, logging
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
from pdf_processor import PDFProcessor
from utils.validator import FileValidator

class StatsTracker:
    def __init__(self, stats_file="merger_stats.json"):
        self.stats_file = stats_file
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.stats = self.load_stats()

    def load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            default_stats = {self.today: {"processed_count": 0, "error_count": 0, "total_time": 0, "success_rate": 100.0, "total_invoice_balance": 0.0}}
            with open(self.stats_file, 'w') as f:
                json.dump(default_stats, f, indent=4)
            return default_stats
        except Exception as e:
            print(f"Error loading stats file: {e}")
            return {self.today: {"processed_count": 0, "error_count": 0, "total_time": 0, "success_rate": 100.0, "total_invoice_balance": 0.0}}

    def save_stats(self):
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            print(f"Error saving stats file: {e}")

    def update_processing_stats(self, success, processing_time):
        if self.today not in self.stats:
            self.stats[self.today] = {"processed_count": 0, "error_count": 0, "total_time": 0, "success_rate": 100.0, "total_invoice_balance": 0.0}
        self.stats[self.today]["processed_count"] += 1
        self.stats[self.today]["total_time"] += processing_time
        if not success:
            self.stats[self.today]["error_count"] += 1
        total = self.stats[self.today]["processed_count"]
        errors = self.stats[self.today]["error_count"]
        self.stats[self.today]["success_rate"] = ((total - errors) / total) * 100 if total > 0 else 100
        self.save_stats()

    def get_today_stats(self):
        return self.stats.get(self.today, {"processed_count": 0, "error_count": 0, "total_time": 0, "success_rate": 100.0, "total_invoice_balance": 0.0})

class ModernInvoiceMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice & Affidavit Merger")
        self.root.geometry("800x600")
        self.stats_tracker = StatsTracker()
        self.folder_path = tk.StringVar()   # Input folder
        self.output_folder = tk.StringVar()   # Output folder
        self.status_var = tk.StringVar(value="Ready to process files...")
        self.ignore_mismatch_var = tk.BooleanVar()
        self.process_button = None
        self.progress = None
        self.setup_styles()
        self.setup_ui()
        self.setup_menu()
        self.update_stats_display()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("TFrame", padding=10)
        self.style.configure("Header.TLabel", font=("Helvetica", 20, "bold"))
        self.style.configure("Stats.TLabel", font=("Helvetica", 12))
        self.style.configure("StatsValue.TLabel", font=("Helvetica", 16, "bold"))
        self.style.configure("Content.TLabel", font=("Helvetica", 11))

    def setup_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES, padx=20, pady=20)

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=X, pady=(0, 20))
        ttk.Label(header_frame, text="Invoice & Affidavit Merger", style="Header.TLabel").pack(pady=10)

        stats_frame = ttk.Frame(main_container)
        stats_frame.pack(fill=X, pady=(0, 20))
        self.create_stats_card(stats_frame, "Today's Processed", "processed_count", 0)
        self.create_stats_card(stats_frame, "Success Rate", "success_rate", 1, suffix="%")
        self.create_stats_card(stats_frame, "Avg. Processing Time", "avg_time", 2, suffix="s")
        self.create_stats_card(stats_frame, "Errors Today", "error_count", 3)

        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=BOTH, expand=YES)
        
        # Input folder selection
        input_frame = ttk.Frame(content_frame)
        input_frame.pack(pady=10, fill=X)
        ttk.Label(input_frame, text="Input Folder:").pack(side=LEFT, padx=5)
        ttk.Entry(input_frame, textvariable=self.folder_path, width=40).pack(side=LEFT, padx=5)
        ttk.Button(input_frame, text="Select Folder", command=self.select_folder).pack(side=LEFT, padx=5)
        
        # Output folder selection
        output_frame = ttk.Frame(content_frame)
        output_frame.pack(pady=10, fill=X)
        ttk.Label(output_frame, text="Output Folder:").pack(side=LEFT, padx=5)
        ttk.Entry(output_frame, textvariable=self.output_folder, width=40).pack(side=LEFT, padx=5)
        ttk.Button(output_frame, text="Select Folder", command=self.select_output_folder).pack(side=LEFT, padx=5)

        options_frame = ttk.Frame(content_frame)
        options_frame.pack(pady=10)
        ttk.Checkbutton(options_frame, text="Allow document count mismatch", variable=self.ignore_mismatch_var).pack()

        self.progress = ttk.Progressbar(content_frame, length=400, mode='determinate')
        self.progress.pack(pady=10)
        ttk.Label(content_frame, textvariable=self.status_var).pack()

        button_frame = ttk.Frame(content_frame)
        button_frame.pack(pady=20)
        self.process_button = ttk.Button(button_frame, text="Process Files", command=self.process_files)
        self.process_button.pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Help", command=self.show_help).pack(side=LEFT, padx=5)

        self.total_balance_label = ttk.Label(content_frame, text="Total Invoice Balance: $0.00", style="StatsValue.TLabel")
        self.total_balance_label.pack(pady=10)

    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)

    def show_about(self):
        messagebox.showinfo("About", "Invoice & Affidavit Merger\nVersion 1.0\nDeveloped for Windows")

    def show_help(self):
        help_text = (
            "1. Click 'Select Folder' to choose your input folder containing PDFs.\n"
            "2. Click 'Select Folder' for Output Folder to choose where merged files will be saved.\n"
            "3. PDFs must include 'invoice' and 'affidavit' in their names.\n"
            "4. Click 'Process Files' to merge.\n"
            "For mismatches, check 'Allow document count mismatch'."
        )
        messagebox.showinfo("Help", help_text)

    def create_stats_card(self, parent, title, stat_key, column, suffix=""):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=5)
        ttk.Label(frame, text=title, style="Stats.TLabel").grid(row=0, column=0, pady=2)
        value_label = ttk.Label(frame, text="0" + suffix, style="StatsValue.TLabel")
        value_label.grid(row=1, column=0)
        setattr(self, f"stat_{stat_key}_label", value_label)

    def update_stats_display(self):
        stats = self.stats_tracker.get_today_stats()
        self.stat_processed_count_label["text"] = str(stats["processed_count"])
        self.stat_success_rate_label["text"] = f"{stats['success_rate']:.1f}%"
        avg_time = stats["total_time"] / stats["processed_count"] if stats["processed_count"] > 0 else 0
        self.stat_avg_time_label["text"] = f"{avg_time:.1f}s"
        self.stat_error_count_label["text"] = str(stats["error_count"])
        self.root.after(5000, self.update_stats_display)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def process_files(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select an input folder first!")
            return
        # If no output folder is set, use a default subfolder in the input folder.
        if not self.output_folder.get():
            default_out = os.path.join(self.folder_path.get(), "output")
            os.makedirs(default_out, exist_ok=True)
            self.output_folder.set(default_out)
        self.process_button.configure(state=DISABLED)
        self.status_var.set("Processing... Please wait...")
        self.progress['value'] = 0
        self.queue = queue.Queue()
        threading.Thread(target=self._process_thread, daemon=True).start()
        self.root.after(100, self.check_queue)

    def _process_thread(self):
        start_time = time.time()
        try:
            # Pass output folder to PDFProcessor.
            processor = PDFProcessor(
                self.folder_path.get(),
                output_dir=self.output_folder.get(),
                ignore_mismatches=self.ignore_mismatch_var.get()
            )
            stats, mismatch_details = processor.process_pdfs()
            message_parts = []
            if mismatch_details:
                message_parts.append("Warning: Document mismatches found:\n")
                message_parts.extend(mismatch_details)
                message_parts.append("\n")
            message_parts.append(
                f"Processing complete!\n\nFound {stats['invoice_count']} invoices and {stats['affidavit_count']} affidavits\n"
                f"Successfully created {stats['processed_count']} merged files"
            )
            processing_time = time.time() - start_time
            self.stats_tracker.update_processing_stats(True, processing_time)
            self.stats_tracker.stats[self.stats_tracker.today]['total_invoice_balance'] = stats.get('total_invoice_balance', 0.0)
            self.queue.put(("success", "\n".join(message_parts)))
            logging.info("Processing thread completed successfully.")
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats_tracker.update_processing_stats(False, processing_time)
            self.queue.put(("error", str(e)))
            logging.error(f"Error in processing thread: {e}")
        finally:
            self.root.after(100, self.check_queue)

    def check_queue(self):
        try:
            msg_type, message = self.queue.get_nowait()
            if msg_type == "success":
                messagebox.showinfo("Success", message)
                self.status_var.set("Ready for next batch...")
                total_balance = self.stats_tracker.get_today_stats().get('total_invoice_balance', 0.0)
                self.total_balance_label["text"] = f"Total Invoice Balance: ${total_balance:.2f}"
                self.progress['value'] = 100
                self.process_button.configure(state=NORMAL)
            elif msg_type == "error":
                messagebox.showerror("Error", message)
                self.status_var.set("Error occurred. Please try again.")
                self.progress['value'] = 100
                self.process_button.configure(state=NORMAL)
        except queue.Empty:
            current_value = self.progress['value']
            if current_value < 100:
                self.progress['value'] = min(current_value + 1, 100)
                self.root.after(100, self.check_queue)
            else:
                self.status_var.set("Processing complete!")
                self.process_button.configure(state=NORMAL)

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    ModernInvoiceMergerGUI(root)
    root.mainloop()
