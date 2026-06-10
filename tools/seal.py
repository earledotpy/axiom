#!/usr/bin/env python3
"""Command-line mandate sealing and key verification tool for AXIOM Level 2A."""

import argparse
import base64
import json
import os
import sys
from getpass import getpass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

# Ensure axiom is in the Python search path if executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from axiom.security.level2a.canonical import canonicalize
from axiom.security.level2a.sealing import verify_payload_signature


def get_passphrase(confirm: bool = False) -> str:
    """Prompt the user for a passphrase securely."""
    while True:
        passphrase = getpass("Enter passphrase for private key: ")
        if not passphrase:
            print("Error: Passphrase cannot be empty.", file=sys.stderr)
            continue
        if confirm:
            confirm_passphrase = getpass("Confirm passphrase: ")
            if passphrase != confirm_passphrase:
                print("Error: Passphrases do not match. Try again.", file=sys.stderr)
                continue
        return passphrase


def cmd_generate_key(args: argparse.Namespace) -> None:
    """Generate a passphrase-protected Ed25519 private key and export public key."""
    out_dir = args.out_dir or "."
    os.makedirs(out_dir, exist_ok=True)

    private_path = os.path.join(out_dir, "private_key.pem")
    public_path = os.path.join(out_dir, "public_key.pem")

    passphrase = args.passphrase
    if not passphrase:
        passphrase = get_passphrase(confirm=True)

    # Generate keypair
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key with passphrase encryption
    try:
        private_bytes = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=BestAvailableEncryption(passphrase.encode("utf-8")),
        )
        with open(private_path, "wb") as f:
            f.write(private_bytes)
    except Exception as exc:
        print(f"Error saving private key: {exc}", file=sys.stderr)
        sys.exit(1)

    # Serialize public key to PEM
    try:
        public_bytes = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )
        with open(public_path, "wb") as f:
            f.write(public_bytes)
    except Exception as exc:
        print(f"Error saving public key: {exc}", file=sys.stderr)
        sys.exit(1)

    # Compute raw base64 public key (as used in sealing.py)
    raw_pub_bytes = public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    b64_pub_key = base64.b64encode(raw_pub_bytes).decode("ascii")

    print(f"Successfully generated Ed25519 keypair.")
    print(f"  Private key written to: {private_path}")
    print(f"  Public key written to:  {public_path}")
    print(f"  Raw Base64 Public Key:  {b64_pub_key}")


