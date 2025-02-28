import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import threading
import time

class WordleSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wordle Solver Pro")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Game state tracking
        self.manual_constraints = {
            'correct': {},
            'present': set(),
            'absent': set()
        }
        self.color_states = {}  # Tracks non-gray colors only
        self.current_guesses = []
        self.auto_update = True
        
        # Initialize Chrome driver
        self.init_chrome()
        
        # Create GUI elements
        self.create_widgets()
        
        # Start auto-update thread
        self.update_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.update_thread.start()

    def init_chrome(self):
        chrome_options = Options()
        # Suppress performance logging and metrics
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--disable-metrics")
        chrome_options.add_argument("--disable-metrics-reporting")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("detach", True)
        
        # Service configuration
        self.service = Service(
            ChromeDriverManager().install(),
        service_args=["--verbose", "--log-path=chromedriver.log"]
    )
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        self.driver.get("https://www.nytimes.com/games/wordle/index.html")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Control Panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        self.auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Auto-Refresh", 
                       variable=self.auto_update_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Force Refresh", 
                  command=self.force_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Suggest Next", 
                  command=self.suggest_next).pack(side=tk.LEFT, padx=5)

        # Guess Display
        self.grid_frame = ttk.Frame(main_frame)
        self.grid_frame.pack(pady=10)

        # Status Display
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=10)
        # Add Reset button to control frame
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset_constraints).pack(side=tk.LEFT, padx=5)
        
    def reset_constraints(self):
        # Clear all manual modifications
        self.color_states.clear()
        self.manual_constraints = {
            'correct': {},
            'present': set(),
            'absent': set()
        }
        
        # Force fresh load from storage
        self.force_refresh()
        self.status_label.config(text="Reset complete - synced with current game state")
    
    def auto_refresh(self):
        while True:
            if self.auto_update_var.get():
                self.root.after(0, self.update_grid)
            time.sleep(2)

    def force_refresh(self):
        self.update_grid()

    def update_grid(self):
        try:
            state = self.get_game_state()
            if state:
                game_data = state['states'][0]['data']
                new_guesses = [guess.upper() for guess in game_data.get('boardState', []) if guess]
                
                # Always preserve colors unless guesses changed
                if new_guesses != self.current_guesses:
                    self.current_guesses = new_guesses
                    self.create_letter_grid(self.color_states)
                else:
                    # Just update constraints from existing colors
                    self.apply_existing_constraints()
                
        except Exception as e:
            messagebox.showerror("Refresh Error", str(e))
            
    def apply_existing_constraints(self):
        # Reapply constraints from current color states
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
        # Clear existing grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Create new grid rows with dark gray default
        self.letter_buttons = []
        for row_idx, guess in enumerate(self.current_guesses):
            row_frame = ttk.Frame(self.grid_frame)
            row_frame.pack(pady=2)
            
            for col_idx, letter in enumerate(guess):
                # Get previous color if exists, else dark gray
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
                
                # Update constraints with initial color
                self.update_constraints(row_idx, col_idx, bg_color)

        # Update color states with non-gray colors
        self.color_states = {
            (r, c): b.cget('bg')
            for r, c, b in self.letter_buttons
            if b.cget('bg') != '#787c7e'
        }

    def cycle_color(self, row_idx, col_idx):
        colors = ['#787c7e', '#c9b458', '#6aaa64']  # Dark gray, Yellow, Green
        btn = next(b for r, c, b in self.letter_buttons if r == row_idx and c == col_idx)
        
        current_color = btn.cget('bg')
        next_color = colors[(colors.index(current_color) + 1) % len(colors)]
        
        # Update button appearance
        btn.config(
            bg=next_color,
            fg='white' if next_color == '#787c7e' else 'black'
        )
        
        # Update color states
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
        status = color_map.get(color, 'absent')  # Default to absent

        # Clear previous entries for this position
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

    def suggest_next(self):
        print(self.manual_constraints)
        with open('./wordle/valid_words.txt') as f:
            all_words = [word.strip().upper() for word in f]

        valid_words = []
        for word in all_words:
            valid = True
            
            # Check correct positions
            for pos, letter in self.manual_constraints['correct'].items():
                if word[pos] != letter:
                    valid = False
                    break
                    
            # Check present letters
            for letter in self.manual_constraints['present']:
                if letter not in word:
                    valid = False
                    break
                    
            # Check absent letters
            for letter in self.manual_constraints['absent']:
                if letter in word and letter not in self.manual_constraints['present']:
                    valid = False
                    break

            if valid:
                valid_words.append(word)

        if valid_words:
            suggestion = self.get_best_guess(valid_words)
            self.status_label.config(text=f"Suggested: {suggestion}")
        else:
            self.status_label.config(text="No valid words found!")

    def get_best_guess(self, word_list):
        letter_scores = {}
        for word in word_list:
            for letter in set(word):
                letter_scores[letter] = letter_scores.get(letter, 0) + 1
        
        return max(word_list, 
                 key=lambda word: sum(letter_scores[letter] for letter in set(word)))

    def on_close(self):
        self.driver.quit()
        self.service.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WordleSolverApp(root)
    root.mainloop()