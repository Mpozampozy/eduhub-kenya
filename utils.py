import os
from datetime import datetime

def list_files(folder):
    folder_path = os.path.join("uploads", folder)
    if not os.path.exists(folder_path):
        return []
    return sorted(os.listdir(folder_path))

def days_remaining(expiry_date):
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        remaining = (expiry - datetime.today()).days
        return max(remaining, 0)
    except:
        return "N/A"

def is_membership_active(expiry_date):
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        return expiry >= datetime.today()
    except:
        return False
