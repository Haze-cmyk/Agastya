# Agastya: Quantum-Inspired Green Fleet Optimizer

Agastya is a high-performance maritime engineering platform designed to optimize commercial vessel fleet deployment, operational cruising speeds, alternative fuel transitions, and port shore power utilization. By synthesizing hydrodynamic propulsion physics with quantum-inspired multi-objective evolutionary algorithms, Agastya assists fleet managers, charterers, and decarbonization analysts in navigating conflicting trade-offs between bunker fuel consumption, voyage operating expenditures, and lifecycle Well-to-Wake (WTW) greenhouse gas emissions.

---

## Architecture Overview

Agastya is architected as two decoupled systems communicating solely via a validated REST API:
- **Frontend**: Single Page Application built with Vite, React, TypeScript, and self-hosted styling. Deploys statically to Netlify. Includes client-side Web Worker fallback for offline simulation.
- **Backend**: Asynchronous REST API powered by FastAPI, NumPy, SciPy, and scikit-learn. Deploys to containerized environments (Render, Railway, Docker). Runs multi-objective optimization as bounded background jobs.

```
                      +------------------------------------------+
                      |         Agastya Frontend (Vite)          |
                      |   - React 18 + TypeScript + UI Engine    |
                      |   - Interactive Pareto 2D/3D Charts      |
                      |   - Scenario Sensitivity Sliders         |
                      |   - Web Worker Offline Fallback Engine   |
                      +--------------------+---------------------+
                                           |
                                  HTTP / JSON (REST)
                                           |
                      +--------------------v---------------------+
                      |         Agastya Backend (FastAPI)        |
                      +------------------------------------------+
                      |                                          |
                      |  +------------------------------------+  |
                      |  |     Hydrodynamic Physics Engine    |  |
                      |  |  - Speed^n power law               |  |
                      |  |  - Part-load SFOC curve            |  |
                      |  |  - Beaufort added resistance       |  |
                      |  |  - Progressive hull biofouling     |  |
                      |  +------------------------------------+  |
                      |                                          |
                      |  +------------------------------------+  |
                      |  |  Well-to-Wake Fuels & Slip Engine  |  |
                      |  |  - HFO, VLSFO, MGO, LNG, Methanol  |  |
                      |  |  - Ammonia, Liquid Hydrogen        |  |
                      |  |  - Methane & N2O slip penalties    |  |
                      |  |  - Cryogenic boil-off gas (BOG)    |  |
                      |  +------------------------------------+  |
                      |                                          |
                      |  +------------------------------------+  |
                      |  |   Multi-Objective Metaheuristics   |  |
                      |  |  - QIEA (Quantum Rotation Gates)   |  |
                      |  |  - QI-PSO (Delta Potential Well)   |  |
                      |  |  - NSGA-II, Classical GA, PSO      |  |
                      |  |  - Pareto Archive & Hypervolume    |  |
                      |  +------------------------------------+  |
                      |                                          |
                      |  +------------------------------------+  |
                      |  |  Bounded Asynchronous Job Manager  |  |
                      |  |  - Non-blocking background worker  |  |
                      |  |  - Token-bucket rate limiter       |  |
                      |  |  - Graceful cancellation & timeout |  |
                      |  +------------------------------------+  |
                      +------------------------------------------+
```

---

## Key Features

1. **Hydrodynamic Propulsion Modeling**:
   - Vessel-specific speed exponent ($P \propto \Delta^{2/3} v^n$) where $n$ is calibrated by hull type (container, bulk carrier, tanker).
   - Realistic non-linear SFOC engine efficiency curve with low-load penalties.
   - Environmental added resistance via Douglas/Beaufort scale.
   - Hull roughness and biofouling degradation over docking cycles.
   - Hydrodynamic speed clamping with cavitation and maneuverability guards.

2. **Quantum-Inspired Optimization**:
   - **QIEA (Quantum-Inspired Evolutionary Algorithm)**: Employs Q-bit representation ($|\psi\rangle = \cos\theta|0\rangle + \sin\theta|1\rangle$) and unitary quantum rotation gates to navigate high-dimensional non-linear fleet decision spaces. Includes an $H_\epsilon$ catastrophe operator to escape premature convergence.
   - **QI-PSO (Quantum-Behaved PSO)**: Implements delta-potential well dynamics with stochastic state collapse.
   - Classical baselines for honest comparison: **NSGA-II**, **Classical GA**, and **Classical PSO**.

3. **Alternative Fuel & Lifecycle Analysis**:
   - Compares conventional fuels (HFO, VLSFO, MGO) against decarbonization pathways (LNG, Methanol, Ammonia, Hydrogen).
   - Detailed calculations of Tank-to-Wake (TTW) combustion, Well-to-Tank (WTT) upstream factors, LNG methane slip, ammonia $\mathrm{N}_2\mathrm{O}$ slip, and cryogenic boil-off gas.
   - Cold ironing / Onshore Power Supply (OPS) integration based on port grid carbon intensity.

4. **Robust Boundary & Error Handling**:
   - Two-sided validation (FastAPI Pydantic models with field-level diagnostics, React inline validation).
   - Infeasible demand/emission handling: returns closest repaired solution plus itemized constraint breaches.
   - Protected against NaN, division-by-zero, negative speeds, and oversized payloads (413).
   - Asynchronous job execution with configurable timeouts (`MAX_JOB_SECONDS`), cancel triggers, and bounded memory (LRU job purge).

