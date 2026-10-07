import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:8000/api/auth/register/', method='POST', headers={'Content-Type': 'application/json'}, data=b'{\"email\":\"local@demo.com\",\"password\":\"TestPassword123!\",\"first_name\":\"Local\",\"last_name\":\"User\",\"tenant_name\":\"LocalTenant\"}')
try:
    urllib.request.urlopen(req)
except Exception as e: print(e)

req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login/', method='POST', headers={'Content-Type': 'application/json'}, data=b'{\"email\":\"local@demo.com\",\"password\":\"TestPassword123!\"}')
try:
    with urllib.request.urlopen(req) as f:
        cookies = f.headers.get('Set-Cookie', '')
except Exception as e: print(e)

req = urllib.request.Request('http://127.0.0.1:8000/api/ingestion/suricata/', method='POST', headers={'Content-Type': 'application/json', 'Cookie': cookies}, data=b'{\"events\": [{\"timestamp\":\"2024-01-15T12:00:00\",\"event_type\":\"alert\",\"src_ip\":\"185.220.101.5\",\"dest_ip\":\"192.168.1.45\",\"proto\":\"TCP\",\"alert\":{\"signature\":\"ET DOS\"},\"flow\":{\"bytes_toserver\":150000,\"pkts_toserver\":1500,\"duration\":2.0},\"tcp\":{\"syn\":1500}}]}')
try:
    with urllib.request.urlopen(req) as f:
        print(f.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())

