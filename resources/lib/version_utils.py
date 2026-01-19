"""
Vanilla Python version comparison utility.
Supports version number extensions like ~rc03, -rc03, etc.
"""

import re
from typing import Union


class Version:
    """
    A version object that can be compared with other versions.
    Supports formats like: 1.2.3, 1.2.3~rc03, 1.2.3-rc03, 1.2.3_004
    """

    # Pre-release identifiers in order of precedence (lower = earlier)
    PRERELEASE_ORDER = {
        'alpha': 1,
        'a': 1,
        'beta': 2,
        'b': 2,
        'rc': 3,
        'pre': 4,
    }

    def __init__(self, version_string: str):
        self.original = version_string
        self.parts = []
        self.prerelease = None
        self.prerelease_num = 0
        self._parse(version_string)

    def _parse(self, version_string: str):
        """Parse version string into comparable components."""
        # Handle pre-release markers: ~, -, _
        # Examples: 1.2.3~rc4, 1.2.3-rc4, 1.2.3_004
        prerelease_pattern = r'([~\-_])(alpha|a|beta|b|rc|pre)?(\d+)?'
        match = re.search(prerelease_pattern, version_string, re.IGNORECASE)

        if match:
            separator = match.group(1)
            prerelease_type = match.group(2)
            prerelease_num = match.group(3)

            # Split at the separator
            base_version = version_string[:match.start()]

            # Determine prerelease type
            if prerelease_type:
                self.prerelease = prerelease_type.lower()
            else:
                # If no type specified (e.g., 1.2.3_004), treat as patch number
                self.prerelease = None

            # Store prerelease number
            if prerelease_num:
                self.prerelease_num = int(prerelease_num)
        else:
            base_version = version_string

        # Parse numeric parts
        # Remove any non-numeric/non-dot characters at the end
        base_version = re.sub(r'[^0-9.].*$', '', base_version)

        # Split by dots and convert to integers
        parts = base_version.split('.')
        for part in parts:
            if part:
                try:
                    self.parts.append(int(part))
                except ValueError:
                    # If we can't convert to int, try to extract leading digits
                    digit_match = re.match(r'(\d+)', part)
                    if digit_match:
                        self.parts.append(int(digit_match.group(1)))
                    else:
                        self.parts.append(0)

    def _compare(self, other: 'Version') -> int:
        """
        Compare this version to another.
        Returns: -1 if self < other, 0 if equal, 1 if self > other
        """
        # Compare numeric parts
        max_len = max(len(self.parts), len(other.parts))
        for i in range(max_len):
            self_part = self.parts[i] if i < len(self.parts) else 0
            other_part = other.parts[i] if i < len(other.parts) else 0

            if self_part < other_part:
                return -1
            elif self_part > other_part:
                return 1

        # If numeric parts are equal, compare prerelease status
        # No prerelease (stable) > prerelease
        if self.prerelease is None and other.prerelease is None:
            # Both stable, compare prerelease numbers (for underscore versions)
            if self.prerelease_num < other.prerelease_num:
                return -1
            elif self.prerelease_num > other.prerelease_num:
                return 1
            return 0

        if self.prerelease is None and other.prerelease is not None:
            return 1  # Stable > prerelease

        if self.prerelease is not None and other.prerelease is None:
            return -1  # Prerelease < stable

        # Both have prerelease, compare types
        self_pre_order = self.PRERELEASE_ORDER.get(self.prerelease, 99)
        other_pre_order = self.PRERELEASE_ORDER.get(other.prerelease, 99)

        if self_pre_order < other_pre_order:
            return -1
        elif self_pre_order > other_pre_order:
            return 1

        # Same prerelease type, compare numbers
        if self.prerelease_num < other.prerelease_num:
            return -1
        elif self.prerelease_num > other.prerelease_num:
            return 1

        return 0

    def __lt__(self, other: 'Version') -> bool:
        return self._compare(other) < 0

    def __le__(self, other: 'Version') -> bool:
        return self._compare(other) <= 0

    def __gt__(self, other: 'Version') -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: 'Version') -> bool:
        return self._compare(other) >= 0

    def __eq__(self, other: 'Version') -> bool:
        return self._compare(other) == 0

    def __ne__(self, other: 'Version') -> bool:
        return self._compare(other) != 0

    def __str__(self) -> str:
        return self.original

    def __repr__(self) -> str:
        return f"Version('{self.original}')"


def parse_version(version_string: str) -> Version:
    """Parse a version string into a Version object."""
    return Version(version_string)
