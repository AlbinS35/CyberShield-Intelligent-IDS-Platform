import urllib.request
req = urllib.request.Request('https://cybershield-backend-15ro.onrender.com/api/ingestion/suricata/', method='POST')
req.add_header('Content-Type', 'application/json')
try:
    with urllib.request.urlopen(req, data=b'{"events": []}') as f:
        print(f.read().decode())
except urllib.error.HTTPError as e:
    print('Error:', e.code)
    print(e.read().decode()[:500])
