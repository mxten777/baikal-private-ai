"""Stage 1.2: 인덱싱 진행률 컬럼 추가

documents.total_chunks    — 전체 청크 수 (청킹 직후 결정)
documents.processed_chunks — 임베딩+저장 완료된 청크 수 (batch마다 증가)
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_indexing_progress"
down_revision = "0007_document_lineage"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "documents",
        sa.Column("total_chunks", sa.Integer(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processed_chunks", sa.Integer(), nullable=True),
    )
    # 기존 완료된 문서는 chunk_count == total_chunks == processed_chunks
    op.execute(sa.text("""
        UPDATE documents
        SET total_chunks = chunk_count,
            processed_chunks = chunk_count
        WHERE status = 'completed'
    """))


def downgrade():
    op.drop_column("documents", "processed_chunks")
    op.drop_column("documents", "total_chunks")
