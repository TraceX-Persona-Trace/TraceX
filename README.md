# TraceX

**Ethical OSINT Identity Intelligence Platform**

## Stack

- **Frontend:** React + TypeScript + Vite (`/frontend`)
- **Backend:** Python + FastAPI (`/backend`)
- **Database:** SQLite + SQLAlchemy *(future chunks)*

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Health check: `GET http://localhost:8000/api/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

All `/api` requests are proxied to `http://localhost:8000`.

## Project Structure

```
tracex/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── .env.example     # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── main.tsx     # React entry point
│   │   └── App.tsx      # Root component
│   ├── index.html
│   ├── vite.config.ts   # Vite config with /api proxy
│   ├── tsconfig.json
│   └── package.json
└── README.md
```
