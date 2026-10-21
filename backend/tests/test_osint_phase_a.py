"""Chunk 8 Phase A tests. All network and CLI execution is mocked."""
from __future__ import annotations

import subprocess
import unittest
from datetime import datetime
from types import SimpleNamespace

import dns.exception
import dns.resolver
from whois.exceptions import WhoisError

from osint.cli import resolve_allowlisted_executable
from osint.providers.dns import DnsProvider
from osint.providers.harvester import TheHarvesterProvider
from osint.providers.sherlock import SherlockProvider
from osint.providers.whois import WhoisProvider
from osint.registry import build_default_registry, default_provider_names
from osint.types import (
    STATUS_EMPTY,
    STATUS_INVALID_TARGET,
    STATUS_LOOKUP_FAILED,
    STATUS_MALFORMED_OUTPUT,
    STATUS_OK,
    STATUS_PROVIDER_UNAVAILABLE,
    STATUS_TIMEOUT,
    TARGET_TYPE_DOMAIN,
    TARGET_TYPE_USERNAME,
)
from osint.validation import InvalidTargetError, normalize_public_domain, normalize_public_username


class DummyName:
    def __init__(self, text: str) -> None:
        self._text = text

    def to_text(self) -> str:
        return self._text


class FakeResolver:
    def __init__(self, by_type: dict) -> None:
        self.by_type = by_type

    def resolve(self, qname, rdtype):
        key = str(rdtype).upper()
        if key not in self.by_type:
            raise dns.resolver.NoAnswer(response=None)
        value = self.by_type[key]
        if isinstance(value, BaseException):
            raise value
        return value


def _nxdomain() -> dns.resolver.NXDOMAIN:
    try:
        return dns.resolver.NXDOMAIN(qnames=["absent.example.com"])
    except TypeError:
        return dns.resolver.NXDOMAIN()


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["mock"], returncode=returncode, stdout=stdout, stderr=stderr)


class RegistryTests(unittest.TestCase):
    def test_default_providers_are_registered(self) -> None:
        registry = build_default_registry(
            theharvester=TheHarvesterProvider(which_fn=lambda _name: None),
            sherlock=SherlockProvider(which_fn=lambda _name: None),
        )
        self.assertEqual(registry.names(), ["dns", "sherlock", "theharvester", "whois"])
        self.assertEqual(default_provider_names(), ["dns", "sherlock", "theharvester", "whois"])
        infos = {info.name: info for info in registry.infos()}
        self.assertTrue(infos["dns"].available)
        self.assertFalse(infos["dns"].optional)
        self.assertTrue(infos["whois"].available)
        self.assertFalse(infos["theharvester"].available)
        self.assertTrue(infos["theharvester"].optional)
        self.assertFalse(infos["sherlock"].available)
        self.assertTrue(infos["sherlock"].optional)
        self.assertEqual(infos["dns"].supported_target_types, [TARGET_TYPE_DOMAIN])
        self.assertEqual(infos["sherlock"].supported_target_types, [TARGET_TYPE_USERNAME])

    def test_get_unknown_provider_returns_none(self) -> None:
        registry = build_default_registry(
            theharvester=TheHarvesterProvider(which_fn=lambda _name: None),
            sherlock=SherlockProvider(which_fn=lambda _name: None),
        )
        self.assertIsNone(registry.get("not-a-provider"))


class ValidationTests(unittest.TestCase):
    def test_valid_public_domain(self) -> None:
        self.assertEqual(normalize_public_domain("Example.COM."), "example.com")

    def test_invalid_domains(self) -> None:
        for value in (
            "",
            "localhost",
            "127.0.0.1",
            "192.168.0.1",
            "not a domain",
            "example",
            "https://example.com",
            "example.com/path",
            "foo.local",
            "foo.internal",
            "example.com;rm",
            "user@example.com",
            "-bad.com",
        ):
            with self.subTest(value=value):
                with self.assertRaises(InvalidTargetError):
                    normalize_public_domain(value)

    def test_valid_username(self) -> None:
        self.assertEqual(normalize_public_username("@Demo_User"), "Demo_User")

    def test_invalid_usernames(self) -> None:
        for value in ("", "a b", "https://x.com/u", "user;id", "user/name", "user@host"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidTargetError):
                    normalize_public_username(value)


