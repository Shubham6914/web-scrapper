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

    def clean_filename(self, filename):
        """Clean and format filename"""
        try:
            # Remove numeric prefix pattern (e.g., "30607540202200-")
            filename = re.sub(r'^\d+-', '', filename)
            
            # Split on hyphens and clean each part
            parts = filename.split('-')
            cleaned_parts = []
            
            for part in parts:
                # Remove special characters and extra spaces
                cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', part)
                # Convert to title case and strip
                cleaned = ' '.join(word.capitalize() for word in cleaned.split())
                cleaned = cleaned.strip()
                if cleaned:  # Only add non-empty parts
                    cleaned_parts.append(cleaned)
            
            # Join parts with spaces
            clean_name = ' '.join(cleaned_parts)
            
            # Remove redundant spaces
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            # Replace spaces with hyphens for final filename
            final_name = clean_name.replace(' ', '-')
            
            return final_name
            
        except Exception as e:
            self._log_message(f"Error in clean_filename: {str(e)}")
            return filename

    def generate_unique_name(self, title, original_filename, download_url):
        """Generates a unique, clean filename"""
        try:
            # Get the file extension
            file_extension = self.get_file_info(download_url, original_filename)
            
            # Clean the original filename
            base_name = self.clean_filename(original_filename)
            
            # If title is available and different from filename, use it
            if title and title.strip() != base_name:
                cleaned_title = self.clean_filename(title)
                if cleaned_title:
                    base_name = cleaned_title
            
            # Remove any file extension from base_name
            base_name = os.path.splitext(base_name)[0]
            
            # Generate final filename
            final_name = f"{base_name}{file_extension}"
            
            # Ensure uniqueness
            if final_name in self.used_names:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_name = f"{base_name}-{timestamp}{file_extension}"
            
            self.used_names.add(final_name)
            self._log_message(f"Generated filename: {final_name}")
            
            return final_name
            
        except Exception as e:
            self._log_message(f"Error in generate_unique_name: {str(e)}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"document-{timestamp}{file_extension}"

    def get_file_info(self, download_url, original_filename):
        """Extract and validate file extension"""
        try:
            # Get extension from original filename first
            original_ext = os.path.splitext(original_filename)[1].lower()
            
            # If original extension is valid, use it
            if original_ext in self.valid_extensions:
                return original_ext
            
            # Try getting extension from URL
            url_ext = os.path.splitext(download_url.split('?')[0])[1].lower()
            if url_ext in self.valid_extensions:
                return url_ext
            
            # Default to PDF if no valid extension found
            return '.pdf'
            
        except Exception as e:
            self._log_message(f"Error in get_file_info: {str(e)}")
            return '.pdf'