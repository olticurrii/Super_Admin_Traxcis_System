"""Fix organization_settings table structure."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_organization_settings_table(db_name: str, tenant_id: int) -> dict:
    """
    Drop and recreate organization_settings table with correct structure.
    
    The table should NOT be a key-value store, but a single-row table
    with all settings as columns.
    
    Args:
        db_name: Name of the tenant database to fix
        tenant_id: The Super Admin tenant ID
        
    Returns:
        dict with status and message
    """
    try:
        # Construct database URL
        db_url = f"{settings.POSTGRES_SERVER_URL.rsplit('/', 1)[0]}/{db_name}"
        db_url = db_url.replace('/postgres', f'/{db_name}')
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Drop the old organization_settings table
            connection.execute(text("""
                DROP TABLE IF EXISTS organization_settings CASCADE;
            """))
            
            # Create the correct structure (single-row table with all settings as columns)
            connection.execute(text("""
                CREATE TABLE organization_settings (
                    id SERIAL PRIMARY KEY,
                    allow_breaks BOOLEAN DEFAULT true NOT NULL,
                    require_documentation BOOLEAN DEFAULT false NOT NULL,
                    orgchart_show_unassigned_panel BOOLEAN DEFAULT true NOT NULL,
                    orgchart_manager_subtree_edit BOOLEAN DEFAULT false NOT NULL,
                    orgchart_department_colors BOOLEAN DEFAULT true NOT NULL,
                    orgchart_compact_view BOOLEAN DEFAULT false NOT NULL,
                    orgchart_show_connectors BOOLEAN DEFAULT true NOT NULL,
                    feedback_allow_anonymous BOOLEAN DEFAULT true NOT NULL,
                    feedback_enable_threading BOOLEAN DEFAULT false NOT NULL,
                    feedback_enable_moderation BOOLEAN DEFAULT false NOT NULL,
                    feedback_notify_managers BOOLEAN DEFAULT true NOT NULL,
                    feedback_weekly_digest BOOLEAN DEFAULT false NOT NULL,
                    performance_module_enabled BOOLEAN DEFAULT true NOT NULL,
                    performance_allow_self_goals BOOLEAN DEFAULT true NOT NULL,
                    performance_require_goal_approval BOOLEAN DEFAULT false NOT NULL,
                    performance_enable_peer_reviews BOOLEAN DEFAULT false NOT NULL,
                    performance_allow_anonymous_peer BOOLEAN DEFAULT true NOT NULL,
                    performance_show_kpi_trends BOOLEAN DEFAULT true NOT NULL,
                    performance_top_performer_threshold INTEGER DEFAULT 80 NOT NULL,
                    performance_monthly_reports BOOLEAN DEFAULT true NOT NULL,
                    email_notifications_enabled BOOLEAN DEFAULT true NOT NULL,
                    inapp_notifications_enabled BOOLEAN DEFAULT true NOT NULL,
                    daily_summary_enabled BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
            """))
            
            connection.commit()
            
            logger.info(f"Fixed organization_settings table structure for {db_name}")
            
            return {
                "status": "success",
                "message": f"Fixed organization_settings table for {db_name}"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix organization_settings for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix organization_settings: {str(e)}"
        }


