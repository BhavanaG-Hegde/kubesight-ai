# KubeSight AI Frontend

React TypeScript dashboard for the KubeSight AI Kubernetes observability
platform.

## Local Development

```bash
cd frontend
npm install
npm run dev
```

The app expects the backend at:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Quality Checks

```bash
npm run lint
npm run test
npm run test:e2e
npm run build
npm audit --omit=dev
```

The Playwright suite starts Vite automatically and mocks backend API responses
for smoke coverage of protected routes, analytics, and incident detail.

## Routes

```text
/login
/register
/dashboard
/analytics
/namespaces
/namespaces/:namespace/pods/:podName
/incidents
/incidents/:incidentId
/ai
```
