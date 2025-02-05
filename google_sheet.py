# Required libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os.path

class GoogleSheetsSync:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Handle Google Sheets authentication"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('sheets', 'v4', credentials=self.creds)

    def update_sheet(self, data_frame):
        """Update Google Sheet with current data"""
        try:
            sheet = self.service.spreadsheets()
            
            # Convert DataFrame to values list
            values = [data_frame.columns.values.tolist()] + data_frame.values.tolist()
            
            body = {
                'values': values
            }
            
            # Clear existing content
            sheet.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range='A1:Z1000'  # Adjust range as needed
            ).execute()
            
            # Update with new content
            result = sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return result
        except Exception as e:
            print(f"Error updating Google Sheet: {str(e)}")
            return None