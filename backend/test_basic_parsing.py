"""
Test basic parsing logic on sample OCR text
"""
import re

def _fallback_basic_parsing(text: str):
    """Same logic from enhanced_gemini_processor.py"""
    tradelines = []
    lines = text.split('\n')

    # State machine for parsing TransUnion format
    current_tradeline = None
    looking_for_details = False

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Detect "Account Name" header (TransUnion format)
        if line.lower() == "account name":
            print(f"✅ Found 'Account Name' at line {i}")
            # Save previous tradeline if exists
            if current_tradeline and current_tradeline.get("creditor_name"):
                print(f"   💾 Saving previous tradeline: {current_tradeline['creditor_name']}")
                tradelines.append(current_tradeline)
                current_tradeline = None
                looking_for_details = False

            # Next non-empty line should be the creditor name
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not next_line.lower() in ['account information', 'address', 'phone']:
                    print(f"   Creditor: {next_line}")
                    current_tradeline = {
                        "creditor_name": next_line,
                        "account_number": "",
                        "account_balance": "",
                        "credit_limit": "",
                        "monthly_payment": "",
                        "date_opened": "",
                        "account_type": "",
                        "account_status": "",
                        "is_negative": False
                    }
                    looking_for_details = True
                    break
            continue  # Skip to next iteration

        # Extract details if we have a current tradeline
        if current_tradeline and looking_for_details:
            print(f"  → Checking: '{line[:60]}...'")
            # Account number (usually has **** or XXXX)
            if re.search(r'\*{4}|\bXXXX\b', line):
                acc_match = re.search(r'[\dX*]{4,}[\dX*-]*', line)
                if acc_match:
                    current_tradeline["account_number"] = acc_match.group()
                    print(f"   Account number: {acc_match.group()}")

            # Balance
            if line.startswith('Balance'):
                bal_match = re.search(r'\$[\d,]+', line)
                if bal_match:
                    current_tradeline["account_balance"] = bal_match.group().replace(',', '')
                    print(f"   Balance: {bal_match.group()}")

            # Credit Limit
            if 'credit limit' in line.lower() or line.startswith('Limit'):
                limit_match = re.search(r'\$[\d,]+', line)
                if limit_match:
                    current_tradeline["credit_limit"] = limit_match.group().replace(',', '')
                    print(f"   Credit limit: {limit_match.group()}")

            # Monthly Payment
            if 'monthly payment' in line.lower():
                pay_match = re.search(r'\$[\d,]+', line)
                if pay_match:
                    current_tradeline["monthly_payment"] = pay_match.group().replace(',', '')
                    print(f"   Monthly payment: {pay_match.group()}")

            # Date Opened
            if 'date opened' in line.lower():
                date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', line)
                if date_match:
                    current_tradeline["date_opened"] = date_match.group()
                    print(f"   Date opened: {date_match.group()}")

            # Account Type
            if 'account type' in line.lower():
                type_part = line.split('Account Type', 1)[-1].strip()
                if type_part:
                    current_tradeline["account_type"] = type_part
                    print(f"   Account type: {type_part}")

            # Account Status
            status_keywords = ['charge off', 'collection', 'delinquent', 'current', 'closed', 'paid']
            for keyword in status_keywords:
                if keyword in line.lower():
                    current_tradeline["account_status"] = line
                    if keyword in ['charge off', 'collection', 'delinquent']:
                        current_tradeline["is_negative"] = True
                    print(f"   Status: {line}")
                    break

    # Don't forget the last tradeline
    if current_tradeline and current_tradeline.get("creditor_name"):
        print(f"   ✅ Saving last tradeline: {current_tradeline['creditor_name']}")
        tradelines.append(current_tradeline)

    return tradelines


# Test with sample OCR text from pages 8-10
sample_text = """
Accounts with Adverse Information

Account Name

CAPITAL ONE 515307682365****

Account Information

Address P O Box 31293 Salt Lake City, UT 84131
Phone (800) 955-7070
Monthly Payment $28
Date Opened 10/19/2022
Responsibility Individual Account
Account Type Revolving Account
Loan Type CREDIT CARD
Balance $459
Date Updated 05/24/2025
Last Payment Made 05/06/2025
High Balance $1,880
Credit Limit $2,000
Pay Status Current Account
"""

print("Testing basic parsing on sample OCR text...")
print("="*60)
tradelines = _fallback_basic_parsing(sample_text)
print("="*60)
print(f"\nTotal tradelines found: {len(tradelines)}")
for tl in tradelines:
    print(f"\n{tl['creditor_name']}")
    for key, val in tl.items():
        if val and key != 'creditor_name':
            print(f"  {key}: {val}")
