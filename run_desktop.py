import threading
import webview
import os
import sys

# Try both possible src locations for import
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir1 = os.path.join(base_dir, "twitch-analytics-app", "src")
src_dir2 = os.path.join(base_dir, "src")

if os.path.exists(os.path.join(src_dir1, "app.py")):
    src_dir = src_dir1
    app_module = "app"
elif os.path.exists(os.path.join(src_dir2, "app.py")):
    src_dir = src_dir2
    app_module = "app"
else:
    # Try importing as a package (src/app.py as src.app)
    if os.path.exists(os.path.join(base_dir, "twitch-analytics-app", "src", "__init__.py")):
        src_dir = os.path.join(base_dir, "twitch-analytics-app")
        app_module = "src.app"
        sys.path.insert(0, src_dir)
    elif os.path.exists(os.path.join(base_dir, "src", "__init__.py")):
        src_dir = base_dir
        app_module = "src.app"
        sys.path.insert(0, src_dir)
    else:
        raise RuntimeError("Cannot find src/app.py. Please check your folder structure.")

sys.path.insert(0, src_dir)

def run_flask():
    os.environ["FLASK_ENV"] = "production"
    os.chdir(src_dir)
    # Dynamically import the app module
    import importlib
    app_mod = importlib.import_module(app_module)
    app_mod.app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    webview.create_window("Twitch Analytics App", "http://127.0.0.1:5000", width=1200, height=800)
    webview.start()
