import socket
from unittest.mock import patch

import pytest

from app.services.exceptions import UnsafeUrlError
from app.services.url_validator import validate_public_url


def address_info(*addresses):
    return [
        (
            socket.AF_INET6 if ":" in address else socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            (address, 443),
        )
        for address in addresses
    ]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/page",
        "http://example.com:8080/page?q=1",
    ],
)
def test_public_urls_are_returned_unchanged_when_dns_is_public(url):
    with patch(
        "app.services.url_validator.socket.getaddrinfo",
        return_value=address_info("93.184.216.34"),
    ):
        assert validate_public_url(url) == url


def test_reserved_documentation_address_is_rejected():
    with patch(
        "app.services.url_validator.socket.getaddrinfo",
        return_value=address_info("198.51.100.10"),
    ):
        with pytest.raises(UnsafeUrlError):
            validate_public_url("https://198.51.100.10/")


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "javascript:alert(1)",
        "data:text/html,hello",
        "http://localhost/",
        "http://service.local/",
        "http://example.com@127.0.0.1/",
        "http://example.com\\@127.0.0.1/",
        "http://exa mple.com/",
        "http://example.com:not-a-port/",
        "http://./",
        "",
    ],
)
def test_invalid_or_unsafe_schemes_and_hosts_are_rejected(url):
    with pytest.raises(UnsafeUrlError):
        validate_public_url(url)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.0.1",
        "169.254.169.254",
        "0.0.0.0",
        "::1",
        "fc00::1",
        "fe80::1",
        "::ffff:127.0.0.1",
    ],
)
def test_non_public_resolved_addresses_are_rejected(address):
    host = f"[{address}]" if ":" in address else "example.com"
    with patch(
        "app.services.url_validator.socket.getaddrinfo",
        return_value=address_info(address),
    ):
        with pytest.raises(UnsafeUrlError):
            validate_public_url(f"http://{host}/")


def test_dns_failure_is_rejected():
    with patch(
        "app.services.url_validator.socket.getaddrinfo",
        side_effect=socket.gaierror("not found"),
    ):
        with pytest.raises(UnsafeUrlError):
            validate_public_url("https://does-not-exist.example/")


def test_public_ipv6_is_allowed():
    with patch(
        "app.services.url_validator.socket.getaddrinfo",
        return_value=address_info("2001:4860:4860::8888"),
    ):
        assert validate_public_url("https://example.com/") == "https://example.com/"
