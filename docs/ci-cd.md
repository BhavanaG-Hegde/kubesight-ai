# CI/CD

KubeSight AI uses GitHub Actions to keep every pull request and push to `main`
validated before it becomes part of the portfolio history.

## Pipeline

The CI workflow runs three jobs:

1. Backend
   - Installs the FastAPI package with development dependencies.
   - Runs Ruff linting.
   - Runs the pytest unit test suite on Python 3.11.

2. Frontend
   - Installs React dependencies with `npm ci`.
   - Runs ESLint.
   - Builds the Vite production bundle.
   - Audits production dependencies.

3. Docker
   - Validates `docker-compose.yml`.
   - Builds the backend image.
   - Builds the frontend image.

The Docker job depends on successful backend and frontend jobs so image builds
only run after the application checks are green.

## Dependency Updates

Dependabot checks GitHub Actions, frontend npm packages, and backend Python
packages weekly. This keeps the project close to current tooling without
introducing hidden automatic deploys.

## Local Commands

Run the same checks locally when the required runtimes are installed:

```bash
cd backend
pip install -e ".[dev]"
ruff check .
pytest -q
```

```bash
cd frontend
npm ci
npm run lint
npm run build
npm audit --omit=dev
```

```bash
docker compose config --quiet
docker build -f docker/backend.Dockerfile -t kubesight-ai-backend:local .
docker build -f docker/frontend.Dockerfile -t kubesight-ai-frontend:local .
```
