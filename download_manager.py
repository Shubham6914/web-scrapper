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
import datetime


class DownloadManager:
    def __init__(self, driver, config_manager, name_handler, progress_tracker, url_manager, report_manager):
        self.driver = driver
        self.config_manager = config_manager
        self.name_handler = name_handler
        self.progress_tracker = progress_tracker
        self.url_manager = url_manager
        self.report_manager = report_manager
        self.wait = WebDriverWait(self.driver, 10)

    
    def download_document(self, url, category, subcategory):
        """Main method to handle document download process"""
        try:
            self.config_manager.log_message(f"\n=== Starting Download Process ===")
            self.config_manager.log_message(f"URL: {url}")
            self.config_manager.log_message(f"Category: {category}")
            self.config_manager.log_message(f"Subcategory: {subcategory}")
            
            # Check if already downloaded
            if self.url_manager.is_processed(url):
                self.config_manager.log_message("URL already processed, skipping")
                return False
            
            # Get current download directory
            current_dir = self.config_manager.get_current_download_dir()
            self.config_manager.log_message(f"Download directory: {current_dir}")
            
            # Set Chrome preferences for download directory using multiple methods
            try:
                # Method 1: Using Chrome options
                if hasattr(self.driver, 'options'):
                    prefs = {
                        "download.default_directory": current_dir,
                        "download.prompt_for_download": False,
                        "download.directory_upgrade": True,
                        "safebrowsing.enabled": True,
                        "plugins.always_open_pdf_externally": True
                    }
                    self.driver.options.add_experimental_option("prefs", prefs)
                
                # Method 2: Using JavaScript
                js_script = f"""
                    const prefs = {{
                        "download.default_directory": "{current_dir}",
                        "download.prompt_for_download": false,
                        "download.directory_upgrade": true,
                        "safebrowsing.enabled": true,
                        "plugins.always_open_pdf_externally": true
                    }};
                    Object.keys(prefs).forEach(key => {{
                        if (chrome.preferences) {{
                            chrome.preferences.setPref(key, prefs[key]);
                        }}
                    }});
                """
                self.driver.execute_script(js_script)
                
                # Method 3: Using CDP command if available
                if hasattr(self.driver, 'execute_cdp_cmd'):
                    self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                        'behavior': 'allow',
                        'downloadPath': current_dir
                    })
                
                self.config_manager.log_message("Download preferences updated")
            except Exception as e:
                self.config_manager.log_message(f"Warning: Could not set download preferences: {str(e)}")
            
            # Navigate to document page
            self.driver.get(url)
            self.driver.execute_script('document.body.style.zoom = "200%";')
            
            # Get document title
            document_title = self.get_document_title()
            if not document_title:
                self.config_manager.log_message("Failed to get document title")
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
            
            # Additional wait for download preferences to take effect
            self.driver.implicitly_wait(2)
            
            # Verify download and rename file
            file_info = self.verify_and_rename_file(cleaned_title, download_url, category, subcategory)
            
            if file_info:
                # Add URL to processed list
                self.url_manager.add_url(category, subcategory, url)
                
                # Record in report manager with correct filename and size
                self.report_manager.add_download_record(
                    filename=file_info['filename'],
                    category=category,
                    subcategory=subcategory,
                    url=url,
                    file_size=file_info['file_size']
                )
                
                # Update progress tracker with verified count
                self.progress_tracker.record_download(
                    category=category,
                    subcategory=subcategory,
                    count=1  # Record single download
                )
                
                current_downloads = self.progress_tracker.get_subcategory_downloads(category, subcategory)
                self.config_manager.log_message(f"Current downloads for {subcategory}: {current_downloads}")
                
                # Check if we've reached 2 downloads
                if current_downloads >= 2:
                    self.config_manager.log_message(f"Subcategory {subcategory} has reached required downloads")
                    self.progress_tracker.mark_subcategory_complete(category, subcategory)
                    
                    # Check if category is complete
                    if self.progress_tracker.is_category_complete(category):
                        self.config_manager.log_message(f"Category {category} completed")
                        self.config_manager.mark_category_complete(category)
                
                self.config_manager.log_message("Download process completed successfully")
                return True
            
            self.config_manager.log_message("Download verification failed")
            return False
                
        except Exception as e:
            self.config_manager.log_message(f"Error in download process: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return False
        finally:
            # Log download attempt regardless of outcome
            self.config_manager.log_message("=== Download Process Ended ===\n")
            
            
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
                return None, None

            # Get download URL and original filename
            download_url = modal_download_button.get_attribute('href')
            original_filename = os.path.basename(download_url.split('?')[0])
            self.config_manager.log_message(f" 1st Original filename: {original_filename}")
            
            # Clean up URL and filename
            if download_url.endswith('#'):
                download_url = download_url[:-1]
            if original_filename.endswith('#'):
                original_filename = original_filename[:-1]
                
            # # Preserve original filename structure but ensure .pdf extension
            # if not original_filename.lower().endswith('.pdf'):
            #     original_filename += '.pdf'
            
            self.config_manager.log_message(f"Download URL: {download_url}")
            self.config_manager.log_message(f"Original filename: {original_filename}")
            
            # Use original filename structure
            cleaned_title = original_filename
            
            # Set download attributes
            self.driver.execute_script("""
                var link = arguments[0];
                var fileName = arguments[1];
                link.setAttribute('download', fileName);
                link.setAttribute('target', '_blank');
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
            # Define valid extensions
            valid_extensions = {'.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xlsx', '.xls'}
            
            # Initial wait for download
            time.sleep(5)
            
            # Get directories but prioritize correct directory
            current_dir = self.config_manager.get_current_download_dir()
            base_dir = self.config_manager.insurance_files_dir
            
            self.config_manager.log_message(f"\n=== Starting File Verification ===")
            self.config_manager.log_message(f"Looking for file: {cleaned_title}")
            self.config_manager.log_message(f"Target directory: {current_dir}")
            
            # Extract document ID
            doc_id = download_url.split('/')[-2]
            
            # Wait for file with timeout
            max_attempts = 3
            found_file = None
            source_dir = None
            
            for attempt in range(max_attempts):
                self.config_manager.log_message(f"\nAttempt {attempt + 1} of {max_attempts}")
                
                directories_to_check = [
                    (current_dir, "Target Directory"),
                    (base_dir, "Base Directory"),
                ]
                
                for directory, dir_type in directories_to_check:
                    if not os.path.exists(directory):
                        continue
                    
                    self.config_manager.log_message(f"Checking {dir_type}: {directory}")
                    
                    # Get all valid files in directory
                    files = [
                        f for f in os.listdir(directory) 
                        if os.path.isfile(os.path.join(directory, f)) 
                        and os.path.splitext(f)[1].lower() in valid_extensions
                    ]
                    
                    if files:
                        self.config_manager.log_message(f"Found files: {files}")
                        
                        for file in files:
                            # Document ID match is primary criteria
                            if doc_id in file:
                                found_file = file
                                source_dir = directory
                                self.config_manager.log_message(f"Found file: {file} (document ID match)")
                                break
                    
                    if found_file:
                        break
                        
                if found_file:
                    break
                    
                self.config_manager.log_message("No file found, waiting 5 seconds...")
                time.sleep(5)
            
            if not found_file:
                self.config_manager.log_message("No matching file found after all attempts")
                return None
            
            self.config_manager.log_message(f"\n=== Moving File ===")
            self.config_manager.log_message(f"Found file: {found_file}")
            self.config_manager.log_message(f"Source: {source_dir}")
            self.config_manager.log_message(f"Target: {current_dir}")
            
            # Get actual extension from found file
            actual_extension = os.path.splitext(found_file)[1].lower()
            
            # Create new filename with correct extension
            new_filename = os.path.splitext(cleaned_title)[0] + actual_extension
            
            # Setup paths
            old_path = os.path.join(source_dir, found_file)
            new_path = os.path.join(current_dir, new_filename)
            
            # Handle file already exists
            if os.path.exists(new_path):
                base, ext = os.path.splitext(new_filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{base}_{timestamp}{ext}"
                new_path = os.path.join(current_dir, new_filename)
            
            # Ensure target directory exists
            os.makedirs(current_dir, exist_ok=True)
            
            # Move file
            try:
                os.rename(old_path, new_path)
                self.config_manager.log_message(f"Successfully moved file to: {new_path}")
                
                # Get file size
                file_size = os.path.getsize(new_path)
                
                # Return file information instead of adding to report
                return {
                    'filename': new_filename,
                    'file_size': file_size,
                    'file_path': new_path
                }
                    
            except Exception as e:
                self.config_manager.log_message(f"Error moving file: {str(e)}")
                return None
                
        except Exception as e:
            self.config_manager.log_message(f"Error in file verification: {str(e)}")
            self.config_manager.log_message(traceback.format_exc())
            return None
        