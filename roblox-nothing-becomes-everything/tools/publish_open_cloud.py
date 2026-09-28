#!/usr/bin/env python3
"""Publish "Nothing Becomes Everything" to Roblox without opening Studio, through Open Cloud.

    python3 tools/publish_open_cloud.py            # upload audio, write IDs, rebuild, publish
    python3 tools/publish_open_cloud.py --check    # only check the settings below

Reads these environment variables. Put them in your environment settings; never in code or chat.
  ROBLOX_API_KEY      Open Cloud API key (create.roblox.com > Open Cloud > API Keys) with
                        - Assets: Read + Write
                        - universe-places: Write, on this experience
                      and Accepted IP Addresses 0.0.0.0/0 (the publishing machine's IP changes).
  ROBLOX_USER_ID      your Roblox user ID (the number in your profile's web address)
  ROBLOX_UNIVERSE_ID  the experience's Universe ID (Creator Dashboard > the experience > Copy Universe ID)
  ROBLOX_PLACE_ID     its start place ID (Creator Dashboard > Places > Copy Start Place ID)

The experience must exist first (publish it once from Studio, or create it in the Creator Dashboard).
Uploads only the three audio packs whose ID in Config is still 0, writes the new IDs into
src/ReplicatedStorage/Config.lua, rebuilds the place and publishes it. Open Cloud can't upload
videos, so zone videos and the loading screen image are still uploaded in Studio (README step 2).
"""
import json, os, re, subprocess, sys, time, urllib.error, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, 'src', 'ReplicatedStorage', 'Config.lua')
PLACE = os.path.join(ROOT, 'NothingBecomesEverything.rbxlx')
UPLOAD = os.path.join(ROOT, 'upload')
API = 'https://apis.roblox.com'
PACKS = [('VoicePackId', 'voice_pack.ogg', 'Nothing Becomes Everything - voice'),
         ('MusicPackId', 'music_pack.ogg', 'Nothing Becomes Everything - music'),
         ('SfxPackId', 'sfx_pack.ogg', 'Nothing Becomes Everything - sound effects')]


def env(name):
    value = os.environ.get(name, '').strip()
    if not value:
        sys.exit(f'Missing environment variable {name}. See the top of tools/publish_open_cloud.py.')
    return value


def call(method, url, key, body=None, headers=None):
    req = urllib.request.Request(url, data=body, method=method, headers={'x-api-key': key, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors='replace')[:600]
        hint = {401: 'the API key is wrong, expired, or its Accepted IP Addresses exclude this machine',
                403: 'the API key lacks the permission for this (Assets read+write / universe-places write)',
                404: 'the universe or place ID is wrong'}.get(e.code, '')
        sys.exit(f'{method} {url} failed: HTTP {e.code} {detail}' + (f'\nLikely cause: {hint}.' if hint else ''))


def config_ids():
    text = open(CONFIG).read()
    return {name: int(re.search(rf'\b{name}\s*=\s*(\d+)', text).group(1)) for name, _, _ in PACKS}


def write_id(name, asset_id):
    text = open(CONFIG).read()
    new, n = re.subn(rf'(\b{name}\s*=\s*)\d+', rf'\g<1>{asset_id}', text, count=1)
    if n != 1:
        sys.exit(f'Could not find {name} in {CONFIG}')
    open(CONFIG, 'w').write(new)


def upload_audio(key, user_id, filename, display):
    boundary = uuid.uuid4().hex
    meta = json.dumps({'assetType': 'Audio', 'displayName': display,
                       'description': 'Audio pack for the Roblox game Nothing Becomes Everything',
                       'creationContext': {'creator': {'userId': str(user_id)}}})
    blob = open(os.path.join(UPLOAD, filename), 'rb').read()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="request"\r\n'
            f'Content-Type: application/json\r\n\r\n{meta}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="fileContent"; filename="{filename}"\r\n'
            f'Content-Type: audio/ogg\r\n\r\n').encode() + blob + f'\r\n--{boundary}--\r\n'.encode()
    op = call('POST', f'{API}/assets/v1/assets', key, body, {'Content-Type': f'multipart/form-data; boundary={boundary}'})
    path = op.get('path') or f"operations/{op.get('operationId')}"
    for _ in range(80):                                        # uploads usually finish in seconds
        status = call('GET', f'{API}/assets/v1/{path}', key)
        if status.get('done'):
            asset_id = (status.get('response') or {}).get('assetId')
            if not asset_id:
                sys.exit(f'Upload of {filename} finished without an asset ID: {json.dumps(status)[:400]}')
            return int(asset_id)
        time.sleep(3)
    sys.exit(f'Upload of {filename} is still processing. Check Creator Dashboard > Creations > Audio, then run again.')


def main():
    key, user_id = env('ROBLOX_API_KEY'), env('ROBLOX_USER_ID')
    universe, place = env('ROBLOX_UNIVERSE_ID'), env('ROBLOX_PLACE_ID')
    for label, value in (('ROBLOX_USER_ID', user_id), ('ROBLOX_UNIVERSE_ID', universe), ('ROBLOX_PLACE_ID', place)):
        if not value.isdigit():
            sys.exit(f'{label} should be a number, got {value!r}')
    ids = config_ids()
    if '--check' in sys.argv:
        print('Settings look complete. Config audio IDs:', ids)
        return
    for name, filename, display in PACKS:
        if ids[name] > 0:
            print(f'{name}: already {ids[name]}, skipping upload')
            continue
        asset_id = upload_audio(key, user_id, filename, display)
        write_id(name, asset_id)
        print(f'{name}: uploaded {filename} -> {asset_id}')
    subprocess.run([sys.executable, os.path.join(HERE, 'build_place.py')], check=True)
    body = open(PLACE, 'rb').read()
    result = call('POST', f'{API}/universes/v1/{universe}/places/{place}/versions?versionType=Published', key, body,
                  {'Content-Type': 'application/xml'})
    print(f"Published version {result.get('versionNumber')} of place {place}.")
    print('New audio can take a while to pass Roblox moderation before it plays. The experience stays private until '
          'you make it public in the Creator Dashboard (README step 8).')


if __name__ == '__main__':
    main()
