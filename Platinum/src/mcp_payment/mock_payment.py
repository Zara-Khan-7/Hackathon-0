"""Mock payment/banking data for testing and development."""

MOCK_ACCOUNTS = [
    {
        "account_id": "acc_001",
        "name": "Business Current Account",
        "bank": "Emirates NBD",
        "currency": "AED",
        "balance": 125000.00,
        "type": "current",
    },
    {
        "account_id": "acc_002",
        "name": "Savings Account",
        "bank": "Emirates NBD",
        "currency": "AED",
        "balance": 350000.00,
        "type": "savings",
    },
]

MOCK_TRANSACTIONS = [
    {
        "txn_id": "txn_001",
        "account_id": "acc_001",
        "date": "2026-02-20",
        "description": "Payment from Acme Corp - Invoice #101",
        "amount": 5000.00,
        "type": "credit",
        "status": "completed",
    },
    {
        "txn_id": "txn_002",
        "account_id": "acc_001",
        "date": "2026-02-19",
        "description": "Office Rent - February 2026",
        "amount": -8500.00,
        "type": "debit",
        "status": "completed",
    },
    {
        "txn_id": "txn_003",
        "account_id": "acc_001",
        "date": "2026-02-18",
        "description": "Payment to Global Supplies - PO #4521",
        "amount": -3200.00,
        "type": "debit",
        "status": "completed",
    },
    {
        "txn_id": "txn_004",
        "account_id": "acc_002",
        "date": "2026-02-15",
        "description": "Monthly transfer from current",
        "amount": 10000.00,
        "type": "credit",
        "status": "completed",
    },
]

MOCK_PAYMENTS = []


def get_accounts() -> list[dict]:
    return list(MOCK_ACCOUNTS)


def get_balance(account_id: str) -> dict | None:
    for acc in MOCK_ACCOUNTS:
        if acc["account_id"] == account_id:
            return {"account_id": account_id, "balance": acc["balance"], "currency": acc["currency"]}
    return None


def get_transactions(account_id: str | None = None) -> list[dict]:
    if account_id:
        return [t for t in MOCK_TRANSACTIONS if t["account_id"] == account_id]
    return list(MOCK_TRANSACTIONS)


def initiate_payment(from_account: str, to_name: str, to_iban: str,
                     amount: float, reference: str) -> dict:
    payment = {
        "payment_id": f"pay_{len(MOCK_PAYMENTS) + 1:03d}",
        "from_account": from_account,
        "to_name": to_name,
        "to_iban": to_iban,
        "amount": amount,
        "reference": reference,
        "status": "pending_mock",
        "date": "2026-02-21",
    }
    MOCK_PAYMENTS.append(payment)
    return payment


def get_payment_status(payment_id: str) -> dict | None:
    for p in MOCK_PAYMENTS:
        if p["payment_id"] == payment_id:
            return p
    return None
