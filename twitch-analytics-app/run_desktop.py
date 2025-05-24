import threading
import webview
import os
import sys

# Ensure src is in the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

def run_flask():
    os.environ["FLASK_ENV"] = "production"
    from app import app  # Now imports from src/app.py due to sys.path change
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    webview.create_window("Twitch Analytics App", "http://127.0.0.1:5000", width=1200, height=800)
    webview.start()
