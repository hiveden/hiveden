import logging
from hiveden.db.session import get_db_manager
from hiveden.db.repositories.core import ConfigRepository, ModuleRepository
from hiveden.config.settings import config

logger = logging.getLogger(__name__)

def get_system_domain_value() -> str:
    """Get the effective system domain (DB > Env)."""
    db_manager = get_db_manager()
    module_repo = ModuleRepository(db_manager)
    config_repo = ConfigRepository(db_manager)
    
    # Try DB
    try:
        core_module = module_repo.get_by_short_name('core')
        if core_module:
            cfg = config_repo.get_by_module_and_key(core_module.id, 'domain')
            if cfg:
                return cfg['value']
    except Exception as e:
        logger.warning(f"Failed to fetch domain from DB: {e}")
        
    # Fallback
    return config.domain
