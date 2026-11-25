"""Script para adicionar tabelas de conquistas ao database.py."""
import sys
sys.path.insert(0, '.')

# Read database.py and add the tables
with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tables = '''

-- Conquistas e Achievements
CREATE TABLE IF NOT EXISTS cartas_conquistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conquista TEXT NOT NULL,
    progresso INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    desbloqueada_em TEXT NOT NULL DEFAULT (date('now')),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cartas_conquista_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conquista_id INTEGER NOT NULL,
    desbloqueada INTEGER NOT NULL DEFAULT 0,
    data_desbloqueio TEXT NOT NULL DEFAULT (date('now')),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(conquista_id) REFERENCES cartas_conquistas(id) ON DELETE CASCADE
);

-- Tabela para rastrear progresso em eventos
CREATE TABLE IF NOT EXISTS cartas_eventos_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    evento TEXT NOT NULL,
    progresso INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_cartas_conquista_user ON cartas_conquista_usuario(user_id, conquista_id);
CREATE INDEX IF NOT EXISTS idx_cartas_eventos_user ON cartas_eventos_usuario(user_id);
'''

# Inserir após o marcador
marker = "-- Inventário dedicado ao Laboratório; saldo separado de Almas e Fragmentos da Forja."
if marker in content:
    content = content.replace(marker, new_tables + marker)
    print("✅ Tabelas de conquistas adicionadas ao database.py")
else:
    print("❌ Marker não encontrado")

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
