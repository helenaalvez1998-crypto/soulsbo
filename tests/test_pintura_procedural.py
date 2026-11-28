"""Regressões semânticas e visuais do motor procedural de ilustração."""
from __future__ import annotations

import inspect
import unittest

from PIL import Image

from sistemas.cartas import CARTAS_POR_ID
from sistemas import pintura_procedural as pintura

PALETA = ((174, 132, 71), (68, 51, 45), (195, 153, 87), (202, 180, 132))


class ProceduralPaintingTests(unittest.TestCase):
    def _card(self, card_id: str) -> dict:
        return CARTAS_POR_ID[card_id].para_dict()

    def test_renderer_has_no_numpy_dependency(self):
        source = inspect.getsource(pintura)
        self.assertNotIn("import numpy", source.casefold())
        self.assertNotIn("from numpy", source.casefold())

    def test_actual_card_category_and_title_override_internal_id_prefix(self):
        duelista = pintura.analisar_direcao(self._card("arma_duas_luas"))
        monge = pintura.analisar_direcao(self._card("magia_brasa_errante"))
        self.assertEqual(duelista.subject, "agile scout or duelist")
        self.assertEqual(monge.subject, "cleric or preacher")

    def test_special_category_does_not_turn_physical_relics_into_spells(self):
        for card_id in (
            "gwent_especial_medico",
            "gwent_especial_execucao",
            "reliquia_noite_chama",
            "reliquia_lamina_negra",
            "reliquia_algemas_margit",
        ):
            with self.subTest(card_id=card_id):
                direction = pintura.analisar_direcao(self._card(card_id))
                self.assertEqual(direction.subject, "named relic or weapon")

    def test_godfrey_reference_in_event_title_is_not_a_character_portrait(self):
        direction = pintura.analisar_direcao(self._card("gwent_especial_chifre"))
        self.assertEqual(direction.subject, "sonic shockwave")
        self.assertEqual(direction.canonical, "")

    def test_plural_factions_render_as_a_formation(self):
        for card_id in (
            "covenant_lobos_cinza",
            "covenant_sentinelas",
            "covenant_ultimos",
            "covenant_filhos_brasa",
            "covenant_peregrinos_nevoa",
            "covenant_irmandade_ferro",
        ):
            with self.subTest(card_id=card_id):
                self.assertEqual(pintura.analisar_direcao(self._card(card_id)).subject, "battle group")

    def test_canonical_primordials_have_distinct_subjects(self):
        expectations = {
            "chefe_dama_vazio": "canonical ranni",
            "chefe_malenia_lamina_miquella": "canonical malenia",
            "chefe_radahn_flagelo_estrelas": "canonical radahn",
            "chefe_placidusax_lorde_dragao": "canonical placidusax",
            "primordial_origem": "canonical elden beast",
            "primordial_abismo": "primordial entity",
            "primordial_trono": "canonical marika",
            "primordial_eternidade": "canonical maliketh",
        }
        for card_id, expected in expectations.items():
            with self.subTest(card_id=card_id):
                self.assertEqual(pintura.analisar_direcao(self._card(card_id)).subject, expected)

    def test_event_and_environment_are_semantic_not_faction_only(self):
        storm = pintura.analisar_direcao(self._card("gwent_especial_tempestade"))
        frost = pintura.analisar_direcao(self._card("gwent_especial_geada"))
        blessing = pintura.analisar_direcao(self._card("gwent_especial_egide"))
        vow = pintura.analisar_direcao(self._card("gwent_especial_vinculo"))
        self.assertEqual(storm.subject, "storm event")
        self.assertEqual(frost.scene, "frozen highlands")
        self.assertEqual(blessing.subject, "protective blessing")
        self.assertEqual(vow.subject, "ancestral vow")

    def test_special_cards_get_their_own_visual_event_not_a_generic_humanoid(self):
        expectations = {
            "gwent_especial_tempestade": "storm event",
            "gwent_especial_geada": "frost phenomenon",
            "gwent_especial_chifre": "sonic shockwave",
            "gwent_especial_egide": "protective blessing",
            "gwent_especial_vinculo": "ancestral vow",
            "gwent_especial_requiem": "resurrection or summoning",
            "gwent_especial_batedor": "spectral dash",
            "gwent_especial_muralha": "fortification event",
            "elden_especial_podrida": "scarlet bloom",
            "elden_especial_geada": "full moon phenomenon",
        }
        for card_id, expected in expectations.items():
            with self.subTest(card_id=card_id):
                self.assertEqual(pintura.analisar_direcao(self._card(card_id)).subject, expected)

    def test_dragonkin_title_is_a_human_warrior_when_lore_says_warrior(self):
        direction = pintura.analisar_direcao(self._card("magia_trovao_oco"))
        self.assertEqual(direction.subject, "ancient dragon warrior")
        self.assertEqual(direction.scene, "storm-riven sky temple")

    def test_supporting_roles_and_scenes_are_not_forced_into_knight_template(self):
        expectations = {
            "gwent_unidade_intendente": ("artisan or merchant", "crossroads caravan"),
            "gwent_unidade_bibliotecaria": ("scholar or explorer", "academy observatory"),
            "gwent_unidade_gigante": ("giant", "frozen highlands"),
            "gwent_unidade_portaestandarte": ("standard bearer", "sacred golden citadel"),
            "luterano_anjo": ("winged celestial", "forgotten cathedral"),
        }
        for card_id, expected in expectations.items():
            with self.subTest(card_id=card_id):
                direction = pintura.analisar_direcao(self._card(card_id))
                self.assertEqual((direction.subject, direction.scene), expected)


    def test_specific_architectures_for_relics_and_rare_flame_variants(self):
        expectations = {
            "gwent_especial_medico": ("named relic or weapon", "sacred reliquary chamber"),
            "gwent_especial_execucao": ("named relic or weapon", "death sanctum"),
            "gwent_especial_queima": ("flame event", "black flame sanctuary"),
            "elden_especial_loucura": ("flame event", "frenzied flame cathedral"),
            "gwent_especial_vinculo": ("ancestral vow", "ancient crucible sanctuary"),
        }
        for card_id, expected in expectations.items():
            with self.subTest(card_id=card_id):
                direction = pintura.analisar_direcao(self._card(card_id))
                self.assertEqual((direction.subject, direction.scene), expected)

    def test_pair_necromancer_and_second_angel_have_dedicated_archetypes(self):
        self.assertEqual(pintura.analisar_direcao(self._card("gwent_unidade_dupla_veu")).subject,
                         "paired characters")
        self.assertEqual(pintura.analisar_direcao(self._card("gwent_unidade_necromante")).subject,
                         "necromancer")
        self.assertEqual(pintura.analisar_direcao(self._card("luterano_anjo2")).subject,
                         "winged celestial")

    def test_flame_variants_are_visually_distinct_and_deterministic(self):
        cards = [self._card(k) for k in (
            "gwent_especial_queima", "elden_especial_loucura", "elden_especial_chama"
        )]
        images = [pintura.renderizar_pintura_carta(c, (144, 160), PALETA) for c in cards]
        self.assertEqual(len({im.tobytes() for im in images}), 3)
        for card, first in zip(cards, images):
            again = pintura.renderizar_pintura_carta(card, (144, 160), PALETA)
            self.assertEqual(first.tobytes(), again.tobytes())

    def test_no_unsupported_staff_is_added_to_a_monk(self):
        direction = pintura.analisar_direcao(self._card("magia_brasa_errante"))
        self.assertEqual(direction.subject, "cleric or preacher")
        self.assertEqual(direction.equipment, "")

    def test_same_card_and_palette_render_identical_pixels(self):
        card = self._card("chefe_dama_vazio")
        first = pintura.renderizar_pintura_carta(card, (160, 180), PALETA)
        second = pintura.renderizar_pintura_carta(card, (160, 180), PALETA)
        self.assertEqual(first.mode, "RGBA")
        self.assertEqual(first.size, (160, 180))
        self.assertEqual(first.tobytes(), second.tobytes())

    def test_different_card_storyboards_produce_different_art(self):
        relic = pintura.renderizar_pintura_carta(self._card("reliquia_noite_chama"), (144, 160), PALETA)
        event = pintura.renderizar_pintura_carta(self._card("gwent_especial_chifre"), (144, 160), PALETA)
        self.assertNotEqual(relic.tobytes(), event.tobytes())

    def test_renderer_produces_valid_nonempty_rgba_art(self):
        for card_id in (
            "chefe_guardiao_cinzas",
            "chefe_placidusax_lorde_dragao",
            "covenant_lobos_cinza",
            "gwent_especial_medico",
            "primordial_origem",
            "primordial_abismo",
        ):
            with self.subTest(card_id=card_id):
                art = pintura.renderizar_pintura_carta(self._card(card_id), (192, 215), PALETA)
                self.assertIsInstance(art, Image.Image)
                self.assertEqual(art.mode, "RGBA")
                self.assertGreater(len(set(art.get_flattened_data())), 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
