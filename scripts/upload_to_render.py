import requests, sys

url = 'https://doc-intel-financial-platform.onrender.com/api/v1/documents/process'

files_to_upload = [
    ('dataset/Dataset/Balance Sheets/Consolidated Balance Sheet 2023.pdf', 'balance_sheet'),
    ('dataset/Dataset/Invoices/batch2-0499.jpg', 'invoice'),
    ('dataset/Dataset/Balance Sheets/Consolidated Balance Sheet 2018.pdf', 'balance_sheet'),
    ('dataset/Dataset/Profit & Loss/Consolidated Profit & Loss 2020.pdf', 'profit_and_loss'),
    ('dataset/Dataset/Cash Flow/Consolidated Cash Flow Statement 2019.pdf', 'cash_flow_statement')
]

for filepath, dtype in files_to_upload:
    print(f"Uploading {filepath} to Render...")
    try:
        with open(filepath, 'rb') as f:
            resp = requests.post(url, files={'file': f}, data={'document_type': dtype}, timeout=60)
            res = resp.json()
            status = res.get('processing_status')
            conf = res.get('overall_confidence')
            print(f"SUCCESS: {filepath} -> {status} (conf: {conf})")
    except Exception as err:
        print(f"FAILED: {filepath} -> {err}")
