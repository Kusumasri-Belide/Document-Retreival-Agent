import io
import os
import sys
import time
from typing import List, Dict, Optional

import requests
from msal import ConfidentialClientApplication, PublicClientApplication
from backend.config import DOCS_DIR
from dotenv import load_dotenv

load_dotenv()

# OneDrive/Microsoft Graph API configuration
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")  # Optional for public client
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")  # "common" for personal accounts
ONEDRIVE_FOLDER_PATH = os.getenv("ONEDRIVE_FOLDER_PATH", "/")  # Root folder by default

# Microsoft Graph API scopes
SCOPES = ["https://graph.microsoft.com/Files.Read.All"]

# Graph API endpoints
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

class OneDriveClient:
    def __init__(self):
        self.access_token = None
        self.app = None
        self._init_msal_app()
    
    def _init_msal_app(self):
        """Initialize MSAL application for authentication."""
        if CLIENT_SECRET:
            # Confidential client (web app)
            self.app = ConfidentialClientApplication(
                CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{TENANT_ID}",
                client_credential=CLIENT_SECRET,
            )
        else:
            # Public client (desktop app)
            self.app = PublicClientApplication(
                CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            )
    
    def authenticate(self):
        """Authenticate and get access token."""
        # Try to get token silently first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                return
        
        # Interactive authentication - always use interactive flow for delegated permissions
        print("🔐 Opening browser for Microsoft authentication...")
        result = self.app.acquire_token_interactive(scopes=SCOPES)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            print("✅ Successfully authenticated with Microsoft Graph")
        else:
            error_msg = result.get('error_description', result.get('error', 'Unknown error'))
            raise Exception(f"Authentication failed: {error_msg}")
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make authenticated request to Microsoft Graph API."""
        if not self.access_token:
            self.authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{GRAPH_API_BASE}{endpoint}", headers=headers, params=params)
        
        if response.status_code == 401:
            # Token expired, re-authenticate
            self.authenticate()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.get(f"{GRAPH_API_BASE}{endpoint}", headers=headers, params=params)
        
        response.raise_for_status()
        return response.json()
    
    def _download_file_content(self, download_url: str) -> bytes:
        """Download file content from OneDrive."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
        return response.content
    
    def list_folder_contents(self, folder_path: str = "/") -> List[Dict]:
        """List contents of a OneDrive folder."""
        if folder_path == "/":
            endpoint = "/me/drive/root/children"
        else:
            # Remove leading slash and encode path
            clean_path = folder_path.lstrip("/")
            endpoint = f"/me/drive/root:/{clean_path}:/children"
        
        items = []
        while endpoint:
            response = self._make_request(endpoint)
            items.extend(response.get("value", []))
            endpoint = response.get("@odata.nextLink", "").replace(GRAPH_API_BASE, "") if "@odata.nextLink" in response else None
        
        return items
    
    def download_file(self, item: Dict, dest_path: str):
        """Download a file from OneDrive."""
        download_url = item.get("@microsoft.graph.downloadUrl")
        if not download_url:
            print(f"⚠️  No download URL for {item['name']}")
            return
        
        content = self._download_file_content(download_url)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(content)
        
        print(f"⬇️  Downloaded: {dest_path}")

def _safe_name(name: str) -> str:
    """Create a safe filename by removing invalid characters."""
    return "".join(c for c in name if c not in '<>:"/\\|?*').strip() or "untitled"

def _ensure_dir(path: str):
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def fetch_onedrive_folder(folder_path: str = "/"):
    """Fetch all files from a OneDrive folder recursively."""
    client = OneDriveClient()
    client.authenticate()
    _ensure_dir(DOCS_DIR)
    
    def recurse_folder(current_path: str, local_prefix: str = ""):
        """Recursively download files from OneDrive folder."""
        try:
            items = client.list_folder_contents(current_path)
            
            for item in items:
                name = _safe_name(item["name"])
                
                if item.get("folder"):
                    # It's a folder, recurse into it
                    new_path = f"{current_path.rstrip('/')}/{item['name']}" if current_path != "/" else f"/{item['name']}"
                    new_prefix = os.path.join(local_prefix, name) if local_prefix else name
                    recurse_folder(new_path, new_prefix)
                else:
                    # It's a file, download it
                    dest_dir = os.path.join(DOCS_DIR, local_prefix) if local_prefix else DOCS_DIR
                    _ensure_dir(dest_dir)
                    dest_path = os.path.join(dest_dir, name)
                    
                    # Skip if file already exists and hasn't been modified
                    if os.path.exists(dest_path):
                        local_mtime = os.path.getmtime(dest_path)
                        # Parse OneDrive modified time
                        remote_mtime_str = item.get("lastModifiedDateTime", "")
                        if remote_mtime_str:
                            from datetime import datetime
                            remote_mtime = datetime.fromisoformat(remote_mtime_str.replace("Z", "+00:00")).timestamp()
                            if local_mtime >= remote_mtime:
                                print(f"⏭️  Skipping (up to date): {os.path.join(local_prefix, name) if local_prefix else name}")
                                continue
                    
                    client.download_file(item, dest_path)
                    
        except Exception as e:
            print(f"⚠️  Error processing folder {current_path}: {e}")
    
    recurse_folder(folder_path)
    print("✅ OneDrive ingestion complete.")

if __name__ == "__main__":
    if not CLIENT_ID:
        print("❌ Set MICROSOFT_CLIENT_ID in .env file")
        sys.exit(1)
    
    folder_path = ONEDRIVE_FOLDER_PATH or "/"
    print(f"📁 Fetching from OneDrive folder: {folder_path}")
    fetch_onedrive_folder(folder_path)