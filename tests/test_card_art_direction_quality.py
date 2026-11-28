import unittest

from sistemas.direcao_arte_prompts import (
    construir_direcao_visual_carta,
    montar_prompt_mestre,
    pistas_lore_visuais,
)


class CardArtDirectionQualityTests(unittest.TestCase):
    def test_card_name_and_lore_drive_a_specific_storyboard(self):
        card = {
            "nome": "Cavaleiro da Árvore Áurea",
            "descricao": "Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital.",
            "categoria": "Unidade",
            "faccao": "Ordem Áurea",
        }
        brief = construir_direcao_visual_carta(
            card,
            faction_direction="gold and ivory, restrained Erdtree motifs",
        )
        self.assertIn("Cavaleiro da Árvore Áurea", brief)
        self.assertIn(card["descricao"], brief)
        self.assertIn("MOUNTED SUBJECT", brief)
        self.assertIn("PATROL / WATCH", brief)
        self.assertIn("ERDTREE / GOLDEN TREE", brief)
        self.assertIn("ROYAL CAPITAL", brief)
        self.assertIn("gold and ivory", brief)
        self.assertIn("one exact instant", brief)
        self.assertIn("foreground, subject plane and background", brief)
        self.assertIn("motivated key light", brief)

    def test_specific_non_human_or_object_title_is_not_replaced_by_warrior(self):
        card = {
            "nome": "Lâmina do Juramento",
            "lore": "Uma relíquia antiga sela o pacto entre duas casas rivais.",
            "categoria": "Unidade",
            "faccao": "Véu Carmesim",
        }
        brief = construir_direcao_visual_carta(card)
        self.assertIn("a named weapon, relic, spell, place, event or group must not be replaced by a generic warrior", brief)
        self.assertIn("NAMED RELIC / WEAPON", brief)
        self.assertIn("RELIC", brief.upper())

    def test_special_card_visualizes_the_event_not_an_arbitrary_caster(self):
        card = {
            "nome": "Chuva de Cinzas",
            "descricao": "Uma nuvem de cinzas cobre a fileira inimiga e reduz sua visibilidade.",
            "categoria": "Especial",
            "faccao": "Os Esquecidos",
        }
        brief = construir_direcao_visual_carta(card)
        self.assertIn("SPECIAL CARD", brief)
        self.assertIn("exact event, effect, phenomenon", brief)
        self.assertIn("ASH / AFTERMATH", brief)
        self.assertIn("Do not substitute a generic spellcaster portrait", brief)

    def test_both_card_generation_paths_use_the_shared_storyboard(self):
        from sistemas.atelie_coliseu import gerar_prompt_carta_estruturado
        from sistemas.cartas import CARTAS_POR_ID
        from sistemas.prompt_arte_criador import gerar_prompt_arte

        card_id, model = next(iter(CARTAS_POR_ID.items()))
        definition = model.para_dict()
        creator_prompt = gerar_prompt_arte(definition, card_id=card_id)["prompt"]
        coliseum_prompt = gerar_prompt_carta_estruturado(definition)["prompt"]

        for prompt in (creator_prompt, coliseum_prompt):
            self.assertIn("CARD-SPECIFIC ART DIRECTION — SOURCE-LOCKED STORYBOARD", prompt)
            self.assertIn(str(model.nome), prompt)
            self.assertIn("PROFESSIONAL FINISH", prompt)
            self.assertIn("HARD ANTI-GENERIC RULES", prompt)

    def test_lore_cues_are_evidence_based_and_do_not_force_missing_equipment(self):
        cues = pistas_lore_visuais(
            "Sentinela do Portão",
            "O guardião protege a passagem durante a noite.",
        )
        joined = " ".join(cues)
        self.assertIn("PROTECTION / WATCH", joined)
        self.assertNotIn("bow", joined.casefold())
        self.assertNotIn("dragon", joined.casefold())

    def test_master_prompt_includes_storyboard_but_does_not_leak_legacy_fields(self):
        card = {
            "nome": "Guardião da Passagem",
            "descricao": "Um sentinela protege a ponte de pedra durante a tempestade.",
            "categoria": "Unidade",
            "faccao": "Ordem Áurea",
            "raridade": "Rara",
            "fileira": "melee",
            "poder_base": 4,
        }
        prompt = montar_prompt_mestre(
            card=card,
            detail_prompt="COST: 99; MAXIMUM POWER: 99; legacy instruction that must not appear",
        )
        self.assertIn("CARD-SPECIFIC ART DIRECTION — SOURCE-LOCKED STORYBOARD", prompt)
        self.assertIn("Guardião da Passagem", prompt)
        self.assertIn("tempestade", prompt)
        self.assertNotIn("COST: 99", prompt)
        self.assertNotIn("MAXIMUM POWER: 99", prompt)
        self.assertNotIn("legacy instruction that must not appear", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
