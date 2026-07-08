from __future__ import annotations

import textwrap
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AIAnalysisError, AIAnalysisNotFoundError, IncidentNotFoundError
from app.models.ai_analysis import AIAnalysis
from app.models.incident import Incident
from app.models.pod import Pod
from app.repositories.ai_analysis_repository import AIAnalysisRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.kubernetes_catalog_repository import KubernetesCatalogRepository
from app.schemas.ai import (
    AIAnalysisRead,
    AIQuestionRequest,
    IncidentAnalysisRequest,
    PodLogAnalysisRequest,
)
from app.schemas.kubernetes import PodLogRead, PodRead
from app.services.kubernetes_service import KubernetesService


class AIAssistantService:
    def __init__(
        self,
        db: Session,
        kubernetes_service: KubernetesService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.kubernetes = kubernetes_service
        self.analyses = AIAnalysisRepository(db)
        self.incidents = IncidentRepository(db)
        self.catalog = KubernetesCatalogRepository(db)

    def get_analysis(self, analysis_id: UUID) -> AIAnalysisRead:
        analysis = self.analyses.get(analysis_id)
        if analysis is None:
            raise AIAnalysisNotFoundError("AI analysis not found.")
        return self.to_read_model(analysis)

    def list_recent_analyses(self, *, limit: int, offset: int) -> list[AIAnalysisRead]:
        return [
            self.to_read_model(analysis)
            for analysis in self.analyses.list_recent(limit=limit, offset=offset)
        ]

    def analyze_pod_logs(self, payload: PodLogAnalysisRequest) -> AIAnalysisRead:
        kubernetes = self._require_kubernetes()
        pod = kubernetes.get_pod(payload.namespace, payload.pod_name)
        logs = kubernetes.get_pod_logs(
            payload.namespace,
            payload.pod_name,
            container=payload.container,
            tail_lines=payload.tail_lines,
            previous=payload.previous,
            timestamps=True,
        )
        prompt = self._pod_log_prompt(pod=pod, logs=logs, question=payload.question)
        response = self._generate(prompt)
        pod_record = self._ensure_pod_record(pod)
        analysis = self._save_analysis(
            prompt=prompt,
            response=response,
            question=payload.question,
            pod_id=pod_record.id,
        )
        return self.to_read_model(analysis)

    def analyze_incident(
        self,
        incident_id: UUID,
        payload: IncidentAnalysisRequest,
    ) -> AIAnalysisRead:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError("Incident not found.")

        logs = self._incident_logs(incident, payload) if payload.include_pod_logs else None
        prompt = self._incident_prompt(
            incident=incident,
            logs=logs,
            question=payload.question,
        )
        response = self._generate(prompt)
        analysis = self._save_analysis(
            prompt=prompt,
            response=response,
            question=payload.question,
            incident_id=incident.id,
            pod_id=incident.pod_id,
        )
        return self.to_read_model(analysis)

    def answer_question(self, payload: AIQuestionRequest) -> AIAnalysisRead:
        incident: Incident | None = None
        pod: PodRead | None = None
        logs: PodLogRead | None = None
        stored_pod: Pod | None = None

        if payload.incident_id is not None:
            incident = self.incidents.get(payload.incident_id)
            if incident is None:
                raise IncidentNotFoundError("Incident not found.")

        if payload.namespace and payload.pod_name:
            kubernetes = self._require_kubernetes()
            pod = kubernetes.get_pod(payload.namespace, payload.pod_name)
            stored_pod = self._ensure_pod_record(pod)
            if payload.include_logs:
                logs = kubernetes.get_pod_logs(
                    payload.namespace,
                    payload.pod_name,
                    container=None,
                    tail_lines=payload.tail_lines,
                    previous=False,
                    timestamps=True,
                )

        prompt = self._question_prompt(
            question=payload.question,
            incident=incident,
            pod=pod,
            logs=logs,
        )
        response = self._generate(prompt)
        analysis = self._save_analysis(
            prompt=prompt,
            response=response,
            question=payload.question,
            incident_id=incident.id if incident else None,
            pod_id=stored_pod.id if stored_pod else incident.pod_id if incident else None,
        )
        return self.to_read_model(analysis)

    def to_read_model(self, analysis: AIAnalysis) -> AIAnalysisRead:
        return AIAnalysisRead(
            id=analysis.id,
            incident_id=analysis.incident_id,
            pod_id=analysis.pod_id,
            model_name=analysis.model_name,
            question=analysis.question,
            response=analysis.response,
            created_at=analysis.created_at,
        )

    def _save_analysis(
        self,
        *,
        prompt: str,
        response: str,
        question: str | None,
        incident_id: UUID | None = None,
        pod_id: UUID | None = None,
    ) -> AIAnalysis:
        analysis = self.analyses.create(
            model_name=self.settings.ollama_model,
            prompt=prompt,
            response=response,
            question=question,
            incident_id=incident_id,
            pod_id=pod_id,
        )
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def _generate(self, prompt: str) -> str:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        try:
            with httpx.Client(timeout=self.settings.ollama_request_timeout_seconds) as client:
                response = client.post(
                    url,
                    json={
                        "model": self.settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AIAnalysisError("Unable to reach Ollama for AI analysis.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AIAnalysisError("Ollama returned an invalid JSON response.") from exc

        if not isinstance(payload, dict):
            raise AIAnalysisError("Ollama returned an unexpected response shape.")
        answer = payload.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise AIAnalysisError("Ollama returned an empty AI analysis.")
        return answer.strip()

    def _pod_log_prompt(
        self,
        *,
        pod: PodRead,
        logs: PodLogRead,
        question: str | None,
    ) -> str:
        return self._base_prompt(
            context=f"""
            Analyze these Kubernetes pod logs.

            Namespace: {pod.namespace}
            Pod: {pod.name}
            Phase: {pod.phase}
            Restart count: {pod.restart_count}
            Ready containers: {pod.ready_containers}/{pod.total_containers}
            User question: {question or "Explain likely root cause and remediation."}

            Logs:
            {self._format_logs(logs.lines)}
            """
        )

    def _incident_prompt(
        self,
        *,
        incident: Incident,
        logs: PodLogRead | None,
        question: str | None,
    ) -> str:
        return self._base_prompt(
            context=f"""
            Analyze this stored Kubernetes incident.

            Title: {incident.title}
            Type: {incident.incident_type}
            Severity: {incident.severity}
            Status: {incident.status}
            Namespace: {incident.namespace.name if incident.namespace else "unknown"}
            Pod: {incident.pod.name if incident.pod else "unknown"}
            Summary: {incident.summary}
            Existing root cause: {incident.root_cause or "not recorded"}
            Existing recommendation: {incident.recommendation or "not recorded"}
            User question: {question or "Identify probable root cause and next steps."}

            Recent logs:
            {self._format_logs(logs.lines) if logs else "No logs included."}
            """
        )

    def _question_prompt(
        self,
        *,
        question: str,
        incident: Incident | None,
        pod: PodRead | None,
        logs: PodLogRead | None,
    ) -> str:
        incident_context = (
            f"""
            Incident title: {incident.title}
            Incident type: {incident.incident_type}
            Incident severity: {incident.severity}
            Incident summary: {incident.summary}
            """
            if incident
            else "No stored incident context supplied."
        )
        pod_context = (
            f"""
            Namespace: {pod.namespace}
            Pod: {pod.name}
            Phase: {pod.phase}
            Restart count: {pod.restart_count}
            Ready containers: {pod.ready_containers}/{pod.total_containers}
            """
            if pod
            else "No live pod context supplied."
        )
        return self._base_prompt(
            context=f"""
            Answer this Kubernetes troubleshooting question.

            Question: {question}

            Incident context:
            {incident_context}

            Pod context:
            {pod_context}

            Logs:
            {self._format_logs(logs.lines) if logs else "No logs included."}
            """
        )

    def _base_prompt(self, *, context: str) -> str:
        return textwrap.dedent(
            f"""
            You are KubeSight AI, a Kubernetes incident assistant.
            Use only the provided evidence. If evidence is insufficient, say what is missing.
            Keep the explanation practical and concise.

            Return the answer with these sections:
            1. Plain-language summary
            2. Probable root cause
            3. Evidence
            4. Troubleshooting steps
            5. Useful kubectl commands
            6. Prevention recommendation

            {textwrap.dedent(context).strip()}
            """
        ).strip()

    def _incident_logs(
        self,
        incident: Incident,
        payload: IncidentAnalysisRequest,
    ) -> PodLogRead | None:
        if incident.namespace is None or incident.pod is None:
            return None
        kubernetes = self._require_kubernetes()
        return kubernetes.get_pod_logs(
            incident.namespace.name,
            incident.pod.name,
            container=None,
            tail_lines=payload.tail_lines,
            previous=False,
            timestamps=True,
        )

    def _ensure_pod_record(self, pod: PodRead) -> Pod:
        cluster = self.catalog.ensure_cluster(
            name=self.settings.monitored_cluster_name,
            context_name=self.settings.kubernetes_context,
        )
        namespace = self.catalog.ensure_namespace(cluster=cluster, name=pod.namespace)
        stored_pod = self.catalog.ensure_pod(
            namespace=namespace,
            name=pod.name,
            phase=pod.phase,
            restart_count=pod.restart_count,
            ready_containers=pod.ready_containers,
            total_containers=pod.total_containers,
        )
        return stored_pod

    def _require_kubernetes(self) -> KubernetesService:
        if self.kubernetes is None:
            self.kubernetes = KubernetesService(settings=self.settings)
        return self.kubernetes

    def _format_logs(self, lines: list[str]) -> str:
        if not lines:
            return "No log lines returned."
        return "\n".join(lines[-200:])
