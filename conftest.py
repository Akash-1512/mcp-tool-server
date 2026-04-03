# conftest.py
import sys
from pathlib import Path

# Put the project root on sys.path so 'mcp_server' is importable
sys.path.insert(0, str(Path(__file__).parent))