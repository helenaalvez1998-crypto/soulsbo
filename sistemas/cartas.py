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

VERSAO_ARTES = 41


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
    "primeira_luz": {"nome": "Graça Dourada", "texto": "Na primeira rodada, recebe +1 de bônus ao entrar em campo."},
    "retaliacao": {"nome": "Retaliação dos Semideuses", "texto": "Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária."},
    "impeto": {"nome": "Ímpeto do Lorde", "texto": "Recebe +1 de bônus ao entrar se sua pontuação estiver acima da adversária."},
    "ultimo_folego": {"nome": "Último Suspiro", "texto": "Na terceira rodada, recebe +1 de bônus ao entrar em campo."},
    "contragolpe": {"nome": "Contragolpe", "texto": "Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária."},
    "encadeamento": {"nome": "Postura Encadeada", "texto": "Recebe +2 de bônus se entrar na mesma fileira da sua última unidade jogada."},
    "adaptacao": {"nome": "Passo do Peregrino", "texto": "Recebe +1 de bônus se entrar em fileira diferente da sua última unidade jogada."},
    "sangue_frio": {"nome": "Concentração", "texto": "Recebe +2 de bônus ao entrar quando as pontuações estão empatadas."},
    "instinto": {"nome": "Instinto de Caçador", "texto": "Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária."},
    "precisao": {"nome": "Mira Cariana", "texto": "Recebe +1 de bônus ao entrar na fileira de Longa Distância."},
    "drenagem": {"nome": "Selo Enfraquecedor", "texto": "Reduz em 1 o bônus de cada unidade inimiga, até o mínimo de -2."},
    "scarlet_bloom": {"nome": "Flor Escarlate", "texto": "Aplica 1 marca de Podridão Escarlate a cada inimigo da fileira. Ao passar de 1 para 2, o alvo com bônus positivo perde 1 (mín. 0). Primordial: até 3 desses alvos perdem mais 1 (mín. -2). Com 2 marcas, não há nova redução."},
    "cacador_arcano": {"nome": "Caçador de Feitiços", "texto": "Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo."},
    "quebra_ritmo": {"nome": "Ruptura de Postura", "texto": "Recebe +1 de bônus se a última unidade jogada pelo adversário entrou na mesma fileira."},
    # Efeitos exclusivos: somente a respectiva Primordial pode utilizá-los.
    "lei_primeva": {"nome": "Lei Primeva", "texto": "Recebe +2 de bônus ao entrar na primeira rodada."},
    "decreto_soberano": {"nome": "Decreto Soberano", "texto": "Ao entrar, reduz em 2 o bônus de todas as unidades inimigas (mín. -2)."},
    "olho_tempestade": {"nome": "Olho da Tempestade", "texto": "Recebe +2 de bônus ao entrar se sua fileira estiver sob clima ativo."},
    "fome_abismo": {"nome": "Fome do Abismo", "texto": "Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária."},
    "paradoxo_eterno": {"nome": "Paradoxo Eterno", "texto": "Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior."},
    "guardiao_fileira": {"nome": "Guardião da Fileira", "texto": "Ao entrar, recebe +1 de bônus por aliado na mesma fileira (máx. +3)."},
    "cacador_solitario": {"nome": "Caçador Solitário", "texto": "Recebe +2 de bônus ao entrar se não houver outro aliado na mesma fileira."},
    "estandarte": {"nome": "Estandarte", "texto": "Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira."},
    "resistencia_climatica": {"nome": "Resistência Climática", "texto": "Ignora até 2 pontos de penalidade climática; sem clima ativo ao entrar, recebe +1."},
    "eco_arcano": {"nome": "Eco Arcano", "texto": "Recebe +2 de bônus ao entrar se houver ao menos uma carta especial no seu descarte."},
    "gwent_clima": {"nome": "Tempestade dos Picos", "texto": "Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mínimo 1); Resistência Climática pode absorver a penalidade."},
    "gwent_nevoa": {"nome": "Névoa de Sellia", "texto": "Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Podridão Escarlate; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada."},
    "gwent_geada": {"nome": "Lua Gélida", "texto": "Todas as unidades inimigas recebem 1 marca de Geada; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada."},
    "gwent_chuva": {"nome": "Sangue Corrompido", "texto": "Aplica 1 Sangramento a cada inimigo em Cerco. Na segunda marca, consome as marcas e reduz 2 de bônus (mín. -2). Estados expiram no fim da rodada."},
    "gwent_chifre": {"nome": "Rugido de Godfrey", "texto": "Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada."},
    "gwent_medico": {"nome": "Lágrima Sagrada", "texto": "Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7."},
    "gwent_queima": {"nome": "Chama Negra", "texto": "Em cada lado, tenta remover a unidade de maior poder efetivo. Escudo bloqueia a remoção; se ela ocorrer, gatilhos de queda são resolvidos."},
    "gwent_purificar": {"nome": "Lei da Regressão", "texto": "Remove o clima ativo das três fileiras para os dois jogadores."},
    "gwent_execucao": {"nome": "Lâmina da Morte Destinada", "texto": "Escolha uma fileira e um inimigo nela com poder efetivo até 6. Tenta removê-lo; Escudo pode bloquear. Se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade eleva o limite até 9."},
    "gwent_vinculo": {"nome": "Juramento do Crisol", "texto": "Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada."},
    "gwent_batedor": {"nome": "Passo do Cão de Caça", "texto": "Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis."},
    "gwent_muralha": {"nome": "Bastião de Leyndell", "texto": "Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada."},
    "vinganca": {"nome": "Vingança", "texto": "Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus."},
    "escudo_ferro": {"nome": "Escudo de Ferro", "texto": "Entra com 1 Escudo, que bloqueia a primeira tentativa de remoção; sacrifícios ignoram Escudos."},
    "ressurgir": {"nome": "Ressurgir", "texto": "Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo."},
    "devorar": {"nome": "Devorar", "texto": "Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4)."},
    "gloria": {"nome": "Glória", "texto": "Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece."},
    "sobrevivente": {"nome": "Sobrevivente", "texto": "Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece."},
    "escolha_ritmo": {"nome": "Ritmo de Combate", "texto": "Ao entrar em campo, recebe +1 de bônus."},
    "legado": {"nome": "Legado", "texto": "Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior."},
    "devoto": {"nome": "Devoção", "texto": "Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo."},
    "sinergia_faccao": {"nome": "Sinergia de Facção", "texto": "Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo."},
    "espolios": {"nome": "Espólios", "texto": "Se você vencer a rodada com ao menos uma unidade com Espólios em campo, compra 1 carta da reserva (uma compra no total, mesmo com várias)."},
    "gwent_egide": {"nome": "Bênção da Árvore Áurea", "texto": "Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios."},
    "gwent_requiem": {"nome": "Chamado dos Mortos", "texto": "Traz do descarte diretamente ao campo uma unidade escolhida com poder-base até 6; a raridade pode elevar esse limite até 9."},
    "gwent_passo": {"nome": "Passo do Lobo", "texto": "Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira."},
    "dupla_fornalha": {"nome": "Pacto da Fornalha", "texto": "+2 se houver outra unidade aliada na mesma fileira."},
    "irmandade_veu": {"nome": "Formação do Véu", "texto": "+2 se houver outra unidade aliada em uma fileira diferente."},
    "circulo_arcano": {"nome": "Círculo de Ressonância", "texto": "+2 se houver outra unidade aliada na mesma fileira ou uma carta especial no descarte."},
    "gwent_sangramento": {"nome": "Sangramento", "texto": "Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada."},
    "gwent_geada_cariana": {"nome": "Geada Cariana", "texto": "Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Geada; cada marca reduz 1 de poder efetivo até o fim da rodada. A raridade pode aplicar a segunda marca imediatamente a até 3 alvos."},
    "gwent_podrida": {"nome": "Podridão Escarlate", "texto": "Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas."},
    "gwent_loucura": {"nome": "Loucura Frenética", "texto": "Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas."},
    "gwent_chama": {"nome": "Chama do Gigante", "texto": "Remove Geada de todos os aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus."},
    "gwent_invocacao": {"nome": "Lobos Solitários", "texto": "Escolha uma fileira e invoque Lobos Espirituais nela com 3 de poder; a raridade pode elevar o poder da invocação até 6."},
    "gwent_v77_ord_egide": {"nome": "Égide da Graça", "texto": "Escolha um aliado sem Escudo para receber proteção. A raridade pode ampliar a proteção a até 3 aliados; Escudos não bloqueiam sacrifícios."},
    "gwent_v77_ord_hino": {"nome": "Cântico Dourado", "texto": "Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada."},
    "gwent_v77_ord_silencio": {"nome": "Silêncio da Graça", "texto": "Remove o clima ativo das três fileiras para os dois jogadores."},
    "gwent_v77_veu_sangramento": {"nome": "Rito Hemático", "texto": "Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada."},
    "gwent_v77_veu_podrida": {"nome": "Névoa Rubra", "texto": "Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas."},
    "gwent_v77_veu_loucura": {"nome": "Delírio Carmesim", "texto": "Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas."},
    "gwent_v77_veu_execucao": {"nome": "Sentença Carmesim", "texto": "Escolha uma fileira e um inimigo nela. Escudo pode bloquear; se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade amplia o limite de poder efetivo, respeitando o teto do efeito."},
    "gwent_v77_esq_muralha": {"nome": "Bastião das Ruínas", "texto": "Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada."},
    "gwent_v77_esq_chifre": {"nome": "Cântico dos Fiéis", "texto": "Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada."},
    "gwent_v77_esq_medico": {"nome": "Misericórdia Final", "texto": "Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7."},
    "gwent_v77_esq_egide": {"nome": "Vigília do Relicário", "texto": "Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios."},
    "gwent_v77_esq_passo": {"nome": "Procissão dos Fiéis", "texto": "Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira; a raridade pode mover até 3."},
    "gwent_v77_esq_chama": {"nome": "Luz na Geada", "texto": "Remove Geada dos aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus."},
    "gwent_v77_esq_vinculo": {"nome": "Juramento dos Fiéis", "texto": "Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada."},
    "gwent_v77_esq_batedor": {"nome": "Sino do Peregrino", "texto": "Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis."},
    "gwent_v77_esq_purificar": {"nome": "Céu sem Cinzas", "texto": "Remove o clima ativo das três fileiras para os dois jogadores."},
    "gwent_v77_esq_clima": {"nome": "Bruma Sepulcral", "texto": "Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mín. 1); Resistência Climática pode absorver a penalidade."},
    "reliquia_godrick": {"nome": "Grande Runa de Godrick", "texto": "Exige ao menos 1 unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas; uso único por partida."},
    "reliquia_renala": {"nome": "Runa dos Não Nascidos", "texto": "Remove Geada e Podridão dos aliados afetados; cada unidade purificada recebe +1 de bônus. Uso único por partida."},
    "reliquia_morte": {"nome": "Runa da Morte", "texto": "Em cada fileira, a unidade inimiga com maior bônus positivo perde até 2 pontos de bônus (sem ficar negativa). Uso único por partida."},
    "reliquia_noite_chama": {"nome": "Espada da Noite e da Chama", "texto": "Noite: aplica 1 marca de Geada (máx. 2) a todos os inimigos da fileira escolhida. Chama: atinge o inimigo de maior poder efetivo na fileira, reduzindo 1 de poder-base (mín. 1) e 2 de bônus. Escudo bloqueia o golpe; a Relíquia é consumida."},
    "reliquia_lamina_negra": {"nome": "Lâmina Negra", "texto": "Na fileira escolhida, reduz em 3 o bônus do alvo escolhido ou, sem alvo, do inimigo de maior poder efetivo. Escudo é consumido e bloqueia o efeito sem consumir a Relíquia."},
    "reliquia_algemas": {"nome": "Algemas de Margit", "texto": "Na fileira escolhida, zera o bônus positivo do alvo escolhido ou do inimigo com maior bônus. Bônus negativos não mudam; Escudos não bloqueiam o efeito. A ativação consome a Relíquia."},
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
    "gwent_v76_esq_cavaleiro_penitente": "melee", "gwent_v76_esq_peregrino_cinza": "ranged",
    "gwent_v76_esq_guardiao_vitrais": "siege", "gwent_v76_esq_irma_ruinas": "ranged",
    "gwent_v76_esq_confessor_velado": "ranged", "gwent_v76_esq_guardia_santuario": "melee",
    "gwent_v76_esq_cantor_hino": "ranged", "gwent_v76_esq_diaconisa_altar": "siege",
    "gwent_v76_esq_oraculo_silencioso": "siege", "gwent_v76_esq_serafim_caido": "ranged",
    "gwent_v76_esq_martir_cinzento": "melee", "gwent_v76_esq_prelado_ruinas": "siege",
    "gwent_v76_esq_arauto_cantico": "ranged", "gwent_v76_esq_guardiao_relicario": "melee",
    "gwent_v76_esq_santo_sem_nome": "siege", "gwent_v76_esq_anjo_selo": "ranged",
    "gwent_v76_ordem_guardiao_graal": "melee", "gwent_v76_ordem_sentinela_luz": "ranged",
    "gwent_v76_lua_tecela_nevoa": "siege", "gwent_v76_lua_cavaleiro_astral": "melee",
    "gwent_v76_veu_flagelante": "melee", "gwent_v76_veu_lamina_hemantica": "ranged",
    "gwent_v76_veu_carrasco_altar": "melee", "gwent_v76_veu_arauto_sangue": "ranged",
    "gwent_v76_veu_cao_rubro": "melee",
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
    Carta("chefe_rei_afogado", "Godfrey, Primeiro Lorde", "Unidade", 'Ordem Áurea', 7, "Épica", 3, "primeira_luz", "Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias."),
    Carta("chefe_oraculo_ruina", "Gurranq, Clérigo Bestial", "Unidade", 'Ordem Áurea', 7, "Lendária", 4, "impeto", "O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte."),
    Carta("chefe_cacador_sem_rosto", "Assassina da Faca Negra", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "retaliacao", "Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn."),
    Carta("chefe_vigia_cinzento", "Cavaleiro de Leyndell", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "drenagem", "Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea."),
    Carta("chefe_aparicao_veio", "Lâmina Negra Errante", "Unidade", 'Véu Carmesim', 3, "Comum", 1, "adaptacao", "Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa."),
    Carta("chefe_malenia_lamina_miquella", "Malenia, Lâmina de Miquella", "Unidade", 'Véu Carmesim', 9, "Primordial", 6, "scarlet_bloom", "Malenia, Empírea nascida sob a Podridão Escarlate, é filha de Marika e Radagon e irmã gêmea de Miquella. Treinada por um espadachim cego, tornou-se a Lâmina de Miquella e protegeu o irmão em Elphael. Com a Mão de Malenia e suas próteses douradas, enfrentou Radahn em Caelid e liberou a florescência que cobriu a região com Podridão Escarlate. Esta carta retrata Malenia antes de sua transformação em Deusa da Podridão."),
    Carta("chefe_radahn_flagelo_estrelas", "Radahn, Flagelo Estelar", "Unidade", 'Ordem Áurea', 9, "Primordial", 6, "quebra_ritmo", "General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão."),
    Carta("chefe_maliketh_morte_destinada", "Maliketh, Lâmina Negra", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "cacador_arcano", "Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina."),
    Carta("chefe_messmer_impalador", "Messmer, o Empalador", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "quebra_ritmo", "Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras."),
    Carta("chefe_placidusax_lorde_dragao", "Placidusax, Lorde Dragão", "Unidade", 'Lua Negra', 9, "Primordial", 6, "olho_tempestade", "Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido."),
    # Armas
    Carta("arma_lamina_peregrino", "Duelista da Casa Hoslow", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "primeira_luz", "Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue."),
    Carta("arma_martelo_fornalha", "Ferreiro Vulcânico", "Unidade", 'Véu Carmesim', 6, "Rara", 2, "encadeamento", "Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir."),
    Carta("arma_cajado_marulho", "Feiticeiro Cariano", "Unidade", 'Lua Negra', 5, "Rara", 2, "cacador_arcano", "Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua."),
    Carta("arma_duas_luas", "Espadachim da Lua Negra", "Unidade", 'Lua Negra', 7, "Épica", 3, "precisao", "Formado nas artes marciais da realeza cariana, o espadachim treina seus golpes sob a luz fria da Lua Negra e protege os caminhos de Liurnia."),
    Carta("arma_grande_sino", "Sentinela de Leyndell", "Unidade", 'Ordem Áurea', 8, "Lendária", 4, "instinto", "Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada."),
    Carta("arma_agulha_astro", "Leitora de Sellia", "Unidade", 'Lua Negra', 3, "Comum", 1, "primeira_luz", "Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna."),
    Carta("arma_lanca_fornalha", "Lanceiro da Árvore Áurea", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "primeira_luz", "Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar."),
    Carta("arma_arco_peregrino", "Batedor de Gelmir", "Unidade", 'Véu Carmesim', 5, "Comum", 1, "impeto", "Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos."),
    # Magias
    Carta("magia_brasa_errante", "Monge do Fogo", "Unidade", 'Lua Negra', 3, "Comum", 1, "sangue_frio", "Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes."),
    Carta("magia_selo_vigilia", "Confessora da Ordem Áurea", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "adaptacao", "Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo."),
    Carta("magia_trovao_oco", "Dragoeiro Ancião", "Unidade", 'Ordem Áurea', 6, "Épica", 3, "drenagem", "Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha."),
    Carta("magia_nevoa_antiga", "Astróloga de Liurnia", "Unidade", 'Lua Negra', 7, "Épica", 3, "encadeamento", "Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos."),
    Carta("magia_sol_negro", "Apóstolo da Pele Divina", "Unidade", 'Véu Carmesim', 8, "Lendária", 4, "quebra_ritmo", "Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses."),
    Carta("magia_fagulha", "Aprendiz Cariano", "Unidade", 'Lua Negra', 4, "Comum", 1, "cacador_arcano", "Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante."),
    Carta("magia_orbe_eco", "Erudito da Academia", "Unidade", 'Lua Negra', 4, "Comum", 1, "precisao", "Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes."),
    Carta("magia_chama_fria", "Feiticeira da Lua Gélida", "Unidade", 'Lua Negra', 3, "Comum", 1, "sangue_frio", "A feiticeira percorre Liurnia estudando as artes gélidas dos antigos astrólogos e os encantamentos lunares preservados pela realeza cariana."),
    # Covenants / juramentos
    Carta("covenant_lobos_cinza", "Cavaleiros de Radahn", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "instinto", "Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid."),
    Carta("covenant_lua_velada", "Juramentada de Ranni", "Unidade", 'Lua Negra', 6, "Épica", 3, "primeira_luz", "Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea."),
    Carta("covenant_sentinelas", "Guardiões de Sellia", "Unidade", 'Lua Negra', 4, "Comum", 1, "adaptacao", "Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria."),
    Carta("covenant_coroa_abismo", "Cavaleiro de Mohgwyn", "Unidade", 'Véu Carmesim', 7, "Lendária", 4, "drenagem", "Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg."),
    Carta("covenant_ultimos", "Cavaleiros Juramentados", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "ultimo_folego", "Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego."),
    Carta("covenant_filhos_brasa", "Discípulos do Fogo", "Unidade", 'Ordem Áurea', 5, "Comum", 1, "contragolpe", "Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos."),
    Carta("covenant_peregrinos_nevoa", "Peregrinos de Nokron", "Unidade", 'Lua Negra', 4, "Comum", 1, "primeira_luz", "Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela."),
    Carta("covenant_irmandade_ferro", "Guardas da Árvore Áurea", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "retaliacao", "Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea."),
    # Cartas especiais do modo Gwent: entram na coleção por recompensas/pacotes do Discord.
    Carta("gwent_especial_tempestade", "Tempestade dos Picos", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_clima", "Nas encostas dos Picos dos Gigantes, tempestades antigas varrem os desfiladeiros e castigam os viajantes que desafiam o inverno."),
    Carta("gwent_especial_nevoa", "Miasma da Podridão", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_nevoa", "O hálito dos pântanos de Caelid carrega esporos da Podridão Escarlate, transformando o ar em uma névoa difícil de atravessar."),
    Carta("gwent_especial_geada", "Geada dos Picos", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_geada", "O vento que desce dos Picos dos Gigantes congela os caminhos e cobre de gelo as ruínas esquecidas."),
    Carta("gwent_especial_chuva", "Sangue Corrompido", "Especial", 'Véu Carmesim', 0, "Comum", 1, "gwent_chuva", "Nos degraus do Palácio de Mohgwyn, o sangue derramado alimenta os ritos dos devotos que oferecem sua devoção à Mãe Sem Forma."),
    Carta("gwent_especial_chifre", "Rugido de Godfrey", "Especial", 'Ordem Áurea', 0, "Épica", 3, "gwent_chifre", "O rugido de Godfrey, o Primeiro Lorde Prístino, ainda ressoa nos campos de batalha como memória dos guerreiros que o seguiram."),
    Carta("gwent_especial_medico", "Lágrima Sagrada", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_medico", "Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada."),
    Carta("gwent_especial_queima", "Chama Negra", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_queima", "A chama negra nasceu do poder da Runa da Morte e foi usada pelos Apóstolos da Pele Divina para caçar os próprios deuses."),
    Carta("gwent_especial_purificar", "Lei da Regressão", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_purificar", "A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo."),
    Carta("gwent_especial_execucao", "Lâmina da Morte Destinada", "Especial", 'Ordem Áurea', 0, "Épica", 3, "gwent_execucao", "A lâmina fragmentada carrega a Morte Destinada que Maliketh selou, lembrança de uma força capaz de pôr fim até à imortalidade dos semideuses."),
    Carta("gwent_especial_vinculo", "Juramento do Crisol", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_vinculo", "Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree."),
    Carta("gwent_especial_batedor", "Passo do Cão de Caça", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_batedor", "Os Cavaleiros do Cão de Caça perseguem suas presas sem hesitação; seu passo silencioso os conduz pelas sombras antes que o alvo perceba a aproximação."),
    Carta("gwent_especial_muralha", "Bastião de Leyndell", "Especial", 'Ordem Áurea', 0, "Comum", 1, "gwent_muralha", "As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital."),
    # Táticas de estado inspiradas nos efeitos de Elden Ring.
    Carta("elden_especial_sangramento", "Ritual de Sangue", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_sangramento", "Os acólitos de Mohgwyn repetem antigos ritos de sangue diante da Mãe Sem Forma, oferecendo feridas e devoção à dinastia carmesim."),
    Carta("elden_especial_geada", "Lua Cheia de Rennala", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_geada_cariana", "A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana."),
    Carta("elden_especial_podrida", "Flor da Podridão Escarlate", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_podrida", "Na planície de Aeonia, a florescência de Malenia deixou uma flor escarlate; desde então, a Podridão se espalha pelas terras feridas de Caelid."),
    Carta("elden_especial_loucura", "Chama Frenética", "Especial", 'Lua Negra', 0, "Épica", 3, "gwent_loucura", "A chama oferecida pelos Três Dedos invade os olhos dos que a contemplam e reduz vontade, carne e lembranças a um único caos ardente."),
    Carta("elden_especial_chama", "Chama do Gigante", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_chama", "Nos Picos dos Gigantes, o último de sua linhagem guarda a chama eterna da Forja, cujo poder ainda pode incendiar a Árvore Áurea."),
    Carta("elden_especial_invocacao", "Lobos Solitários", "Especial", 'Lua Negra', 0, "Rara", 2, "gwent_invocacao", "Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres."),
    # V19 — Relíquias: cada jogador pode ativar apenas uma por partida.
    Carta("reliquia_grande_runa_godrick", "Grande Runa de Godrick", "Especial", 'Ordem Áurea', 0, "Lendária", 4, "reliquia_godrick", "Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto."),
    Carta("reliquia_runa_nao_nascidos", "Runa dos Não Nascidos", "Especial", 'Lua Negra', 0, "Lendária", 4, "reliquia_renala", "A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada."),
    Carta("reliquia_runa_morte", "Runa da Morte", "Especial", 'Véu Carmesim', 0, "Mítica", 5, "reliquia_morte", "O fragmento da Morte Destinada guarda a força que Maliketh selou para impedir que a morte verdadeira retornasse às Terras Intermédias."),
    Carta("reliquia_noite_chama", "Espada da Noite e da Chama", "Especial", 'Lua Negra', 0, "Lendária", 4, "reliquia_noite_chama", "Herança da família real cariana, a espada preserva duas tradições arcanas antigas: a feitiçaria da noite e a chama dos gigantes."),
    Carta("reliquia_lamina_negra", "Lâmina Negra", "Especial", 'Véu Carmesim', 0, "Mítica", 5, "reliquia_lamina_negra", "Maliketh empunha a Lâmina Negra para manter selada a Morte Destinada, poder que Marika confiou ao seu guardião para sustentar a ordem sem morte."),
    Carta("reliquia_algemas_margit", "Algemas de Margit", "Especial", 'Ordem Áurea', 0, "Épica", 3, "reliquia_algemas", "Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível."),
    # Novas unidades de facção e sinergia.
    Carta("gwent_unidade_baluarte", "Cavaleiro do Crisol", "Unidade", 'Ordem Áurea', 6, "Rara", 2, "guardiao_fileira", "Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina."),
    Carta("gwent_unidade_lamina_sem_juramento", "Caçador de Dedos", "Unidade", 'Véu Carmesim', 6, "Rara", 2, "cacador_solitario", "Entre as trilhas esquecidas das Terras Intermédias, o caçador segue o rastro dos emissários dos Dois Dedos e evita qualquer juramento que limite sua caça."),
    Carta("gwent_unidade_portaestandarte", "Porta-estandarte Áureo", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "estandarte", "O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital."),
    Carta("gwent_unidade_oraculo_clima", "Profeta de Liurnia", "Unidade", 'Lua Negra', 5, "Rara", 2, "resistencia_climatica", "O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas."),
    Carta("gwent_unidade_eco", "Erudito das Pedras", "Unidade", 'Lua Negra', 5, "Rara", 2, "eco_arcano", "Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas."),
    Carta("gwent_unidade_cavaleira", "Cavaleira Cariana", "Unidade", 'Lua Negra', 5, "Comum", 1, "quebra_ritmo", "A cavaleira recebeu treinamento nas fileiras da realeza cariana e guarda as passagens de Liurnia com a disciplina dos antigos juramentos lunares."),
    Carta("gwent_unidade_gigante", "Gigante de Fogo", "Unidade", 'Ordem Áurea', 7, "Épica", 3, "instinto", "Último de sua linhagem, o Gigante de Fogo guarda a chama primordial nos Picos dos Gigantes e carrega o dever de impedir que ela se apague."),
    Carta("gwent_unidade_cartografa", "Exploradora de Nokron", "Unidade", 'Lua Negra', 4, "Comum", 1, "adaptacao", "Sob o céu subterrâneo de Nokron, a exploradora mapeia pontes suspensas e passagens ocultas entre os palácios em ruínas."),
    Carta("gwent_unidade_invocador", "Apóstolo Errante", "Unidade", 'Véu Carmesim', 7, "Épica", 3, "cacador_arcano", "O apóstolo errante percorre as estradas em busca de manuscritos proibidos, levando consigo os ritos que aprendeu com seus mestres."),
    Carta("gwent_unidade_mestre_forja", "Ferreiro de Gelmir", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "dupla_fornalha", "Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes."),
    Carta("gwent_unidade_dupla_veu", "Gêmeas da Cidade Eterna", "Unidade", 'Lua Negra', 5, "Rara", 2, "irmandade_veu", "Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas."),
    Carta("gwent_unidade_circulo", "Discípulo da Academia", "Unidade", 'Lua Negra', 5, "Rara", 2, "circulo_arcano", "Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria."),

    # Etapa 2: unidades de facção que usam os efeitos de ciclo de vida (escudo, queda, ressurreição...).
    # Ordem Áurea — muralha (escudo/sobrevivência/vingança) e banquete (devorar/espólios).
    Carta("gwent_unidade_sentinela_rubra", "Cavaleiro de Radahn", "Unidade", 'Ordem Áurea', 4, "Comum", 1, "escudo_ferro", "Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid."),
    Carta("gwent_unidade_veterano_cercos", "Cavaleiro Draconiano", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "sobrevivente", "Revestido de escamas e armadura dourada, o cavaleiro draconiano guarda os acessos da capital; seus golpes carregam o trovão dos dragões ancestrais."),
    Carta("gwent_unidade_herdeiro_portao", "Godwyn, o Dourado", "Unidade", 'Ordem Áurea', 6, "Épica", 3, "vinganca", "O príncipe dourado foi amado por dragões e homens; sua queda marcou a primeira rachadura irreversível no destino das Terras Intermédias."),
    Carta("gwent_unidade_carniceiro_forja", "Carrasco de Gelmir", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "devorar", "Um executor da Mansão Vulcânica veste o aço manchado dos recusantes e serve aos banquetes de Tanith."),
    Carta("gwent_unidade_intendente", "Mercador Nômade", "Unidade", 'Ordem Áurea', 3, "Comum", 1, "espolios", "Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos."),
    # Lua Negra — fantasmas (retorno e persistência) e caravana (saque e blindagem).
    Carta("gwent_unidade_cacadora_fantasma", "Assassina de Ravenmount", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "sobrevivente", "Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir."),
    Carta("gwent_unidade_cantora_lamentos", "Fia, Leito de Morte", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "ressurgir", "Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos."),
    Carta("gwent_unidade_senhor_cacada", "Blaidd, o Meio-Lobo", "Unidade", 'Lua Negra', 6, "Épica", 3, "vinganca", "Sombra meio-lobo jurada a Ranni, Blaidd protege a princesa lunar desde a infância. A lealdade que o liga a ela o coloca em conflito com o destino imposto pelos Dois Dedos."),
    Carta("gwent_unidade_saqueadora_veu", "Ladina da Cidade Eterna", "Unidade", 'Lua Negra', 4, "Comum", 1, "espolios", "Nas passagens ocultas de Nokron, a ladina recolhe relíquias esquecidas e evita os sentinelas que guardam a Cidade Eterna."),
    Carta("gwent_unidade_contrabandista", "Recusante Vulcânico", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "escudo_ferro", "Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir."),
    # Véu Carmesim — rúnico (proteção e retorno) e eclipse (consumo e conhecimento).
    Carta("gwent_unidade_guardiao_runas", "Guardião da Ordem Áurea", "Unidade", 'Ordem Áurea', 5, "Comum", 1, "escudo_ferro", "Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital."),
    Carta("gwent_unidade_necromante", "Servo dos Mortos", "Unidade", 'Lua Negra', 4, "Rara", 2, "ressurgir", "Um devoto da raiz da morte percorre criptas esquecidas, guiado por sussurros que os vivos não conseguem ouvir."),
    Carta("gwent_unidade_detonador", "Guerreiro Frenético", "Unidade", 'Véu Carmesim', 6, "Épica", 3, "vinganca", "A chama frenética tomou-lhe os olhos e apagou o nome que um dia teve; agora, ele vagueia pelas Terras Intermédias sob a influência dos Três Dedos."),
    Carta("gwent_unidade_devorador_mana", "Cavaleiro Sangrento", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "devorar", "Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea."),
    Carta("gwent_unidade_bibliotecaria", "Bibliotecária de Raya", "Unidade", 'Lua Negra', 4, "Comum", 1, "espolios", "Entre os salões da Academia de Raya Lucaria, a bibliotecária guarda os estudos de pedra cintilante e os escritos que sobreviveram às disputas dos sábios."),

    # Etapa 2: cartas especiais novas (todas funcionam sem alvo escolhido; `target_id` apenas refina).
    Carta("gwent_especial_egide", "Bênção da Árvore Áurea", "Especial", 'Ordem Áurea', 0, "Rara", 2, "gwent_egide", "Quando a Graça alcança os santuários de Leyndell, os guardiões renovam seus votos diante da Árvore Áurea e recebem sua bênção dourada."),
    Carta("gwent_especial_requiem", "Chamado dos Mortos", "Especial", 'Os Esquecidos', 0, "Épica", 3, "gwent_requiem", "Um cântico atravessa as catacumbas e ecoa entre os nomes que a história tentou apagar."),
    Carta("gwent_especial_passo", "Passo do Lobo", "Especial", 'Véu Carmesim', 0, "Rara", 2, "gwent_passo", "Nas terras devastadas de Caelid, os lobos seguem rastros de sangue entre ruínas e desfiladeiros, alcançando presas que julgavam ter escapado."),
    Carta("gwent_mitica_coroa", "Cavaleiro Consagrado", "Unidade", 'Ordem Áurea', 8, "Mítica", 5, "estandarte", "Um cavaleiro consagrado guarda os ramos pálidos do Haligtree, onde a esperança resiste à decadência."),
    Carta("gwent_singular_primeiro", "Juramento Primordial", "Unidade", 'Véu Carmesim', 10, "Singular", 0, "cacador_solitario", "O juramento foi selado quando o Crisol ainda reunia as formas primordiais da vida, antes de a ordem dourada definir as fronteiras do mundo."),
    Carta("gwent_singular_intocavel", "Adaga da Faca Negra", "Unidade", 'Véu Carmesim', 9, "Singular", 0, "precisao", "Forjada para as Assassinas da Faca Negra, a lâmina recebeu um fragmento da Runa da Morte na noite em que Godwyn foi assassinado."),
    Carta("gwent_singular_nivel1", "Vontade de Marika", "Unidade", 'Ordem Áurea', 10, "Singular", 0, "ultimo_folego", "A vontade da Rainha Eterna permanece gravada no Anel Prístino; mesmo após sua ruptura, seus fragmentos continuam a determinar o destino das Terras Intermédias."),
     Carta("gwent_singular_cacador_chefes", "Coroa do Lorde Prístino", "Unidade", 'Lua Negra', 9, "Singular", 0, "paradoxo_eterno", "A coroa relembra o reinado de Godfrey, o Primeiro Lorde Prístino, e os guerreiros que abriram caminho para o domínio da Árvore Áurea."),
    # Nova facção: Os Esquecidos (Luteranos)
    Carta("luterano_cruzado", "Cruzado Esquecido", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "sinergia_faccao", "Um guerreiro sagrado guarda as estradas em ruínas e carrega no escudo o símbolo de uma ordem que já não existe."),
    Carta("luterano_missionario", "Missionário Esquecido", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "legado", "Nas capelas esquecidas, este missionário preserva escrituras da antiga irmandade e mantém seus ritos vivos entre os poucos fiéis que restaram."),
    Carta("luterano_bispo", "Bispo Esquecido", "Unidade", 'Os Esquecidos', 5, "Lendária", 4, "devoto", "Mesmo após a queda das catedrais, o bispo reúne os sobreviventes dos Esquecidos e conduz suas preces entre as colunas partidas do antigo santuário."),
    Carta("luterano_anjo", "Anjo Esquecido", "Unidade", 'Os Esquecidos', 3, "Épica", 3, "gloria", "Um mensageiro alado atravessa os vitrais partidos da antiga catedral, levando uma luz que quase se apagou."),
    Carta("luterano_papa", "Papa Esquecido", "Unidade", 'Os Esquecidos', 7, "Mítica", 5, "sinergia_faccao", "Sumo sacerdote dos Esquecidos, governa uma ordem que sobreviveu à queda de seus templos."),
    Carta("luterano_sacerdote", "Sacerdote Esquecido", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "devoto", "Um sacerdote conserva os ritos de sua ordem em um santuário quase tomado pelo tempo."),
    Carta("luterano_irmao", "Irmão Esquecido", "Unidade", 'Os Esquecidos', 3, "Comum", 1, "legado", "Um peregrino humilde permanece ao lado de sua irmandade, mesmo quando todos os demais recuam."),
    Carta("luterano_diacon", "Diácono Esquecido", "Unidade", 'Os Esquecidos', 2, "Comum", 1, "escolha_ritmo", "Nas capelas dos Esquecidos, o diácono alimenta as lamparinas do altar e conduz os ritos que os sacerdotes já não conseguem manter."),
]

CARTAS_PRIMORDIAIS = [
    Carta("primordial_origem", "Besta Prístina", "Unidade", 'Ordem Áurea', 8, "Primordial", 6, "lei_primeva", "A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada."),
    Carta("primordial_trono", "Marika, Rainha Eterna", "Unidade", 'Ordem Áurea', 8, "Primordial", 6, "decreto_soberano", "Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias."),
    Carta("primordial_tempestade", "Placidusax, Senhor Dragão", "Unidade", 'Lua Negra', 8, "Primordial", 6, "olho_tempestade", "Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula."),
    Carta("primordial_abismo", "Mãe Sem Forma", "Unidade", 'Véu Carmesim', 8, "Primordial", 6, "fome_abismo", "A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo."),
    Carta("primordial_eternidade", "Maliketh, Guardião da Morte", "Unidade", 'Ordem Áurea', 8, "Primordial", 6, "paradoxo_eterno", "Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika."),
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

# Expansão V75 — expansão histórica com unidades das quatro facções.
# Seis cartas Luteranas foram reclassificadas na revisão V76 sem alterar seus IDs.
CARTAS_EXPANSAO_V75 = [
    # ORDEM ÁUREA — formação, proteção e purificação.
    Carta("gwent_v75_ordem_veterano_juramento", "Veterano do Juramento", "Unidade", 'Ordem Áurea', 4, "Rara", 2, "", "Veterano das muralhas internas de Leyndell, traz no escudo o juramento feito diante da Árvore Áurea.", fileira="melee"),
    Carta("gwent_v75_ordem_guardiao_crisol", "Guardião do Crisol Menor", "Unidade", 'Ordem Áurea', 4, "Rara", 2, "", "O guardião carrega as marcas do Crisol, vestígios das formas primordiais que existiam antes de a Árvore Áurea moldar a ordem das Terras Intermédias.", fileira="melee"),
    Carta("gwent_v75_ordem_confessora_graca", "Confessora da Graça", "Unidade", 'Ordem Áurea', 5, "Épica", 3, "", "Uma Confessora percorre os caminhos de Leyndell em silêncio, levando os ensinamentos da Lei da Regressão aos santuários esquecidos.", fileira="siege"),
    Carta("gwent_v75_ordem_arauto_estandarte", "Arauto Áureo", "Unidade", 'Ordem Áurea', 5, "Épica", 3, "", "O arauto ergue o estandarte de Leyndell e proclama, diante das muralhas, o juramento que une os defensores à Ordem Áurea.", fileira="ranged"),

    # VÉU CARMESIM — marcas de Sangramento, pressão e sacrifício calculado.
    Carta("gwent_v75_veu_acolito_sangue", "Acólito Sanguíneo", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "", "Um acólito do Palácio de Mohgwyn prepara o altar para os ritos secretos da dinastia e reverencia a chama do sangue.", fileira="ranged"),
    Carta("gwent_v75_veu_devota_hemorragia", "Devota da Hemorragia", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "", "A devota ajoelha-se diante do altar de Mohgwyn e oferece seu sangue à dinastia que aguarda o nascimento de uma nova era.", fileira="siege"),
    Carta("gwent_v75_veu_carrasco_preco", "Carrasco Carmesim", "Unidade", 'Véu Carmesim', 5, "Épica", 3, "", "O carrasco conduz procissões sob estandartes vermelhos, vestindo as vestes cerimoniais dos guerreiros de Mohgwyn.", fileira="melee"),
    Carta("gwent_v75_veu_cacador_sangue", "Caçador de Mohgwyn", "Unidade", 'Véu Carmesim', 5, "Épica", 3, "", "O caçador patrulha os salões do Palácio de Mohgwyn, seguindo os rastros deixados pelos ritos sangrentos da dinastia.", fileira="ranged"),

    # LUA NEGRA — Geada, leitura de campo e controle gravitacional.
    Carta("gwent_v75_lua_oraculo_geada", "Oráculo Gélido de Sellia", "Unidade", 'Lua Negra', 4, "Rara", 2, "", "Uma astróloga de Sellia lê presságios nas lâminas de gelo que se formam sobre as águas imóveis da cidade.", fileira="siege"),
    Carta("gwent_v75_lua_cartografo_lunar", "Cartógrafo de Nokron", "Unidade", 'Lua Negra', 4, "Rara", 2, "", "À luz das estrelas subterrâneas, o cartógrafo registra pontes, aquedutos e passagens ocultas que ligam as ruínas de Nokron.", fileira="ranged"),
    Carta("gwent_v75_lua_graviturgista", "Graviturgista de Nokron", "Unidade", 'Lua Negra', 5, "Épica", 3, "", "Um astrólogo das Cidades Eternas estuda as correntes gravitacionais que sustentam as ruínas suspensas de Nokron.", fileira="siege"),
    Carta("gwent_v75_lua_guardia", "Guardiã do Juramento Lunar", "Unidade", 'Lua Negra', 5, "Épica", 3, "", "A guardiã preserva os antigos pactos da realeza cariana e vigia os caminhos escolhidos por Ranni sob a luz fria da lua.", fileira="melee"),
    # Nova facção: Os Esquecidos — fé, tradição e rituais sagrados.
    Carta("luterano_apostolo", "Apóstolo Esquecido", "Unidade", 'Os Esquecidos', 5, "Épica", 3, "", "Um pregador percorre as estradas douradas com fragmentos de escrituras antigas.", fileira="melee"),
    Carta("luterano_pastor", "Pastor Esquecido", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "legado", "Um guia errante conduz os fiéis por trilhas esquecidas e capelas abandonadas.", fileira="ranged"),
    Carta("luterano_mistico", "Místico Esquecido", "Unidade", 'Os Esquecidos', 5, "Rara", 2, "devoto", "Um intérprete de sinais antigos contempla as estrelas sobre as ruínas de Sellia.", fileira="siege"),
    Carta("luterano_profeta", "Profeta Esquecido", "Unidade", 'Os Esquecidos', 6, "Mítica", 5, "sinergia_faccao", "O profeta reúne os últimos fiéis sob os vitrais partidos de Leyndell e interpreta as escrituras que sobreviveram à queda de sua irmandade.", fileira="melee"),
    Carta("luterano_vigia", "Vigia da Noite", "Unidade", 'Os Esquecidos', 3, "Comum", 1, "gloria", "Um sentinela solitário vigia os portões enquanto a noite cobre as ruínas.", fileira="melee"),
    Carta("luterano_anjo2", "Anjo de Segunda Ordem", "Unidade", 'Os Esquecidos', 5, "Lendária", 4, "gloria", "Uma presença alada atravessa os salões esquecidos, iluminando os vitrais partidos.", fileira="siege"),
]


# Expansão V76 — revisão de equilíbrio e expansão de Os Esquecidos.
# Após corrigir a facção de seis cartas Luteranas que estavam classificadas em
# outras casas, todas as quatro facções passam a ter exatamente 30 unidades.
CARTAS_EXPANSAO_V76 = [
    # OS ESQUECIDOS — 16 unidades: fé, proteção, irmandade e retorno dos caídos.
    Carta("gwent_v76_esq_cavaleiro_penitente", "Cavaleiro Penitente", "Unidade", 'Os Esquecidos', 4, "Comum", 1, "escudo_ferro", "Um cavaleiro cobre o próprio escudo com cinzas e guarda a passagem de uma capela soterrada.", fileira="melee"),
    Carta("gwent_v76_esq_peregrino_cinza", "Peregrino das Cinzas", "Unidade", 'Os Esquecidos', 3, "Comum", 1, "legado", "Um viajante cruza estradas cobertas de cinza levando consigo as últimas páginas de um evangelho perdido.", fileira="ranged"),
    Carta("gwent_v76_esq_guardiao_vitrais", "Guardião dos Vitrais", "Unidade", 'Os Esquecidos', 4, "Comum", 1, "estandarte", "Um sentinela permanece diante dos vitrais partidos, protegendo os símbolos de uma fé quase apagada.", fileira="siege"),
    Carta("gwent_v76_esq_irma_ruinas", "Irmã das Ruínas", "Unidade", 'Os Esquecidos', 3, "Comum", 1, "", "Uma irmã recolhe velas e fragmentos de escritura nas galerias abandonadas do antigo mosteiro.", fileira="ranged"),

    Carta("gwent_v76_esq_confessor_velado", "Confessor Velado", "Unidade", 'Os Esquecidos', 5, "Rara", 2, "devoto", "Sob um capuz de linho, o confessor ouve os últimos arrependimentos dos viajantes que chegam à cripta.", fileira="ranged"),
    Carta("gwent_v76_esq_guardia_santuario", "Guardiã do Santuário", "Unidade", 'Os Esquecidos', 5, "Rara", 2, "guardiao_fileira", "Uma defensora vigia o altar de pedra e mantém a entrada do santuário livre de profanadores.", fileira="melee"),
    Carta("gwent_v76_esq_cantor_hino", "Cantor do Último Hino", "Unidade", 'Os Esquecidos', 4, "Rara", 2, "sobrevivente", "Sua voz ecoa por uma nave vazia enquanto os últimos fiéis abandonam a catedral em ruínas.", fileira="ranged"),
    Carta("gwent_v76_esq_diaconisa_altar", "Diaconisa do Altar", "Unidade", 'Os Esquecidos', 5, "Rara", 2, "escolha_ritmo", "A diaconisa prepara o altar com cálices antigos e conduz um rito antes da chegada dos invasores.", fileira="siege"),

    Carta("gwent_v76_esq_oraculo_silencioso", "Oráculo Silencioso", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "eco_arcano", "Entre colunas rachadas, um oráculo interpreta inscrições que sobreviveram à queda do santuário.", fileira="siege"),
    Carta("gwent_v76_esq_serafim_caido", "Serafim Caído", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "gloria", "Um serafim de asas marcadas desce sobre a catedral, recolhendo as últimas preces entre as ruínas.", fileira="ranged"),
    Carta("gwent_v76_esq_martir_cinzento", "Mártir Cinzento", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "vinganca", "Ferido diante do relicário, o mártir permanece de pé para impedir que a chama sagrada se apague.", fileira="melee"),
    Carta("gwent_v76_esq_prelado_ruinas", "Prelado das Ruínas", "Unidade", 'Os Esquecidos', 6, "Épica", 3, "sinergia_faccao", "O prelado reúne os sobreviventes sob os arcos desmoronados e ergue o antigo selo da irmandade.", fileira="siege"),

    Carta("gwent_v76_esq_arauto_cantico", "Arauto do Cântico", "Unidade", 'Os Esquecidos', 7, "Lendária", 4, "estandarte", "Com um estandarte bordado em prata gasta, o arauto conduz os fiéis através do vale coberto de névoa.", fileira="ranged"),
    Carta("gwent_v76_esq_guardiao_relicario", "Guardião do Relicário", "Unidade", 'Os Esquecidos', 7, "Lendária", 4, "ressurgir", "Um guardião protege as relíquias da ordem numa câmara selada sob a antiga catedral.", fileira="melee"),

    Carta("gwent_v76_esq_santo_sem_nome", "Santo Sem Nome", "Unidade", 'Os Esquecidos', 8, "Mítica", 5, "sinergia_faccao", "Uma figura venerada sem registro nos livros atravessa o santuário, envolta em luz pálida e poeira dourada.", fileira="siege"),
    Carta("gwent_v76_esq_anjo_selo", "Anjo do Último Selo", "Unidade", 'Os Esquecidos', 8, "Mítica", 5, "gloria", "O último guardião alado desce diante do portão selado, com as asas abertas sobre os fiéis restantes.", fileira="ranged"),

    # ORDEM ÁUREA — duas reposições para preservar 30 unidades após a correção de facção.
    Carta("gwent_v76_ordem_guardiao_graal", "Guardião do Graal", "Unidade", 'Ordem Áurea', 4, "Rara", 2, "guardiao_fileira", "Nos salões inferiores de Leyndell, o guardião jurou proteger o cálice consagrado que os sacerdotes ocultaram durante a queda da capital.", fileira="melee"),
    Carta("gwent_v76_ordem_sentinela_luz", "Sentinela da Graça", "Unidade", 'Ordem Áurea', 5, "Rara", 2, "estandarte", "Uma sentinela ergue o estandarte dourado sobre a muralha voltada para a Árvore Áurea.", fileira="ranged"),

    # LUA NEGRA — duas reposições para preservar 30 unidades após a correção.
    Carta("gwent_v76_lua_tecela_nevoa", "Tecelã da Névoa", "Unidade", 'Lua Negra', 4, "Rara", 2, "eco_arcano", "Uma feiticeira traça runas no ar e observa a névoa se fechar sobre as ruínas de Nokron.", fileira="siege"),
    Carta("gwent_v76_lua_cavaleiro_astral", "Cavaleiro Astral", "Unidade", 'Lua Negra', 5, "Rara", 2, "resistencia_climatica", "Um cavaleiro cariano avança sob uma chuva de cristais sem desviar os olhos do céu noturno.", fileira="melee"),

    # VÉU CARMESIM — cinco reposições para preservar 30 unidades após a correção.
    Carta("gwent_v76_veu_flagelante", "Flagelante de Mohgwyn", "Unidade", 'Véu Carmesim', 4, "Rara", 2, "legado", "Um penitente percorre os degraus do palácio sanguíneo, deixando marcas vermelhas na pedra.", fileira="melee"),
    Carta("gwent_v76_veu_lamina_hemantica", "Lâmina Hemática", "Unidade", 'Véu Carmesim', 5, "Rara", 2, "contragolpe", "Uma duelista da dinastia sanguínea desembainha uma lâmina estreita diante do altar de Mohgwyn.", fileira="ranged"),
    Carta("gwent_v76_veu_carrasco_altar", "Carrasco do Altar", "Unidade", 'Véu Carmesim', 6, "Épica", 3, "devorar", "O carrasco executa os ritos de sacrifício no altar rubro, sob os estandartes da dinastia.", fileira="melee"),
    Carta("gwent_v76_veu_arauto_sangue", "Arauto do Sangue", "Unidade", 'Véu Carmesim', 6, "Épica", 3, "estandarte", "Um arauto percorre a procissão carmesim carregando o símbolo da chama sanguínea.", fileira="ranged"),
    Carta("gwent_v76_veu_cao_rubro", "Cão Rubro", "Unidade", 'Véu Carmesim', 4, "Comum", 1, "instinto", "Um cão de guerra fareja intrusos entre as muralhas úmidas do palácio de Mohgwyn.", fileira="melee"),
]


# Expansão V77 — normalização dos pools táticos: 11 especiais por facção.
# Os efeitos usam handlers já existentes; cada carta tem ID próprio, texto temático
# próprio e o mesmo efeito canônico no servidor, na API e na interface.
CARTAS_EXPANSAO_V77 = [
    # ORDEM ÁUREA: 3 novas especiais (8 -> 11).
    Carta("gwent_v77_ord_egide", "Égide da Graça", "Especial", "Ordem Áurea", 0, "Rara", 2, "gwent_v77_ord_egide", "Uma muralha de luz dourada envolve os defensores que juraram proteger a Árvore Áurea."),
    Carta("gwent_v77_ord_hino", "Cântico Dourado", "Especial", "Ordem Áurea", 0, "Rara", 2, "gwent_v77_ord_hino", "O coro dos sacerdotes atravessa as muralhas de Leyndell, celebrando a ordem estabelecida sob a luz da Árvore Áurea."),
    Carta("gwent_v77_ord_silencio", "Silêncio Dourado", "Especial", "Ordem Áurea", 0, "Épica", 3, "gwent_v77_ord_silencio", "Quando os sacerdotes da Ordem Áurea erguem a voz, o brilho da Graça recobre as muralhas e silencia os presságios do céu."),

    # VÉU CARMESIM: 4 novas especiais (7 -> 11).
    Carta("gwent_v77_veu_sangramento", "Rito Hemático", "Especial", "Véu Carmesim", 0, "Rara", 2, "gwent_v77_veu_sangramento", "No altar subterrâneo, os acólitos de Mohgwyn repetem o rito de sangue e juram sua devoção à dinastia carmesim."),
    Carta("gwent_v77_veu_podrida", "Névoa Rubra", "Especial", "Véu Carmesim", 0, "Rara", 2, "gwent_v77_veu_podrida", "Uma névoa escarlate paira sobre o Palácio de Mohgwyn, nascida dos ritos que oferecem sangue à Mãe Sem Forma."),
    Carta("gwent_v77_veu_loucura", "Delírio Carmesim", "Especial", "Véu Carmesim", 0, "Épica", 3, "gwent_v77_veu_loucura", "Nos salões de Mohgwyn, os devotos entoam um cântico febril à Mãe Sem Forma e se perdem no êxtase do sangue."),
    Carta("gwent_v77_veu_execucao", "Sentença Carmesim", "Especial", "Véu Carmesim", 0, "Lendária", 4, "gwent_v77_veu_execucao", "No altar de Mohgwyn, o carrasco recebe a lâmina ritual e pronuncia a sentença sobre aqueles que traíram a dinastia."),

    # OS ESQUECIDOS: 10 novas especiais (1 -> 11).
    Carta("gwent_v77_esq_muralha", "Bastião das Ruínas", "Especial", "Os Esquecidos", 0, "Comum", 1, "gwent_v77_esq_muralha", "Os últimos guardiões se abrigam sob os arcos quebrados e juram impedir que as ruínas de sua antiga irmandade sejam profanadas."),
    Carta("gwent_v77_esq_chifre", "Cântico dos Fiéis", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_chifre", "Nas ruínas, os fiéis entoam o último cântico da irmandade e preservam uma tradição que o tempo tentou apagar."),
    Carta("gwent_v77_esq_medico", "Misericórdia Final", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_medico", "Nas catacumbas dos Esquecidos, uma irmã recolhe os que tombaram e pronuncia a última prece antes de conduzi-los de volta à irmandade."),
    Carta("gwent_v77_esq_egide", "Vigília do Relicário", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_egide", "Os monges dos Esquecidos velam a relíquia sem nome, repetindo preces antigas para impedir que a última luz do santuário se apague."),
    Carta("gwent_v77_esq_passo", "Procissão dos Fiéis", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_passo", "Sob estandartes gastos, os sobreviventes cruzam as ruínas em procissão e mantêm viva a fé que ainda os reúne."),
    Carta("gwent_v77_esq_chama", "Luz na Geada", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_chama", "Entre os Esquecidos, uma chama pálida é mantida acesa nos invernos mais cruéis, lembrando aos peregrinos que ainda existe abrigo."),
    Carta("gwent_v77_esq_vinculo", "Juramento dos Fiéis", "Especial", "Os Esquecidos", 0, "Épica", 3, "gwent_v77_esq_vinculo", "Os sobreviventes repetem o juramento dos antigos monges diante do altar vazio, preservando uma fé que já não encontra templos."),
    Carta("gwent_v77_esq_batedor", "Sino do Peregrino", "Especial", "Os Esquecidos", 0, "Comum", 1, "gwent_v77_esq_batedor", "O sino de bronze convoca peregrinos dispersos de volta à capela; seu toque é reconhecido mesmo sob as pedras das catacumbas."),
    Carta("gwent_v77_esq_purificar", "Céu sem Cinzas", "Especial", "Os Esquecidos", 0, "Rara", 2, "gwent_v77_esq_purificar", "Quando o último hino ecoa pelos vitrais partidos, as nuvens se afastam e a cinza deixa de cobrir os santuários dos Esquecidos."),
    Carta("gwent_v77_esq_clima", "Bruma Sepulcral", "Especial", "Os Esquecidos", 0, "Épica", 3, "gwent_v77_esq_clima", "As criptas dos Esquecidos exalam uma névoa fria; dizem que ela preserva os sussurros dos que foram enterrados sem nome."),
]

_LUTERANO_CARTAS = []

_CARTAS_BASE = [*_CARTAS_BASE, *CARTAS_EXPANSAO_V75, *CARTAS_EXPANSAO_V76, *CARTAS_EXPANSAO_V77, *_LUTERANO_CARTAS]

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
    faccao = ("Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos")[n % 4]
    fileira = ("melee", "ranged", "siege")[(n // 23) % 3]
    raridade = "Épica" if marco == "platina" else "Rara"
    habilidade = HABILIDADES_COMUNS[(n // 7) % len(HABILIDADES_COMUNS)] if (raridade == "Épica" or n % 2 == 0) else ""
    minimo, maximo = FAIXA_PODER[raridade]
    poder = minimo + ((n // 11) % (maximo - minimo + 1))

    identidades = {
        "Ordem Áurea": ("Guardião do Crisol", "Sentinela da Luz", "Veterano Áureo"),
        "Véu Carmesim": ("Duelista Hemático", "Arauto Sanguíneo", "Caçador Rubro"),
        "Lua Negra": ("Astrólogo Lunar", "Teurgo de Nokron", "Vidente Astral"),
        "Os Esquecidos": ("Vigário Errante", "Monge do Santuário", "Devoto das Ruínas"),
    }
    nome_base = identidades[faccao][(n // 13) % len(identidades[faccao])]

    descricoes = {
        "Ordem Áurea": "Nas patrulhas que guardam as estradas de Leyndell, os juramentados mantêm viva a promessa feita diante da Árvore Áurea.",
        "Véu Carmesim": "Nos salões do Palácio de Mohgwyn, os servidores da dinastia aprendem os ritos de sangue e juram fidelidade à Mãe Sem Forma.",
        "Lua Negra": "Nas torres de Liurnia e nas ruínas de Nokron, estudiosos carianos observam as estrelas em busca de presságios ocultos.",
        "Os Esquecidos": "Entre capelas desabadas e catacumbas sem nome, os fiéis preservam as últimas palavras daqueles que a história abandonou.",
    }
    # Regras de combate, fileira e origem da recompensa permanecem fora da lore.
    descricao = descricoes[faccao]

    return Carta(
        id=f"jogo_{slug}_{marco}", nome=nome_base[:27], categoria="Unidade", faccao=faccao,
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
    faccao = ("Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos")[indice % 4]
    fileira = ("melee", "ranged", "siege")[(n // 29) % 3]
    habilidade = HABILIDADES_COMUNS[(n // 17) % len(HABILIDADES_COMUNS)] if (raridade in {"Épica", "Lendária"} or n % 2 == 0) else ""

    titulo = str(nome_patente).strip()
    lores_patente = {
        "Arauto da Ruína": "O arauto percorre as fronteiras devastadas e anuncia a queda dos antigos estandartes, reunindo os sobreviventes sob um novo juramento.",
        "Cavaleiro do Abismo": "Nas profundezas onde a luz da Árvore Áurea não alcança, o cavaleiro vigia a passagem entre as ruínas e as trevas antigas.",
        "Caçador de Almas": "O caçador segue os rastros deixados pelos espíritos inquietos e recolhe as almas que vagam sem descanso.",
        "Cinzas Novatas": "Recém-chegado às capelas abandonadas, o novato aprende com os guardiões a preservar a chama entre as cinzas.",
        "Executor Sombrio": "Sob o manto da noite, o executor cumpre as sentenças que os senhores das Terras Intermédias preferem manter ocultas.",
        "Guardião das Cinzas": "Diante dos altares cobertos de cinza, o guardião protege a última brasa da irmandade.",
        "Guerreiro Caído": "Mesmo após a derrota, o guerreiro permanece ligado ao juramento que o levou à batalha e se recusa a abandonar seus companheiros.",
        "Lenda do Coliseu": "Seu nome atravessa as arquibancadas e chega aos confins das Terras Intermédias; no Coliseu, cada vitória passa a integrar a memória dos combatentes.",
        "Senhor das Almas": "O senhor reúne espíritos errantes sob seu domínio e conhece os nomes que os vivos esqueceram.",
        "Sentinela Imortal": "A sentinela vigia os caminhos antigos sem ceder ao tempo, fiel ao posto mesmo após a queda de seu reino.",
    }
    lore = lores_patente.get(
        titulo,
        f"O título de {titulo} nasceu de seus feitos nas Terras Intermédias e carrega a memória dos que lutaram ao seu lado.",
    )

    return Carta(
        id=f"patente_{indice + 1}",
        nome=titulo[:27],
        categoria="Unidade",
        faccao=faccao,
        poder=int(poder),
        raridade=raridade,
        custo=CUSTO_RARIDADE[raridade],
        habilidade=habilidade,
        descricao=lore,
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
