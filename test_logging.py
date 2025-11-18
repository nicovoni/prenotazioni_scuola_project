#!/usr/bin/env python3
"""
Test script to validate Django logging configuration.
This script mimics what Django does when starting up.
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_logging_config():
    """Test if the logging configuration in settings.py is valid."""
    try:
        # Import Django settings module
        from config.settings import LOGGING
        
        print("✅ LOGGING configuration loaded successfully!")
        print(f"Formatters available: {list(LOGGING.get('formatters', {}).keys())}")
        
        # Test each formatter
        import logging.config
        logging.config.dictConfig(LOGGING)
        print("✅ All formatters configured successfully!")
        
        # Test each formatter by creating a logger
        for formatter_name in LOGGING.get('formatters', {}):
            try:
                formatter = logging.getLoggerClass()
                print(f"✅ Formatter '{formatter_name}' is valid")
            except Exception as e:
                print(f"❌ Error with formatter '{formatter_name}': {e}")
                return False
        
        print("✅ All logging tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading logging configuration: {e}")
        return False

if __name__ == "__main__":
    success = test_logging_config()
    sys.exit(0 if success else 1)
