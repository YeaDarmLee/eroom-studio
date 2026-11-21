"""Add rooms.shape (optional CSS polygon for non-rectangular rooms on floor plans).

Revision ID: d2b4e6a8shape01
Revises: c7a1d3f0pub01
"""
from alembic import op
import sqlalchemy as sa

revision = 'd2b4e6a8shape01'
down_revision = 'c7a1d3f0pub01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms', sa.Column('shape', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('rooms', 'shape')
