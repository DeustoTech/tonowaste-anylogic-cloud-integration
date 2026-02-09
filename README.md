# TONOWASTE AnyLogic Cloud API Service (Lightweight)

This project is a high-performance, lightweight REST API wrapper for the **TONOWASTE** simulation model on AnyLogic Cloud. It uses **FastAPI** for the web layer and **Pydantic** for data validation.



## 🚀 Key Features

* **FastAPI Engine**: Extremely low overhead and high speed compared to heavier frameworks.
* **Strict Validation**: Data integrity is guaranteed via Pydantic models for TONOWASTE parameters.
* **Dynamic Parsing**: Automatically converts AnyLogic Dataset outputs into clean, structured JSON.
* **Auto-Documentation**: Interactive Swagger UI available at `/docs`.
* **Deployment Ready**: Fully optimized for Docker and Portainer environments.

---

## 📂 Project Structure

| Directory/File | Description |
| :--- | :--- |
| `scripts/service_anylogic.py` | **API Entry point.** FastAPI routes and data schemas. |
| `core/anylogic_wrapper.py` | **Simulation Logic.** Core wrapper for AnyLogic Cloud API. |
| `configs/` | JSON templates with default simulation parameters. |
| `Dockerfile` | Standard Docker instructions for Python-slim images. |
| `requirements.txt` | Python dependencies (FastAPI, Uvicorn, etc.). |
| `.env.example` | Template for required environment variables. |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* Python 3.9+
* `pip` (Python package manager)
* An AnyLogic Cloud API Key.

### 2. Environment Setup
The service requires an API Key. Create a `.env` file in the root directory:
```bash
ANYLOGIC_API_KEY='your-api-key-here'