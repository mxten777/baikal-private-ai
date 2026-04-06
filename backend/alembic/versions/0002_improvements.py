"""RAG improvements - query_logs, document permissions

Revision ID: 0002_improvements
Revises: 0001_initial
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_improvements"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. documents 테이블에 권한 컬럼 추가
    op.add_column("documents", sa.Column("allowed_roles", sa.JSON, nullable=True, server_default=None))
    op.add_column("documents", sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"))

    # 2. document_chunks에 nl_content 컬럼 추가 (표 자연어 임베딩용)
    op.add_column("document_chunks", sa.Column("nl_content", sa.Text, nullable=True))

    # 3. users 테이블에 department 컬럼 추가 (그룹 기반 권한)
    op.add_column("users", sa.Column("department", sa.String(100), nullable=True))

    # 4. query_logs 테이블 생성 (감사 로그)
    op.create_table(
        "query_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("response_summary", sa.Text, nullable=True),
        sa.Column("document_ids", sa.JSON, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_query_logs_user_id", "query_logs", ["user_id"])
    op.create_index("ix_query_logs_created_at", "query_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_query_logs_created_at", table_name="query_logs")
    op.drop_index("ix_query_logs_user_id", table_name="query_logs")
    op.drop_table("query_logs")
    op.drop_column("users", "department")
    op.drop_column("document_chunks", "nl_content")
    op.drop_column("documents", "is_public")
    op.drop_column("documents", "allowed_roles")
