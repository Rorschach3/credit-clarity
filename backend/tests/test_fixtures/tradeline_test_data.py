"""
Test fixtures and data for tradeline extraction pipeline
Contains the exact test data from tradeline_test_rows.sql for validation
"""
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

# Expected tradeline records from tradeline_test_rows.sql for exact matching
EXPECTED_TRADELINE_RECORDS = [
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'LENTEGRITY LLC',
        'account_number': '2212311376****',
        'account_status': 'Closed',
        'account_type': 'Installment',
        'date_opened': '12/29/2022',
        'monthly_payment': '$0',
        'credit_limit': None,
        'account_balance': '$0',
        'user_id': None,
        'id': '953619a2-912e-498c-a79c-49895b9fa452',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'MOHELA/DEPT OF ED',
        'account_number': '25068505471E0012024052124****',
        'account_status': 'Current',
        'account_type': 'Installment',
        'date_opened': '05/21/2024',
        'monthly_payment': '$0',
        'credit_limit': None,
        'account_balance': '$3,000',
        'user_id': None,
        'id': 'c41ecbf4-9c25-4752-8b81-04d996f5249f',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CREDIT ONE BANK',
        'account_number': '37936304390****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '10/10/2023',
        'monthly_payment': '$30',
        'credit_limit': None,
        'account_balance': '$542',
        'user_id': None,
        'id': '1ce93bd0-11df-4ffc-83d3-4eb4045a6cce',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CAPITAL ONE',
        'account_number': '414709844770****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '01/23/2013',
        'monthly_payment': None,
        'credit_limit': '$25,000',
        'account_balance': '$0',
        'user_id': None,
        'id': '143f2970-47ae-48aa-b127-8416bd86dd91',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'JPMCB CARD SERVICES',
        'account_number': '414740410515****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '10/12/2011',
        'monthly_payment': None,
        'credit_limit': '$10,000',
        'account_balance': '$0',
        'user_id': None,
        'id': 'b7be7295-8f72-409e-bfdf-201bdd4ea065',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'JPMCB CARD SERVICES',
        'account_number': '438854005968****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '12/05/2003',
        'monthly_payment': None,
        'credit_limit': '$20,000',
        'account_balance': '$0',
        'user_id': None,
        'id': '683497fd-ab27-49c1-8793-c2c86a92ef76',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'JPMCB CARD SERVICES',
        'account_number': '438857611255****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '08/22/2014',
        'monthly_payment': None,
        'credit_limit': '$25,000',
        'account_balance': '$0',
        'user_id': None,
        'id': '6d353fc1-861e-4afb-9cd6-4b644590b417',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'BANK OF AMERICA',
        'account_number': '440066972254****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '04/22/2013',
        'monthly_payment': '$25',
        'credit_limit': '$142,000',
        'account_balance': '$99',
        'user_id': None,
        'id': 'dc8b9bb4-192d-4464-bac4-12cdb60e2c80',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CAPITAL ONE',
        'account_number': '468839067359****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '07/29/2016',
        'monthly_payment': None,
        'credit_limit': '$2,000',
        'account_balance': '$0',
        'user_id': None,
        'id': 'e6355fe4-4c7c-4e4a-8017-5a166a81b72e',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CAPITAL ONE',
        'account_number': '517805758255****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '06/03/2016',
        'monthly_payment': None,
        'credit_limit': None,
        'account_balance': '$0',
        'user_id': None,
        'id': '8fa72e31-dbfc-4ca4-a463-7f194069aa40',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CAPITAL ONE',
        'account_number': '517805938237****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '12/31/2015',
        'monthly_payment': None,
        'credit_limit': None,
        'account_balance': '$0',
        'user_id': None,
        'id': 'ec8647c4-cd16-4971-938d-ffa33890a47c',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'CAPITAL ONE',
        'account_number': '517805988806****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': '04/23/2014',
        'monthly_payment': None,
        'credit_limit': '$500',
        'account_balance': '$0',
        'user_id': None,
        'id': '7246ce34-3e35-494c-8715-e2697c850a89',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'SYNCB/CARE CREDIT DC',
        'account_number': '524306003974****',
        'account_status': 'Current',
        'account_type': 'Revolving',
        'date_opened': None,
        'monthly_payment': '$30',
        'credit_limit': '$3,500',
        'account_balance': None,
        'user_id': None,
        'id': '683bb6b8-4d2b-4cfe-90dd-d98232162b8a',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'DISCOVER CARD',
        'account_number': '601100752703****',
        'account_status': 'Closed',
        'account_type': 'Revolving',
        'date_opened': '05/08/2005',
        'monthly_payment': None,
        'credit_limit': '$20,000',
        'account_balance': '$0',
        'user_id': None,
        'id': '2f4a8709-155f-4bc7-8e7b-5c1360fbbd81',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'WEBBANK/FINGERHUT',
        'account_number': '636992104989****',
        'account_status': 'Closed',
        'account_type': 'Revolving',
        'date_opened': '09/30/2015',
        'monthly_payment': None,
        'credit_limit': '$1,100',
        'account_balance': '$0',
        'user_id': None,
        'id': 'aff32617-64e1-4e2d-a727-6966ac24f847',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'SELF FINANCIAL INC/LEAD BANK',
        'account_number': '64161****',
        'account_status': 'Closed',
        'account_type': 'Revolving',
        'date_opened': '01/22/2021',
        'monthly_payment': None,
        'credit_limit': '$100',
        'account_balance': '$0',
        'user_id': None,
        'id': '7b135bec-d12e-4905-a47d-fd9371900f4e',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'SCHOOLSFIRST FCU',
        'account_number': '755678****',
        'account_status': 'Closed',
        'account_type': 'Installment',
        'date_opened': '01/16/2014',
        'monthly_payment': '$0',
        'credit_limit': None,
        'account_balance': '$0',
        'user_id': None,
        'id': '2ce8dc17-be7c-45f6-be31-04011c2f16e4',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'SUNRISE BANK SELF LENDER',
        'account_number': 'CBA0000000001022****',
        'account_status': 'Closed',
        'account_type': 'Installment',
        'date_opened': '09/04/2021',
        'monthly_payment': '$0',
        'credit_limit': None,
        'account_balance': '$0',
        'user_id': None,
        'id': 'aed1e0a1-0ee2-48b3-87a8-212b53fc0bad',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'SUNRISE BANK SELF LENDER',
        'account_number': 'CBA0000000001497****',
        'account_status': 'Current',
        'account_type': 'Installment',
        'date_opened': '12/25/2024',
        'monthly_payment': '$25',
        'credit_limit': None,
        'account_balance': '$417',
        'user_id': None,
        'id': 'fc6e4bf3-cbb3-4c8a-80d3-0ba7282e6a6f',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    },
    {
        'credit_bureau': 'TransUnion',
        'creditor_name': 'UPSTART-A/CRB',
        'account_number': 'CR393****',
        'account_status': 'Current',
        'account_type': 'Installment',
        'date_opened': '09/01/2023',
        'monthly_payment': '$291',
        'credit_limit': None,
        'account_balance': '$9,728',
        'user_id': None,
        'id': '659fc1e2-7fcc-40b9-a347-373f858f0abf',
        'created_at': '2025-07-29 16:20:56.585099+00',
        'updated_at': '2025-07-29 16:20:57.107416+00'
    }
]


