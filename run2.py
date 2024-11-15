import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import json
import requests
from typing import Optional
import threading
import time
import logging
from datetime import datetime

class ConsoleHandler(logging.Handler):
    def __init__(self, console_widget):
        logging.Handler.__init__(self)
        self.console_widget = console_widget

    def emit(self, record):
        msg = self.format(record)
        self.console_widget.insert(tk.END, f"{msg}\n")
        self.console_widget.see(tk.END)
        self.console_widget.update_idletasks()

class OllamaAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Project Analyzer")
        self.root.geometry("1200x800")
        
        # Setup logging
        self.setup_logging()
        
        # Configure grid weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Variables
        self.project_path = tk.StringVar()
        self.model_name = tk.StringVar(value="llama2")
        self.base_url = tk.StringVar(value="http://localhost:11434")
        self.is_analyzing = False
        self.is_connected = False
        
        # File type filters
        self.file_filters = {
            'javascript': tk.BooleanVar(value=True),
            'typescript': tk.BooleanVar(value=True),
            'css': tk.BooleanVar(value=True),
            'json': tk.BooleanVar(value=True),
            'jsx': tk.BooleanVar(value=True),
            'tsx': tk.BooleanVar(value=True),
            'scss': tk.BooleanVar(value=True),
        }
        
        self.create_widgets()
        self.logger.info("Application started")
        
    def setup_logging(self):
        self.logger = logging.getLogger('OllamaAnalyzer')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # File handler for full logging
        log_file = f'logs/analyzer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
    def create_widgets(self):
        # Project settings frame
        settings_frame = ttk.LabelFrame(self.root, text="Project Settings", padding="10")
        settings_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Project path selection
        ttk.Label(settings_frame, text="Project Path:").grid(row=0, column=0, padx=5, pady=5)
        path_entry = ttk.Entry(settings_frame, textvariable=self.project_path)
        path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(settings_frame, text="Browse", command=self.browse_project).grid(row=0, column=2, padx=5)
        
        # Model settings
        ttk.Label(settings_frame, text="Model:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.model_name).grid(row=1, column=1, sticky="ew", padx=5)
        
        ttk.Label(settings_frame, text="Ollama URL:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.base_url).grid(row=2, column=1, sticky="ew", padx=5)
        
        # Connection status and test button
        self.connection_status = ttk.Label(settings_frame, text="⚠️ Not Connected", foreground="red")
        self.connection_status.grid(row=2, column=2, padx=5)
        ttk.Button(settings_frame, text="Connect to Ollama", command=self.connect_to_ollama).grid(row=2, column=3, padx=5)
        
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # File type filters frame
        filters_frame = ttk.LabelFrame(settings_frame, text="File Filters", padding="5")
        filters_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
        
        for i, (file_type, var) in enumerate(self.file_filters.items()):
            ttk.Checkbutton(filters_frame, text=f".{file_type}", variable=var).grid(row=0, column=i, padx=5)
        
        # Query frame
        query_frame = ttk.LabelFrame(self.root, text="Query", padding="10")
        query_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.query_text = scrolledtext.ScrolledText(query_frame, height=3)
        self.query_text.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.analyze_button = ttk.Button(query_frame, text="Analyze", command=self.start_analysis, state="disabled")
        self.analyze_button.grid(row=1, column=0, pady=5)
        self.progress_bar = ttk.Progressbar(query_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=1, sticky="ew", padx=5)
        
        query_frame.grid_columnconfigure(1, weight=1)
        
        # Results frame with notebook
        results_frame = ttk.LabelFrame(self.root, text="Results", padding="10")
        results_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Console output tab
        self.console_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD)
        self.notebook.add(self.console_text, text="Console")
        
        # Set up console handler for logging
        console_handler = ConsoleHandler(self.console_text)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Analysis results tab
        self.results_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD)
        self.notebook.add(self.results_text, text="Analysis Results")
        
        # File list tab
        self.file_list_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD)
        self.notebook.add(self.file_list_text, text="Project Files")
        
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
    def browse_project(self):
        directory = filedialog.askdirectory()
        if directory:
            self.project_path.set(directory)
            self.logger.info(f"Selected project directory: {directory}")
            self.scan_project_files()
            
    def scan_project_files(self):
        """Scan and display project files based on selected filters"""
        if not self.project_path.get():
            return
            
        self.file_list_text.delete(1.0, tk.END)
        self.logger.info("Scanning project files...")
        
        try:
            files = self.get_filtered_files()
            self.file_list_text.insert(tk.END, "Project Files:\n\n")
            
            # Group files by type
            files_by_type = {}
            for file in files:
                ext = os.path.splitext(file)[1][1:]  # Remove the dot
                if ext not in files_by_type:
                    files_by_type[ext] = []
                files_by_type[ext].append(file)
            
            # Display files grouped by type
            for ext, file_list in sorted(files_by_type.items()):
                self.file_list_text.insert(tk.END, f"\n{ext.upper()} Files ({len(file_list)}):\n")
                for file in sorted(file_list):
                    self.file_list_text.insert(tk.END, f"  {file}\n")
            
            self.logger.info(f"Found {len(files)} files matching the filters")
        except Exception as e:
            self.logger.error(f"Error scanning project files: {str(e)}")
            
    def get_filtered_files(self):
        """Get list of files based on selected filters"""
        files = []
        ignore_dirs = {'node_modules', '.next', '.git', 'public', 'out', 'build', 'dist'}
        ignore_extensions = {'.map', '.lock', '.log', '.env'}
        
        enabled_extensions = [f".{ext}" for ext, var in self.file_filters.items() if var.get()]
        
        for root, dirs, filenames in os.walk(self.project_path.get()):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in ignore_extensions):
                    continue
                    
                if any(filename.endswith(ext) for ext in enabled_extensions):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.project_path.get())
                    files.append(relative_path)
                    
        return files

    def connect_to_ollama(self):
        self.logger.info("Attempting to connect to Ollama...")
        try:
            response = requests.get(f"{self.base_url.get()}/api/version")
            if response.status_code == 200:
                self.logger.info("Successfully connected to Ollama service")
                
                model_response = requests.post(
                    f"{self.base_url.get()}/api/generate",
                    json={"model": self.model_name.get(), "prompt": "test", "stream": False}
                )
                
                if model_response.status_code == 200:
                    self.is_connected = True
                    self.connection_status.config(text="✅ Connected", foreground="green")
                    self.analyze_button.config(state="normal")
                    self.logger.info(f"Successfully connected to model: {self.model_name.get()}")
                    messagebox.showinfo("Success", "Successfully connected to Ollama!")
                else:
                    self.logger.error(f"Model not found: {self.model_name.get()}")
                    self.is_connected = False
                    self.connection_status.config(text="⚠️ Model Not Found", foreground="red")
                    self.analyze_button.config(state="disabled")
                    messagebox.showerror("Error", f"Model '{self.model_name.get()}' not found. Please check the model name.")
            else:
                raise Exception("Ollama service not responding")
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama service")
            self.is_connected = False
            self.connection_status.config(text="❌ Connection Failed", foreground="red")
            self.analyze_button.config(state="disabled")
            messagebox.showerror("Error", "Cannot connect to Ollama. Please make sure:\n\n1. Ollama is installed\n2. Ollama service is running\n3. Run 'ollama serve' in terminal")
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            self.is_connected = False
            self.connection_status.config(text="❌ Error", foreground="red")
            self.analyze_button.config(state="disabled")
            messagebox.showerror("Error", f"Connection failed: {str(e)}")

    def analyze_project(self):
        if not self.is_connected:
            self.logger.error("Cannot start analysis - not connected to Ollama")
            messagebox.showerror("Error", "Please connect to Ollama first")
            return
            
        project_path = self.project_path.get()
        if not project_path:
            self.logger.error("Cannot start analysis - no project path selected")
            messagebox.showerror("Error", "Please select a project directory")
            return
            
        self.console_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.is_analyzing = True
        self.logger.info("Starting project analysis...")
        
        try:
            files = self.get_filtered_files()
            total_files = len(files)
            self.progress_bar["maximum"] = total_files
            
            self.logger.info(f"Found {total_files} files to analyze")
            question = self.query_text.get(1.0, tk.END).strip()
            
            results = {}
            for i, file_path in enumerate(files, 1):
                if not self.is_analyzing:
                    self.logger.info("Analysis stopped by user")
                    break
                    
                self.logger.info(f"Analyzing file {i}/{total_files}: {file_path}")
                try:
                    if not self.verify_connection():
                        raise Exception("Lost connection to Ollama")
                    
                    full_path = os.path.join(project_path, file_path)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Query Ollama
                    response = self.query_ollama(
                        content=content,
                        file_path=file_path,
                        question=question
                    )
                    
                    if response:
                        results[file_path] = response
                        self.results_text.insert(tk.END, f"\n=== {file_path} ===\n{response}\n")
                        self.results_text.see(tk.END)
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {str(e)}")
                    if not self.verify_connection():
                        if not messagebox.askyesno("Connection Lost", "Lost connection to Ollama. Try to reconnect?"):
                            break
                        self.connect_to_ollama()
                
                self.progress_bar["value"] = i
                self.root.update_idletasks()
                time.sleep(0.5)
                # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analysis_{timestamp}.json"
            output_dir = "analysis_results"
            
            # Create output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_path = os.path.join(output_dir, output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Analysis completed. Results saved to: {output_path}")
            messagebox.showinfo("Complete", f"Analysis completed!\nResults saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
        finally:
            self.is_analyzing = False
            self.progress_bar["value"] = 0
            
    def query_ollama(self, content: str, file_path: str, question: str) -> str:
        """Query Ollama with file content and question"""
        url = f"{self.base_url.get()}/api/generate"
        
        system_prompt = f"""You are analyzing the file {file_path} from a Next.js project.
Focus on providing specific, actionable insights related to the question.
If the file is not relevant to the question, respond with 'NOT_RELEVANT'."""

        prompt = f"""
File: {file_path}

Content:
{content}

Question: {question}

Please provide a detailed analysis focusing specifically on this file and the question asked.
If this file is not relevant to the question, respond with 'NOT_RELEVANT'.
"""

        try:
            response = requests.post(url, json={
                "model": self.model_name.get(),
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            })
            
            response.raise_for_status()
            result = response.json()['response']
            
            # Only return result if it's relevant
            if result.strip() != 'NOT_RELEVANT':
                return result
            else:
                self.logger.info(f"File {file_path} not relevant to the question")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error querying Ollama: {str(e)}")
            raise
            
    def verify_connection(self) -> bool:
        """Verify connection to Ollama is still active"""
        try:
            response = requests.get(f"{self.base_url.get()}/api/version")
            return response.status_code == 200
        except:
            return False
            
    def start_analysis(self):
        """Start or stop analysis"""
        if self.is_analyzing:
            self.is_analyzing = False
            self.analyze_button.config(text="Analyze")
            self.logger.info("Analysis stopped by user")
        else:
            self.analyze_button.config(text="Stop")
            thread = threading.Thread(target=self.analyze_project)
            thread.daemon = True
            thread.start()

def main():
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ollama_analyzer.log'),
            logging.StreamHandler()
        ]
    )
    
    root = tk.Tk()
    app = OllamaAnalyzerGUI(root)
    
    # Add window close handler
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if app.is_analyzing:
                app.is_analyzing = False
                time.sleep(1)  # Give time for analysis to stop
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()