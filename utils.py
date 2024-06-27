# this imports the cryptography package
import json
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def encrypt():
    key = Fernet.generate_key()

    with open('Secret.json', 'rb') as f:
        data = f.read()

    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)

    with open('encryptedSecret.json', 'wb') as f:
        f.write(encrypted)
    return key.decode('utf-8')


def decrypt(key):
    with open('encryptedSecret.json', 'rb') as f:
        encrypted_data = f.read()

    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_data)

    return decrypted


def gdrive():
    scope = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    key = os.getenv('KEY')

    if not key:
        raise ValueError("KEY not found in environment variables")

    key = key.encode()
    secret = decrypt(key)
    secret = json.loads(secret)

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(secret, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    folder = GoogleDrive(gauth)

    client = gspread.authorize(credentials)

    return folder, client
