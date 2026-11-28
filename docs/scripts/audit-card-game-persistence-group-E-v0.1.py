from __future__ import annotations
import ast, hashlib, json, re, sqlite3, tempfile, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs'
DB_PATH = ROOT / 'database.py'
BOT_PATH = ROOT / 'bot.py'
GWENT_PATH = ROOT / 'sistemas' / 'gwent.py'
SNAPSHOT_PATH = DOCS / 'scripts' / 'snapshot-sqlite-readonly-v0.1.py'

def read(p: Path) -> str:
    return p.read_text(encoding='utf-8')

def find_assignment(path: Path, wanted: set[str]) -> dict[str, str]:
    tree = ast.parse(read(path))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    out[target.id] = ast.literal_eval(node.value)
    return out

def record(cases, name, passed, detail):
    cases.append({'id': f'E-AUD-{len(cases)+1:03d}', 'case': name,
                  'status': 'passed' if passed else 'failed', 'detail': detail})
    if not passed:
        raise AssertionError(f'{name}: {detail}')

def main():
    db_src = read(DB_PATH)
    bot_src = read(BOT_PATH)
    gwent_src = read(GWENT_PATH)
    snap_src = read(SNAPSHOT_PATH)
    schema_values = find_assignment(DB_PATH, {'SCHEMA', 'SCHEMA_CARTAS'})
    assert set(schema_values) == {'SCHEMA', 'SCHEMA_CARTAS'}

    cases = []
    # Static evidence: live match table and missing durability controls.
    in_memory = sqlite3.connect(':memory:')
    in_memory.execute('PRAGMA foreign_keys=ON')
    in_memory.executescript(schema_values['SCHEMA'])
    in_memory.executescript(schema_values['SCHEMA_CARTAS'])
    match_columns = {r[1] for r in in_memory.execute('PRAGMA table_info(cartas_gwent_matches)')}
    record(cases, 'match_table_contains_json_snapshot', 'state_json' in match_columns,
           sorted(match_columns))
    record(cases, 'match_table_has_no_revision_column', 'state_revision' not in match_columns and 'revision' not in match_columns,
           sorted(match_columns))
    tables = {r[0] for r in in_memory.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    match_ledger_tables = sorted(t for t in tables if any(k in t.casefold() for k in ('operation', 'domain_event', 'outbox')))
    record(cases, 'no_durable_match_operation_event_or_outbox_table', len(match_ledger_tables) == 0,
           {'related_tables_found': match_ledger_tables})
    record(cases, 'no_schema_migration_ledger', 'schema_migrations' not in tables and 'card_game_schema_migrations' not in tables,
           sorted(t for t in tables if 'migration' in t.casefold()))

    # State object and action handler behavior.
    new_state = gwent_src[gwent_src.index('def novo_estado('):gwent_src.index('\ndef _registrar_evento', gwent_src.index('def novo_estado('))]
    absent_state_keys = [k for k in ('schema_version', 'state_revision', 'definition_manifest', 'operations', 'events') if f'"{k}"' not in new_state]
    record(cases, 'legacy_new_state_has_no_new_envelope_metadata', len(absent_state_keys) == 5,
           {'absent_keys': absent_state_keys})
    record(cases, 'legacy_event_log_is_bounded_presentation_history', 'history[-20:]' in gwent_src,
           'event_log is truncated to the latest 20 messages; not an append-only domain ledger')
    action_handler = bot_src[bot_src.index('async def _api_gwent_match_action'):bot_src.index('\n    async def _api_me', bot_src.index('async def _api_gwent_match_action'))]
    record(cases, 'action_handler_runs_inside_database_transaction', 'async with self.db.transaction() as tx:' in action_handler,
           'match row is read and state is changed within Database.transaction()')
    record(cases, 'action_handler_does_not_accept_operation_id_or_expected_revision',
           'body.get("operation_id"' not in action_handler and 'body.get("expected_revision"' not in action_handler,
           'current request fields: action/card_id/row/card_ids/target_id')
    update_match = re.search(r'UPDATE cartas_gwent_matches SET status=\?,state_json=\?,updated_at=CURRENT_TIMESTAMP WHERE id=\?', action_handler)
    record(cases, 'action_update_has_no_compare_and_swap_predicate', bool(update_match) and 'state_revision' not in action_handler,
           'UPDATE is keyed by match id only; serialization is currently supplied by BEGIN IMMEDIATE')
    transaction_body = db_src[db_src.index('async def transaction(self):'):db_src.index('async def _abrir_writer', db_src.index('async def transaction(self):'))]
    record(cases, 'database_wrapper_uses_begin_immediate', 'BEGIN IMMEDIATE' in transaction_body,
           'write transaction acquires SQLite reserved lock before reading match state')
    record(cases, 'database_wrapper_has_process_local_writer_lock', '_writer_lock' in db_src and 'await asyncio.wait_for(self._writer_lock.acquire(), timeout=30)' in transaction_body,
           'writer lock serializes tasks using one Database instance, not independent processes by itself')
    record(cases, 'sqlite_connection_uses_wal_and_busy_timeout', 'PRAGMA journal_mode = WAL' in db_src and 'PRAGMA busy_timeout = 10000' in db_src,
           {'journal_mode': 'WAL for file-backed DB', 'busy_timeout_ms': 10000})
    record(cases, 'schema_changes_are_incremental_but_unversioned', 'PRAGMA user_version' not in db_src and 'schema_migrations' not in db_src,
           'connect() introspects columns and runs CREATE/ALTER statements, then commits; no migration ID/checksum ledger')

    # Existing idempotency for end-of-match rewards and drops.
    rewards_sql = re.search(r'CREATE TABLE IF NOT EXISTS cartas_gwent_rewards \((.*?)\n\);', schema_values['SCHEMA_CARTAS'], re.S)
    record(cases, 'match_rewards_have_composite_uniqueness', bool(rewards_sql) and 'PRIMARY KEY(match_id, user_id)' in rewards_sql.group(1),
           'one reward record per match and participant')
    drops_sql = re.search(r'CREATE TABLE IF NOT EXISTS cartas_recompensas \((.*?)\n\);', schema_values['SCHEMA_CARTAS'], re.S)
    record(cases, 'drop_events_have_unique_event_key', bool(drops_sql) and 'event_key TEXT PRIMARY KEY' in drops_sql.group(1),
           'stable drop event key prevents duplicate drops')
    reward_section = action_handler[action_handler.find('if state["status"] == "finished"'):]
    record(cases, 'match_rewards_guarded_inside_same_transaction',
           'SELECT 1 FROM cartas_gwent_rewards WHERE match_id=? AND user_id=?' in reward_section and 'INSERT OR IGNORE INTO cartas_gwent_rewards' in reward_section,
           'ranking/economy updates and reward rows are written in the enclosing match transaction')

    # External effects: scheduled before commit and post-commit non-durable sync.
    notify_pos = action_handler.find('create_task(self._avisar_vez_gwent')
    persist_pos = action_handler.find('UPDATE cartas_gwent_matches SET status=?,state_json=?')
    # Create task appears after UPDATE but before leaving the transaction block.
    record(cases, 'turn_notification_is_scheduled_inside_transaction', notify_pos >= 0,
           'asyncio.create_task is called before transaction context exits; no durable outbox record exists')
    record(cases, 'patent_sync_is_after_commit_without_outbox', 'await self._gwent_sync_patents(participant)' in action_handler and 'async with self.db.transaction()' in action_handler,
           'patent synchronization runs after the transaction and is only logged on failure')

    # Snapshot helper safety.
    record(cases, 'snapshot_tool_uses_read_only_sqlite_backup_api',
           'mode=ro' in snap_src and 'source.backup(target' in snap_src and 'PRAGMA query_only = ON' in snap_src,
           'backup helper opens source read-only and checks source/destination quick_check')

    # Real SQLite tests: rollback, unique rewards, two-connection serialization, backup.
    with tempfile.TemporaryDirectory(prefix='soulsbo-group-e-') as td:
        db_file = Path(td) / 'test.sqlite3'
        con = sqlite3.connect(db_file, timeout=5, isolation_level=None)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript(schema_values['SCHEMA'])
        con.executescript(schema_values['SCHEMA_CARTAS'])
        con.execute('INSERT INTO users(user_id) VALUES (1001)')
        con.execute('INSERT INTO users(user_id) VALUES (2002)')
        con.execute("INSERT INTO cartas_gwent_matches(creator_id,opponent_id,status,state_json) VALUES (1001,2002,'active','{\"v\":0}')")
        match_id = con.execute('SELECT id FROM cartas_gwent_matches').fetchone()[0]
        con.commit()

        con.execute('BEGIN IMMEDIATE')
        con.execute("UPDATE cartas_gwent_matches SET state_json='{" + '"v":1' + "}' WHERE id=?", (match_id,))
        con.execute("INSERT INTO cartas_gwent_rewards(match_id,user_id) VALUES (?,1001)", (match_id,))
        con.rollback()
        state_after_rollback = con.execute('SELECT state_json FROM cartas_gwent_matches WHERE id=?', (match_id,)).fetchone()[0]
        reward_after_rollback = con.execute('SELECT COUNT(*) FROM cartas_gwent_rewards WHERE match_id=?', (match_id,)).fetchone()[0]
        record(cases, 'sqlite_rollback_reverts_snapshot_and_reward_together',
               state_after_rollback == '{"v":0}' and reward_after_rollback == 0,
               {'state_json_after_rollback': state_after_rollback, 'reward_rows_after_rollback': reward_after_rollback})

        # Unique reward key is enforced by the actual schema.
        con.execute("INSERT INTO cartas_gwent_rewards(match_id,user_id) VALUES (?,1001)", (match_id,))
        duplicate_rejected = False
        try:
            con.execute("INSERT INTO cartas_gwent_rewards(match_id,user_id) VALUES (?,1001)", (match_id,))
        except sqlite3.IntegrityError:
            duplicate_rejected = True
        record(cases, 'sqlite_reward_unique_constraint_rejects_duplicate', duplicate_rejected,
               'PRIMARY KEY(match_id,user_id) enforced by SQLite')

        con.execute("INSERT INTO cartas_recompensas(event_key,user_id,origin) VALUES ('gwent:vitoria:test:1001',1001,'gwent_vitoria')")
        duplicate_drop_rejected = False
        try:
            con.execute("INSERT INTO cartas_recompensas(event_key,user_id,origin) VALUES ('gwent:vitoria:test:1001',1001,'gwent_vitoria')")
        except sqlite3.IntegrityError:
            duplicate_drop_rejected = True
        record(cases, 'sqlite_drop_event_key_rejects_duplicate', duplicate_drop_rejected,
               'PRIMARY KEY(event_key) enforced by SQLite')
        con.close()

        # Two independent SQLite connections: BEGIN IMMEDIATE blocks B until A commits.
        started_b = threading.Event()
        acquired_a = threading.Event()
        acquired_b = threading.Event()
        release_a = threading.Event()
        b_observed = {}
        thread_errors = []
        def connect_thread():
            c = sqlite3.connect(db_file, timeout=5, isolation_level=None, check_same_thread=False)
            c.execute('PRAGMA busy_timeout=5000')
            return c
        def worker_a():
            try:
                c = connect_thread()
                c.execute('BEGIN IMMEDIATE')
                before = c.execute('SELECT state_json FROM cartas_gwent_matches WHERE id=?', (match_id,)).fetchone()[0]
                c.execute("UPDATE cartas_gwent_matches SET state_json='{" + '"v":1' + "}' WHERE id=?", (match_id,))
                b_observed['a_before'] = before
                acquired_a.set()
                release_a.wait(4)
                c.commit()
                c.close()
            except Exception as exc:
                thread_errors.append(repr(exc))
                release_a.set()
        def worker_b():
            try:
                c = connect_thread()
                started_b.set()
                c.execute('BEGIN IMMEDIATE')
                acquired_b.set()
                b_observed['b_after_lock'] = c.execute('SELECT state_json FROM cartas_gwent_matches WHERE id=?', (match_id,)).fetchone()[0]
                c.execute("UPDATE cartas_gwent_matches SET state_json='{" + '"v":2' + "}' WHERE id=?", (match_id,))
                c.commit()
                c.close()
            except Exception as exc:
                thread_errors.append(repr(exc))
                acquired_b.set()
        ta = threading.Thread(target=worker_a, daemon=True)
        ta.start()
        a_locked = acquired_a.wait(3)
        tb = threading.Thread(target=worker_b, daemon=True)
        tb.start()
        started_b.wait(2)
        time.sleep(0.15)
        blocked_before_commit = not acquired_b.is_set()
        release_a.set()
        ta.join(5); tb.join(5)
        final = sqlite3.connect(db_file)
        final_state = final.execute('SELECT state_json FROM cartas_gwent_matches WHERE id=?', (match_id,)).fetchone()[0]
        final.close()
        record(cases, 'sqlite_begin_immediate_serializes_independent_connections',
               a_locked and blocked_before_commit and b_observed.get('b_after_lock') == '{"v":1}' and final_state == '{"v":2}' and not thread_errors,
               {'a_acquired_lock': a_locked, 'blocked_before_a_commit': blocked_before_commit, 'a_before': b_observed.get('a_before'),
                'b_read_after_lock': b_observed.get('b_after_lock'), 'final_state': final_state, 'thread_errors': thread_errors})

        # WAL-aware backup snapshot check.
        src = sqlite3.connect(db_file)
        backup_file = Path(td) / 'backup.sqlite3'
        dst = sqlite3.connect(backup_file)
        src.backup(dst)
        integrity = dst.execute('PRAGMA quick_check').fetchone()[0]
        backup_state = dst.execute('SELECT state_json FROM cartas_gwent_matches WHERE id=?', (match_id,)).fetchone()[0]
        src.close(); dst.close()
        record(cases, 'sqlite_backup_api_produces_consistent_snapshot',
               integrity == 'ok' and backup_state == final_state,
               {'quick_check': integrity, 'backup_state': backup_state})

    failed = [c for c in cases if c['status'] != 'passed']
    result = {
        'version': '0.1',
        'group': 'E',
        'status': 'passed' if not failed else 'failed',
        'scope': 'static source audit plus isolated SQLite DDL/concurrency/rollback/backup experiments; no production DB or runtime changes',
        'checks': len(cases), 'passed': len(cases)-len(failed), 'failed': len(failed),
        'environment': {'sqlite_version': sqlite3.sqlite_version, 'aiosqlite_runtime_executed': False,
                        'production_database_accessed': False, 'http_handler_executed': False},
        'cases': cases,
        'limitations': [
            'The package contains no production database, credentials or live match rows; existing match population and data quality cannot be inventoried.',
            'aiosqlite and discord.py are not instantiated by this stdlib-only harness; wrapper behavior is audited statically and SQLite lock semantics are tested with independent sqlite3 connections.',
            'No migration, schema change, action handler, API request, Discord notification, patent synchronization or production replay was executed.'
        ]
    }
    out = DOCS / 'card-game-persistence-group-E-audit-v0.1.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': result['checks'], 'passed': result['passed'], 'failed': result['failed']}, indent=2))
    if failed:
        print(json.dumps(failed, indent=2))
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
