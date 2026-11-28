-- Card Engine v2 isolated alpha migration; documentation export of the Python migration.

-- DO NOT execute this against the legacy Soulsbo database.

-- migration_id: 0001_card_engine_v2_persistence_core

-- checksum_sha256: f1dcda10f4bf29a2b6ffa0e736289ac3544f7f501fc87f87559ac8839973457f

-- Applied by SQLiteMatchRepository inside BEGIN IMMEDIATE.

CREATE TABLE IF NOT EXISTS card_game_schema_migrations (
        migration_id TEXT PRIMARY KEY,
        checksum_sha256 TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        app_version TEXT NOT NULL
    );

CREATE TABLE IF NOT EXISTS card_engine_v2_database_marker (
        marker_id INTEGER PRIMARY KEY CHECK(marker_id = 1),
        engine_id TEXT NOT NULL UNIQUE,
        schema_version INTEGER NOT NULL CHECK(schema_version = 7)
    );

CREATE TABLE IF NOT EXISTS cartas_gwent_matches (
        match_id INTEGER PRIMARY KEY CHECK(match_id > 0),
        schema_version INTEGER NOT NULL CHECK(schema_version = 7),
        status TEXT NOT NULL CHECK(status IN ('active', 'finished')),
        state_json TEXT NOT NULL,
        state_revision INTEGER NOT NULL CHECK(state_revision >= 0),
        event_watermark INTEGER NOT NULL CHECK(event_watermark >= 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

CREATE TABLE IF NOT EXISTS cartas_gwent_match_operations (
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        fingerprint_sha256 TEXT NOT NULL,
        actor_json TEXT NOT NULL,
        expected_revision INTEGER NOT NULL CHECK(expected_revision >= 0),
        revision_before INTEGER NOT NULL CHECK(revision_before >= 0),
        revision_after INTEGER NOT NULL CHECK(revision_after >= 0),
        outcome TEXT NOT NULL CHECK(outcome IN ('applied','partial','blocked','consumed_no_effect','rejected')),
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY(match_id, operation_id),
        FOREIGN KEY(match_id) REFERENCES cartas_gwent_matches(match_id) ON DELETE RESTRICT
    );

CREATE TABLE IF NOT EXISTS cartas_gwent_match_events (
        event_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        sequence INTEGER NOT NULL CHECK(sequence > 0),
        kind TEXT NOT NULL,
        effect_scope TEXT NOT NULL CHECK(effect_scope IN ('direct','reactive','system')),
        source_effect_id TEXT,
        source_instance_id TEXT,
        target_instance_ids_json TEXT NOT NULL,
        caused_by_event_ids_json TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(match_id, sequence),
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT
    );

CREATE TABLE IF NOT EXISTS cartas_gwent_match_rewards (
        reward_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        player_id TEXT NOT NULL,
        reward_key TEXT NOT NULL,
        reward_type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(match_id, reward_key),
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT
    );

CREATE TABLE IF NOT EXISTS cartas_gwent_outbox (
        outbox_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        source_event_id TEXT,
        topic TEXT NOT NULL,
        idempotency_key TEXT NOT NULL UNIQUE,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','in_flight','delivered','dead_letter')),
        attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
        next_attempt_at TEXT NOT NULL,
        lease_until TEXT,
        delivered_at TEXT,
        last_error TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT,
        FOREIGN KEY(source_event_id)
            REFERENCES cartas_gwent_match_events(event_id) ON DELETE RESTRICT
    );

CREATE TABLE IF NOT EXISTS card_engine_v2_legacy_archive (
        archive_id TEXT PRIMARY KEY,
        legacy_match_id INTEGER NOT NULL,
        source_sha256 TEXT NOT NULL,
        source_state_json TEXT NOT NULL,
        target_schema_version INTEGER NOT NULL,
        migration_id TEXT NOT NULL,
        occurrence_mapping_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(legacy_match_id, source_sha256)
    );

CREATE INDEX IF NOT EXISTS idx_cartas_gwent_match_events_match_sequence ON cartas_gwent_match_events(match_id, sequence);

CREATE INDEX IF NOT EXISTS idx_cartas_gwent_outbox_due ON cartas_gwent_outbox(status, next_attempt_at, lease_until);

CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_events_no_update
       BEFORE UPDATE ON cartas_gwent_match_events
       BEGIN SELECT RAISE(ABORT, 'domain event journal is append-only'); END;

CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_events_no_delete
       BEFORE DELETE ON cartas_gwent_match_events
       BEGIN SELECT RAISE(ABORT, 'domain event journal is append-only'); END;

CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_operations_no_update
       BEFORE UPDATE ON cartas_gwent_match_operations
       BEGIN SELECT RAISE(ABORT, 'operation ledger is immutable'); END;

CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_operations_no_delete
       BEFORE DELETE ON cartas_gwent_match_operations
       BEGIN SELECT RAISE(ABORT, 'operation ledger is immutable'); END;
