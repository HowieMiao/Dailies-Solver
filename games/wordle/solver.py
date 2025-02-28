import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from games.game_base import DailyGame  # Fixed import path

class WordleSolver(DailyGame):
    def __init__(self):
        self.driver = None
        self.service = None
        self.current_guesses = []
        self.color_states = {}
        self.manual_constraints = {
            'correct': {}, 
            'present': set(), 
            'absent': set()
        }
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
        self.driver.get("https://www.nytimes.com/games/wordle/index.html")

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
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset_constraints).pack(side=tk.LEFT, padx=5)

        # Grid Display
        self.grid_frame = ttk.Frame(main_frame)
        self.grid_frame.pack(pady=10)

        # Status Display
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=10)

        return main_frame

    def reset_constraints(self):
        self.color_states.clear()
        self.manual_constraints = {
            'correct': {},
            'present': set(),
            'absent': set()
        }
        self.force_refresh()
        self.status_label.config(text="Reset complete - synced with current game state")
    
    def auto_refresh(self):
        while True:
            if self.auto_update_var.get():
                self.update_grid()
            time.sleep(2)

    def force_refresh(self):
        self.update_grid()

    def update_grid(self):
        try:
            state = self.get_game_state()
            if state:
                game_data = state['states'][0]['data']
                new_guesses = [guess.upper() for guess in game_data.get('boardState', []) if guess]
                
                if new_guesses != self.current_guesses:
                    self.current_guesses = new_guesses
                    self.create_letter_grid(self.color_states)
                else:
                    self.apply_existing_constraints()
                
        except Exception as e:
            messagebox.showerror("Refresh Error", str(e))
            
    def apply_existing_constraints(self):
        for (row, col), color in self.color_states.items():
            try:
                if row < len(self.current_guesses) and col < len(self.current_guesses[row]):
                    self.update_constraints(row, col, color)
            except IndexError:
                continue
            
    def get_game_state(self):
        try:
            keys = self.driver.execute_script("return Object.keys(localStorage);")
            wordle_key = next((k for k in keys if k.startswith("games-state-wordleV2/")), None)
            
            if not wordle_key:
                return None
                
            state_json = self.driver.execute_script(
                f'return localStorage.getItem("{wordle_key}");'
            )
            return json.loads(state_json) if state_json else None
            
        except Exception as e:
            messagebox.showerror("State Error", str(e))
            return None

    def create_letter_grid(self, previous_colors=None):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.letter_buttons = []
        for row_idx, guess in enumerate(self.current_guesses):
            row_frame = ttk.Frame(self.grid_frame)
            row_frame.pack(pady=2)
            
            for col_idx, letter in enumerate(guess):
                bg_color = previous_colors.get((row_idx, col_idx), '#787c7e') if previous_colors else '#787c7e'
                
                btn = tk.Button(
                    row_frame,
                    text=letter,
                    width=3,
                    bg=bg_color,
                    fg='white' if bg_color == '#787c7e' else 'black',
                    command=lambda r=row_idx, c=col_idx: self.cycle_color(r, c)
                )
                btn.grid(row=0, column=col_idx, padx=2)
                self.letter_buttons.append((row_idx, col_idx, btn))
                
                self.update_constraints(row_idx, col_idx, bg_color)

        self.color_states = {
            (r, c): b.cget('bg')
            for r, c, b in self.letter_buttons
            if b.cget('bg') != '#787c7e'
        }

    def cycle_color(self, row_idx, col_idx):
        colors = ['#787c7e', '#c9b458', '#6aaa64']
        btn = next(b for r, c, b in self.letter_buttons if r == row_idx and c == col_idx)
        
        current_color = btn.cget('bg')
        next_color = colors[(colors.index(current_color) + 1) % len(colors)]
        
        btn.config(
            bg=next_color,
            fg='white' if next_color == '#787c7e' else 'black'
        )
        
        if next_color == '#787c7e':
            self.color_states.pop((row_idx, col_idx), None)
        else:
            self.color_states[(row_idx, col_idx)] = next_color
            
        self.update_constraints(row_idx, col_idx, next_color)

    def update_constraints(self, row_idx, col_idx, color):
        letter = self.current_guesses[row_idx][col_idx]
        color_map = {
            '#787c7e': 'absent',
            '#c9b458': 'present',
            '#6aaa64': 'correct'
        }
        status = color_map.get(color, 'absent')

        if status == 'correct':
            self.manual_constraints['correct'][col_idx] = letter
            if letter in self.manual_constraints['absent']:
                self.manual_constraints['absent'].remove(letter)
            if letter in self.manual_constraints['present']:
                self.manual_constraints['present'].remove(letter)
        elif status == 'present':
            self.manual_constraints['present'].add(letter)
            if letter in self.manual_constraints['absent']:
                self.manual_constraints['absent'].remove(letter)
            if col_idx in self.manual_constraints['correct']:
                del self.manual_constraints['correct'][col_idx]
        else:
            if letter not in self.manual_constraints['present'] and letter not in self.manual_constraints['correct'].values():
                self.manual_constraints['absent'].add(letter)
                
    def get_suggestion(self):
        """Implementation of abstract method from DailyGame"""
        return self.suggest_next()
    
    def suggest_next(self):
        with open('./games/wordle/valid_words.txt') as f:
            all_words = [word.strip().upper() for word in f]

        valid_words = []
        for word in all_words:
            valid = True
            
            for pos, letter in self.manual_constraints['correct'].items():
                if word[pos] != letter:
                    valid = False
                    break
                    
            for letter in self.manual_constraints['present']:
                if letter not in word:
                    valid = False
                    break
                    
            for letter in self.manual_constraints['absent']:
                if letter in word and letter not in self.manual_constraints['present']:
                    valid = False
                    break

            if valid:
                valid_words.append(word)

        if valid_words:
            suggestion = self.get_best_guess(valid_words)
            self.status_label.config(text=f"Suggested: {suggestion}")
            return suggestion
        else:
            self.status_label.config(text="No valid words found!")
            return None

    def get_best_guess(self, word_list):
        letter_scores = {}
        for word in word_list:
            for letter in set(word):
                letter_scores[letter] = letter_scores.get(letter, 0) + 1
        
        return max(word_list, 
                 key=lambda word: sum(letter_scores[letter] for letter in set(word)))

    def cleanup(self):
        if self.driver:
            self.driver.quit()
        if self.service:
            self.service.stop()