"""
Google Sheets Logging - Log control actions to Google Sheets
"""

import os
import json
from datetime import datetime
from typing import Optional

try:
    import google.auth
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False


class GoogleSheetsLogger:
    """Handle logging to Google Sheets"""

    def __init__(self):
        self.service = None
        self.initialized = False

        if not GOOGLE_SHEETS_AVAILABLE:
            print("[Google Sheets] Google API libraries not available")
            return

        try:
            self._initialize()
        except Exception as e:
            print(f"[Google Sheets] Initialization error: {e}")

    def _initialize(self):
        """Initialize Google Sheets API connection"""
        try:
            # Try to get credentials from environment variable first
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')

            if credentials_json:
                # Load from JSON string in environment variable
                try:
                    credentials_dict = json.loads(credentials_json)
                    credentials = ServiceAccountCredentials.from_service_account_info(
                        credentials_dict,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    print("[Google Sheets] Loaded credentials from environment variable")
                except json.JSONDecodeError as e:
                    print(f"[Google Sheets] Error parsing GOOGLE_CREDENTIALS_JSON: {e}")
                    return
            elif credentials_path and os.path.exists(credentials_path):
                # Load from file as fallback
                credentials = ServiceAccountCredentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                print(f"[Google Sheets] Loaded credentials from file: {credentials_path}")
            else:
                print("[Google Sheets] No credentials found in environment variable or file")
                return

            # Build service
            self.service = build('sheets', 'v4', credentials=credentials)
            self.initialized = True
            print("[Google Sheets] Initialized successfully")

        except Exception as e:
            print(f"[Google Sheets] Error initializing: {e}")

    def log_action(self, ip_address: str, action_type: str, parameter: str) -> bool:
        """
        Log a control action to Google Sheets

        Args:
            ip_address: IP address of the client
            action_type: Type of action (button press, command, etc.)
            parameter: Parameter associated with the action

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.initialized:
            print("[Google Sheets] Not initialized, skipping log")
            return False

        try:
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
            cells = os.getenv('GOOGLE_SPREADSHEET_CELLS', "'control log'!A:D")

            if not spreadsheet_id:
                print("[Google Sheets] No spreadsheet ID configured")
                return False

            # Prepare row data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_values = [
                timestamp,
                ip_address,
                action_type,
                str(parameter)
            ]

            # Append row
            body = {
                'values': [row_values]
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=cells,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            print(f"[Google Sheets] Logged action: {action_type} = {parameter} from {ip_address}")
            return True

        except HttpError as e:
            print(f"[Google Sheets] API error: {e}")
            return False
        except Exception as e:
            print(f"[Google Sheets] Error logging action: {e}")
            return False


# Singleton instance
_logger = None


def get_logger() -> GoogleSheetsLogger:
    """Get or create logger instance"""
    global _logger
    if _logger is None:
        _logger = GoogleSheetsLogger()
    return _logger


def log_action(ip_address: str, action_type: str, parameter: str) -> bool:
    """
    Log a control action to Google Sheets (immediate logging)

    Args:
        ip_address: IP address of the client
        action_type: Type of action
        parameter: Parameter associated with the action

    Returns:
        True if logged successfully, False otherwise
    """
    logger = get_logger()
    return logger.log_action(ip_address, action_type, parameter)
