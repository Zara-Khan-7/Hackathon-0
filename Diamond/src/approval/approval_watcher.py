"""HITL Approval Watcher — monitors Pending_Approval/ and prompts user in terminal.

On approval: moves file to Approved/, creates EXECUTE_*.md in Needs_Action/
On rejection: moves file to Rejected/
On modify: opens content for editing, then re-prompts
"""

import argparse
import signal
import sys
import time
from pathlib import Path

from src.utils import frontmatter
from src.utils.file_ops import (
    get_folder,
    list_md_files,
    safe_move,
    create_task_file,
)
from src.utils.logger import log_action, log_error

try:
    from colorama import init, Fore, Style
    init()
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


class ApprovalWatcher:
    """Watches Pending_Approval/ and prompts user for decisions."""

    def __init__(self, poll_interval: int = 5):
        self.poll_interval = poll_interval
        self._running = True
        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        print(f"\n{YELLOW}Approval watcher shutting down...{RESET}")
        self._running = False

    def _display_item(self, filepath: Path) -> tuple[dict, str]:
        """Display an approval item and return (metadata, body)."""
        metadata, body = frontmatter.read_file(filepath)

        print(f"\n{'='*60}")
        print(f"{BOLD}{CYAN}APPROVAL REQUEST: {filepath.name}{RESET}")
        print(f"{'='*60}")

        if metadata:
            print(f"\n{BOLD}Metadata:{RESET}")
            for key, value in metadata.items():
                print(f"  {key}: {value}")

        print(f"\n{BOLD}Content:{RESET}")
        print(body)
        print(f"\n{'='*60}")

        return metadata, body

    def _prompt_decision(self) -> str:
        """Prompt user for approval decision."""
        print(f"\n{BOLD}Decision:{RESET}")
        print(f"  {GREEN}[A] Approve{RESET} — Execute this action")
        print(f"  {RED}[R] Reject{RESET}  — Cancel this action")
        print(f"  {YELLOW}[M] Modify{RESET}  — Edit before approving")
        print(f"  {CYAN}[S] Skip{RESET}    — Decide later")
        print()

        while True:
            choice = input(f"{BOLD}Your choice (A/R/M/S): {RESET}").strip().upper()
            if choice in ("A", "R", "M", "S"):
                return choice
            print(f"{RED}Invalid choice. Please enter A, R, M, or S.{RESET}")

    def _handle_approve(self, filepath: Path, metadata: dict, body: str) -> None:
        """Approve: move to Approved/, create EXECUTE task in Needs_Action/."""
        # Move original to Approved/
        approved_path = safe_move(filepath, "Approved")
        log_action("Approved", filepath.name, "approval")

        # Create execution task in Needs_Action/
        exec_metadata = {
            "type": "execute",
            "source_approval": filepath.name,
            "approved_file": str(approved_path.name),
            "priority": metadata.get("priority", "medium"),
            "status": "pending",
            "requires_approval": False,
        }

        # Copy relevant metadata
        for key in ("subtype", "from", "subject", "original_task"):
            if key in metadata:
                exec_metadata[key] = metadata[key]

        exec_body = f"# Execute Approved Action\n\n"
        exec_body += f"**Approved from:** {filepath.name}\n"
        exec_body += f"**Approved file:** {approved_path.name}\n\n"
        exec_body += f"## Original Content\n\n{body}\n"

        task_name = filepath.stem.replace("APPROVE_", "")
        exec_path = create_task_file("Needs_Action", "EXECUTE", task_name, exec_metadata, exec_body)
        log_action("Created execution task", exec_path.name, "approval")

        print(f"\n{GREEN}Approved! Execution task created: {exec_path.name}{RESET}")

    def _handle_reject(self, filepath: Path) -> None:
        """Reject: move to Rejected/."""
        safe_move(filepath, "Rejected")
        log_action("Rejected", filepath.name, "approval")
        print(f"\n{RED}Rejected. Moved to Rejected/{RESET}")

    def _handle_modify(self, filepath: Path, metadata: dict, body: str) -> tuple[dict, str]:
        """Modify: let user edit the body, then re-prompt."""
        print(f"\n{YELLOW}Enter modified content (type 'END' on a new line when done):{RESET}")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)

        new_body = "\n".join(lines)
        if new_body.strip():
            frontmatter.write_file(filepath, metadata, new_body)
            log_action("Modified", filepath.name, "approval")
            print(f"\n{YELLOW}Content updated. Re-prompting...{RESET}")
            return metadata, new_body
        else:
            print(f"\n{YELLOW}No changes made.{RESET}")
            return metadata, body

    def process_item(self, filepath: Path) -> None:
        """Process a single approval item."""
        metadata, body = self._display_item(filepath)

        while True:
            decision = self._prompt_decision()

            if decision == "A":
                self._handle_approve(filepath, metadata, body)
                break
            elif decision == "R":
                self._handle_reject(filepath)
                break
            elif decision == "M":
                metadata, body = self._handle_modify(filepath, metadata, body)
                # Loop back to re-prompt
            elif decision == "S":
                print(f"\n{CYAN}Skipped. Will ask again next cycle.{RESET}")
                break

    def poll_once(self) -> int:
        """Check for pending approvals and prompt for each."""
        files = list_md_files("Pending_Approval")
        if not files:
            return 0

        print(f"\n{BOLD}{YELLOW}Found {len(files)} pending approval(s){RESET}")

        processed = 0
        for filepath in files:
            if not self._running:
                break
            self.process_item(filepath)
            processed += 1

        return processed

    def run(self, once: bool = False) -> None:
        """Main loop — watch for pending approvals."""
        print(f"{BOLD}{CYAN}Approval Watcher started. Watching Pending_Approval/{RESET}")
        print(f"Press Ctrl+C to stop.\n")

        while self._running:
            count = self.poll_once()

            if once:
                if count == 0:
                    print("No pending approvals.")
                break

            time.sleep(self.poll_interval)

        print(f"\n{YELLOW}Approval watcher stopped.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="HITL Approval Watcher")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval (seconds)")
    args = parser.parse_args()

    watcher = ApprovalWatcher(poll_interval=args.interval)
    watcher.run(once=args.once)


if __name__ == "__main__":
    main()
