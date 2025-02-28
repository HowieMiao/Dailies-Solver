import tkinter as tk
from abc import ABC, abstractmethod

class DailyGame(ABC):
    @abstractmethod
    def create_ui(self, parent_frame):
        pass
    
    @abstractmethod
    def update_grid(self):
        pass
    
    @abstractmethod
    def get_suggestion(self):
        pass
    
    @abstractmethod
    def reset_constraints(self):
        pass
    
    @abstractmethod
    def cleanup(self):
        pass