import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from games.game_base import DailyGame

class LoldleSolver(DailyGame):
    def __init__(self):
        self.driver = None
        self.service = None
        self.current_guesses = []
        self.auto_update_var = tk.BooleanVar(value=True)
        self.init_chrome()
        self.update_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.update_thread.start()

    def init_chrome(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--disable-metrics")
        chrome_options.add_argument("--disable-metrics-reporting")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("detach", True)
        
        self.service = Service(
            ChromeDriverManager().install(),
            service_args=["--verbose", "--log-path=chromedriver.log"]
        )
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        self.driver.get("https://loldle.net/classic")

    def create_ui(self, parent_frame):
        main_frame = ttk.Frame(parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Control Panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        ttk.Checkbutton(control_frame, text="Auto-Refresh", 
                       variable=self.auto_update_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Force Refresh", 
                  command=self.force_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Suggest Next", 
                  command=self.suggest_next).pack(side=tk.LEFT, padx=5)

        # Grid Display
        self.grid_frame = ttk.Frame(main_frame)
        self.grid_frame.pack(pady=10)

        # Status Display
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=10)

        return main_frame

    def auto_refresh(self):
        while True:
            if self.auto_update_var.get():
                self.update_grid()
            time.sleep(2)

    def force_refresh(self):
        self.update_grid()

    def update_grid(self):
        try:
            # Fetch game state from Loldle
            game_state = self.get_game_state()
            
            if game_state:
                # Process and display the guesses
                self.current_guesses = game_state['guesses']
                self.create_letter_grid(game_state['results'])
                
        except Exception as e:
            messagebox.showerror("Refresh Error", str(e))

    def get_game_state(self):
        """
        Loldle stores game state in the HTML structure.
        Results can be:
        - correct (Green)
        - partial (Yellow)
        - incorrect (Red)
        - too-low (Red with up arrow)
        - too-high (Red with down arrow)
        """
        try:
            # Get all guess rows
            guess_rows = self.driver.find_elements(By.CLASS_NAME, "guess-row") #FIXME: This is not working
            
            guesses = []
            results = []
            
            for row in guess_rows:
                cells = row.find_elements(By.CLASS_NAME, "guess-cell")
                guess = "".join([cell.text for cell in cells])
                result = []
                
                for cell in cells:
                    classes = cell.get_attribute("class").split()
                    if 'correct' in classes:
                        result.append('correct')
                    elif 'partial' in classes:
                        result.append('partial')
                    elif 'too-low' in classes:
                        result.append('too-low')
                    elif 'too-high' in classes:
                        result.append('too-high')
                    else:
                        result.append('incorrect')
                
                guesses.append(guess)
                results.append(result)
            
            return {
                'guesses': guesses,
                'results': results
            }
            
        except Exception as e:
            messagebox.showerror("State Error", str(e))
            return None

    def create_letter_grid(self, results):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        for row_idx, (guess, result) in enumerate(zip(self.current_guesses, results)):
            row_frame = ttk.Frame(self.grid_frame)
            row_frame.pack(pady=2)
            
            for col_idx, (letter, res) in enumerate(zip(guess, result)):
                # Determine color and symbol based on result
                color_map = {
                    'correct': ('#6aaa64', ''),       # Green
                    'partial': ('#c9b458', ''),       # Yellow
                    'incorrect': ('#787c7e', ''),     # Gray
                    'too-low': ('#ff6961', '↑'),      # Red with up arrow
                    'too-high': ('#ff6961', '↓')      # Red with down arrow
                }
                bg_color, symbol = color_map.get(res, ('#787c7e', ''))
                
                label = tk.Label(
                    row_frame,
                    text=f"{letter}{symbol}",
                    width=4,
                    bg=bg_color,
                    fg='white' if bg_color == '#787c7e' else 'black',
                    font=('Arial', 12)
                )
                label.grid(row=0, column=col_idx, padx=2)

    def get_suggestion(self):
        """Implementation of abstract method from DailyGame"""
        return self.suggest_next()

    def suggest_next(self):
        # TODO: Implement Loldle-specific suggestion logic
        # This will require accessing champion data and filtering based on constraints
        suggestion = "Implement suggestion logic"
        self.status_label.config(text=f"Suggested: {suggestion}")
        return suggestion

    def cleanup(self):
        if self.driver:
            self.driver.quit()
        if self.service:
            self.service.stop()
    
    def reset_constraints(self):
        #     Reset all constraints and force a fresh load from the game state.
        self.current_guesses = []
        self.status_label.config(text="Reset complete - synced with current game state")
        self.force_refresh()