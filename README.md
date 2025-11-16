# Sketch-Brawl

Sketch Brawl is an AI-powered doodle battler where anything you draw becomes alive — and fights.
Players sketch monsters and gear like a kid, and the AI instantly interprets each stroke into stats, abilities, personalities, and chaotic battle actions.
Every match is unpredictable, creative, and powered entirely by your imagination.

## Usage Guide

### 1. Backend + Core Services (Docker)

1. Move into the project directory:
   ```bash
   cd /Users/chenyuxin/Sketch-Brawl
   ```
2. Start PostgreSQL, Redis, MinIO, and the FastAPI backend (Docker is required):
   ```bash
   docker compose -f ops/docker-compose.yml up --build postgres redis minio backend
   ```
3. Once the stack is healthy the backend will be available at `http://localhost:8000`.

#### Required Environment

Set the Gemini key ahead of time in your shell session or in `backend/.env`:

```bash
export GEMINI_API_KEY=your_key_here
```

### 2. Frontend (Local Development Mode)

1. Change into the frontend workspace:
   ```bash
   cd frontend
   ```
2. Tell the frontend where to find the backend:
   ```bash
   export NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```
3. Install dependencies and run the dev server:
   ```bash
   yarn install
   yarn dev --hostname 127.0.0.1 --port 3000
   ```

The React dev server will default to `http://127.0.0.1:3000`, proxying API calls to the FastAPI backend you launched earlier.
