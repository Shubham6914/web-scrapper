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
        self.insurance_files_dir = os.path.join(self.app_dir, 'INSURANCE_FILES')
        self.log_dir = os.path.join(self.app_dir, 'logs')
        self.config_file = os.path.join(self.app_dir, 'config.json')
        
         # Define default configurations first
        self.default_config = {
            'current_category': None,
            'current_subcategory': None,
            'completed_categories': [],
            'completed_subcategories': {},
            'pagination': {
                'current_page': 1,
                'last_processed_page': 1,
                'urls_processed': 0
            }
        }
        
        # Add pagination configuration
        self.pagination_config = {
            'max_pages': 5,
            'results_per_page': 20  # Default value
        }
        # Create base directories silently first
        self._create_base_directories_silent()
        
        # Initialize log file path after directories are created
        self.log_file = os.path.join(
            self.log_dir, 
            f'session_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        
        # Initialize config
        self.config = self.load_config()
        
        # Track current category and subcategory
        self.current_category = None
        self.current_subcategory = None
        self.current_download_dir = None        
        
        # Log initialization
        self.log_message("ConfigManager initialized successfully")

    def _create_base_directories_silent(self):
        """Create base directories without logging"""
        for directory in [self.user_data_dir, self.insurance_files_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def log_message(self, message):
        """Log a message with timestamp"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f'[{timestamp}] {message}\n'
            
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
            print(log_entry.strip())  # Also print to console
        except Exception as e:
            print(f"Error writing to log: {str(e)}")
            print(f"Message was: {message}")

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
        """Load configuration from file with pagination support"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Ensure pagination configuration exists
                    if 'pagination' not in config:
                        config['pagination'] = self.default_config['pagination']
                    return config
            except Exception as e:
                self.log_message(f"Error loading config: {str(e)}")
                return self.default_config.copy()  # Return a copy of default config
        return self.default_config.copy()  # Return a copy of default config

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
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Download preferences
        download_dir = self.current_download_dir or self.insurance_files_dir
        chrome_prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
            "download.open_pdf_in_system_reader": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        # Remove automation flags and logging
        chrome_options.add_experimental_option('excludeSwitches', [
            'enable-automation',
            'enable-logging'
        ])
        
        return chrome_options

    
    def update_download_preferences(self, driver):
        """Update Chrome download preferences during runtime"""
        try:
            current_dir = self.current_download_dir or self.insurance_files_dir
            self.log_message(f"Updating download preferences to: {current_dir}")
            
            # Method 1: Try using Chrome options if available
            if hasattr(driver, 'options'):
                prefs = {
                    "download.default_directory": current_dir,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True,
                    "plugins.always_open_pdf_externally": True
                }
                driver.options.add_experimental_option("prefs", prefs)
                self.log_message("Updated preferences using Chrome options")
            
            # Method 2: Try using JavaScript
            js_script = f"""
                const prefs = {{
                    "download.default_directory": "{current_dir}",
                    "download.prompt_for_download": false,
                    "download.directory_upgrade": true,
                    "safebrowsing.enabled": true,
                    "plugins.always_open_pdf_externally": true
                }};
                Object.keys(prefs).forEach(key => {{
                    chrome.preferences.setPref(key, prefs[key]);
                }});
            """
            driver.execute_script(js_script)
            
            # Method 3: Try CDP command only if supported
            if hasattr(driver, 'execute_cdp_cmd'):
                driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                    'behavior': 'allow',
                    'downloadPath': current_dir
                })
                self.log_message("Updated download behavior using CDP command")
            
            self.log_message("Download preferences updated successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Error updating download preferences: {str(e)}")
            return False
    
    
    def update_category_progress(self, category, subcategory):
        """Update category and subcategory progress"""
        self.config['current_category'] = category
        self.config['current_subcategory'] = subcategory
        self.save_config()

    def mark_subcategory_complete(self, category, subcategory):
        """Mark a subcategory as completed with pagination reset"""
        try:
            if category not in self.config['completed_subcategories']:
                self.config['completed_subcategories'][category] = []
            
            if subcategory not in self.config['completed_subcategories'][category]:
                self.config['completed_subcategories'][category].append(subcategory)
                # Reset pagination for next subcategory
                self.reset_pagination(category, subcategory)
                self.save_config()
                self.log_message(f"Marked {category}/{subcategory} as complete")
        except Exception as e:
            self.log_message(f"Error marking subcategory complete: {str(e)}")

    def mark_category_complete(self, category):
        """Mark a category as completed"""
        if category not in self.config['completed_categories']:
            self.config['completed_categories'].append(category)
            self.save_config()
            
    def update_config(self, page, index):
        """Update and save configuration"""
        self.config['lastPage'] = page
        self.config['lastIndex'] = index
        self.save_config()

    def reset_index(self):
        """Reset index in configuration"""
        self.config['lastIndex'] = 0
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