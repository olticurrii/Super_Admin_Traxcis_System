"""add company_name to tenants

Revision ID: 20260106_224500
Revises: 20260106_223423
Create Date: 2026-01-06 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260106_224500'
down_revision = '20260106_223423'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add company_name column to tenants table.
    
    This allows users to login by providing their company name,
    making it easy to find the correct tenant without needing
    to pre-register every user.
    """
    # Add company_name column (nullable first for existing data)
    op.add_column('tenants', sa.Column('company_name', sa.String(), nullable=True))
    
    # For existing tenants, set company_name = name (as default)
    op.execute("UPDATE tenants SET company_name = name WHERE company_name IS NULL")
    
    # Now make it NOT NULL
    op.alter_column('tenants', 'company_name', nullable=False)
    
    # Add unique constraint and index
    op.create_unique_constraint('uq_tenant_company_name', 'tenants', ['company_name'])
    op.create_index(op.f('ix_tenants_company_name'), 'tenants', ['company_name'], unique=False)


def downgrade() -> None:
    """Remove company_name column."""
    op.drop_index(op.f('ix_tenants_company_name'), table_name='tenants')
    op.drop_constraint('uq_tenant_company_name', 'tenants', type_='unique')
    op.drop_column('tenants', 'company_name')

