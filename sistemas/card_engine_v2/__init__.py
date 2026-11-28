"""Isolated Card Engine v2 prototype; not wired into the legacy runtime."""

from .errors import (
    CardEngineError,
    IdempotencyConflict,
    InvalidMatchState,
    InvalidOperation,
    MatchNotFound,
    MigrationChecksumMismatch,
    OutboxStateError,
    PersistenceConflict,
)
from .repository import HandlerResult, OperationReceipt, SQLiteMatchRepository
from .gameplay import ActionDefinition, GameplayResolver, ProtectionProfile
from .targeting import TargetPolicy, build_target_offer, resolve_target_selection
from .alpha_catalog import AlphaCatalog
from .match import AlphaMatchController
from .deck_builder import AlphaDeckBuilder, DeckValidation
from .deck_repository import SQLiteDeckRepository
from .application import AlphaGameApplication, AsyncAlphaGameApplication
from .power import effective_power, metric_resolver_for_weather
from .zones import locate_instance, move_instance_row, transition_instance_zone
from .validation import validate_match_state

__all__ = [
    "ActionDefinition",
    "AlphaCatalog",
    "AlphaDeckBuilder",
    "AlphaGameApplication",
    "AsyncAlphaGameApplication",
    "AlphaMatchController",
    "CardEngineError",
    "GameplayResolver",
    "DeckValidation",
    "HandlerResult",
    "IdempotencyConflict",
    "InvalidMatchState",
    "InvalidOperation",
    "MatchNotFound",
    "MigrationChecksumMismatch",
    "OperationReceipt",
    "OutboxStateError",
    "PersistenceConflict",
    "ProtectionProfile",
    "TargetPolicy",
    "build_target_offer",
    "resolve_target_selection",
    "SQLiteDeckRepository",
    "SQLiteMatchRepository",
    "locate_instance",
    "move_instance_row",
    "transition_instance_zone",
    "validate_match_state",
    "effective_power",
    "metric_resolver_for_weather",
]