def cmd_export_public_key(args: argparse.Namespace) -> None:
    """Export public key from a passphrase-protected private key file."""
    if not os.path.exists(args.private_key):
        print(f"Error: Private key file '{args.private_key}' not found.", file=sys.stderr)
        sys.exit(1)

    passphrase = args.passphrase
    if not passphrase:
        passphrase = get_passphrase()

    # Load private key
    try:
        with open(args.private_key, "rb") as f:
            private_data = f.read()
        private_key = load_pem_private_key(private_data, password=passphrase.encode("utf-8"))
    except Exception as exc:
        print(f"Error loading private key (invalid passphrase or corrupted key file): {exc}", file=sys.stderr)
        sys.exit(1)

    public_key = private_key.public_key()

    # Format public key
    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    raw_pub_bytes = public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    b64_pub_key = base64.b64encode(raw_pub_bytes).decode("ascii")

    if args.out:
        try:
            with open(args.out, "wb") as f:
                f.write(public_pem)
            print(f"Public key exported to: {args.out}")
        except Exception as exc:
            print(f"Error saving public key: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(public_pem.decode("utf-8").strip())
        print(f"\nRaw Base64 Public Key: {b64_pub_key}")


def cmd_sign(args: argparse.Namespace) -> None:
    """Sign a mandate or envelope JSON payload."""
    if not os.path.exists(args.payload_file):
        print(f"Error: Payload file '{args.payload_file}' not found.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.private_key):
        print(f"Error: Private key file '{args.private_key}' not found.", file=sys.stderr)
        sys.exit(1)

    # Load payload
    try:
        with open(args.payload_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        print(f"Error loading payload JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(payload, dict):
        print("Error: Payload must be a JSON object (dictionary).", file=sys.stderr)
        sys.exit(1)

    passphrase = args.passphrase
    if not passphrase:
        passphrase = get_passphrase()

    # Load private key
    try:
        with open(args.private_key, "rb") as f:
            private_data = f.read()
        private_key = load_pem_private_key(private_data, password=passphrase.encode("utf-8"))
    except Exception as exc:
        print(f"Error loading private key: {exc}", file=sys.stderr)
        sys.exit(1)

    public_key = private_key.public_key()
    raw_pub_bytes = public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    b64_pub_key = base64.b64encode(raw_pub_bytes).decode("ascii")

    # Set or overwrite the public key field in the payload
    payload["signer_public_key"] = b64_pub_key

    # Pop existing signature if present for computing signature
    payload.pop("signature", None)

    # Canonicalize and sign
    try:
        canonical_bytes = canonicalize(payload)
        signature_bytes = private_key.sign(canonical_bytes)
        b64_sig = base64.b64encode(signature_bytes).decode("ascii")
    except Exception as exc:
        print(f"Error signing payload: {exc}", file=sys.stderr)
        sys.exit(1)

    # Set signature in payload
    payload["signature"] = b64_sig

    # Write output
    out_file = args.out or args.payload_file
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Successfully signed payload and saved to: {out_file}")
    except Exception as exc:
        print(f"Error saving signed payload: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_verify(args: argparse.Namespace) -> None:
    """Verify signature of a signed mandate/envelope file."""
    if not os.path.exists(args.payload_file):
        print(f"Error: Payload file '{args.payload_file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.payload_file, "r", encoding="utf-8") as f:
            envelope = json.load(f)
    except Exception as exc:
        print(f"Error loading JSON payload: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(envelope, dict):
        print("Error: Payload must be a JSON object.", file=sys.stderr)
        sys.exit(1)

    # Retrieve signer key and signature
    signature = envelope.get("signature")
    if not signature:
        print("Error: Payload does not contain a 'signature' field.", file=sys.stderr)
        sys.exit(1)

    signer_pub = args.public_key
    if not signer_pub:
        signer_pub = envelope.get("signer_public_key")
        if not signer_pub:
            print("Error: No public key provided via --public-key or in 'signer_public_key' payload field.", file=sys.stderr)
            sys.exit(1)

    # If --public-key is a file path, load it as PEM. If it's a string, we check if it is PEM or raw base64.
    if args.public_key and os.path.exists(args.public_key):
        try:
            with open(args.public_key, "rb") as f:
                pub_data = f.read()
            # If it's PEM format, parse it
            if b"-----BEGIN PUBLIC KEY-----" in pub_data:
                from cryptography.hazmat.primitives.serialization import load_pem_public_key
                loaded_pub = load_pem_public_key(pub_data)
                raw_pub = loaded_pub.public_bytes(
                    encoding=Encoding.Raw,
                    format=PublicFormat.Raw,
                )
                signer_pub = base64.b64encode(raw_pub).decode("ascii")
            else:
                signer_pub = pub_data.decode("ascii").strip()
        except Exception as exc:
            print(f"Error loading public key file: {exc}", file=sys.stderr)
            sys.exit(1)

    # Strip signature from envelope for verification
    payload_to_verify = {k: v for k, v in envelope.items() if k != "signature"}

    # Verify signature
    is_valid = verify_payload_signature(payload_to_verify, signature, signer_pub)

    if is_valid:
        print("Verification SUCCESS: Signature is VALID.")
        # If public key was passed, verify it matches the payload key
        payload_pub = envelope.get("signer_public_key")
        if payload_pub and payload_pub != signer_pub:
            print(f"Warning: Payload's 'signer_public_key' ({payload_pub}) does not match verify key ({signer_pub})", file=sys.stderr)
    else:
        print("Verification FAILURE: Signature is INVALID.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="AXIOM Level 2A Mandate Sealing and Verification Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-key subparser
    parser_gen = subparsers.add_parser("generate-key", help="Generate secure Ed25519 private key")
    parser_gen.add_argument("--out-dir", help="Directory to save the generated private_key.pem and public_key.pem")
    parser_gen.add_argument("--passphrase", help="Passphrase to encrypt the private key (prompts if omitted)")

    # export-public-key subparser
    parser_export = subparsers.add_parser("export-public-key", help="Export public key from private key")
    parser_export.add_argument("--private-key", required=True, help="Path to private_key.pem")
    parser_export.add_argument("--passphrase", help="Passphrase for the private key (prompts if omitted)")
    parser_export.add_argument("--out", help="Path to save the public_key.pem")

    # sign subparser
    parser_sign = subparsers.add_parser("sign", help="Sign a mandate or envelope payload")
    parser_sign.add_argument("payload_file", help="Path to JSON file to sign")
    parser_sign.add_argument("--private-key", required=True, help="Path to private_key.pem")
    parser_sign.add_argument("--passphrase", help="Passphrase for the private key (prompts if omitted)")
    parser_sign.add_argument("--out", help="Path to save the signed JSON (overwrites payload_file if omitted)")

    # verify subparser
    parser_verify = subparsers.add_parser("verify", help="Verify signature of a signed payload")
    parser_verify.add_argument("payload_file", help="Path to signed JSON file")
    parser_verify.add_argument("--public-key", help="Path to public_key.pem, or raw Base64 public key (reads from payload if omitted)")

    args = parser.parse_args()

    if args.command == "generate-key":
        cmd_generate_key(args)
    elif args.command == "export-public-key":
        cmd_export_public_key(args)
    elif args.command == "sign":
        cmd_sign(args)
    elif args.command == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
