# Super Admin Service

A standalone FastAPI application for creating and managing tenant databases for a multi-tenant SaaS HRMS system.

## Overview

This service is **completely separate** from the HRMS application and is responsible for:

- ✅ Creating new PostgreSQL databases (tenants)
- ✅ Running HRMS Alembic migrations on each new tenant database
- ✅ Seeding an initial HRMS admin user into each tenant database
- ✅ Storing tenant connection information in a central `super_admin_db`
- ✅ Generating secure random passwords for tenant admins
- ✅ Returning the password **ONCE** (never stored permanently)
- ✅ **NEW:** Listing all tenant databases with details
- ✅ **NEW:** Search and filter tenants by name, email, database, status
- ✅ **NEW:** Enable/Disable tenants (soft disable without data loss)
- ✅ **NEW:** Delete tenant records with confirmation

## System Requirements

- Python 3.8+
- PostgreSQL 12+
- Access to the HRMS Alembic configuration file
- Node.js 18+ (for frontend, optional)

## Installation

1. **Clone or navigate to this repository:**
   ```bash
   cd Super_Admin_Traxcis_System
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure PostgreSQL is running and create the super_admin_db:**
   ```bash
   psql -U postgres -c "CREATE DATABASE super_admin_db;"
   ```

## Configuration

The application uses the following default configuration (defined in `app/config.py`):

- **PostgreSQL Server Admin URL:** `postgresql+psycopg2://postgres:Oc132456@localhost:5432/postgres`
- **Super Admin Database URL:** `postgresql+psycopg2://postgres:Oc132456@localhost:5432/super_admin_db`
- **HRMS Alembic Path:** `/Users/olti/Desktop/Projektet e oltit/HR/backend/alembic.ini`

You can override these settings by creating a `.env` file in the project root:

```env
POSTGRES_SERVER_URL=postgresql+psycopg2://user:password@host:port/postgres
POSTGRES_SUPER_ADMIN_URL=postgresql+psycopg2://user:password@host:port/super_admin_db
HRMS_ALEMBIC_INI_PATH=/path/to/hrms/backend/alembic.ini
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
```

## Database Setup

### Initialize Super Admin Database

Before running the application, you need to create and initialize the `super_admin_db`:

1. **Create the database:**
   ```bash
   psql -U postgres -c "CREATE DATABASE super_admin_db;"
   ```

2. **Run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

This will create the `tenants` table in the `super_admin_db` to store tenant metadata.

## Running the Application

### Backend (FastAPI)

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at:
- **API:** http://localhost:8001
- **Interactive Docs:** http://localhost:8001/docs
- **Alternative Docs:** http://localhost:8001/redoc

### Frontend (Next.js) - Optional

A modern React/Next.js admin dashboard is included in the `frontend/` directory.

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to http://localhost:3000

See `frontend/README.md` for detailed frontend documentation.

## API Endpoints

### Root Endpoint

