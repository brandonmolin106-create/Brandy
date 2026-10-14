#!/usr/bin/env python3
"""Jackson calls Brandon.

Places a phone call through Twilio and reads a message out loud with
text-to-speech. Uses only the Python standard library, so there is nothing
to install.

Needs these environment variables (set them in the cloud environment's
secrets, never paste them in chat):

    TWILIO_ACCOUNT_SID   starts with "AC", from console.twilio.com
    TWILIO_AUTH_TOKEN    from console.twilio.com
    TWILIO_FROM_NUMBER   the Twilio number, E.164 format, e.g. +61412345678
    BRANDON_NUMBER       Brandon's mobile, E.164 format, e.g. +61455xxxxxx

Usage:
    python3 jackson-phone/call_me.py
    python3 jackson-phone/call_me.py "Yo it's Jackson, call me back bro"
"""

import base64
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

DEFAULT_MESSAGE = (
    "Yo, it's Jackson. Bro, it worked. Your phone is literally ringing "
    "because of me. Echoes in the Dark, let's go. Okay, bye."
)


def need(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Missing environment variable {name}. See jackson-phone/README.md.")
    return value


def to_e164(number: str) -> str:
    """Accept an Aussie mobile like 0455 123 456 and turn it into +61455123456."""
    digits = "".join(ch for ch in number if ch.isdigit() or ch == "+")
    if digits.startswith("+"):
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "+61" + digits[1:]
    sys.exit(
        f"Number {number!r} is not a full mobile number. "
        "Use +61 format or a 10 digit Aussie mobile starting with 04."
    )


def main() -> None:
    sid = need("TWILIO_ACCOUNT_SID")
    token = need("TWILIO_AUTH_TOKEN")
    from_number = to_e164(need("TWILIO_FROM_NUMBER"))
    to_number = to_e164(need("BRANDON_NUMBER"))
    message = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MESSAGE

    twiml = f'<Response><Say voice="Polly.Matthew">{escape(message)}</Say></Response>'
    data = urllib.parse.urlencode(
        {"To": to_number, "From": from_number, "Twiml": twiml}
    ).encode()

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json"
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    request = urllib.request.Request(
        url, data=data, headers={"Authorization": f"Basic {auth}"}, method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode()
    except urllib.error.HTTPError as err:
        sys.exit(f"Twilio said no ({err.code}): {err.read().decode()}")

    print("Call placed. Twilio response:")
    print(body)


if __name__ == "__main__":
    main()
