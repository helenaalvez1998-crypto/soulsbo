"""Catálogo e regras puras do Cartas do Coliseu.

Todas as artes usam símbolos e geometria original; nenhum recurso visual de jogos
proprietários é incorporado ao catálogo.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from levels import PATENTES

VERSAO_ARTES = 32


RARIDADES = ("Comum", "Rara", "Épica", "Lendária", "Mítica", "Primordial", "Singular")
PESOS_RARIDADE = {"Comum": 69.47, "Rara": 22.02, "Épica": 7.01, "Lendária": 1.00, "Mítica": 0.50, "Primordial": 0.0, "Singular": 0.0}
CUSTO_RARIDADE = {"Comum": 1, "Rara": 2, "Épica": 3, "Lendária": 4, "Mítica": 5, "Primordial": 6, "Singular": 0}
FAIXA_PODER = {
    "Comum": (3, 5),
    "Rara": (4, 6),
    "Épica": (5, 7),
    "Lendária": (6, 8),
    "Mítica": (8, 9),
    "Primordial": (8, 9),
    "Singular": (8, 10),
}
ALMAS_DUPLICATA = {"Comum": 5, "Rara": 15, "Épica": 40, "Lendária": 100, "Mítica": 180, "Primordial": 250, "Singular": 0}
BONUS_EVOLUCAO_FRAGMENTOS = {"Comum": 20, "Rara": 40, "Épica": 80, "Lendária": 160}
CUSTO_APRIMORAMENTO_ALMAS = {"Comum": 10, "Rara": 20, "Épica": 40, "Lendária": 80, "Mítica": 150, "Primordial": 250}


def limite_poder_modelo(carta: "Carta") -> int:
    """Teto individual do modelo: parte do poder-base e nunca ultrapassa 12."""
    if str(getattr(carta, "categoria", "")).casefold() == "especial":
        return 0
    return min(12, max(5, int(getattr(carta, "poder", 1)) + 6))


def faixa_poder_exemplar(carta: "Carta", raridade: str) -> tuple[int, int]:
    """Faixa inicial da raridade limitada pelo teto próprio do modelo."""
    if str(getattr(carta, "categoria", "")).casefold() == "especial":
        return (0, 0)
    minimo, maximo = FAIXA_PODER.get(str(raridade), FAIXA_PODER["Comum"])
    maximo = min(int(maximo), limite_poder_modelo(carta))
    minimo = min(int(minimo), maximo)
    return (minimo, maximo)
CUSTO_FORJA = {"Comum": 0, "Rara": 0, "Épica": 0, "Lendária": 0, "Mítica": 0, "Primordial": 0, "Singular": 0}
PRECO_PACOTE_FOGUEIRA = 120
CARTAS_POR_PACOTE = 3
PITY_CARTAS = 10

# Habilidades comuns: efeitos situacionais que permitem montar decks com estilos diferentes.
# As cinco habilidades Primordiais ficam separadas porque cada uma pertence a uma carta única.
HABILIDADES_COMUNS = (
    "primeira_luz", "retaliacao", "impeto", "ultimo_folego", "contragolpe",
    "encadeamento", "adaptacao", "sangue_frio", "instinto", "precisao",
    "drenagem", "cacador_arcano", "quebra_ritmo",
)
HABILIDADES_PRIMORDIAIS = (
    "lei_primeva", "decreto_soberano", "olho_tempestade", "fome_abismo", "paradoxo_eterno",
)

HABILIDADES: dict[str, dict[str, str]] = {
    "primeira_luz": {"nome": "Graça Dourada", "texto": "Na primeira rodada, ganha +1 de poder ao entrar em campo."},
    "retaliacao": {"nome": "Retaliação dos Semideuses", "texto": "Ganha +1 de poder quando sua pontuação total é menor que a do adversário."},
    "impeto": {"nome": "Ímpeto do Lorde", "texto": "Ganha +1 de poder quando sua pontuação total é maior que a do adversário."},
    "ultimo_folego": {"nome": "Último Suspiro", "texto": "Na terceira rodada, ganha +1 de poder ao entrar em campo."},
    "contragolpe": {"nome": "Contragolpe", "texto": "Ganha +2 de poder quando sua pontuação total é menor que a do adversário."},
    "encadeamento": {"nome": "Postura Encadeada", "texto": "Ganha +2 de poder se for jogada na mesma fileira que sua última unidade."},
    "adaptacao": {"nome": "Passo do Peregrino", "texto": "Ganha +1 de poder se for jogada em uma fileira diferente da sua última unidade."},
    "sangue_frio": {"nome": "Concentração", "texto": "Ganha +2 de poder quando os dois jogadores estão com a mesma pontuação."},
    "instinto": {"nome": "Instinto de Caçador", "texto": "Ganha +2 de poder quando sua pontuação total é menor que a do adversário."},
    "precisao": {"nome": "Mira Cariana", "texto": "Ganha +1 de poder ao entrar na fileira de Longa Distância."},
    "drenagem": {"nome": "Selo Enfraquecedor", "texto": "Diminui em 1 o bônus dos inimigos, até o mínimo de -2."},
    "cacador_arcano": {"nome": "Caçador de Feitiços", "texto": "Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero."},
    "quebra_ritmo": {"nome": "Ruptura de Postura", "texto": "Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior."},
    # Efeitos exclusivos: somente a respectiva Primordial pode utilizá-los.
    "lei_primeva": {"nome": "Lei Primeva", "texto": "Recebe +2 de poder ao entrar na primeira rodada."},
    "decreto_soberano": {"nome": "Decreto Soberano", "texto": "Reduz em 2 o bônus de todas as unidades inimigas, até o limite de -2."},
    "olho_tempestade": {"nome": "Olho da Tempestade", "texto": "Recebe +2 quando sua fileira estiver sob efeito climático."},
    "fome_abismo": {"nome": "Fome do Abismo", "texto": "Ganha +2 de poder quando sua pontuação total é menor que a do adversário."},
    "paradoxo_eterno": {"nome": "Paradoxo Eterno", "texto": "Recebe +2 na terceira rodada se o adversário venceu a segunda."},
    "guardiao_fileira": {"nome": "Guardião da Fileira", "texto": "+1 para cada outra unidade sua na mesma fileira, até +3."},
    "cacador_solitario": {"nome": "Caçador Solitário", "texto": "+2 se não houver outra unidade sua na fileira."},
    "estandarte": {"nome": "Estandarte", "texto": "Concede +1 às outras unidades aliadas da mesma fileira."},
    "resistencia_climatica": {"nome": "Resistência Climática", "texto": "Ignora até 2 pontos de penalidade climática; sem clima ativo ao entrar, recebe +1."},
    "eco_arcano": {"nome": "Eco Arcano", "texto": "+2 se você tiver uma carta especial no descarte."},
    "gwent_nevoa": {"nome": "Névoa de Sellia", "texto": "Aplica 1 marca de Podridão Escarlate a todas as unidades inimigas da fileira escolhida; raridades Lendárias ou superiores aplicam uma segunda marca."},
    "gwent_geada": {"nome": "Lua Gélida", "texto": "Aplica 1 marca de Geada a todas as unidades inimigas em campo; raridades Lendárias ou superiores aplicam uma segunda marca."},
    "gwent_chuva": {"nome": "Sangue Corrompido", "texto": "Aplica uma marca de Sangramento a todas as unidades inimigas na fileira de Cerco; a segunda marca reduz 2 de bônus (mínimo -2) e consome as marcas."},
    "gwent_chifre": {"nome": "Rugido de Godfrey", "texto": "Concede +2 às suas unidades na fileira escolhida até o fim da rodada."},
    "gwent_medico": {"nome": "Lágrima Sagrada", "texto": "Devolve à sua mão uma unidade do seu descarte com poder-base 4 ou menos; você pode escolher o alvo."},
    "gwent_queima": {"nome": "Chama Negra", "texto": "Tenta remover a unidade de maior poder efetivo de cada lado; um escudo pode bloquear cada remoção."},
    "gwent_purificar": {"nome": "Lei da Regressão", "texto": "Remove todos os efeitos climáticos."},
    "gwent_execucao": {"nome": "Lâmina da Morte Destinada", "texto": "Remove uma unidade inimiga escolhida da fileira selecionada se ela tiver poder efetivo 6 ou menos; um escudo pode bloquear a remoção."},
    "gwent_vinculo": {"nome": "Juramento do Crisol", "texto": "Se houver ao menos duas unidades aliadas na fileira escolhida, concede +2 a todas elas até o fim da rodada."},
    "gwent_batedor": {"nome": "Passo do Cão de Caça", "texto": "Compra uma carta da reserva, se disponível."},
    "gwent_muralha": {"nome": "Bastião de Leyndell", "texto": "Concede +1 às suas unidades na fileira escolhida até o fim da rodada."},
    "vinganca": {"nome": "Vingança", "texto": "Ao cair, concede +1 às unidades aliadas da mesma fileira."},
    "escudo_ferro": {"nome": "Escudo de Ferro", "texto": "Entra com escudo: ignora a primeira remoção sofrida."},
    "ressurgir": {"nome": "Ressurgir", "texto": "Se houver uma unidade elegível, traz do descarte a mais forte com poder base 5 ou menos diretamente ao campo."},
    "devorar": {"nome": "Devorar", "texto": "Ao entrar, consome a unidade aliada de menor poder efetivo na mesma fileira e recebe bônus igual ao poder dela, até +4."},
    "sobrevivente": {"nome": "Sobrevivente", "texto": "Ao fim da rodada, permanece no campo (a mais forte, se houver várias)."},
    "espolios": {"nome": "Espólios", "texto": "Se você vencer a rodada com ela em campo, compra uma carta."},
    "gwent_egide": {"nome": "Bênção da Árvore Áurea", "texto": "Concede escudo a uma unidade sua."},
    "gwent_requiem": {"nome": "Chamado dos Mortos", "texto": "Traz do descarte diretamente ao campo uma unidade com poder base 6 ou menos."},
    "gwent_passo": {"nome": "Passo do Lobo", "texto": "Move uma unidade sua para a fileira escolhida."},
    "dupla_fornalha": {"nome": "Pacto da Fornalha", "texto": "+2 se houver outra unidade aliada na mesma fileira."},
    "irmandade_veu": {"nome": "Formação do Véu", "texto": "+2 se houver outra unidade aliada em uma fileira diferente."},
    "circulo_arcano": {"nome": "Círculo de Ressonância", "texto": "+2 se houver outra unidade aliada na mesma fileira ou uma carta especial no descarte."},
    "gwent_sangramento": {"nome": "Sangramento", "texto": "Marca as unidades inimigas da fileira; a segunda marca reduz o bônus em 2 (mínimo -2) e consome as marcas. Marcas expiram no fim da rodada."},
    "gwent_geada_cariana": {"nome": "Geada Cariana", "texto": "Aplica até duas marcas às unidades inimigas da fileira escolhida; cada marca reduz 1 de poder efetivo até o fim da rodada."},
    "gwent_podrida": {"nome": "Podridão Escarlate", "texto": "Cada marca reduz 1 de poder efetivo; a segunda também corrói 1 ponto de bônus positivo, se houver. Marcas expiram no fim da rodada."},
    "gwent_loucura": {"nome": "Loucura Frenética", "texto": "Cada marca reduz 1 de poder efetivo; a segunda remove todos os bônus positivos da unidade. Marcas expiram no fim da rodada."},
    "gwent_chama": {"nome": "Chama do Gigante", "texto": "Remove Geada de todas as suas unidades; cada unidade purificada recebe +1 de poder até o fim da rodada."},
    "gwent_invocacao": {"nome": "Cinzas dos Lobos Solitários", "texto": "Invoca Lobos Espirituais com 3 de poder na fileira escolhida."},
    "reliquia_godrick": {"nome": "Grande Runa de Godrick", "texto": "Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas."},
    "reliquia_renala": {"nome": "Grande Runa dos Não Nascidos", "texto": "Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus."},
    "reliquia_morte": {"nome": "Runa da Morte", "texto": "Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira."},
    "reliquia_noite_chama": {"nome": "Espada da Noite e da Chama", "texto": "Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe."},
    "reliquia_lamina_negra": {"nome": "Lâmina Negra", "texto": "Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia."},
    "reliquia_algemas": {"nome": "Algemas de Margit", "texto": "Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados."},
}


# A fileira é definida pelo papel tático da unidade, não pela facção.
# Cartas geradas sem entrada explícita usam o padrão de seu arquétipo.
FILEIRAS_POR_CARTA = {
    "chefe_dama_vazio": "siege", "chefe_oraculo_ruina": "melee",
    "chefe_cervo_sombrio": "melee", "chefe_cacador_sem_rosto": "melee",
    "chefe_aparicao_veio": "melee", "arma_lamina_peregrino": "melee",
    "arma_duas_luas": "melee", "covenant_lobos_cinza": "melee",
    "arma_cajado_marulho": "ranged", "arma_agulha_astro": "ranged",
    "magia_brasa_errante": "melee", "magia_selo_vigilia": "melee",
    "magia_trovao_oco": "ranged", "magia_fagulha": "ranged",
    "magia_orbe_eco": "ranged", "magia_chama_fria": "ranged",
    "magia_sol_negro": "melee", "covenant_lua_velada": "ranged",
    "covenant_sentinelas": "melee", "covenant_coroa_abismo": "melee",
    "covenant_ultimos": "melee", "covenant_peregrinos_nevoa": "ranged",
    "gwent_unidade_oraculo_clima": "siege", "gwent_unidade_eco": "siege",
    "gwent_unidade_cavaleira": "melee", "gwent_unidade_cartografa": "ranged",
    "gwent_unidade_invocador": "siege", "gwent_unidade_dupla_veu": "melee",
    "gwent_unidade_circulo": "siege", "gwent_unidade_guardiao_runas": "melee",
    "gwent_unidade_necromante": "siege", "gwent_unidade_detonador": "melee",
    "gwent_unidade_devorador_mana": "melee", "gwent_unidade_bibliotecaria": "siege",
    "gwent_unidade_saqueadora_veu": "ranged", "gwent_unidade_contrabandista": "ranged",
    "gwent_unidade_cacadora_fantasma": "melee", "gwent_unidade_senhor_cacada": "melee",
    "gwent_unidade_sentinela_rubra": "melee", "gwent_unidade_veterano_cercos": "melee",
    "gwent_unidade_herdeiro_portao": "melee", "gwent_unidade_carniceiro_forja": "melee",
    "gwent_unidade_intendente": "ranged", "gwent_unidade_gigante": "melee",
    "gwent_unidade_mestre_forja": "melee", "gwent_unidade_lamina_sem_juramento": "melee",
    "gwent_unidade_portaestandarte": "melee", "gwent_mitica_coroa": "melee",
    "gwent_singular_primeiro": "melee", "gwent_singular_intocavel": "melee",
    "gwent_singular_nivel1": "melee", "gwent_singular_cacador_chefes": "melee",
    "primordial_origem": "siege", "primordial_trono": "melee",
    "primordial_tempestade": "siege", "primordial_abismo": "siege",
    "primordial_eternidade": "melee",
    # Classificação tática explícita das cartas que antes herdavam a fileira do tipo legado.
    "chefe_guardiao_cinzas": "melee", "chefe_rei_afogado": "melee",
    "chefe_vigia_cinzento": "melee", "chefe_malenia_lamina_miquella": "melee",
    "chefe_radahn_flagelo_estrelas": "siege", "chefe_maliketh_morte_destinada": "melee",
    "chefe_messmer_impalador": "melee", "chefe_placidusax_lorde_dragao": "siege",
    "arma_martelo_fornalha": "melee", "arma_grande_sino": "melee",
    "arma_lanca_fornalha": "melee", "arma_arco_peregrino": "ranged",
    "magia_nevoa_antiga": "siege", "covenant_filhos_brasa": "melee",
    "covenant_irmandade_ferro": "melee", "gwent_unidade_baluarte": "melee",
    "gwent_unidade_cantora_lamentos": "ranged",
    "luterano_cruzado": "melee", "luterano_missionario": "ranged",
    "luterano_bispo": "siege", "luterano_anjo": "ranged",
    "luterano_papa": "siege", "luterano_sacerdote": "ranged",
    "luterano_irmao": "melee", "luterano_diacon": "ranged",
    "gwent_v75_ordem_veterano_juramento": "melee",
    "gwent_v75_ordem_guardiao_crisol": "melee",
    "gwent_v75_ordem_confessora_graca": "ranged",
    "gwent_v75_ordem_arauto_estandarte": "ranged",
    "gwent_v75_veu_acolito_sangue": "ranged",
    "gwent_v75_veu_devota_hemorragia": "melee",
    "gwent_v75_veu_carrasco_preco": "melee",
    "gwent_v75_veu_cacador_sangue": "ranged",
    "gwent_v75_lua_oraculo_geada": "siege",
    "gwent_v75_lua_cartografo_lunar": "ranged",
    "gwent_v75_lua_graviturgista": "siege",
    "gwent_v75_lua_guardia": "melee",
    "luterano_apostolo": "melee", "luterano_pastor": "ranged",
    "luterano_mistico": "siege", "luterano_profeta": "siege",
    "luterano_vigia": "ranged", "luterano_anjo2": "ranged",
}


@dataclass(frozen=True, slots=True)
class Carta:
    id: str
    nome: str
    categoria: str
    faccao: str
    poder: int
    raridade: str
    custo: int
    habilidade: str
    descricao: str = ""
    jogo_origem: str = ""
    fileira: str = ""

    def para_dict(self) -> dict[str, Any]:
        """Serializa a carta com facção e fileira tática separadas; não expõe campos legados."""
        data = asdict(self)
        papeis = {"melee": "Linha de frente", "ranged": "Atirador", "siege": "Artilharia"}
        especial = str(self.categoria or "").casefold() == "especial"
        fileira = self.fileira or FILEIRAS_POR_CARTA.get(self.id, "melee")
        if fileira not in {"melee", "ranged", "siege"}:
            raise ValueError(f"Fileira tática inválida no catálogo: {self.id}")
        if self.faccao not in {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}:
            raise ValueError(f"Facção inválida no catálogo: {self.id}")
        data.update({
            "categoria": "Especial" if especial else "Unidade",
            "faccao": self.faccao,
            "fileira": fileira,
            "row_label": "Carta especial" if especial else {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}[fileira],
            "papel_gwent": "Tática" if especial else papeis[fileira],
            "tipo_combate": "Carta especial" if especial else {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}[fileira],
            "categoria_arte": "Especial" if especial else "Unidade",
            "categoria_origem": "Especial" if especial else "Unidade",
            "jogo_origem": "",
        })
        return data


# Catálogo inicial. As cartas de jogos e patentes são geradas deterministicamente.
_CARTAS_BASE = [
    # Chefes
    Carta("chefe_guardiao_cinzas", "Cavaleiro da Árvore Áurea", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "quebra_ritmo", "Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital."),
    Carta("chefe_dama_vazio", "Ranni, Bruxa da Lua", "Unidade", 'Lua Negra', 6, "Épica", 3, "ultimo_folego", "A princesa lunar rompeu com os Dois Dedos e busca um destino independente da Vontade Maior."),
    Carta("chefe_cervo_sombrio", "Cavaleiro do Cão de Caça", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "contragolpe", "Um cavaleiro errante segue a trilha de presas pelas florestas enevoadas das Terras Intermédias."),
    Carta("chefe_rei_afogado", "Godfrey, Primeiro Lorde Prístino", "Unidade", 'Ordem Áurea', 7, "Épica", 3, "primeira_luz", "Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias."),
    Carta("chefe_oraculo_ruina", "Gurranq, Clérigo Bestial", "Unidade", 'Ordem Áurea', 7, "Lendária", 4, "impeto", "O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte."),
    Carta("chefe_cacador_sem_rosto", "Assassina da Faca Negra", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "retaliacao", "Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn."),
    Carta("chefe_vigia_cinzento", "Cavaleiro de Leyndell", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "drenagem", "Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea."),
    Carta("chefe_aparicao_veio", "Lâmina Negra Errante", "Unidade", 'Véu Carmesim', 3, "Comum", 1, "adaptacao", "Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa."),
    Carta("chefe_malenia_lamina_miquella", "Malenia, Lâmina de Miquella", "Unidade", 'Véu Carmesim', 9, "Primordial", 4, "drenagem", "Espadachim lendária e irmã gêmea de Miquella, luta enquanto a Podridão Escarlate consome seu corpo."),
    Carta("chefe_radahn_flagelo_estrelas", "Radahn, Flagelo das Estrelas", "Unidade", 'Ordem Áurea', 9, "Primordial", 4, "quebra_ritmo", "General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão."),
    Carta("chefe_maliketh_morte_destinada", "Maliketh, Lâmina Negra", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "cacador_arcano", "Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina."),
    Carta("chefe_messmer_impalador", "Messmer, o Empalador", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "quebra_ritmo", "Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras."),
    Carta("chefe_placidusax_lorde_dragao", "Placidusax, Lorde Dragão", "Unidade", 'Lua Negra', 9, "Primordial", 4, "olho_tempestade", "Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido."),
    # Armas
    Carta("arma_lamina_peregrino", "Duelista da Casa Hoslow", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "primeira_luz", "Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue."),
    Carta("arma_martelo_fornalha", "Ferreiro de Volcano Manor", "Unidade", 'Véu Carmesim', 6, "Rara", 2, "encadeamento", "Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir."),
    Carta("arma_cajado_marulho", "Feiticeiro Cariano", "Unidade", 'Lua Negra', 5, "Rara", 2, "cacador_arcano", "Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua."),
    Carta("arma_duas_luas", "Espadachim da Lua Negra", "Unidade", 'Lua Negra', 7, "Épica", 3, "precisao", "Um duelista das tradições carianas conduz a lâmina sob a luz fria da Lua Negra."),
    Carta("arma_grande_sino", "Sentinela do Portão de Leyndell", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "instinto", "Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada."),
    Carta("arma_agulha_astro", "Leitora de Estrelas de Sellia", "Unidade", 'Lua Negra', 3, "Comum", 1, "primeira_luz", "Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna."),
    Carta("arma_lanca_fornalha", "Lanceiro da Árvore Áurea", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "primeira_luz", "Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar."),
    Carta("arma_arco_peregrino", "Batedor da Mansão Vulcânica", "Unidade", 'Véu Carmesim', 5, "Comum", 1, "impeto", "Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos."),
    # Magias
    Carta("magia_brasa_errante", "Monge do Fogo", "Unidade", 'Lua Negra', 3, "Comum", 1, "sangue_frio", "Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes."),
    Carta("magia_selo_vigilia", "Confessora da Ordem Áurea", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "adaptacao", "Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo."),
    Carta("magia_trovao_oco", "Dragoeiro Ancião", "Unidade", 'Ordem Áurea', 6, "Épica", 3, "drenagem", "Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha."),
    Carta("magia_nevoa_antiga", "Astróloga de Liurnia", "Unidade", 'Lua Negra', 7, "Épica", 3, "encadeamento", "Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos."),
    Carta("magia_sol_negro", "Apóstolo da Pele Divina", "Unidade", 'Véu Carmesim', 8, "Lendária", 4, "quebra_ritmo", "Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses."),
    Carta("magia_fagulha", "Aprendiz de Feitiçaria Cariana", "Unidade", 'Lua Negra', 4, "Comum", 1, "cacador_arcano", "Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante."),
    Carta("magia_orbe_eco", "Erudito da Academia", "Unidade", 'Lua Negra', 4, "Comum", 1, "precisao", "Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes."),
    Carta("magia_chama_fria", "Feiticeira da Lua Gélida", "Unidade", 'Lua Negra', 3, "Comum", 1, "sangue_frio", "Uma feiticeira errante combina o frio das antigas artes lunares com chamas de origem desconhecida."),
    # Covenants / juramentos
    Carta("covenant_lobos_cinza", "Cavaleiros de Radahn", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "instinto", "Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid."),
    Carta("covenant_lua_velada", "Juramentada de Ranni", "Unidade", 'Lua Negra', 6, "Épica", 3, "primeira_luz", "Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea."),
    Carta("covenant_sentinelas", "Guardiões de Sellia", "Unidade", 'Lua Negra', 4, "Comum", 1, "adaptacao", "Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria."),
    Carta("covenant_coroa_abismo", "Cavaleiro da Dinastia Mohgwyn", "Unidade", 'Véu Carmesim', 7, "Lendária", 4, "drenagem", "Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg."),
    Carta("covenant_ultimos", "Cavaleiros de sangue juramentados", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "ultimo_folego", "Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego."),
    Carta("covenant_filhos_brasa", "Discípulos do Monge do Fogo", "Unidade", 'Ordem Áurea', 5, "Comum", 1, "contragolpe", "Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos."),
    Carta("covenant_peregrinos_nevoa", "Peregrinos da Cidade Eterna", "Unidade", 'Lua Negra', 4, "Comum", 1, "primeira_luz", "Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela."),
    Carta("covenant_irmandade_ferro", "Guardas da Árvore Áurea", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "retaliacao", "Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea."),
    # Cartas especiais do modo Gwent: entram na coleção por recompensas/pacotes do Discord.
    Carta("gwent_especial_nevoa", "Miasma da Podridão", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_nevoa", "Uma nuvem pútrida se espalha pelo campo, lembrando os pântanos corrompidos de Caelid."),
    Carta("gwent_especial_geada", "Geada dos Picos dos Gigantes", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_geada", "O frio dos Picos dos Gigantes avança sobre o campo e silencia o vigor dos combatentes."),
    Carta("gwent_especial_chuva", "Sangue Corrompido", "Especial", 'Véu Carmesim', 0, "Comum", 1, "gwent_chuva", "Um rito sanguíneo mancha o campo de batalha com a promessa de uma dívida ainda não paga."),
    Carta("gwent_especial_chifre", "Rugido de Godfrey", "Especial", 'Ordem Áurea', 0, "Épica", 3, "gwent_chifre", "O rugido do Primeiro Lorde Prístino ecoa entre as fileiras e reacende a coragem dos guerreiros."),
    Carta("gwent_especial_medico", "Lágrima Sagrada", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_medico", "Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada."),
    Carta("gwent_especial_queima", "Chama Negra", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_queima", "A chama negra, temida até pelos deuses, consome tudo o que toca."),
    Carta("gwent_especial_purificar", "Lei da Regressão", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_purificar", "A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo."),
    Carta("gwent_especial_execucao", "Lâmina da Morte Destinada", "Especial", 'Ordem Áurea', 0, "Épica", 3, "gwent_execucao", "A lâmina da Morte Destinada carrega o fragmento de um poder que deveria permanecer selado."),
    Carta("gwent_especial_vinculo", "Juramento do Crisol", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_vinculo", "Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree."),
    Carta("gwent_especial_batedor", "Passo do Cão de Caça", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_batedor", "O passo do cão de caça atravessa o campo antes que o inimigo perceba sua aproximação."),
    Carta("gwent_especial_muralha", "Bastião de Leyndell", "Especial", 'Ordem Áurea', 0, "Comum", 1, "gwent_muralha", "As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital."),
    # Táticas de estado inspiradas nos efeitos de Elden Ring.
    Carta("elden_especial_sangramento", "Ritual de Sangue", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_sangramento", "O ritual desperta o poder do sangue e transforma cada ferida em um presságio de ruína."),
    Carta("elden_especial_geada", "Lua Cheia de Rennala", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_geada_cariana", "A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana."),
    Carta("elden_especial_podrida", "Flor da Podridão Escarlate", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_podrida", "A flor escarlate floresce onde a podridão encontra carne, pedra e memória."),
    Carta("elden_especial_loucura", "Chama Frenética", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_loucura", "A chama frenética consome razão e identidade, deixando apenas o caos da Chama Frenética."),
    Carta("elden_especial_chama", "Chama do Gigante", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_chama", "A chama dos gigantes arde contra o frio que tenta aprisionar os vivos."),
    Carta("elden_especial_invocacao", "Cinzas dos Lobos Solitários", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_invocacao", "Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres."),
    # V19 — Relíquias: cada jogador pode ativar apenas uma por partida.
    Carta("reliquia_grande_runa_godrick", "Grande Runa de Godrick", "Especial", 'Ordem Áurea', 0, "Lendária", 3, "reliquia_godrick", "Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto."),
    Carta("reliquia_runa_nao_nascidos", "Grande Runa dos Não Nascidos", "Especial", 'Lua Negra', 0, "Lendária", 3, "reliquia_renala", "A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada."),
    Carta("reliquia_runa_morte", "Runa da Morte", "Especial", 'Véu Carmesim', 0, "Mítica", 4, "reliquia_morte", "O fragmento da Morte Destinada recorda o poder que Maliketh recebeu para manter selado."),
    Carta("reliquia_noite_chama", "Espada da Noite e da Chama", "Especial", 'Lua Negra', 0, "Lendária", 3, "reliquia_noite_chama", "Arma lendária da Mansão Cariana. Sua postura especial libera um ataque mágico ou uma onda de fogo."),
    Carta("reliquia_lamina_negra", "Lâmina Negra", "Especial", 'Véu Carmesim', 0, "Mítica", 4, "reliquia_lamina_negra", "A arma de Maliketh, que guarda a Morte Destinada selada em sua lâmina. Não é uma das adagas usadas pelas Assassinas da Faca Negra."),
    Carta("reliquia_algemas_margit", "Algemas de Margit", "Especial", 'Ordem Áurea', 0, "Épica", 2, "reliquia_algemas", "Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível."),
    # Novas unidades de facção e sinergia.
    Carta("gwent_unidade_baluarte", "Cavaleiro do Crisol", "Unidade", 'Ordem Áurea', 6, "Rara", 2, "guardiao_fileira", "Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina."),
    Carta("gwent_unidade_lamina_sem_juramento", "Caçador de Dedos", "Unidade", 'Véu Carmesim', 6, "Rara", 2, "cacador_solitario", "Caçador de Dedos, um duelista errante que prefere trilhas solitárias e confrontos sem testemunhas."),
    Carta("gwent_unidade_portaestandarte", "Porta-estandarte de Leyndell", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "estandarte", "O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital."),
    Carta("gwent_unidade_oraculo_clima", "Profeta de Liurnia", "Unidade", 'Lua Negra', 5, "Rara", 2, "resistencia_climatica", "O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas."),
    Carta("gwent_unidade_eco", "Erudito das Pedras Cintilantes", "Unidade", 'Lua Negra', 5, "Rara", 2, "eco_arcano", "Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas."),
    Carta("gwent_unidade_cavaleira", "Cavaleira Cariana", "Unidade", 'Lua Negra', 5, "Comum", 1, "quebra_ritmo", "Uma duelista cariana, treinada nas tradições de combate da realeza lunar."),
    Carta("gwent_unidade_gigante", "Gigante de Fogo", "Unidade", 'Ordem Áurea', 7, "Épica", 3, "instinto", "Uma presença colossal na linha de frente."),
    Carta("gwent_unidade_cartografa", "Exploradora da Cidade Eterna", "Unidade", 'Lua Negra', 4, "Comum", 1, "adaptacao", "Encontra rotas onde os outros veem obstáculos."),
    Carta("gwent_unidade_invocador", "Apóstolo da Pele Divina Errante", "Unidade", 'Véu Carmesim', 7, "Épica", 3, "cacador_arcano", "Converte conhecimento arcano em força de combate."),
    Carta("gwent_unidade_mestre_forja", "Mestre Ferreiro de Volcano Manor", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "dupla_fornalha", "Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes."),
    Carta("gwent_unidade_dupla_veu", "Gêmeas da Cidade Eterna", "Unidade", 'Lua Negra', 5, "Rara", 2, "irmandade_veu", "Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas."),
    Carta("gwent_unidade_circulo", "Discípulo da Academia", "Unidade", 'Lua Negra', 5, "Rara", 2, "circulo_arcano", "Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria."),

    # Etapa 2: unidades de facção que usam os efeitos de ciclo de vida (escudo, queda, ressurreição...).
    # Ordem Áurea — muralha (escudo/sobrevivência/vingança) e banquete (devorar/espólios).
    Carta("gwent_unidade_sentinela_rubra", "Cavaleiro de Radahn", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "escudo_ferro", "Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid."),
    Carta("gwent_unidade_veterano_cercos", "Cavaleiro Draconiano", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "sobrevivente", "Já viu mais muralhas caírem do que rostos conhecidos."),
    Carta("gwent_unidade_herdeiro_portao", "Godwyn, o Dourado", "Unidade", 'Ordem Áurea', 6, "Épica", 3, "vinganca", "Quando cai, a formação inteira jura vingá-lo."),
    Carta("gwent_unidade_carniceiro_forja", "Carrasco de Volcano Manor", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "devorar", "Consome os restos da batalha para ampliar a própria força."),
    Carta("gwent_unidade_intendente", "Mercador Nômade", "Unidade", 'Ordem Áurea', 3, "Comum", 1, "espolios", "Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos."),
    # Lua Negra — fantasmas (retorno e persistência) e caravana (saque e blindagem).
    Carta("gwent_unidade_cacadora_fantasma", "Assassina de Ravenmount", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "sobrevivente", "Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir."),
    Carta("gwent_unidade_cantora_lamentos", "Fia, Companheira do Leito de Morte", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "ressurgir", "Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos."),
    Carta("gwent_unidade_senhor_cacada", "Blaidd, o Meio-Lobo", "Unidade", 'Lua Negra', 6, "Épica", 3, "vinganca", "A presa que o derruba desperta a matilha inteira."),
    Carta("gwent_unidade_saqueadora_veu", "Ladina da Cidade Eterna", "Unidade", 'Lua Negra', 4, "Comum", 1, "espolios", "Nenhuma rota é cara demais para quem leva o butim."),
    Carta("gwent_unidade_contrabandista", "Recusante da Mansão Vulcânica", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "escudo_ferro", "Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir."),
    # Véu Carmesim — rúnico (proteção e retorno) e eclipse (consumo e conhecimento).
    Carta("gwent_unidade_guardiao_runas", "Guardião da Ordem Áurea", "Unidade", 'Ordem Áurea', 5, "Comum", 1, "escudo_ferro", "Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital."),
    Carta("gwent_unidade_necromante", "Servo dos que Vivem na Morte", "Unidade", 'Lua Negra', 4, "Rara", 2, "ressurgir", "Desperta no campo os que o descarte ainda guarda."),
    Carta("gwent_unidade_detonador", "Guerreiro da Chama Frenética", "Unidade", 'Véu Carmesim', 6, "Épica", 3, "vinganca", "Sua queda libera a energia que ele guardava."),
    Carta("gwent_unidade_devorador_mana", "Cavaleiro de Sangue de Mohg", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "devorar", "Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea."),
    Carta("gwent_unidade_bibliotecaria", "Bibliotecária de Raya Lucaria", "Unidade", 'Lua Negra', 4, "Comum", 1, "espolios", "O conhecimento reunido na guerra vale mais que ouro."),

    # Etapa 2: cartas especiais novas (todas funcionam sem alvo escolhido; `target_id` apenas refina).
    Carta("gwent_especial_egide", "Bênção da Árvore Áurea", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_egide", "Concede escudo a uma unidade sua (a escolhida, ou a mais forte sem escudo)."),
    Carta("gwent_especial_requiem", "Chamado dos Mortos", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_requiem", "Traz direto ao campo uma unidade com poder base 6 ou menos do seu descarte (a escolhida, ou a mais forte)."),
    Carta("gwent_especial_passo", "Passo do Lobo", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_passo", "Move uma unidade sua para a fileira escolhida (a escolhida, ou a mais fraca fora dela)."),
    Carta("gwent_mitica_coroa", "Cavaleiro Consagrado do Haligtree", "Unidade", 'Ordem Áurea', 8, "Mítica", 5, "estandarte", "Uma presença mítica que fortalece a formação aliada."),
    Carta("gwent_singular_primeiro", "Juramento Primordial do Crisol", "Unidade", 'Véu Carmesim', 10, "Singular", 0, "cacador_solitario", "Exemplar singular conquistado por um feito extraordinário."),
    Carta("gwent_singular_intocavel", "Adaga da Faca Negra", "Unidade", 'Véu Carmesim', 9, "Singular", 0, "precisao", "Conquistada ao concluir um desafio sem sofrer dano."),
    Carta("gwent_singular_nivel1", "Vontade de Marika", "Unidade", 'Ordem Áurea', 10, "Singular", 0, "ultimo_folego", "Conquistada ao vencer um desafio no nível um."),
     Carta("gwent_singular_cacador_chefes", "Coroa do Lorde Prístino", "Unidade", 'Lua Negra', 9, "Singular", 0, "paradoxo_eterno", "Conquistada ao derrotar todos os chefes de um desafio."),
    # Nova facção: Os Esquecidos (Luteranos)
    Carta("luterano_cruzado", "Cruzado Esquecido", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "sinergia_faccao", "Um guerreiro sagrado que luta pela fé, mesmo após ser esquecido pelo mundo. Ganha força com aliados da mesma facção."),
    Carta("luterano_missionario", "Missionário Esquecido", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "legado", "Espalha a palavra divina. Se venceu a rodada anterior, entra com +2 de poder."),
    Carta("luterano_bispo", "Bispo Esquecido", "Unidade", 'Os Esquecidos', 5, "Lendária", 3, "devoto", "Líder espiritual que fortalece aliados da mesma facção."),
    Carta("luterano_anjo", "Anjo Esquecido", "Unidade", 'Os Esquecidos', 3, "Épica", 2, "gloria", "Mensageiro divino que permanece no campo se vencer a rodada."),
    Carta("luterano_papa", "Papa Esquecido", "Unidade", 'Os Esquecidos', 7, "Mítica", 4, "sinergia_faccao", "Sumo sacerdote esquecido. Sua presença fortalece todos os aliados da fé."),
    Carta("luterano_sacerdote", "Sacerdote Esquecido", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "devoto", "Cura e fortalece aliados da mesma facção."),
    Carta("luterano_irmao", "Irmão Esquecido", "Unidade", 'Os Esquecidos', 3, "Comum", 1, "legado", "Um irmão de fé que ganha força ao vencer."),
    Carta("luterano_diacon", "Diácono Esquecido", "Unidade", 'Os Esquecidos', 2, "Comum", 1, "escolha_ritmo", "Auxilia nos rituais e escolhe o melhor momento para agir."),
]

CARTAS_PRIMORDIAIS = [
    Carta("primordial_origem", "Besta Prístina, Arauto da Vontade Maior", "Unidade", 'Ordem Áurea', 8, "Primordial", 4, "lei_primeva", "A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada."),
    Carta("primordial_trono", "Marika, Rainha Eterna", "Unidade", 'Ordem Áurea', 8, "Primordial", 4, "decreto_soberano", "Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias."),
    Carta("primordial_tempestade", "Placidusax, Senhor Dragão", "Unidade", 'Lua Negra', 8, "Primordial", 4, "olho_tempestade", "Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula."),
    Carta("primordial_abismo", "Mãe Sem Forma", "Unidade", 'Véu Carmesim', 8, "Primordial", 4, "fome_abismo", "A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo."),
    Carta("primordial_eternidade", "Maliketh, Guardião da Morte Destinada", "Unidade", 'Ordem Áurea', 8, "Primordial", 4, "paradoxo_eterno", "Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika."),
]
# V18 — metade das unidades não possui habilidade especial.
# Priorizamos cartas Comuns e completamos a meta com cartas Raras; Épicas+ preservam efeitos.
_unidades_v18 = [c for c in [*_CARTAS_BASE, *CARTAS_PRIMORDIAIS] if c.categoria.casefold() != "especial"]
_protegidas_com_efeito_v18 = {"chefe_guardiao_cinzas", "covenant_irmandade_ferro"}
_sem_efeito_v18 = [c for c in _unidades_v18 if c.raridade == "Comum" and c.id not in _protegidas_com_efeito_v18]
_meta_sem_efeito_v18 = (len(_unidades_v18) // 2) + 2  # reserva duas unidades sem efeito para equilibrar as patentes geradas
_faltam_v18 = max(0, _meta_sem_efeito_v18 - len(_sem_efeito_v18))
_sem_efeito_v18 += sorted(
    [c for c in _unidades_v18 if c.raridade == "Rara" and c.id not in _protegidas_com_efeito_v18],
    key=lambda c: hashlib.sha256(c.id.encode("utf-8")).hexdigest(),
)[:_faltam_v18]
CARTAS_SEM_EFEITO_IDS = frozenset(c.id for c in _sem_efeito_v18)
_cartas_v18 = []
for _c in [*_CARTAS_BASE, *CARTAS_PRIMORDIAIS]:
    if _c.id in CARTAS_SEM_EFEITO_IDS:
        _poder = min(FAIXA_PODER[_c.raridade][1], _c.poder + 1)
        _cartas_v18.append(Carta(_c.id, _c.nome, _c.categoria, _c.faccao, _poder, _c.raridade, _c.custo, "", _c.descricao, _c.jogo_origem, _c.fileira))
    else:
        _cartas_v18.append(_c)
_CARTAS_BASE = [c for c in _cartas_v18 if c.id not in {x.id for x in CARTAS_PRIMORDIAIS}]
CARTAS_PRIMORDIAIS = [c for c in _cartas_v18 if c.id in {x.id for x in CARTAS_PRIMORDIAIS}]

# Expansão V75 — 12 unidades novas, quatro por facção.
# As cartas entram após o balanceamento legado V18 para preservar suas habilidades próprias.
CARTAS_EXPANSAO_V75 = [
    # ORDEM ÁUREA — formação, proteção e purificação.
    Carta("gwent_v75_ordem_veterano_juramento", "Veterano do Juramento Dourado", "Unidade", 'Ordem Áurea', 4, "Rara", 2, "", "Veterano de Leyndell que mantém a formação unida: ao entrar, fortalece a si e o aliado mais fraco da mesma fileira.", fileira="melee"),
    Carta("gwent_v75_ordem_guardiao_crisol", "Guardião do Crisol Menor", "Unidade", 'Ordem Áurea', 4, "Rara", 2, "", "Não possui habilidade individual. Pode completar combos da Ordem Áurea quando estiver em campo com a unidade compatível.", fileira="melee"),
    Carta("gwent_v75_ordem_confessora_graca", "Confessora da Graça Serena", "Unidade", 'Ordem Áurea', 5, "Épica", 3, "", "Uma Confessora treinada na Lei da Regressão remove condições negativas de até dois aliados na fileira de Cerco e os fortalece.", fileira="siege"),
    Carta("gwent_v75_ordem_arauto_estandarte", "Arauto do Estandarte Áureo", "Unidade", 'Ordem Áurea', 5, "Épica", 3, "", "Não possui habilidade individual. Pode completar combos de formação da Ordem Áurea com a unidade compatível.", fileira="ranged"),

    # VÉU CARMESIM — marcas de Sangramento, pressão e sacrifício calculado.
    Carta("gwent_v75_veu_acolito_sangue", "Acólito da Dinastia Sanguínea", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "", "Servo do Palácio de Mohgwyn que marca o inimigo mais forte da fileira; a segunda marca provoca Hemorragia.", fileira="ranged"),
    Carta("gwent_v75_veu_devota_hemorragia", "Devota da Hemorragia", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "", "Não possui habilidade individual. Pode completar o combo Banquete da Hemorragia com a unidade compatível.", fileira="siege"),
    Carta("gwent_v75_veu_carrasco_preco", "Carrasco da Procissão Carmesim", "Unidade", 'Véu Carmesim', 5, "Épica", 3, "", "O carrasco sacrifica o aliado mais fraco da mesma fileira para absorver parte de seu poder, com ganho limitado.", fileira="melee"),
    Carta("gwent_v75_veu_cacador_sangue", "Caçador das Catacumbas de Mohgwyn", "Unidade", 'Véu Carmesim', 5, "Épica", 3, "", "Não possui habilidade individual. Pode completar combos de marca de Sangramento com a unidade compatível.", fileira="ranged"),

    # LUA NEGRA — Geada, leitura de campo e controle gravitacional.
    Carta("gwent_v75_lua_oraculo_geada", "Oráculo Gélido de Sellia", "Unidade", 'Lua Negra', 4, "Rara", 2, "", "Uma astróloga de Sellia aplica Geada ao inimigo mais forte da fileira; completar a segunda marca fortalece o oráculo.", fileira="siege"),
    Carta("gwent_v75_lua_cartografo_lunar", "Cartógrafo das Cidades Eternas", "Unidade", 'Lua Negra', 4, "Rara", 2, "", "Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.", fileira="ranged"),
    Carta("gwent_v75_lua_graviturgista", "Graviturgista de Nokron", "Unidade", 'Lua Negra', 5, "Épica", 3, "", "Dobra a gravidade sobre até dois inimigos fortalecidos na fileira escolhida; se atingir dois, recebe poder adicional.", fileira="siege"),
    Carta("gwent_v75_lua_guardia", "Guardiã do Juramento Lunar", "Unidade", 'Lua Negra', 5, "Épica", 3, "", "Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.", fileira="melee"),
    # Nova facção: Os Esquecidos — fé, tradição e rituais sagrados.
    Carta("luterano_apostolo", "Apóstolo Esquecido", "Unidade", 'Ordem Áurea', 5, "Épica", 3, "", "Espalha a verdade divina; ao entrar em campo com aliado da mesma facção, ambos ganham +1 de poder.", fileira="melee"),
    Carta("luterano_pastor", "Pastor Esquecido", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "legado", "Guia o rebanho fiel. Se venceu a rodada anterior, entra em campo com +2 de poder.", fileira="ranged"),
    Carta("luterano_mistico", "Místico Esquecido", "Unidade", 'Lua Negra', 5, "Rara", 2, "devoto", "Conecta-se ao sagrado; cada aliada da mesma facção em campo concede +1 de bônus adicional.", fileira="siege"),
    Carta("luterano_profeta", "Profeta Esquecido", "Unidade", 'Ordem Áurea', 6, "Mítica", 4, "sinergia_faccao", "Líder espiritual que une o rebanho. Ganha +1 de poder para cada aliada da Fé em campo.", fileira="melee"),
    Carta("luterano_vigia", "Vigia da Noite", "Unidade", 'Véu Carmesim', 3, "Comum", 1, "gloria", "Mantém a vigilância durante a noite. Permanece no campo ao vencer a rodada.", fileira="melee"),
    Carta("luterano_anjo2", "Anjo de Segunda Ordem", "Unidade", 'Lua Negra', 5, "Lendária", 3, "gloria", "Brilho do sagrado. Ao vencer rodada, permanece no campo para o início da próxima.", fileira="siege"),
]

_LUTERANO_CARTAS = []

_CARTAS_BASE = [*_CARTAS_BASE, *CARTAS_EXPANSAO_V75, *_LUTERANO_CARTAS]

CARTAS_POR_ID: dict[str, Carta] = {c.id: c for c in [*_CARTAS_BASE, *CARTAS_PRIMORDIAIS]}


def slug_jogo(nome: str) -> str:
    normalizado = unicodedata.normalize("NFKD", str(nome or ""))
    ascii_nome = "".join(ch for ch in normalizado if not unicodedata.combining(ch)).lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_nome).strip("_") or "jogo_sem_nome"
    # Sufixo estável evita colisões entre títulos que normalizam para o mesmo slug.
    suffix = hashlib.sha256(str(nome or "").casefold().encode("utf-8")).hexdigest()[:6]
    return f"{slug[:62]}_{suffix}"


def _hash_int(valor: str) -> int:
    return int.from_bytes(hashlib.sha256(valor.encode("utf-8")).digest()[:8], "big")


def carta_jogo(nome_jogo: str, marco: str) -> Carta:
    """Cria uma recompensa com nome e território coerentes com seu arquétipo."""
    marco = "platina" if str(marco).lower() == "platina" else "zerado"
    slug = slug_jogo(nome_jogo)
    n = _hash_int(f"{slug}:{marco}:gwent-reward-v2")
    faccao = ("Véu Carmesim", "Ordem Áurea", "Lua Negra")[n % 3]
    fileira = ("melee", "ranged", "siege")[(n // 23) % 3]
    raridade = "Épica" if marco == "platina" else "Rara"
    habilidade = HABILIDADES_COMUNS[(n // 7) % len(HABILIDADES_COMUNS)] if (raridade == "Épica" or n % 2 == 0) else ""
    minimo, maximo = FAIXA_PODER[raridade]
    poder = minimo + ((n // 11) % (maximo - minimo + 1))

    identidades = {
        "Ordem Áurea": (
            ("Cavaleiro de Leyndell", ("da Graça Dourada", "da Capital Dourada")),
            ("Sentinela da Árvore Áurea", ("de Leyndell", "da Árvore Áurea")),
            ("Juramentado do Crisol", ("do Crisol", "das Raízes Antigas")),
        ),
        "Véu Carmesim": (
            ("Cavaleiro Sanguíneo", ("da Dinastia Sanguínea", "de Mohgwyn")),
            ("Recusante de Volcano Manor", ("do Monte Gelmir", "da Mansão Vulcânica")),
            ("Lâmina de Ravenmount", ("da Névoa", "de Ravenmount")),
        ),
        "Lua Negra": (
            ("Feiticeiro Cariano", ("da Lua Negra", "da Tradição Cariana")),
            ("Astrólogo de Liurnia", ("das Pedras Cintilantes", "de Liurnia")),
            ("Erudito de Raya Lucaria", ("da Academia", "dos Sábios Carianos")),
        ),
    }
    opcoes = identidades[faccao]
    nome_base, epitetos = opcoes[(n // 13) % len(opcoes)]
    epiteto = epitetos[(n // 19) % len(epitetos)]
    titulo = f"{nome_base} {epiteto}"

    descricoes = {
        "Ordem Áurea": "Combatente da Ordem Áurea, treinado para sustentar a formação e proteger seus aliados.",
        "Véu Carmesim": "Combatente do Véu Carmesim, habituado a emboscadas, precisão e pressão sobre o adversário.",
        "Lua Negra": "Estudioso da Lua Negra, dedicado à feitiçaria, à observação dos astros e ao controle do campo.",
    }
    descricao = descricoes[faccao] + " Papel tático: " + {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}[fileira] + "."
    if habilidade:
        nome_habilidade = HABILIDADES.get(habilidade, {}).get("nome", "técnica especial")
        descricao += f" Habilidade: {nome_habilidade}."
    else:
        descricao += " Sem habilidade especial; seu valor vem do poder-base e dos bônus de combate."
    descricao += " Recompensa por domínio completo." if marco == "platina" else " Recompensa por conquista."

    return Carta(
        id=f"jogo_{slug}_{marco}", nome=titulo[:95], categoria="Unidade", faccao=faccao,
        poder=int(poder), raridade=raridade, custo=CUSTO_RARIDADE[raridade],
        habilidade=habilidade, descricao=descricao[:240], jogo_origem="", fileira=fileira,
    )



def carta_patente(indice: int, nivel_minimo: int, nome_patente: str) -> Carta:
    """Gera uma recompensa de patente com título coerente com sua facção."""
    seed = f"patente:{indice}:{nome_patente}:soulsbot-card-v1"
    n = _hash_int(seed)
    if nivel_minimo >= 75:
        raridade = "Lendária"
    elif nivel_minimo >= 30:
        raridade = "Épica"
    elif nivel_minimo >= 10:
        raridade = "Rara"
    else:
        raridade = "Comum"
    minimo, maximo = FAIXA_PODER[raridade]
    poder = minimo + (n % (maximo - minimo + 1))
    faccao = ("Véu Carmesim", "Ordem Áurea", "Lua Negra")[(n // 9) % 3]
    fileira = ("melee", "ranged", "siege")[(n // 29) % 3]
    habilidade = HABILIDADES_COMUNS[(n // 17) % len(HABILIDADES_COMUNS)] if (raridade in {"Épica", "Lendária"} or n % 2 == 0) else ""

    nomes_por_faccao = {
        "Ordem Áurea": ("Lorde de Leyndell", "Veterano de Leyndell", "Escudeiro da Árvore Áurea", "Recruta de Leyndell"),
        "Véu Carmesim": ("Lorde Sanguíneo", "Cavaleiro de Mohgwyn", "Acólito Sanguíneo", "Recruta de Mohgwyn"),
        "Lua Negra": ("Mestre Cariano", "Feiticeiro Cariano", "Aprendiz Cariano", "Novato de Raya Lucaria"),
    }
    indice_nome = 0 if nivel_minimo >= 75 else 1 if nivel_minimo >= 30 else 2 if nivel_minimo >= 10 else 3
    titulo = f"{nomes_por_faccao[faccao][indice_nome]} — {nome_patente}"

    return Carta(
        id=f"patente_{indice + 1}",
        nome=titulo[:95],
        categoria="Unidade",
        faccao=faccao,
        poder=int(poder),
        raridade=raridade,
        custo=CUSTO_RARIDADE[raridade],
        habilidade=habilidade,
        descricao=(f"Recompensa por alcançar o nível {nivel_minimo}. Papel tático: " + {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}[fileira] + ". " + (HABILIDADES.get(habilidade, {}).get("texto", "") if habilidade else "Esta carta não tem habilidade especial; seu efeito vem do poder e dos bônus recebidos em combate.")),
        fileira=fileira,
    )



CARTAS_PATENTE = [carta_patente(i, nivel, nome) for i, (nivel, nome) in enumerate(PATENTES)]
CARTAS_POR_ID.update({c.id: c for c in CARTAS_PATENTE})

# Catálogo estático global usado pelos drops. Patentes e cartas dinâmicas de jogos antigos
# ficam fora do pool; Singular e Primordial possuem fluxos especiais.
CARTAS_PACOTE = [c for c in _CARTAS_BASE]
CARTAS_PACOTE_POR_RARIDADE = {
    raridade: [c for c in [*CARTAS_PACOTE, *CARTAS_PRIMORDIAIS] if c.raridade == raridade]
    for raridade in RARIDADES
}


def get_carta(card_id: str) -> Carta | None:
    if card_id in CARTAS_POR_ID:
        return CARTAS_POR_ID[card_id]
    if str(card_id).startswith("jogo_"):
        m = re.fullmatch(r"jogo_(.+)_(zerado|platina)", str(card_id))
        if m:
            slug, marco = m.groups()
            # O slug não é reversível em nome original; a função é usada após
            # carregar o snapshot persistido ou com o nome de jogo do registro.
            return None
    return None


def carta_de_jogo_por_id(card_id: str, nome_jogo: str) -> Carta:
    carta = carta_jogo(nome_jogo, "platina" if str(card_id).endswith("_platina") else "zerado")
    if carta.id != card_id:
        raise ValueError("ID de carta de jogo não corresponde ao título armazenado.")
    return carta
