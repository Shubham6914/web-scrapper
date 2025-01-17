import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import os
import math

class DownloadReportManager:
    def __init__(self, excel_file='download_reports.xlsx'):
        self.excel_file = excel_file
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.categories = {
            'Case Law': ['case', 'versus', 'vs', 'judgment', 'decision', 'ruling', 'opinion', 'order', 'court'],
            'Legislative': ['act', 'regulation', 'statute', 'law', 'legislation', 'bill', 'code', 'ordinance', 'rule', 'legal'],
            'Academic': ['research', 'study', 'analysis', 'theory', 'journal', 'review', 'publication', 'paper', 'thesis', 'dissertation'],
            'Educational': ['guide', 'manual', 'handbook', 'course', 'syllabus', 'lecture', 'notes', 'tutorial', 'exam', 'quiz'],
            'Legal Practice': ['practice', 'procedure', 'pleading', 'motion', 'brief', 'petition', 'filing', 'firm'],
            'Legal Commentary': ['commentary', 'annotation', 'explanation', 'interpretation', 'discussion', 'analysis'],
            'Legal Documentation': ['document', 'agreement', 'contract', 'deed', 'memorandum', 'affidavit', 'form'],
            'Legal Research': ['research', 'analysis', 'methodology', 'findings', 'report', 'survey', 'study'],
            'Forms': ['form', 'template', 'format', 'sample', 'specimen', 'model', 'draft', 'example']
        }
        
        self.subject_areas = {
            'Constitutional Law': ['constitution', 'constitutional', 'fundamental rights', 'federal', 'amendment', 'basic law'],
            'Criminal Law': ['criminal', 'crime', 'offense', 'prosecution', 'penal', 'defense', 'bail', 'punishment'],
            'Civil Law': ['civil', 'tort', 'contract', 'damages', 'liability', 'negligence', 'remedy', 'compensation'],
            'Corporate Law': ['corporate', 'company', 'business', 'merger', 'acquisition', 'shareholder', 'director'],
            'Patent Law': ['patent', 'intellectual property', 'trademark', 'copyright', 'ip', 'innovation', 'invention'],
            'Family Law': ['family', 'divorce', 'marriage', 'custody', 'adoption', 'alimony', 'domestic'],
            'Administrative Law': ['administrative', 'agency', 'regulation', 'compliance', 'enforcement', 'governance'],
            'Environmental Law': ['environmental', 'environment', 'pollution', 'conservation', 'ecology', 'climate'],
            'International Law': ['international', 'treaty', 'convention', 'global', 'foreign', 'diplomatic', 'cross-border'],
            'Labor Law': ['labor', 'employment', 'worker', 'union', 'workplace', 'compensation', 'hr'],
            'Tax Law': ['tax', 'taxation', 'revenue', 'fiscal', 'income', 'audit', 'financial'],
            'Securities Law': ['securities', 'investment', 'stock', 'trading', 'finance', 'market', 'shares'],
            'Property Law': ['property', 'real estate', 'land', 'lease', 'tenant', 'ownership', 'title'],
            'Banking Law': ['banking', 'bank', 'financial', 'credit', 'loan', 'mortgage', 'debt'],
            'Other': []
        }
        self.initialize_excel()

    def convert_size(self, size_bytes):
        """Convert bytes to human readable format"""
        if size_bytes == 0 or size_bytes is None:
            return "0 B"
        
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
    def calculate_total_size_per_day(self, date):
        """Calculate total size for a specific date"""
        daily_data = self.df[self.df['Date'] == date]
        total_bytes = daily_data['File Size'].sum()
        return total_bytes, self.convert_size(total_bytes)

    def add_download_record(self, filename, document_title, url, file_size):
        """Add a new download record with proper file size handling"""
        category, subject = self.categorize_document(filename, document_title)
        file_type = os.path.splitext(filename)[1]
        
        # Calculate daily totals
        daily_files = len(self.df[self.df['Date'] == self.today]) + 1
        total_bytes, readable_total = self.calculate_total_size_per_day(self.today)
        
        new_record = pd.DataFrame([{
            'Date': self.today,
            'Filename': filename,
            'Category': category,
            'Subject Area': subject,
            'File Type': file_type,
            'File Size': file_size,  # Raw bytes
            'File Size (Readable)': self.convert_size(file_size),  # Human readable format
            'URL': url,
            'Total Files Per Day': daily_files,
            'Total Size Per Day': readable_total
        }])

        self.df = pd.concat([self.df, new_record], ignore_index=True)
        self.df.to_excel(self.excel_file, index=False)
        
    def update_daily_totals(self):
        """Update daily totals for all dates"""
        dates = self.df['Date'].unique()
        
        for date in dates:
            date_mask = self.df['Date'] == date
            daily_files = len(self.df[date_mask])
            total_bytes, readable_total = self.calculate_total_size_per_day(date)
            
            self.df.loc[date_mask, 'Total Files Per Day'] = daily_files
            self.df.loc[date_mask, 'Total Size Per Day'] = readable_total
        
        self.df.to_excel(self.excel_file, index=False)

    def initialize_excel(self):
        """Create or load the Excel file with necessary sheets"""
        try:
            self.df = pd.read_excel(self.excel_file)
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=[
                'Date',
                'Filename',
                'Category',
                'Subject Area',
                'File Type',
                'File Size',
                'File Size (Readable)',
                'URL',
                'Total Files Per Day',
                'Total Size Per Day'
            ])
            self.df.to_excel(self.excel_file, index=False)
    
    def generate_daily_summary(self):
        """Generate and update daily summary information"""
        # Group by date and calculate summaries
        daily_summary = self.df.groupby('Date').agg({
            'Filename': 'count',  # Count files per day
            'File Size': 'sum'    # Sum of file sizes
        }).reset_index()

        # Rename columns for clarity
        daily_summary.columns = ['Date', 'Total Files', 'Total Size (Bytes)']

        # Add readable size column
        daily_summary['Total Size (Readable)'] = daily_summary['Total Size (Bytes)'].apply(self.convert_size)

        # Sort by date in descending order (most recent first)
        daily_summary = daily_summary.sort_values('Date', ascending=False)

        # Create or update the Daily Summary sheet
        try:
            with pd.ExcelWriter(self.excel_file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                daily_summary.to_excel(writer, sheet_name='Daily Summary', index=False)
        except ValueError:
            # If 'Daily Summary' sheet doesn't exist, create new one
            with pd.ExcelWriter(self.excel_file, mode='a', engine='openpyxl') as writer:
                daily_summary.to_excel(writer, sheet_name='Daily Summary', index=False)

        return daily_summary

    def update_excel_structure(self):
        """Update Excel structure by removing Download Time column and ensuring correct order"""
        if 'Download Time' in self.df.columns:
            self.df = self.df.drop('Download Time', axis=1)

        # Ensure columns are in correct order
        desired_columns = [
            'Date',
            'Filename',
            'Category',
            'Subject Area',
            'File Type',
            'File Size',
            'File Size (Readable)',
            'URL',
            'Total Files Per Day',
            'Total Size Per Day'
        ]

        # Reorder columns (only existing ones)
        existing_columns = [col for col in desired_columns if col in self.df.columns]
        self.df = self.df[existing_columns]
        
        # Save updated structure
        self.df.to_excel(self.excel_file, index=False)

    def refresh_all_data(self):
        """Refresh all data and summaries"""
        # Update daily totals
        self.update_daily_totals()
        
        # Generate fresh summary
        self.generate_daily_summary()
        
        # Update Excel structure
        self.update_excel_structure()

    def get_current_stats(self):
        """Get current day's statistics"""
        today_data = self.df[self.df['Date'] == self.today]
        total_files = len(today_data)
        total_size = today_data['File Size'].sum()
        
        return {
            'Date': self.today,
            'Total Files Downloaded': total_files,
            'Total Size': self.convert_size(total_size),
            'File Types': today_data['File Type'].value_counts().to_dict()
        }

    def categorize_document(self, filename, document_title):
        """Enhanced categorization with better matching"""
        title_lower = document_title.lower()
        
        # More specific category matching
        category_scores = {}
        for cat, keywords in self.categories.items():
            score = sum(3 if keyword in title_lower.split() else 
                       2 if keyword in title_lower else 0 
                       for keyword in keywords)
            if score > 0:
                category_scores[cat] = score
        
        category = max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else 'Other'
        
        # Enhanced subject area matching
        matching_subjects = []
        for area, keywords in self.subject_areas.items():
            if any(keyword in title_lower.split() or 
                  any(kw in title_lower for kw in keyword.split())
                  for keyword in keywords):
                matching_subjects.append(area)
        
        subject_area = ' & '.join(matching_subjects) if matching_subjects else 'Other'
        
        return category, subject_area
