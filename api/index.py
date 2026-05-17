import sys
from pathlib import Path

# Add the root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app_server import app
