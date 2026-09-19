"""
Generate a self-signed SSL certificate for 10.226.157.87
"""
import datetime
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# Paths
cert_dir = Path(__file__).parent / "ssl"
cert_dir.mkdir(exist_ok=True)
key_path = cert_dir / "key.pem"
cert_path = cert_dir / "cert.pem"

# Generate private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Write private key
key_path.write_bytes(
    key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
)

# Build certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "10.226.157.87"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CrewAI RAG Local"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=825))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address("10.226.157.87")),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.DNSName("localhost"),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

print("[OK] Certificate generated:")
print(f"   Key:  {key_path}")
print(f"   Cert: {cert_path}")
