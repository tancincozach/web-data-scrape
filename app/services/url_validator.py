import ipaddress
import socket
from urllib.parse import urlsplit

from .exceptions import UnsafeUrlError

_ALLOWED_SCHEMES = {"http", "https"}
_BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
_MAX_URL_LENGTH = 2048


def validate_public_url(url: str) -> str:
    """Return ``url`` if it is a safe, public HTTP(S) target.

    This is an application-level SSRF control: it rejects non-HTTP schemes,
    embedded credentials, private/loopback/link-local addresses, and hostnames
    that do not resolve to a public address. It does not replace network-level
    egress controls, because DNS can be rebound between validation and connect.
    """

    if not isinstance(url, str) or not url.strip():
        raise UnsafeUrlError("A URL is required.")

    url = url.strip()
    if len(url) > _MAX_URL_LENGTH:
        raise UnsafeUrlError("The URL is too long.")
    if any(character.isspace() or ord(character) < 32 for character in url):
        raise UnsafeUrlError(
            "The URL contains invalid whitespace or control characters."
        )
    if "\\" in url:
        raise UnsafeUrlError("The URL contains an invalid path separator.")

    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        host = parsed.hostname
    except ValueError as exc:
        raise UnsafeUrlError("The URL is malformed.") from exc

    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError("Only HTTP and HTTPS URLs are supported.")
    if not host:
        raise UnsafeUrlError("The URL must include a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("URLs containing credentials are not allowed.")

    try:
        host = host.rstrip(".").encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafeUrlError("The URL hostname is invalid.") from exc
    host = host.lower()
    if not host:
        raise UnsafeUrlError("The URL must include a hostname.")
    if host == "localhost" or host.endswith(_BLOCKED_HOST_SUFFIXES):
        raise UnsafeUrlError("The URL hostname is not allowed.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeUrlError("The URL port is invalid.") from exc
    if port is None:
        port = 443 if scheme == "https" else 80

    try:
        address_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeUrlError("The URL hostname could not be resolved.") from exc
    if not address_info:
        raise UnsafeUrlError("The URL hostname could not be resolved.")

    for _family, _type, _proto, _canonname, sockaddr in address_info:
        try:
            address = ipaddress.ip_address(sockaddr[0].split("%", 1)[0])
        except ValueError as exc:
            raise UnsafeUrlError("The URL resolved to an invalid address.") from exc
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not address.is_global:
            raise UnsafeUrlError("The URL resolves to a non-public address.")

    return url
