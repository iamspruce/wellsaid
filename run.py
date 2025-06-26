# run.py (no change needed for path handling if app.main:app is used)
import uvicorn
import os
import sys
# from pathlib import Path # No longer strictly necessary to add project_root to sys.path explicitly here
# sys.path.insert(0, str(project_root)) # Can likely remove this line if your only problem was 'models' import

host = "0.0.0.0"
port = 7860
app_module = "app.main:app" # This refers to the 'app' package correctly

if __name__ == "__main__":
    print(f"Starting Uvicorn server for {app_module} at http://{host}:{port}")
    # ... rest of your print statements and uvicorn.run call
    uvicorn.run(app_module, host=host, port=port, reload=True)