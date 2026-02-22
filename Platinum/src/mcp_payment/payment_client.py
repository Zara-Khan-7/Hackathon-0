"""Payment MCP client — subprocess wrapper for the Payment server."""

from src.utils.mcp_registry import call_mcp


def list_accounts() -> dict:
    """List all bank accounts."""
    return call_mcp("payment", "list_accounts")


def get_balance(account_id: str) -> dict:
    """Get balance for a specific account."""
    return call_mcp("payment", "get_balance", {"account_id": account_id})


def list_transactions(account_id: str | None = None) -> dict:
    """List recent transactions."""
    args = {}
    if account_id:
        args["account_id"] = account_id
    return call_mcp("payment", "list_transactions", args)


def initiate_payment(from_account: str, to_name: str, to_iban: str,
                     amount: float, reference: str) -> dict:
    """Initiate a bank transfer (DANGEROUS — local only)."""
    return call_mcp("payment", "initiate_payment", {
        "from_account": from_account,
        "to_name": to_name,
        "to_iban": to_iban,
        "amount": amount,
        "reference": reference,
    })


def payment_status(payment_id: str) -> dict:
    """Check payment status."""
    return call_mcp("payment", "payment_status", {"payment_id": payment_id})
