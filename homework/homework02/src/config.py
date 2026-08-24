import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
print(".env loaded (if present)")

def get_key(name, default=None):
    return os.getenv(name, default)

PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data"
print("PROJECT_ROOT:", PROJECT_ROOT)
print("DATA_DIR:", DATA_DIR)