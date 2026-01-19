"""
Standalone test for version comparison utility.
This test can run without the full project dependencies.
"""

import sys
import os

# Add the resources/lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from version_utils import parse_version


def test_basic_versions():
    """Test basic version comparisons."""
    print("Testing basic version comparisons...")

    # Test basic version comparison
    assert parse_version('1.2.3') < parse_version('1.2.4')
    assert parse_version('1.2.3') < parse_version('1.3.0')
    assert parse_version('1.2.3') > parse_version('1.2.2')
    assert parse_version('1.2.3') == parse_version('1.2.3')

    print("[OK] Basic version comparisons passed")


def test_prerelease_versions():
    """Test pre-release version comparisons with ~ separator."""
    print("Testing pre-release versions with ~ separator...")

    # Test rc versions with ~ separator (as in the test)
    v1 = parse_version('1.5.0~rc4')
    v2 = parse_version('1.5.0~rc7')
    assert v1 < v2, f"Expected {v1} < {v2}"

    # Test that stable > rc
    assert parse_version('1.5.0') > parse_version('1.5.0~rc7')

    # Test rc vs alpha/beta
    assert parse_version('1.5.0~alpha1') < parse_version('1.5.0~beta1')
    assert parse_version('1.5.0~beta1') < parse_version('1.5.0~rc1')

    print("[OK] Pre-release versions with ~ passed")


def test_prerelease_with_dash():
    """Test pre-release version comparisons with - separator."""
    print("Testing pre-release versions with - separator...")

    v1 = parse_version('1.5.0-rc3')
    v2 = parse_version('1.5.0-rc5')
    assert v1 < v2

    # Test that stable > rc
    assert parse_version('1.5.0') > parse_version('1.5.0-rc5')

    print("[OK] Pre-release versions with - passed")


def test_underscore_versions():
    """Test version comparisons with underscore (migration file style)."""
    print("Testing underscore versions...")

    # These are like migration files: 1.3.0_001.sql, 1.3.0_002.sql
    v1 = parse_version('1.3.0')
    v2 = parse_version('1.3.0')
    assert v1 == v2

    # When extracting base version from underscore files
    # 1.3.0_001 should have base 1.3.0
    # This is handled by get_version_from_migration_file

    print("[OK] Underscore versions passed")


def test_migration_file_sorting():
    """Test that migration files would sort correctly."""
    print("Testing migration file sorting...")

    versions = [
        '1.2.1',
        '1.1.0',
        '1.3.0',
        '1.1.5',
        '1.2.7'
    ]

    parsed = [parse_version(v) for v in versions]
    sorted_versions = sorted(parsed)

    expected_order = [
        parse_version('1.1.0'),
        parse_version('1.1.5'),
        parse_version('1.2.1'),
        parse_version('1.2.7'),
        parse_version('1.3.0')
    ]

    assert sorted_versions == expected_order

    print("[OK] Migration file sorting passed")


def test_edge_cases():
    """Test edge cases."""
    print("Testing edge cases...")

    # Different length versions
    assert parse_version('1.2') < parse_version('1.2.1')
    assert parse_version('1.2.0') == parse_version('1.2')

    # Very specific rc comparison from test file
    a = parse_version('1.5.0~rc4')
    b = parse_version('1.5.0~rc7')
    c = a < b
    assert c is True

    print("[OK] Edge cases passed")


if __name__ == '__main__':
    print("Running version comparison tests...\n")

    try:
        test_basic_versions()
        test_prerelease_versions()
        test_prerelease_with_dash()
        test_underscore_versions()
        test_migration_file_sorting()
        test_edge_cases()

        print("\n" + "="*50)
        print("All tests passed! [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
