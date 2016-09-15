__author__ = 'Peter Brittain'

try:
    from .version import version
except ImportError:
    # Someone is running straight from the GIT repo - dummy out the version
    version = "0.0.0"

__version__ = version
