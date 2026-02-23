"""Payment MCP Server — JSON-RPC over stdio (LOCAL-ONLY).

Tools:
- list_accounts (SAFE) — list bank accounts
- get_balance (SAFE) — get account balance
- list_transactions (SAFE) — list recent transactions
- initiate_payment (DANGEROUS) — initiate a bank transfer
- payment_status (SAFE) — check payment status
"""

import json
import sys
import os

from src.mcp_payment.mock_payment import (
    get_accounts, get_balance, get_transactions,
    initiate_payment, get_payment_status,
)

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

TOOLS = [
    {
        "name": "list_accounts",
        "description": "List all bank accounts",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_balance",
        "description": "Get balance for a specific bank account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "The account ID"},
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "list_transactions",
        "description": "List recent transactions, optionally filtered by account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Filter by account ID (optional)"},
            },
        },
    },
    {
        "name": "initiate_payment",
        "description": "Initiate a bank transfer (DANGEROUS — requires approval)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_account": {"type": "string", "description": "Source account ID"},
                "to_name": {"type": "string", "description": "Recipient name"},
                "to_iban": {"type": "string", "description": "Recipient IBAN"},
                "amount": {"type": "number", "description": "Amount to transfer"},
                "reference": {"type": "string", "description": "Payment reference"},
            },
            "required": ["from_account", "to_name", "to_iban", "amount", "reference"],
        },
    },
    {
        "name": "payment_status",
        "description": "Check the status of a payment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "The payment ID to check"},
            },
            "required": ["payment_id"],
        },
    },
]


def handle_tool_call(name: str, arguments: dict) -> dict:
    """Handle a single tool call."""
    if name == "list_accounts":
        accounts = get_accounts()
        return {"accounts": accounts, "count": len(accounts)}

    elif name == "get_balance":
        account_id = arguments.get("account_id", "")
        result = get_balance(account_id)
        if result is None:
            return {"error": f"Account not found: {account_id}"}
        return result

    elif name == "list_transactions":
        account_id = arguments.get("account_id")
        txns = get_transactions(account_id)
        return {"transactions": txns, "count": len(txns)}

    elif name == "initiate_payment":
        if DRY_RUN:
            return {
                "status": "dry_run",
                "from_account": arguments.get("from_account"),
                "to_name": arguments.get("to_name"),
                "amount": arguments.get("amount"),
                "note": "Payment NOT initiated (dry-run mode)",
            }

        result = initiate_payment(
            from_account=arguments["from_account"],
            to_name=arguments["to_name"],
            to_iban=arguments["to_iban"],
            amount=arguments["amount"],
            reference=arguments["reference"],
        )
        return {"status": "initiated", "payment": result}

    elif name == "payment_status":
        payment_id = arguments.get("payment_id", "")
        result = get_payment_status(payment_id)
        if result is None:
            return {"error": f"Payment not found: {payment_id}"}
        return result

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_request(request: dict) -> dict:
    """Handle a JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id", 1)

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ai-employee-payment", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}]
                },
            }
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": str(e)},
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }


def main():
    """Read JSON-RPC requests from stdin, write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
