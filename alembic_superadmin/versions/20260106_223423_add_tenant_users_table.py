"""add tenant_users table

Revision ID: 20260106_223423
Revises: 
Create Date: 2026-01-06 22:34:23.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260106_223423'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create tenant_users table for mapping user emails to tenants.
    
    This allows any user (not just admins) to login by storing
    a mapping: email -> tenant_id in the Super Admin database.
    """
    op.create_table(
        'tenant_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_tenant_user_email')
    )
    op.create_index(op.f('ix_tenant_users_id'), 'tenant_users', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_users_email'), 'tenant_users', ['email'], unique=False)
    op.create_index(op.f('ix_tenant_users_tenant_id'), 'tenant_users', ['tenant_id'], unique=False)


def downgrade() -> None:
    """Drop tenant_users table."""
    op.drop_index(op.f('ix_tenant_users_tenant_id'), table_name='tenant_users')
    op.drop_index(op.f('ix_tenant_users_email'), table_name='tenant_users')
    op.drop_index(op.f('ix_tenant_users_id'), table_name='tenant_users')
    op.drop_table('tenant_users')