5. **Client-Side Offline Fallback**:
   - If the backend is undergoing a cold start or network connectivity drops, the frontend automatically switches to an in-browser Web Worker executing physics calculations and a reduced genetic optimizer.

---

## Directory Structure

```
Agastya/
├── frontend/               # Vite + React + TypeScript web application
│   ├── src/
│   │   ├── components/     # UI building blocks (Navigation, Header, Status, Modal)
│   │   ├── pages/          # Predictor, Optimizer, Scenarios, Benchmarks, Case Studies
│   │   ├── charts/         # SVG/Canvas Pareto fronts, SFOC curves, sensitivity charts
│   │   ├── workers/        # Dedicated Web Worker for offline fallback simulation
│   │   ├── lib/            # API client with exponential backoff, math utilities, parsers
│   │   ├── types/          # Shared TypeScript interfaces
│   │   └── styles/         # WCAG AA theme system adhering to strict engineering palette
│   ├── public/             # Static assets, fonts, icons
│   ├── tests/              # Vitest unit and integration test suite
│   ├── netlify.toml        # Netlify deployment configuration
│   ├── _headers            # Security and cache control headers
│   └── package.json
│
├── backend/                # FastAPI Python application
│   ├── app/
│   │   ├── main.py         # Application entry point, middleware, routes
│   │   ├── api/            # Route controllers (predict, optimize, benchmark, scenarios, health)
│   │   ├── core/           # Configuration, structured logging, errors, seeded RNG
│   │   ├── models/         # Hydrodynamic physics, QI regressor, machine learning baselines
│   │   ├── optimizers/     # QIEA, QI-PSO, NSGA-II, GA, PSO, Pareto archive
│   │   ├── constraints/    # Penalty formulations, repair heuristics, domain validators
│   │   ├── fuels/          # Fuel specifications, lifecycle WTW calculations, shore power
│   │   ├── jobs/           # In-memory bounded LRU job store, asynchronous runner
│   │   └── schemas/        # Pydantic schemas with comprehensive boundary validations
│   ├── data/               # Reference vessels, fuels, ports, and synthetic generator
│   ├── benchmarks/         # Precomputed 30-run statistical benchmark datasets & scripts
│   ├── tests/              # Pytest comprehensive test suite
│   ├── Dockerfile          # Container specification
│   ├── render.yaml         # Render deployment blueprint
│   ├── railway.json        # Railway deployment configuration
│   └── requirements.txt
│
├── docs/                   # Engineering documentation
│   ├── math_model.md       # Full mathematical & physics formulations
│   ├── api_reference.md    # REST API endpoints, schemas, and codes
│   └── edge_case_matrix.md # Boundary conditions and verification matrix
│
├── LICENSE                 # MIT License
└── README.md               # Root documentation
```

---

## Local Development Quickstart

### Prerequisites
- Node.js (v18+ recommended) & npm
- Python (3.11+ recommended) & pip

### Backend Setup
1. Open a terminal in `backend/`:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create local environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
4. Access interactive OpenAPI documentation at `http://localhost:8000/docs`.

### Frontend Setup
1. Open a terminal in `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Configure local environment:
   ```bash
   cp .env.example .env
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:5173` in your browser.

---

## Testing

### Backend Test Suite (pytest)
From `backend/`:
```bash
pytest -v
```

### Frontend Test Suite (Vitest)
From `frontend/`:
```bash
npm run test
```

---

## Deployment Settings

### Backend: Railway (Active Production)
- **Live Endpoint**: `https://agastya-production-b60f.up.railway.app`
- **Documentation**: `https://agastya-production-b60f.up.railway.app/docs`
- **Healthcheck Path**: `/health`
- **Root Directory**: `backend`
- **Build / Start**: Auto-detected via `backend/Dockerfile` and `backend/railway.json`
- **Environment variables**:
  - `ALLOWED_ORIGINS`: `*` (or comma-separated list of allowed origins)
  - `PORT`: `8000` (set automatically by host)
  - `MAX_JOB_SECONDS`: `180`
  - `MAX_FLEET_SIZE`: `100`

### Frontend: Netlify
- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Environment variables**:
  - `VITE_API_URL`: `https://agastya-production-b60f.up.railway.app` (preconfigured in `frontend/netlify.toml`)

---

## Known Limitations

1. **Synthetic Telemetry Baseline**: In the absence of proprietary onboard high-frequency noon-report telemetry, benchmark datasets are synthetically generated using calibrated hydrodynamic physical formulations with Gaussian sensor perturbation.
2. **In-Memory Volatile Job Store**: Optimization background jobs are tracked in an in-memory LRU queue. A server restart or Render free-tier spin-down will reset active jobs.
3. **2D Route Network Assumption**: Weather routing is parameterized via sea-state resistance multipliers along fixed great-circle route distances rather than dynamic isochrone pathfinding across 4D ocean currents.

---

## License
MIT License. See [LICENSE](file:///c:/Users/Jayesh%20Thakur/Desktop/Agastya/LICENSE) for details.
