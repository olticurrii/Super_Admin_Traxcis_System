"""Module for running HRMS Alembic migrations on tenant databases."""
# CRITICAL: Patch bcrypt BEFORE any imports that might use it
# This prevents the 72-byte password error during passlib initialization
try:
    import bcrypt as _bcrypt_module
    _original_hashpw = _bcrypt_module.hashpw
    
    def _safe_hashpw(password, salt):
        """Wrapper that truncates password to 72 bytes before hashing."""
        if isinstance(password, str):
            password = password.encode('utf-8')
        if len(password) > 72:
            password = password[:72]
        return _original_hashpw(password, salt)
    
    # Monkey-patch bcrypt.hashpw globally
    _bcrypt_module.hashpw = _safe_hashpw
    # Also patch it in the module's __dict__ if needed
    if hasattr(_bcrypt_module, '__dict__'):
        _bcrypt_module.__dict__['hashpw'] = _safe_hashpw
except ImportError:
    pass  # bcrypt not available, will fail later anyway

from alembic import command
from alembic.config import Config
from app.config import settings
import logging
import os
import sys

logger = logging.getLogger(__name__)


def run_hrms_migrations(db_url: str) -> None:
    """
    Run HRMS Alembic migrations on a tenant database.
    
    Args:
        db_url: Database URL for the tenant database
        
    Raises:
        Exception: If migrations fail
    """
    alembic_ini_path = settings.HRMS_ALEMBIC_INI_PATH
    
    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(
            f"HRMS Alembic configuration not found at: {alembic_ini_path}"
        )
    
    # Get the directory containing the alembic.ini file (HRMS backend directory)
    alembic_dir = os.path.dirname(os.path.abspath(alembic_ini_path))
    
    # IMPORTANT: Install stub for HRMS hashing module BEFORE adding HRMS to sys.path
    # This prevents bcrypt initialization issues when the hashing module is imported
    import types
    hashing_stub = types.ModuleType('app.core.hashing')
    hashing_stub.hash_password = lambda p: p  # Stub function
    hashing_stub.verify_password = lambda p, h: False  # Stub function
    hashing_stub.Hasher = type('Hasher', (), {
        'hash_password': staticmethod(lambda p: p),
        'verify_password': staticmethod(lambda p, h: False)
    })
    hashing_stub.pwd_context = None
    
    # Save original if it exists
    original_hashing_module = None
    if 'app.core.hashing' in sys.modules:
        original_hashing_module = sys.modules['app.core.hashing']
    
    # Install the stub BEFORE any HRMS modules are imported
    sys.modules['app.core.hashing'] = hashing_stub
    logger.info("Installed stub for app.core.hashing to prevent bcrypt initialization issues")
    
    # IMPORTANT: We need to temporarily remove our 'app' module from sys.modules
    # to avoid conflicts when importing HRMS's 'app' module
    # Save any existing app modules
    super_admin_app_modules = {k: v for k, v in sys.modules.items() if k.startswith('app.') and k != 'app.config'}
    
    # Remove our app modules temporarily (except app.config which we need)
    for module_name in list(super_admin_app_modules.keys()):
        if module_name != 'app.config':
            del sys.modules[module_name]
    
    # Add HRMS backend directory to Python path so imports work
    # This must be done before Alembic loads env.py which imports app.core
    # We need to add it at the beginning of sys.path to ensure it's found first
    if alembic_dir not in sys.path:
        sys.path.insert(0, alembic_dir)
        logger.info(f"Added HRMS backend directory to Python path: {alembic_dir}")
    
    # Also set PYTHONPATH environment variable as a fallback
    pythonpath = os.environ.get('PYTHONPATH', '')
    if alembic_dir not in pythonpath:
        if pythonpath:
            os.environ['PYTHONPATH'] = f"{alembic_dir}:{pythonpath}"
        else:
            os.environ['PYTHONPATH'] = alembic_dir
    
    # Verify app.core can be imported before proceeding
    # Change to HRMS directory to ensure relative imports work
    original_cwd = os.getcwd()
    try:
        os.chdir(alembic_dir)
        try:
            # Clear any cached app modules and import fresh
            if 'app' in sys.modules:
                del sys.modules['app']
            if 'app.core' in sys.modules:
                del sys.modules['app.core']
            
            import app.core
            logger.info("Successfully verified app.core import from HRMS backend")
        except ImportError as e:
            logger.error(f"Could not import app.core: {e}")
            logger.error(f"HRMS backend directory: {alembic_dir}")
            logger.error(f"Python path (first 3): {sys.path[:3]}")
            logger.error(f"Current working directory: {os.getcwd()}")
            raise ImportError(
                f"Cannot import app.core from HRMS backend. "
                f"Make sure the HRMS backend directory is correct: {alembic_dir}. "
                f"Error: {str(e)}"
            ) from e
    finally:
        os.chdir(original_cwd)
    
    try:
        # Load the HRMS Alembic configuration
        # Change to HRMS directory before loading config so env.py can find modules
        original_cwd = os.getcwd()
        os.chdir(alembic_dir)
        try:
            alembic_cfg = Config(alembic_ini_path)
        finally:
            os.chdir(original_cwd)
        
        # Override the sqlalchemy.url with the tenant database URL
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        # CRITICAL: The HRMS env.py uses settings.database_url from app.core.config
        # We need to set DATABASE_URL environment variable so settings can read it
        # Save original if it exists
        original_db_url_env = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = db_url
        logger.info(f"Set DATABASE_URL environment variable to: {db_url[:50]}...")
        
        # Set the script location to the absolute path of the alembic directory
        # This ensures Alembic can find the scripts folder even when run from a different directory
        script_location = alembic_cfg.get_main_option("script_location")
        if script_location and not os.path.isabs(script_location):
            # If script_location is relative, make it absolute based on alembic.ini location
            script_location = os.path.join(alembic_dir, script_location)
        elif not script_location:
            # Default to 'alembic' folder in the same directory as alembic.ini
            script_location = os.path.join(alembic_dir, "alembic")
        
        alembic_cfg.set_main_option("script_location", script_location)
        
        # Change to the HRMS backend directory before running migrations
        # This ensures env.py can resolve paths correctly
        original_cwd = os.getcwd()
        try:
            os.chdir(alembic_dir)
            
            # Run migrations up to head
            logger.info(f"Running HRMS migrations on database: {db_url}")
            logger.info(f"Working directory: {os.getcwd()}")
            logger.info(f"Script location: {script_location}")
            
            try:
                # Check current revision before upgrade
                try:
                    current_rev = command.current(alembic_cfg)
                    logger.info(f"Current database revision: {current_rev}")
                except Exception as e:
                    logger.info(f"No current revision (fresh database): {e}")
                
                # Check what revisions are available
                try:
                    history = list(command.history(alembic_cfg))
                    logger.info(f"Available migration revisions: {len(history)} total")
                    if history:
                        logger.info(f"First migration: {history[0].revision}")
                        logger.info(f"Last migration: {history[-1].revision}")
                except Exception as e:
                    logger.warning(f"Could not get migration history: {e}")
                
                # Check if this is a fresh database (no alembic_version table)
                from sqlalchemy import create_engine, inspect
                check_engine = create_engine(db_url)
                inspector = inspect(check_engine)
                existing_tables = inspector.get_table_names()
                is_fresh_db = 'alembic_version' not in existing_tables
                
                if is_fresh_db:
                    logger.info("Fresh database detected. The initial migration is empty, creating tables from Base.metadata first...")
                    try:
                        # Import HRMS Base and all models to register them
                        from app.core.database import Base
                        # Import all models to register them with Base.metadata
                        import app.models  # This will import all models from the models package
                        
                        # Create all tables from metadata
                        Base.metadata.create_all(bind=check_engine)
                        created_tables = inspector.get_table_names()
                        logger.info(f"Tables created from Base.metadata: {created_tables}")
                        
                        # Check if tenant_id column already exists (Base.metadata might include it)
                        # If it does, we need to stamp directly to head to skip the migration that adds it
                        users_table_columns = []
                        if 'users' in created_tables:
                            try:
                                users_table_columns = [col['name'] for col in inspector.get_columns('users')]
                            except Exception as e:
                                logger.warning(f"Could not get users table columns: {e}")
                        
                        has_tenant_id = 'tenant_id' in users_table_columns
                        logger.info(f"Users table columns: {users_table_columns}")
                        logger.info(f"tenant_id exists: {has_tenant_id}")
                        
                        if has_tenant_id:
                            logger.info("tenant_id column already exists in users table (from Base.metadata).")
                            logger.info("Stamping directly to head revision to skip the migration that adds tenant_id...")
                            # If tenant_id already exists, stamp directly to head (skip the migration that adds it)
                            try:
                                command.stamp(alembic_cfg, "head")
                                logger.info("HRMS migrations completed successfully (stamped to head, skipped tenant_id migration)")
                            except Exception as stamp_error:
                                logger.warning(f"Could not stamp to head: {stamp_error}")
                                # Try stamping to the specific revision that adds tenant_id
                                logger.info("Trying to stamp to c0ed1feb217a (add_tenant_id migration)...")
                                command.stamp(alembic_cfg, "c0ed1feb217a")
                                logger.info("Stamped to c0ed1feb217a successfully")
                        else:
                            # Stamp with the first (empty) migration
                            logger.info("Stamping database with initial migration (366f6da1e3be)...")
                            command.stamp(alembic_cfg, "366f6da1e3be")
                            
                            # Now run remaining migrations (like adding tenant_id)
                            logger.info("Running remaining migrations...")
                            try:
                                command.upgrade(alembic_cfg, "head")
                                logger.info("HRMS migrations completed successfully")
                            except Exception as upgrade_err:
                                error_str = str(upgrade_err)
                                # If the error is about tenant_id already existing, just stamp to head
                                if "tenant_id" in error_str.lower() and ("already exists" in error_str.lower() or "duplicate" in error_str.lower() or "duplicatecolumn" in error_str.lower()):
                                    logger.warning(f"Migration error (tenant_id already exists): {error_str}")
                                    logger.info("tenant_id already exists in schema, stamping to head instead...")
                                    try:
                                        command.stamp(alembic_cfg, "head")
                                        logger.info("Stamped to head successfully, skipping tenant_id migration")
                                    except Exception as stamp_err:
                                        # If head doesn't work, try the specific revision
                                        logger.info("Trying to stamp to c0ed1feb217a (add_tenant_id revision)...")
                                        command.stamp(alembic_cfg, "c0ed1feb217a")
                                        logger.info("Stamped to c0ed1feb217a successfully")
                                else:
                                    raise
                    except Exception as create_error:
                        logger.error(f"Failed to create tables: {create_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        raise
                else:
                    # Database has migrations, try upgrade
                    logger.info("Executing alembic upgrade head...")
                    try:
                        command.upgrade(alembic_cfg, "head")
                        logger.info("HRMS migrations completed successfully")
                    except Exception as upgrade_error:
                        error_str = str(upgrade_error)
                        # If tables don't exist, create them
                        if "does not exist" in error_str or "relation" in error_str.lower():
                            logger.warning(f"Upgrade failed: {error_str}")
                            logger.info("Creating tables from Base.metadata...")
                            from app.core.database import Base
                            # Import all models to register them
                            import app.models  # This will import all models from the models package
                            Base.metadata.create_all(bind=check_engine)
                            command.stamp(alembic_cfg, "366f6da1e3be")
                            command.upgrade(alembic_cfg, "head")
                            logger.info("Migrations completed after creating tables")
                        else:
                            raise
                
                # Verify that tables were created
                from sqlalchemy import create_engine, inspect
                verify_engine = create_engine(db_url)
                inspector = inspect(verify_engine)
                tables = inspector.get_table_names()
                logger.info(f"Tables created in database: {tables}")
                
                if not tables:
                    raise Exception(
                        "No tables were created after running migrations. "
                        "This suggests migrations may not have executed properly or the database is empty."
                    )
                
                if 'users' not in tables:
                    logger.warning("Users table not found after migrations. This may cause issues when seeding admin user.")
                    logger.warning(f"Available tables: {tables}")
                
            except Exception as migration_error:
                logger.error(f"Migration error: {str(migration_error)}")
                import traceback
                logger.error(traceback.format_exc())
                # Check what tables exist
                try:
                    from sqlalchemy import create_engine, inspect
                    verify_engine = create_engine(db_url)
                    inspector = inspect(verify_engine)
                    tables = inspector.get_table_names()
                    logger.error(f"Available tables after failed migration: {tables}")
                except Exception as e:
                    logger.error(f"Could not inspect database: {e}")
                raise
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        logger.error(f"Failed to run HRMS migrations: {str(e)}")
        raise
    finally:
        # Restore our app modules after migrations complete
        # Remove HRMS app modules
        hrms_app_modules = {k: v for k, v in sys.modules.items() if k.startswith('app.')}
        for module_name in list(hrms_app_modules.keys()):
            if module_name not in super_admin_app_modules:
                del sys.modules[module_name]
        
        # Restore our app modules
        sys.modules.update(super_admin_app_modules)
        
        # Restore HRMS hashing module if it was removed
        if original_hashing_module:
            sys.modules['app.core.hashing'] = original_hashing_module
        
        # Restore original DATABASE_URL environment variable
        if 'original_db_url_env' in locals():
            if original_db_url_env:
                os.environ['DATABASE_URL'] = original_db_url_env
            elif 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']
        
        # Remove HRMS backend from sys.path
        if alembic_dir in sys.path:
            sys.path.remove(alembic_dir)

