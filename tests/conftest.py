"""
Pytest configuration and fixtures for fabric-launcher tests.
"""

import sys
from unittest.mock import MagicMock

# Mock fabric-cicd and sempy modules that aren't available in test environment
sys.modules["fabric_cicd"] = MagicMock()
sys.modules["fabric_cicd.constants"] = MagicMock()
sys.modules["fabric_cicd.fabric_item_factory"] = MagicMock()
sys.modules["fabric_cicd.fabric_workspace"] = MagicMock()
sys.modules["sempy"] = MagicMock()
sys.modules["sempy.fabric"] = MagicMock()
