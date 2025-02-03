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
from selenium.webdriver.chrome.options import Options

import os
import time
import traceback

class DownloadManager:
    def __init__(self, driver, config_manager, download_tracker, name_handler, progress_tracker, url_manager, report_manager):
        self.driver = driver
        self.config_manager = config_manager
        self.download_tracker = download_tracker
        self.name_handler = name_handler
        self.progress_tracker = progress_tracker
        self.url_manager = url_manager
        self.report_manager = report_manager
        self.wait = WebDriverWait(self.driver, 10)

    def download_document(self, url, category, subcategory):
        """Main method to handle document download process"""
        try:
            self.config_manager.log_message(f"\nStarting download for: {url}")
            
            # Set Chrome preferences for download directory
            current_dir = self.config_manager.get_current_download_dir()
            chrome_options = Options()
            prefs = {
                "download.default_directory": current_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Update driver preferences
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
            
            # Navigate to document page
            self.driver.get(url)
            self.driver.execute_script('document.body.style.zoom = "200%";')
            
            # Get document title
            document_title = self.get_document_title()
            if not document_title:
                return False
            
            # Handle download button
            if self.find_and_click_download_button():
                self.config_manager.log_message("Download button clicked successfully")
            else:
                self.config_manager.log_message("Failed to click download button")
                return False
            
            # Handle modal
            cleaned_title, download_url = self.handle_download_modal(document_title, category, subcategory)
            if not cleaned_title or not download_url:
                self.config_manager.log_message("Failed to handle download modal")
                return False
            
            # Verify download
            return self.verify_and_rename_file(cleaned_title, download_url, category, subcategory)
                
        except Exception as e:
            self.config_manager.log_message(f"Error in download process: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return False
    def get_document_title(self):
        """Extract and clean document title"""
        try:
            title_element = self.driver.find_element(By.CSS_SELECTOR, '[data-e2e="doc_page_title"]')
            document_title = title_element.text
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
                self.config_manager.log_message("No download button found")
                return False
                
            button = elements[0]
            self.driver.execute_script('arguments[0].style.color = "red";', button)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            
            try:
                button.click()
                self.config_manager.log_message("Download button clicked")
                return True
            except:
                self.driver.execute_script("arguments[0].click();", button)
                self.config_manager.log_message("Download button clicked via JavaScript")
                return True
                
        except Exception as e:
            self.config_manager.log_message(f"Error with download button: {str(e)}")
            return False

    def handle_download_modal(self, document_title, category, subcategory):
        """Handle download modal and initiate download"""
        try:
            # Get current download directory
            current_dir = self.config_manager.get_current_download_dir()
            self.config_manager.log_message(f"Setting download directory to: {current_dir}")
            
            # Wait for modal download button
            modal_download_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-e2e="modal-download-button"]'))
            )

            if not modal_download_button:
                self.config_manager.log_message("Download button not found")
                return None, None

            # Get download URL and clean it
            download_url = modal_download_button.get_attribute('href')
            if download_url.endswith('#'):
                download_url = download_url[:-1]
                
            original_filename = os.path.basename(download_url.split('?')[0])
            if original_filename.endswith('#'):
                original_filename = original_filename[:-1]
                
            # Ensure .pdf extension
            if not original_filename.lower().endswith('.pdf'):
                original_filename += '.pdf'
                
            self.config_manager.log_message(f"Download URL: {download_url}")
            self.config_manager.log_message(f"Original filename: {original_filename}")
            
            # Generate clean filename
            document_title = document_title.strip() if document_title else original_filename
            cleaned_title = f"{document_title}.pdf"
            
            # Create a temporary download link with correct attributes
            self.driver.execute_script("""
                var link = arguments[0];
                var fileName = arguments[1];
                
                // Set download attributes
                link.setAttribute('download', fileName);
                link.setAttribute('target', '_blank');
                
                // Force download behavior
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', this.href, true);
                    xhr.responseType = 'blob';
                    xhr.onload = function() {
                        var blob = xhr.response;
                        var a = document.createElement('a');
                        a.href = window.URL.createObjectURL(blob);
                        a.download = fileName;
                        a.style.display = 'none';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    };
                    xhr.send();
                });
            """, modal_download_button, cleaned_title)

            # Click download button
            modal_download_button.click()
            self.config_manager.log_message("Download initiated")
            
            return cleaned_title, download_url
                
        except Exception as e:
            self.config_manager.log_message(f"Error in download modal: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return None, None
    def verify_and_rename_file(self, cleaned_title, download_url, category, subcategory):
        """Verify download and rename file"""
        try:
            time.sleep(15)  # Wait for download
            
            # Get both directories
            current_dir = self.config_manager.get_current_download_dir()
            base_dir = self.config_manager.insurance_files_dir
            
            self.config_manager.log_message(f"Checking directories:")
            self.config_manager.log_message(f"Current dir: {current_dir}")
            self.config_manager.log_message(f"Base dir: {base_dir}")
            
            # Check both directories for the file
            directories_to_check = [current_dir, base_dir]
            found_file = None
            source_dir = None
            
            for directory in directories_to_check:
                self.config_manager.log_message(f"Checking directory: {directory}")
                
                if not os.path.exists(directory):
                    continue
                    
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                self.config_manager.log_message(f"Files in {directory}: {files}")
                
                # Look for both the original name and cleaned title
                for file in files:
                    if file.endswith('.pdf') and (
                        file.startswith(cleaned_title.replace('.pdf', '')) or
                        'Medical-Insurance' in file
                    ):
                        found_file = file
                        source_dir = directory
                        break
                        
                if found_file:
                    break
            
            if not found_file:
                self.config_manager.log_message("No matching file found in any directory")
                return False
                
            self.config_manager.log_message(f"Found file: {found_file} in {source_dir}")
            
            # Move file to correct directory if needed
            old_path = os.path.join(source_dir, found_file)
            new_path = os.path.join(current_dir, cleaned_title)
            
            if old_path != new_path:
                # Ensure target directory exists
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                
                # Move and rename file
                os.rename(old_path, new_path)
                self.config_manager.log_message(f"File moved and renamed to: {cleaned_title}")
                
                # Update tracking
                self.download_tracker.record_download(category, subcategory)
                
                # Update report
                try:
                    file_size = os.path.getsize(new_path)
                    self.report_manager.add_download_record(
                        filename=cleaned_title,
                        document_title=cleaned_title,
                        url=download_url,
                        file_size=file_size
                    )
                except Exception as e:
                    self.config_manager.log_message(f"Error updating report: {str(e)}")
                
                return True
            
            return True
                
        except Exception as e:
            self.config_manager.log_message(f"Error in file verification: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return False