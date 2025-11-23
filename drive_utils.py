import os
import sys
import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate_drive():
    """
    Authenticate with Google Drive using PyDrive2.
    - Uses saved credentials.json for automatic login.
    - Falls back to browser login if no credentials exist.
    - Loads client secrets securely from Streamlit secrets if provided.
    """
    gauth = GoogleAuth()

    # Load client secrets file securely from Streamlit secrets
    client_path = st.secrets.get("google_client_secrets_path")
    if client_path and os.path.exists(client_path):
        gauth.settings['client_config_file'] = client_path

    # Try to load saved credentials
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()   # First-time login → browser flow
    elif gauth.access_token_expired:
        gauth.Refresh()              # Refresh silently
    else:
        gauth.Authorize()            # Already valid

    # Save the current credentials to a file
    gauth.SaveCredentialsFile("credentials.json")

    return GoogleDrive(gauth)

def upload_to_drive(drive, local_path, filename):
    """
    Upload a file to Google Drive using PyDrive2.
    Returns the file ID of the uploaded file.
    """
    file = drive.CreateFile({'title': filename})
    file.SetContentFile(local_path)
    file.Upload()
    return file['id']
