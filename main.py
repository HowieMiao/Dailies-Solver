import tkinter as tk
from tkinter import ttk, messagebox
import importlib.util
from pathlib import Path
import sys

class GameSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Daily Game Solver")
        self.current_game = None
        
        # Get project root
        self.project_root = Path(__file__).parent
        
        # Add to Python path
        sys.path.append(str(self.project_root))
        
        self.games = self.find_available_games()
        self.create_selector_ui()

    def find_available_games(self):
        games_dir = self.project_root / "games"
        return [d.name for d in games_dir.iterdir() if d.is_dir() and (d / "solver.py").exists()]

    def create_selector_ui(self):
        main_frame = ttk.Frame(self.root, padding=20,)
        main_frame.pack()

        ttk.Label(main_frame, text="Select Game:").pack(pady=10,padx=80)
        
        # Initialize with blank selection
        self.game_var = tk.StringVar(value="")  # Set to empty string
        
        self.selector = ttk.Combobox(
            main_frame, 
            textvariable=self.game_var,
            values=self.games,
            state="readonly"
        )
        self.selector.pack(pady=5)
        self.selector.bind("<<ComboboxSelected>>", self.load_game)
        
        # Remove auto-loading of first game
        self.game_container = ttk.Frame(main_frame)
        self.game_container.pack(pady=20, fill=tk.BOTH, expand=True)

    def load_game(self, event=None):
        # Cleanup previous game
        if self.current_game:
            self.current_game.cleanup()
            for widget in self.game_container.winfo_children():
                widget.destroy()

        # Load new game
        game_name = self.game_var.get()
        solver_path = self.project_root / "games" / game_name / "solver.py"
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"games.{game_name}.solver",
                str(solver_path)
            )
            
            if spec is None:
                raise ImportError(f"Could not load {game_name} solver")
                
            game_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(game_module)
            
            # Dynamically determine the solver class name
            class_name = f"{game_name.capitalize()}Solver"
            solver_class = getattr(game_module, class_name)
            
            # Initialize game
            self.current_game = solver_class()
            game_frame = self.current_game.create_ui(self.game_container)
            game_frame.pack(fill=tk.BOTH, expand=True)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {game_name}: {str(e)}")

    def run(self):
        self.root.mainloop()
        if self.current_game:
            self.current_game.cleanup()

if __name__ == "__main__":
    selector = GameSelector()
    selector.run()