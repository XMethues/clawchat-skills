from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
ACCOUNT_BOOK = SCRIPT_DIR / "account_book.py"


class SubscriptionCurrencyTests(unittest.TestCase):
    def run_cli(
        self,
        *args: str,
        expected_returncode: int = 0,
    ) -> dict:
        completed = subprocess.run(
            [sys.executable, str(ACCOUNT_BOOK), *args],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            expected_returncode,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        return json.loads(completed.stdout)

    def create_subscription_fixture(self, directory: str, *, with_rate: bool) -> Path:
        book_path = Path(directory) / "account-book.json"
        self.run_cli("init", "--book", str(book_path))
        self.run_cli(
            "upsert-account",
            "--book",
            str(book_path),
            "--id",
            "acct_usd",
            "--name",
            "USD Cash",
            "--type",
            "asset",
            "--currency",
            "USD",
            "--balance",
            "1000",
            "--confirmed",
        )
        self.run_cli(
            "upsert-category",
            "--book",
            str(book_path),
            "--id",
            "subscriptions",
            "--name",
            "Subscriptions",
            "--kind",
            "expense",
            "--confirmed",
        )
        if with_rate:
            self.run_cli(
                "add-exchange-rate",
                "--book",
                str(book_path),
                "--id",
                "fx_usd_cny_20260716",
                "--date",
                "2026-07-16",
                "--from",
                "USD",
                "--to",
                "CNY",
                "--rate",
                "7.20",
                "--source",
                "test fixture",
                "--confirmed",
            )
        self.run_cli(
            "add-subscription",
            "--book",
            str(book_path),
            "--id",
            "sub_codex",
            "--name",
            "Codex",
            "--amount",
            "200",
            "--currency",
            "USD",
            "--cadence",
            "monthly",
            "--next-billing-date",
            "2026-07-16",
            "--category",
            "subscriptions",
            "--account",
            "acct_usd",
            "--confirmed",
        )
        return book_path

    def test_subscription_charge_uses_persisted_exact_date_rate(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=True)

            payload = self.run_cli(
                "charge-subscription",
                "--book",
                str(book_path),
                "--subscription",
                "sub_codex",
                "--date",
                "2026-07-16",
                "--no-balance-update",
                "--dry-run",
            )

            transaction = payload["record"]["transaction"]
            self.assertEqual(transaction["base_amount_minor"], 144000)
            self.assertEqual(
                transaction["exchange_rate_id"],
                "fx_usd_cny_20260716",
            )
            self.assertEqual(transaction["subscription_id"], "sub_codex")
            self.assertEqual(transaction["source"]["type"], "subscription")
            self.assertFalse(transaction["needs_review"])

    def test_confirmed_charge_persists_conversion_link_and_schedule(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=True)

            payload = self.run_cli(
                "charge-subscription",
                "--book",
                str(book_path),
                "--subscription",
                "sub_codex",
                "--date",
                "2026-07-16",
                "--no-balance-update",
                "--confirmed",
            )

            self.assertEqual(payload["status"], "charged")
            transaction_path = book_path.parent / "transactions" / "2026-07.json"
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))[
                "transactions"
            ][0]
            self.assertEqual(transaction["base_amount_minor"], 144000)
            self.assertEqual(transaction["exchange_rate_id"], "fx_usd_cny_20260716")
            self.assertEqual(transaction["subscription_id"], "sub_codex")

            book = json.loads(book_path.read_text(encoding="utf-8"))
            subscription = next(
                item for item in book["subscriptions"] if item["id"] == "sub_codex"
            )
            self.assertEqual(subscription["last_transaction_id"], transaction["id"])
            self.assertEqual(subscription["last_charged_date"], "2026-07-16")
            self.assertEqual(subscription["next_billing_date"], "2026-08-16")

    def test_subscription_definition_can_remain_in_billed_currency(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=False)

            book = json.loads(book_path.read_text(encoding="utf-8"))
            subscription = next(
                item for item in book["subscriptions"] if item["id"] == "sub_codex"
            )
            self.assertIsNone(subscription["base_amount_minor"])
            self.assertNotIn("needs_review", subscription)
            self.assertNotIn("review_reason", subscription)

    def test_charge_does_not_reuse_subscription_definition_rate(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=False)
            self.run_cli(
                "add-exchange-rate",
                "--book",
                str(book_path),
                "--id",
                "fx_old",
                "--date",
                "2026-06-16",
                "--from",
                "USD",
                "--to",
                "CNY",
                "--rate",
                "7.00",
                "--source",
                "old fixture",
                "--confirmed",
            )
            self.run_cli(
                "add-subscription",
                "--book",
                str(book_path),
                "--id",
                "sub_codex",
                "--name",
                "Codex",
                "--amount",
                "200",
                "--currency",
                "USD",
                "--exchange-rate-id",
                "fx_old",
                "--cadence",
                "monthly",
                "--next-billing-date",
                "2026-07-16",
                "--category",
                "subscriptions",
                "--account",
                "acct_usd",
                "--confirmed",
            )
            self.run_cli(
                "add-exchange-rate",
                "--book",
                str(book_path),
                "--id",
                "fx_charge_date",
                "--date",
                "2026-07-16",
                "--from",
                "USD",
                "--to",
                "CNY",
                "--rate",
                "7.20",
                "--source",
                "charge-date fixture",
                "--confirmed",
            )

            payload = self.run_cli(
                "charge-subscription",
                "--book",
                str(book_path),
                "--subscription",
                "sub_codex",
                "--date",
                "2026-07-16",
                "--no-balance-update",
                "--dry-run",
            )

            transaction = payload["record"]["transaction"]
            self.assertEqual(transaction["base_amount_minor"], 144000)
            self.assertEqual(transaction["exchange_rate_id"], "fx_charge_date")

    def test_matching_subscription_cannot_be_written_as_unlinked_transaction(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=False)

            payload = self.run_cli(
                "add-transaction",
                "--book",
                str(book_path),
                "--date",
                "2026-07-16",
                "--kind",
                "expense",
                "--amount",
                "200",
                "--currency",
                "USD",
                "--title",
                "Codex 订阅（本月）",
                "--category",
                "subscriptions",
                "--account",
                "acct_usd",
                "--source-type",
                "chat",
                "--source-text",
                "Codex订阅200美金/月，本月已从MP账户扣款",
                "--no-balance-update",
                "--dry-run",
                expected_returncode=1,
            )

            self.assertEqual(payload["code"], "subscription_charge_required")
            self.assertEqual(payload["matching_subscription"], "sub_codex")

    def test_explicitly_independent_matching_expense_can_be_previewed(self) -> None:
        with TemporaryDirectory() as directory:
            book_path = self.create_subscription_fixture(directory, with_rate=False)

            payload = self.run_cli(
                "add-transaction",
                "--book",
                str(book_path),
                "--date",
                "2026-07-16",
                "--kind",
                "expense",
                "--amount",
                "200",
                "--currency",
                "USD",
                "--title",
                "Codex independent purchase",
                "--category",
                "subscriptions",
                "--account",
                "acct_usd",
                "--source-type",
                "chat",
                "--source-text",
                "This is independent from the Codex subscription",
                "--allow-unlinked-subscription",
                "--no-balance-update",
                "--dry-run",
            )

            self.assertEqual(payload["status"], "preview")
            self.assertIsNone(payload["record"]["transaction"]["subscription_id"])

    def test_skill_contract_requires_complete_foreign_subscription_charge(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        subscriptions = (SKILL_DIR / "references" / "subscriptions.md").read_text(
            encoding="utf-8"
        )

        required_rules = (
            "Never use `add-transaction` for an actual subscription charge",
            "Do not write the charge first and ask for the conversion afterward",
        )
        for rule in required_rules:
            self.assertIn(rule, skill + subscriptions)


if __name__ == "__main__":
    unittest.main()
