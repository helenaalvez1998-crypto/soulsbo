#!/usr/bin/env python3
"""Regressions for rarity-as-classification UI across the site."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

class SiteRarityClassificationUITests(unittest.TestCase):
    def read(self, name):
        return (SITE / name).read_text(encoding="utf-8")

    def test_main_card_ui_has_no_rarity_potency_label_or_scale(self):
        source = self.read("app.js").casefold()
        for forbidden in (
            "potência da raridade", "potencia da raridade", "rarity_power",
            "raritypower", "v54-rarity-power", "v54-card-rarity-line",
            "gwent-rarity-potency", "raritybudget", "rarity potency",
        ):
            self.assertNotIn(forbidden, source)

    def test_home_card_details_have_no_numeric_rarity_score(self):
        source = self.read("index.html").casefold()
        self.assertNotIn("raritypot", source)
        self.assertNotIn("cd-rarity-power", source)
        self.assertNotIn("potência da raridade", source)
        self.assertNotIn("potencia da raridade", source)

    def test_forge_no_longer_renders_rarity_potency(self):
        source = self.read("forja.html").casefold()
        for forbidden in ("potência da raridade", "potencia da raridade", "rarity-power", "potencia_raridade", "/ 6"):
            self.assertNotIn(forbidden, source)

    def test_styles_do_not_recreate_obsolete_potency_widgets(self):
        combined = "\n".join(self.read(name).casefold() for name in ("style.css", "narabot-visual-v59.css"))
        for forbidden in (".v54-rarity-power", ".v54-card-rarity-line", ".cd-rarity-power", ".gwent-rarity-potency"):
            self.assertNotIn(forbidden, combined)

    def test_rarity_classification_is_preserved_in_card_ui(self):
        app = self.read("app.js")
        home = self.read("index.html")
        forge = self.read("forja.html")
        self.assertIn("v51-card-rarity", app)
        self.assertIn("card.raridade", app)
        self.assertIn("c.raridade", home)
        self.assertIn("x.rarity", forge)
        self.assertIn("Caminho de raridade", home)

    def test_art_prompts_do_not_request_visible_rarity_potency(self):
        creator = (ROOT / "sistemas" / "prompt_arte_criador.py").read_text(encoding="utf-8")
        atelier = (ROOT / "sistemas" / "atelie_coliseu.py").read_text(encoding="utf-8")
        self.assertNotIn("RARITY POTENCY (separate field)", creator)
        self.assertNotIn("use RARITY POTENCY", atelier)
        self.assertIn("Do not print or depict rarity potency", creator)
        self.assertIn("Do not create a rarity-potency field", atelier)

    def test_required_artwork_fields_exclude_internal_rarity_metadata(self):
        atelier = (ROOT / "sistemas" / "atelie_coliseu.py").read_text(encoding="utf-8").casefold()
        start = atelier.index("complete collectible card — strict output rules")
        end = atelier.index('""".strip()', start)
        required_block = atelier[start:end]
        self.assertIn("base power, maximum power", required_block)
        self.assertNotIn("rarity potency", required_block)
        self.assertIn("legacy rarity-potency metadata is internal only", required_block)

    def test_v2_site_api_does_not_serialize_rarity_potency(self):
        hub = (ROOT / "site_hub.py").read_text(encoding="utf-8").casefold()
        self.assertIn('data["definition"].pop("potencia_raridade", none)', hub)
        self.assertIn('definition.pop("potencia_raridade", none)', hub)
        self.assertNotIn('"potencia_raridade": int(rarity_effect_budget', hub)

    def test_legacy_event_log_does_not_expose_rarity_budget_text(self):
        app = self.read("app.js").casefold()
        self.assertIn("function gwentpubliceventtext(value)", app)
        self.assertIn("efeito adicional da carta aplicado.", app)
        self.assertIn("gwentpubliceventtext(item)", app)
        self.assertIn("gwentpubliceventtext(data.last_event", app)

    def test_generated_card_prompt_has_no_visible_rarity_potency_field(self):
        from sistemas.cartas import CARTAS_POR_ID
        from sistemas.prompt_arte_criador import gerar_prompt_arte

        card_id = next(iter(CARTAS_POR_ID))
        card = CARTAS_POR_ID[card_id]
        result = gerar_prompt_arte(card.para_dict(), card_id=card_id)
        prompt = result["prompt"].casefold()
        self.assertNotRegex(prompt, r"rarity potency\s*[:=]\s*\d")
        self.assertNotIn("potência da raridade", prompt)
        self.assertNotIn("potencia da raridade", prompt)
        self.assertNotIn("0–6 rarity", prompt)

if __name__ == "__main__":
    unittest.main(verbosity=2)
