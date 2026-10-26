# Frontend and Backend Learning Project

This project demonstrates how a local web page communicates with a backend API deployed on a cloud server.

## Goal

1. A user enters a number `x` in a local web page
2. The frontend sends `x` to the backend API
3. The backend returns `x` squared
4. The frontend displays the result

## Project structure

```text
20260908_frontend_backend/
├── frontend/              # Local browser application
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── README.md
├── backend/               # FastAPI service for cloud deployment
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
└── README.md
```

## API contract

**Endpoint:** `POST /square`

Request body:

```json
{"x": 5}
```

Response body:

```json
{"x": 5, "square": 25}
```

## Learning order

1. Implement and run the FastAPI backend locally
2. Build the local HTML, CSS, and JavaScript frontend
3. Connect the frontend to the local backend
4. Deploy the backend to the cloud server
5. Update the frontend to call the deployed API

## Run locally

Install the backend dependencies and start the API:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

In another PowerShell window, start the local frontend server:

```powershell
cd frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500`. The page calls `http://127.0.0.1:8000/square` by default.

## Cloud deployment

The backend code is ready for cloud deployment, but this project does not deploy automatically. Once the API is deployed, change `API_URL` in `frontend/app.js` to the public HTTPS endpoint.

## Current status

The frontend and local backend are implemented. Cloud deployment has not been performed.
