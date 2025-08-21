"""
Test configuration for StringSmith tests.
"""

import sys
import os

# Add the parent directory to the Python path so we can import stringsmith
test_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.dirname(test_dir)
sys.path.insert(0, package_dir)