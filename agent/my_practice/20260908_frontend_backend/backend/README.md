# Backend

This folder contains a Python FastAPI service intended for deployment to the cloud server.

Run it locally:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

The service exposes `POST /square`, validates the submitted number, and returns its square as JSON.
