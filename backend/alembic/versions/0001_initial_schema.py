"""Create initial KubeSight AI schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("admin", "viewer", name="user_role")
cluster_status = sa.Enum("connected", "degraded", "disconnected", name="cluster_status")
pod_phase = sa.Enum("Running", "Pending", "Succeeded", "Failed", "Unknown", name="pod_phase")
health_status = sa.Enum("healthy", "warning", "critical", "unknown", name="health_status")
log_severity = sa.Enum(
    "trace",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "unknown",
    name="log_severity",
)
incident_type = sa.Enum(
    "crash_loop_back_off",
    "oom_killed",
    "image_pull_back_off",
    "high_restart_count",
    "high_cpu",
    "high_memory",
    "timeout_errors",
    "database_connection_failure",
    "error_log_spike",
    "pod_not_ready",
    name="incident_type",
)
incident_severity = sa.Enum("info", "warning", "critical", name="incident_severity")
incident_status = sa.Enum(
    "open",
    "acknowledged",
    "resolved",
    name="incident_status",
)


def created_at_column() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def updated_at_column() -> sa.Column:
    return sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "clusters",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("context_name", sa.String(length=255), nullable=True),
        sa.Column("api_server", sa.String(length=500), nullable=True),
        sa.Column("status", cluster_status, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clusters")),
    )
    op.create_index(op.f("ix_clusters_name"), "clusters", ["name"], unique=True)

    op.create_table(
        "cluster_snapshots",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_pods", sa.Integer(), nullable=False),
        sa.Column("running_pods", sa.Integer(), nullable=False),
        sa.Column("pending_pods", sa.Integer(), nullable=False),
        sa.Column("failed_pods", sa.Integer(), nullable=False),
        sa.Column("restart_count", sa.Integer(), nullable=False),
        sa.Column("cpu_millicores", sa.Integer(), nullable=False),
        sa.Column("memory_mebibytes", sa.Integer(), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("sampled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["cluster_id"],
            ["clusters.id"],
            name=op.f("fk_cluster_snapshots_cluster_id_clusters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cluster_snapshots")),
    )
    op.create_index(
        op.f("ix_cluster_snapshots_cluster_id"),
        "cluster_snapshots",
        ["cluster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cluster_snapshots_sampled_at"),
        "cluster_snapshots",
        ["sampled_at"],
        unique=False,
    )

    op.create_table(
        "kubernetes_namespaces",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["cluster_id"],
            ["clusters.id"],
            name=op.f("fk_kubernetes_namespaces_cluster_id_clusters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kubernetes_namespaces")),
        sa.UniqueConstraint(
            "cluster_id",
            "name",
            name=op.f("uq_namespaces_cluster_id_name"),
        ),
    )
    op.create_index(
        op.f("ix_kubernetes_namespaces_cluster_id"),
        "kubernetes_namespaces",
        ["cluster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_kubernetes_namespaces_name"),
        "kubernetes_namespaces",
        ["name"],
        unique=False,
    )

    op.create_table(
        "deployments",
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("desired_replicas", sa.Integer(), nullable=False),
        sa.Column("available_replicas", sa.Integer(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("selector", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["kubernetes_namespaces.id"],
            name=op.f("fk_deployments_namespace_id_kubernetes_namespaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deployments")),
        sa.UniqueConstraint(
            "namespace_id",
            "name",
            name=op.f("uq_deployments_namespace_id_name"),
        ),
    )
    op.create_index(op.f("ix_deployments_name"), "deployments", ["name"], unique=False)
    op.create_index(
        op.f("ix_deployments_namespace_id"),
        "deployments",
        ["namespace_id"],
        unique=False,
    )

    op.create_table(
        "kubernetes_services",
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("service_type", sa.String(length=80), nullable=True),
        sa.Column("cluster_ip", sa.String(length=80), nullable=True),
        sa.Column("ports", sa.JSON(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["kubernetes_namespaces.id"],
            name=op.f("fk_kubernetes_services_namespace_id_kubernetes_namespaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kubernetes_services")),
        sa.UniqueConstraint(
            "namespace_id",
            "name",
            name=op.f("uq_services_namespace_id_name"),
        ),
    )
    op.create_index(
        op.f("ix_kubernetes_services_name"),
        "kubernetes_services",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_kubernetes_services_namespace_id"),
        "kubernetes_services",
        ["namespace_id"],
        unique=False,
    )

    op.create_table(
        "pods",
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("node_name", sa.String(length=255), nullable=True),
        sa.Column("phase", pod_phase, nullable=False),
        sa.Column("health_status", health_status, nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("restart_count", sa.Integer(), nullable=False),
        sa.Column("ready_containers", sa.Integer(), nullable=False),
        sa.Column("total_containers", sa.Integer(), nullable=False),
        sa.Column("cpu_millicores", sa.Integer(), nullable=False),
        sa.Column("memory_mebibytes", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("owner_kind", sa.String(length=80), nullable=True),
        sa.Column("owner_name", sa.String(length=255), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("annotations", sa.JSON(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["kubernetes_namespaces.id"],
            name=op.f("fk_pods_namespace_id_kubernetes_namespaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pods")),
        sa.UniqueConstraint("namespace_id", "name", name=op.f("uq_pods_namespace_id_name")),
    )
    op.create_index(op.f("ix_pods_health_status"), "pods", ["health_status"], unique=False)
    op.create_index(op.f("ix_pods_name"), "pods", ["name"], unique=False)
    op.create_index(op.f("ix_pods_namespace_id"), "pods", ["namespace_id"], unique=False)
    op.create_index(op.f("ix_pods_phase"), "pods", ["phase"], unique=False)

    op.create_table(
        "incidents",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("incident_type", incident_type, nullable=False),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("status", incident_status, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("detection_source", sa.String(length=80), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["cluster_id"],
            ["clusters.id"],
            name=op.f("fk_incidents_cluster_id_clusters"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["kubernetes_namespaces.id"],
            name=op.f("fk_incidents_namespace_id_kubernetes_namespaces"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            name=op.f("fk_incidents_pod_id_pods"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
    )
    op.create_index(op.f("ix_incidents_cluster_id"), "incidents", ["cluster_id"], unique=False)
    op.create_index(
        op.f("ix_incidents_incident_type"),
        "incidents",
        ["incident_type"],
        unique=False,
    )
    op.create_index(op.f("ix_incidents_namespace_id"), "incidents", ["namespace_id"], unique=False)
    op.create_index(op.f("ix_incidents_pod_id"), "incidents", ["pod_id"], unique=False)
    op.create_index(op.f("ix_incidents_severity"), "incidents", ["severity"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)

    op.create_table(
        "log_entries",
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("container_name", sa.String(length=120), nullable=False),
        sa.Column("severity", log_severity, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            name=op.f("fk_log_entries_pod_id_pods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_log_entries")),
    )
    op.create_index(
        op.f("ix_log_entries_fingerprint"),
        "log_entries",
        ["fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_log_entries_observed_at"),
        "log_entries",
        ["observed_at"],
        unique=False,
    )
    op.create_index(op.f("ix_log_entries_pod_id"), "log_entries", ["pod_id"], unique=False)
    op.create_index(op.f("ix_log_entries_severity"), "log_entries", ["severity"], unique=False)

    op.create_table(
        "pod_events",
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_uid", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_component", sa.String(length=120), nullable=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            name=op.f("fk_pod_events_pod_id_pods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pod_events")),
        sa.UniqueConstraint("pod_id", "event_uid", name=op.f("uq_pod_events_pod_id_event_uid")),
    )
    op.create_index(op.f("ix_pod_events_pod_id"), "pod_events", ["pod_id"], unique=False)
    op.create_index(op.f("ix_pod_events_reason"), "pod_events", ["reason"], unique=False)

    op.create_table(
        "pod_metrics",
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cpu_millicores", sa.Integer(), nullable=False),
        sa.Column("memory_mebibytes", sa.Integer(), nullable=False),
        sa.Column("cpu_limit_millicores", sa.Integer(), nullable=True),
        sa.Column("memory_limit_mebibytes", sa.Integer(), nullable=True),
        sa.Column("sampled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            name=op.f("fk_pod_metrics_pod_id_pods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pod_metrics")),
    )
    op.create_index(op.f("ix_pod_metrics_pod_id"), "pod_metrics", ["pod_id"], unique=False)
    op.create_index(op.f("ix_pod_metrics_sampled_at"), "pod_metrics", ["sampled_at"], unique=False)

    op.create_table(
        "ai_analyses",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pod_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_ai_analyses_incident_id_incidents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            name=op.f("fk_ai_analyses_pod_id_pods"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_analyses")),
    )
    op.create_index(
        op.f("ix_ai_analyses_incident_id"),
        "ai_analyses",
        ["incident_id"],
        unique=False,
    )
    op.create_index(op.f("ix_ai_analyses_pod_id"), "ai_analyses", ["pod_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_analyses_pod_id"), table_name="ai_analyses")
    op.drop_index(op.f("ix_ai_analyses_incident_id"), table_name="ai_analyses")
    op.drop_table("ai_analyses")

    op.drop_index(op.f("ix_pod_metrics_sampled_at"), table_name="pod_metrics")
    op.drop_index(op.f("ix_pod_metrics_pod_id"), table_name="pod_metrics")
    op.drop_table("pod_metrics")

    op.drop_index(op.f("ix_pod_events_reason"), table_name="pod_events")
    op.drop_index(op.f("ix_pod_events_pod_id"), table_name="pod_events")
    op.drop_table("pod_events")

    op.drop_index(op.f("ix_log_entries_severity"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_pod_id"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_observed_at"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_fingerprint"), table_name="log_entries")
    op.drop_table("log_entries")

    op.drop_index(op.f("ix_incidents_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_severity"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_pod_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_namespace_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_incident_type"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_cluster_id"), table_name="incidents")
    op.drop_table("incidents")

    op.drop_index(op.f("ix_pods_phase"), table_name="pods")
    op.drop_index(op.f("ix_pods_namespace_id"), table_name="pods")
    op.drop_index(op.f("ix_pods_name"), table_name="pods")
    op.drop_index(op.f("ix_pods_health_status"), table_name="pods")
    op.drop_table("pods")

    op.drop_index(op.f("ix_kubernetes_services_namespace_id"), table_name="kubernetes_services")
    op.drop_index(op.f("ix_kubernetes_services_name"), table_name="kubernetes_services")
    op.drop_table("kubernetes_services")

    op.drop_index(op.f("ix_deployments_namespace_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_name"), table_name="deployments")
    op.drop_table("deployments")

    op.drop_index(op.f("ix_kubernetes_namespaces_name"), table_name="kubernetes_namespaces")
    op.drop_index(op.f("ix_kubernetes_namespaces_cluster_id"), table_name="kubernetes_namespaces")
    op.drop_table("kubernetes_namespaces")

    op.drop_index(op.f("ix_cluster_snapshots_sampled_at"), table_name="cluster_snapshots")
    op.drop_index(op.f("ix_cluster_snapshots_cluster_id"), table_name="cluster_snapshots")
    op.drop_table("cluster_snapshots")

    op.drop_index(op.f("ix_clusters_name"), table_name="clusters")
    op.drop_table("clusters")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    incident_status.drop(bind, checkfirst=True)
    incident_severity.drop(bind, checkfirst=True)
    incident_type.drop(bind, checkfirst=True)
    log_severity.drop(bind, checkfirst=True)
    health_status.drop(bind, checkfirst=True)
    pod_phase.drop(bind, checkfirst=True)
    cluster_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
