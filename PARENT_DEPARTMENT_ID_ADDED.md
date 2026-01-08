# ✅ Parent Department ID Column Added to Tenant Schema

## 🎯 Issue Resolved

**Problem:** When creating new tenant databases, the `departments` table was missing the `parent_department_id` column that the HR application requires for hierarchical department structures.

**Solution:** Added `parent_department_id` column to all tenant schema creation files.

---

## 📝 Changes Made

### 1. Updated `app/superadmin/create_perfect_schema.py`

**File:** `/app/superadmin/create_perfect_schema.py` (Line 49-57)

**Before:**
```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    manager_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
```

**After:**
```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    manager_id INTEGER,
    parent_department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
CREATE INDEX idx_departments_parent_id ON departments(parent_department_id);
```

### 2. Updated `tenant_migrations/versions/initial_tenant_schema.py`

**File:** `tenant_migrations/versions/initial_tenant_schema.py` (Line 25-37)

**Changes:**
- ✅ Changed `parent_id` → `parent_department_id` (for consistency with HR app)
- ✅ Added foreign key constraint: `REFERENCES departments(id) ON DELETE SET NULL`
- ✅ Added index: `idx_departments_parent_id`

### 3. Updated `tenant_migrations/versions/complete_full_hrms_schema.py`

**File:** `tenant_migrations/versions/complete_full_hrms_schema.py` (Line 25-37)

**Changes:**
- ✅ Changed `parent_id` → `parent_department_id`
- ✅ Added foreign key constraint
- ✅ Added index

---

## 🏗️ Schema Structure

### Departments Table (Complete)

```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    manager_id INTEGER,
    parent_department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Indexes
CREATE INDEX ix_departments_id ON departments(id);
CREATE INDEX ix_departments_name ON departments(name);
CREATE INDEX idx_departments_parent_id ON departments(parent_department_id);
```

### Column Details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique department ID |
| `name` | VARCHAR | NOT NULL, UNIQUE | Department name |
| `description` | TEXT | NULL | Department description |
| `manager_id` | INTEGER | REFERENCES users(id) | Department manager |
| `parent_department_id` | INTEGER | REFERENCES departments(id) ON DELETE SET NULL | Parent department for hierarchy |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

---

## 🔧 How It Works

### Hierarchical Department Structure

```
Company
├── Engineering (parent_department_id = NULL)
│   ├── Frontend Team (parent_department_id = 1)
│   └── Backend Team (parent_department_id = 1)
├── Sales (parent_department_id = NULL)
│   ├── Inside Sales (parent_department_id = 2)
│   └── Field Sales (parent_department_id = 2)
└── HR (parent_department_id = NULL)
```

### Foreign Key Behavior

**`ON DELETE SET NULL`** means:
- If a parent department is deleted
- All child departments have their `parent_department_id` set to `NULL`
- Child departments are NOT deleted (they become top-level departments)

**Example:**
```sql
-- Before deletion
Department: Engineering (id=1, parent_department_id=NULL)
Department: Frontend (id=2, parent_department_id=1)

-- Delete Engineering
DELETE FROM departments WHERE id = 1;

-- After deletion
Department: Frontend (id=2, parent_department_id=NULL)  -- Now top-level
```

---

## 🚀 Deployment

### Step 1: Commit Changes

```bash
cd "/Users/olti/Desktop/Projektet e oltit/Super_Admin_Traxcis_System"

git add app/superadmin/create_perfect_schema.py
git add tenant_migrations/versions/initial_tenant_schema.py
git add tenant_migrations/versions/complete_full_hrms_schema.py
git add PARENT_DEPARTMENT_ID_ADDED.md

git commit -m "feat: Add parent_department_id column to departments table in tenant schema"
git push
```

### Step 2: Render Auto-Deploy

- ✅ Render will automatically detect the push
- ✅ Build and deploy (~2-3 minutes)
- ✅ New tenants will have the correct schema

### Step 3: Verify

Create a new tenant and check the schema:

```sql
-- Connect to the new tenant database
\c tenant_database_name

-- Check departments table structure
\d departments

-- You should see:
-- parent_department_id | integer | | | 
```

---

## 📊 Impact

### ✅ New Tenants (Created After Deploy)

- **Status:** ✅ Will have `parent_department_id` column automatically
- **Action Required:** None - works out of the box

### ⚠️ Existing Tenants (Created Before Deploy)

- **Status:** ⚠️ Missing `parent_department_id` column
- **Action Required:** Run migration script (see below)

---

## 🔧 Fix Existing Tenants

If you have existing tenant databases that need this column, run this SQL for each tenant:

```sql
-- Connect to the tenant database
\c tenant_database_name

-- Add parent_department_id column
ALTER TABLE departments 
ADD COLUMN parent_department_id INTEGER 
REFERENCES departments(id) ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX idx_departments_parent_id 
ON departments(parent_department_id);

-- Verify
\d departments
```

### Automated Fix Script

Or use this Python script to fix all existing tenants:

```python
from sqlalchemy import create_engine, text
from app.superadmin.service import list_tenants
from app.database import get_super_admin_db

def fix_existing_tenants():
    """Add parent_department_id to all existing tenant databases."""
    db = next(get_super_admin_db())
    tenants = list_tenants(db, skip=0, limit=1000)
    
    for tenant in tenants:
        print(f"Fixing tenant: {tenant.name} (DB: {tenant.db_name})")
        
        db_url = f"postgresql+psycopg2://{tenant.db_user}:{tenant.db_password}@{tenant.db_host}:{tenant.db_port}/{tenant.db_name}"
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'departments' 
                AND column_name = 'parent_department_id'
            """))
            
            if not result.fetchone():
                print(f"  Adding parent_department_id column...")
                
                # Add column
                conn.execute(text("""
                    ALTER TABLE departments 
                    ADD COLUMN parent_department_id INTEGER 
                    REFERENCES departments(id) ON DELETE SET NULL
                """))
                
                # Add index
                conn.execute(text("""
                    CREATE INDEX idx_departments_parent_id 
                    ON departments(parent_department_id)
                """))
                
                conn.commit()
                print(f"  ✅ Fixed!")
            else:
                print(f"  ✅ Already has column")

if __name__ == "__main__":
    fix_existing_tenants()
```

---

## ✅ Verification Checklist

After deployment:

- [ ] Commit and push changes to GitHub
- [ ] Wait for Render to deploy (~2-3 minutes)
- [ ] Create a new test tenant
- [ ] Verify `departments` table has `parent_department_id` column
- [ ] Test creating hierarchical departments in HR app
- [ ] (Optional) Fix existing tenants using migration script

---

## 📋 Files Modified

1. ✅ `app/superadmin/create_perfect_schema.py` - Main schema creation
2. ✅ `tenant_migrations/versions/initial_tenant_schema.py` - Migration file
3. ✅ `tenant_migrations/versions/complete_full_hrms_schema.py` - Complete schema migration
4. ✅ `PARENT_DEPARTMENT_ID_ADDED.md` - This documentation

---

## 🎯 Summary

**What was added:**
- ✅ `parent_department_id` column to `departments` table
- ✅ Foreign key constraint: `REFERENCES departments(id) ON DELETE SET NULL`
- ✅ Index: `idx_departments_parent_id` for performance

**Who is affected:**
- ✅ **New tenants:** Automatically have the column
- ⚠️ **Existing tenants:** Need manual migration (see above)

**Next steps:**
1. Commit and push to GitHub
2. Wait for Render auto-deploy
3. Test with a new tenant
4. (Optional) Fix existing tenants

---

**Status:** ✅ Ready to deploy!

