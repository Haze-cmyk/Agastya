# Agastya: Edge-Case Verification Matrix

This matrix specifies all boundary conditions, defensive mechanisms, and verification targets implemented across the Agastya platform.

| Category | Edge Case / Boundary Condition | Defensive Mechanism / System Behavior | Verification Test Target |
| :--- | :--- | :--- | :--- |
| **Input & Data** | NaN, negative, zero, or missing numeric values | Backend Pydantic validation returns HTTP 422 with field-level diagnostic messages; frontend provides inline schema validation. | `tests/test_validation.py` & Vitest validation suite |
| **Input & Data** | Absurdly large values (e.g. speed = 500 kn, distance = $10^9$ nm) | Range bounded in schemas (`gt=0`, `le=40` for speed; `le=50000` for distance). Returns 422. | `tests/test_validation.py` |
| **Input & Data** | Decimal comma vs point (e.g. `12,5` vs `12.5`) | Robust string pre-processor parses European decimal commas into IEEE 754 floats. | `tests/test_data_parser.py` |
| **Input & Data** | CSV column mismatch, missing required columns | Detailed column diff returned with list of missing headers and suggested mappings. | `tests/test_data_parser.py` |
| **Input & Data** | Non-numeric or noisy text in numerical columns | Coerced to NaN with user notification; noisy outliers handled via median filtering. | `tests/test_data_parser.py` |
| **Input & Data** | Tiny dataset upload (< 10 rows) | Gracefully rejected with explanatory message requiring sufficient telemetry for training. | `tests/test_predict.py` |
| **Input & Data** | Oversized payload / upload (> 2MB) | Request rejected immediately with HTTP 413 Payload Too Large. | `tests/test_api_edge.py` |
| **Physics** | Very low speed ($v < 5$ kn) where hydrodynamic formula breaks | Clamped to minimum maneuverability speed; warning flag attached to output. | `tests/test_physics.py` |
| **Physics** | Very high speed ($v > 30$ kn) exceeding engine MCR | Power clamped to $P_{MCR}$; warning flag and cavitation/stall notice issued. | `tests/test_physics.py` |
| **Physics** | Extreme sea state (Beaufort scale $> 8$) | Non-linear wave resistance multiplier clamped at 2.50x with storm advisory. | `tests/test_physics.py` |
| **Physics** | Severe hull fouling ($t_{drydock} > 60$ months) | Progressive biofouling saturation model capped at $+40\%$ frictional resistance. | `tests/test_physics.py` |
| **Physics** | Low engine load ($L < 25\%$ MCR) | SFOC penalty function applies auxiliary blower and unburned hydrocarbon correction. | `tests/test_physics.py` |
| **Fuels** | LNG methane slip ($\mathrm{CH}_4$) | Well-to-wake lifecycle calculates 28x GWP penalty based on engine combustion cycle. | `tests/test_fuels.py` |
| **Fuels** | Ammonia nitrous oxide slip ($\mathrm{N}_2\mathrm{O}$) | Well-to-wake lifecycle calculates 273x GWP penalty based on SCR de-NOx efficiency. | `tests/test_fuels.py` |
| **Fuels** | Cryogenic fuel boil-off (LH2, LNG, NH3) | Boil-off rate ($\%/\text{day}$) subtracted and added to venting/auxiliary emissions. | `tests/test_fuels.py` |
| **Fuels** | Dual-fuel pilot injection & mismatched blends | Validates pilot fuel requirement ($3-5\%$) and enforces fuel blend sum $= 100\%$. | `tests/test_fuels.py` |
| **Optimization**| Infeasible problem (demand exceeds fleet capacity) | Never crashes. Returns best-effort closest candidate, penalty score, and list of violated constraints. | `tests/test_repair.py` & `test_optimizers.py` |
| **Optimization**| Emission cap below physical minimum | Infeasible flag set; repair heuristic suggests vessel count reduction or clean fuel switch. | `tests/test_repair.py` |
| **Optimization**| Degenerate or single-point Pareto front | Spacing calculation handles $|P^*| < 2$ without divide-by-zero; catastrophe gate diversifies population. | `tests/test_pareto.py` |
| **Optimization**| Selected fuel unavailable at bunkering port | Constraint validator flags port violation; repair operator swaps to available fuel or dual-fuel reserve. | `tests/test_repair.py` |
| **Optimization**| Shore power missing at destination port | Port compatibility validator forces auxiliary generator mode at berth. | `tests/test_shore_power.py` |
| **Optimization**| Route with zero cargo demand | Handled gracefully as empty repositioning leg or skipped vessel deployment. | `tests/test_optimizers.py` |
| **Optimization**| Fleet size = 1 or fleet size = hundreds | Dynamic allocation matrix scales from single-vessel loop to large fleet without array mismatch. | `tests/test_optimizers.py` |
| **Numerical** | Zero distance or zero travel time | Division-by-zero guard returns 0 fuel rate and zero speed instead of IEEE NaN/Inf. | `tests/test_physics.py` |
| **Numerical** | Seeded RNG reproducibility | Explicit random seeds in NumPy/Python yield bit-for-bit identical Pareto archives and training metrics. | `tests/test_rng.py` |
| **Runtime** | Job timeout (`MAX_JOB_SECONDS`) | Runner checks timeout per generation; terminates gracefully with partial Pareto front and status `TIMED_OUT`. | `tests/test_jobs.py` |
| **Runtime** | User cancels job mid-run (`POST /jobs/{id}/cancel`) | Worker checks cancellation token every generation and immediately releases worker thread. | `tests/test_jobs.py` |
| **Runtime** | Job store memory overflow | Bounded LRU store with maximum 100 jobs automatically purges oldest completed/failed jobs. | `tests/test_jobs.py` |
| **Runtime** | Rapid burst requests / DoS | In-memory token bucket rate limiter protects `/api/optimize` and `/api/benchmark`. | `tests/test_api_edge.py` |
| **Runtime** | Max concurrent optimization jobs | Queue limit (max 3 concurrent running jobs); returns HTTP 429 when saturated. | `tests/test_jobs.py` |
| **Network** | Render free-tier cold start | Frontend displays "Server is waking up" modal with exponential backoff retry. | Vitest network tests |
| **Network** | Backend unavailable or offline browser | Frontend switches seamlessly to local Web Worker engine with explicit "Reduced Local Mode" badge. | Vitest worker tests |
| **Network** | API version mismatch | Client queries `/api/version` on initial load; prompts user if schema version diverged. | Vitest API tests |
| **UI** | Double-click on Run button | Buttons immediately disable and show loading indicators upon initial click. | Vitest UI tests |
| **UI** | Browser refresh mid-run | Input parameters and active Job IDs persist in `localStorage`; state automatically resumes. | Vitest storage tests |
