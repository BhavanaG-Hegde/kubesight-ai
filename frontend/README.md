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

## Routes

```text
/login
/register
/dashboard
/namespaces
/namespaces/:namespace/pods/:podName
/incidents
/ai
```
