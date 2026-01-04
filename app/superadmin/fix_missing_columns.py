"""Fix script to add missing columns to existing tables."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_missing_columns(db_name: str, tenant_id: int) -> dict:
    """
    Add missing columns to existing tables based on HRMS backend requirements.
    
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
            # Fix organization_settings table - add ALL missing columns
            connection.execute(text("""
                ALTER TABLE organization_settings 
                ADD COLUMN IF NOT EXISTS allow_breaks BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS require_documentation BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS orgchart_show_unassigned_panel BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS orgchart_manager_subtree_edit BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS orgchart_department_colors BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS orgchart_compact_view BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS orgchart_show_connectors BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS feedback_allow_anonymous BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS feedback_enable_threading BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS feedback_enable_moderation BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS feedback_notify_managers BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS feedback_weekly_digest BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_module_enabled BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_allow_self_goals BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_require_goal_approval BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_enable_peer_reviews BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_allow_anonymous_peer BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_show_kpi_trends BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_top_performer_threshold INTEGER DEFAULT 80 NOT NULL,
                ADD COLUMN IF NOT EXISTS performance_monthly_reports BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS inapp_notifications_enabled BOOLEAN DEFAULT true NOT NULL,
                ADD COLUMN IF NOT EXISTS daily_summary_enabled BOOLEAN DEFAULT false NOT NULL;
            """))
            
            # Fix time_entries table - add missing columns
            connection.execute(text("""
                ALTER TABLE time_entries 
                ADD COLUMN IF NOT EXISTS break_start TIMESTAMP,
                ADD COLUMN IF NOT EXISTS break_end TIMESTAMP,
                ADD COLUMN IF NOT EXISTS is_terrain BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS work_summary VARCHAR;
            """))
            
            # Fix performance_objectives table - add missing columns
            connection.execute(text("""
                ALTER TABLE performance_objectives 
                ADD COLUMN IF NOT EXISTS start_date DATE,
                ADD COLUMN IF NOT EXISTS approved_by_id INTEGER REFERENCES users(id),
                ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'pending',
                ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP,
                ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR;
            """))
            
            # Rename created_by to created_by_id in performance_objectives if needed
            # First check if created_by exists and created_by_id doesn't
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'performance_objectives' 
                AND column_name IN ('created_by', 'created_by_id');
            """))
            columns = [row[0] for row in result]
            
            if 'created_by' in columns and 'created_by_id' not in columns:
                # Rename the column
                connection.execute(text("""
                    ALTER TABLE performance_objectives 
                    RENAME COLUMN created_by TO created_by_id;
                """))
            elif 'created_by' in columns and 'created_by_id' in columns:
                # Both exist, drop the old one (assuming created_by_id is the correct one)
                connection.execute(text("""
                    ALTER TABLE performance_objectives 
                    DROP COLUMN IF EXISTS created_by;
                """))
            
            connection.commit()
            
            logger.info(f"Added all missing columns to {db_name}")
            
            return {
                "status": "success",
                "message": f"Added all missing columns to {db_name}"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix columns for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix columns: {str(e)}"
        }


