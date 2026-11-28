"""Domain and persistence errors for the isolated Card Engine v2 prototype."""


class CardEngineError(Exception):
    """Base exception for the isolated engine."""


class MatchNotFound(CardEngineError):
    """Raised when a match does not exist in the v2 repository."""


class InvalidMatchState(CardEngineError):
    """Raised when a match envelope violates v0.7 invariants."""


class InvalidOperation(CardEngineError):
    """Raised when an operation request is malformed."""


class IdempotencyConflict(CardEngineError):
    """An operation_id was reused with a different canonical request."""


class PersistenceConflict(CardEngineError):
    """The match revision changed before the compare-and-swap update."""


class MigrationChecksumMismatch(CardEngineError):
    """A migration id was previously applied with a different checksum."""


class OutboxStateError(CardEngineError):
    """An outbox item cannot make the requested state transition."""
