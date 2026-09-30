# Agastya Frontend: Green Fleet Engineering Portal

Single Page Application providing interactive Pareto front analysis, single-vessel hydrodynamic fuel prediction, alternative fuel sensitivity sliders, and statistical algorithm benchmarking. Built with React 18, TypeScript, and Vite.

---

## Design System & Palette

Agastya implements a rigorous industrial engineering design system adhering strictly to the required palette:
- **Golden Earth** (`#99621E`): Primary accent, navigation active marks, primary action buttons.
- **Toasted Almond** (`#D38B5D`): Secondary accent, chart marks, fill highlights.
- **Lime Cream** (`#F3FFB6`): Page canvas, soft panel backgrounds.
- **Muted Teal** (`#739E82`): Subdued structural borders, secondary button actions.
- **Dark Spruce** (`#2C5530`): Primary typography, high-contrast headings, header/footer backgrounds.

All text combinations achieve WCAG AA contrast (contrast ratio 8.4:1 on canvas).

---

## Directory Structure

```
frontend/
├── src/
│   ├── components/        # Navigation sidebar, Header bar, Status badges, Alert banners
│   ├── pages/             # Optimizer, Predictor, Scenario Analyzer, Benchmarks, Case Studies
│   ├── charts/            # Responsive SVG Pareto front charts, SFOC curves, waterfall charts
│   ├── workers/           # Web Worker simulation engine for offline / reduced local mode
│   ├── lib/               # Typed API client, exponential backoff retries, CSV export/import
│   ├── types/             # Shared TypeScript schemas
│   └── styles/            # Theme variables and global print stylesheets
├── public/                # Static assets, SVG icon
├── tests/                 # Vitest test suite
├── netlify.toml           # Netlify build and redirect configuration
├── _headers               # Production security headers
├── package.json           # Dependencies and scripts
└── vite.config.ts         # Vite build configuration
```

---

## Local Development

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Run Unit Tests
```bash
npm run test
```

### Production Build
```bash
npm run build
```

---

## Netlify Deployment Settings
- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Environment variables**:
  - `VITE_API_URL`: URL of deployed FastAPI backend (e.g. `https://agastya-backend.onrender.com`)
