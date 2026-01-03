-- IMMEDIATE FIX: Add is_admin column to ALL existing tenant databases
-- Run this directly on your PostgreSQL server

-- Step 1: Connect to your PostgreSQL server
-- psql postgresql://olticurri:84SuVnkW0msge8tAYGD7UhEKanOQDegC@dpg-d55fjm0gjchc738eo1og-a/postgres

-- Step 2: Get list of all tenant databases
-- \c super_admin_db_qvvv
-- SELECT id, db_name FROM tenants WHERE status = 'active';

-- Step 3: For EACH tenant database in the list above, run this:
-- Replace 'TENANT_DB_NAME' with actual database name from step 2

-- Connect to first tenant database
\c TENANT_DB_NAME_HERE

-- Add is_admin column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL;

-- Update all admin users to have is_admin = true
UPDATE users SET is_admin = true WHERE role = 'admin';

-- Verify the fix
SELECT id, email, role, is_admin FROM users;

-- Repeat for each tenant database from step 2
-- \c next_tenant_db_name
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false NOT NULL;
-- UPDATE users SET is_admin = true WHERE role = 'admin';
-- SELECT id, email, role, is_admin FROM users;

