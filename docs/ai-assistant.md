# AI Assistant

KubeSight AI integrates with Ollama and Llama 3.2 for local troubleshooting
assistance. The backend sends Kubernetes logs, incident context, and user
questions to Ollama, then stores the generated analysis in PostgreSQL.

## Local Setup

Install and start Ollama, then pull the model:

```bash
ollama pull llama3.2
ollama serve
```

Environment variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_REQUEST_TIMEOUT_SECONDS=60
```

With Docker Compose, Ollama is available through the optional `ai` profile:

```bash
docker compose --profile ai up -d ollama
```

The model still needs to be pulled into the Ollama runtime.

## API Endpoints

All AI endpoints require JWT authentication.

```text
GET  /api/v1/ai/analyses
GET  /api/v1/ai/analyses/{analysis_id}
POST /api/v1/ai/pods/logs/analyze
POST /api/v1/ai/incidents/{incident_id}/analyze
POST /api/v1/ai/ask
```

## Use Cases

- Analyze selected pod logs.
- Explain a stored incident in plain language.
- Suggest root cause and troubleshooting steps.
- Answer focused questions such as:
  - Why is payment-service unhealthy?
  - What caused this restart?
  - How can I fix this issue?

## Persistence

Generated responses are stored in `ai_analyses` with optional links to:

- `incidents`
- `pods`

This makes AI output searchable and reviewable later instead of being a
throwaway chat response.
