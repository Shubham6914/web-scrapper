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
        """
        Extract and validate file information
        """
        # Get extension from URL first
        url_ext = os.path.splitext(download_url.split('?')[0])[1].lower()
        # Get extension from original filename as backup
        original_ext = os.path.splitext(original_filename)[1].lower()
        
        # Use URL extension if valid, otherwise use original extension
        file_extension = url_ext if url_ext in self.valid_extensions else original_ext
        
        self._log_message(f"URL Extension: {url_ext}")
        self._log_message(f"Original Extension: {original_ext}")
        self._log_message(f"Selected Extension: {file_extension}")
        
        return file_extension

    def generate_unique_name(self, title, original_filename, download_url, category=None, subcategory=None):
        """
        Generates a unique, clean filename while preserving the correct extension
        Added optional category/subcategory for better organization
        """
        # Get the correct file extension
        file_extension = self.get_file_info(download_url, original_filename)
        
        # Clean the title
        cleaned_name = self._clean_name(title)
        
        # Add category/subcategory prefix if provided
        if category and subcategory:
            cleaned_name = f"{category}_{subcategory}_{cleaned_name}"
        
        # Ensure uniqueness
        base_name = cleaned_name
        counter = 1
        while f"{cleaned_name}{file_extension}" in self.used_names:
            cleaned_name = f"{base_name} ({counter})"
            counter += 1
        
        final_name = f"{cleaned_name}{file_extension}"
        self.used_names.add(final_name)
        
        self._log_message(f"Final filename: {final_name}")
        return final_name

    def _clean_name(self, name):
        """
        Clean the filename while preserving meaningful content
        """
        # Remove Scribd ID pattern (e.g., "313200875-")
        name = re.sub(r'^\d+-', '', name)
        
        # Replace hyphens and underscores with spaces
        name = name.replace('-', ' ').replace('_', ' ')
        
        # Remove any standalone numbers
        words = name.split()
        cleaned_words = [word for word in words if not word.isdigit()]
        
        # Join words and clean up spaces
        cleaned_name = ' '.join(cleaned_words)
        cleaned_name = ' '.join(cleaned_name.split())
        
        # Capitalize words
        cleaned_name = cleaned_name.title()
        
        return cleaned_name.strip()