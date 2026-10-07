import urllib.request, json
req = urllib.request.Request('https://cybershield-backend-15ro.onrender.com/api/auth/register/', method='POST', headers={'Content-Type': 'application/json'}, data=b'{\"email\":\"test_suricata@demo.com\",\"password\":\"TestPassword123!\",\"first_name\":\"Test\",\"last_name\":\"User\",\"tenant_name\":\"TestSuricataTenant\"}')
try:
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())
        print('Registered')
except urllib.error.HTTPError as e:
    print('Reg Error:', e.code, e.read().decode())

req = urllib.request.Request('https://cybershield-backend-15ro.onrender.com/api/auth/login/', method='POST', headers={'Content-Type': 'application/json'}, data=b'{\"email\":\"test_suricata@demo.com\",\"password\":\"TestPassword123!\"}')
try:
    with urllib.request.urlopen(req) as f:
        headers = f.headers
        cookies = headers.get('Set-Cookie', '')
        print('Logged in, got cookie')
except urllib.error.HTTPError as e:
    print('Login Error:', e.code, e.read().decode())

req = urllib.request.Request('https://cybershield-backend-15ro.onrender.com/api/ingestion/suricata/', method='POST', headers={'Content-Type': 'application/json', 'Cookie': cookies}, data=b'{\"events\": [{\"timestamp\":\"2024-01-15T12:00:00\",\"event_type\":\"alert\",\"src_ip\":\"185.220.101.5\",\"dest_ip\":\"192.168.1.45\",\"proto\":\"TCP\",\"alert\":{\"signature\":\"ET DOS\"},\"flow\":{\"bytes_toserver\":150000,\"pkts_toserver\":1500,\"duration\":2.0},\"tcp\":{\"syn\":1500}}]}')
try:
    with urllib.request.urlopen(req) as f:
        print('Suricata Success:', f.read().decode())
except urllib.error.HTTPError as e:
    print('Suricata Error:', e.code, e.read().decode()[:500])

