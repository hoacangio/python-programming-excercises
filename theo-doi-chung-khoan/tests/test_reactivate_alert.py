"""
Tests for reactivate_price_alert functionality.

Test cases:
- Successfully reactivate an inactive alert that belongs to the user
- Reject reactivation if alert doesn't belong to the user (security)
- Reject reactivation if alert_id doesn't exist
- Verify that reactivated alert is active in the database
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories import alert_repository, user_repository
from services import alert_service
from database import get_db_connection


def setup_test_db():
    """Create a test database with sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM price_alerts")
    cursor.execute("DELETE FROM users")
    conn.commit()
    
    # Create test users
    cursor.execute("""
        INSERT INTO users (username, telegram_chat_id)
        VALUES (?, ?)
    """, ("test_user_1", "123456789"))
    user_id_1 = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO users (username, telegram_chat_id)
        VALUES (?, ?)
    """, ("test_user_2", "987654321"))
    user_id_2 = cursor.lastrowid
    
    conn.commit()
    
    return conn, user_id_1, user_id_2


def test_reactivate_own_alert():
    """Test: User can reactivate their own inactive alert."""
    print("\n📝 Test 1: Reactivate own inactive alert")
    
    conn, user_id_1, user_id_2 = setup_test_db()
    cursor = conn.cursor()
    
    # Create an alert for user_1
    cursor.execute("""
        INSERT INTO price_alerts (user_id, symbol, target_price, condition, alert_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_1, "VNM", 85000, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT", 1))
    alert_id = cursor.lastrowid
    conn.commit()
    
    # Deactivate it
    alert_repository.deactivate_price_alert(alert_id)
    
    # Verify it's inactive
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 0, "Alert should be inactive"
    print("  ✓ Alert deactivated successfully")
    
    # Reactivate it via service
    try:
        alert_service.reactivate_price_alert(alert_id, user_id_1)
        print("  ✓ Reactivation call succeeded")
    except Exception as e:
        print(f"  ✗ Reactivation failed: {e}")
        conn.close()
        return False
    
    # Verify it's now active
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 1, "Alert should be active after reactivation"
    print("  ✓ Alert is now active in database")
    
    conn.close()
    return True


def test_reactivate_other_users_alert_fails():
    """Test: User cannot reactivate another user's alert (security)."""
    print("\n📝 Test 2: Prevent reactivation of other user's alert")
    
    conn, user_id_1, user_id_2 = setup_test_db()
    cursor = conn.cursor()
    
    # Create an alert for user_1
    cursor.execute("""
        INSERT INTO price_alerts (user_id, symbol, target_price, condition, alert_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_1, "VNM", 85000, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT", 0))
    alert_id = cursor.lastrowid
    conn.commit()
    
    # Try to reactivate as user_2 (different user)
    try:
        alert_service.reactivate_price_alert(alert_id, user_id_2)
        print("  ✗ Should have raised ValueError for unauthorized access")
        conn.close()
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected with error: {e}")
    except Exception as e:
        print(f"  ✗ Wrong exception type: {e}")
        conn.close()
        return False
    
    # Verify alert is still inactive
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 0, "Alert should remain inactive"
    print("  ✓ Alert remains inactive after failed reactivation")
    
    conn.close()
    return True


def test_reactivate_nonexistent_alert_fails():
    """Test: Reactivating non-existent alert raises ValueError."""
    print("\n📝 Test 3: Reject reactivation of non-existent alert")
    
    conn, user_id_1, user_id_2 = setup_test_db()
    
    nonexistent_alert_id = 9999
    
    try:
        alert_service.reactivate_price_alert(nonexistent_alert_id, user_id_1)
        print("  ✗ Should have raised ValueError for non-existent alert")
        conn.close()
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejected with error: {e}")
    except Exception as e:
        print(f"  ✗ Wrong exception type: {e}")
        conn.close()
        return False
    
    conn.close()
    return True


def test_reactivate_already_active_alert():
    """Test: Reactivating an already active alert works without error."""
    print("\n📝 Test 4: Reactivate an already active alert")
    
    conn, user_id_1, user_id_2 = setup_test_db()
    cursor = conn.cursor()
    
    # Create an active alert
    cursor.execute("""
        INSERT INTO price_alerts (user_id, symbol, target_price, condition, alert_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_1, "VNM", 85000, "GREATER_THAN_OR_EQUAL", "TAKE_PROFIT", 1))
    alert_id = cursor.lastrowid
    conn.commit()
    
    # Verify it's active
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 1, "Alert should be active"
    print("  ✓ Alert is initially active")
    
    # Try to reactivate it (should work without error)
    try:
        alert_service.reactivate_price_alert(alert_id, user_id_1)
        print("  ✓ Reactivation of already-active alert succeeded")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        conn.close()
        return False
    
    # Verify it's still active
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 1, "Alert should remain active"
    print("  ✓ Alert remains active")
    
    conn.close()
    return True


def test_reactivate_with_repository_directly():
    """Test: Repository-level reactivate function works correctly."""
    print("\n📝 Test 5: Repository-level reactivate function")
    
    conn, user_id_1, user_id_2 = setup_test_db()
    cursor = conn.cursor()
    
    # Create an alert
    cursor.execute("""
        INSERT INTO price_alerts (user_id, symbol, target_price, condition, alert_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_1, "ACB", 3500, "LESS_THAN_OR_EQUAL", "STOP_LOSS", 0))
    alert_id = cursor.lastrowid
    conn.commit()
    
    # Call repository reactivate directly
    try:
        alert_repository.reactivate_price_alert(alert_id, user_id_1)
        print("  ✓ Repository reactivate call succeeded")
    except Exception as e:
        print(f"  ✗ Repository reactivate failed: {e}")
        conn.close()
        return False
    
    # Verify it's now active
    cursor.execute("SELECT is_active FROM price_alerts WHERE id = ?", (alert_id,))
    is_active = cursor.fetchone()[0]
    assert is_active == 1, "Alert should be active"
    print("  ✓ Alert is active in database")
    
    conn.close()
    return True


def run_all_tests():
    """Run all reactivate alert tests."""
    print("=" * 60)
    print("🧪 TESTING REACTIVATE ALERT FUNCTIONALITY")
    print("=" * 60)
    
    results = []
    
    results.append(("Reactivate own alert", test_reactivate_own_alert()))
    results.append(("Prevent other user reactivation", test_reactivate_other_users_alert_fails()))
    results.append(("Reject non-existent alert", test_reactivate_nonexistent_alert_fails()))
    results.append(("Reactivate already-active alert", test_reactivate_already_active_alert()))
    results.append(("Repository-level reactivate", test_reactivate_with_repository_directly()))
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n✅ {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
