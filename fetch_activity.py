"""
Fetch recent Slack platform activity logs via apps.activity.list API.
This is what `slack run` displays in its terminal activity pane.
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Load CLI credentials (same token `slack run` uses)
with open(r'C:\Users\gfood\.slack\credentials.json') as f:
    creds = json.load(f)

token = creds.get('E0BBXU90CTC', {}).get('token', '')
print(f'Token prefix: {token[:15]}')
print(f'Token length: {len(token)}')
print()

# Fetch activity logs - the platform activity for the running app
# Time window: from 09:15 AM IST = 03:45 UTC
app_id = 'A0BBGGVJNCF'
team_id = 'E0BBXU90CTC'

# Try apps.activity.list (what slack run polls)
params = urllib.parse.urlencode({
    'app_id': app_id,
    'team_id': team_id,
    'min_date_created': '1783081500',  # ~09:15 IST in epoch
    'limit': 200,
    'source': 'APP',
})

url = f'https://slack.com/api/apps.activity.list?{params}'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    
    if data.get('ok'):
        activities = data.get('activities', [])
        print(f'Total activity entries: {len(activities)}')
        print('=' * 80)
        for act in activities:
            ts = act.get('created', 0)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%H:%M:%S UTC')
            level = act.get('level', '')
            component = act.get('component_type', '')
            text = act.get('text', '')
            print(f'[{dt}] [{level}] [{component}] {text}')
    else:
        print(f'API error: {data.get("error")}')
        print(f'Full: {json.dumps(data, indent=2)[:500]}')
except Exception as e:
    print(f'Request failed: {e}')
