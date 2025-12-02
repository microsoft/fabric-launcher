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


# Create a minimal pandas mock with DataFrame support
class MockRow(dict):
    """Row that supports both dict-style and attribute-style access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No attribute '{name}'") from None


class MockDataFrame:
    """Minimal DataFrame mock for testing."""

    def __init__(self, data=None):
        self._data = data or {}
        self._empty = len(self._data) == 0 or (
            isinstance(self._data, dict) and all(len(v) == 0 for v in self._data.values())
        )

    @property
    def empty(self):
        return self._empty

    def __len__(self):
        if self._data and isinstance(self._data, dict):
            first_col = next(iter(self._data.values()), [])
            return len(first_col)
        return 0

    def __getitem__(self, key):
        if isinstance(key, str):
            if isinstance(self._data, dict) and key in self._data:
                return self._data[key]
            raise KeyError(key)
        # Boolean indexing - return filtered DataFrame
        if hasattr(key, "__iter__"):
            return self._filter_by_mask(key)
        raise KeyError(key)

    def _filter_by_mask(self, mask):
        """Filter DataFrame by boolean mask."""
        if not self._data:
            return MockDataFrame({})

        # Convert mask to list if needed
        mask_list = list(mask) if hasattr(mask, "__iter__") else [mask]

        new_data = {}
        for col, values in self._data.items():
            new_data[col] = [v for v, m in zip(values, mask_list) if m]

        return MockDataFrame(new_data)

    def iterrows(self):
        if not self._data or self._empty:
            return iter([])
        length = len(next(iter(self._data.values())))
        for i in range(length):
            row = MockRow({k: v[i] for k, v in self._data.items()})
            yield i, row

    def groupby(self, key):
        return MockGroupBy(self._data, key)


class MockGroupBy:
    """Mock for pandas groupby."""

    def __init__(self, data, key):
        self._data = data
        self._key = key

    def size(self):
        return MockSeries(self._data, self._key)


class MockSeries:
    """Mock for pandas Series."""

    def __init__(self, data, key):
        self._data = data
        self._key = key

    def to_dict(self):
        if not self._data or self._key not in self._data:
            return {}
        # Count occurrences of each value
        from collections import Counter

        return dict(Counter(self._data[self._key]))


class MockPandas:
    """Mock pandas module."""

    @staticmethod
    def dataframe(data=None):  # noqa: N802 - matches pandas.DataFrame API
        return MockDataFrame(data)


# Create instance and add DataFrame attribute to match pandas API
_mock_pandas = MockPandas()
_mock_pandas.DataFrame = MockDataFrame  # Allow both pandas.DataFrame() and direct call


# Add pandas to sys.modules
sys.modules["pandas"] = _mock_pandas
