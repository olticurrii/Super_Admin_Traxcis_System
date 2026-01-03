"""Utility to fix schema for existing tenant databases - COMPLETE VERSION."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_tenant_schema(db_name: str, tenant_id: int) -> dict:
    """
    Add ALL missing columns and tables to an existing tenant database.
    
    Args:
        db_name: Name of the tenant database to fix
        tenant_id: The Super Admin tenant ID this database belongs to
        
    Returns:
        dict with status and message
    """
    try:
        # Construct database URL for the tenant
        db_url = f"{settings.POSTGRES_SERVER_URL.rsplit('/', 1)[0]}/{db_name}"
        db_url = db_url.replace('/postgres', f'/{db_name}')
        
        # Create engine
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as connection:
            # Check if users table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                return {
                    "status": "error",
                    "message": f"Users table does not exist in {db_name}"
                }
            
            # Add ALL missing columns to users table
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL,
                ADD COLUMN IF NOT EXISTS job_role VARCHAR,
                ADD COLUMN IF NOT EXISTS department_id INTEGER,
                ADD COLUMN IF NOT EXISTS manager_id INTEGER,
                ADD COLUMN IF NOT EXISTS avatar_url VARCHAR,
                ADD COLUMN IF NOT EXISTS phone VARCHAR,
                ADD COLUMN IF NOT EXISTS hire_date DATE,
                ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'UTC',
                ADD COLUMN IF NOT EXISTS locale VARCHAR DEFAULT 'en',
                ADD COLUMN IF NOT EXISTS theme VARCHAR DEFAULT 'light',
                ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT true NOT NULL;
            """))
            
            # Update admin users with correct tenant_id
            result = connection.execute(
                text("""
                    UPDATE users 
                    SET is_admin = true,
                        tenant_id = COALESCE(tenant_id, :tenant_id),
                        timezone = COALESCE(timezone, 'UTC'),
                        locale = COALESCE(locale, 'en'),
                        theme = COALESCE(theme, 'light'),
                        email_notifications = COALESCE(email_notifications, true)
                    WHERE role = 'admin';
                """),
                {"tenant_id": tenant_id}
            )
            updated_count = result.rowcount
            
            # Create ALL missing tables
            
            # Settings table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR NOT NULL UNIQUE,
                    value VARCHAR,
                    description VARCHAR,
                    category VARCHAR,
                    data_type VARCHAR DEFAULT 'string' NOT NULL,
                    is_public BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_settings_id ON settings(id);
                CREATE UNIQUE INDEX IF NOT EXISTS ix_settings_key ON settings(key);
            """))
            
            # Roles table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    description VARCHAR,
                    is_system BOOLEAN DEFAULT false NOT NULL,
                    permissions JSON,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_roles_id ON roles(id);
            """))
            
            # Resources table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS resources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    resource_type VARCHAR NOT NULL,
                    description VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_resources_id ON resources(id);
            """))
            
            # Permissions table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id SERIAL PRIMARY KEY,
                    role VARCHAR NOT NULL,
                    resource VARCHAR NOT NULL,
                    action VARCHAR NOT NULL,
                    granted BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_permissions_id ON permissions(id);
            """))
            
            # Feedback table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    type VARCHAR NOT NULL,
                    title VARCHAR,
                    content VARCHAR NOT NULL,
                    sentiment VARCHAR,
                    sentiment_score FLOAT,
                    keywords JSON,
                    category VARCHAR,
                    status VARCHAR DEFAULT 'pending' NOT NULL,
                    response VARCHAR,
                    responded_by INTEGER REFERENCES users(id),
                    responded_at TIMESTAMP,
                    is_anonymous BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_feedback_id ON feedback(id);
            """))
            
            # Time entries table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS time_entries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    clock_in TIMESTAMP NOT NULL,
                    clock_out TIMESTAMP,
                    duration INTEGER,
                    notes VARCHAR,
                    task_id INTEGER REFERENCES tasks(id),
                    project_id INTEGER REFERENCES projects(id),
                    location VARCHAR,
                    is_approved BOOLEAN DEFAULT false NOT NULL,
                    approved_by INTEGER REFERENCES users(id),
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_time_entries_id ON time_entries(id);
            """))
            
            # Notifications table (if not exists)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    message VARCHAR,
                    data JSON,
                    is_read BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    read_at TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications(id);
            """))
            
            # Projects table (if not exists)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_projects_id ON projects(id);
            """))
            
            # Tasks table (if not exists)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    status VARCHAR DEFAULT 'todo' NOT NULL,
                    priority VARCHAR DEFAULT 'medium' NOT NULL,
                    assignee_id INTEGER REFERENCES users(id),
                    assignee VARCHAR,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    project_id INTEGER REFERENCES projects(id),
                    position INTEGER DEFAULT 0 NOT NULL,
                    due_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    is_private BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_tasks_id ON tasks(id);
            """))
            
            # Announcements table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    content VARCHAR NOT NULL,
                    author_id INTEGER NOT NULL REFERENCES users(id),
                    priority VARCHAR DEFAULT 'normal' NOT NULL,
                    is_published BOOLEAN DEFAULT false NOT NULL,
                    published_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_announcements_id ON announcements(id);
            """))
            
            # Performance reviews table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS performance_reviews (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id),
                    reviewer_id INTEGER NOT NULL REFERENCES users(id),
                    review_period_start DATE NOT NULL,
                    review_period_end DATE NOT NULL,
                    rating INTEGER,
                    comments VARCHAR,
                    goals JSON,
                    achievements JSON,
                    areas_of_improvement JSON,
                    status VARCHAR DEFAULT 'draft' NOT NULL,
                    submitted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_performance_reviews_id ON performance_reviews(id);
            """))
            
            # Payroll table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS payroll (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id),
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    base_salary NUMERIC(10,2) NOT NULL,
                    bonuses NUMERIC(10,2) DEFAULT 0 NOT NULL,
                    deductions NUMERIC(10,2) DEFAULT 0 NOT NULL,
                    net_salary NUMERIC(10,2) NOT NULL,
                    status VARCHAR DEFAULT 'pending' NOT NULL,
                    paid_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_payroll_id ON payroll(id);
            """))
            
            # Documents table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    file_type VARCHAR,
                    file_size INTEGER,
                    uploaded_by INTEGER NOT NULL REFERENCES users(id),
                    employee_id INTEGER REFERENCES employees(id),
                    category VARCHAR,
                    is_confidential BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_documents_id ON documents(id);
            """))
            
            # Audit logs table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    action VARCHAR NOT NULL,
                    resource_type VARCHAR,
                    resource_id INTEGER,
                    changes JSON,
                    ip_address VARCHAR,
                    user_agent VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs(id);
            """))
            
            connection.commit()
            
            logger.info(f"Added ALL missing tables and columns to {db_name}, updated {updated_count} admin users")
            
            return {
                "status": "success",
                "message": f"Added ALL missing tables and columns to {db_name}, updated {updated_count} admin users"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix schema for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix schema: {str(e)}"
        }
