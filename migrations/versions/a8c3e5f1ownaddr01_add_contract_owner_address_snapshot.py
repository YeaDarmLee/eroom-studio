"""Freeze the lessor address on signed contracts."""
from alembic import op
import sqlalchemy as sa


revision = 'a8c3e5f1ownaddr01'
down_revision = 'f29a1108tenant'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contracts', sa.Column('owner_address_snapshot', sa.String(255)))


def downgrade():
    op.drop_column('contracts', 'owner_address_snapshot')
