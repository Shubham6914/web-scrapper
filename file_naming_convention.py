import os
import re
from datetime import datetime

class DocumentNameHandler:
    def __init__(self, log_file):
        self.used_names = set()
        self.valid_extensions = {'.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xlsx', '.xls'}
        self.log_file = log_file

    def _log_message(self, message):
        """Internal logging method"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a') as f:
            f.write(f'[{timestamp}] {message}\n')

    def get_file_info(self, download_url, original_filename):
        """Extract and validate file information"""
        try:
            # Get extension from URL first
            url_ext = os.path.splitext(download_url.split('?')[0])[1].lower()
            # Get extension from original filename as backup
            original_ext = os.path.splitext(original_filename)[1].lower()
            
            # Use URL extension if valid, otherwise use original extension
            file_extension = url_ext if url_ext in self.valid_extensions else original_ext
            
            # If no valid extension found, default to .pdf
            if not file_extension:
                file_extension = '.pdf'
            
            self._log_message(f"URL Extension: {url_ext}")
            self._log_message(f"Original Extension: {original_ext}")
            self._log_message(f"Selected Extension: {file_extension}")
            
            return file_extension
            
        except Exception as e:
            self._log_message(f"Error in get_file_info: {str(e)}")
            return '.pdf'

    def generate_unique_name(self, title, original_filename, download_url):
        """Generates a unique, clean filename while preserving the original structure"""
        try:
            # Get the file extension
            file_extension = self.get_file_info(download_url, original_filename)
            
            # Remove any URL parameters or hash from original filename
            if '#' in original_filename:
                original_filename = original_filename.split('#')[0]
            
            # Get the base name without extension
            base_name = os.path.splitext(original_filename)[0]
            
            # Remove any Scribd ID prefix if present
            base_name = re.sub(r'^\d+-', '', base_name)
            
            # Clean up the name but preserve hyphens
            cleaned_name = base_name.strip()
            
            # Ensure uniqueness
            final_name = f"{cleaned_name}{file_extension}"
            if final_name in self.used_names:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_name = f"{cleaned_name}_{timestamp}{file_extension}"
            
            self.used_names.add(final_name)
            self._log_message(f"Final filename: {final_name}")
            
            return final_name
            
        except Exception as e:
            self._log_message(f"Error generating filename: {str(e)}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"document_{timestamp}{file_extension}"

    def _clean_name(self, name):
        """Clean the filename while preserving hyphens"""
        try:
            # Remove any leading/trailing spaces
            name = name.strip()
            
            # Remove any invalid filename characters but keep hyphens
            name = re.sub(r'[<>:"/\\|?*]', '', name)
            
            return name
            
        except Exception as e:
            self._log_message(f"Error cleaning name: {str(e)}")
            return name