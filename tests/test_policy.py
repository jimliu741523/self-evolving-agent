"""Stdlib unittest for agent.policy — T3 claim parsing + enforcement."""
from __future__ import annotations

import unittest

from agent.policy import (
    parse_commit_message, check_claim, verify_message, CommitClaim, T3_RULES,
)


class TestParse(unittest.TestCase):
    def test_t3_with_rule(self):
        msg = "fix typo in README\n\ntier: T3\nrule: typo fix\n"
        c = parse_commit_message(msg)
        self.assertEqual(c.tier, "T3")
        self.assertEqual(c.rule, "typo fix")

    def test_no_claim(self):
        c = parse_commit_message("just a normal commit\n")
        self.assertIsNone(c.tier)
        self.assertIsNone(c.rule)

    def test_invalid_tier_rejected(self):
        c = parse_commit_message("foo\n\ntier: T9\nrule: typo fix\n")
        self.assertIsNone(c.tier)

    def test_case_insensitive_keys(self):
        c = parse_commit_message("foo\n\nTIER: T3\nRule: typo fix\n")
        self.assertEqual(c.tier, "T3")
        self.assertEqual(c.rule, "typo fix")


class TestCheck(unittest.TestCase):
    def test_t1_passes_without_rule(self):
        r = check_claim(CommitClaim(tier="T1", rule=None))
        self.assertTrue(r.ok)

    def test_no_claim_passes(self):
        r = check_claim(CommitClaim(tier=None, rule=None))
        self.assertTrue(r.ok)

    def test_t3_without_rule_fails(self):
        r = check_claim(CommitClaim(tier="T3", rule=None))
        self.assertFalse(r.ok)
        self.assertIn("without a rule", r.reason)

    def test_t3_with_unknown_rule_fails(self):
        r = check_claim(CommitClaim(tier="T3", rule="vibes"))
        self.assertFalse(r.ok)
        self.assertIn("not in exhaustive list", r.reason)

    def test_t3_with_known_rule_passes(self):
        for rule in T3_RULES:
            r = check_claim(CommitClaim(tier="T3", rule=rule))
            self.assertTrue(r.ok, msg=f"rule {rule!r} should pass")


class TestVerifyMessage(unittest.TestCase):
    def test_passes_for_well_formed_t3(self):
        r = verify_message("typo\n\ntier: T3\nrule: typo fix\n")
        self.assertTrue(r.ok)

    def test_fails_for_malformed_t3(self):
        r = verify_message("typo\n\ntier: T3\n")
        self.assertFalse(r.ok)


if __name__ == "__main__":
    unittest.main()
