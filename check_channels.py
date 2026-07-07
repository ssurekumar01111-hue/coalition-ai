import json
import urllib.request
import urllib.parse

# Load credentials
with open(r'C:\Users\gfood\.slack\credentials.json') as f:
    creds = json.load(f)

team_creds = creds.get('E0BBXU90CTC', {})
token = team_creds.get('token', '')
print('Token type:', token[:15] if token else 'NONE')

# Use conversations.list to find mission-laptops-lucknow
url = 'https://slack.com/api/conversations.list'
params = urllib.parse.urlencode({
    'limit': 200,
    'exclude_archived': False,
    'types': 'public_channel,private_channel'
})
req = urllib.request.Request(
    f'{url}?{params}',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

if data.get('ok'):
    channels = data.get('channels', [])
    mission_channels = [c for c in channels if 'mission' in c['name'].lower()]
    print(f'Total channels: {len(channels)}')
    print(f'Mission channels found: {len(mission_channels)}')
    for c in mission_channels:
        archived = ' [ARCHIVED]' if c.get('is_archived') else ''
        name = c['name']
        cid = c['id']
        print(f'  - #{name} (id={cid}){archived}')
    
    # Also look for any channel with 'lucknow' in the name
    lucknow_channels = [c for c in channels if 'lucknow' in c['name'].lower()]
    if lucknow_channels:
        print(f'\nLucknow channels: {len(lucknow_channels)}')
        for c in lucknow_channels:
            archived = ' [ARCHIVED]' if c.get('is_archived') else ''
            print(f'  - #{c["name"]} (id={c["id"]}){archived}')
    else:
        print('\nNo channels with "lucknow" in name found.')
else:
    print('API error:', data.get('error'))
    print('Full response:', data)
