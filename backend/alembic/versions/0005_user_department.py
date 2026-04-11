"""User 테이블에 department 필드 추가

Revision ID: 0005_user_department
Revises: 0004_chunk_page_number
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_user_department"
down_revision = "0004_chunk_page_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100)"
    ))


def downgrade() -> None:
    op.drop_column("users", "department")
