import os
import pkgutil
import importlib

# Get the current package name
package_name = __name__

# Dynamically import all modules in the current package
for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    module = importlib.import_module(f"{package_name}.{module_name}")
    globals().update(
        {name: cls for name, cls in module.__dict__.items() if isinstance(cls, type)}
    )

# Define __all__ to include all imported classes
__all__ = [name for name, cls in globals().items() if isinstance(cls, type)]
