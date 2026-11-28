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
SITE_HUB_PATH = ROOT / "site_hub.py"


class DiscordUiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ui_source = UI_PATH.read_text(encoding="utf-8")
        cls.ui_tree = ast.parse(cls.ui_source)
        cls.panel_source = PANEL_PATH.read_text(encoding="utf-8")
        cls.site_hub_source = SITE_HUB_PATH.read_text(encoding="utf-8")

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

    def test_jogo_panel_routes_to_the_site_destinations(self):
        self.assertIn("/#arena", self.panel_source)
        self.assertIn("/#deck", self.panel_source)
        self.assertIn("/#market", self.panel_source)
        self.assertIn("/#oficios", self.panel_source)
        self.assertIn("/card-engine-v2", self.panel_source)

    def test_jogo_panel_does_not_duplicate_site_actions(self):
        for obsolete_label in (
            "Minha coleção", "Histórico de drops", "Estatísticas",
            "Forja no site", "Receitas de Linhagem", "Transmutação",
            "Rituais Ancestrais", "Biblioteca de Cartas", "Cartas Geradas",
            "Ateliê de Arte",
        ):
            self.assertNotIn(obsolete_label, self.panel_source)
        self.assertNotIn('label="Forja"', self.panel_source)
        self.assertIn('label="Mercado e drops"', self.panel_source)
        self.assertIn('label="Ofícios"', self.panel_source)
        self.assertIn('label="Atualizar resumo"', self.panel_source)
        self.assertIn('label="Ritual de Convergência"', self.panel_source)
        self.assertIn("coliseu_convergir_exemplares", self.panel_source)

    def test_site_forge_dispatches_lapidation_and_ascension_separately(self):
        self.assertIn('if action == "lapidar":', self.site_hub_source)
        self.assertIn("coliseu_aprimorar_exemplar(uid, exemplar_id)", self.site_hub_source)
        self.assertIn('elif action == "ascender":', self.site_hub_source)
        self.assertIn("coliseu_evoluir_exemplar(uid, exemplar_id)", self.site_hub_source)

    def test_resume_flow_uses_persisted_participant_match_list(self):
        self.assertIn('label="Minhas partidas"', self.ui_source)
        self.assertIn("gateway.list_matches", self.ui_source)
        self.assertIn("MyMatchesView", self.ui_source)

    def test_large_target_sets_have_pagination(self):
        self.assertIn("Alvos anteriores", self.ui_source)
        self.assertIn("Próximos alvos", self.ui_source)

    def test_panel_opens_the_site_alpha_instead_of_duplicating_its_discord_ui(self):
        self.assertIn('label="Card Engine v2 · Alpha"', self.panel_source)
        self.assertIn("/card-engine-v2", self.panel_source)
        self.assertNotIn("AlphaHomeView", self.panel_source)
        self.assertNotIn("str(exc)", self.panel_source)


if __name__ == "__main__":
    unittest.main()
