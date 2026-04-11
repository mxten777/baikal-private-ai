"""QueryLog KPI 필드 확장

Revision ID: 0003_querylog_kpi_fields
Revises: 0002_improvements
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_querylog_kpi_fields"
down_revision = "0002_improvements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL 네이티브 ADD COLUMN IF NOT EXISTS 사용 (asyncpg 호환)
    ddl_statements = [
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS session_id VARCHAR(36)",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS retrieved_chunks JSON",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS reranked_order JSON",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS cited_sources JSON",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS model_name VARCHAR(100)",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS retrieval_ms INTEGER",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS reranking_ms INTEGER",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS llm_ms INTEGER",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS feedback_score INTEGER",
        "ALTER TABLE query_logs ADD COLUMN IF NOT EXISTS click_source_flag BOOLEAN",
    ]
    for stmt in ddl_statements:
        op.execute(sa.text(stmt))


def downgrade() -> None:
    op.drop_column("query_logs", "click_source_flag")
    op.drop_column("query_logs", "feedback_score")
    op.drop_column("query_logs", "llm_ms")
    op.drop_column("query_logs", "reranking_ms")
    op.drop_column("query_logs", "retrieval_ms")
    op.drop_column("query_logs", "model_name")
    op.drop_column("query_logs", "cited_sources")
    op.drop_column("query_logs", "reranked_order")
    op.drop_column("query_logs", "retrieved_chunks")
    op.drop_column("query_logs", "session_id")
