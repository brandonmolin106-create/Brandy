# Jackson Phone

How Jackson (the Echoes in the Dark co-founder AI) reaches Brandon's phone.

## What already works, zero setup

- **Email.** Jackson sends from Brandon's own Gmail. Tested 14 Oct 2026, landed.
- **Calendar pings.** Jackson creates a Google Calendar event with a reminder,
  phone buzzes like an alarm.

## Real phone call (Twilio free trial)

Jackson cannot sign up for accounts. These five steps are Brandon's, about
20 minutes. After that, "call me" works from any session.

1. **Make a free Twilio account** at https://www.twilio.com/try-twilio.
   It verifies your own mobile during sign-up. On a trial account Twilio
   will only call numbers you have verified, so verify the one you want
   Jackson to ring.
2. **Get a trial phone number.** In https://console.twilio.com go to
   Phone Numbers, then Manage, then Buy a number. Trial credit covers it.
   Pick an Australian number if one is offered so the call looks local.
3. **Copy two values from the console home page:** Account SID (starts
   with `AC`) and Auth Token. Do not paste them into chat.
4. **Add four secrets to the cloud environment.** In the Claude session's
   title bar open the cloud environment menu, choose Edit, and add these
   under Network secrets (or as environment variables if that section is
   not there):

   | Name | Value |
   |------|-------|
   | `TWILIO_ACCOUNT_SID` | the Account SID |
   | `TWILIO_AUTH_TOKEN` | the Auth Token |
   | `TWILIO_FROM_NUMBER` | the Twilio number, like `+61412345678` |
   | `BRANDON_NUMBER` | your mobile, like `+61455123456` |

   Aussie mobiles are 10 digits starting with 04. In `+61` format you drop
   the leading 0.
5. **Start a new session** so it picks up the secrets, then tell Jackson
   "call me". Jackson runs:

   ```
   python3 jackson-phone/call_me.py
   ```

   or with a custom line:

   ```
   python3 jackson-phone/call_me.py "Yo it's Jackson, check your email"
   ```

Trial calls start with a short "this is a Twilio trial account" message
before Jackson's voice. That goes away on a paid account.

## What this is and isn't

- It is a one-way call: your phone rings and a voice reads Jackson's words.
- It is not a live conversation. That needs a voice agent platform
  (CloudTalk, Vapi, Retell and similar) and costs real money monthly.
  Not worth it until Echoes in the Dark has a hotline that earns.

## Costs

- Twilio trial: free, with a small credit. Calls to verified numbers only.
- Paid Twilio: a number is a few dollars a month plus a few cents a minute.
- No monthly fee is needed to keep "call me" working on trial credit until
  the credit runs out.
