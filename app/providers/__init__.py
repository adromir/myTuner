import os
import sys
import pkgutil
import importlib
import importlib.util
import inspect
from typing import Dict, Type, List
from .base import MediaProvider
import logging

logger = logging.getLogger("mytuner")

_providers: Dict[str, MediaProvider] = {}

def register_provider(provider_class: Type[MediaProvider]):
    """Registers a provider class if it has a valid id."""
    try:
        # We must instantiate the provider to get its id
        # Note: All providers must have a parameterless constructor.
        instance = provider_class()
        pid = instance.id
        if pid:
            _providers[pid] = instance
            logger.info(f"Registered provider: {pid} ({provider_class.__name__})")
    except Exception as e:
        logger.error(f"Failed to register provider {provider_class.__name__}: {e}")

def discover_built_in_providers():
    """Discover providers inside the app.providers package."""
    package_name = __name__
    package_dir = os.path.dirname(__file__)
    
    # Recursively find all modules in the providers directory
    for root, dirs, files in os.walk(package_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_path = os.path.join(root, file)
                rel_path = os.path.relpath(module_path, package_dir)
                module_name = package_name + "." + rel_path.replace(os.path.sep, ".")[:-3]
                
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, MediaProvider) and obj is not MediaProvider:
                            # Avoid registering imported classes from other modules
                            if obj.__module__ == module_name:
                                register_provider(obj)
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")

def discover_external_plugins():
    """Discover providers inside the /plugins directory in the project root."""
    plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "plugins"))
    
    os.makedirs(plugins_dir, exist_ok=True)
        
    for file in os.listdir(plugins_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = file[:-3]
            file_path = os.path.join(plugins_dir, file)
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, MediaProvider) and obj is not MediaProvider:
                        if obj.__module__ == module_name:
                            register_provider(obj)
            except Exception as e:
                logger.error(f"Failed to load external plugin {file}: {e}")

# Initialize discovery
discover_built_in_providers()
discover_external_plugins()

def get_provider(name: str) -> MediaProvider:
    return _providers.get(name)

def get_all_providers() -> List[MediaProvider]:
    return list(_providers.values())
