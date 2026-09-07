"""WebSocket message type handlers for the inference server.

This package provides handlers for different WebSocket message types:

turn.py:
    Unified public entrypoint for both 'start' and 'message' turn commands.

start.py:
    Session bootstrap for the initial start payload.

message.py:
    Message-turn planning for follow-up user turns.

dispatch.py:
    Execution path routing for validated turn plans.

history.py:
    Shared history seeding and user-utterance normalization.

sampling.py:
    Shared sampling parameter extraction.

cancel.py:
    Handles request cancellation during streaming. Aborts the
    active generation request and cleans up state.

validators.py:
    Input validation utilities shared across message handlers.
    Validates sampling parameters, token limits, and field formats.

Import from submodules directly to avoid circular imports:
    from src.messages.turn import handle_turn_message
"""
