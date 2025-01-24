# auth_manager.py

"""Key features of AuthManager:

Handles complete login process
CAPTCHA verification
OTP handling
Multiple retry attempts
Detailed logging
Random delays for human-like behavior
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
class AuthManager:
    def __init__(self, driver, config_manager):
        """
        Initialize Authentication Manager
        
        Parameters:
        - driver: Selenium WebDriver instance
        - config_manager: ConfigManager instance for logging
        """
        self.driver = driver
        self.config_manager = config_manager
        self.wait_time = 10
        self.credentials = {
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD')
        }

    def random_sleep(self):
        """Add random delay between actions"""
        sleep_time = random.randint(3, 8)
        time.sleep(sleep_time)

    def check_login_status(self):
        """
        Check if already logged in
        Returns: Boolean indicating login status
        """
        try:
            wait = WebDriverWait(self.driver, 5)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.sign_out_button')))
            self.config_manager.log_message('Already logged in, proceeding to search page.')
            return True
        except (TimeoutException, NoSuchElementException):
            self.config_manager.log_message('Not logged in, performing login.')
            return False

    def handle_captcha(self):
        """Handle CAPTCHA verification"""
        try:
            iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')
            self.driver.switch_to.frame(iframe)
            self.driver.find_element(By.CSS_SELECTOR, '.recaptcha-checkbox-border').click()
            self.config_manager.log_message('Clicked on CAPTCHA checkbox')
            self.driver.switch_to.default_content()
            return True
        except Exception as e:
            self.config_manager.log_message(f"Error clicking CAPTCHA: {str(e)}")
            return False

    def handle_otp(self):
        """Handle OTP verification"""
        try:
            # Wait for OTP input field
            otp_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="code"]'))
            )
            self.config_manager.log_message('OTP input field found')
            
            # Wait for user to input OTP manually
            self.config_manager.log_message('Waiting for manual OTP input...')
            WebDriverWait(self.driver, 300).until(
                lambda driver: driver.find_element(By.CSS_SELECTOR, 'input[name="code"]').get_attribute('value') != ''
            )
            self.config_manager.log_message('OTP entered')

            # Click verify button
            verify_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            verify_button.click()
            self.config_manager.log_message('Clicked verify button')

            # Wait for successful login confirmation
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.sign_out_button'))
            )
            return True

        except TimeoutException:
            self.config_manager.log_message('No OTP verification required or timeout waiting for OTP')
            return False
        except Exception as e:
            self.config_manager.log_message(f'Error during OTP handling: {str(e)}')
            return False

    def perform_login(self):
        """
        Perform complete login process
        Returns: Boolean indicating login success
        """
        try:
            # Check if already logged in
            if self.check_login_status():
                return True

            # Navigate to login page
            self.driver.get('https://auth.scribd.com/u/login')
            
            # Wait for login form to be visible
            wait = WebDriverWait(self.driver, self.wait_time)
            
            # Enter credentials with explicit waits
            username_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
            username_field.send_keys(self.credentials['username'])
            self.config_manager.log_message('Entered username')
            
            password_field = wait.until(EC.presence_of_element_located((By.ID, 'password')))
            password_field.send_keys(self.credentials['password'])
            self.config_manager.log_message('Entered password')

            # Handle CAPTCHA if present
            if self.handle_captcha():
                time.sleep(30)  # Wait after CAPTCHA
                self.config_manager.log_message('Waited for 30 seconds after CAPTCHA')
                self.random_sleep()

            # Try multiple selectors for login button
            login_button_selectors = [
                (By.NAME, 'action'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, '.login_button'),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]")
            ]

            for selector_type, selector in login_button_selectors:
                try:
                    login_button = wait.until(EC.element_to_be_clickable((selector_type, selector)))
                    login_button.click()
                    self.config_manager.log_message(f'Clicked login button using selector: {selector}')
                    break
                except Exception:
                    continue
            else:
                self.config_manager.log_message("Could not find login button with any selector")
                return False

            # Handle OTP if required
            if self.handle_otp():
                self.config_manager.log_message('Successfully logged in after OTP verification')
                return True

            # Final login check with extended wait
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.sign_out_button'))
                )
                self.config_manager.log_message('Login successful - found sign out button')
                return True
            except TimeoutException:
                self.config_manager.log_message('Login failed - could not verify successful login')
                return False

        except Exception as e:
            self.config_manager.log_message(f"Critical error during login: {str(e)}")
            return False
        
        
    def ensure_login(self):
        """
        Ensure user is logged in, retry if necessary
        Returns: Boolean indicating final login status
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.perform_login():
                    return True
                self.config_manager.log_message(f"Login attempt {attempt + 1} failed, retrying...")
                time.sleep(5)
            except Exception as e:
                self.config_manager.log_message(f"Error in login attempt {attempt + 1}: {str(e)}")
        
        self.config_manager.log_message("All login attempts failed")
        return False