class DnsProviderTests(unittest.TestCase):
    def test_valid_domain_parses_records(self) -> None:
        resolver = FakeResolver(
            {
                "A": [SimpleNamespace(address="93.184.216.34")],
                "AAAA": [SimpleNamespace(address="2606:2800:220:1:248:1893:25c8:1946")],
                "MX": [SimpleNamespace(exchange=DummyName("mail.example.com."), preference=10)],
                "NS": [SimpleNamespace(target=DummyName("a.iana-servers.net."))],
                "TXT": [SimpleNamespace(strings=[b"v=spf1 -all"])],
            }
        )
        result = DnsProvider(resolver=resolver).execute("Example.COM", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(result.target, "example.com")
        values = {(f.finding_type, f.value) for f in result.findings}
        self.assertIn(("dns_a", "93.184.216.34"), values)
        self.assertIn(("dns_aaaa", "2606:2800:220:1:248:1893:25c8:1946"), values)
        self.assertIn(("dns_mx", "mail.example.com"), values)
        self.assertIn(("dns_ns", "a.iana-servers.net"), values)
        self.assertIn(("dns_txt", "v=spf1 -all"), values)

    def test_invalid_domain_does_not_query(self) -> None:
        class GuardResolver:
            def resolve(self, *args, **kwargs):
                raise AssertionError("resolver must not be called for invalid targets")

        result = DnsProvider(resolver=GuardResolver()).execute("not a domain", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_INVALID_TARGET)
        self.assertEqual(result.findings, [])

    def test_nxdomain_is_empty_not_fabricated(self) -> None:
        resolver = FakeResolver({key: _nxdomain() for key in ("A", "AAAA", "MX", "NS", "TXT")})
        result = DnsProvider(resolver=resolver).execute("absent.example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_EMPTY)
        self.assertEqual(result.findings, [])

    def test_timeout(self) -> None:
        resolver = FakeResolver({key: dns.exception.Timeout() for key in ("A", "AAAA", "MX", "NS", "TXT")})
        result = DnsProvider(resolver=resolver).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_TIMEOUT)
        self.assertEqual(result.findings, [])

    def test_lookup_failure(self) -> None:
        resolver = FakeResolver(
            {key: RuntimeError("nameserver failure") for key in ("A", "AAAA", "MX", "NS", "TXT")}
        )
        result = DnsProvider(resolver=resolver).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_LOOKUP_FAILED)
        self.assertEqual(result.findings, [])


class WhoisProviderTests(unittest.TestCase):
    def test_valid_domain_maps_present_fields_only(self) -> None:
        payload = {
            "domain_name": "EXAMPLE.COM",
            "registrar": "RESERVED-Internet Assigned Numbers Authority",
            "creation_date": datetime(1995, 8, 14, 4, 0, 0),
            "expiration_date": None,
            "emails": None,
            "name_servers": ["A.IANA-SERVERS.NET", "B.IANA-SERVERS.NET"],
            "country": "",
        }

        def lookup(domain, **kwargs):
            self.assertEqual(domain, "example.com")
            self.assertIn("timeout", kwargs)
            return payload

        result = WhoisProvider(lookup_fn=lookup).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_OK)
        fields = {f.details["field"] for f in result.findings if f.details}
        self.assertIn("domain_name", fields)
        self.assertIn("registrar", fields)
        self.assertIn("creation_date", fields)
        self.assertIn("name_servers", fields)
        self.assertNotIn("expiration_date", fields)
        self.assertNotIn("emails", fields)
        self.assertNotIn("country", fields)

    def test_invalid_domain(self) -> None:
        def lookup(*args, **kwargs):
            raise AssertionError("WHOIS must not run for invalid targets")

        result = WhoisProvider(lookup_fn=lookup).execute("foo.local", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_INVALID_TARGET)
        self.assertEqual(result.findings, [])

    def test_whois_error_is_lookup_failed(self) -> None:
        def lookup(*args, **kwargs):
            raise WhoisError("No match for domain")

        result = WhoisProvider(lookup_fn=lookup).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_LOOKUP_FAILED)
        self.assertEqual(result.findings, [])
        self.assertIn("No match", result.error or "")

    def test_timeout(self) -> None:
        def lookup(*args, **kwargs):
            raise TimeoutError("timed out")

        result = WhoisProvider(lookup_fn=lookup).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_TIMEOUT)
        self.assertEqual(result.findings, [])

    def test_empty_payload_is_not_fabricated(self) -> None:
        result = WhoisProvider(lookup_fn=lambda *a, **k: {}).execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_EMPTY)
        self.assertEqual(result.findings, [])


