import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

class DownloadManager:
    def __init__(self, driver, config_manager, download_tracker, name_handler, progress_tracker, url_manager):
        """
        Initialize Download Manager
        Args:
            driver: Selenium WebDriver instance
            config_manager: ConfigManager instance
            download_tracker: DownloadTracker instance
            name_handler: DocumentNameHandler instance
            progress_tracker: ProgressTracker instance
            url_manager: ProcessedURLManager instance
        """
        self.driver = driver
        self.config_manager = config_manager
        self.download_tracker = download_tracker
        self.name_handler = name_handler
        self.progress_tracker = progress_tracker
        self.url_manager = url_manager
        self.wait = WebDriverWait(self.driver, 10)

    def download_document(self, url, category, subcategory):
        """
        Main method to handle document download process
        Args:
            url: Document URL
            category: Current category
            subcategory: Current subcategory
        Returns:
            bool: Download success status
        """
        try:
            # Check if URL already processed
            if self.url_manager.is_processed(url):
                self.config_manager.log_message(f"URL already processed: {url}")
                return False

            self.config_manager.log_message(f"\nDownloading document from {url}")
            self.config_manager.log_message(f"Category: {category}, Subcategory: {subcategory}")
            
            # Navigate to document
            self.driver.get(url)
            self.driver.execute_script('document.body.style.zoom = "200%";')
            
            # Get document title
            document_title = self.get_document_title()
            if not document_title:
                return False
            
            # Handle download button
            if not self.find_and_click_download_button():
                return False
            
            # Handle modal and get file info
            cleaned_title = self.handle_download_modal(document_title, category, subcategory)
            if not cleaned_title:
                return False
            
            # Verify download
            if self.verify_download(cleaned_title, category, subcategory):
                # Mark URL as processed
                self.url_manager.add_url(category, subcategory, url)
                # Record download
                self.download_tracker.record_download(category, subcategory)
                self.progress_tracker.update_search_progress(category, subcategory, True)
                return True
                
            return False
            
        except Exception as e:
            self.config_manager.log_message(f"Error downloading document: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return False

    def get_document_title(self):
        """Extract and clean document title"""
        try:
            title_element = self.driver.find_element(By.CSS_SELECTOR, '[data-e2e="doc_page_title"]')
            document_title = title_element.text
            document_title = ''.join(c for c in document_title if c.isalnum() or c in ' -')
            return ' '.join(document_title.split())
        except Exception as e:
            self.config_manager.log_message(f"Could not find document title: {str(e)}")
            return f'document_{int(time.time())}'

    def find_and_click_download_button(self):
        """Find and click the download button"""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '[data-e2e="doc-actions-download-button-doc_actions"]'
            )
            
            if not elements:
                return False
                
            button = elements[0]
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            
            try:
                button.click()
            except:
                self.driver.execute_script("arguments[0].click();", button)
            
            return True
            
        except Exception as e:
            self.config_manager.log_message(f"Error with download button: {str(e)}")
            return False

    def handle_download_modal(self, document_title, category, subcategory):
        """
        Handle download modal and initiate download
        Args:
            document_title: Document title
            category: Current category
            subcategory: Current subcategory
        Returns:
            str: Cleaned file title or None
        """
        try:
            modal_download_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-e2e="modal-download-button"]'))
            )

            if not modal_download_button:
                return None

            download_url = modal_download_button.get_attribute('href')
            original_filename = os.path.basename(download_url.split('?')[0])
            
            cleaned_title = self.name_handler.generate_unique_name(
                document_title,
                original_filename,
                download_url,
                category,
                subcategory
            )
            
            self.driver.execute_script("""
                arguments[0].setAttribute('download', arguments[1]);
                arguments[0].setAttribute('target', '_blank');
            """, modal_download_button, cleaned_title)

            modal_download_button.click()
            return cleaned_title
            
        except Exception as e:
            self.config_manager.log_message(f"Error in download modal: {str(e)}")
            return None

    def verify_download(self, cleaned_title, category, subcategory):
        """
        Verify download completion and move file to correct directory
        Args:
            cleaned_title: Cleaned file title
            category: Current category
            subcategory: Current subcategory
        Returns:
            bool: Verification status
        """
        try:
            time.sleep(15)  # Wait for download
            
            # Get current subcategory directory
            current_dir = self.config_manager.get_current_download_dir()
            if not current_dir:
                return False
                
            downloaded_files = sorted(
                [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))],
                key=lambda x: os.path.getmtime(os.path.join(current_dir, x))
            )
            
            if not downloaded_files:
                return False
                
            latest_file = downloaded_files[-1]
            old_path = os.path.join(current_dir, latest_file)
            new_path = os.path.join(current_dir, cleaned_title)
            
            if old_path != new_path:
                os.rename(old_path, new_path)
                
            return os.path.exists(new_path)
                
        except Exception as e:
            self.config_manager.log_message(f"Error verifying download: {str(e)}")
            return False