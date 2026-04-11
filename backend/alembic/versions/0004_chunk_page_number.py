"""DocumentChunk 페이지 번호 및 소스 타입 추가

Revision ID: 0004_chunk_page_number
Revises: 0003_querylog_kpi_fields
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_chunk_page_number"
down_revision = "0003_querylog_kpi_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL 네이티브 ADD COLUMN IF NOT EXISTS 사용 (asyncpg 호환)
    op.execute(sa.text(
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER"
    ))
    op.execute(sa.text(
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS source_type VARCHAR(20)"
    ))


def downgrade() -> None:
    op.drop_column("document_chunks", "source_type")
    op.drop_column("document_chunks", "page_number")
