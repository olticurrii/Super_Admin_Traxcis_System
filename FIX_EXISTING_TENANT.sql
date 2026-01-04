-- SQL Script to Fix Existing Tenant Database (tenant_id: 4)
-- This adds the missing is_admin column to existing tenant databases

-- Step 1: Connect to your PostgreSQL server
-- Example: psql -U your_username -h your_host -d postgres

-- Step 2: Find the database name for tenant_id 4
-- Connect to super_admin_db_qvvv and run:
-- SELECT id, name, db_name, admin_email FROM tenants WHERE id = 4;

-- Step 3: Connect to the tenant database
-- Replace 'tenant_database_name' with the actual database name from step 2
-- \c tenant_database_name

-- Step 4: Check current schema
\d users

-- Step 5: Add is_admin column if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL;

-- Step 6: Set is_admin=true for admin users
UPDATE users 
SET is_admin = true 
WHERE role = 'admin' OR email = 'olti@example.com';

-- Step 7: Verify the fix
SELECT id, email, role, is_admin FROM users;

-- Expected output should show is_admin column with true for admin users

-- Step 8: Try logging in again - should work now!


