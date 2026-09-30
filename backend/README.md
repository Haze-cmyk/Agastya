# Agastya Backend: Quantum-Inspired Fleet Optimization Engine

FastAPI backend delivering hydrodynamic physics predictions, machine learning benchmarks, and quantum-inspired multi-objective evolutionary optimization algorithms (QIEA, QI-PSO, NSGA-II).

---

## Architecture & Directory Layout

```
backend/
├── app/
│   ├── main.py            # FastAPI entry point, CORS, payload limits, exception handlers
│   ├── api/               # API route controllers
│   │   ├── predict.py     # Fuel consumption prediction and ML training endpoints
│   │   ├── optimize.py    # Asynchronous background job creation, status, and cancel
│   │   ├── scenarios.py   # Multi-fuel sensitivity scenario analysis
│   │   ├── benchmark.py   # Statistical benchmark retrieval and live comparison
│   │   ├── health.py      # /health uptime and /api/version checks
│   │   └── data_routes.py # Reference vessel, fuel, port, and case study catalogs
│   ├── core/              # Configuration, structured logging, errors, seeded RNG
│   ├── models/            # Hydrodynamic physics engine, QIR, baseline regressors
│   ├── optimizers/        # QIEA, QI-PSO, NSGA-II, GA, PSO, Pareto archive tools
│   ├── constraints/       # Constraint validators, penalty functions, repair operator
│   ├── fuels/             # Fuel catalog, Well-to-Wake lifecycle calculator, shore power
│   ├── jobs/              # Bounded thread-safe in-memory job store & background runner
│   └── schemas/           # Strict Pydantic models with field diagnostics
├── data/                  # Static reference data (vessels, fuels, ports, synthetic data)
├── benchmarks/            # Statistical 30-run benchmark generator and precomputed JSON
├── tests/                 # Comprehensive pytest test suite
├── Dockerfile             # Slim container build specification
├── render.yaml            # Render deployment blueprint
├── railway.json           # Railway deployment configuration
├── requirements.txt       # Dependencies
└── .env.example           # Template configuration
```

---

## Local Development

### 1. Environment Setup
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc specification: `http://localhost:8000/redoc`

### 3. Run the Test Suite
```bash
pytest -v
```

---

## Deployment Instructions

### Deploy to Render
1. Connect your GitHub repository (`https://github.com/Haze-cmyk/Agastya.git`) to Render.
2. Select **New Web Service**.
3. Configure the following parameters:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add the required Environment Variables:
   - `ALLOWED_ORIGINS`: `https://agastya-fleet.netlify.app,http://localhost:5173`
   - `MAX_JOB_SECONDS`: `180`
   - `MAX_FLEET_SIZE`: `100`
   - `MAX_CONCURRENT_JOBS`: `3`
   - `RATE_LIMIT_PER_MINUTE`: `120`

### Deploy to Railway
1. Create a new Railway project and link the repository.
2. Under service settings, set the **Root Directory** to `backend`.
3. Railway automatically detects `railway.json` and `Dockerfile`.
4. Configure environment variables matching `.env.example`.

---

## Bounded Job Store Note
Optimization jobs run in an in-memory thread pool and are retained in an LRU queue (up to 100 jobs). If the server spins down (e.g. Render free tier sleep) or restarts, job state is lost. This is by design to eliminate external database overhead.
