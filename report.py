import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import os
import math
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from google_sheet import GoogleSheetsSync


class DownloadReportManager:
    def __init__(self, excel_file='download_reports.xlsx', spreadsheet_id=None):
        self.excel_file = excel_file
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.google_sync = None
        
        if spreadsheet_id:
            self.google_sync = GoogleSheetsSync(spreadsheet_id)
            
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

    def initialize_excel(self):
        """Create or load the Excel file with necessary sheets"""
        try:
            self.df = pd.read_excel(self.excel_file)
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=[
                'Date',
                'Filename',
                'Category',
                'Subcategory',
                'File Type',
                'File Size',
                'File Size (Readable)',
                'URL',
                'Total Files Per Day',
                'Total Size Per Day'
            ])
            self.df.to_excel(self.excel_file, index=False)

    def add_download_record(self, filename, category, subcategory, url, file_size):
        """Add a new download record and sync with Google Sheets"""
        try:
            file_type = os.path.splitext(filename)[1].lower()
            
            # Calculate daily totals
            daily_files = len(self.df[self.df['Date'] == self.today]) + 1
            total_bytes, readable_total = self.calculate_total_size_per_day(self.today)
            
            new_record = pd.DataFrame([{
                'Date': self.today,
                'Filename': filename,
                'Category': category,
                'Subcategory': subcategory,
                'File Type': file_type,
                'File Size': file_size,
                'File Size (Readable)': self.convert_size(file_size),
                'URL': url,
                'Total Files Per Day': daily_files,
                'Total Size Per Day': readable_total
            }])

            self.df = pd.concat([self.df, new_record], ignore_index=True)
            self.df.to_excel(self.excel_file, index=False)
            
            # Sync with Google Sheets if enabled
            if self.google_sync:
                self.google_sync.update_sheet(self.df)
                
        except Exception as e:
            print(f"Error adding download record: {str(e)}")

    def update_daily_totals(self):
        """Update daily totals and sync"""
        dates = self.df['Date'].unique()
        
        for date in dates:
            date_mask = self.df['Date'] == date
            daily_files = len(self.df[date_mask])
            total_bytes, readable_total = self.calculate_total_size_per_day(date)
            
            self.df.loc[date_mask, 'Total Files Per Day'] = daily_files
            self.df.loc[date_mask, 'Total Size Per Day'] = readable_total
        
        self.df.to_excel(self.excel_file, index=False)
        
        # Sync with Google Sheets if enabled
        if self.google_sync:
            self.google_sync.update_sheet(self.df)

    def generate_daily_summary(self):
        """Generate daily summary and sync"""
        daily_summary = self.df.groupby('Date').agg({
            'Filename': 'count',
            'File Size': 'sum'
        }).reset_index()

        daily_summary.columns = ['Date', 'Total Files', 'Total Size (Bytes)']
        daily_summary['Total Size (Readable)'] = daily_summary['Total Size (Bytes)'].apply(self.convert_size)
        daily_summary = daily_summary.sort_values('Date', ascending=False)

        # Update Excel
        with pd.ExcelWriter(self.excel_file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            daily_summary.to_excel(writer, sheet_name='Daily Summary', index=False)

        # Sync with Google Sheets if enabled
        if self.google_sync:
            self.google_sync.update_sheet(daily_summary)

        return daily_summary

    def refresh_all_data(self):
        """Refresh all data and sync"""
        self.update_daily_totals()
        self.generate_daily_summary()
        
        # Sync with Google Sheets if enabled
        if self.google_sync:
            self.google_sync.update_sheet(self.df)

    def get_current_stats(self):
        """Get current day's statistics"""
        today_data = self.df[self.df['Date'] == self.today]
        return {
            'Date': self.today,
            'Total Files Downloaded': len(today_data),
            'Total Size': self.convert_size(today_data['File Size'].sum()),
            'Categories': today_data['Category'].value_counts().to_dict(),
            'Subcategories': today_data['Subcategory'].value_counts().to_dict()
        }