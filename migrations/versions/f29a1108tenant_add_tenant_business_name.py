"""Store business names on member profiles and finalized contracts."""
from alembic import op
import sqlalchemy as sa


revision = 'f29a1108tenant'
down_revision = 'd2b4e6a8shape01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('business_name', sa.String(120)))
    op.add_column('contracts', sa.Column('user_business_name_snapshot', sa.String(120)))


def downgrade():
    op.drop_column('contracts', 'user_business_name_snapshot')
    op.drop_column('users', 'business_name')
