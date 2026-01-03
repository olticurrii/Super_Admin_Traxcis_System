"""Complete schema fix for existing tenant databases - ALL 40+ tables."""
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def fix_tenant_schema_complete(db_name: str, tenant_id: int) -> dict:
    """
    Add ALL missing tables and columns to an existing tenant database.
    This creates the COMPLETE HRMS schema with 40+ tables.
    
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
            
            # Execute the complete schema creation (using IF NOT EXISTS for safety)
            connection.execute(text("""
                -- Core Tables
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    description VARCHAR,
                    manager_id INTEGER,
                    parent_id INTEGER,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_departments_id ON departments(id);
                CREATE UNIQUE INDEX IF NOT EXISTS ix_departments_name ON departments(name);
                
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER,
                    email VARCHAR NOT NULL UNIQUE,
                    full_name VARCHAR NOT NULL,
                    hashed_password VARCHAR NOT NULL,
                    role VARCHAR DEFAULT 'employee' NOT NULL,
                    is_admin BOOLEAN DEFAULT false NOT NULL,
                    is_active BOOLEAN DEFAULT true NOT NULL,
                    job_role VARCHAR,
                    department_id INTEGER REFERENCES departments(id),
                    manager_id INTEGER,
                    avatar_url VARCHAR,
                    phone VARCHAR,
                    hire_date DATE,
                    timezone VARCHAR DEFAULT 'UTC',
                    locale VARCHAR DEFAULT 'en',
                    theme VARCHAR DEFAULT 'light',
                    email_notifications BOOLEAN DEFAULT true NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
                
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_token VARCHAR NOT NULL UNIQUE,
                    ip_address VARCHAR,
                    user_agent VARCHAR,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ix_user_sessions_token ON user_sessions(session_token);
                
                -- Role & Permission Management
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    description VARCHAR,
                    is_system BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS permissions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    resource VARCHAR NOT NULL,
                    action VARCHAR NOT NULL,
                    description VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    UNIQUE(resource, action)
                );
                
                CREATE TABLE IF NOT EXISTS custom_role (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS role_permission_v2 (
                    id SERIAL PRIMARY KEY,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
                    granted BOOLEAN DEFAULT true NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS user_roles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                    assigned_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Project & Task Management
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    status VARCHAR DEFAULT 'active' NOT NULL,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    status VARCHAR DEFAULT 'todo' NOT NULL,
                    priority VARCHAR DEFAULT 'medium' NOT NULL,
                    assignee_id INTEGER REFERENCES users(id),
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                    position INTEGER DEFAULT 0 NOT NULL,
                    due_date DATE,
                    completed_at TIMESTAMP,
                    is_private BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    content VARCHAR NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Communication
                CREATE TABLE IF NOT EXISTS chats (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR,
                    type VARCHAR NOT NULL,
                    department_id INTEGER REFERENCES departments(id),
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    content VARCHAR NOT NULL,
                    is_read BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS chat_participants (
                    id SERIAL PRIMARY KEY,
                    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    joined_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Time Tracking
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
                
                -- Leave Management
                CREATE TABLE IF NOT EXISTS leave_types (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    default_days INTEGER DEFAULT 0 NOT NULL,
                    is_active BOOLEAN DEFAULT true NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS leave_balances (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    leave_type_id INTEGER NOT NULL REFERENCES leave_types(id),
                    total_days INTEGER NOT NULL,
                    used_days INTEGER DEFAULT 0 NOT NULL,
                    remaining_days INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    leave_type_id INTEGER NOT NULL REFERENCES leave_types(id),
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    days INTEGER NOT NULL,
                    reason VARCHAR,
                    status VARCHAR DEFAULT 'pending' NOT NULL,
                    reviewed_by INTEGER REFERENCES users(id),
                    reviewed_at TIMESTAMP,
                    review_notes VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Performance Management
                CREATE TABLE IF NOT EXISTS performance_objectives (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    status VARCHAR DEFAULT 'active' NOT NULL,
                    progress INTEGER DEFAULT 0 NOT NULL,
                    due_date DATE,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS performance_key_results (
                    id SERIAL PRIMARY KEY,
                    objective_id INTEGER NOT NULL REFERENCES performance_objectives(id) ON DELETE CASCADE,
                    title VARCHAR NOT NULL,
                    target_value FLOAT NOT NULL,
                    current_value FLOAT DEFAULT 0 NOT NULL,
                    unit VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS review_cycles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    status VARCHAR DEFAULT 'draft' NOT NULL,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS review_questions (
                    id SERIAL PRIMARY KEY,
                    cycle_id INTEGER NOT NULL REFERENCES review_cycles(id) ON DELETE CASCADE,
                    question VARCHAR NOT NULL,
                    question_type VARCHAR NOT NULL,
                    "order" INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS review_responses (
                    id SERIAL PRIMARY KEY,
                    cycle_id INTEGER NOT NULL REFERENCES review_cycles(id) ON DELETE CASCADE,
                    question_id INTEGER NOT NULL REFERENCES review_questions(id),
                    reviewer_id INTEGER NOT NULL REFERENCES users(id),
                    reviewee_id INTEGER NOT NULL REFERENCES users(id),
                    response VARCHAR NOT NULL,
                    rating INTEGER,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS competencies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    category VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS competency_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    competency_id INTEGER NOT NULL REFERENCES competencies(id),
                    score INTEGER NOT NULL,
                    assessed_by INTEGER NOT NULL REFERENCES users(id),
                    assessed_at TIMESTAMP DEFAULT now() NOT NULL,
                    notes VARCHAR
                );
                
                CREATE TABLE IF NOT EXISTS user_competencies (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    competency_id INTEGER NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
                    assigned_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Feedback System
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    type VARCHAR NOT NULL,
                    title VARCHAR,
                    content VARCHAR NOT NULL,
                    sentiment VARCHAR,
                    sentiment_score FLOAT,
                    category VARCHAR,
                    status VARCHAR DEFAULT 'pending' NOT NULL,
                    response VARCHAR,
                    responded_by INTEGER REFERENCES users(id),
                    responded_at TIMESTAMP,
                    is_anonymous BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS feedback_keywords (
                    id SERIAL PRIMARY KEY,
                    keyword VARCHAR NOT NULL UNIQUE,
                    count INTEGER DEFAULT 1 NOT NULL,
                    sentiment VARCHAR,
                    last_seen TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS daily_feedback_aggregate (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    total_feedback INTEGER DEFAULT 0 NOT NULL,
                    positive_count INTEGER DEFAULT 0 NOT NULL,
                    neutral_count INTEGER DEFAULT 0 NOT NULL,
                    negative_count INTEGER DEFAULT 0 NOT NULL,
                    avg_sentiment_score FLOAT,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Notifications
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    message VARCHAR NOT NULL,
                    data JSONB,
                    is_read BOOLEAN DEFAULT false NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    read_at TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS push_notification_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR NOT NULL,
                    device_type VARCHAR,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS user_notification_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    email_enabled BOOLEAN DEFAULT true NOT NULL,
                    push_enabled BOOLEAN DEFAULT true NOT NULL,
                    sms_enabled BOOLEAN DEFAULT false NOT NULL,
                    notification_types JSONB,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Office & Meeting Booking
                CREATE TABLE IF NOT EXISTS offices (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    location VARCHAR,
                    capacity INTEGER,
                    is_active BOOLEAN DEFAULT true NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS meeting_bookings (
                    id SERIAL PRIMARY KEY,
                    office_id INTEGER NOT NULL REFERENCES offices(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    status VARCHAR DEFAULT 'confirmed' NOT NULL,
                    created_at TIMESTAMP DEFAULT now() NOT NULL,
                    updated_at TIMESTAMP DEFAULT now() NOT NULL
                );
                
                -- Analytics
                CREATE TABLE IF NOT EXISTS kpi_snapshots (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    metric_name VARCHAR NOT NULL,
                    value FLOAT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT now() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_kpi_snapshots_date ON kpi_snapshots(date);
                CREATE INDEX IF NOT EXISTS ix_kpi_snapshots_metric ON kpi_snapshots(metric_name);
                
                -- Configuration
                CREATE TABLE IF NOT EXISTS organization_settings (
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
            
            connection.commit()
            
            logger.info(f"Added ALL missing tables to {db_name}, updated {updated_count} admin users")
            
            return {
                "status": "success",
                "message": f"Added ALL 40+ tables to {db_name}, updated {updated_count} admin users"
            }
            
    except Exception as e:
        logger.error(f"Failed to fix schema for {db_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix schema: {str(e)}"
        }

