import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sys
import os
import io

# --- IMPORT OPTIMIZER ---
try:
    import lineup_optimizer
except ImportError:
    messagebox.showerror("Configuration Error", "Could not import 'lineup_optimizer.py'.\nMake sure it is in the same folder as this script.")
    sys.exit(1)

# --- COLORS & FONTS ---
LAKERS_PURPLE = "#552583"
LAKERS_GOLD = "#FDB927"
LAKERS_BLACK = "#000000"
LAKERS_WHITE = "#FFFFFF"

# Fonts
FONT_HEADER = ("Impact", 28)
FONT_LABEL = ("Arial", 11, "bold")
FONT_ENTRY = ("Arial", 11)
FONT_BUTTON = ("Arial", 11, "bold")
FONT_RESULT = ("Consolas", 10)

# --- GUI APPLICATION ---

class LineupOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lakers Lineup Optimizer")
        self.root.geometry("700x700")
        self.root.configure(bg=LAKERS_PURPLE) 

        # --- THEME CONFIGURATION ---
        self.style = ttk.Style()
        self.style.theme_use('alt')
        
        # Configure Button Style (Black Background, Gold Text)
        self.style.configure(
            "Lakers.TButton",
            background=LAKERS_BLACK,
            foreground=LAKERS_GOLD,
            font=FONT_BUTTON,
            borderwidth=1,
            focuscolor="none",
            padding=6
        )
        self.style.map(
            "Lakers.TButton",
            background=[('active', LAKERS_GOLD), ('pressed', LAKERS_WHITE)],
            foreground=[('active', LAKERS_BLACK), ('pressed', LAKERS_BLACK)]
        )

        # Configure Combobox Style
        self.style.configure(
            "TCombobox",
            fieldbackground=LAKERS_BLACK,
            background=LAKERS_BLACK,
            foreground=LAKERS_GOLD,
            arrowcolor=LAKERS_GOLD,
            borderwidth=1
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[('readonly', LAKERS_BLACK)],
            selectbackground=[('readonly', LAKERS_GOLD)],
            selectforeground=[('readonly', LAKERS_BLACK)]
        )

        # --- HEADER SECTION ---
        header_frame = tk.Frame(root, bg=LAKERS_PURPLE, height=100)
        header_frame.pack(fill="x", side="top", pady=10)
        
        # Title Label
        lbl_title = tk.Label(
            header_frame, 
            text="LAKERS ANALYTICS\nLINEUP OPTIMIZER", 
            font=FONT_HEADER, 
            bg=LAKERS_PURPLE, 
            fg=LAKERS_GOLD,
            justify="left"
        )
        lbl_title.pack(side="left", padx=30, pady=10)

        # Gold Separator
        tk.Frame(root, bg=LAKERS_GOLD, height=4).pack(fill="x", padx=30)

        # --- MAIN FORM SECTION ---
        main_frame = tk.Frame(root, bg=LAKERS_PURPLE, padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Entry Config
        entry_config = {
            "bg": LAKERS_BLACK, 
            "fg": LAKERS_GOLD, 
            "insertbackground": LAKERS_GOLD, 
            "bd": 1, 
            "relief": "solid"
        }

        # --- Row 1: Input File (XLSX) ---
        tk.Label(main_frame, text="PLAYER DATA FILE (.XLSX)", font=FONT_LABEL, bg=LAKERS_PURPLE, fg=LAKERS_GOLD).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.input_path_var = tk.StringVar()
        self.entry_input = tk.Entry(main_frame, textvariable=self.input_path_var, width=50, font=FONT_ENTRY, **entry_config)
        self.entry_input.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), ipady=4)
        
        ttk.Button(main_frame, text="BROWSE", command=self.browse_input, style="Lakers.TButton").grid(row=1, column=1)

        # Spacer
        tk.Label(main_frame, text="", bg=LAKERS_PURPLE).grid(row=2, column=0, pady=5)

        # --- Row 2: Config File (CSV) ---
        # Note: Optimization configs are still CSV based on your code
        tk.Label(main_frame, text="PLAY CONFIGURATION FILE (.CSV)", font=FONT_LABEL, bg=LAKERS_PURPLE, fg=LAKERS_GOLD).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        self.config_path_var = tk.StringVar()
        
        self.entry_config = tk.Entry(main_frame, textvariable=self.config_path_var, width=50, font=FONT_ENTRY, **entry_config)
        self.entry_config.grid(row=4, column=0, sticky=tk.W, padx=(0, 10), ipady=4)
        
        ttk.Button(main_frame, text="BROWSE", command=self.browse_config, style="Lakers.TButton").grid(row=4, column=1)

        # Spacer
        tk.Label(main_frame, text="", bg=LAKERS_PURPLE).grid(row=5, column=0, pady=5)

        # --- Row 3: Output Folder ---
        tk.Label(main_frame, text="OUTPUT FOLDER", font=FONT_LABEL, bg=LAKERS_PURPLE, fg=LAKERS_GOLD).grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        self.output_folder_var = tk.StringVar()
        self.entry_folder = tk.Entry(main_frame, textvariable=self.output_folder_var, width=50, font=FONT_ENTRY, **entry_config)
        self.entry_folder.grid(row=7, column=0, sticky=tk.W, padx=(0, 10), ipady=4)
        
        ttk.Button(main_frame, text="BROWSE", command=self.browse_output, style="Lakers.TButton").grid(row=7, column=1)

        # Spacer
        tk.Label(main_frame, text="", bg=LAKERS_PURPLE).grid(row=8, column=0, pady=5)

        # --- Row 4: Output Filename ---
        tk.Label(main_frame, text="OUTPUT FILENAME (.xlsx)", font=FONT_LABEL, bg=LAKERS_PURPLE, fg=LAKERS_GOLD).grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        
        self.output_name_var = tk.StringVar(value="output.xlsx")
        self.entry_name = tk.Entry(main_frame, textvariable=self.output_name_var, width=50, font=FONT_ENTRY, **entry_config)
        self.entry_name.grid(row=10, column=0, sticky=tk.W, padx=(0, 10), ipady=4)

        # Spacer
        tk.Label(main_frame, text="", bg=LAKERS_PURPLE).grid(row=11, column=0, pady=5)

        # --- Row 5: Play Selection ---
        tk.Label(main_frame, text="SELECT PLAY", font=FONT_LABEL, bg=LAKERS_PURPLE, fg=LAKERS_GOLD).grid(row=12, column=0, sticky=tk.W, pady=(0, 5))
        
        self.play_var = tk.StringVar()
        self.combo_play = ttk.Combobox(main_frame, textvariable=self.play_var, state="readonly", font=FONT_ENTRY, width=48)
        
        # Initial State: Prompt user to load config
        self.combo_play['values'] = ["Please load config file first..."]
        self.combo_play.current(0)
        
        self.combo_play.grid(row=13, column=0, sticky=tk.W, pady=(0, 20), ipady=4)

        # --- Row 6: BIG OPTIMIZE BUTTON ---
        self.btn_optimize = ttk.Button(
            main_frame, 
            text="RUN OPTIMIZATION", 
            command=self.run_optimization,
            style="Lakers.TButton"
        )
        self.btn_optimize.grid(row=14, column=0, columnspan=2, sticky="ew", pady=10, ipady=5)
        
    def browse_input(self):
        # Updated to filter for Excel files
        filename = filedialog.askopenfilename(
            title="Select Player Data (Excel)", 
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename: self.input_path_var.set(filename)
        
    def browse_config(self):
        filename = filedialog.askopenfilename(
            title="Select Play Configs (CSV)", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename: 
            self.config_path_var.set(filename)
            self.update_play_dropdown()

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder: self.output_folder_var.set(folder)

    def update_play_dropdown(self):
        config_path = self.config_path_var.get().strip()
        if config_path and os.path.exists(config_path):
            lineup_optimizer.load_play_configs(config_path)
            if lineup_optimizer.PLAY_CONFIGS:
                self.combo_play['values'] = list(lineup_optimizer.PLAY_CONFIGS.keys())
                self.combo_play.current(0)
            else:
                self.combo_play['values'] = ["Error: File is empty or invalid"]
                self.combo_play.current(0)
        else:
            self.combo_play['values'] = ["Please load config file first..."]
            self.combo_play.current(0)

    def run_optimization(self):
        input_path = self.input_path_var.get().strip()
        config_path = self.config_path_var.get().strip()
        output_folder = self.output_folder_var.get().strip()
        output_name = self.output_name_var.get().strip()
        selected_play = self.play_var.get()

        # --- Validation ---
        if not config_path or not os.path.exists(config_path):
            messagebox.showerror("Configuration Error", "Please select a valid Play Configuration CSV file.")
            return
        
        # Ensure latest config is loaded
        lineup_optimizer.load_play_configs(config_path)
        if not lineup_optimizer.PLAY_CONFIGS:
             messagebox.showerror("Configuration Error", "Config file loaded but contained no valid plays.")
             return

        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Validation Error", "Please select a valid input Excel file.")
            return
        
        # Validating Excel Extension
        if not input_path.lower().endswith('.xlsx'):
             messagebox.showwarning("Warning", "Input file does not have .xlsx extension. Optimization may fail.")

        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Validation Error", "Please select a valid output folder.")
            return
            
        if not output_name.lower().endswith('.xlsx'):
             messagebox.showerror("Validation Error", "Output filename must end with .xlsx")
             return
        
        if selected_play not in lineup_optimizer.PLAY_CONFIGS:
             messagebox.showerror("Validation Error", "Please select a valid play from the dropdown.")
             return

        full_output_path = os.path.join(output_folder, output_name)

        # --- Execution with Capture ---
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output 

        success = False
        output_text = ""
        
        try:
            lineup_optimizer.solve_lineup_optimization(input_path, selected_play, full_output_path)
            output_text = captured_output.getvalue()
            
            if "Infeasible" in output_text:
                success = False
                output_text += "\n\n[STATUS] Optimization Failed: Infeasible."
            elif "Expected Net Points" in output_text: # Updated check string based on new optimizer code
                success = True
                output_text += f"\n\n[STATUS] Optimization Successful!\n[EXPORT] Excel saved to: {full_output_path}"
            else:
                success = False
                output_text += "\n\n[STATUS] Unknown status. Check output."
                
        except Exception as e:
            output_text = captured_output.getvalue() + f"\n[CRITICAL ERROR] Execution failed: {e}"
            success = False
        finally:
            sys.stdout = original_stdout 

        # --- Show Popup ---
        self.show_results_popup(output_text, success)

    def show_results_popup(self, text_content, success):
        popup = tk.Toplevel(self.root)
        popup.title("Lineup Results")
        popup.geometry("800x600")
        
        popup_bg = "#1a1a1a"
        popup.configure(bg=popup_bg)

        status_text = "OPTIMIZATION RESULTS"
        status_color = LAKERS_GOLD if success else "#D9534F"
        
        tk.Label(popup, text=status_text, font=FONT_HEADER, bg=popup_bg, fg=status_color).pack(pady=15)

        txt_area = scrolledtext.ScrolledText(
            popup, width=90, height=25, 
            font=FONT_RESULT, 
            bg="black", fg="white", insertbackground="white",
            bd=1, relief="solid"
        )
        txt_area.pack(padx=20, pady=10, expand=True, fill='both')
        txt_area.insert(tk.END, text_content)
        txt_area.configure(state='disabled') 

        ttk.Button(
            popup, text="CLOSE WINDOW", command=popup.destroy,
            style="Lakers.TButton"
        ).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = LineupOptimizerApp(root)
    root.mainloop()