class HarvesterProviderTests(unittest.TestCase):
    def test_unavailable_returns_structured_status(self) -> None:
        provider = TheHarvesterProvider(which_fn=lambda _name: None)
        self.assertFalse(provider.is_available())
        result = provider.execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_PROVIDER_UNAVAILABLE)
        self.assertEqual(result.findings, [])
        self.assertTrue(result.meta and result.meta.get("optional") is True)

    def test_malformed_output(self) -> None:
        def run_fn(argv, **kwargs):
            self.assertFalse(kwargs.get("shell"))
            self.assertEqual(argv[1:], ["-d", "example.com", "-l", "50", "-b", "duckduckgo"])
            return _completed(stdout="??? totally not harvester output ???")

        provider = TheHarvesterProvider(
            which_fn=lambda name: "/usr/bin/theHarvester" if name == "theHarvester" else None,
            run_fn=run_fn,
        )
        result = provider.execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_MALFORMED_OUTPUT)
        self.assertEqual(result.findings, [])

    def test_json_output_is_parsed(self) -> None:
        def run_fn(argv, **kwargs):
            return _completed(stdout='{"emails": ["osint@example.com"], "hosts": ["www.example.com"], "ips": []}')

        provider = TheHarvesterProvider(
            which_fn=lambda name: "/usr/bin/theHarvester" if name == "theHarvester" else None,
            run_fn=run_fn,
        )
        result = provider.execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_OK)
        values = {(f.finding_type, f.value) for f in result.findings}
        self.assertIn(("email", "osint@example.com"), values)
        self.assertIn(("host", "www.example.com"), values)

    def test_timeout(self) -> None:
        def run_fn(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

        provider = TheHarvesterProvider(
            which_fn=lambda name: "/usr/bin/theHarvester" if name == "theHarvester" else None,
            run_fn=run_fn,
        )
        result = provider.execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_TIMEOUT)

    def test_nonzero_exit_without_stdout_is_lookup_failed(self) -> None:
        def run_fn(argv, **kwargs):
            return _completed(stdout="", stderr="source failed", returncode=2)

        provider = TheHarvesterProvider(
            which_fn=lambda name: "/usr/bin/theHarvester" if name == "theHarvester" else None,
            run_fn=run_fn,
        )
        result = provider.execute("example.com", TARGET_TYPE_DOMAIN)
        self.assertEqual(result.status, STATUS_LOOKUP_FAILED)


class SherlockProviderTests(unittest.TestCase):
    def test_unavailable_returns_structured_status(self) -> None:
        provider = SherlockProvider(which_fn=lambda _name: None)
        self.assertFalse(provider.is_available())
        result = provider.execute("demo_user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_PROVIDER_UNAVAILABLE)
        self.assertEqual(result.findings, [])

    def test_malformed_output(self) -> None:
        def run_fn(argv, **kwargs):
            self.assertFalse(kwargs.get("shell"))
            self.assertEqual(argv[-1], "demo_user")
            return _completed(stdout="garbage that is not sherlock")

        provider = SherlockProvider(
            which_fn=lambda name: "/usr/bin/sherlock" if name == "sherlock" else None,
            run_fn=run_fn,
        )
        result = provider.execute("demo_user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_MALFORMED_OUTPUT)
        self.assertEqual(result.findings, [])

    def test_text_hits_are_parsed(self) -> None:
        def run_fn(argv, **kwargs):
            return _completed(stdout="[+] GitHub: https://github.com/demo_user\n[*] Checking Twitter")

        provider = SherlockProvider(
            which_fn=lambda name: "/usr/bin/sherlock" if name == "sherlock" else None,
            run_fn=run_fn,
        )
        result = provider.execute("demo_user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_OK)
        self.assertEqual(result.findings[0].finding_type, "social_profile")
        self.assertEqual(result.findings[0].value, "https://github.com/demo_user")

    def test_json_negative_status_is_not_a_hit(self) -> None:
        def run_fn(argv, **kwargs):
            return _completed(stdout='{"GitHub": {"url": "https://github.com/demo_user", "status": "Unknown"}}')

        provider = SherlockProvider(
            which_fn=lambda name: "/usr/bin/sherlock" if name == "sherlock" else None,
            run_fn=run_fn,
        )
        result = provider.execute("demo_user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_EMPTY)
        self.assertEqual(result.findings, [])

    def test_timeout(self) -> None:
        def run_fn(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

        provider = SherlockProvider(
            which_fn=lambda name: "/usr/bin/sherlock" if name == "sherlock" else None,
            run_fn=run_fn,
        )
        result = provider.execute("demo_user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_TIMEOUT)

    def test_invalid_username(self) -> None:
        def run_fn(*args, **kwargs):
            raise AssertionError("Sherlock must not run for invalid usernames")

        result = SherlockProvider(
            which_fn=lambda name: "/usr/bin/sherlock",
            run_fn=run_fn,
        ).execute("bad user", TARGET_TYPE_USERNAME)
        self.assertEqual(result.status, STATUS_INVALID_TARGET)


class CliAllowlistTests(unittest.TestCase):
    def test_basename_must_match_allowlist(self) -> None:
        def which_fn(name: str):
            if name == "sherlock":
                return "/tmp/not-sherlock/python"
            return None

        self.assertIsNone(resolve_allowlisted_executable(("sherlock",), which_fn=which_fn))

    def test_allowlisted_name_resolves(self) -> None:
        path = resolve_allowlisted_executable(
            ("sherlock",),
            which_fn=lambda name: "/usr/bin/sherlock" if name == "sherlock" else None,
        )
        self.assertEqual(path, "/usr/bin/sherlock")


if __name__ == "__main__":
    unittest.main()
