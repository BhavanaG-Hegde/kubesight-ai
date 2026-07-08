# Roadmap

## Phase 1: Repository Foundation

- Create the folder structure.
- Add initial documentation.
- Add `.gitignore` and `.env.example`.
- Push the first commit to GitHub.

## Phase 2: Database Design

- Design users, clusters, pods, metrics, logs, incidents, and AI analysis tables.
- Add database migration tooling.

## Phase 3: Backend Foundation

- Create FastAPI app structure.
- Add settings, logging, exception handling, database session, and health endpoint.
- Add authentication with JWT.

## Phase 4: Frontend Foundation

- Create React TypeScript app.
- Add Material UI theme, routing, protected routes, and API client.

## Phase 5: Kubernetes Integration

- Connect to a local Kubernetes cluster.
- List namespaces, deployments, pods, services, pod events, and pod logs.
- Add read-only Kubernetes RBAC manifests.

## Phase 6: Monitoring And Incident Detection

- Implement pod health scoring. Done for live Kubernetes pod state, events, and logs.
- Detect known failure patterns. Done as incident candidates.
- Store incidents and expose incident history APIs. Done for rule-based detection sync.

## Phase 7: AI Assistant

- Connect to Ollama. Done for backend AI endpoints.
- Analyze logs and incidents using Llama 3.2. Done.
- Generate root cause summaries and troubleshooting steps. Done.

## Phase 8: Analytics And Production Polish

- Add charts and trend analysis.
- Add Dockerfiles and Docker Compose.
- Add GitHub Actions.
- Complete documentation.
