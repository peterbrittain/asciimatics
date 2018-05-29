"""
Asciimatics is a package to help people create full-screen text UIs (from interactive forms to
ASCII animations) on any platform.  It is licensed under the Apache Software Foundation License 2.0.
"""
__author__ = 'Peter Brittain'

try:
    from .version import version
except ImportError:
    # Someone is running straight from the GIT repo - dummy out the version
    version = "0.0.0"

__version__ = version
