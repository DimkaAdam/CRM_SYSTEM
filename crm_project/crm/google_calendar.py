import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Область доступа
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Файл токенов (авторизация)
TOKEN_FILE = "token.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Определяем текущую папку скрипта
CREDENTIALS_FILE = os.path.join(BASE_DIR, "c_id.json")


def get_calendar_events():
    """Получает события из Google Календаря."""

    creds = None
    # Проверяем, есть ли токен
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Если нет, запускаем авторизацию
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=8081)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Подключаем API
    service = build("calendar", "v3", credentials=creds)

    # Получаем ближайшие события
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    return events

