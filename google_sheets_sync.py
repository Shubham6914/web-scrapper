from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os.path
import pandas as pd



# help to create pivot table dynamically in google sheet
class PivotSheetSync:  # Renamed class to avoid conflict
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.creds = None
        self.service = None
        self.authenticate()
        self.ensure_sheets_exist()

    def authenticate(self):
        """Handle Google Sheets authentication"""
        if os.path.exists('pivot_token.pickle'):  # Different token file
            with open('pivot_token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('pivot_token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('sheets', 'v4', credentials=self.creds)
        
    def create_initial_sheets(self):
        """Create all required sheets"""
        try:
            print("Creating initial sheets...")
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            required_sheets = ['Active Progress', 'Daily Progress', 'Summary View']
            
            requests = []
            for sheet_name in required_sheets:
                if sheet_name not in existing_sheets:
                    requests.append({
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': 26
                                }
                            }
                        }
                    })
            
            if requests:
                body = {'requests': requests}
                result = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                print(f"Created sheets: {[req['addSheet']['properties']['title'] for req in requests]}")
            else:
                print("All required sheets already exist")
                
        except Exception as e:
            print(f"Error creating sheets: {str(e)}")
            raise

    def ensure_sheets_exist(self):
        """Create required sheets if they don't exist"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            required_sheets = ['Active Progress', 'Daily Progress', 'Summary View']
            
            requests = []
            for sheet_name in required_sheets:
                if sheet_name not in existing_sheets:
                    requests.append({
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    })
            
            if requests:
                body = {'requests': requests}
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                print(f"Created sheets: {[req['addSheet']['properties']['title'] for req in requests]}")
        
        except Exception as e:
            print(f"Error ensuring sheets exist: {str(e)}")

    def update_sheet(self, data_frame, sheet_name):
        """Update specific sheet with data"""
        try:
            # Convert DataFrame to values list
            values = [data_frame.columns.values.tolist()] + data_frame.values.tolist()
            
            body = {
                'values': values
            }
            
            # Clear existing content
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:Z1000"
            ).execute()
            
            # Update with new content
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"Updated sheet: {sheet_name}")
            return result
        except Exception as e:
            print(f"Error updating sheet {sheet_name}: {str(e)}")
            return None

    def get_sheet_data(self, sheet_name):
        """Get data from specific sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:Z1000"
            ).execute()
            
            return result.get('values', [])
        except Exception as e:
            print(f"Error getting sheet data: {str(e)}")
            return None