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
"""This ConfigManager class handles:
Directory setup and management with category-subcategory structure
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
        # Base Directory Setup
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = os.path.join(self.app_dir, 'chrome-user-data')
        self.insurance_files_dir = os.path.join(self.app_dir, 'Insurance_files')
        self.log_dir = os.path.join(self.app_dir, 'logs')
        self.config_file = os.path.join(self.app_dir, 'config.json')
        
        # Create base directories
        self.create_base_directories()
        
        # Initialize config
        self.config = self.load_config()
        
        # Setup logging
        self.log_file = os.path.join(
            self.log_dir, 
            f'session_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        
        # Track current category and subcategory
        self.current_category = None
        self.current_subcategory = None
        self.current_download_dir = None

    def create_base_directories(self):
        """Create base directories if they don't exist"""
        for directory in [self.user_data_dir, self.insurance_files_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.log_message(f"Created directory: {directory}")

    def setup_category_directory(self, category):
        """
        Setup directory for a new category
        Args:
            category: Category name
        Returns:
            str: Path to category directory
        """
        self.current_category = category
        category_dir = os.path.join(self.insurance_files_dir, category)
        
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
            self.log_message(f"Created category directory: {category_dir}")
            
        return category_dir

    def setup_subcategory_directory(self, category, subcategory):
        """
        Setup directory for a new subcategory
        Args:
            category: Category name
            subcategory: Subcategory name
        Returns:
            str: Path to subcategory directory
        """
        self.current_subcategory = subcategory
        category_dir = os.path.join(self.insurance_files_dir, category)
        subcategory_dir = os.path.join(category_dir, subcategory)
        
        if not os.path.exists(subcategory_dir):
            os.makedirs(subcategory_dir)
            self.log_message(f"Created subcategory directory: {subcategory_dir}")
        
        # Update current download directory
        self.current_download_dir = subcategory_dir
        return subcategory_dir

    def get_current_download_dir(self):
        """Get current download directory"""
        return self.current_download_dir

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'current_category': None,
            'current_subcategory': None,
            'completed_categories': [],
            'completed_subcategories': {}
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
                json.dump(self.config, f, indent=4)
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

        # Download preferences - using current subcategory directory
        chrome_prefs = {
            "download.default_directory": self.current_download_dir or self.insurance_files_dir,
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

    def update_category_progress(self, category, subcategory):
        """Update category and subcategory progress"""
        self.config['current_category'] = category
        self.config['current_subcategory'] = subcategory
        self.save_config()

    def mark_subcategory_complete(self, category, subcategory):
        """Mark a subcategory as completed"""
        if category not in self.config['completed_subcategories']:
            self.config['completed_subcategories'][category] = []
        
        if subcategory not in self.config['completed_subcategories'][category]:
            self.config['completed_subcategories'][category].append(subcategory)
            self.save_config()

    def mark_category_complete(self, category):
        """Mark a category as completed"""
        if category not in self.config['completed_categories']:
            self.config['completed_categories'].append(category)
            self.save_config()

    def get_directory_structure(self):
        """Return current directory structure"""
        return {
            'base_dir': self.app_dir,
            'user_data_dir': self.user_data_dir,
            'insurance_files_dir': self.insurance_files_dir,
            'log_dir': self.log_dir,
            'current_category': self.current_category,
            'current_subcategory': self.current_subcategory,
            'current_download_dir': self.current_download_dir
        }