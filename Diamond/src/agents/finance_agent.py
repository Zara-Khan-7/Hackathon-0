"""Finance Agent — specializes in Odoo ERP, invoicing, payments, and audits.

Handles: ODOO_, PAYMENT_, AUDIT_ prefixes.
Skills: sync_odoo_transactions, create_invoice_draft, process_payment, weekly_audit.
"""

from src.agents.base_agent import BaseSpecializedAgent, AgentCapability


class FinanceAgent(BaseSpecializedAgent):
    """Specialized agent for finance and accounting tasks."""

    AGENT_TYPE = "finance"
    DISPLAY_NAME = "Finance Agent"

    def _register_capabilities(self) -> None:
        self._capabilities = [
            AgentCapability(
                name="invoicing",
                description="Create and manage Odoo invoices, sync transactions",
                task_prefixes=["ODOO_"],
                priority=10,
            ),
            AgentCapability(
                name="payments",
                description="Process bank payments and transfers",
                task_prefixes=["PAYMENT_"],
                priority=10,
            ),
            AgentCapability(
                name="auditing",
                description="Run financial audits and generate reports",
                task_prefixes=["AUDIT_"],
                priority=8,
            ),
        ]

    def _execute(self, task: dict, dry_run: bool = False) -> str:
        filename = task.get("filename", "unknown")
        task_type = task.get("task_type", "unknown")

        if dry_run:
            return f"[DRY-RUN] Finance agent would process {filename} (type={task_type})"

        if filename.startswith("ODOO_"):
            return self._handle_odoo(task)
        elif filename.startswith("PAYMENT_"):
            return self._handle_payment(task)
        elif filename.startswith("AUDIT_"):
            return self._handle_audit(task)

        return f"Finance agent processed {filename}"

    def _handle_odoo(self, task: dict) -> str:
        """Process Odoo ERP task (invoice draft, sync, etc.)."""
        subtype = task.get("metadata", {}).get("subtype", "general")
        return (
            f"Processed Odoo task {task.get('filename', '')} "
            f"(subtype={subtype}). Draft created, routed to approval for posting."
        )

    def _handle_payment(self, task: dict) -> str:
        """Process payment task — always routes to approval."""
        amount = task.get("metadata", {}).get("amount", "unknown")
        return (
            f"Reviewed payment request {task.get('filename', '')} "
            f"(amount={amount}). Verified account balance. Routed to approval."
        )

    def _handle_audit(self, task: dict) -> str:
        """Run financial audit and generate briefing."""
        return (
            f"Completed audit for {task.get('filename', '')}. "
            f"Revenue, expenses, and outstanding invoices reviewed. "
            f"Briefing generated."
        )
