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

class LoldleSolver(DailyGame):
    def create_ui(self, parent_frame):
    
        self.init_chrome()
    
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
    def update_grid(self):
        pass
    
    def get_suggestion(self):
        pass
    
    def reset_constraints(self):
        pass
    
    def cleanup(self):
        pass