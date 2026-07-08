from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.schemas.kubernetes import ContainerStatusRead, PodRead
from app.schemas.metrics import PodResourceMetricRead
from app.services.metrics_collection_service import MetricsCollectionService


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_collect_now_persists_cluster_snapshot_and_pod_metric(db_session: Session) -> None:
    service = MetricsCollectionService(
        db_session,
        FakeKubernetesService(),
        settings=Settings(
            monitored_cluster_name="test-cluster",
            secret_key="test-secret",
        ),
    )

    response = service.collect_now()
    snapshots = service.list_cluster_snapshots(limit=10)
    pod_metrics = service.list_pod_metrics(
        namespace="payments",
        pod_name="payment-service-9bf",
        since_minutes=None,
        limit=10,
    )

    assert response.metrics_api_available is True
    assert response.total_pods == 1
    assert response.cpu_millicores == 250
    assert response.memory_mebibytes == 128
    assert response.persisted_pod_metrics == 1
    assert response.pods_without_metrics == 0
    assert snapshots[0].cluster_name == "test-cluster"
    assert snapshots[0].restart_count == 2
    assert pod_metrics[0].pod_name == "payment-service-9bf"
    assert pod_metrics[0].cpu_millicores == 250


class FakeKubernetesService:
    def list_all_pods(self) -> list[PodRead]:
        return [
            PodRead(
                name="payment-service-9bf",
                namespace="payments",
                phase="Running",
                restart_count=2,
                ready_containers=1,
                total_containers=1,
                node_name="worker-1",
                containers=[
                    ContainerStatusRead(
                        name="payment-service",
                        ready=True,
                        restart_count=2,
                        state="running",
                    )
                ],
                labels={"app": "payment-service"},
                annotations={},
            )
        ]

    def list_pod_resource_metrics(self) -> list[PodResourceMetricRead]:
        return [
            PodResourceMetricRead(
                namespace="payments",
                pod_name="payment-service-9bf",
                cpu_millicores=250,
                memory_mebibytes=128,
            )
        ]
