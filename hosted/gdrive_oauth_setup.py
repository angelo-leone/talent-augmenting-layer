"""One-time helper to obtain a Google Drive OAuth refresh token.

Run this script ONCE on a machine with a browser to authorise your Google
account.  It will print the refresh token which you then set as the
``GDRIVE_OAUTH_REFRESH_TOKEN`` environment variable on Render (or wherever
you host the app).

Prerequisites
-------------
1. Go to https://console.cloud.google.com/ → APIs & Services → Credentials.
2. Create an **OAuth 2.0 Client ID** of type **Desktop app** (or Web app
   with ``http://localhost:8080/`` as an authorised redirect URI).
3. Download the client JSON or note the Client ID and Client Secret.

Usage
-----
    # Option A — supply client ID and secret as arguments:
    python -m hosted.gdrive_oauth_setup \
        --client-id YOUR_CLIENT_ID \
        --client-secret YOUR_CLIENT_SECRET

    # Option B — point to a downloaded client_secret JSON file:
    python -m hosted.gdrive_oauth_setup \
        --client-secrets-file /path/to/client_secret.json

The script opens a browser window for Google login. After you authorise,
it prints the refresh token to the terminal.
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Obtain a Google Drive OAuth refresh token for the pilot export.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--client-secrets-file",
        help="Path to the OAuth client_secret JSON file downloaded from Google Cloud Console.",
    )
    group.add_argument(
        "--client-id",
        help="OAuth 2.0 Client ID (use together with --client-secret).",
    )
    parser.add_argument(
        "--client-secret",
        help="OAuth 2.0 Client Secret (required when using --client-id).",
    )
    args = parser.parse_args()

    if args.client_id and not args.client_secret:
        parser.error("--client-secret is required when using --client-id")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "ERROR: google-auth-oauthlib is not installed.\n"
            "  pip install google-auth-oauthlib",
            file=sys.stderr,
        )
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/drive.file"]

    if args.client_secrets_file:
        flow = InstalledAppFlow.from_client_secrets_file(
            args.client_secrets_file,
            scopes=scopes,
        )
    else:
        client_config = {
            "installed": {
                "client_id": args.client_id,
                "client_secret": args.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=scopes,
        )

    # This opens a browser and runs a local server to receive the callback
    creds = flow.run_local_server(
        port=8080,
        prompt="consent",
        access_type="offline",
    )

    print("\n" + "=" * 60)
    print("SUCCESS — OAuth credentials obtained")
    print("=" * 60)
    print(f"\nClient ID:     {creds.client_id}")
    print(f"Refresh Token: {creds.refresh_token}")
    print(f"\nSet these environment variables on Render (or your host):\n")
    print(f"  GDRIVE_OAUTH_CLIENT_ID={creds.client_id}")
    print(f"  GDRIVE_OAUTH_CLIENT_SECRET={creds.client_secret}")
    print(f"  GDRIVE_OAUTH_REFRESH_TOKEN={creds.refresh_token}")
    print(f"\nThe access token expires automatically; the refresh token does not.")
    print("=" * 60)


if __name__ == "__main__":
    main()
