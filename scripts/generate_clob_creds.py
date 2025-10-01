#!/usr/bin/env python3
"""
Generate Polymarket CLOB API credentials
"""

from py_clob_client.client import ClobClient
import os
from dotenv import load_dotenv

load_dotenv()

def generate_api_credentials():
    """Generate API credentials using private key"""

    print("Generating Polymarket CLOB API Credentials")
    print("=" * 50)

    # Load private key from environment
    private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')

    if not private_key:
        print("ERROR: POLYGON_WALLET_PRIVATE_KEY not found in .env")
        print("Please add your private key to the .env file first:")
        print("POLYGON_WALLET_PRIVATE_KEY=0x_your_private_key_here")
        return False

    try:
        print("Connecting to Polymarket...")
        # Create client with private key
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137,  # Polygon
            signature_type=1  # Email/Magic wallet
        )

        print("Generating API credentials...")
        # Generate API credentials
        creds = client.create_or_derive_api_creds()

        # Extract credentials
        api_key = creds.api_key
        passphrase = creds.api_passphrase

        print("\n" + "="*50)
        print("SUCCESS: API Credentials Generated!")
        print("="*50)
        print(f"API Key: {api_key}")
        print(f"Passphrase: {passphrase}")
        print("="*50)

        print("\nIMPORTANT: Save these credentials securely!")
        print("Add them to your .env file:")
        print(f"CLOB_API_KEY={api_key}")
        print(f"CLOB_PASSPHRASE={passphrase}")

        # Optionally update .env file automatically
        update_env = input("\nUpdate .env file automatically? (y/n): ").lower().strip()
        if update_env == 'y':
            update_env_file(api_key, passphrase)
            print("SUCCESS: .env file updated!")

        return True

    except Exception as e:
        print(f"ERROR: Failed to generate credentials: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your private key is correct")
        print("2. Make sure you have funds on Polymarket")
        print("3. Verify your internet connection")
        return False

def update_env_file(api_key, passphrase):
    """Update .env file with generated credentials"""

    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

    # Read current .env content
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add credentials
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('CLOB_API_KEY='):
            lines[i] = f'CLOB_API_KEY={api_key}\n'
            updated = True
        elif line.startswith('CLOB_PASSPHRASE='):
            lines[i] = f'CLOB_PASSPHRASE={passphrase}\n'
            updated = True

    # Add credentials if not found
    if not any('CLOB_API_KEY=' in line for line in lines):
        lines.append(f'CLOB_API_KEY={api_key}\n')
    if not any('CLOB_PASSPHRASE=' in line for line in lines):
        lines.append(f'CLOB_PASSPHRASE={passphrase}\n')

    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    success = generate_api_credentials()
    if success:
        print("\nNext steps:")
        print("1. Credentials saved to .env")
        print("2. Run: python scripts/test_clob_authenticated.py")
        print("3. Start building trading endpoints")
    else:
        print("\nPlease fix the errors and try again.")