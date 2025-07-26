#!/usr/bin/env python3
"""
Compare actual vs expected tradeline extraction results
"""

import csv
import json
from collections import defaultdict

# Read expected results from CSV
def read_expected_csv():
    expected = []
    with open('/mnt/g/Downloads/tradelines_test_rows (1).csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            expected.append(row)
    return expected

# Read actual results from our test
def read_actual_results():
    with open('/mnt/c/projects/credit-clarity/test_results.json', 'r') as f:
        return json.load(f)

def analyze_creditors():
    """Compare creditors found vs expected"""
    expected = read_expected_csv()
    actual_data = read_actual_results()
    actual = actual_data['tradelines']
    
    print("🔍 CREDITOR ANALYSIS")
    print("=" * 50)
    
    # Count creditors in expected
    expected_creditors = defaultdict(int)
    for tl in expected:
        creditor = tl['creditor_name'].upper().strip()
        expected_creditors[creditor] += 1
    
    # Count creditors in actual
    actual_creditors = defaultdict(int)
    for tl in actual:
        creditor = tl['creditor_name'].upper().strip()
        actual_creditors[creditor] += 1
    
    print(f"📊 Expected: {len(expected)} tradelines")
    print(f"📊 Actual: {len(actual)} tradelines")
    print(f"📊 Processing method: {actual_data.get('processing_method', 'unknown')}")
    
    print(f"\n📋 EXPECTED CREDITORS ({len(expected_creditors)} unique):")
    for creditor, count in sorted(expected_creditors.items()):
        found_in_actual = creditor in actual_creditors
        status = "✅" if found_in_actual else "❌"
        actual_count = actual_creditors.get(creditor, 0)
        print(f"  {status} {creditor}: Expected {count}, Got {actual_count}")
    
    print(f"\n📋 ONLY IN ACTUAL (not expected):")
    for creditor, count in sorted(actual_creditors.items()):
        if creditor not in expected_creditors:
            print(f"  ⚠️ {creditor}: {count}")
    
    # Missing creditors
    missing = set(expected_creditors.keys()) - set(actual_creditors.keys())
    if missing:
        print(f"\n❌ MISSING CREDITORS ({len(missing)}):")
        for creditor in sorted(missing):
            print(f"  - {creditor} ({expected_creditors[creditor]} tradelines)")
    
    # Coverage analysis
    found_tradelines = sum(min(expected_creditors[c], actual_creditors.get(c, 0)) 
                          for c in expected_creditors.keys())
    coverage = (found_tradelines / len(expected)) * 100
    print(f"\n📈 COVERAGE: {coverage:.1f}% ({found_tradelines}/{len(expected)} tradelines)")

def analyze_account_types():
    """Analyze account types distribution"""
    expected = read_expected_csv()
    actual_data = read_actual_results()
    actual = actual_data['tradelines']
    
    print(f"\n\n🏦 ACCOUNT TYPE ANALYSIS")
    print("=" * 50)
    
    # Expected account types
    expected_types = defaultdict(int)
    for tl in expected:
        acc_type = tl['account_type'].strip()
        expected_types[acc_type] += 1
    
    # Actual account types
    actual_types = defaultdict(int)
    for tl in actual:
        acc_type = tl['account_type'].strip()
        actual_types[acc_type] += 1
    
    print("Expected vs Actual account types:")
    all_types = set(expected_types.keys()) | set(actual_types.keys())
    for acc_type in sorted(all_types):
        exp_count = expected_types.get(acc_type, 0)
        act_count = actual_types.get(acc_type, 0)
        status = "✅" if act_count > 0 else "❌"
        print(f"  {status} {acc_type}: Expected {exp_count}, Got {act_count}")

if __name__ == "__main__":
    try:
        analyze_creditors()
        analyze_account_types()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure both files exist:")
        print("  - /mnt/g/Downloads/tradelines_test_rows (1).csv")
        print("  - /mnt/c/projects/credit-clarity/test_results.json")