def get_expected_tradeline_by_account_number(account_number: str) -> Dict[str, Any] | None:
    """Get expected tradeline record by account number"""
    for record in EXPECTED_TRADELINE_RECORDS:
        if record['account_number'] == account_number:
            return record
    return None


def get_expected_tradelines_by_creditor(creditor_name: str) -> List[Dict[str, Any]]:
    """Get expected tradeline records by creditor name"""
    return [record for record in EXPECTED_TRADELINE_RECORDS 
            if record['creditor_name'] == creditor_name]


def validate_tradeline_format(tradeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tradeline matches expected format
    Returns dict with validation results
    """
    required_fields = [
        'credit_bureau', 'creditor_name', 'account_number', 'account_status',
        'account_type', 'date_opened', 'monthly_payment', 'credit_limit',
        'account_balance', 'user_id', 'id', 'created_at', 'updated_at'
    ]
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check required fields
    for field in required_fields:
        if field not in tradeline:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required field: {field}")
    
    # Validate specific field formats
    if 'credit_bureau' in tradeline and tradeline['credit_bureau'] not in ['TransUnion', 'Equifax', 'Experian']:
        validation_result['warnings'].append(f"Unexpected credit bureau: {tradeline['credit_bureau']}")
    
    if 'account_type' in tradeline and tradeline['account_type'] not in ['Revolving', 'Installment']:
        validation_result['warnings'].append(f"Unexpected account type: {tradeline['account_type']}")
    
    if 'account_status' in tradeline and tradeline['account_status'] not in ['Current', 'Closed']:
        validation_result['warnings'].append(f"Unexpected account status: {tradeline['account_status']}")
    
    # Validate date format (MM/DD/YYYY or None)
    if 'date_opened' in tradeline and tradeline['date_opened'] is not None:
        date_str = tradeline['date_opened']
        try:
            datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            validation_result['errors'].append(f"Invalid date format: {date_str}")
    
    # Validate currency format (starts with $ or is None)
    currency_fields = ['monthly_payment', 'credit_limit', 'account_balance']
    for field in currency_fields:
        if field in tradeline and tradeline[field] is not None:
            value = tradeline[field]
            if not (isinstance(value, str) and value.startswith('$')):
                validation_result['warnings'].append(f"Currency field {field} should start with $: {value}")
    
    return validation_result


def compare_tradeline_to_expected(extracted: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare extracted tradeline to expected record
    Returns detailed comparison results
    """
    comparison_result = {
        'exact_match': True,
        'field_matches': {},
        'differences': []
    }
    
    for field in expected.keys():
        extracted_value = extracted.get(field)
        expected_value = expected[field]
        
        if extracted_value == expected_value:
            comparison_result['field_matches'][field] = True
        else:
            comparison_result['exact_match'] = False
            comparison_result['field_matches'][field] = False
            comparison_result['differences'].append({
                'field': field,
                'expected': expected_value,
                'extracted': extracted_value
            })
    
    return comparison_result


# Sample TransUnion credit report text snippets for testing
SAMPLE_TRANSUNION_TEXT_SNIPPETS = [
    """
    CAPITAL ONE 515307682365****
    Account Type: Revolving Account
    Balance: $459
    Credit Limit: $5,000
    Date Opened: 01/23/2013
    Account Status: Current
    """,
    """
    LENTEGRITY LLC 2212311376****
    Account Type: Installment
    Balance: $0
    Monthly Payment: $0
    Date Opened: 12/29/2022
    Account Status: Closed
    """,
    """
    MOHELA/DEPT OF ED 25068505471E0012024052124****
    Account Type: Installment
    Balance: $3,000
    Monthly Payment: $0
    Date Opened: 05/21/2024
    Account Status: Current
    """
]