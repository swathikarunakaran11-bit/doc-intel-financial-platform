import requests, json

resp = requests.post(
    'http://127.0.0.1:8000/api/v1/documents/process',
    files={'file': open('dataset/Dataset/Invoices/batch2-0499.jpg', 'rb')},
    data={'document_type': 'invoice'}
)
res = resp.json()
print("Status Code:", resp.status_code)
print("Processing Latency:", res.get("processing_metadata", {}).get("processing_time_ms"), "ms")
print("Overall Confidence:", res.get("overall_confidence"))
print("\nExtracted Data:")
for k, v in res.get("extracted_data", {}).items():
    if isinstance(v, dict) and "value" in v:
        print(f"  {k}: {v.get('value')} (conf: {v.get('confidence')})")

print("\nValidation Checks:")
for c in res.get("validation", {}).get("checks", []):
    print(f"  {c['name']}: {c['status']} | {c.get('formula')} -> calc={c.get('calculated_value')} vs rep={c.get('reported_value')} (var={c.get('variance')})")
