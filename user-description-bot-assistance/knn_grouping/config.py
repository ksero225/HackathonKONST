# knn_grouping/config.py
import os
from dotenv import load_dotenv

load_dotenv()

JAVA_BASE_URL = os.getenv("JAVA_BASE_URL")
if not JAVA_BASE_URL:
    raise RuntimeError("Brak zmiennej środowiskowej JAVA_BASE_URL (dodaj do .env)")

FEATURES_PATH = "/api/users/features"
OUTPUT_GROUPS_FILE = "users_knn_groups.json"

GEO_WEIGHT = 3.0

MIN_CLUSTER_RATIO = 0.14
MAX_CLUSTER_RATIO = 0.35

WS_URI = os.getenv("WS_URI", "wss://continuable-manuela-podgy.ngrok-free.dev/ws")
