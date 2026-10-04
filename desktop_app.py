import os
import sys
import threading
import time
import uvicorn
import webview
from pathlib import Path
import socket

# Ensure project root is in Python module search path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api import app
from api.config import settings

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('crewairag.com', port)) == 0

def run_server():
    # Only run if not already running (useful for hot reloads or double launches)
    if not is_port_in_use(settings.port):
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="warning")

if __name__ == '__main__':
    print("Starting CrewAI Desktop App...")
    
    # Start the FastAPI server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for the server to spin up
    retries = 0
    while not is_port_in_use(settings.port) and retries < 15:
        time.sleep(1)
        retries += 1

    url = f"http://{settings.host}:{settings.port}"
    
    # Create the native desktop window using pywebview
    window = webview.create_window(
        f"{settings.app_name} - Desktop", 
        url, 
        width=1280, 
        height=800,
        min_size=(800, 600)
    )
    
    # Start the pywebview native application loop
    webview.start(private_mode=False)
