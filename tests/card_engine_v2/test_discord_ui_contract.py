"""Static architecture guardrails for the optional discord.py UI layer.

The analysis environment may not have discord.py installed, so this test
checks the real UI source without importing/stubbing the Discord package.
Runtime interaction dispatch must additionally be verified in a bot-enabled
staging environment.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_PATH = ROOT / "cogs" / "card_engine_v2_ui.py"
PANEL_PATH = ROOT / "cogs" / "painel_jogo.py"


class DiscordUiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ui_source = UI_PATH.read_text(encoding="utf-8")
        cls.ui_tree = ast.parse(cls.ui_source)
        cls.panel_source = PANEL_PATH.read_text(encoding="utf-8")

    def test_ui_uses_only_player_safe_match_projection(self):
        calls = [
            node.func.attr
            for node in ast.walk(self.ui_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        self.assertIn("player_view", calls)
        self.assertNotIn("view_match", calls)
        self.assertNotIn("view_match_for_player", calls)

    def test_ui_does_not_query_or_mutate_legacy_database_directly(self):
        calls = [
            node.func.attr
            for node in ast.walk(self.ui_tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        self.assertNotIn("coliseu_listar_exemplares", calls)
        self.assertNotIn("coliseu_adicionar_exemplar", calls)
        self.assertNotIn("coliseu_remover_exemplar", calls)
        self.assertNotIn("execute", calls)
        self.assertNotIn("commit", calls)
        self.assertIn("CardEngineV2DiscordGateway", self.ui_source)

    def test_authenticated_discord_identity_is_used_by_handlers(self):
        self.assertGreaterEqual(self.ui_source.count("interaction.user.id"), 8)
        self.assertIn("authenticated_player_id", self.ui_source)

    def test_existing_jogo_panel_exposes_alpha_entry_point(self):
        self.assertIn('label="Partidas v2 · Alpha"', self.panel_source)
        self.assertIn("AlphaHomeView(service, self.user_id)", self.panel_source)

    def test_resume_flow_uses_persisted_participant_match_list(self):
        self.assertIn('label="Minhas partidas"', self.ui_source)
        self.assertIn("gateway.list_matches", self.ui_source)
        self.assertIn("MyMatchesView", self.ui_source)

    def test_large_target_sets_have_pagination(self):
        self.assertIn("Alvos anteriores", self.ui_source)
        self.assertIn("Próximos alvos", self.ui_source)

    def test_panel_does_not_expose_internal_exception_details(self):
        self.assertIn("logger.exception(\"Falha ao inicializar o painel Card Engine v2 alpha\")", self.panel_source)
        self.assertIn("Não foi possível abrir o Card Engine v2 alpha agora.", self.panel_source)
        self.assertNotIn("str(exc)", self.panel_source)


if __name__ == "__main__":
    unittest.main()
