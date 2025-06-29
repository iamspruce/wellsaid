import uvicorn
import os

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 7860))
app_module = "app.main:app"

if __name__ == "__main__":
    print(f"Starting Uvicorn server for {app_module} at http://{host}:{port}")
    uvicorn.run(app_module, host=host, port=port, reload=os.getenv("RELOAD", "true") == "true", log_level="info")
