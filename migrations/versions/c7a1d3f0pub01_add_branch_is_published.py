"""Add branches.is_published (existing branches stay published).

Revision ID: c7a1d3f0pub01
Revises: b6e1106flowfix
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7a1d3f0pub01'
down_revision = 'b6e1106flowfix'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('branches', sa.Column('is_published', sa.Boolean(), nullable=False,
                                        server_default=sa.true()))


def downgrade():
    op.drop_column('branches', 'is_published')
