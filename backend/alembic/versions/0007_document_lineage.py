"""P3-6: Document Lineage — chunk_count, updated_at 컬럼 추가"""
from alembic import op
import sqlalchemy as sa

revision = "0007_document_lineage"
down_revision = "0006_refresh_token_blacklist"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "documents",
        sa.Column("chunk_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    # 기존 완료된 문서의 chunk_count 역산 (마이그레이션 후 정확도 확보)
    op.execute(sa.text("""
        UPDATE documents d
        SET chunk_count = (
            SELECT COUNT(*) FROM document_chunks c WHERE c.document_id = d.id
        )
        WHERE d.status = 'completed'
    """))


def downgrade():
    op.drop_column("documents", "updated_at")
    op.drop_column("documents", "chunk_count")
