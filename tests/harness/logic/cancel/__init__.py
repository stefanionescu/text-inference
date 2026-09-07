"""Cancel test logic for verifying request cancellation and recovery.

This package provides the cancel test suite that verifies:
1. Cancel messages abort in-flight requests with a cancelled acknowledgement
2. No spurious messages arrive after cancel acknowledgement
3. Subsequent requests complete successfully after cancellation
4. Multiple concurrent clients work correctly (one cancels, others complete)

Modules:
    handlers: Message handler builders for cancel and recovery phases
    phases: Phase execution functions (cancel, drain, recovery)
    clients: Client flow orchestration (canceling and normal clients)
    output: Result printing functions
    runner: Public test suite entry point
"""

from .runner import CancelSuiteRequest, run_cancel_suite

__all__ = ["CancelSuiteRequest", "run_cancel_suite"]
