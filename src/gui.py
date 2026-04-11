"""
GUI for Snapchat Memory Fixer
Built with Tkinter for Linux compatibility.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Optional
import threading
import queue
import logging
from datetime import datetime

from processor import MemoryProcessor

logger = logging.getLogger(__name__)

class MemoryFixerGUI:
    """Main GUI application class."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Snapchat Memory Fixer")
        self.root.geometry("1300x1000")
        
        # Configure styles
        self.setup_styles()
        
        # Variables
        self.zip_files = []
        self.output_dir = None
        self.merge_image_overlays = tk.BooleanVar(value=True)
        self.merge_video_overlays = tk.BooleanVar(value=True)
        self.separate_folders = tk.BooleanVar(value=False)
        self.processing = False
        self.processor = None
        
        # Message queue for thread-safe GUI updates
        self.message_queue = queue.Queue()
        
        # Build UI
        self.setup_ui()
        
        # Start polling the message queue
        self.poll_message_queue()
    
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Helvetica", 12))
        style.configure("Success.TLabel", foreground="green")
        style.configure("Error.TLabel", foreground="red")
    
    def setup_ui(self):
        """Setup the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Snapchat Memories Export Fixer", 
                               style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Drag and drop area for zip files
        self.zip_frame = ttk.LabelFrame(main_frame, text="Select all the zip files from your export", padding="10")
        self.zip_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.zip_frame.columnconfigure(0, weight=1)
        
        self.zip_listbox = tk.Listbox(self.zip_frame, height=6)
        self.zip_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        zip_scrollbar = ttk.Scrollbar(self.zip_frame, orient=tk.VERTICAL, 
                                      command=self.zip_listbox.yview)
        zip_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.zip_listbox.config(yscrollcommand=zip_scrollbar.set)
        
        # Zip file buttons
        zip_button_frame = ttk.Frame(self.zip_frame)
        zip_button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(zip_button_frame, text="Add Files", 
                  command=self.add_zip_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(zip_button_frame, text="Remove Selected", 
                  command=self.remove_selected_zip).pack(side=tk.LEFT, padx=5)
        ttk.Button(zip_button_frame, text="Clear All", 
                  command=self.clear_zip_files).pack(side=tk.LEFT, padx=5)
        
        # Output directory selection
        ttk.Label(main_frame, text="Output Directory (in what folder should your memories go?):", 
                 style="Subtitle.TLabel").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_var = tk.StringVar(value="Not selected")
        ttk.Label(output_frame, textvariable=self.output_var, 
                 relief=tk.SUNKEN, padding="5").grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(output_frame, text="Browse", 
                  command=self.select_output_dir).grid(row=0, column=1, padx=(10, 0))
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Overlay options
        overlay_frame = ttk.Frame(options_frame)
        overlay_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(overlay_frame, text="Overlay Options:").pack(anchor=tk.W)
        
        ttk.Checkbutton(overlay_frame, text="Merge overlays with pictures (put the text, filters, drawings, etc back into the pictures)", 
                       variable=self.merge_image_overlays).pack(anchor=tk.W, padx=(20, 0))
        
        video_frame = ttk.Frame(overlay_frame)
        video_frame.pack(anchor=tk.W, padx=(20, 0), pady=(2, 0))
        ttk.Checkbutton(video_frame, text="Merge overlays with videos (put the text, filters, drawings, etc back into the videos)", 
                       variable=self.merge_video_overlays).pack(side=tk.LEFT)
        ttk.Label(video_frame, text="(resource intensive, the processing might take a little if you have many files)", 
                 font=("Helvetica", 9), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Organization options
        ttk.Checkbutton(options_frame, text="Separate pictures and videos in two sub-directories (/videos and /pictures)", 
                       variable=self.separate_folders).pack(anchor=tk.W, pady=(10, 0))
        
        # Progress area
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                           pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(2, weight=1)
        
        # Progress info row
        progress_info_frame = ttk.Frame(progress_frame)
        progress_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_info_frame, textvariable=self.progress_var).pack(side=tk.LEFT)
        
        self.progress_counter = tk.StringVar(value="0/0")
        ttk.Label(progress_info_frame, textvariable=self.progress_counter, 
                 font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT)
        
        # Progress bar row
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=10, 
                                                 state=tk.DISABLED)
        self.log_text.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          pady=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        
        self.process_button = ttk.Button(button_frame, text="Start Processing", 
                                        command=self.toggle_processing, width=20)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, padding="5")
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure drag and drop
        self.setup_drag_drop()
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality (placeholder for future implementation)."""
        # Note: Tkinter DND support varies by platform and requires additional setup
        # For now, we'll rely on file dialog for simplicity
        pass
    
    def handle_drop(self, event):
        """Handle file drop events (placeholder)."""
        # Placeholder for future drag and drop implementation
        pass
    
    def add_zip_files(self):
        """Add zip files via file dialog."""
        files = filedialog.askopenfilenames(
            title="Select Snapchat Export Zip Files",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
        )
        self.add_zip_files_from_paths(files)
    
    def add_zip_files_from_paths(self, file_paths):
        """Add zip files from list of paths."""
        for file_path in file_paths:
            path = Path(file_path)
            if path.suffix.lower() == '.zip' and path not in self.zip_files:
                self.zip_files.append(path)
                self.zip_listbox.insert(tk.END, path.name)
        
        self.update_status()
    
    def remove_selected_zip(self):
        """Remove selected zip file from list."""
        selection = self.zip_listbox.curselection()
        if selection:
            index = selection[0]
            self.zip_listbox.delete(index)
            del self.zip_files[index]
            self.update_status()
    
    def clear_zip_files(self):
        """Clear all zip files from list."""
        self.zip_listbox.delete(0, tk.END)
        self.zip_files.clear()
        self.update_status()
    
    def select_output_dir(self):
        """Select output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir = Path(directory)
            self.output_var.set(str(self.output_dir))
            self.update_status()
    
    def update_status(self):
        """Update status bar based on current state."""
        if not self.zip_files:
            status = "Add Snapchat export zip files to begin"
        elif not self.output_dir:
            status = "Select output directory"
        else:
            status = f"Ready to process {len(self.zip_files)} file(s)"
        
        self.status_var.set(status)
        
        # Enable/disable process button
        can_process = bool(self.zip_files and self.output_dir and not self.processing)
        self.process_button.state(['!disabled' if can_process else 'disabled'])
    
    def toggle_processing(self):
        """Start or stop processing."""
        if self.processing:
            self.stop_processing()
        else:
            self.start_processing()
    
    def start_processing(self):
        """Start the processing in a separate thread."""
        if not self.zip_files or not self.output_dir:
            messagebox.showerror("Error", "Please select zip files and output directory")
            return
        
        # Disable UI
        self.processing = True
        self.process_button.config(text="Stop Processing")
        self.progress_bar['value'] = 0
        self.progress_var.set("Processing...")
        self.progress_counter.set("0/0")
        self.log_message("Starting processing...")
        
        # Start processing thread
        thread = threading.Thread(target=self.process_thread, daemon=True)
        thread.start()
    
    def stop_processing(self):
        """Stop the processing."""
        self.processing = False
        self.process_button.config(text="Start Processing")
        self.progress_bar.stop()
        self.progress_var.set("Stopped")
        self.log_message("Processing stopped by user")
        self.update_status()
    
    def process_thread(self):
        """Processing thread function."""
        try:
            self.processor = MemoryProcessor()
            
            # Create progress callback function
            def progress_callback(current: int, total: int):
                """Send progress update to GUI thread."""
                self.message_queue.put(('progress', (current, total)))
            
            # Ensure output_dir is not None (should be guaranteed by start_processing)
            if not self.output_dir:
                raise ValueError("Output directory not selected")
            
            results = self.processor.process_files(
                self.zip_files, 
                self.output_dir, 
                self.merge_image_overlays.get(),
                self.merge_video_overlays.get(),
                self.separate_folders.get(),
                progress_callback=progress_callback
            )
            
            # Send results to main thread via queue
            self.message_queue.put(('results', results))
            
        except Exception as e:
            self.message_queue.put(('error', str(e)))
    
    def poll_message_queue(self):
        """Poll message queue for thread-safe GUI updates."""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'results':
                    self.handle_results(data)
                elif msg_type == 'error':
                    self.handle_error(data)
                elif msg_type == 'log':
                    self.log_message(data)
                elif msg_type == 'progress':
                    self.handle_progress(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next poll
        self.root.after(100, self.poll_message_queue)
    
    def handle_progress(self, progress_data):
        """Handle progress update."""
        current, total = progress_data
        
        # Update progress counter
        self.progress_counter.set(f"{current}/{total}")
        
        # Update progress bar
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            
            # Update progress text
            if current == 0:
                self.progress_var.set("Processing...")
            elif current == total:
                self.progress_var.set("Finalizing...")
            else:
                self.progress_var.set(f"Processing... ({current}/{total})")
    
    def handle_results(self, results):
        """Handle processing results."""
        self.processing = False
        self.process_button.config(text="Start Processing")
        self.progress_bar.stop()
        
        # Calculate duration
        duration = results['end_time'] - results['start_time']
        duration_str = str(duration).split('.')[0]  # Remove microseconds
        
        # Update UI
        self.progress_var.set(f"Completed in {duration_str}")
        
        # Show summary
        summary = (
            f"Processing completed!\n\n"
            f"Total files: {results['total_files']}\n"
            f"Successfully processed: {results['processed_files']}\n"
            f"Failed: {results['failed_files']}\n"
            f"Duration: {duration_str}"
        )
        
        self.log_message("\n" + summary)
        
        if results['errors']:
            self.log_message("\nErrors encountered:")
            for error in results['errors'][:10]:  # Show first 10 errors
                self.log_message(f"  - {error}")
            if len(results['errors']) > 10:
                self.log_message(f"  ... and {len(results['errors']) - 10} more errors")
        
        # Show message box
        if results['failed_files'] == 0:
            messagebox.showinfo("Success", summary)
        else:
            messagebox.showwarning("Completed with warnings", summary)
        
        self.update_status()
    
    def handle_error(self, error_msg):
        """Handle processing error."""
        self.processing = False
        self.process_button.config(text="Start Processing")
        self.progress_bar.stop()
        self.progress_var.set("Error")
        
        self.log_message(f"Error: {error_msg}")
        messagebox.showerror("Processing Error", error_msg)
        
        self.update_status()
    
    def log_message(self, message):
        """Add message to log text area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """Run the main application loop."""
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        # Start main loop
        self.root.mainloop()