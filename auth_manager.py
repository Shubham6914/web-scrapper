"""
AuthManager: Handles Scribd authentication with robust login verification and error handling
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    StaleElementReferenceException,
    ElementClickInterceptedException
)
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()

class AuthManager:
    def __init__(self, driver, config_manager, debug=False):
        self.driver = driver
        self.config_manager = config_manager
        self.wait_time = 10
        self.debug = debug
        self.session_valid = False
        
        self.credentials = {
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
        
        if not all(self.credentials.values()):
            self.config_manager.log_message("ERROR: Missing credentials in .env file")
            raise ValueError("Missing credentials")

    def wait_for_element(self, selector_type, selector, timeout=10, clickable=False):
        """Enhanced element wait with retry mechanism"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            condition = (
                EC.element_to_be_clickable if clickable 
                else EC.presence_of_element_located
            )
            return wait.until(condition((selector_type, selector)))
        except Exception as e:
            if self.debug:
                self.config_manager.log_message(f"Element not found: {selector}")
            return None

    def random_sleep(self, min_time=2, max_time=5):
        """Randomized delay to simulate human behavior"""
        sleep_time = random.uniform(min_time, max_time)
        time.sleep(sleep_time)

    def verify_logged_in_state(self):
        """Verify login status using Scribd-specific indicators"""
        try:
            # Check URL first
            current_url = self.driver.current_url
            if 'scribd.com/home' in current_url:
                return True

            # Check for Scribd-specific elements
            indicators = [
                (By.CSS_SELECTOR, '.upload_button'),
                (By.CSS_SELECTOR, '.account_button'),
                (By.CSS_SELECTOR, 'button[aria-label="Upload"]'),
                (By.CSS_SELECTOR, 'button[aria-label="Account"]'),
                (By.CSS_SELECTOR, '.profile-menu'),
                (By.CSS_SELECTOR, '.user_menu')
            ]

            for selector_type, selector in indicators:
                element = self.wait_for_element(selector_type, selector, timeout=2)
                if element:
                    return True

            return False

        except Exception as e:
            self.config_manager.log_message(f"Error in verification: {str(e)}")
            return False

    def handle_captcha(self):
        """Handle CAPTCHA verification"""
        try:
            iframe = self.wait_for_element(By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')
            if iframe:
                self.driver.switch_to.frame(iframe)
                captcha_box = self.wait_for_element(
                    By.CSS_SELECTOR, 
                    '.recaptcha-checkbox-border',
                    clickable=True
                )
                if captcha_box:
                    captcha_box.click()
                    self.config_manager.log_message('CAPTCHA clicked')
                    self.driver.switch_to.default_content()
                    return True
            return False
        except Exception as e:
            self.config_manager.log_message(f"CAPTCHA error: {str(e)}")
            self.driver.switch_to.default_content()
            return False

    def perform_login(self):
        """Execute login process"""
        try:
            if self.verify_logged_in_state():
                self.config_manager.log_message('Already logged in')
                return True

            # Navigate to login page
            self.driver.get('https://auth.scribd.com/u/login')
            self.random_sleep(3, 5)

            # Enter credentials
            username_field = self.wait_for_element(By.ID, 'username')
            password_field = self.wait_for_element(By.ID, 'password')

            if not username_field or not password_field:
                self.config_manager.log_message('Login form not found')
                return False

            username_field.clear()
            username_field.send_keys(self.credentials['username'])
            self.random_sleep(1, 2)
            
            password_field.clear()
            password_field.send_keys(self.credentials['password'])
            self.config_manager.log_message('Credentials entered')

            # Handle CAPTCHA
            if self.handle_captcha():
                self.random_sleep(15, 20)

            # Click login button
            login_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, '.login_submit_button'),
                (By.CSS_SELECTOR, '.sign_in_button'),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]")
            ]

            for selector_type, selector in login_selectors:
                button = self.wait_for_element(selector_type, selector, clickable=True)
                if button:
                    button.click()
                    self.config_manager.log_message('Login button clicked')
                    break

            # Wait for login completion
            self.random_sleep(5, 8)

            # Verify login success
            max_verify_attempts = 3
            for i in range(max_verify_attempts):
                if self.verify_logged_in_state():
                    self.config_manager.log_message('Login successful')
                    self.session_valid = True
                    return True
                self.random_sleep(2, 3)

            self.config_manager.log_message('Login verification failed')
            return False

        except Exception as e:
            self.config_manager.log_message(f"Login error: {str(e)}")
            return False

    def ensure_login(self):
        """Ensure successful login with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.perform_login():
                    return True
                
                self.config_manager.log_message(f"Login attempt {attempt + 1} failed")
                self.random_sleep(5, 10)
                
            except Exception as e:
                self.config_manager.log_message(f"Error in attempt {attempt + 1}: {str(e)}")
        
        self.config_manager.log_message("All login attempts failed")
        return False

    def verify_session(self):
        """Verify current session validity"""
        try:
            if self.verify_logged_in_state():
                self.session_valid = True
                return True
            
            self.session_valid = False
            return self.ensure_login()
            
        except Exception as e:
            self.config_manager.log_message(f"Session verification error: {str(e)}")
            self.session_valid = False
            return False

    def is_session_valid(self):
        """Check current session validity"""
        return self.session_valid