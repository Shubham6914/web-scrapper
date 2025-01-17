# config_manager.py
"""This ConfigManager class handles:

Directory setup and management
Configuration loading/saving
Chrome options setup
Logging functionality
"""

from selenium.webdriver.chrome.options import Options
import os
import json
import datetime

class ConfigManager:
    def __init__(self):
        # Directory Setup
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = os.path.join(self.app_dir, 'chrome-user-data')
        self.download_dir = os.path.join(self.app_dir, 'files')
        self.log_dir = os.path.join(self.app_dir, 'logs')
        self.config_file = os.path.join(self.app_dir, 'config.json')
        
        # Create necessary directories
        self.create_directories()
        
        # Initialize config
        self.config = self.load_config()
        
        # Setup logging
        self.log_file = os.path.join(
            self.log_dir, 
            f'session_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )

    def create_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.user_data_dir, self.download_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'lastPage': 1,
            'lastIndex': 0
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.log_message(f"Error loading config: {str(e)}")
                return default_config
        return default_config

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            self.log_message(f"Error saving config: {str(e)}")

    def get_chrome_options(self):
        """Setup and return Chrome options"""
        chrome_options = Options()
        
        # Basic Chrome options
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-data-dir={self.user_data_dir}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-allow-origins=*')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')

        # Download preferences
        chrome_prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        return chrome_options

    def log_message(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a') as f:
            f.write(f'[{timestamp}] {message}\n')

    def update_config(self, page, index):
        """Update and save configuration"""
        self.config['lastPage'] = page
        self.config['lastIndex'] = index
        self.save_config()

    def reset_index(self):
        """Reset index in configuration"""
        self.config['lastIndex'] = 0
        self.save_config()

    def get_directories(self):
        """Return dictionary of all directory paths"""
        return {
            'app_dir': self.app_dir,
            'user_data_dir': self.user_data_dir,
            'download_dir': self.download_dir,
            'log_dir': self.log_dir
        }