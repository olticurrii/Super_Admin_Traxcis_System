#!/usr/bin/env python3
"""
Safe script to delete all tenant databases and their records.

This script:
1. Lists all tenant databases from super_admin_db
2. Shows what will be deleted
3. Deletes only tenant databases (matching pattern tenant_*)
4. Removes tenant records from super_admin_db

IMPORTANT: This will NOT delete:
- System databases (postgres, template0, template1, etc.)
- super_admin_db
- Any database not matching the tenant_* pattern
- Any database not in the tenants table
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.superadmin.models import Tenant
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Protected databases that should NEVER be deleted
PROTECTED_DATABASES = {
    'postgres',
    'template0',
    'template1',
    'super_admin_db',
    'hr_management',  # HRMS main database
}


def get_all_databases():
    """Get list of all databases from PostgreSQL."""
    server_engine = create_engine(
        settings.POSTGRES_SERVER_URL,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True
    )
    
    with server_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false
            ORDER BY datname
        """))
        databases = [row[0] for row in result]
    
    return databases


def get_tenant_databases_from_table():
    """Get all tenant databases from super_admin_db.tenants table."""
    super_admin_engine = create_engine(
        settings.POSTGRES_SUPER_ADMIN_URL,
        pool_pre_ping=True
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=super_admin_engine)
    
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).all()
        tenant_db_names = {tenant.db_name: tenant for tenant in tenants}
        return tenant_db_names
    finally:
        db.close()


def delete_database(db_name: str):
    """Safely delete a database."""
    if db_name in PROTECTED_DATABASES:
        logger.error(f"❌ PROTECTED: Cannot delete {db_name} (protected database)")
        return False
    
    server_engine = create_engine(
        settings.POSTGRES_SERVER_URL,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True
    )
    
    try:
        with server_engine.connect() as conn:
            # Terminate all connections to the database first
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """))
            
            # Drop the database
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
            logger.info(f"✅ Deleted database: {db_name}")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to delete database {db_name}: {str(e)}")
        return False


def delete_tenant_records():
    """Delete all tenant records from super_admin_db."""
    super_admin_engine = create_engine(
        settings.POSTGRES_SUPER_ADMIN_URL,
        pool_pre_ping=True
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=super_admin_engine)
    
    db = SessionLocal()
    try:
        tenants = db.query(Tenant).all()
        count = len(tenants)
        
        for tenant in tenants:
            logger.info(f"  - Deleting tenant record: ID={tenant.id}, Name={tenant.name}, DB={tenant.db_name}")
            db.delete(tenant)
        
        db.commit()
        logger.info(f"✅ Deleted {count} tenant record(s) from super_admin_db")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete tenant records: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main function to safely delete all tenant databases."""
    print("=" * 70)
    print("SAFE TENANT DATABASE DELETION SCRIPT")
    print("=" * 70)
    print()
    
    # Step 1: Get all databases
    logger.info("📋 Step 1: Fetching all databases...")
    all_databases = get_all_databases()
    logger.info(f"   Found {len(all_databases)} total databases")
    
    # Step 2: Get tenant databases from super_admin_db
    logger.info("📋 Step 2: Fetching tenant records from super_admin_db...")
    tenant_records = get_tenant_databases_from_table()
    logger.info(f"   Found {len(tenant_records)} tenant record(s) in super_admin_db")
    
    # Step 3: Identify tenant databases to delete
    logger.info("📋 Step 3: Identifying tenant databases to delete...")
    tenant_databases_to_delete = []
    
    for db_name in all_databases:
        # Only delete if:
        # 1. It matches the tenant_* pattern
        # 2. It's in the tenants table
        # 3. It's not a protected database
        if (db_name.startswith('tenant_') and 
            db_name in tenant_records and 
            db_name not in PROTECTED_DATABASES):
            tenant_databases_to_delete.append(db_name)
    
    # Step 4: Show what will be deleted
    print()
    print("=" * 70)
    print("DATABASES TO BE DELETED:")
    print("=" * 70)
    
    if not tenant_databases_to_delete:
        print("✅ No tenant databases found to delete.")
        print("   All clean!")
        return
    
    for db_name in tenant_databases_to_delete:
        tenant = tenant_records[db_name]
        print(f"  - {db_name}")
        print(f"    Tenant ID: {tenant.id}")
        print(f"    Tenant Name: {tenant.name}")
        print(f"    Admin Email: {tenant.admin_email}")
        print()
    
    print(f"Total: {len(tenant_databases_to_delete)} database(s) will be deleted")
    print()
    
    # Step 5: Confirmation
    print("=" * 70)
    print("⚠️  WARNING: This action cannot be undone!")
    print("=" * 70)
    response = input("Type 'DELETE ALL TENANTS' to confirm: ")
    
    if response != "DELETE ALL TENANTS":
        print("❌ Deletion cancelled. No databases were deleted.")
        return
    
    print()
    print("=" * 70)
    print("DELETING TENANT DATABASES...")
    print("=" * 70)
    
    # Step 6: Delete databases
    deleted_count = 0
    failed_count = 0
    
    for db_name in tenant_databases_to_delete:
        if delete_database(db_name):
            deleted_count += 1
        else:
            failed_count += 1
    
    # Step 7: Delete tenant records
    print()
    logger.info("📋 Step 7: Deleting tenant records from super_admin_db...")
    try:
        records_deleted = delete_tenant_records()
    except Exception as e:
        logger.error(f"Failed to delete tenant records: {str(e)}")
        records_deleted = 0
    
    # Step 8: Summary
    print()
    print("=" * 70)
    print("DELETION SUMMARY")
    print("=" * 70)
    print(f"✅ Databases deleted: {deleted_count}")
    if failed_count > 0:
        print(f"❌ Databases failed: {failed_count}")
    print(f"✅ Tenant records deleted: {records_deleted}")
    print()
    print("✅ Cleanup complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

