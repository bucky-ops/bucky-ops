import secrets

# Generate a random 32-byte private key
private_key = secrets.token_hex(32)

# Convert to Ethereum address format (0x + 40 hex characters)
ethereum_address = "0x" + private_key[:40]

print("Ethereum Address:", ethereum_address)
print("\nPrivate Key (keep this safe!):", "0x" + private_key) 