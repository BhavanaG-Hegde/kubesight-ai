from __future__ import annotations

import pytest

from app.core.config import Settings
from app.schemas.kubernetes import NamespaceRead
from app.workers.background_worker import BackgroundWorker


def test_namespaces_to_scan_excludes_system_namespaces() -> None:
    worker = BackgroundWorker(
        settings=Settings(
            secret_key="test-secret",
            incident_scan_excluded_namespaces=[
                "kube-system",
                "kube-public",
                "kube-node-lease",
                "kubesight",
            ],
        )
    )

    namespaces = worker._namespaces_to_scan(FakeKubernetesService())  # noqa: SLF001

    assert namespaces == ["payments", "orders"]


def test_explicit_namespaces_override_discovery() -> None:
    worker = BackgroundWorker(
        settings=Settings(
            secret_key="test-secret",
            incident_scan_namespaces=["kubesight-samples"],
        )
    )

    namespaces = worker._namespaces_to_scan(FakeKubernetesService())  # noqa: SLF001

    assert namespaces == ["kubesight-samples"]


@pytest.mark.asyncio
async def test_disabled_worker_does_not_start_tasks() -> None:
    worker = BackgroundWorker(
        settings=Settings(
            secret_key="test-secret",
            background_worker_enabled=False,
        )
    )

    await worker.start()

    assert worker._tasks == []  # noqa: SLF001


class FakeKubernetesService:
    def list_namespaces(self) -> list[NamespaceRead]:
        return [
            NamespaceRead(name="kube-system", status="Active", labels={}),
            NamespaceRead(name="kubesight", status="Active", labels={}),
            NamespaceRead(name="payments", status="Active", labels={}),
            NamespaceRead(name="orders", status="Active", labels={}),
        ]
