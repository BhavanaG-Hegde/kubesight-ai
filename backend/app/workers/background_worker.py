from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import KubernetesClientError
from app.db.session import SessionLocal
from app.services.incident_history_service import IncidentHistoryService
from app.services.kubernetes_service import KubernetesService
from app.services.metrics_collection_service import MetricsCollectionService
from app.services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]
KubernetesServiceFactory = Callable[[], KubernetesService]


class BackgroundWorker:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        session_factory: SessionFactory = SessionLocal,
        kubernetes_service_factory: KubernetesServiceFactory = KubernetesService,
    ) -> None:
        self.settings = settings or get_settings()
        self.session_factory = session_factory
        self.kubernetes_service_factory = kubernetes_service_factory
        self._stop_event: asyncio.Event | None = None
        self._tasks: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        if not self.settings.background_worker_enabled:
            logger.info("Background worker is disabled.")
            return
        if self._tasks:
            return

        self._stop_event = asyncio.Event()
        self._tasks = [
            asyncio.create_task(
                self._run_periodic(
                    name="metrics_collection",
                    interval_seconds=self.settings.metrics_collection_interval_seconds,
                    operation=self.collect_metrics_once,
                )
            ),
            asyncio.create_task(
                self._run_periodic(
                    name="incident_scan",
                    interval_seconds=self.settings.incident_scan_interval_seconds,
                    operation=self.scan_incidents_once,
                )
            ),
        ]
        logger.info("Background worker started with %s tasks.", len(self._tasks))

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if not self._tasks:
            return

        done, pending = await asyncio.wait(self._tasks, timeout=10)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._tasks = []
        logger.info(
            "Background worker stopped. completed_tasks=%s cancelled_tasks=%s",
            len(done),
            len(pending),
        )

    async def _run_periodic(
        self,
        *,
        name: str,
        interval_seconds: int,
        operation: Callable[[], None],
    ) -> None:
        if self._stop_event is None:
            raise RuntimeError("Background worker stop event is not initialized.")

        while not self._stop_event.is_set():
            try:
                await asyncio.to_thread(operation)
            except Exception:
                logger.exception("Background worker task failed: %s", name)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                continue

    def collect_metrics_once(self) -> None:
        with self._session_scope() as db:
            service = MetricsCollectionService(
                db,
                self.kubernetes_service_factory(),
                settings=self.settings,
            )
            result = service.collect_now()
            logger.info(
                "Metrics collection completed: total_pods=%s pod_metrics=%s warnings=%s",
                result.total_pods,
                result.persisted_pod_metrics,
                len(result.warnings),
            )

    def scan_incidents_once(self) -> None:
        with self._session_scope() as db:
            kubernetes = self.kubernetes_service_factory()
            monitoring = MonitoringService(kubernetes)
            history = IncidentHistoryService(db, settings=self.settings)
            namespaces = self._namespaces_to_scan(kubernetes)

            for namespace in namespaces:
                try:
                    detection = monitoring.detect_namespace_incidents(
                        namespace,
                        include_logs=self.settings.incident_scan_include_logs,
                        tail_lines=self.settings.incident_scan_tail_lines,
                    )
                    result = history.persist_detection_result(detection)
                    logger.info(
                        "Incident scan completed for namespace=%s scanned=%s created=%s updated=%s",
                        namespace,
                        result.scanned_pods,
                        result.created,
                        result.updated,
                    )
                except KubernetesClientError as exc:
                    logger.warning(
                        "Incident scan skipped for namespace=%s: %s",
                        namespace,
                        exc,
                    )

    def _namespaces_to_scan(self, kubernetes: KubernetesService) -> list[str]:
        if self.settings.incident_scan_namespaces:
            return self.settings.incident_scan_namespaces

        excluded = set(self.settings.incident_scan_excluded_namespaces)
        namespaces = kubernetes.list_namespaces()
        return [
            namespace.name
            for namespace in namespaces
            if namespace.name not in excluded
        ]

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        db = self.session_factory()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
