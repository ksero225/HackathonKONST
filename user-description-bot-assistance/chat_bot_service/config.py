# config.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY (sprawdź plik .env)")

client = OpenAI(api_key=OPENAI_API_KEY)

JAVA_BASE_URL = os.getenv("JAVA_BASE_URL")
if not JAVA_BASE_URL:
    raise RuntimeError("Brak zmiennej środowiskowej JAVA_BASE_URL (dodaj do .env)")

WS_URI = os.getenv("WS_URI", "wss://continuable-manuela-podgy.ngrok-free.dev/ws")
