"""
Version information for Snapchat Memory Fixer
"""

# Version info
VERSION = "1.0.1"
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 1

# Application name
APP_NAME = "Snapchat Memory Fixer"
APP_SHORT_NAME = "snapmemoryfixer"

# Build info (can be updated during build process)
BUILD_TYPE = "release"
BUILD_NUMBER = None  # Set during CI/CD builds

def get_version_string():
    """Get full version string."""
    if BUILD_NUMBER:
        return f"{VERSION}-b{BUILD_NUMBER}"
    return VERSION

def get_full_name():
    """Get full application name with version."""
    return f"{APP_NAME} v{get_version_string()}"

def get_filename_prefix():
    """Get filename prefix for releases."""
    return f"{APP_SHORT_NAME}-v{VERSION}"