**GET /**  
Returns service information.

**Response:**
```json
{
  "service": "super_admin_service"
}
```

### Health Check

**GET /health**  
Returns service health status.

**Response:**
```json
{
  "status": "healthy"
}
```

### Create Tenant

**POST /super-admin/create-tenant**

Creates a new tenant database, runs HRMS migrations, and seeds an initial admin user.

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "admin_email": "admin@acme.com"
}
```

**Response:**
```json
{
  "tenant_id": 1,
  "tenant_db": "tenant_acme_corporation_1699123456",
  "admin_email": "admin@acme.com",
  "initial_password": "Xk9#mP2$vL8@qR4"
}
```

**Important:** The `initial_password` is returned **only once** and is never stored in plaintext. Make sure to save it securely!

**Example using curl:**
```bash
curl -X POST "http://localhost:8001/super-admin/create-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "admin_email": "admin@acme.com"
  }'
```

### List Tenants ✨ NEW

**GET /super-admin/tenants**

Retrieves a list of all tenant databases with their details.

**Query Parameters:**
- `skip` (optional, default=0): Number of records to skip (pagination)
- `limit` (optional, default=100): Maximum number of records to return

**Response:**
```json
[
  {
    "id": 1,
    "name": "Acme Corporation",
    "db_name": "tenant_acme_corporation_1699123456",
    "db_host": "localhost",
    "db_port": "5432",
    "db_user": "postgres",
    "admin_email": "admin@acme.com",
    "status": "active",
    "created_at": "2025-12-07T10:30:00"
  }
]
```

**Example using curl:**
```bash
# Get all tenants
curl http://localhost:8001/super-admin/tenants

# Get tenants with pagination
curl "http://localhost:8001/super-admin/tenants?skip=0&limit=10"
```

### Delete Tenant ✨ NEW

**DELETE /super-admin/tenants/{tenant_id}**

Deletes a tenant record from the super_admin database.

**Important:** This only removes the tenant record. The actual PostgreSQL database is NOT automatically deleted for safety reasons.

**Path Parameters:**
- `tenant_id`: The ID of the tenant to delete

**Response:**
```json
{
  "message": "Tenant record deleted successfully",
  "tenant_id": 5,
  "db_name": "tenant_acme_corporation_1699123456",
  "note": "The PostgreSQL database was not automatically deleted. Manual cleanup may be required."
}
```

**Error Responses:**
- `404 NOT FOUND`: Tenant with the specified ID does not exist
- `500 INTERNAL SERVER ERROR`: Server error during deletion

**Example using curl:**
```bash
# Delete tenant with ID 5
curl -X DELETE http://localhost:8001/super-admin/tenants/5
```

### Toggle Tenant Status ✨ NEW

**PATCH /super-admin/tenants/{tenant_id}/toggle-status**

Toggles tenant status between 'active' and 'inactive'. This is a **soft disable** that prevents users from logging in without deleting any data.

**Path Parameters:**
- `tenant_id`: The ID of the tenant to toggle

**Response:**
```json
{
  "id": 5,
  "name": "Acme Corporation",
  "db_name": "tenant_acme_corporation_1699123456",
  "status": "inactive",
  "admin_email": "admin@acme.com",
  "db_host": "localhost",
  "db_port": "5432",
  "db_user": "postgres",
  "created_at": "2025-12-07T10:30:00"
}
```

**Key Features:**
- ✅ No data is deleted
- ✅ Database remains intact
- ✅ Instantly reversible
- ✅ Users cannot login when inactive (requires HRMS integration)

**Example using curl:**
```bash
# Toggle status (active → inactive or inactive → active)
curl -X PATCH http://localhost:8001/super-admin/tenants/5/toggle-status
```

## How Provisioning Works

When you call `/super-admin/create-tenant`, the service performs the following steps:

1. **Generate Database Name:** Creates a unique database name using the format:
   ```
   tenant_{name_lowercase}_{timestamp}
   ```

2. **Create Database:** Executes `CREATE DATABASE` on the PostgreSQL server.

3. **Run HRMS Migrations:** 
   - Loads the HRMS Alembic configuration from the specified path
   - Overrides the `sqlalchemy.url` with the new tenant database URL
   - Runs `alembic upgrade head` to apply all HRMS migrations

4. **Generate Admin Password:** Creates a secure random password (12+ characters with letters, digits, and symbols).

5. **Hash Password:** Uses bcrypt to hash the password.

6. **Seed Admin User:** 
   - Connects to the tenant database
   - Imports the HRMS User model (via `models_stub.py`)
   - Creates an admin user with:
     - `email`: The provided admin email
     - `hashed_password`: The bcrypt hashed password
     - `role`: "admin"
     - `is_active`: True

7. **Store Tenant Metadata:** Saves tenant information in `super_admin_db`:
   - Tenant name
   - Database name
   - Database connection details
   - Admin email
   - Status and creation timestamp

8. **Return Response:** Returns tenant ID, database name, admin email, and the **plaintext initial password** (shown only once).

## HRMS User Model Import

The service needs to import the HRMS User model to seed admin users. The import is handled by `app/hrms_provisioning/models_stub.py`.

**Important:** You may need to update `models_stub.py` to match your actual HRMS project structure. The file attempts common import patterns, but if your HRMS models are in a different location, update the import paths accordingly.

Current import attempts:
- `from app.models import User`
- `from models import User`
- `from app.database.models import User`

## Project Structure

```
super_admin_service/
│
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connections and session management
│   ├── security.py             # Password hashing utilities
│   ├── utils.py                # Utility functions
│   │
│   ├── superadmin/
│   │   ├── models.py           # SQLAlchemy models (Tenant)
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── router.py           # API routes
│   │   ├── service.py          # Business logic
│   │
│   ├── hrms_provisioning/
│       ├── database_creator.py # Database creation logic
│       ├── run_migrations.py   # HRMS migration runner
│       ├── seed_admin.py       # Admin user seeding
│       ├── models_stub.py      # HRMS User model importer
│
├── alembic_superadmin/
│   ├── env.py                  # Alembic environment config
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
│
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Security Considerations

1. **Passwords:** Initial admin passwords are generated securely using `secrets` module and are hashed with bcrypt before storage.

2. **Database Credentials:** The service uses PostgreSQL admin credentials to create databases. Ensure these credentials are kept secure.

3. **Password Return:** The initial password is returned only once in the API response and is never stored in plaintext. Make sure to save it securely when provisioning tenants.

4. **Environment Variables:** Use environment variables or `.env` files for sensitive configuration in production.

## Troubleshooting

### Database Creation Fails

- Ensure PostgreSQL is running
- Verify admin credentials are correct
- Check that the PostgreSQL user has `CREATEDB` privilege

### HRMS Migrations Fail

- Verify the HRMS Alembic path is correct
- Ensure the HRMS Alembic configuration file exists
- Check that all HRMS dependencies are available

### User Model Import Fails

- Update `app/hrms_provisioning/models_stub.py` to match your HRMS project structure
- Ensure the HRMS backend path is correct
- Verify the User model exists in the HRMS project

### Database Already Exists Error

- The service doesn't check for existing databases before creation
- Manually drop the database if needed: `DROP DATABASE tenant_name;`

## Development

### Running Alembic Migrations

To create a new migration for the super_admin_db:

```bash
alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:

```bash
alembic upgrade head
```

To rollback:

```bash
alembic downgrade -1
```

## License

This is a proprietary service for managing HRMS tenant databases.

## Support

For issues or questions, please contact the development team.

## New Features Documentation

For detailed documentation on the new features:

- **Tenant List Component**: See `TENANT_LIST_FEATURE.md` for information about the tenant listing interface
- **Search, Filter, and Delete**: See `SEARCH_FILTER_DELETE_GUIDE.md` for comprehensive guide on:
  - Search functionality across multiple fields
  - Status filtering (All/Active/Inactive)
  - Delete tenant records with confirmation
  - Database cleanup procedures
- **Enable/Disable Tenants**: See `ENABLE_DISABLE_FEATURE.md` for comprehensive guide on:
  - Safely disabling tenants without data loss
  - Toggle between active and inactive states
  - Visual indicators for disabled tenants
  - Implementing login blocking in HRMS

