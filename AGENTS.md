# Sketch-Brawl Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-15

## Active Technologies

- Python 3.11 (backend services, telemetry workers); TypeScript 5 + React 18 (web canvas + UI); Unity WebGL (optional guided replay viewer embedded as iframe) + FastAPI, PostgreSQL 15, Redis 7, PlayCanvas-like WebGL canvas or Fabric.js for drawing, TorchServe/ONNX runtime for image-to-attribute inference, Railway deployment stack (001-ai-game-demo)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11 (backend services, telemetry workers); TypeScript 5 + React 18 (web canvas + UI); Unity WebGL (optional guided replay viewer embedded as iframe): Follow standard conventions

## Recent Changes

- 001-ai-game-demo: Added Python 3.11 (backend services, telemetry workers); TypeScript 5 + React 18 (web canvas + UI); Unity WebGL (optional guided replay viewer embedded as iframe) + FastAPI, PostgreSQL 15, Redis 7, PlayCanvas-like WebGL canvas or Fabric.js for drawing, TorchServe/ONNX runtime for image-to-attribute inference, Railway deployment stack

<!-- MANUAL ADDITIONS START -->
for the demo, if database is not required then we can leave it out.
<!-- MANUAL ADDITIONS END -->
