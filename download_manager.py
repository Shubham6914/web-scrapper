# download_manager.py

"""
Key features of DownloadManager:

Handles complete download process
Document title extraction and cleaning
Download button interaction
Modal handling
File verification and renaming
Progress tracking and reporting
Error handling and logging
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

class DownloadManager:
    def __init__(self, driver, config_manager, download_tracker, name_handler, report_manager):
        """
        Initialize Download Manager
        
        Parameters:
        - driver: Selenium WebDriver instance
        - config_manager: ConfigManager instance
        - download_tracker: DownloadTracker instance
        - name_handler: DocumentNameHandler instance
        - report_manager: DownloadReportManager instance
        """
        self.driver = driver
        self.config_manager = config_manager
        self.download_tracker = download_tracker
        self.name_handler = name_handler
        self.report_manager = report_manager
        self.wait = WebDriverWait(self.driver, 10)

    def get_document_title(self):
        """Extract and clean document title"""
        try:
            title_element = self.driver.find_element(By.CSS_SELECTOR, '[data-e2e="doc_page_title"]')
            document_title = title_element.text
            # Clean title for filename
            document_title = ''.join(c for c in document_title if c.isalnum() or c in ' -')
            document_title = ' '.join(document_title.split())
            self.config_manager.log_message(f"Found document title: {document_title}")
            return document_title
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
            self.driver.execute_script('arguments[0].style.color = "red";', button)
            
            # Scroll button into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            
            try:
                button.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", button)
            
            return True
            
        except Exception as e:
            self.config_manager.log_message(f"Error finding download button: {str(e)}")
            return False

    def handle_download_modal(self, document_title):
        """Handle the download modal and initiate download"""
        try:
            # Wait for and find modal download button
            modal_download_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-e2e="modal-download-button"]'))
            )

            if not modal_download_button:
                return False

            # Get download URL and original filename
            download_url = modal_download_button.get_attribute('href')
            original_filename = os.path.basename(download_url.split('?')[0])
            
            # Log information
            self.config_manager.log_message(f"Download URL: {download_url}")
            self.config_manager.log_message(f"Original filename: {original_filename}")
            
            # Generate clean filename
            document_title = document_title.strip() if document_title else original_filename
            cleaned_title = self.name_handler.generate_unique_name(
                document_title,
                original_filename,
                download_url
            )
            
            # Set download attributes
            self.driver.execute_script("""
                var link = arguments[0];
                var fileName = arguments[1];
                link.setAttribute('download', fileName);
                link.setAttribute('target', '_blank');
            """, modal_download_button, cleaned_title)

            # Click download button
            modal_download_button.click()
            self.config_manager.log_message("Clicked download button")
            
            return cleaned_title, download_url
            
        except Exception as e:
            self.config_manager.log_message(f"Error in download modal: {str(e)}")
            return None, None

    def verify_and_rename_file(self, cleaned_title, url):
        """Verify download and rename file if necessary"""
        try:
            # Wait for download to complete
            time.sleep(15)
            
            # Get downloaded files
            download_dir = self.config_manager.download_dir
            downloaded_files = sorted(
                [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))],
                key=lambda x: os.path.getmtime(os.path.join(download_dir, x))
            )
            
            if not downloaded_files:
                return False
                
            latest_file = downloaded_files[-1]
            old_path = os.path.join(download_dir, latest_file)
            new_path = os.path.join(download_dir, cleaned_title)
            
            # Only rename if necessary and preserve extension
            if old_path != new_path:
                # Verify extensions match
                old_ext = os.path.splitext(latest_file)[1].lower()
                new_ext = os.path.splitext(cleaned_title)[1].lower()
                
                if old_ext != new_ext:
                    self.config_manager.log_message(
                        f"Warning: Extension mismatch - Original: {old_ext}, New: {new_ext}"
                    )
                    # Use original extension
                    cleaned_title = f"{os.path.splitext(cleaned_title)[0]}{old_ext}"
                    new_path = os.path.join(download_dir, cleaned_title)
                
                os.rename(old_path, new_path)
                self.config_manager.log_message(f"Renamed file from {latest_file} to {cleaned_title}")
                
                # Update tracking and reports
                self.download_tracker.record_download()
                
                try:
                    file_size = os.path.getsize(new_path)
                    self.report_manager.add_download_record(
                        filename=cleaned_title,
                        document_title=cleaned_title,
                        url=url,
                        file_size=file_size
                    )
                except Exception as e:
                    self.config_manager.log_message(f"Error updating download report: {str(e)}")
                
                return True
                
        except Exception as e:
            self.config_manager.log_message(f"Error during file verification: {str(e)}")
            return False

    def download_document(self, url):
        """
        Main method to handle complete document download process
        
        Returns:
        - Boolean indicating download success
        """
        try:
            # Navigate to document page
            self.driver.get(url)
            self.driver.execute_script('document.body.style.zoom = "200%";')
            
            # Get document title
            document_title = self.get_document_title()
            
            # Find and click download button
            if not self.find_and_click_download_button():
                return False
            
            # Handle download modal
            cleaned_title, download_url = self.handle_download_modal(document_title)
            if not cleaned_title:
                return False
            
            # Verify and rename downloaded file
            return self.verify_and_rename_file(cleaned_title, url)
            
        except Exception as e:
            self.config_manager.log_message(f"Error downloading document: {str(e)}")
            return False