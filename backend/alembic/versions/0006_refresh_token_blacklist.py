"""P3-5: Refresh Token 블랙리스트 테이블 생성"""
from alembic import op
import sqlalchemy as sa

revision = "0006_refresh_token_blacklist"
down_revision = "0005_user_department"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS refresh_token_blacklist (
            jti VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_rtb_user_id ON refresh_token_blacklist(user_id)
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_rtb_expires_at ON refresh_token_blacklist(expires_at)
    """))


def downgrade():
    op.execute(sa.text("DROP TABLE IF EXISTS refresh_token_blacklist"))
