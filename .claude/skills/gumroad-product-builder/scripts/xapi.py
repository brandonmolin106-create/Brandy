"""Tiny X (Twitter) API v2 client with OAuth 1.0a user-context signing. Standard library only.

Reads four env vars (all from the X developer portal, see X-SETUP.md):
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
import uuid

API = "https://api.x.com"
NEEDED = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")


class XError(SystemExit):
    pass


def creds() -> dict | None:
    vals = {k: os.environ.get(k) for k in NEEDED}
    return vals if all(vals.values()) else None


def _pct(s: str) -> str:
    return urllib.parse.quote(str(s), safe="~")


def _oauth_header(method: str, url: str, c: dict, extra_params: dict | None = None) -> str:
    oauth = {
        "oauth_consumer_key": c["X_API_KEY"],
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": c["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    params = {**oauth, **(extra_params or {})}
    norm = "&".join(f"{_pct(k)}={_pct(v)}" for k, v in sorted(params.items()))
    base = "&".join([method.upper(), _pct(url), _pct(norm)])
    key = f"{_pct(c['X_API_SECRET'])}&{_pct(c['X_ACCESS_SECRET'])}".encode()
    sig = base64.b64encode(hmac.new(key, base.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


def _send(req: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            j = json.loads(body)
            msg = j.get("detail") or j.get("title") or j.get("errors") or body
        except Exception:
            msg = body
        raise XError(f"X API error {e.code}: {msg}")


def get(path: str, c: dict, **query) -> dict:
    url = f"{API}{path}"
    full = f"{url}?{urllib.parse.urlencode(query)}" if query else url
    req = urllib.request.Request(full, headers={"Authorization": _oauth_header("GET", url, c, query)})
    return _send(req)


def post_json(path: str, c: dict, payload: dict) -> dict:
    url = f"{API}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": _oauth_header("POST", url, c),
        "Content-Type": "application/json",
    })
    return _send(req)


def upload_image(path: str, c: dict) -> str:
    """Upload a PNG/JPG via v2 media upload. Returns the media id string."""
    with open(path, "rb") as f:
        img = f.read()
    if len(img) > 5 * 1024 * 1024:
        raise XError(f"{path} is {len(img) // 1024} KB; X image limit is 5 MB.")
    ext = os.path.splitext(path)[1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")

    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (("media_category", "tweet_image"), ("media_type", mime)):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"{os.path.basename(path)}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n".encode() + img + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    url = f"{API}/2/media/upload"
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": _oauth_header("POST", url, c),
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    resp = _send(req)
    media_id = (resp.get("data") or {}).get("id") or resp.get("media_id_string")
    if not media_id:
        raise XError(f"Media upload returned no id: {resp}")
    return str(media_id)
