import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkthemes import ThemedTk
import json
from datetime import datetime
import threading
import queue
import time
from typing import Dict
from pdf_processor import PDFProcessor

class StatsTracker:
    def __init__(self, stats_file: str = "merger_stats.json"):
        self.stats_file = stats_file
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.stats = self.load_stats()
        
    def load_stats(self) -> Dict:
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            default_stats = {
                self.today: {
                    "processed_count": 0,
                    "error_count": 0,
                    "total_time": 0,
                    "success_rate": 100.0
                }
            }
            with open(self.stats_file, 'w') as f:
                json.dump(default_stats, f, indent=4)
            return default_stats
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading stats file: {e}")
            return {
                self.today: {
                    "processed_count": 0,
                    "error_count": 0,
                    "total_time": 0,
                    "success_rate": 100.0
                }
            }
    
    def save_stats(self):
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4)
        except OSError as e:
            print(f"Error saving stats file: {e}")
            
    def update_processing_stats(self, success: bool, processing_time: float):
        if self.today not in self.stats:
            self.stats[self.today] = {
                "processed_count": 0,
                "error_count": 0,
                "total_time": 0,
                "success_rate": 100.0
            }
            
        self.stats[self.today]["processed_count"] += 1
        self.stats[self.today]["total_time"] += processing_time
        
        if not success:
            self.stats[self.today]["error_count"] += 1
            
        total = self.stats[self.today]["processed_count"]
        errors = self.stats[self.today]["error_count"]
        self.stats[self.today]["success_rate"] = ((total - errors) / total) * 100 if total > 0 else 100
        
        self.save_stats()
        
    def get_today_stats(self) -> Dict:
        return self.stats.get(self.today, {
            "processed_count": 0,
            "error_count": 0,
            "total_time": 0,
            "success_rate": 100.0
        })

class ModernInvoiceMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice & Affidavit Merger")
        self.root.geometry("800x600")
        self.stats_tracker = StatsTracker()
        
        # Initialize variables
        self.folder_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to process files...")
        self.ignore_mismatch_var = tk.BooleanVar()
        self.process_button = None  # Will be set in setup_ui
        self.progress = None  # Will be set in setup_ui
        
        self.setup_styles()
        self.setup_ui()
        
        # Update stats periodically
        self.update_stats_display()
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure("Header.TFrame", background="#f8fafc")
        style.configure("Header.TLabel", 
                       background="#f8fafc",
                       font=('Helvetica', 20, 'bold'))
        style.configure("Stats.TFrame", background="white")
        style.configure("Stats.TLabel", 
                       background="white",
                       font=('Helvetica', 12))
        style.configure("StatsValue.TLabel",
                       background="white",
                       font=('Helvetica', 16, 'bold'))
        style.configure("Content.TFrame", background="white")
        style.configure("Content.TLabel",
                       background="white",
                       font=('Helvetica', 11))
                       
    def setup_ui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="20")
        main_container.grid(row=0, column=0, sticky="nsew")
        
        # Header Section
        header_frame = ttk.Frame(main_container, style="Header.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ttk.Label(header_frame, 
                 text="Invoice & Affidavit Merger",
                 style="Header.TLabel").grid(row=0, column=0, pady=10)
        
        # Stats Section
        stats_frame = ttk.Frame(main_container, style="Stats.TFrame")
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Create stats cards
        self.create_stats_card(stats_frame, 0, "Today's Processed", "processed_count")
        self.create_stats_card(stats_frame, 1, "Success Rate", "success_rate", suffix="%")
        self.create_stats_card(stats_frame, 2, "Avg. Processing Time", "avg_time", suffix="s")
        self.create_stats_card(stats_frame, 3, "Errors Today", "error_count")
        
        # Main Content Section
        content_frame = ttk.Frame(main_container, style="Content.TFrame")
        content_frame.grid(row=2, column=0, sticky="nsew")
        
        # Folder Selection
        folder_frame = ttk.Frame(content_frame)
        folder_frame.grid(row=0, column=0, pady=20)
        
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=50).grid(row=0, column=0, padx=5)
        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).grid(row=0, column=1)
        
        # Options Section
        options_frame = ttk.Frame(content_frame)
        options_frame.grid(row=1, column=0, pady=10)
        
        ttk.Checkbutton(options_frame, 
                       text="Allow document count mismatch",
                       variable=self.ignore_mismatch_var).grid(row=0, column=0)
        
        # Progress Section
        self.progress = ttk.Progressbar(content_frame, length=400, mode='determinate')
        self.progress.grid(row=2, column=0, pady=10)
        
        ttk.Label(content_frame, textvariable=self.status_var).grid(row=3, column=0)
        
        # Action Buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=4, column=0, pady=20)
        
        self.process_button = ttk.Button(button_frame, text="Process Files", 
                                       command=self.process_files)
        self.process_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="Help",
                  command=self.show_help).grid(row=0, column=1, padx=5)
    
    def create_stats_card(self, parent, column, title, stat_key, suffix=""):
        frame = ttk.Frame(parent, style="Stats.TFrame")
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
        start_time = time.time()
        try:
            processor = PDFProcessor(
                self.folder_path.get(),
                ignore_mismatches=self.ignore_mismatch_var.get()
            )
            stats, mismatch_details = processor.process_pdfs()
            
            message_parts = []
            if mismatch_details:
                message_parts.append("Warning: Document mismatches found:\n")
                message_parts.extend(mismatch_details)
                message_parts.append("\n")
            
            message_parts.append(
                f"Processing complete!\n\n"
                f"Found {stats['invoice_count']} invoices and {stats['affidavit_count']} affidavits\n"
                f"Successfully created {stats['processed_count']} merged files"
            )
            
            processing_time = time.time() - start_time
            self.stats_tracker.update_processing_stats(True, processing_time)
            self.queue.put(("success", "\n".join(message_parts)))
            
        except ValueError as e:
            processing_time = time.time() - start_time
            self.stats_tracker.update_processing_stats(False, processing_time)
            self.queue.put(("error", str(e)))
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats_tracker.update_processing_stats(False, processing_time)
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

        If there is a mismatch between the number of invoices and affidavits,
        you can check 'Allow document count mismatch' to continue processing.

        Need help? Contact IT Support at ext. 1234
        """
        messagebox.showinfo("Help", help_text)