"""Motor de pintura procedural para as ilustrações do Cartas do Coliseu.

Renderização original em camadas com Pillow puro (sem NumPy, sem assets externos):
- atmosfera e profundidade por planos, névoa, luz e partículas;
- cenas escolhidas por evidência semântica do nome, lore, categoria e facção;
- arquétipos distintos com silhueta, pose, equipamento e materiais próprios;
- acabamento pictórico com textura, luz de recorte e microdetalhes.

O resultado é determinístico: a mesma carta e paleta sempre produzem a mesma arte.
"""
from __future__ import annotations

import hashlib
import math
import random
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

BASE_W, BASE_H = 384, 430


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _mul(c: tuple[int, int, int], f: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _alpha(c: tuple[int, int, int], a: int) -> tuple[int, int, int, int]:
    return c[0], c[1], c[2], max(0, min(255, int(a)))


def _seed(card: dict[str, Any]) -> int:
    raw = "|".join(str(card.get(k, "")) for k in (
        "id", "nome", "descricao", "lore", "habilidade", "faccao", "categoria"
    ))
    return int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")


def _contains(text: str, *terms: str) -> bool:
    return any(_norm(term) in text for term in terms)


def _has_word(text: str, *terms: str) -> bool:
    """Correspondência por palavra inteira para não confundir 'espadachim' com 'espada'."""
    return any(re.search(rf"\b{re.escape(_norm(term))}\b", text) is not None for term in terms)


@dataclass(frozen=True)
class ArtDirection:
    subject: str
    scene: str
    faction: str
    action: str
    material: str
    canonical: str = ""
    equipment: str = ""


def analisar_direcao(card: dict[str, Any]) -> ArtDirection:
    """Classifica a carta por evidência textual; nunca inventa equipamento obrigatório."""
    title = _norm(card.get("nome"))
    lore = _norm(card.get("descricao") or card.get("lore"))
    ability = _norm(card.get("habilidade"))
    ident = _norm(" ".join((title, lore)))
    card_id = _norm(card.get("id"))
    faction = _norm(card.get("faccao"))
    category = _norm(card.get("categoria"))

    canonical = ""
    # Um nome próprio só vira personagem central quando abre o título. Assim,
    # 'Rugido de Godfrey' permanece um efeito e 'Cavaleiros de Radahn' permanece grupo.
    if title.startswith("ranni "):
        canonical = "ranni"
    elif title.startswith("fia ") and _contains(title, "leito de morte", "deathbed"):
        canonical = "fia"
    elif title.startswith("marika "):
        canonical = "marika"
    elif title.startswith("godwyn "):
        canonical = "godwyn"
    elif title.startswith(("mae sem forma", "formless mother")):
        canonical = "formless mother"
    elif title.startswith(("besta pristina", "elden beast")):
        canonical = "elden beast"
    elif title.startswith("malenia "):
        canonical = "malenia"
    elif title.startswith("radahn "):
        canonical = "radahn"
    elif title.startswith("godfrey "):
        canonical = "godfrey"
    elif title.startswith("maliketh "):
        canonical = "maliketh"
    elif title.startswith("messmer "):
        canonical = "messmer"
    elif title.startswith("blaidd "):
        canonical = "blaidd"
    elif title.startswith("gurranq "):
        canonical = "gurranq"
    elif title.startswith(("assassina da faca negra", "black knife assassin")):
        canonical = "black knife assassin"
    elif title.startswith("placidusax "):
        canonical = "placidusax"

    # O objeto focal precisa ser realmente um objeto. Portadores de estandarte,
    # arautos e personagens com títulos que mencionam armas continuam sendo figuras.
    is_standard_bearer = _contains(title, "porta estandarte", "arauto do estandarte", "portaestandarte")
    item_terms = ("espada", "lanca", "machado", "martelo", "arco", "cajado", "adaga",
                  "foice", "runa", "anel", "coroa", "livro", "tomo", "algemas",
                  "correntes", "tear", "escudo")
    is_relic = (card_id.startswith("reliquia ") or (not canonical and not is_standard_bearer and (
        _contains(title, "grande runa", "lamina negra", "lamina da morte", "lamina da morte destinada",
                  "espada da noite", "lagrima sagrada", "runa da morte", "coroa do lorde",
                  "adaga da faca negra", "reliquia")
        or _has_word(title, *item_terms, "estandarte")
    )))
    if card_id == "chefe aparicao veio" or _contains(title, "lamina negra errante"):
        canonical = "black blade wanderer"
        is_relic = False

    if is_relic:
        subject, action, material = "named relic or weapon", "the named relic displayed as the unmistakable focal subject", "forged metal, engraved stone, leather wrapping and restrained magical inlay"
    elif category == "especial" and _contains(title, "silencio dourado", "ceu sem cinzas"):
        subject, action, material = "weather-cleansing blessing", "a broad sacred current opens the cloud cover and disperses battlefield weather, revealing clear light through the broken sky", "soft gold-white rays, thinning storm layers, wind-torn ash and translucent sacred particles"
    elif category == "especial" and _contains(title, "luz na geada"):
        subject, action, material = "frost-cleansing flame", "a small but intense pale flame travels across frozen stone, melting the ice around exhausted allies without consuming them", "ivory-gold flame, blue crystal frost, thawing droplets and warm light against cold vapor"
    elif category == "especial" and _contains(title, "bruma sepulcral"):
        subject, action, material = "sepulchral mist", "a low grave-cold fog pours from open crypts and blankets one battlefield line, partially obscuring distant silhouettes", "layered grey-blue fog, damp tombstone, pale particles and deep charcoal stone"
    elif category == "especial" and _contains(title, "tempestade"):
        subject, action, material = "storm event", "a violent storm front sweeps across the battlefield, with directional rain, pressure-heavy clouds and a visible lightning strike only when named", "layered storm clouds, rain-slick stone, cold atmospheric haze and forked white-blue lightning"
    elif category == "especial" and _contains(title, "geada", "gelo"):
        subject, action, material = "frost phenomenon", "a freezing wave advances over the battlefield, crystallizing the ground and air", "translucent ice, frost crystals, blue-white haze and brittle frozen surfaces"
    elif category == "especial" and _contains(title, "rito hematico"):
        subject, action, material = "blood rite", "an officiant performs a precise blood rite before a marked enemy line, with the ritual altar and flowing blood as clear focal elements", "deep crimson liquid, dark sacrificial stone, black iron, ritual linen and suspended red droplets"
    elif category == "especial" and _contains(title, "nevoa rubra"):
        subject, action, material = "scarlet rot mist", "a dense scarlet corruption cloud crawls through an enemy formation, leaving rotting petals and red spores suspended in the air", "crimson rot vapor, decayed rose petals, wet organic residue, dark stone and red particulate"
    elif category == "especial" and _contains(title, "miasma", "sangue corrompido", "ritual de sangue"):
        subject, action, material = "corruption event", "a spreading corruptive vapor or blood rite stains the battlefield at ground level", "dense red-black vapor, wet organic residue, dark liquid and low drifting particles"
    elif category == "especial" and _contains(title, "rugido"):
        subject, action, material = "sonic shockwave", "a powerful roar sends pressure rings across the ranks, visibly bending dust and loose cloth", "compressed air, concentric distortions, dust, torn banners and muted golden light"
    elif category == "especial" and _contains(title, "sino do peregrino"):
        subject, action, material = "pilgrim bell", "a monumental weathered bell swings above ruined cloisters, its visible soundwaves calling a lone messenger toward the viewer", "aged bronze, cracked clapper, dark timber, vibrating dust and concentric pale-gold sound ripples"
    elif category == "especial" and _contains(title, "cantico dourado", "cantico dos fieis"):
        subject, action, material = "sacred choir", "a small choir of distinct faithful figures sings in formation as a visible harmonic current strengthens the line", "layered vestments, aged gold thread, candle smoke, stone arches and restrained luminous sound rings"
    elif category == "especial" and _contains(title, "delirio carmesim"):
        subject, action, material = "frenzied blood ritual", "a crimson rite breaks the discipline of enemy soldiers as distorted silhouettes and fractured rhythm overtake the ranks", "dark red cloth, broken ritual circles, irregular crimson light and ink-black smoke"
    elif category == "especial" and _contains(title, "sentenca carmesim"):
        subject, action, material = "execution", "a masked executioner delivers a controlled sentence to one visibly vulnerable armored target, framed as a ritual judgment", "blackened execution steel, dark crimson cloth, worn iron, restrained blood-red light"
    elif category == "especial" and _contains(title, "misericordia final"):
        subject, action, material = "last mercy and recovery", "a fallen forgotten soldier is lifted from a crypt threshold by a veiled sister, with the return to safety as the focal action", "weathered linen, pale candlelight, worn reliquary silver, ash and soft resurrection haze"
    elif category == "especial" and _contains(title, "procissao dos fieis"):
        subject, action, material = "faithful procession", "a visible line of pilgrims advances through broken cloisters carrying a relic toward the chosen battlefield line", "heavy ceremonial cloth, worn sandals, aged wood, stone dust and narrow shafts of light"
    elif category == "especial" and _contains(title, "bencao", "egide", "vigilia do relicario"):
        subject, action, material = "protective blessing", "a chosen ally or sacred relic is enclosed by a precise protective aureole, with visible shield facets rather than a generic caster", "pale gold filaments, translucent shield facets, worn silver reliquary and fine sacred particles"
    elif category == "especial" and _contains(title, "lei da regressao", "purificar"):
        subject, action, material = "purification phenomenon", "a veil of false appearances is peeled away by a controlled field of pale light", "soft gold-white light, dissolving mist, fine geometric tracery and transparent layers"
    elif category == "especial" and _has_word(title, "chama", "fogo"):
        subject = "flame event"
        if _contains(title, "chama negra"):
            action = "black divine fire advances in dark violet tongues, consuming light and leaving a cold luminous core"
            material = "near-black violet flame, lilac-white cores, soot-dark smoke and sparse spectral embers"
        elif _contains(title, "chama frenetica"):
            action = "chaotic frenzy-fire lashes in irregular branching tongues, distorting the air and overwhelming the scene"
            material = "violent golden-orange flame, yellow-white hot cores, unstable tendrils and incandescent ash"
        elif _contains(title, "gigante"):
            action = "a colossal giant's fire burns against glacial wind, its broad heat plume visible against frozen terrain"
            material = "massive orange-white fire tongues, ember cores, black smoke and frost vapor at the edges"
        else:
            action = "a destructive mass of fire consumes the battlefield with distinct tongues of flame and rolling smoke"
            material = "layered ember, white-hot cores, orange fire, soot and volumetric smoke"
    elif category == "especial" and _contains(title, "juramento"):
        subject, action, material = "ancestral vow", "an ancient vow is embodied through solemn figures, a ritual gesture and the physical weight of the oath", "aged bronze, root-like forms, dark ceremonial cloth and restrained crimson light"
    elif category == "especial" and _contains(title, "passo"):
        subject, action, material = "spectral dash", "a spectral hound-like afterimage crosses the scene at ground level in one unmistakable direction", "dark motion silhouette, silver-blue afterimages and narrow directional light trails"
    elif category == "especial" and _contains(title, "bastiao", "muralha"):
        subject, action, material = "fortification event", "a monumental defensive wall dominates the scene, with tiny defenders establishing its scale", "aged limestone, gold-veined masonry, deep arch shadows and worn battlements"
    elif category == "especial" and _contains(title, "chamado dos mortos", "cinzas dos lobos", "invocacao"):
        subject, action, material = ("wolf summoning" if _contains(title, "lobos") else "resurrection or summoning"), "spectral allies rise from ash and ground mist, clearly readable as summoned figures", "pale spectral fur or translucent spirit forms, ash, cold mist and soft blue-white light"
    elif category == "especial" and _contains(title, "lua cheia"):
        subject, action, material = "full moon phenomenon", "a vast full moon dominates the night sky above a recognizably Carian battlefield", "cold lunar light, cratered moon surface, silver haze and dark stone silhouettes"
    elif category == "especial" and _contains(title, "flor da podridao escarlate"):
        subject, action, material = "scarlet bloom", "a gigantic scarlet flower opens from corrupted ground as the unmistakable focal subject", "layered crimson petals, dark organic stem, wet stone and drifting red spores"
    elif _contains(title, "gemeas", "irmas gemeas"):
        subject, action, material = "paired characters", "two distinct sisters share the composition, with separate silhouettes, gestures and coordinated but non-identical clothing", "layered travel cloth, worn leather, moonlit metal details and individual fabric textures"
    elif _contains(title, "servo dos mortos", "servo dos que vivem na morte", "necromante", "necromancia"):
        subject, action, material = "necromancer", "a hooded death-servant raises spectral dead from the ground, with the summoner and the spirits both clearly legible", "aged dark cloth, bone, cold spectral vapor, tarnished iron and ashen particulate"
    elif (title.startswith(("cavaleiros ", "guardioes ", "guardas ", "discipulos ", "peregrinos ",
                            "servos ", "sentinelas ", "combatentes ", "veteranos ", "apostolos ",
                            "devotos ", "filhos ", "irmaos ", "juramentados "))):
        subject, action, material = "battle group", "a coordinated formation of distinct individuals with readable spacing, varied silhouettes and a shared faction identity", "individual armor and cloth layers, differentiated steel, leather, weathering and faction insignia"
    elif canonical == "formless mother":
        subject, action, material = "primordial entity", "an immense formless presence emerging from a blood-red eclipse, with no human body or generic caster", "translucent crimson membranes, dark organic tendrils, suspended blood-like droplets and void"
    elif canonical:
        subject = f"canonical {canonical}"
        action = "a source-faithful depiction of the named character in a defining posture"
        material = "character-specific armor, hair, cloth, hide and signature equipment"
    elif _contains(title, "vontade de marika", "will of marika"):
        subject, action, material = "divine manifestation", "an impersonal golden will taking shape as a luminous, human-scale silhouette rather than a portrait of Marika", "translucent gold, pale stone dust, fine light filaments and sacred metal"
    elif _contains(title, "juramento primordial do crisol"):
        subject, action, material = "oathbound champion", "a solitary champion bound to an ancient crucible oath, marked by root-like sigils and restrained crimson light", "aged plate, oxidized bronze, dark red cloth and petrified root filaments"
    elif _contains(ident, "montado", "cavaleiro montado", "montaria", "montado em", "sobre seu cavalo", "a cavalo") or (
        _contains(ident, "radahn") and _contains(ident, "cavalo", "leonard", "montaria")
    ):
        subject, action, material = "mounted rider", "a rider and mount moving together through the scene", "worn plate, leather tack, horsehair and weathered cloth"
    elif _contains(title, "dragoeiro") and _contains(lore, "guerreiro", "canaliza", "dragões antigos", "dragoes antigos", "relampagos", "raios"):
        # No catálogo, Dragoeiro Ancião é um guerreiro humano ligado aos dragões,
        # não um dragão quadrúpede. O título e a lore têm prioridade sobre o radical.
        subject, action, material = "ancient dragon warrior", "an armored warrior channels ancestral lightning through both hands during battle; keep the human fighter as the unmistakable subject", "dark forged plate, dragon-scale relief, weathered leather, oxidized bronze and cold-white lightning"
    elif _contains(title, "gigante") or _contains(lore, "presenca colossal", "gigante de fogo"):
        subject, action, material = "giant", "a towering fire giant with exaggerated scale, heavy anatomy and a clear silhouette against the terrain", "charred hide, massive muscle, cracked basalt, scorched cloth and molten fissures"
    elif _contains(title, "anjo", "serafim", "angel", "seraph"):
        subject, action, material = "winged celestial", "a winged messenger with layered feather structure, a readable human figure and a deliberate descent or protective gesture", "weathered ivory feathers, pale cloth, tarnished gold and soft atmospheric light"
    elif is_standard_bearer:
        subject, action, material = "standard bearer", "a single herald carrying a large faction banner in a wind-readable pose", "embroidered heavy cloth, worn pole wood, metal fittings and ceremonial armor"
    elif _contains(title, "ferreiro", "mestre ferreiro", "mercador", "mercante", "contrabandista"):
        subject, action, material = "artisan or merchant", "a working craftsperson or traveling trader surrounded by role-specific tools or wares, not a generic soldier", "worn work leather, coarse linen, soot, hammered iron, wood and practical travel gear"
    elif _contains(title, "bibliotecaria", "bibliotecario", "cartografo", "cartografa", "leitora de estrelas", "exploradora", "erudito"):
        subject, action, material = "scholar or explorer", "a learned observer studying a map, book, instrument or the environment named by the lore", "parchment, ink, worn leather, layered robes, brass instruments and fine stitching"
    elif _contains(title, "papa", "bispo", "sacerdote", "sacerdotisa", "missionario", "peregrino", "diacono", "diaconisa", "pastor", "confessora", "confessor", "apostolo", "monge", "clerigo", "profeta", "irmao", "irmã", "irma", "acolito", "acólito", "devota", "abadessa", "martir", "mártir", "prelado", "santo", "cantor"):
        subject, action, material = "cleric or preacher", "a solemn religious figure performing a blessing, proclamation or rite grounded in the lore", "heavy vestments, woven trim, aged metal, relics and candlelit fabric"
    elif _contains(title, "cavaleiro", "cavaleira", "soldado", "guardiao", "guardia", "sentinela",
                   "escudeiro", "lanceiro", "carrasco", "cruzado", "veterano", "guerreiro", "combatente"):
        subject, action, material = "armored knight", "a disciplined martial figure with weight-bearing armor, grounded stance and role-appropriate equipment", "layered plate, chainmail, leather straps, worn cloth, scuffed steel and forged fittings"
    elif _contains(ident, "dragao", "dragoes", "wyrm", "drake", "lobo", "lobos", "cervo", "fera", "besta", "serpente", "aranha", "corvo", "grifo", "cavalo", "corcel", "behemoth", "wolf", "dragon", "beast"):
        subject, action, material = "creature", "the creature performing a readable action grounded in its title and lore", "fur, scale, horn, hide, claw and natural surface texture"
    elif _contains(ident, "oraculo", "mago", "feiticeir", "arcanista", "bruxa", "sacerdot", "sacerdotisa", "clerigo", "monge", "ritualista", "tecela", "invocador", "apostolo", "erudito", "astrol", "confessora", "mistico", "místico"):
        subject, action, material = "arcane or ritual figure", "a deliberate gesture or ritual action, with hands and focal effect clearly readable", "layered cloth, aged metal, parchment and controlled luminous effects"
    elif _contains(ident, "assassino", "assassina", "ladrao", "ladra", "ladina", "duelista", "espadachim", "batedor", "cacador", "rastreador", "arqueiro", "arqueira", "recusante"):
        subject, action, material = "agile scout or duelist", "a compact, precise stance that communicates vigilance, pursuit or a controlled strike", "fitted leather, practical cloth, darkened steel and fine stitching"
    elif _contains(ident, "rei", "rainha", "dama", "lorde", "senhor", "soberano", "principe", "princesa", "general", "comandante"):
        subject, action, material = "noble or commander", "a commanding, composed presence with authority expressed through bearing", "ceremonial plate, fine cloth, aged gold and restrained ornament"
    else:
        subject, action, material = "lore-specific humanoid", "the exact action or role stated by the card, without adding unsupported equipment", "weathered armor, layered cloth, leather and hand-worked metal"

    # Equipamento é extraído separadamente da ação. A pose pode mudar sem
    # apagar o fato de que a carta nomeia uma lança, arco, cajado, livro ou martelo.
    equipment_text = _norm(" ".join((title, lore)))
    if _contains(title, "lanceiro") or _has_word(equipment_text, "lanca", "lança", "spear"):
        equipment = "spear"
    elif _has_word(equipment_text, "arco", "bow", "arqueiro", "arqueira"):
        equipment = "bow"
    elif _has_word(equipment_text, "martelo", "hammer", "ferreiro"):
        equipment = "hammer"
    elif _has_word(equipment_text, "cajado", "staff", "bastao"):
        equipment = "staff"
    elif _contains(title, "espadachim", "duelista", "assassina", "assassino") or _has_word(equipment_text, "espada", "lamina", "lâmina", "adaga", "foice", "sword", "blade", "dagger"):
        equipment = "blade"
    elif _contains(title, "porta estandarte", "arauto do estandarte", "portaestandarte"):
        equipment = "banner"
    elif _contains(title, "bibliotecaria", "bibliotecario", "cartografo", "cartografa", "leitora", "livro"):
        equipment = "book or map"
    else:
        equipment = ""

    if _contains(title, "lagrima sagrada"):
        scene = "sacred reliquary chamber"
    elif _contains(ident, "morte destinada", "lamina negra", "runa da morte", "maliketh"):
        scene = "death sanctum"
    elif _contains(title, "chama negra"):
        scene = "black flame sanctuary"
    elif _contains(title, "chama frenetica", "chama frenética"):
        scene = "frenzied flame cathedral"
    elif _contains(title, "juramento do crisol", "juramento primordial do crisol"):
        scene = "ancient crucible sanctuary"
    elif _contains(title, "lei da regressao", "lei da regressão"):
        scene = "sacred golden citadel"
    elif _contains(title, "flor da podridao escarlate", "flor da podridão escarlate"):
        scene = "haligtree bloom"
    elif _contains(ident, "ritual de sangue", "sangue corrompido", "dinastia sanguinea", "hemorragia", "moghwyn"):
        scene = "blood-red dynasty palace"
    elif _contains(title, "chama do gigante", "gigante de fogo"):
        scene = "frozen highlands"
    elif canonical in {"black knife assassin", "black blade wanderer", "blaidd", "ranni"}:
        scene = "moonlit ruins"
    elif _contains(title, "anjo", "serafim", "angel", "papa esquecido") or _contains(lore, "mensageiro divino") or (_contains(title, "esquecido") and subject in {"cleric or preacher", "arcane or ritual figure"}) or ("esquecidos" in faction and subject in {"cleric or preacher", "arcane or ritual figure"}):
        scene = "forgotten cathedral"
    elif _contains(title, "dragoeiro") or _contains(ident, "dragões ancestrais", "dragoes ancestrais", "raios ancestrais"):
        scene = "storm-riven sky temple"
    elif "radahn" in title or _contains(ident, "caelid", "flagelo das estrelas", "starscourge"):
        scene = "scarlet wasteland"
    elif "malenia" in title or _contains(ident, "haligtree", "podrida escarlate", "scarlet rot"):
        scene = "haligtree bloom"
    elif "messmer" in title or _contains(ident, "reino das sombras", "shadow keep", "chama impura"):
        scene = "shadow keep"
    elif any(name in title for name in ("maliketh", "gurranq", "placidusax")) or _contains(ident, "farum azula", "bestial sanctum"):
        scene = "storm-riven sky temple"
    elif _contains(ident, "gigante de fogo", "fire giant"):
        scene = "frozen highlands"
    elif _contains(ident, "raya lucaria", "raya", "academia", "observatorio", "bibliotecaria", "bibliotecario", "sellia"):
        scene = "academy observatory"
    elif _contains(ident, "mercador nomade", "caravana", "viajante", "estrada entre assentamentos"):
        scene = "crossroads caravan"
    elif _contains(ident, "ferreiro", "volcano manor", "fornalha", "forja"):
        scene = "crimson forge and volcanic stone"
    elif _contains(ident, "arvore aurea", "erdtree", "leyndell", "catedral", "capital", "portao dourado") or "ordem aurea" in faction:
        scene = "sacred golden citadel"
    elif _contains(ident, "geada", "gelo", "neve", "montanha", "pico", "picos", "geleira"):
        scene = "frozen highlands"
    elif _contains(ident, "lua", "noite", "cariano", "sellia", "estrela", "astral", "lunar", "eclipse") or "lua negra" in faction:
        scene = "moonlit ruins"
    elif _contains(ident, "floresta", "arvore", "bosque", "raiz", "folha", "mata", "wood", "forest"):
        scene = "ancient forest"
    elif _contains(ident, "moghwyn", "mae sem forma", "dinastia sanguinea", "sangue corrompido"):
        scene = "blood-red dynasty palace"
    elif _contains(ident, "vulcao", "forja", "brasa", "lava", "gelmir", "fornalha"):
        scene = "crimson forge and volcanic stone"
    elif "veu carmesim" in faction:
        scene = "crimson forge and volcanic stone"
    elif _contains(ident, "necropole", "cemiterio", "cripta", "tumulo", "afogado", "pantano", "lodo", "necropolis", "swamp") or "esquecidos" in faction:
        scene = "forgotten necropolis or drowned marsh"
    elif _contains(ident, "muralha", "bastiao", "portao", "ordem"):
        scene = "sacred golden citadel"
    elif _contains(ident, "costa", "mar", "oceano", "ilha", "navio", "porto", "naufragio"):
        scene = "storm-worn coast"
    elif _contains(ident, "ruina", "ruinas", "templo", "altar", "santuario", "ponte"):
        scene = "weathered ancient ruins"
    else:
        scene = {
            "ordem aurea": "sacred golden citadel",
            "veu carmesim": "crimson forge and volcanic stone",
            "lua negra": "moonlit ruins",
            "os esquecidos": "forgotten necropolis or drowned marsh",
        }.get(faction, "weathered ancient ruins")

    action_ident = _norm(" ".join((title, lore, ability)))
    if _contains(action_ident, "proteger", "protege", "guardiao", "guardia", "sentinela", "defende", "vigia", "patrulha"):
        action = "holding a watchful defensive position, protecting the passage or subject named in the lore"
    elif _contains(action_ident, "duelo", "duelista", "confronto", "combate", "golpe", "ataque", "strike"):
        action = "a precise combat exchange captured at the instant of contact or imminent impact"
    elif _contains(action_ident, "juramento", "promessa", "pacto", "voto", "alianca"):
        action = "a solemn vow or pact made physically legible through gesture and a specific ritual object"
    elif _contains(action_ident, "observa", "vigia", "espreita", "rastreia", "procura", "caça", "caca"):
        action = "studying the terrain with a clear sightline and a deliberate, alert posture"

    if "lua negra" in faction:
        faction_key = "moon-silver"
    elif "veu carmesim" in faction:
        faction_key = "crimson-iron"
    elif "esquecidos" in faction:
        faction_key = "weathered-ivory"
    else:
        faction_key = "golden-ivory"
    return ArtDirection(subject, scene, faction_key, action, material, canonical, equipment)


class _Painter:
    """Canvas de alta resolução com coordenadas normalizadas 384×430."""
    def __init__(self, width: int, height: int, seed: int):
        self.scale = max(1.0, min(width / BASE_W, height / BASE_H) * 2.35)
        self.w = max(1, int(round(width * self.scale)))
        self.h = max(1, int(round(height * self.scale)))
        self.sx = self.w / BASE_W
        self.sy = self.h / BASE_H
        self.rng = random.Random(seed)
        self.image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        self.rng = random.Random(seed ^ 0x4252555348535452)

    def _brush_texture(self, size: tuple[int, int], mask: Image.Image, base):
        """Marcas de pigmento orientadas e recortadas pela silhueta, sem matrizes externas."""
        width, height = size
        texture = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(texture, "RGBA")
        area = width * height
        # Mais pinceladas em superfícies grandes, mas com limite para cartas em lote.
        count = max(16, min(360, int(math.sqrt(max(1, area)) * .52)))
        light = _mix(base, (255, 244, 217), .48)
        shade = _mix(base, (7, 9, 14), .48)
        vertical = height > width * 1.18
        horizontal = width > height * 1.18
        for _ in range(count):
            x = self.rng.randint(0, max(0, width-1))
            y = self.rng.randint(0, max(0, height-1))
            if vertical:
                dx = self.rng.randint(-5, 5)
                dy = self.rng.randint(5, max(7, min(58, int(height*.24))))
            elif horizontal:
                dx = self.rng.randint(5, max(7, min(58, int(width*.24))))
                dy = self.rng.randint(-5, 5)
            else:
                length = self.rng.randint(5, max(7, min(46, int(max(width,height)*.19))))
                angle = self.rng.choice((-.85, -.55, -.25, .25, .55, .85))
                dx = int(math.cos(angle) * length)
                dy = int(math.sin(angle) * length)
            color = light if self.rng.random() > .44 else shade
            alpha = self.rng.randint(24, 82)
            stroke_w = self.rng.choice((1, 2, 2, 3, 3, 4))
            ex = max(0, min(width-1, x+dx))
            ey = max(0, min(height-1, y+dy))
            draw.line((x, y, ex, ey), fill=(*color, alpha), width=stroke_w, joint="curve")
            if self.rng.random() < .20:
                r = self.rng.choice((1, 1, 2, 3))
                draw.ellipse((x-r, y-r, x+r, y+r), fill=(*color, alpha//2))
        # Pigmento fino e irregular: a textura acompanha a máscara da forma.
        for _ in range(max(4, count//2)):
            x = self.rng.randint(0, max(0, width-1))
            y = self.rng.randint(0, max(0, height-1))
            radius = self.rng.choice((0, 1, 1, 2))
            color = self.rng.choice((light, shade))
            draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                         fill=(*color, self.rng.randint(12, 38)))
        if min(width, height) >= 12:
            texture = texture.filter(ImageFilter.GaussianBlur(max(.25, self.sx*.18)))
        texture.putalpha(ImageChops.multiply(texture.getchannel("A"), mask))
        return texture

    def p(self, xy: tuple[float, float]) -> tuple[int, int]:
        return int(xy[0] * self.sx), int(xy[1] * self.sy)

    def box(self, box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
        return (int(box[0] * self.sx), int(box[1] * self.sy),
                int(box[2] * self.sx), int(box[3] * self.sy))

    def width(self, value: float) -> int:
        return max(1, int(round(value * (self.sx + self.sy) / 2)))

    def paint_polygon(self, points: Iterable[tuple[float, float]], base,
                      *, highlight=None, shadow=None, outline=None, width: float = 1,
                      opacity: int = 255):
        """Pinta uma forma com volume, pigmento recortado e transparência preservada."""
        if len(base) > 3:
            opacity = min(opacity, int(base[3]))
            base = base[:3]
        pts = [self.p(point) for point in points]
        if len(pts) < 3:
            return
        left = max(0, min(point[0] for point in pts))
        top = max(0, min(point[1] for point in pts))
        right = min(self.w - 1, max(point[0] for point in pts))
        bottom = min(self.h - 1, max(point[1] for point in pts))
        if right <= left or bottom <= top:
            return
        local = [(x-left, y-top) for x, y in pts]
        mask = Image.new("L", (right-left+1, bottom-top+1), 0)
        ImageDraw.Draw(mask).polygon(local, fill=255)
        highlight = highlight or _mix(base, (255, 247, 224), .20)
        shadow = shadow or _mul(base, .48)
        # Campo cromático baixo-res ampliado com bicúbica: mantém luz direcional
        # contínua e evita bandas/quadriculado típico de gradiente vetorial.
        gradient_size = (40, 40)
        gradient = Image.new("RGBA", gradient_size, (0, 0, 0, 0))
        gp = gradient.load()
        for gy in range(gradient_size[1]):
            ty = gy / (gradient_size[1]-1)
            for gx in range(gradient_size[0]):
                tx = gx / (gradient_size[0]-1)
                t = max(0.0, min(1.0, .67 * ty + .33 * tx))
                gp[gx, gy] = (*_mix(highlight, shadow, t ** .88), 255)
        layer = gradient.resize(mask.size, Image.Resampling.BICUBIC)
        if opacity < 255:
            mask = mask.point(lambda value: value * max(0, opacity) // 255)
        layer.putalpha(mask)
        texture = self._brush_texture(layer.size, mask, base)
        layer.alpha_composite(texture)
        crop = self.image.crop((left, top, right+1, bottom+1))
        crop.alpha_composite(layer)
        self.image.paste(crop, (left, top))
        self.draw = ImageDraw.Draw(self.image, "RGBA")
        if outline:
            self.draw.line(pts + [pts[0]], fill=outline, width=self.width(width), joint="curve")

    def polygon(self, points: Iterable[tuple[float, float]], fill, outline=None, width: float = 1):
        points = list(points)
        if fill is None or (len(fill) > 3 and int(fill[3]) <= 0):
            pts = [self.p(pt) for pt in points]
            if fill is not None:
                self.draw.polygon(pts, fill=fill)
            if outline:
                self.draw.line(pts + [pts[0]], fill=outline, width=self.width(width), joint="curve")
            return
        self.paint_polygon(points, fill, outline=outline, width=width)

    @staticmethod
    def _spline_points(points: Iterable[tuple[float, float]], *, closed: bool = False, steps: int = 7):
        """Amostra curvas Catmull–Rom para contornos orgânicos sem raster externo."""
        pts = [(float(x), float(y)) for x, y in points]
        if len(pts) < 3:
            return pts
        result = []
        count = len(pts)
        segments = count if closed else count - 1
        for i in range(segments):
            p1 = pts[i]
            p2 = pts[(i + 1) % count]
            p0 = pts[(i - 1) % count] if closed or i > 0 else p1
            p3 = pts[(i + 2) % count] if closed or i + 2 < count else p2
            for j in range(steps):
                t = j / steps; t2 = t*t; t3 = t2*t
                x = .5*((2*p1[0])+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
                y = .5*((2*p1[1])+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
                result.append((x,y))
        result.append(pts[0] if closed else pts[-1])
        return result

    def smooth_polygon(self, points, fill, outline=None, width: float = 1, *, steps: int = 7):
        sampled = self._spline_points(points, closed=True, steps=steps)
        self.polygon(sampled, fill, outline, width)

    def smooth_line(self, points, fill, width: float = 1, *, steps: int = 8):
        sampled = self._spline_points(points, closed=False, steps=steps)
        self.line(sampled, fill, width, joint="curve")

    def line(self, points: Iterable[tuple[float, float]], fill, width: float = 1, joint: str = "curve"):
        self.draw.line([self.p(pt) for pt in points], fill=fill, width=self.width(width), joint=joint)

    def paint_ellipse(self, box, base, *, highlight=None, shadow=None, outline=None,
                      width: float = 1, opacity: int = 255):
        if len(base) > 3:
            opacity = min(opacity, int(base[3]))
            base = base[:3]
        left, top, right, bottom = self.box(box)
        left, top = max(0,left), max(0,top)
        right, bottom = min(self.w-1,right), min(self.h-1,bottom)
        if right <= left or bottom <= top:
            return
        mask = Image.new("L",(right-left+1,bottom-top+1),0)
        ImageDraw.Draw(mask).ellipse((0,0,right-left,bottom-top),fill=255)
        highlight = highlight or _mix(base,(255,247,226),.20)
        shadow = shadow or _mul(base,.46)
        gradient_size=(36,36)
        gradient=Image.new("RGBA",gradient_size,(0,0,0,0)); gp=gradient.load()
        for gy in range(gradient_size[1]):
            ty=gy/(gradient_size[1]-1)
            for gx in range(gradient_size[0]):
                tx=gx/(gradient_size[0]-1)
                gp[gx,gy]=(*_mix(highlight,shadow,(.66*ty+.34*tx)**.9),255)
        layer=gradient.resize(mask.size,Image.Resampling.BICUBIC)
        if opacity < 255:
            mask = mask.point(lambda value: value * max(0, opacity) // 255)
        layer.putalpha(mask)
        texture=self._brush_texture(layer.size,mask,base)
        layer.alpha_composite(texture)
        crop=self.image.crop((left,top,right+1,bottom+1)); crop.alpha_composite(layer)
        self.image.paste(crop,(left,top)); self.draw=ImageDraw.Draw(self.image,"RGBA")
        if outline:
            self.draw.ellipse((left,top,right,bottom),outline=outline,width=self.width(width))

    def ellipse(self, box, fill=None, outline=None, width: float = 1):
        if fill is None or (len(fill) > 3 and int(fill[3]) <= 0):
            self.draw.ellipse(self.box(box), fill=fill, outline=outline, width=self.width(width))
            return
        self.paint_ellipse(box, fill, outline=outline, width=width)

    def rect(self, box, fill=None, outline=None, width: float = 1):
        if fill is None or (len(fill) > 3 and int(fill[3]) <= 0):
            self.draw.rectangle(self.box(box), fill=fill, outline=outline, width=self.width(width))
            return
        x1,y1,x2,y2=box
        self.paint_polygon(((x1,y1),(x2,y1),(x2,y2),(x1,y2)),fill,outline=outline,width=width)

    def arc(self, box, start: float, end: float, fill, width: float = 1):
        self.draw.arc(self.box(box), start, end, fill=fill, width=self.width(width))


def _glow(canvas: _Painter, center: tuple[float, float], radius: float,
          color: tuple[int, int, int], strength: int = 90, vertical: float = 1.0):
    layer = Image.new("RGBA", canvas.image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    cx, cy = canvas.p(center)
    rx, ry = canvas.width(radius), canvas.width(radius * vertical)
    for i in range(8, 0, -1):
        f = i / 8
        rr_x, rr_y = int(rx * f), int(ry * f)
        alpha = int(strength * (1 - f) ** 1.6)
        d.ellipse((cx - rr_x, cy - rr_y, cx + rr_x, cy + rr_y), fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(canvas.width(radius * .42)))
    canvas.image = Image.alpha_composite(canvas.image, layer)
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")


def _gradient(width: int, height: int, top, bottom) -> Image.Image:
    image = Image.new("RGBA", (width, height), (*top, 255))
    d = ImageDraw.Draw(image)
    for y in range(height):
        t = y / max(1, height - 1)
        t = t * t * (3 - 2 * t)
        c = _mix(top, bottom, t)
        d.line((0, y, width, y), fill=(*c, 255))
    return image


def _draw_sky(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    top, mid, accent, metal = palette
    scene = direction.scene
    scene_top = _mix(top, (7, 10, 18), .30)
    scene_bottom = _mix(mid, (12, 16, 22), .50)
    if scene == "moonlit ruins":
        scene_top = _mix(scene_top, (12, 17, 46), .42)
    elif scene == "crimson forge and volcanic stone":
        scene_top = _mix(scene_top, (43, 10, 17), .32)
        scene_bottom = _mix(scene_bottom, (62, 22, 17), .20)
    elif scene == "frozen highlands":
        scene_top = _mix(scene_top, (35, 54, 72), .42)
    elif scene == "scarlet wasteland":
        scene_top = _mix(scene_top, (68, 24, 31), .55)
        scene_bottom = _mix(scene_bottom, (60, 26, 25), .35)
    elif scene == "haligtree bloom":
        scene_top = _mix(scene_top, (28, 47, 48), .46)
        scene_bottom = _mix(scene_bottom, (44, 62, 51), .30)
    elif scene == "shadow keep":
        scene_top = _mix(scene_top, (31, 13, 19), .55)
        scene_bottom = _mix(scene_bottom, (35, 18, 22), .38)
    elif scene == "blood-red dynasty palace":
        scene_top = _mix(scene_top, (34, 5, 17), .62)
        scene_bottom = _mix(scene_bottom, (53, 10, 24), .48)
    elif scene == "storm-riven sky temple":
        scene_top = _mix(scene_top, (22, 33, 48), .58)
        scene_bottom = _mix(scene_bottom, (29, 35, 43), .30)
    elif scene == "academy observatory":
        scene_top = _mix(scene_top, (28, 27, 58), .56)
        scene_bottom = _mix(scene_bottom, (38, 38, 62), .36)
    elif scene == "crossroads caravan":
        scene_top = _mix(scene_top, (59, 43, 34), .48)
        scene_bottom = _mix(scene_bottom, (91, 63, 43), .34)
    elif scene == "forgotten cathedral":
        scene_top = _mix(scene_top, (24, 30, 39), .58)
        scene_bottom = _mix(scene_bottom, (52, 55, 53), .34)
    elif scene == "sacred reliquary chamber":
        scene_top = _mix(scene_top, (32, 27, 21), .62)
        scene_bottom = _mix(scene_bottom, (73, 59, 37), .32)
    elif scene == "death sanctum":
        scene_top = _mix(scene_top, (9, 12, 25), .66)
        scene_bottom = _mix(scene_bottom, (27, 30, 42), .44)
    elif scene == "black flame sanctuary":
        scene_top = _mix(scene_top, (12, 10, 17), .72)
        scene_bottom = _mix(scene_bottom, (42, 21, 26), .40)
    elif scene == "frenzied flame cathedral":
        scene_top = _mix(scene_top, (52, 37, 17), .62)
        scene_bottom = _mix(scene_bottom, (76, 43, 25), .40)
    elif scene == "ancient crucible sanctuary":
        scene_top = _mix(scene_top, (27, 30, 27), .52)
        scene_bottom = _mix(scene_bottom, (55, 43, 34), .40)
    canvas.image = _gradient(canvas.w, canvas.h, scene_top, scene_bottom)
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")
    # Luminous focal region and atmospheric falloff.
    if scene == "moonlit ruins":
        light = (198, 210, 248)
        center = (280, 98)
    elif scene == "crimson forge and volcanic stone":
        light = (245, 114, 55)
        center = (272, 270)
    elif scene == "frozen highlands":
        light = (189, 218, 241)
        center = (235, 118)
    elif scene == "sacred golden citadel":
        light = (246, 211, 132)
        center = (300, 83)
    elif scene == "academy observatory":
        light = (173, 173, 238)
        center = (290, 96)
    elif scene == "crossroads caravan":
        light = (225, 160, 96)
        center = (300, 180)
    elif scene == "forgotten cathedral":
        light = (221, 211, 174)
        center = (193, 106)
    elif scene == "sacred reliquary chamber":
        light = (248, 213, 133)
        center = (193, 160)
    elif scene == "death sanctum":
        light = (137, 150, 198)
        center = (292, 117)
    elif scene == "black flame sanctuary":
        light = (116, 91, 146)
        center = (280, 174)
    elif scene == "frenzied flame cathedral":
        light = (239, 178, 61)
        center = (192, 123)
    elif scene == "ancient crucible sanctuary":
        light = (166, 112, 78)
        center = (190, 155)
    elif scene == "blood-red dynasty palace":
        light = (191, 36, 59)
        center = (191, 145)
    else:
        light = _mix(accent, (175, 188, 206), .25)
        center = (208, 135)
    _glow(canvas, center, 160, light, 100, 1.15)
    # Camadas de nuvens desfocadas: volume atmosférico sem formas ovais duras.
    clouds = Image.new("RGBA", canvas.image.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds, "RGBA")
    for _ in range(9):
        x, y = rng.randint(-30, 320), rng.randint(42, 205)
        length, thickness = rng.randint(55, 150), rng.randint(10, 25)
        shade = _mix(scene_top, scene_bottom, rng.uniform(.25, .70))
        cd.ellipse((int(x*canvas.sx), int(y*canvas.sy), int((x+length)*canvas.sx),
                    int((y+thickness)*canvas.sy)), fill=(*shade, rng.randint(24, 44)))
    clouds = clouds.filter(ImageFilter.GaussianBlur(canvas.width(13)))
    canvas.image = Image.alpha_composite(canvas.image, clouds)
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")
    # Moon / sun is a real light source, not an arbitrary ring.
    if scene in ("moonlit ruins", "frozen highlands"):
        canvas.ellipse((246, 50, 316, 120), fill=(205, 216, 239, 220), outline=(240, 244, 255, 170), width=2)
        canvas.ellipse((260, 45, 324, 112), fill=(*scene_top, 220))
        canvas.arc((247, 52, 314, 120), 265, 85, fill=(225, 231, 250, 180), width=2)
    elif scene == "sacred golden citadel":
        # Fonte dourada fora do eixo do rosto para não criar um halo automático.
        canvas.ellipse((296, 35, 356, 95), fill=(255, 224, 153, 125), outline=(255, 244, 200, 155), width=1)
        for ang in range(0, 360, 45):
            r = math.radians(ang)
            canvas.line(((326 + math.cos(r) * 38, 65 + math.sin(r) * 38),
                         (326 + math.cos(r) * 49, 65 + math.sin(r) * 49)), (255, 224, 158, 65), 1)
    elif scene == "academy observatory":
        canvas.ellipse((278, 39, 350, 111), fill=(153, 154, 214, 70), outline=(216, 218, 248, 145), width=2)
        canvas.arc((280, 42, 349, 112), 200, 340, (236, 230, 255, 150), 2)


def _draw_architecture(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    top, mid, accent, metal = palette
    scene = direction.scene
    far = Image.new("RGBA", canvas.image.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(far, "RGBA")
    # Distant ridge and architecture.
    ridge = []
    for x in range(-20, 421, 24):
        ridge.append((x, rng.randint(210, 264)))
    far_pts = [(-20, 300), *ridge, (410, 300), (410, 430), (-20, 430)]
    fd.polygon([(int(x * canvas.sx), int(y * canvas.sy)) for x, y in far_pts], fill=(9, 13, 21, 190))
    canvas.image = Image.alpha_composite(canvas.image, far)
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")

    if scene == "ancient forest":
        for x in (-10, 42, 332, 390):
            width = rng.randint(12, 25)
            canvas.polygon(((x, 270), (x + width, 270), (x + width * .58, 45)), (8, 17, 16, 210), (*_alpha(accent, 55),))
            for branch_y in (105, 150, 195):
                side = -1 if x < 150 else 1
                canvas.line(((x + width / 2, branch_y + 40), (x + width / 2 + side * 62, branch_y)), (22, 39, 31, 180), 7)
        for _ in range(15):
            x, y = rng.randint(0, 384), rng.randint(75, 235)
            r = rng.randint(12, 27)
            canvas.ellipse((x-r, y-r*.45, x+r, y+r*.45), fill=(16, 37, 28, 95))
    elif scene in ("sacred golden citadel", "weathered ancient ruins"):
        for x, base, width, height in ((16, 300, 35, 165), (75, 280, 27, 124),
                                       (300, 295, 42, 155), (350, 282, 30, 135)):
            stone = _mix((14, 18, 24), metal, .12)
            canvas.rect((x, base-height, x+width, base), fill=(*stone, 225), outline=(*metal, 75), width=1)
            canvas.polygon(((x-5, base-height), (x+width/2, base-height-22), (x+width+5, base-height)),
                           (*_mul(stone, 1.12), 235), (*metal, 90), 1)
            for wy in range(int(base-height+28), base-12, 35):
                canvas.arc((x+width*.27, wy, x+width*.73, wy+29), 180, 360, (*accent, 80), 2)
        # Broken arch behind the hero.
        canvas.arc((108, 105, 280, 330), 180, 355, (*metal, 95), 5)
        canvas.line(((108, 218), (108, 298)), (*metal, 95), 4)
        canvas.line(((280, 218), (280, 298)), (*metal, 95), 4)
    elif scene == "forgotten cathedral":
        # Nave quebrada, contrafortes e vitral rosácea: um santuário, não um pântano genérico.
        for x, y, w, h in ((14, 164, 43, 210), (66, 126, 34, 246),
                           (286, 126, 34, 246), (327, 164, 43, 210)):
            canvas.polygon(((x,y+h),(x+5,y+24),(x+w/2,y),(x+w-4,y+24),(x+w,y+h)),
                           (25,30,35,235),(149,145,128,145),2)
            canvas.arc((x+7,y+35,x+w-7,y+104),180,360,(204,195,165,105),2)
        canvas.arc((100,70,284,310),190,350,(198,190,164,155),5)
        canvas.ellipse((151,112,233,194),(35,44,54,145),(225,212,176,190),3)
        for i in range(7):
            x=192+math.cos(math.tau*i/7)*34
            y=153+math.sin(math.tau*i/7)*34
            canvas.line(((192,153),(x,y)),(192,181,151,110),2)
        for x in (102,282):
            canvas.line(((x,235),(x+(-20 if x<190 else 20),330)),(112,106,87,115),3)
    elif scene == "sacred reliquary chamber":
        # Câmara de relíquias: altar recuado, colunas laterais e vitral quente.
        for x in (20, 65, 319, 364):
            canvas.rect((x,125,x+17,330),(25,24,22,235),(161,139,99,135),2)
            canvas.arc((x-4,112,x+21,160),180,360,(211,188,137,120),2)
        canvas.arc((104,74,280,285),188,352,(220,194,140,140),4)
        canvas.polygon(((135,295),(249,295),(277,355),(106,355)),(44,35,26,235),(181,145,91,180),2)
        canvas.rect((145,268,239,308),(65,52,35,245),(221,188,118,195),2)
        for x in (153,231):
            canvas.line(((x,265),(x,230)),(233,197,133,145),2)
    elif scene == "death sanctum":
        # Santuário da Morte Destinada: arco partido, raízes secas e runas apagadas.
        for x,y in ((30,150),(348,138)):
            canvas.polygon(((x-20,350),(x-12,y+26),(x,y),(x+15,y+24),(x+21,350)),
                           (17,19,28,245),(124,131,157,130),2)
            for n in range(3):
                canvas.arc((x-12,y+48+n*35,x+14,y+79+n*35),185,350,(124,139,177,100),1)
        canvas.arc((84,58,300,344),190,350,(139,151,190,135),5)
        for side in (-1,1):
            for n in range(4):
                canvas.smooth_line(((192+side*12,406),(192+side*(38+n*8),346-n*14),
                                    (192+side*(70+n*12),301-n*20)),(54,61,76,165),rng.choice((3,5,7)),steps=6)
        for _ in range(22):
            x,y=rng.randint(45,340),rng.randint(100,330)
            canvas.ellipse((x-2,y-2,x+2,y+2),(143,158,205,rng.randint(35,100)))
    elif scene == "black flame sanctuary":
        for x in (34,316):
            canvas.rect((x,130,x+34,345),(18,15,23,245),(114,92,134,110),2)
            canvas.polygon(((x-8,130),(x+17,88),(x+42,130)),(23,16,28,245),(133,105,143,130),2)
        canvas.arc((85,83,301,346),180,355,(106,82,135,125),5)
        for x in (88,295):
            canvas.polygon(((x-12,335),(x-8,277),(x,239),(x+9,280),(x+14,335)),(19,15,24,245),(102,88,129,125),2)
    elif scene == "frenzied flame cathedral":
        for x in (24,72,295,343):
            canvas.rect((x,142,x+24,346),(36,27,18,235),(188,137,59,155),2)
            canvas.arc((x-2,111,x+26,169),180,360,(225,174,72,145),2)
        canvas.arc((91,67,294,330),185,352,(231,172,64,155),5)
        canvas.ellipse((159,108,225,174),(111,72,25,95),(237,184,68,170),2)
        for side in (-1,1):
            canvas.smooth_line(((192,165),(192+side*25,126),(192+side*50,103)),(242,190,90,145),3,steps=6)
    elif scene == "ancient crucible sanctuary":
        # Colunas de raízes petrificadas e arco mineral, evocando o Crisol anterior à Erdtree.
        canvas.arc((72,60,312,355),185,355,(160,111,78,145),7)
        for side in (-1,1):
            x=192+side*130
            canvas.smooth_line(((x,430),(x-side*14,342),(x+side*8,267),(x-side*29,182)),
                               (64,70,54,235),14,steps=8)
            for n in range(3):
                canvas.smooth_line(((x-side*12,310-n*42),(x+side*(27+n*8),283-n*47),
                                    (x+side*(49+n*6),244-n*48)),(99,82,57,180),5,steps=7)
        for _ in range(20):
            x,y=rng.randint(30,354),rng.randint(125,380)
            canvas.ellipse((x-2,y-3,x+2,y+3),(180,123,80,rng.randint(40,110)))
    elif scene == "crimson forge and volcanic stone":
        canvas.polygon(((0, 275), (60, 220), (118, 274), (186, 196), (253, 276), (320, 225), (384, 274), (384, 430), (0, 430)),
                       (22, 12, 14, 235), (101, 41, 33, 105), 2)
        # Forja ao fundo: boca do forno, chaminé e bigorna reduzem o cenário genérico.
        canvas.rect((285,170,355,286),(25,17,18,235),(140,68,48,170),2)
        canvas.arc((297,178,343,250),180,360,(225,104,52,150),4)
        canvas.ellipse((306,208,334,259),(228,75,33,105))
        canvas.line(((43,297),(98,297),(111,284),(126,297),(151,297)),(25,20,19,230),5)
        canvas.polygon(((62,287),(84,278),(111,283),(119,294),(76,299)),(57,51,47,235),(176,129,94,150),2)
        for _ in range(14):
            x, y = rng.randint(0, 384), rng.randint(120, 390)
            r = rng.randint(2, 8)
            canvas.ellipse((x-r, y-r, x+r, y+r), fill=(255, rng.randint(85, 145), 45, rng.randint(45, 125)))
        canvas.line(((0, 324), (90, 304), (152, 328), (232, 301), (384, 323)), (236, 75, 40, 90), 3)
    elif scene == "moonlit ruins":
        for x in (21, 337):
            canvas.rect((x, 132, x+30, 315), fill=(12, 16, 33, 235), outline=(130, 145, 190, 90), width=2)
            canvas.polygon(((x-7, 132), (x+15, 92), (x+37, 132)), (21, 26, 48, 245), (141, 154, 201, 100), 2)
            for y in range(169, 290, 38):
                canvas.rect((x+8, y, x+22, y+20), fill=(12, 19, 39, 255), outline=(129, 148, 196, 75), width=1)
        canvas.arc((90, 140, 295, 345), 180, 360, (139, 151, 208, 90), 4)
    elif scene == "forgotten necropolis or drowned marsh":
        for x in (25, 87, 296, 365):
            y = rng.randint(160, 220)
            canvas.line(((x, y), (x, 324)), (9, 13, 17, 235), 5)
            canvas.line(((x-20, y+25), (x+19, y+25)), (*metal, 90), 3)
            canvas.line(((x-14, y+8), (x+14, y+43)), (10, 14, 18, 220), 3)
        for _ in range(12):
            x, y = rng.randint(0, 384), rng.randint(280, 380)
            canvas.ellipse((x-12, y-4, x+12, y+4), fill=(*accent, 25))
    elif scene == "storm-worn coast":
        canvas.polygon(((0, 270), (70, 238), (140, 274), (228, 225), (312, 269), (384, 244), (384, 430), (0, 430)),
                       (8, 22, 33, 235), (90, 130, 153, 90), 2)
        for y in range(285, 420, 24):
            canvas.arc((30, y-9, 350, y+20), 0, 180, (114, 157, 177, 55), 2)
    elif scene == "scarlet wasteland":
        canvas.polygon(((0,282),(70,215),(124,273),(197,202),(270,273),(326,218),(384,279),(384,430),(0,430)),
                       (39,20,24,245),(160,74,57,105),2)
        for _ in range(30):
            x,y=rng.randint(0,384),rng.randint(245,410)
            canvas.line(((x,y),(x+rng.randint(6,20),y-rng.randint(1,4))), (164,80,62,rng.randint(28,78)),1)
        for _ in range(18):
            x,y=rng.randint(0,384),rng.randint(145,360)
            canvas.ellipse((x-2,y-2,x+2,y+2),(203,91,68,rng.randint(45,125)))
    elif scene == "haligtree bloom":
        for x in (-8,28,350):
            canvas.line(((x,320),(x+35,180),(x+65,105)),(58,88,70,220),13)
            for j in range(4):
                xx=x+25+j*12; yy=155+j*23
                canvas.ellipse((xx-25,yy-10,xx+15,yy+11),(61,102,77,95))
        for _ in range(45):
            x,y=rng.randint(0,384),rng.randint(95,400)
            canvas.ellipse((x-2,y-4,x+2,y+4),(188,82,89,rng.randint(30,110)))
    elif scene == "shadow keep":
        for x in (18,78,300,353):
            canvas.rect((x,132,x+25,318),(19,16,22,245),(120,65,59,115),2)
            canvas.polygon(((x-6,132),(x+12,92),(x+31,132)),(28,19,24,245),(145,82,65,130),2)
        canvas.arc((80,125,300,355),180,360,(170,76,59,95),5)
        for _ in range(17):
            x,y=rng.randint(0,384),rng.randint(250,420)
            canvas.ellipse((x-3,y-3,x+3,y+3),(241,94,46,rng.randint(30,100)))
    elif scene == "blood-red dynasty palace":
        # Mohgwyn: monumental dark-red nave, blood pools and narrow ritual spires.
        for x, y, w, h in ((17,190,42,180),(75,148,30,224),(284,151,31,220),(334,190,38,182)):
            canvas.rect((x,y,x+w,y+h),(25,13,21,245),(145,48,64,145),2)
            canvas.polygon(((x-8,y),(x+w/2,y-37),(x+w+8,y)),(41,13,25,250),(164,55,69,165),2)
        canvas.arc((88,106,296,376),180,360,(182,54,73,110),6)
        canvas.polygon(((112,330),(272,330),(309,430),(75,430)),(49,7,22,175),(118,23,43,105),2)
        for i in range(7):
            x=121+i*24
            canvas.line(((x,365),(x+rng.randint(-8,8),410)),(180,48,65,rng.randint(35,85)),2)
    elif scene == "storm-riven sky temple":
        # Floating stone platforms and broken pillars suspended in a storm front.
        for x, y, w, h in ((18,215,55,88),(88,172,38,126),(300,190,46,106),(352,226,45,85)):
            canvas.rect((x,y,x+w,y+h),(31,37,47,235),(146,159,172,110),2)
            canvas.polygon(((x-8,y),(x+w/2,y-24),(x+w+8,y)),(39,46,57,240),(163,174,185,100),2)
        for x,y in ((70,260),(283,245),(164,190)):
            canvas.polygon(((x,y),(x+40,y+8),(x+25,y+22),(x-12,y+15)),(42,48,57,235),(170,179,187,100),2)
        for _ in range(22):
            x,y=rng.randint(0,384),rng.randint(110,310)
            canvas.line(((x,y),(x+rng.randint(-5,5),y+rng.randint(12,28))),(177,197,214,rng.randint(30,90)),1)
    elif scene == "academy observatory":
        # Terraços e cúpulas da academia, com janelas profundas e observatório ao fundo.
        for x,y,w,h in ((8,174,56,190),(76,131,45,225),(303,145,57,205),(365,190,34,165)):
            canvas.polygon(((x,y+24),(x+10,y),(x+w-8,y+5),(x+w,y+30),(x+w-5,y+h),(x+4,y+h-7)),
                           (32,34,57,230),(141,143,193,130),1)
            canvas.arc((x+8,y+28,x+w-8,y+88),180,360,(182,180,232,135),2)
            for wy in range(y+102,y+h-12,33):
                canvas.rect((x+14,wy,x+w-14,wy+19),(12,16,35,210),(136,137,188,110),1)
        canvas.arc((91,83,291,300),188,350,(162,161,226,125),4)
        canvas.ellipse((159,93,224,158),(20,24,46,90),(181,180,227,105),2)
    elif scene == "crossroads caravan":
        # Estrada em perspectiva, barraca de lona e carroça discreta do comerciante.
        canvas.polygon(((0,295),(384,295),(312,430),(72,430)),(66,49,36,205),(151,112,76,90),1)
        for side in (-1,1):
            x=192+side*118
            canvas.line(((x,300),(192+side*80,430)),(160,123,82,80),2)
        canvas.polygon(((25,252),(83,179),(144,254)),(69,43,35,230),(172,123,83,175),2)
        canvas.polygon(((30,250),(83,192),(139,252),(129,270),(43,270)),(103,67,46,230),(196,145,100,140),1)
        canvas.line(((50,265),(145,265)),(35,28,25,240),4)
        # Carroça em silhueta: rodas, eixo, baú e cobertura.
        canvas.ellipse((253,292,305,344),(20,21,24,220),(175,135,94,180),3)
        canvas.ellipse((263,302,295,334),(25,26,27,245),(172,144,105,150),2)
        canvas.rect((260,251,323,302),(42,33,27,235),(168,133,91,175),2)
        canvas.polygon(((253,250),(270,217),(311,217),(330,250)),(75,50,37,235),(194,148,101,170),2)
        canvas.ellipse((130,227,144,241),(248,174,91,145))
    else:  # frozen highlands fallback
        canvas.polygon(((0, 275), (69, 190), (125, 276), (218, 165),
                        (286, 270), (342, 203), (384, 278), (384, 430), (0, 430)),
                       (23, 38, 53, 235), (176, 204, 224, 95), 2)
        for _ in range(30):
            x, y = rng.randint(0, 384), rng.randint(140, 420)
            canvas.line(((x, y), (x+rng.randint(-3, 3), y+8)),
                        (220, 235, 245, rng.randint(30, 90)), 1)

    # Plano de chão escuro com fissuras e manchas irregulares; evita a grade
    # geométrica que fazia o piso parecer uma arena sintética.
    canvas.polygon(((0, 294), (384, 294), (384, 430), (0, 430)), (7, 10, 15, 118))
    for _ in range(15):
        x=rng.randint(-5,389); y=rng.randint(324,426)
        length=rng.randint(8,38); bend=rng.randint(-9,9)
        shade=_mix((37,34,31),metal,rng.uniform(.08,.22))
        canvas.smooth_line(((x,y),(x+length*.42,y+bend*.35),
                            (x+length,y+bend)),(*shade,rng.randint(18,42)),
                           rng.choice((.6,.8,1.0)),steps=5)
    for _ in range(36):
        x=rng.randint(0,384); y=rng.randint(316,430)
        r=rng.choice((.7,1,1.4,2))
        canvas.ellipse((x-r,y-r,x+r,y+r),(*_mix((36,33,31),metal,.16),rng.randint(10,29)))
    # Foreground framing silhouettes create depth around the center.
    for side in (-1, 1):
        x = 0 if side < 0 else 384
        canvas.polygon(((x, 230), (x+side*32, 300), (x+side*48, 430), (x, 430)), (3, 6, 10, 110))


def _draw_fog_and_grain(canvas: _Painter, accent, rng: random.Random):
    layer = Image.new("RGBA", canvas.image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for y, alpha in ((245, 25), (285, 34), (334, 18)):
        yy = int(y * canvas.sy)
        d.ellipse((-int(60*canvas.sx), yy-int(25*canvas.sy), canvas.w+int(60*canvas.sx), yy+int(25*canvas.sy)),
                  fill=(168, 180, 190, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(canvas.width(18)))
    canvas.image = Image.alpha_composite(canvas.image, layer)
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")
    # Small particulate glints, biased to edges so they do not obscure the focal figure.
    for _ in range(64):
        x = rng.choice((rng.randint(0, 82), rng.randint(300, 383)))
        y = rng.randint(65, 420)
        r = rng.choice((.7, 1.0, 1.5))
        canvas.ellipse((x-r, y-r, x+r, y+r), fill=(*accent, rng.randint(25, 95)))


def _cloth(canvas: _Painter, points, base, accent, rng: random.Random, *, edge=None, folds: int = 7):
    # Bordas curvas e pinceladas longitudinais simulam trama e queda do tecido.
    canvas.smooth_polygon(points, base, edge or (*_mix(base, accent, .42), 140), 1.15, steps=8)
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
    for i in range(folds):
        x = left + (right-left) * (i+.5) / folds
        start_y = top + (bottom-top) * rng.uniform(.07, .22)
        end_y = bottom-rng.uniform(0, 15)
        bend = rng.uniform(-14, 14)
        color = _mix(base, (242, 225, 196), rng.uniform(.12,.30))
        canvas.smooth_line(((x,start_y),(x+bend*.35,(start_y+end_y)/2),(x+bend,end_y)),
                           (*color,rng.randint(32,92)),rng.choice((.8,1,1.4)),steps=6)
        if rng.random()<.38:
            canvas.smooth_line(((x+2,start_y+8),(x+bend*.15,(start_y+end_y)*.53),
                                (x+bend+3,end_y-10)),(*_mul(base,.65),rng.randint(25,62)),.8,steps=6)
    # Borda superior recebe reflexo de tecido apenas em segmentos curtos.
    if len(points)>=3:
        canvas.smooth_line((points[0],points[1],points[2]),(*_mix(base,accent,.33),155),.8,steps=5)


def _metal_plate(canvas: _Painter, points, metal, accent, rng: random.Random, *, dark=None, detail=True):
    dark = dark or _mul(metal, .42)
    canvas.paint_polygon(points, _mix(metal, dark, .22), highlight=_mix(metal, (255, 247, 222), .18),
                         shadow=_mix(dark, (5, 7, 12), .32), outline=(*_mul(metal, 1.18), 235), width=3)
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
    # Faceted plate catches directional light on its upper-left bevel.
    center_x = (left + right) / 2
    canvas.polygon(((left+4, top+3), (center_x, top+5), (right-5, top+13),
                    (center_x, top+(bottom-top)*.55), (left+8, bottom-7)),
                   (*_mix(metal, (238, 233, 218), .24), 245), (*accent, 130), 1)
    canvas.line(((left+7, top+6), (center_x, top+9), (right-8, top+17)), (255, 255, 255, 100), 1)
    canvas.line(((left+9, bottom-7), (center_x, bottom-5), (right-9, bottom-11)), (*_mul(metal, .55), 210), 2)
    if detail:
        for t in (.18, .82):
            x = left + (right-left)*t
            y = top + (bottom-top)*.28
            canvas.ellipse((x-2, y-2, x+2, y+2), fill=(*_mix(metal, (255, 242, 207), .55), 230))
        if bottom-top > 28 and right-left > 25:
            canvas.line(((center_x, top+12), (center_x-3, (top+bottom)/2), (center_x+2, bottom-12)), (*accent, 85), 1)


def _leather_strap(canvas: _Painter, points, base=(62, 39, 27)):
    canvas.line(points, (*_mul(base, .55), 255), 8)
    canvas.line(points, (*base, 255), 5)
    for x, y in points[::max(1, len(points)//3)]:
        canvas.ellipse((x-1.5, y-1.5, x+1.5, y+1.5), fill=(205, 164, 103, 220))


def _draw_humanoid(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random, *, scale=1.0, y_shift=0, center_x=None):
    top, mid, accent, metal = palette
    is_mage = direction.subject == "arcane or ritual figure"
    is_duelist = direction.subject == "agile scout or duelist"
    is_noble = direction.subject == "noble or commander"
    is_armored = direction.subject in {"armored knight", "mounted rider", "ancient dragon warrior"}
    is_robe = direction.subject in {"arcane or ritual figure", "scholar or explorer", "cleric or preacher"}
    is_civilian = direction.subject == "artisan or merchant"
    is_standard = direction.subject == "standard bearer"
    is_light = is_mage or is_duelist or is_noble or is_robe or is_civilian or is_standard
    cx = float(center_x) if center_x is not None else 190 + rng.randint(-15, 15)
    base_y = 409 + y_shift
    if direction.subject == "mounted rider":
        # Montaria em três volumes sobrepostos: garupa, tórax/pescoço e cabeça.
        # Articulações e arreios têm leitura própria; evita a silhueta de oval com palitos.
        _glow(canvas, (192, 350), 105, accent, 28, .52)
        hide = (30, 25, 23)
        horse_body=((cx-112,296),(cx-96,268),(cx-56,250),(cx-3,247),(cx+49,261),
                    (cx+81,286),(cx+76,325),(cx+47,352),(cx-25,359),(cx-84,340))
        canvas.smooth_polygon(horse_body,(*hide,255),(143,115,86,185),2,steps=9)
        canvas.paint_ellipse((cx-79,270,cx+30,339),(56,43,35),highlight=(111,82,58),
                             shadow=(21,19,19),outline=(110,81,60,120),width=1)
        # Pescoço ascendente e peito em planos de músculo, com transição para a cabeça.
        neck=((cx+29,291),(cx+47,250),(cx+69,211),(cx+104,205),(cx+126,228),
              (cx+113,269),(cx+84,317),(cx+56,337))
        canvas.smooth_polygon(neck,(38,30,27,255),(157,124,91,200),2,steps=8)
        canvas.paint_polygon(((cx+57,264),(cx+81,222),(cx+108,220),(cx+112,265),(cx+82,301)),
                             (75,53,40),highlight=(134,95,66),shadow=(24,21,20),outline=(98,71,52,100),width=1)
        head=((cx+91,224),(cx+103,199),(cx+132,194),(cx+154,208),
              (cx+149,233),(cx+127,249),(cx+103,245))
        canvas.smooth_polygon(head,(42,31,27,255),(164,131,96,210),2,steps=8)
        muzzle=((cx+130,214),(cx+157,218),(cx+171,231),(cx+150,244),(cx+127,238))
        canvas.smooth_polygon(muzzle,(32,25,23,255),(134,103,77,190),1.5,steps=7)
        canvas.ellipse((cx+136,210,cx+143,217),(213,173,105,245))
        canvas.ellipse((cx+138,211,cx+141,215),(14,13,13,255))
        # Orelhas, crina em mechas e cauda com direção do vento.
        canvas.smooth_polygon(((cx+102,203),(cx+93,177),(cx+115,194),(cx+120,210)),(30,23,22,255),(137,103,77,170),1,steps=6)
        for i in range(8):
            sx=cx+69+i*7; sy=211+i*7
            canvas.smooth_line(((sx,sy),(sx+18,sy+21),(sx+10,sy+44)),(22,18,18,235),rng.choice((2,3,4)),steps=6)
        canvas.smooth_line(((cx-104,307),(cx-137,329),(cx-154,365)),(25,19,18,245),7,steps=8)
        for i in range(5):
            canvas.smooth_line(((cx-133+i*4,338),(cx-148+i*5,362),(cx-155+i*7,382)),(47,29,26,225),2,steps=6)
        # Quatro membros com joelho, boleto e casco; dois parcialmente ocultos.
        legs=(
            ((cx-74,322),(cx-91,352),(cx-86,389),(cx-91,406)),
            ((cx-39,344),(cx-47,369),(cx-36,397),(cx-37,409)),
            ((cx+35,337),(cx+46,363),(cx+43,393),(cx+48,408)),
            ((cx+62,321),(cx+76,349),(cx+69,382),(cx+77,406)),
        )
        for index, path in enumerate(legs):
            base=(37,29,26,255) if index in (0,3) else (24,21,20,255)
            canvas.smooth_line(path,base,12 if index in (0,3) else 9,steps=7)
            canvas.smooth_line((path[1],path[2],path[3]),(102,75,55,165),2,steps=7)
            hx,hy=path[-1]
            canvas.polygon(((hx-9,hy-4),(hx+9,hy-4),(hx+12,hy+5),(hx-11,hy+5)),
                           (17,16,16,255),(110,88,68,170),1)
        # Sela, manta curta e arreios de couro atravessam o tronco sem cobri-lo.
        canvas.smooth_polygon(((cx-44,274),(cx+14,263),(cx+46,282),(cx+36,307),
                               (cx-34,310),(cx-56,292)),(37,25,21,255),(164,119,76,200),2,steps=7)
        canvas.smooth_line(((cx-23,270),(cx+43,271),(cx+97,235)),(103,66,42,250),4,steps=7)
        canvas.smooth_line(((cx+92,234),(cx+114,248),(cx+129,244)),(139,103,70,230),2,steps=6)
        canvas.smooth_line(((cx+108,240),(cx+92,269),(cx+58,288)),(131,96,64,235),2,steps=7)
        canvas.smooth_line(((cx-59,294),(cx-36,312),(cx-7,322)),(153,112,74,155),2,steps=7)
        # Correias e estribos metálicos sob a sela.
        canvas.line(((cx-35,295),(cx-43,352)),(75,47,29,255),4)
        canvas.line(((cx+28,291),(cx+37,350)),(75,47,29,255),4)
        canvas.polygon(((cx-54,348),(cx-29,348),(cx-25,365),(cx-51,365)),(75,79,79,255),(182,159,116,225),2)
        canvas.polygon(((cx+27,346),(cx+51,346),(cx+56,363),(cx+31,363)),(75,79,79,255),(182,159,116,225),2)
        # Luz quente acompanha o dorso e separa a montaria do cenário.
        canvas.smooth_line(((cx-82,270),(cx-33,258),(cx+20,263),(cx+61,284)),(189,153,109,110),2,steps=8)
        _glow(canvas,(cx+128,225),24,(224,177,102),32,.8)
        # Rider occupies upper middle; scaled down to sit naturally on the saddle.
        cx = 185
        base_y = 348
        scale = min(scale, .90)

    head_y = 129 + y_shift * .25
    head_r = 23 if not is_mage else 22
    shoulder = 62 if is_robe else (58 if is_duelist or is_civilian else (66 if is_standard else 74))
    torso_top, waist_y, hip_y = 161+y_shift*.12, 260+y_shift*.18, 291+y_shift*.18
    knee_y, foot_y = 350+y_shift*.18, base_y
    def pt(x, y):
        return cx + (x-cx)*scale, head_y + (y-head_y)*scale
    def poly(points, fill, outline=None, width=1):
        canvas.polygon([pt(x,y) for x,y in points], fill, outline, width*scale)
    def line(points, fill, width=1):
        canvas.line([pt(x,y) for x,y in points], fill, width*scale)
    def ellipse(box, fill=None, outline=None, width=1):
        canvas.ellipse(tuple(pt(box[i], box[i+1])[j] for i in (0,2) for j in (0,1)), fill, outline, width*scale)

    body = _mix((20, 24, 31), top, .25)
    cloth = _mix(top, (72, 52, 43), .20)
    skin = (133, 101, 79)
    if is_civilian:
        body = (39, 34, 29)
        cloth = _mix(mid, (82, 62, 44), .38)
    # Silhueta traseira adequada ao papel: capa militar, manto ritual ou mochila.
    if not is_civilian:
        if is_duelist:
            # Manto curto e assimétrico: pernas e silhueta móvel permanecem expostas.
            cape_points = ((cx-38, torso_top+5),(cx+13, torso_top+9),(cx+57, waist_y+25),
                           (cx+26, waist_y+39),(cx-20, waist_y+25),(cx-49, waist_y+2))
        else:
            cape_points = ((cx-32, torso_top+8), (cx+31, torso_top+8), (cx+78, foot_y-3),
                           (cx+18, foot_y-19), (cx-74, foot_y+2), (cx-55, 257))
        cape_color = _mul(top, .55 if is_robe else .62)
        _cloth(canvas, [pt(x,y) for x,y in cape_points], cape_color, accent, rng,
               edge=(*_mix(cape_color,metal,.24),145), folds=13 if is_robe else (5 if is_duelist else 9))
        if not is_duelist:
            for i in range(7 if is_robe else 5):
                xx = cx-45+i*15
                line(((xx, 240), (xx+rng.randint(-16, 15), 335+rng.randint(0, 36))),
                     (*_mix(top, metal, .25), rng.randint(45,95)), 1)
    else:
        # Mercadores e artesãos usam volume funcional nas costas, não uma capa de herói.
        _leather_strap(canvas,(pt(cx-27,torso_top+10),pt(cx+44,waist_y+44)),(55,36,25))
    # Legs are separate articulated forms, with distinct knee and shin guards.
    hip = (cx-3, hip_y)
    for side in (-1, 1):
        sx = cx + side*22
        knee_x = sx + side*rng.randint(5, 17)
        ankle_x = knee_x + side*rng.randint(-4, 9)
        leg_width = 24 if is_armored or is_noble else (17 if is_light else 22)
        line(((sx, hip_y), (knee_x, knee_y), (ankle_x, foot_y-18)), (*body, 255), leg_width)
        if is_armored or is_noble or is_standard:
            poly(((knee_x-15, knee_y-12), (knee_x+13, knee_y-13), (ankle_x+12, foot_y-18),
                  (ankle_x-12, foot_y-15)), (*_mul(body, .78), 255), (*metal, 150), 1)
            _metal_plate(canvas, (pt(knee_x-14,knee_y-16), pt(knee_x+13,knee_y-15),
                                  pt(knee_x+10,knee_y+8), pt(knee_x-12,knee_y+9)), metal, accent, rng)
            poly(((ankle_x-13, foot_y-26), (ankle_x+13, foot_y-24),
                  (ankle_x+24, foot_y-4), (ankle_x-16, foot_y-3)), (*_mul(body, .68),255), (*metal,150), 1)
        else:
            # Calça, calçado e caneleira de couro sem placas metálicas inventadas.
            poly(((ankle_x-10,foot_y-31),(ankle_x+10,foot_y-30),
                  (ankle_x+17,foot_y-4),(ankle_x-17,foot_y-3)),(*_mul(cloth,.68),245),(*_mul(body,.7),170),1)
        line(((ankle_x-8, foot_y-6), (ankle_x+20, foot_y-5)), (*_mix(body,metal,.28),190), 1.2)
    # Torso: robes, workwear, light leather and plate use different silhouettes.
    if is_robe or is_civilian:
        flare = 68 if is_robe else 54
        robe_points = ((cx-shoulder,torso_top+2),(cx-shoulder+10,torso_top-5),
                       (cx+shoulder-8,torso_top-2),(cx+shoulder,torso_top+10),
                       (cx+flare,foot_y-1),(cx+27,foot_y-8),(cx-18,foot_y-3),
                       (cx-flare,foot_y-1),(cx-shoulder+9,waist_y+36))
        base_cloth = _mul(cloth,.76 if is_robe else .88)
        _cloth(canvas, [pt(x,y) for x,y in robe_points], base_cloth, accent, rng,
               edge=(*_mix(base_cloth, metal, .25),145), folds=14 if is_robe else 9)
        # Sobreveste e painéis de tecido têm bordas independentes; não viram uma placa lisa.
        if is_robe:
            poly(((cx-43,torso_top+8),(cx+38,torso_top+7),(cx+26,waist_y+30),
                  (cx+4,foot_y-4),(cx-31,waist_y+34)), (*_mix(cloth,top,.25),230), (*metal,115), 1)
        else:
            poly(((cx-31,torso_top+8),(cx+33,torso_top+6),(cx+25,waist_y+24),
                  (cx-27,waist_y+27)), (*_mix(cloth,(55,43,34),.20),245), (*metal,105), 1)
        for i in range(7 if is_robe else 5):
            x = cx-45+i*(90/(6 if is_robe else 4))
            line(((x,torso_top+18),(cx+(x-cx)*.72,foot_y-8)),
                 (*_mix(base_cloth,metal,.30),rng.randint(45,105)), 1.2)
        # Faixa, bolsa, costura ou cinto de trabalho, conforme a função.
        line(((cx-36,waist_y+17),(cx+38,waist_y+16)), (*_mul(body,.66),225), 5)
        if is_civilian:
            _leather_strap(canvas,(pt(cx-31,torso_top+10),pt(cx+27,waist_y+18)),(68,43,28))
            poly(((cx+24,waist_y+2),(cx+48,waist_y+4),(cx+50,waist_y+35),(cx+26,waist_y+34)),
                 (74,48,31,245),(*metal,130),1)
    elif is_duelist:
        # Couro segmentado e proteção leve: silhueta ágil sem ombreiras de cavaleiro.
        torso_shape=((cx-shoulder,torso_top+16),(cx-shoulder+15,torso_top+2),
                     (cx+shoulder-10,torso_top+4),(cx+shoulder,torso_top+20),
                     (cx+34,waist_y),(cx-29,waist_y+5))
        poly(torso_shape,(*body,250),(*_mix(metal,accent,.30),150),1)
        _cloth(canvas,[pt(cx-37,torso_top+17),pt(cx+35,torso_top+14),
                       pt(cx+27,waist_y-4),pt(cx-30,waist_y+3)],cloth,accent,rng,
               edge=(*_mix(cloth,metal,.25),125),folds=5)
        _leather_strap(canvas,(pt(cx-35,torso_top+22),pt(cx+26,waist_y-14)),(48,31,24))
    elif is_standard:
        torso_shape=((cx-shoulder,torso_top+17),(cx-shoulder+12,torso_top),
                     (cx+shoulder-12,torso_top),(cx+shoulder,torso_top+17),
                     (cx+35,waist_y),(cx-35,waist_y))
        poly(torso_shape,(*body,255),(*metal,180),2)
        _metal_plate(canvas,(pt(cx-30,torso_top+8),pt(cx+30,torso_top+8),
                             pt(cx+20,waist_y-5),pt(cx,waist_y+7),pt(cx-22,waist_y-5)),metal,accent,rng,detail=False)
    else:
        torso_shape = ((cx-shoulder,torso_top+17),(cx-shoulder+13,torso_top),(cx+shoulder-13,torso_top),
                       (cx+shoulder,torso_top+17),(cx+45,waist_y),(cx-43,waist_y))
        poly(torso_shape, (*body,255), (*metal,230), 3)
        # Under-tunic and center breastplate.
        poly(((cx-42,torso_top+12),(cx+42,torso_top+12),(cx+28,waist_y-3),(cx,waist_y+17),(cx-28,waist_y-3)),
             (*cloth,255), (*accent,205), 2)
        _metal_plate(canvas, (pt(cx-37,torso_top+6), pt(cx+37,torso_top+6), pt(cx+26,waist_y-11),
                              pt(cx,waist_y+3), pt(cx-26,waist_y-11)), metal, accent, rng)
        # Shoulder protection only belongs to plate armor; nobles use fabric mantles.
        if is_armored or is_noble:
            for side in (-1,1):
                sx = cx+side*(shoulder-4)
                poly(((sx-side*19,torso_top+2),(sx+side*12,torso_top+8),(sx+side*21,torso_top+30),
                      (sx+side*4,torso_top+40),(sx-side*20,torso_top+25)), (*_mul(metal,.64),255), (*metal,210), 1.5)
                line(((sx-side*13,torso_top+8),(sx+side*8,torso_top+17)), (255,255,255,85), 1)
                ellipse((sx-3,torso_top+20,sx+3,torso_top+26), fill=(*accent,220))
        # Belt, clasp and engraved panel.
        line(((cx-39,waist_y),(cx+40,waist_y)), (28,18,15,255), 9)
        line(((cx-39,waist_y-3),(cx+40,waist_y-3)), (*metal,220), 2)
        poly(((cx,waist_y-11),(cx+12,waist_y),(cx,waist_y+11),(cx-12,waist_y)),
             (*accent,240), (*metal,255), 2)
        for i in range(4):
            line(((cx-27+i*18,torso_top+28),(cx-23+i*15,waist_y-19)), (*metal,70), 1)
        # Fine etched channels, rivets and central sigil make the cuirass a crafted object.
        line(((cx-23,torso_top+25),(cx-12,torso_top+40),(cx,torso_top+47)),(*metal,145),1)
        line(((cx+23,torso_top+25),(cx+12,torso_top+40),(cx,torso_top+47)),(*metal,145),1)
        for side in (-1,1):
            for yy in (torso_top+18,torso_top+34,torso_top+49):
                ellipse((cx+side*31-2,yy-2,cx+side*31+2,yy+2),(*_mix(metal,(255,247,218),.3),235))
    # Arms use a bent, asymmetric gesture to give each pose a readable action.
    left_sh = (cx-shoulder+8, torso_top+19)
    right_sh = (cx+shoulder-8, torso_top+17)
    left_el = (cx-shoulder-10, torso_top+79)
    right_el = (cx+shoulder+15, torso_top+61)
    left_hand = (cx-shoulder+5, torso_top+115)
    right_hand = (cx+shoulder+24, torso_top+95)
    if is_mage:
        right_el, right_hand = (cx+75, torso_top+47), (cx+88, torso_top+5)
        left_el, left_hand = (cx-60, torso_top+85), (cx-28, torso_top+65)
    elif is_duelist:
        right_el, right_hand = (cx+78, torso_top+50), (cx+110, torso_top+14)
        left_el, left_hand = (cx-73, torso_top+76), (cx-99, torso_top+102)
    for start, elbow, hand, side in ((left_sh,left_el,left_hand,-1),(right_sh,right_el,right_hand,1)):
        sleeve_width = 15 if is_robe or is_mage else (14 if is_civilian else 19)
        line((start, elbow, hand), (*body,255), sleeve_width)
        if is_armored or is_noble or is_standard:
            ellipse((elbow[0]-10,elbow[1]-10,elbow[0]+10,elbow[1]+10),
                    (*_mix(body,metal,.27),255), (*metal,190), 1.5)
            # Braçadeira de metal com chanfro e luz lateral.
            poly(((elbow[0]-11,elbow[1]-11),(elbow[0]+11,elbow[1]-11),
                  (hand[0]+8,hand[1]+6),(hand[0]-8,hand[1]+8)), (*_mul(metal,.68),245), (*metal,185), 1.5)
        else:
            line(((start[0],start[1]),(elbow[0],elbow[1])),(*_mix(cloth,metal,.24),180),2)
            line(((elbow[0]-5,elbow[1]+2),(hand[0],hand[1])),(*_mul(cloth,.72),185),1)
        ellipse((hand[0]-8,hand[1]-8,hand[0]+8,hand[1]+8),
                (113,83,62,255) if is_armored or is_noble else skin, (*metal,165), 1)
    # Head, neck and face are drawn after the torso so the silhouette reads clearly.
    poly(((cx-12,torso_top-6),(cx+12,torso_top-6),(cx+13,torso_top+21),(cx-13,torso_top+21)),
         (*skin,255), (*_mul(skin,.65),255), 1)
    canvas.paint_ellipse(tuple(pt(x,y) for x,y in ((cx-head_r,head_y-head_r),(cx+head_r,head_y+head_r)) for y in (y,)) if False else (pt(cx-head_r,head_y-head_r)[0],pt(cx-head_r,head_y-head_r)[1],pt(cx+head_r,head_y+head_r)[0],pt(cx+head_r,head_y+head_r)[1]),
                         skin,highlight=(190,145,111),shadow=(65,45,38),outline=(*_mul(skin,.56),255),width=2)
    # Facial shadow plane, nose bridge, eye line and cheek light.
    poly(((cx-18,head_y-7),(cx+17,head_y-9),(cx+11,head_y+14),(cx-13,head_y+17)),
         (67,48,41,150))
    line(((cx-14,head_y-4),(cx-3,head_y-5)), (21,19,20,255), 2)
    line(((cx+4,head_y-5),(cx+15,head_y-4)), (21,19,20,255), 2)
    line(((cx,head_y-1),(cx-3,head_y+7),(cx+3,head_y+8)), (45,34,31,210), 2)
    line(((cx-7,head_y+14),(cx+8,head_y+14)), (33,24,22,220), 2)
    ellipse((cx-17,head_y-1,cx-9,head_y+6), (190,140,107,75))
    # Hair, hood or helmet silhouette.
    if is_mage or direction.subject in {"scholar or explorer", "cleric or preacher"}:
        poly(((cx-28,head_y-11),(cx-35,head_y-49),(cx-4,head_y-34),(cx+25,head_y-48),(cx+30,head_y-7)),
             (*_mul(top,.45),255), (*metal,185), 2)
        poly(((cx-34,head_y-10),(cx,head_y-24),(cx+34,head_y-10),(cx+43,head_y+8),
              (cx+24,head_y+3),(cx,head_y-3),(cx-24,head_y+5)), (*_mul(top,.66),255), (*accent,175), 2)
        line(((cx-23,head_y-17),(cx+22,head_y-17)), (*metal,190), 2)
    elif is_armored:
        # Capacete segmentado: só aparece em arquétipos explicitamente militares.
        ellipse((cx-29,head_y-37,cx+29,head_y+18),(*_mul(metal,.64),255),(*metal,220),2)
        poly(((cx-25,head_y-10),(cx-21,head_y+16),(cx-8,head_y+28),(cx+8,head_y+28),
              (cx+23,head_y+15),(cx+26,head_y-10),(cx+12,head_y-18),(cx-12,head_y-18)),
             (*_mul(body,.68),255),(*metal,215),2)
        line(((cx-27,head_y-8),(cx,head_y-16),(cx+27,head_y-8)), (255,255,255,145), 3)
        line(((cx-22,head_y+3),(cx+21,head_y+3)), (*_mul(metal,.52),255), 4)
        line(((cx,head_y-14),(cx,head_y+22)), (*_mix(metal,(255,246,220),.25),240), 3)
        # Narrow eye slit and inset side vents make the visor legible at card size.
        line(((cx-13,head_y-1),(cx+13,head_y-1)), (5,8,13,255), 5)
        line(((cx-10,head_y-2),(cx+8,head_y-2)), (*accent,220), 1)
        for side in (-1,1):
            line(((cx+side*21,head_y+8),(cx+side*16,head_y+17)),(*metal,165),2)
    else:
        # Cabeça descoberta: cabelo, costeleta e contorno facial substituem o capacete genérico.
        hair_color = (59,39,31) if not is_noble else _mix(metal,(232,211,160),.42)
        if is_civilian:
            hair_color = (42,34,28)
        poly(((cx-24,head_y-3),(cx-25,head_y-25),(cx-9,head_y-39),
              (cx+14,head_y-36),(cx+27,head_y-18),(cx+23,head_y-3),
              (cx+13,head_y-15),(cx-10,head_y-13)), (*hair_color,245), (*_mul(hair_color,.68),190), 1)
        if is_noble:
            # Diadema ou aro cerimonial de baixa altura, sem transformar a figura em capacete.
            canvas.arc((cx-25,head_y-28,cx+25,head_y+1),190,350,(*metal,220),3)
            canvas.ellipse((cx-3,head_y-31,cx+3,head_y-25),(*accent,240),(*metal,210),1)
        elif is_civilian:
            canvas.line(((cx-23,head_y-5),(cx-30,head_y+8)),(*hair_color,220),4)
            canvas.line(((cx+22,head_y-5),(cx+28,head_y+8)),(*hair_color,220),4)

    # A arma/objeto é desenhado a partir do título e da lore, nunca por padrão.
    equipment = direction.equipment
    weapon_x, weapon_y = right_hand
    if equipment == "staff":
        canvas.line(((weapon_x, weapon_y+30),(weapon_x-7, weapon_y-121)), (*_mul(metal,.78),255), 6)
        canvas.line(((weapon_x-2,weapon_y-12),(weapon_x-7,weapon_y-111)), (255,255,255,130), 2)
        canvas.polygon(((weapon_x-23,weapon_y-96),(weapon_x-7,weapon_y-129),(weapon_x+10,weapon_y-94),
                        (weapon_x-7,weapon_y-75)), (*accent,170), (*metal,235), 1)
        _glow(canvas,(weapon_x-7,weapon_y-103),33,accent,66)
    elif equipment == "blade" or (is_duelist and _contains(direction.action,"combat","strike")):
        canvas.line(((weapon_x-18,weapon_y+14),(weapon_x+46,weapon_y-119)), (151,165,177,255), 6)
        canvas.line(((weapon_x-6,weapon_y-2),(weapon_x+44,weapon_y-108)), (244,242,226,225), 2)
        canvas.line(((weapon_x-34,weapon_y+8),(weapon_x+4,weapon_y+24)), (*accent,250), 5)
    elif equipment == "spear":
        canvas.line(((weapon_x-24,weapon_y+42),(weapon_x+34,weapon_y-146)), (*_mix(metal,(68,43,28),.42),255), 6)
        canvas.polygon(((weapon_x+26,weapon_y-143),(weapon_x+34,weapon_y-169),
                        (weapon_x+43,weapon_y-143),(weapon_x+34,weapon_y-130)),
                       (*_mix(metal,(226,218,197),.22),255),(*metal,225),2)
    elif equipment == "bow":
        canvas.arc((weapon_x-25,weapon_y-97,weapon_x+55,weapon_y+35),245,115,(*_mix(metal,(75,42,27),.3),255),6)
        canvas.line(((weapon_x+10,weapon_y-91),(weapon_x+10,weapon_y+28)),(*metal,185),1)
    elif equipment == "hammer":
        canvas.line(((weapon_x-5,weapon_y+24),(weapon_x+2,weapon_y-89)),(*_mix(metal,(67,42,29),.35),255),8)
        canvas.polygon(((weapon_x-29,weapon_y-104),(weapon_x+28,weapon_y-104),
                        (weapon_x+31,weapon_y-70),(weapon_x-27,weapon_y-70)),
                       (*_mix(metal,(44,39,35),.30),255),(*metal,220),3)
    elif equipment == "banner":
        pole_x, pole_y = cx+shoulder+24, torso_top-54
        canvas.line(((pole_x,pole_y),(pole_x-4,foot_y-2)),(*_mix(metal,(74,47,31),.48),255),5)
        canvas.polygon(((pole_x-1,pole_y+8),(pole_x+55,pole_y+24),
                        (pole_x+45,pole_y+98),(pole_x-2,pole_y+86)),
                       (*accent,235),(*metal,210),1)
        canvas.line(((pole_x+7,pole_y+17),(pole_x+43,pole_y+30),(pole_x+35,pole_y+82)),
                    (*_mix(accent,(255,231,171),.35),210),2)
    elif equipment == "book or map":
        canvas.polygon(((weapon_x-18,weapon_y-20),(weapon_x+17,weapon_y-26),
                        (weapon_x+22,weapon_y+13),(weapon_x-13,weapon_y+20)),
                       (94,65,42,255),(*metal,220),2)
        canvas.line(((weapon_x+1,weapon_y-22),(weapon_x+5,weapon_y+16)),(*_mix(metal,(245,227,184),.35),225),1)
        for j in range(3):
            canvas.line(((weapon_x-10,weapon_y-10+j*8),(weapon_x-1,weapon_y-9+j*8)),(223,203,163,160),1)

    # Final rim light on the side facing the principal light.
    line(((cx-shoulder,torso_top+12),(cx-shoulder-3,torso_top+66),(cx-33,waist_y+9)), (255,231,184,100), 2)
    line(((cx+shoulder,torso_top+16),(cx+shoulder+5,torso_top+53)), (*accent,90), 2)


def _draw_twin_pair(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    """Duas irmãs: contraste de função e silhueta, com leitura clara em miniatura."""
    top, mid, accent, metal = palette
    rear_palette = (
        _mix(top, (22, 28, 47), .34), _mix(mid, (25, 29, 43), .30),
        _mix(accent, (166, 179, 222), .30), _mix(metal, (168, 180, 206), .32),
    )
    # A irmã ao fundo é estudiosa e observadora; a da frente é a exploradora.
    rear = ArtDirection("scholar or explorer", direction.scene, direction.faction,
                        "the elder sister studies the buried passage and holds a map close to her chest",
                        "layered travel mantle, parchment, brass fittings and worn leather")
    front = ArtDirection("agile scout or duelist", direction.scene, direction.faction,
                         "the younger sister leads with a low alert stance, one hand parting the underground mist",
                         "fitted dark leather, short travel cloak, practical cloth and discreet steel")
    _draw_humanoid(canvas, rear, rear_palette, rng, scale=.78, y_shift=9, center_x=255)
    _draw_humanoid(canvas, front, palette, rng, scale=.94, y_shift=1, center_x=128)
    # Map and compass separate their roles without creating duplicate staffs/weapons.
    canvas.polygon(((238,245),(270,237),(276,271),(246,282)),
                   (173,145,101,235),(225,202,157,220),1)
    canvas.line(((246,252),(267,248),(270,265)),(72,61,52,180),1)
    canvas.ellipse((117,232,135,250),(38,47,57,245),(190,169,126,210),1)
    canvas.line(((126,235),(132,246)),(*metal,190),1)
    # Shared stitched crescent insignia; offset to avoid mirror symmetry.
    canvas.arc((104,194,134,231),194,342,(*metal,170),2)
    canvas.arc((239,178,266,212),202,346,(*accent,155),1.5)


def _draw_necromancer(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    """Servo da morte com invocações espectrais legíveis, não apenas névoa decorativa."""
    top, mid, accent, metal = palette
    ritual = ArtDirection("arcane or ritual figure", direction.scene, direction.faction,
                          direction.action, direction.material, direction.canonical, "")
    _glow(canvas, (191, 306), 118, (148, 173, 203), 78, .82)
    # Duas presenças incompletas emergem atrás do invocador, em escala menor.
    for side in (-1, 1):
        x = 192 + side * 112
        y = 287 + rng.randint(-8, 12)
        _glow(canvas, (x, y+22), 42, (153, 185, 211), 42, .65)
        canvas.ellipse((x-16,y-47,x+16,y-15),(12,21,34,218),(192,210,222,205),1.7)
        # Cavidades oculares e mandíbula sugerida por poucos planos claros.
        canvas.ellipse((x-9,y-37,x-2,y-29),(3,8,16,255))
        canvas.ellipse((x+2,y-37,x+9,y-29),(3,8,16,255))
        canvas.arc((x-9,y-28,x+9,y-12),8,170,(215,227,233,210),1.2)
        canvas.smooth_polygon(((x-22,y-13),(x-31,y+35),(x-17,y+54),
                               (x,y+43),(x+17,y+54),(x+31,y+35),(x+22,y-13)),
                              (93,124,150,142),(206,222,228,190),1.1,steps=5)
        for rib in range(3):
            canvas.arc((x-17+rib*2,y+2+rib*8,x+17-rib*2,y+29+rib*8),8,172,
                       (219,232,237,145-rib*18),1.2)
        # Mãos espectrais apontam para o ritual, com dedos independentes.
        canvas.smooth_line(((x-side*8,y+43),(x-side*14,y+66),(192-side*34,354)),
                           (153,174,191,145),6,steps=6)
        for finger in range(3):
            fx = 192-side*34 + side*(finger-1)*5
            canvas.smooth_line(((192-side*34,354),(fx,342-finger*2),(fx-side*2,332-finger*3)),
                               (193,208,219,155),2,steps=5)
    ritual_palette = (_mix(top,(18,22,33),.55), _mix(mid,(13,16,25),.60),
                      _mix(accent,(135,174,194),.42), _mix(metal,(159,181,198),.28))
    _draw_humanoid(canvas, ritual, ritual_palette, rng, scale=1.0)
    # Amuleto ósseo central e costuras frias definem a função sem impor arma.
    canvas.ellipse((176,245,207,278),(16,22,31,240),(167,185,205,190),2)
    canvas.ellipse((187,256,196,266),(191,218,239,235))
    for side in (-1,1):
        canvas.smooth_line(((192+side*26,192),(192+side*42,228),(192+side*37,261)),
                           (154,171,188,135),2,steps=7)


def _draw_group(canvas: _Painter, card: dict[str, Any], direction: ArtDirection, palette, rng: random.Random):
    """Forma uma pequena unidade coletiva, sem duplicar um único retrato em escala."""
    title = _norm(card.get("nome"))
    top, mid, accent, metal = palette
    is_robed = _contains(title, "discipulos", "peregrinos", "apostolos", "devotos")
    is_guard = _contains(title, "guardioes", "guardas", "sentinelas")
    is_knight = _contains(title, "cavaleiros", "combatentes", "veteranos", "juramentados")
    # Os flancos ficam em segundo plano e a figura central conduz a leitura.
    figures = ((104, 177, .76), (279, 177, .76), (191, 131, 1.0))
    for index, (cx, head_y, scale) in enumerate(figures):
        foot_y = 408 if index == 2 else 382
        shoulder = 43 if index == 2 else 34
        body = _mix((16, 20, 27), top, .34 if index == 2 else .22)
        robe = _mix(top, mid, .34)
        if is_robed:
            robe_points=((cx-shoulder,head_y+37),(cx+shoulder,head_y+37),
                         (cx+shoulder+17,foot_y),(cx-shoulder-17,foot_y))
            _cloth(canvas,robe_points,robe,accent,rng,edge=(*_mix(robe,metal,.55),195),folds=7)
            canvas.polygon(((cx-12,head_y+43),(cx+12,head_y+43),(cx+18,foot_y),(cx-18,foot_y)),
                           (*_mul(robe,.7),235),(*metal,120),1)
        else:
            # Capa curta, túnica e placas de ombro em camadas separadas.
            cape=((cx-shoulder,head_y+35),(cx+shoulder,head_y+35),(cx+shoulder+21,foot_y),
                  (cx-shoulder-22,foot_y))
            _cloth(canvas,cape,_mul(top,.58),accent,rng,edge=(*accent,145),folds=6)
            torso=((cx-shoulder,head_y+40),(cx-shoulder+8,head_y+29),
                   (cx+shoulder-8,head_y+29),(cx+shoulder,head_y+40),
                   (cx+30,head_y+116),(cx-30,head_y+116))
            canvas.paint_polygon(torso,body,highlight=_mix(body,metal,.24),shadow=_mul(body,.44),
                                 outline=(*metal,210),width=2)
            canvas.polygon(((cx-25,head_y+50),(cx+25,head_y+50),(cx+18,head_y+104),
                            (cx,head_y+119),(cx-18,head_y+104)),
                           (*_mix(robe,body,.3),255),(*accent,180),2)
            for side in (-1,1):
                canvas.polygon(((cx+side*(shoulder-6),head_y+36),
                                (cx+side*(shoulder+13),head_y+47),
                                (cx+side*(shoulder+17),head_y+71),
                                (cx+side*(shoulder-2),head_y+79)),
                               (*_mul(metal,.68),255),(*metal,220),2)
                canvas.ellipse((cx+side*(shoulder-1)-2,head_y+55,
                                cx+side*(shoulder-1)+2,head_y+59),fill=(*accent,235))
        # Cabeça e capuz/capacete são proporcionais à distância de cada integrante.
        radius=17 if index==2 else 14
        canvas.paint_ellipse((cx-radius,head_y,cx+radius,head_y+radius*2),
                             _mix(body,(151,119,94),.38),
                             highlight=_mix(body,(236,215,183),.25),
                             shadow=_mul(body,.55),outline=(*metal,210),width=2)
        if is_robed:
            canvas.polygon(((cx-radius-7,head_y+8),(cx,head_y-12),(cx+radius+7,head_y+8),
                            (cx+radius,head_y+26),(cx-radius,head_y+26)),
                           (*_mul(top,.48),255),(*metal,155),2)
        else:
            canvas.arc((cx-radius-4,head_y-5,cx+radius+4,head_y+radius*2),180,360,(*metal,225),4)
            canvas.line(((cx-radius+2,head_y+radius),(cx+radius-2,head_y+radius)),(9,12,17,245),3)
        # Pernas visíveis abaixo das capas, com botas e joelheiras.
        for side in (-1,1):
            leg_x=cx+side*14
            canvas.line(((leg_x,foot_y-54),(leg_x+side*4,foot_y-13)),(*body,255),12 if index==2 else 9)
            canvas.line(((leg_x-5,foot_y-13),(leg_x+8,foot_y-9)),(*_mul(body,.62),255),6)
            if not is_robed:
                canvas.ellipse((leg_x-6,foot_y-53,leg_x+6,foot_y-41),
                               (*_mul(metal,.7),255),(*metal,200),1)
        # Pequenos detalhes de costura, rebite e dobra para diferenciar os planos.
        for j in range(4):
            y=head_y+73+j*13
            canvas.line(((cx-18+j*2,y),(cx+17-j*2,y+2)),(*metal,65),1)
    if is_guard:
        # Escudos ficam nos flancos: leitura defensiva sem lotar a figura central.
        for cx,cy in ((66,279),(315,279)):
            canvas.polygon(((cx,cy-42),(cx+26,cy-30),(cx+22,cy+20),(cx,cy+44),
                            (cx-22,cy+20),(cx-26,cy-30)),
                           (*_mul(metal,.55),245),(*metal,235),3)
            canvas.polygon(((cx,cy-27),(cx+15,cy-20),(cx+12,cy+14),(cx,cy+29),
                            (cx-12,cy+14),(cx-15,cy-20)),
                           (*_mix(top,accent,.22),235),(*accent,220),2)
    if _contains(title,"estandarte","portaestandarte"):
        canvas.line(((306,102),(306,343)),(*_mul(metal,.65),255),7)
        canvas.polygon(((309,111),(368,126),(353,204),(309,192)),(*accent,225),(*metal,220),2)
    if is_knight and not is_robed:
        # Armas discretas nos flancos para o arquétipo militar, sem transformar
        # sacerdotes ou peregrinos em soldados armados.
        for x, y, side in ((52,275,-1),(329,275,1)):
            canvas.line(((x,y+34),(x+side*19,y-87)),(*_mul(metal,.7),255),5)
            canvas.line(((x+side*19,y-87),(x+side*25,y-104)),(*metal,235),2)



def _draw_winged_celestial(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    """Anjo com asas orgânicas em leques de penas sobrepostas e figura central."""
    top, mid, accent, metal = palette
    _glow(canvas, (192, 174), 145, (231, 216, 174), 76, 1.22)
    for side in (-1, 1):
        # Silhueta ampla e curva; a asa é uma massa anatômica antes das penas.
        wing = ((192+side*34,205),(192+side*42,169),(192+side*67,126),
                (192+side*102,91),(192+side*146,57),(192+side*176,76),
                (192+side*181,104),(192+side*161,152),(192+side*137,195),
                (192+side*102,229),(192+side*64,242))
        canvas.smooth_polygon(wing,(82,82,76,115),None,steps=6)
        # Remiges longas: cada pena tem volume, ponta arredondada e eixo de luz.
        for i in range(15):
            t=i/14
            root_x=192+side*(44+ t*54)
            root_y=208-t*55
            tip_x=192+side*(84+t*91)
            tip_y=105-t*27+math.sin(t*math.pi)*27 + (2 if side < 0 else -3)
            spread=8+(1-t)*6
            feather=((root_x-side*7,root_y+8),(root_x+side*7,root_y-8),
                     (tip_x+side*spread,tip_y+9),(tip_x,tip_y-5),
                     (tip_x-side*spread,tip_y+12),(root_x-side*3,root_y+19))
            tone=_mix((195,188,169),(109,111,108),t*.48)
            canvas.smooth_polygon(feather,(*tone,190),(*_mix(tone,(255,246,220),.35),105),.55,steps=5)
            canvas.smooth_line(((root_x,root_y+5),(tip_x,tip_y+12)),
                               (238,231,210,82),.65,steps=6)
            # Barbas curtas nas penas maiores, indicando estrutura e não pétalas.
            if i%2==0:
                for q in range(3):
                    bx=root_x+(tip_x-root_x)*(q+1)/4
                    by=root_y+(tip_y-root_y)*(q+1)/4
                    canvas.smooth_line(((bx,by),(bx+side*6,by-3)),(238,231,210,58),.55,steps=4)
        # Cobertura secundária na raiz, como pequenas penas de contorno.
        for j in range(6):
            x=192+side*(43+j*8); y=191-j*5
            canvas.smooth_polygon(((x-7,y+9),(x+2,y-5),(x+17,y-16),
                                   (x+13,y+1),(x+2,y+16)),
                                  (181,173,155,175),(240,231,207,88),.5,steps=5)
    # Halo em arco interrompido e inclinado, evitando o aspecto de ícone perfeito.
    canvas.arc((148,30,238,122),190,343,(243,224,170,220),2.5)
    canvas.arc((153,36,232,116),202,335,(255,248,224,95),1)
    base=ArtDirection("cleric or preacher",direction.scene,direction.faction,
                      direction.action,direction.material,direction.canonical,"")
    _draw_humanoid(canvas,base,palette,rng,scale=.97)
    # A luz de recorte acompanha as penas, sem contorno brilhante uniforme.
    for side in (-1,1):
        canvas.smooth_line(((192+side*47,203),(192+side*103,146),(192+side*153,97)),
                           (248,235,206,72),.9,steps=7)


def _draw_giant(canvas: _Painter, card: dict[str, Any], direction: ArtDirection,
                palette, rng: random.Random):
    """Gigante de fogo: massa corporal colossal, peso e focos térmicos, sem proporção humana comum."""
    top, mid, accent, metal = palette
    cx = 192
    _glow(canvas, (194, 240), 170, (232, 91, 37), 92, 1.25)
    # Pernas afastadas e curtas em relação ao tronco para comunicar escala e massa.
    canvas.polygon(((106,279),(166,268),(184,363),(159,420),(91,421),(78,391)),
                   (48,34,31,255),(143,91,67,190),2)
    canvas.polygon(((211,270),(278,272),(311,390),(291,420),(223,417),(199,351)),
                   (48,34,31,255),(143,91,67,190),2)
    for x in (111, 267):
        canvas.polygon(((x-33,390),(x+35,391),(x+52,425),(x-49,425)),
                       (29,23,22,255),(142,105,79,190),2)
    # Tronco amplo com placas naturais de rocha e couro queimado.
    torso=((94,125),(122,91),(167,78),(221,82),(264,111),(297,196),
           (271,295),(218,340),(155,340),(102,287),(77,205))
    canvas.paint_polygon(torso,(53,39,34),highlight=(132,85,59),shadow=(17,18,22),
                         outline=(139,95,70,220),width=2)
    # Ombros e braços longos, com volumes sobrepostos para afastar a aparência de boneco.
    for side in (-1,1):
        sx = cx + side*105
        shoulder = ((cx+side*64,125),(sx,132),(sx+side*24,183),
                    (cx+side*95,245),(cx+side*69,272),(cx+side*42,221))
        canvas.paint_polygon(shoulder,(57,39,33),highlight=(133,77,50),shadow=(18,18,21),
                             outline=(151,94,61,180),width=2)
        canvas.line(((cx+side*87,220),(cx+side*115,291),(cx+side*131,323)),
                    (41,29,27,255),22)
        canvas.line(((cx+side*111,293),(cx+side*140,326)),(119,68,45,240),8)
        # Fissuras incandescentes são finas e localizadas, não um corpo coberto por fogo.
        for j in range(4):
            y = 151 + j*27
            x = cx + side*(74 + rng.randint(-10,15))
            canvas.line(((x,y),(x-side*11,y+11),(x-side*5,y+24)),
                        (232,105+rng.randint(0,45),45,rng.randint(85,165)),2)
    # Peitoral em placas irregulares e cicatrizes de calor.
    for points in (
        ((126,137),(165,116),(187,151),(166,196),(117,186)),
        ((202,119),(248,139),(270,192),(219,202),(192,160)),
        ((122,205),(173,194),(190,254),(150,276),(105,247)),
        ((198,211),(257,207),(274,255),(222,283),(188,252)),
    ):
        canvas.paint_polygon(points,(76,56,43),highlight=(154,103,67),shadow=(28,26,25),
                             outline=(174,117,72,150),width=1)
    # Cabeça pequena em proporção ao tórax; crina e barba de fogo sugerem a natureza ígnea.
    canvas.ellipse((157,55,224,139),(69,46,37,255),(170,111,73,220),2)
    canvas.polygon(((158,93),(143,59),(168,68),(178,34),(196,65),(220,40),
                    (225,92),(211,110),(171,110)),
                   (109,41,27,255),(214,111,56,220),2)
    canvas.ellipse((171,82,181,90),(245,185,91,245))
    canvas.ellipse((201,82,211,90),(245,185,91,245))
    canvas.polygon(((174,110),(192,119),(210,108),(204,132),(190,142),(177,130)),
                   (48,29,25,255),(153,81,52,210),1)
    for i in range(13):
        x = 164 + i*5
        y = rng.randint(111,128)
        canvas.line(((x,y),(x+rng.randint(-10,10),y+32+rng.randint(0,22))),
                    (190,65,31,rng.randint(105,210)),rng.choice((2,3,4)))
    # Pano de cintura pesado, gasto e queimado nas bordas.
    _cloth(canvas,((129,288),(253,287),(278,405),(223,420),(173,414),(111,405)),
           (52,30,28),(190,75,42),rng,edge=(142,70,48,180),folds=12)
    # Cinzas e fagulhas reforçam a diferença de escala frente à paisagem.
    for _ in range(42):
        x = rng.randint(65,322); y = rng.randint(90,400); r = rng.choice((1,2,3))
        canvas.ellipse((x-r,y-r,x+r,y+r),(242,125,52,rng.randint(55,170)))


def _draw_divine_manifestation(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    """Vontade de Marika: presença impessoal dourada, não retrato inventado da rainha."""
    top, mid, accent, metal = palette
    _glow(canvas,(192,220),190,(248,215,132),112,1.2)
    # Núcleo humanoide apenas como escala; sem rosto ou identidade facial afirmada.
    figure=((190,82),(218,105),(228,174),(257,231),(242,352),(218,413),
            (192,394),(166,413),(142,352),(127,231),(156,174),(166,105))
    canvas.paint_polygon(figure,(124,92,48),highlight=(244,207,124),shadow=(30,25,23),
                         outline=(255,226,160,175),width=2)
    canvas.ellipse((165,42,219,106),(173,131,74,210),(255,230,168,215),2)
    # Veios de ouro atravessam a figura como fios de luz, não como raios aleatórios.
    for side in (-1,1):
        for i in range(5):
            x=192+side*(13+i*7)
            canvas.line(((x,112),(x+side*12,181),(x+side*6,250),
                         (x+side*19,323),(x+side*11,397)),
                        (255,222,142,rng.randint(70,155)),rng.choice((1,2,3)))
    for i in range(9):
        angle=math.tau*i/9
        x=192+math.cos(angle)*rng.randint(88,145)
        y=220+math.sin(angle)*rng.randint(115,178)
        canvas.line(((192,215),(x,y)),(245,212,137,rng.randint(26,75)),1)
    canvas.arc((78,55,306,386),208,336,(255,233,171,150),2)


def _draw_oathbound_champion(canvas: _Painter, card: dict[str, Any], direction: ArtDirection,
                             palette, rng: random.Random):
    """Avatar singular do Crisol: cavaleiro solitário cercado por raízes petrificadas."""
    base = ArtDirection("armored knight", direction.scene, direction.faction,
                        direction.action, direction.material, direction.canonical, direction.equipment)
    _draw_humanoid(canvas, base, palette, rng, scale=1.04)
    top, mid, accent, metal = palette
    _glow(canvas,(192,251),125,(170,52,58),48,.9)
    for side in (-1,1):
        for i in range(3):
            canvas.line(((192+side*8,402),(192+side*(37+i*10),351-i*17),
                         (192+side*(74+i*14),301-i*20),(192+side*(84+i*16),231-i*12)),
                        (101,83,58,190-i*25),rng.choice((4,6,8)))
            canvas.line(((192+side*8,402),(192+side*(37+i*10),351-i*17),
                         (192+side*(74+i*14),301-i*20)),(194,160,112,95),1)
    canvas.arc((116,146,268,324),198,342,(206,156,103,150),3)


def _draw_dragonbound_warrior(canvas: _Painter, direction: ArtDirection, palette, rng: random.Random):
    """Guerreiro dracônico: armadura humana, escamas como material e relâmpago canalizado."""
    top, mid, accent, metal = palette
    armored = ArtDirection("ancient dragon warrior", direction.scene, direction.faction,
                           direction.action, direction.material, direction.canonical, "")
    # Reutiliza anatomia de cavaleiro, mas não adiciona espada ou cajado ausente da lore.
    _draw_humanoid(canvas, armored, palette, rng, scale=1.02)
    # Ombreiras em placas sobrepostas, com borda escamada em vez de penas/chifres genéricos.
    for side in (-1, 1):
        shoulder_x = 190 + side * 61
        for row in range(3):
            y = 185 + row * 13
            for col in range(3):
                x = shoulder_x + side * (col * 7 - 6)
                canvas.polygon(((x-8,y-5),(x+2,y-9),(x+10,y+1),(x+3,y+10),(x-7,y+5)),
                               (*_mix(metal,(36,49,60),.34+row*.06),235),
                               (*_mix(metal,(220,205,170),.18),170),1)
        canvas.line(((shoulder_x-side*13,168),(shoulder_x,147),(shoulder_x+side*17,164)),
                    (*_mix(metal,(231,220,187),.25),220),3)
    # Fendas luminosas no peitoral sugerem energia dracônica contida na armadura.
    for path in (
        ((177,211),(184,228),(174,244),(185,261)),
        ((205,208),(198,224),(210,240),(201,259)),
    ):
        canvas.smooth_line(path,(190,220,250,180),2,steps=8)
        canvas.smooth_line(path,(238,244,255,235),.9,steps=8)
    # Descargas saem das mãos e atravessam o ar em ramificações curtas, sem virar esfera mágica.
    for hand in ((105,253),(278,234)):
        _glow(canvas,hand,52,(153,194,255),85,.8)
        for branch in range(4):
            side = -1 if hand[0] < 190 else 1
            start_x = hand[0] + side * rng.randint(3,14)
            start_y = hand[1] + rng.randint(-9,9)
            end_x = start_x + side * rng.randint(32,70)
            end_y = start_y + rng.randint(-48,42)
            bend_x = (start_x+end_x)/2 + rng.randint(-14,14)
            bend_y = (start_y+end_y)/2 + rng.randint(-20,20)
            points=((start_x,start_y),(bend_x,bend_y),(end_x,end_y))
            canvas.smooth_line(points,(123,174,255,165),3,steps=6)
            canvas.smooth_line(points,(225,239,255,245),1,steps=6)
            if branch % 2 == 0:
                canvas.line(((bend_x,bend_y),(bend_x+side*12,bend_y-17)),(190,216,255,185),1)
    # Pequenas escamas gravadas na gola e nos antebraços completam o material.
    for y in (159,169,179):
        for x in range(173,211,9):
            canvas.arc((x-5,y-4,x+5,y+6),205,335,(*_mix(metal,(238,229,203),.3),145),1)


def _draw_beast(canvas: _Painter, card: dict[str, Any], direction: ArtDirection, palette, rng: random.Random):
    top, mid, accent, metal = palette
    ident = _norm(" ".join((str(card.get("nome", "")), str(card.get("descricao", "")))))
    cx = 192
    if direction.canonical == "elden beast" or _contains(ident, "besta pristina", "elden beast"):
        # Entidade astral serpentina: corpo sinuoso, crista luminosa e nadadeiras
        # orgânicas. A silhueta não reutiliza o molde quadrúpede de lobo/cavalo.
        _glow(canvas, (198, 214), 178, (236, 203, 125), 110, 1.25)
        _glow(canvas, (282, 112), 92, (181, 208, 242), 70, 1.0)
        canvas.polygon(((55,357),(98,295),(171,264),(224,203),(257,138),(302,104),
                        (286,170),(250,239),(205,297),(138,337),(79,383)),
                       (34,49,67,235),(211,197,151,220),4)
        body_path=((57,358),(111,319),(165,286),(214,238),(250,184),(284,130))
        canvas.line(body_path,(31,43,59,255),47)
        canvas.line(body_path,(176,183,178,255),32)
        canvas.line(body_path,(240,224,177,235),12)
        for i,(x,y) in enumerate(((107,323),(150,294),(192,258),(226,218),(252,178))):
            side=-1 if i%2==0 else 1
            canvas.polygon(((x,y),(x+side*42,y-47),(x+side*22,y+15),(x+4,y+17)),
                           (92,119,125,180),(225,214,175,190),2)
            canvas.line(((x,y),(x+side*33,y-40)),(250,231,190,150),2)
        # Cabeça alongada, sem chifres humanos, olhos e mandíbula de criatura dracônica.
        canvas.polygon(((258,137),(286,94),(332,84),(356,112),(342,151),(307,164)),
                       (89,107,111,255),(224,213,178,235),3)
        canvas.polygon(((322,130),(365,143),(348,164),(306,157)),
                       (39,52,62,255),(197,185,154,210),2)
        canvas.ellipse((322,110,331,119),fill=(244,211,123,255))
        canvas.line(((290,98),(286,60),(313,90)),(205,188,146,245),5)
        canvas.line(((304,95),(324,58),(326,98)),(205,188,146,245),5)
        # Cauda e filamentos de luz dão escala à silhueta primordial.
        canvas.line(((64,357),(35,390),(19,387)),(96,116,121,245),15)
        for _ in range(48):
            x,y=rng.randint(42,350),rng.randint(75,385)
            canvas.ellipse((x-1,y-1,x+2,y+2),(246,224,164,rng.randint(60,185)))
        return
    cx = 192
    body = _mix((18, 22, 27), top, .28)
    # Muscular torso, neck, hindquarters and four grounded limbs.
    _glow(canvas, (cx, 302), 115, accent, 38, .7)
    canvas.ellipse((cx-94, 238, cx+82, 344), fill=(*body,255), outline=(*metal,205), width=4)
    canvas.ellipse((cx-86, 255, cx+32, 326), fill=(*_mul(body,.77),255))
    for x, joint in ((cx-65,cx-77),(cx-22,cx-29),(cx+45,cx+50),(cx+72,cx+80)):
        knee = 365 + rng.randint(-8, 8)
        canvas.line(((x,315),(joint,knee),(joint+5,404)), (*body,255), 22)
        canvas.line(((joint-8,401),(joint+18,408)), (*_mul(body,.65),255), 8)
        canvas.line(((x,317),(joint,knee)), (*metal,55), 2)
    # Neck/head directed toward action, with muzzle and readable eye.
    canvas.polygon(((cx+33, 271),(cx+72, 196),(cx+119, 202),(cx+142, 250),
                    (cx+114, 294),(cx+62, 311)), (*_mul(body,1.18),255), (*metal,215), 3)
    canvas.ellipse((cx+99, 194, cx+164, 258), fill=(*_mul(body,1.28),255), outline=(*metal,210), width=3)
    canvas.polygon(((cx+142, 227),(cx+189, 245),(cx+150, 271),(cx+119, 257)),
                   (*_mul(body,.84),255), (*metal,180), 2)
    canvas.ellipse((cx+133, 217, cx+139, 223), fill=(*accent,255))
    # Horns, antlers or ears selected by title.
    ident = _norm(" ".join((str(card.get("nome", "")), str(card.get("descricao", "")),
                            direction.subject, direction.action, direction.material)))
    if direction.subject == "creature":
        # Chifres, galhadas, asas e cauda são desenhados somente quando o texto os sustenta.
        if _contains(ident, "horn", "chifre", "antler", "cervo", "galhada"):
            for side in (-1, 1):
                sx = cx+132+side*7
                canvas.line(((sx,216),(sx+side*22,171),(sx+side*18,146)), (*_mix(metal,(235,222,194),.24),255), 7)
                for branch in range(2):
                    yy = 183-branch*18
                    canvas.line(((sx+side*13,yy),(sx+side*28,yy-13)), (*metal,235), 4)
        else:
            canvas.polygon(((cx+112,207),(cx+115,173),(cx+138,198)), (*body,255), (*metal,185), 2)
            canvas.polygon(((cx+151,205),(cx+166,176),(cx+166,216)), (*body,255), (*metal,185), 2)
    if direction.canonical == "placidusax":
        # Duas asas membranosas e duas cabeças: leitura imediata do lorde dragão antigo.
        canvas.polygon(((cx-27,263),(cx-96,158),(cx-174,93),(cx-149,231),(cx-103,292),(cx-51,319)),
                       (34,43,52,248),(184,193,198,210),4)
        canvas.polygon(((cx+9,260),(cx+93,153),(cx+174,100),(cx+144,238),(cx+98,299),(cx+48,317)),
                       (34,43,52,248),(184,193,198,210),4)
        for i in range(6):
            canvas.line(((cx-100+i*10,282),(cx-158+i*8,125+i*19)),(186,198,205,145),2)
            canvas.line(((cx+100-i*10,282),(cx+157-i*8,130+i*18)),(186,198,205,145),2)
        # Two necks split from the armored chest and terminate in distinct heads.
        canvas.line(((cx-9,244),(cx-58,184),(cx-108,169)),(*_mul(body,1.2),255),27)
        canvas.line(((cx+18,241),(cx+71,174),(cx+117,166)),(*_mul(body,1.2),255),27)
        for hx, hy, direction_sign in ((cx-126,165,-1),(cx+132,161,1)):
            canvas.ellipse((hx-31,hy-23,hx+32,hy+25),fill=(*_mul(body,1.28),255),outline=(*metal,225),width=3)
            canvas.polygon(((hx+direction_sign*17,hy+4),(hx+direction_sign*58,hy+17),
                            (hx+direction_sign*31,hy+30),(hx-6,hy+22)),
                           (*_mul(body,.78),255),(*metal,190),2)
            canvas.ellipse((hx+direction_sign*8-3,hy-8,hx+direction_sign*8+3,hy-2),fill=(*accent,255))
            canvas.line(((hx-10,hy-17),(hx-22,hy-46),(hx-1,hy-23)),(*_mix(metal,(238,220,183),.32),255),5)
            canvas.line(((hx+12,hy-17),(hx+28,hy-41),(hx+27,hy-14)),(*_mix(metal,(238,220,183),.32),255),5)
        canvas.line(((cx-71,331),(cx-130,377),(cx-167,387)),(*_mul(body,.9),255),17)
        _glow(canvas,(cx,231),110,(143,173,211),53,.9)
    # Scale/fur texture highlights follow body volume, avoiding even stipple.
    for i in range(19):
        x = rng.randint(cx-74, cx+76)
        y = rng.randint(257, 324)
        canvas.line(((x,y),(x+rng.randint(4,11),y-rng.randint(2,6))), (*_mix(body,metal,.48),rng.randint(55,120)), 1)
    # Claws and muzzle highlights.
    for x in (cx-74, cx-27, cx+53, cx+82):
        canvas.line(((x,400),(x+8,410)), (194,183,163,220), 3)


def _draw_relic(canvas: _Painter, card: dict[str, Any], palette, rng: random.Random, direction: ArtDirection):
    top, mid, accent, metal = palette
    ident = _norm(" ".join((str(card.get("nome", "")), str(card.get("descricao", "")))))
    cx, cy = 192, 225
    _glow(canvas, (cx, cy), 125, accent, 95, 1.0)
    if _contains(ident, "lagrima sagrada", "holy tear"):
        # Uma gota translúcida física: refração, núcleo luminoso e aro de condensação.
        canvas.ellipse((130,122,254,326),(105,156,171,65),(214,237,238,180),3)
        canvas.polygon(((192,78),(248,185),(253,226),(234,276),(192,312),
                        (150,276),(131,226),(136,185)),
                       (127,183,189,155),(238,248,237,245),5)
        canvas.polygon(((192,92),(227,182),(229,225),(210,267),(192,286),
                        (174,261),(156,222),(162,181)),
                       (202,233,215,130),(255,255,246,220),2)
        canvas.polygon(((174,170),(190,116),(201,151),(191,219)),
                       (246,255,239,130),(255,255,255,160),1)
        canvas.ellipse((175,205,209,239),(231,213,145,155),(255,244,194,230),2)
        _glow(canvas,(192,222),78,(186,231,219),105,.9)
        for i in range(5):
            x=145+i*23
            canvas.arc((x-12,175+i*7,x+18,218+i*7),195,330,(239,251,245,115),2)
    elif _contains(ident, "espada da noite e da chama", "night and flame"):
        # Lâmina reta bipartida: a metade lunar fria contrasta com a metade ígnea.
        canvas.polygon(((192,49),(211,157),(203,270),(192,350),(181,270),(173,157)),
                       (103,151,187,255),(232,235,224,255),4)
        canvas.polygon(((192,55),(201,158),(194,263),(192,342),(184,260),(184,158)),
                       (226,237,226,255),(255,255,244,235),2)
        canvas.polygon(((192,59),(211,157),(203,270),(192,350),(192,210)),
                       (197,91,51,190),(255,185,97,190),1)
        canvas.line(((192,64),(192,290)),(255,249,223,235),3)
        canvas.line(((147,259),(237,259)),(*_mix(metal,(245,223,174),.3),255),10)
        canvas.line(((151,253),(233,253)),(255,239,190,230),2)
        canvas.rect((183,267,201,333),fill=(75,48,35,255),outline=(*metal,255),width=3)
        canvas.ellipse((182,330,202,350),fill=(*accent,255),outline=(*metal,255),width=2)
        _glow(canvas,(164,188),84,(116,190,239),90,.75)
        _glow(canvas,(220,188),84,(248,117,53),95,.75)
        for i in range(7):
            y=122+i*24
            canvas.line(((205,y),(216+i%3*3,y-9)),(255,157,73,150),2)
    elif _contains(ident, "lamina da morte destinada", "destined death blade", "lamina negra"):
        # Aço negro, canal de energia púrpura e runas da Morte Destinada.
        canvas.polygon(((192,49),(214,157),(205,275),(192,355),(179,275),(170,157)),
                       (28,27,38,255),(151,138,167,245),4)
        canvas.polygon(((192,64),(202,163),(197,271),(192,334),(186,270),(181,160)),
                       (70,54,84,255),(197,167,204,235),2)
        canvas.line(((191,75),(192,307)),(180,119,211,245),4)
        canvas.line(((150,260),(234,260)),(48,43,58,255),10)
        canvas.line(((154,255),(230,255)),(189,155,220,230),2)
        canvas.rect((184,268,200,337),fill=(39,29,39,255),outline=(*metal,230),width=3)
        for y in (118,169,220,294):
            canvas.polygon(((192,y-8),(198,y),(192,y+8),(186,y)),(177,111,207,175),(220,196,240,180),1)
        _glow(canvas,(192,202),100,(119,76,176),105,1.0)
    elif _contains(ident, "coroa", "crown"):
        canvas.polygon(((98,260),(110,145),(151,188),(192,100),(234,188),(276,145),(286,260)),
                       (*_mul(metal,.55),255), (*_mix(metal,(255,246,217),.5),255), 4)
        canvas.polygon(((111,250),(273,250),(268,275),(116,275)), (51,35,28,255), (*accent,230), 3)
        for x in (117,151,192,234,268):
            canvas.ellipse((x-5,181 if x not in (192,) else 98,x+5,191 if x not in (192,) else 108), fill=(*accent,255))
    elif _contains(ident, "anel", "ring"):
        canvas.ellipse((102,148,282,315), fill=(0,0,0,0), outline=(*_mul(metal,.7),255), width=25)
        canvas.arc((105,150,279,310), 190, 346, fill=(255,255,255,225), width=7)
        canvas.polygon(((179,130),(192,92),(212,130),(192,151)), (*accent,230), (*metal,255), 3)
    elif _contains(ident, "livro", "tomo", "book", "pergaminho", "scroll"):
        canvas.polygon(((92,142),(188,164),(192,326),(94,302)), (62,42,29,255), (*metal,230), 4)
        canvas.polygon(((196,164),(292,140),(290,303),(194,326)), (92,62,38,255), (*metal,230), 4)
        for y in range(184,292,21):
            canvas.line(((108,y),(178,y+18)), (217,191,148,145), 2)
            canvas.line(((208,y+15),(276,y)), (217,191,148,145), 2)
        canvas.line(((190,165),(190,326)), (*accent,220), 4)
    elif _contains(ident, "estandarte", "bandeira", "banner"):
        canvas.line(((192,75),(192,380)), (*_mul(metal,.58),255), 9)
        canvas.polygon(((196,92),(304,123),(274,222),(196,204)), (*accent,210), (*metal,255), 3)
        canvas.ellipse((221,134,272,185), fill=(*_mul(top,.5),220), outline=(*metal,240), width=3)
    elif _contains(ident, "runa", "rune"):
        canvas.ellipse((89,112,295,324), fill=(23,24,29,245), outline=(*metal,255), width=8)
        canvas.ellipse((105,128,279,308), fill=(*_mix(top,(8,12,20),.58),245), outline=(*accent,220), width=3)
        points=[]
        for i in range(12):
            ang=math.radians(-90+i*30)
            radius=78 if i%2==0 else 49
            points.append((cx+math.cos(ang)*radius,cy+math.sin(ang)*radius))
        canvas.polygon(points, (*accent,70), (*metal,230), 3)
        canvas.ellipse((cx-23,cy-23,cx+23,cy+23),fill=(*accent,220),outline=(255,245,215,240),width=3)
        for ang in range(0,360,45):
            rad=math.radians(ang)
            canvas.line(((cx+math.cos(rad)*32,cy+math.sin(rad)*32),
                         (cx+math.cos(rad)*63,cy+math.sin(rad)*63)),(*metal,190),2)
    elif _contains(ident, "algemas", "correntes", "chain", "shackles"):
        canvas.ellipse((104,157,171,244),fill=(0,0,0,0),outline=(*_mul(metal,.78),255),width=17)
        canvas.ellipse((211,205,278,292),fill=(0,0,0,0),outline=(*_mul(metal,.78),255),width=17)
        for i in range(7):
            x=155+i*12; y=188+i*8
            canvas.ellipse((x-8,y-13,x+8,y+13),fill=(0,0,0,0),outline=(*metal,245),width=5)
            canvas.line(((x-4,y-8),(x+3,y-9)),(255,255,255,135),2)
        canvas.line(((129,246),(129,309),(254,309),(254,289)),(50,52,55,255),8)
        canvas.polygon(((192,306),(218,326),(192,359),(166,326)),(*accent,125),(*metal,230),3)
    elif _contains(ident, "lagrima sagrada", "tear", "lacrima"):
        canvas.polygon(((192,86),(247,176),(253,225),(236,270),(192,298),(148,270),(131,225),(137,176)),
                       (130,183,190,120),(229,240,229,245),5)
        canvas.polygon(((192,97),(231,179),(234,223),(215,260),(192,278)),
                       (224,245,221,150),(255,255,247,230),2)
        canvas.line(((165,185),(186,127),(199,118)),(255,255,255,210),5)
        _glow(canvas,(192,208),100,(194,230,215),95)
    elif _contains(ident, "escudo", "shield"):
        canvas.polygon(((192,88),(288,128),(272,270),(192,352),(112,270),(96,128)),
                       (*_mul(metal,.52),255), (*metal,255), 5)
        canvas.polygon(((192,115),(262,145),(250,255),(192,316),(134,255),(122,145)),
                       (*_mix(top,accent,.20),255), (*accent,255), 3)
        canvas.polygon(((192,150),(218,210),(192,270),(166,210)), (*metal,230), (*accent,230), 2)
    else:
        # Named blade, axe, spear or staff: make the silhouette legible at thumbnail size.
        if _contains(ident, "machado", "axe", "martelo", "hammer"):
            canvas.line(((192,100),(192,363)), (*_mix(metal,(72,44,29),.45),255), 13)
            canvas.polygon(((188,125),(115,112),(93,174),(169,222),(192,202)), (*_mul(metal,.68),255), (*metal,255), 4)
            canvas.line(((113,128),(165,190)), (255,255,255,145), 3)
        elif _contains(ident, "arco", "bow"):
            canvas.arc((82,98,300,355), 270, 90, fill=(*_mul(metal,.72),255), width=15)
            canvas.line(((192,104),(192,351)), (*accent,180), 2)
            canvas.line(((192,104),(192,351)), (*metal,200), 1)
        else:
            canvas.polygon(((192,62),(211,170),(201,286),(192,355),(183,286),(173,170)),
                           (*_mul(metal,.7),255), (*metal,255), 4)
            canvas.line(((192,74),(192,290)), (255,255,255,175), 3)
            canvas.line(((142,265),(242,265)), (*accent,255), 9)
            canvas.rect((181,270,203,332), fill=(78,48,32,255), outline=(*metal,255), width=3)
        # Inscription et rebites sur o objeto, como acabamento de forja.
        for y in (155,210,265,320):
            canvas.ellipse((187,y-3,193,y+3), fill=(255,241,205,210))
    # Small altar or reliquary pedestal anchors the object in a physical place.
    canvas.polygon(((110,366),(274,366),(300,407),(84,407)), (18,21,27,245), (*metal,180), 2)
    canvas.line(((100,375),(285,375)), (*accent,200), 2)


def _draw_limb(canvas: _Painter, points, widths, base, highlight, *, opacity=255, outline=None):
    """Membro orgânico afunilado com planos de volume, em vez de linhas cilíndricas."""
    pts=[(float(x),float(y)) for x,y in points]
    left=[]; right=[]
    for i,(x,y) in enumerate(pts):
        before=pts[max(0,i-1)]; after=pts[min(len(pts)-1,i+1)]
        dx,dy=after[0]-before[0],after[1]-before[1]
        length=max(1.0,math.hypot(dx,dy))
        nx,ny=-dy/length,dx/length
        width=widths[min(i,len(widths)-1)]
        left.append((x+nx*width/2,y+ny*width/2))
        right.append((x-nx*width/2,y-ny*width/2))
    poly=left+list(reversed(right))
    fill=(*base,opacity)
    canvas.smooth_polygon(poly,fill,outline or (*_mul(base,.66),min(190,opacity)),.8,steps=6)
    canvas.smooth_line(left,(*highlight,min(185,opacity)),max(.8,widths[0]*.12),steps=6)
    if len(pts)>2:
        canvas.smooth_line(right,(*_mul(base,.62),min(125,opacity)),.8,steps=6)


def _draw_ranni(canvas: _Painter, palette, rng: random.Random):
    """Ranni: boneca lunar azul, quatro braços, cabelo ruivo e chapéu de bruxa amplo."""
    top, mid, accent, metal = palette
    _glow(canvas,(192,171),145,(94,143,218),78,1.25)
    # Silhueta de tecido assimétrica, com cauda deslocada pelo vento lunar.
    robe=((143,160),(160,151),(187,154),(220,148),(242,164),(255,223),
          (277,326),(305,411),(263,423),(221,414),(192,430),(158,420),
          (116,427),(91,411),(118,323),(127,238),(119,191))
    _cloth(canvas,robe,(24,37,67),accent,rng,edge=(104,128,174,150),folds=20)
    inner=((165,169),(190,166),(218,164),(235,177),(243,273),(252,409),
           (218,422),(190,413),(161,420),(145,407),(155,276))
    _cloth(canvas,inner,(67,91,133),metal,rng,edge=(178,195,223,150),folds=13)
    # Painel central de seda clara, com pregas interrompidas e bordado lunar.
    canvas.smooth_polygon(((181,172),(203,169),(212,247),(219,404),(194,423),
                           (170,406),(176,267)),(164,190,218,190),(225,235,244,165),1)
    for side in (-1,1):
        canvas.smooth_line(((192+side*14,204),(192+side*20,263),
                            (192+side*32,335),(192+side*39,409)),(191,207,231,130),1.7)
        canvas.smooth_line(((192+side*7,228),(192+side*12,302),
                            (192+side*20,382)),(16,27,49,150),2.2)
    # Faixa de cintura e fecho em prata lunar.
    canvas.smooth_line(((157,250),(178,257),(204,255),(229,247)),(17,25,43,245),8)
    canvas.smooth_line(((160,248),(181,253),(205,251),(229,245)),(164,180,207,205),1.6)
    canvas.ellipse((185,243,201,260),(75,99,143,255),(215,225,239,220),1.5)
    canvas.arc((187,245,199,257),205,340,(237,240,246,220),1)

    # Quatro braços em planos distintos: dois carnais e dois espectrais.
    arm_sets=[
        ([(151,181),(120,199),(108,158)],[20,15,10],(75,106,157),(185,207,235),238),
        ([(228,180),(259,194),(282,145)],[20,15,10],(78,107,159),(195,214,238),238),
        ([(158,218),(126,258),(111,303)],[16,12,8],(65,115,180),(190,222,250),164),
        ([(224,218),(260,253),(286,287)],[16,12,8],(65,115,180),(190,222,250),164),
    ]
    for points,widths,base,highlight,opacity in arm_sets:
        _draw_limb(canvas,points,widths,base,highlight,opacity=opacity,outline=(*_mix(base,highlight,.3),min(155,opacity)))
        hx,hy=points[-1]
        canvas.paint_ellipse((hx-7,hy-8,hx+7,hy+8),_mix(base,(207,225,245),.36),
                             highlight=_mix(highlight,(255,255,255),.12),
                             shadow=_mul(base,.55),outline=(*highlight,min(185,opacity)),width=1,opacity=opacity)
        # Dedos discretos com articulação, sem aparência de garras ou luvas metálicas.
        for finger in (-1,0,1):
            end=(hx+finger*5+2,hy+13+abs(finger)*2)
            canvas.smooth_line(((hx+finger*3,hy+4),end),(*highlight,min(180,opacity)),1.15,steps=5)

    # Cabeça em porcelana azul: oval com mandíbula, maçãs e luz lateral.
    canvas.smooth_polygon(((169,111),(176,98),(191,94),(207,101),(216,119),
                           (212,149),(199,166),(185,165),(171,151),(166,130)),
                          (129,169,216,255),(213,231,246,230),1.2)
    canvas.paint_ellipse((169,105,214,162),(132,176,220),highlight=(202,224,242),
                         shadow=(65,91,140),outline=(186,211,235,180),width=1)
    # Sombra sob a franja e planos da face.
    canvas.smooth_polygon(((169,119),(179,111),(196,112),(213,121),
                           (209,135),(196,128),(181,131),(169,138)),
                          (42,62,99,105),None)
    # Olhos amendoados, íris, reflexos, ponte nasal e boca.
    for x in (180,202):
        canvas.smooth_polygon(((x-6,130),(x-2,126),(x+4,128),(x+6,132),
                               (x+1,135),(x-4,134)),(20,28,48,245),None)
        canvas.ellipse((x-1.6,128,x+2.1,133),(8,13,25,255))
        canvas.ellipse((x+.2,128.4,x+1.6,129.8),(239,244,250,240))
        canvas.smooth_line(((x-6,125),(x,123),(x+6,125)),(43,54,78,210),1)
    canvas.smooth_line(((192,132),(189,144),(194,147)),(75,102,146,205),1)
    canvas.smooth_line(((185,154),(192,157),(200,153)),(91,61,78,215),1.2)
    canvas.paint_ellipse((171,140,180,149),(166,196,229,90),opacity=95)
    canvas.paint_ellipse((204,140,212,149),(166,196,229,70),opacity=75)

    # Cabelos ruivos em mechas curvas, com sombra de raiz e reflexos finos.
    hair=(139,43,53); hair_light=(213,103,91)
    locks=[
        ((169,111),(157,131),(155,169),(146,220),(153,258),(166,231),(170,179),(178,133)),
        ((176,104),(167,126),(167,164),(159,205),(166,244),(179,208),(181,155),(188,119)),
        ((213,111),(226,135),(228,173),(238,215),(230,258),(218,227),(217,177),(205,132)),
        ((207,105),(220,127),(220,163),(229,201),(223,237),(211,206),(207,158),(197,119)),
    ]
    for idx,lock in enumerate(locks):
        canvas.smooth_polygon(lock,(*_mul(hair,1.0 if idx%2==0 else .84),255),(*_mul(hair,.65),180),.8)
        canvas.smooth_line((lock[0],lock[2],lock[4],lock[5]),(*hair_light,155 if idx%2==0 else 115),1.5)
        for j in range(2):
            canvas.smooth_line(((lock[1][0]+j*2,lock[1][1]),
                                (lock[2][0]+j*2,lock[2][1]),
                                (lock[3][0]+j*2,lock[3][1])),(*_mix(hair,hair_light,.55),85),.8)

    # Chapéu lunar de tecido gasto: copa dobrada e aba larga com espessura.
    hat=((147,111),(147,77),(164,47),(189,12),(204,27),(227,55),(237,100),
         (219,96),(201,83),(177,92),(162,106))
    canvas.smooth_polygon(hat,(20,32,58,255),(120,147,191,225),1.6)
    canvas.smooth_line(((157,84),(176,45),(193,18),(207,48),(223,79)),(100,125,174,195),2)
    # A aba tem curvatura e sombra inferior; o rosto continua livre.
    canvas.paint_ellipse((101,94,281,126),(22,34,58),highlight=(52,68,102),
                         shadow=(8,14,27),outline=(152,177,218,230),width=1.5)
    canvas.arc((108,91,275,126),190,346,(196,213,239,190),2)
    canvas.smooth_line(((118,110),(158,105),(194,108),(235,104),(271,111)),
                       (7,13,26,210),2)
    canvas.ellipse((185,55,202,73),(112,147,207,235),(225,236,248,235),1.5)
    canvas.ellipse((189,59,195,65),(218,230,244,240))
    # Bordado e pequenas marcas de uso no tecido do chapéu.
    for i in range(8):
        x=160+i*9; y=76-abs(4-i)*2
        canvas.smooth_line(((x,y),(x+3,y-5),(x+7,y-3)),(150,171,209,90),.8)
    # Arco lunar atrás da figura, interrompido por nuvens e pela silhueta.
    canvas.arc((87,70,300,299),206,336,(171,199,241,90),2)


def _draw_canonical_character(canvas: _Painter, card: dict[str, Any], direction: ArtDirection,
                              palette, rng: random.Random):
    """Silhuetas autorais para identidades recorrentes presentes no catálogo."""
    top, mid, accent, metal = palette
    if direction.canonical == "ranni":
        _draw_ranni(canvas, palette, rng)
        return
    archetypes = {
        "ranni": "arcane or ritual figure",
        "fia": "arcane or ritual figure",
        "marika": "noble or commander",
        "godwyn": "noble or commander",
        "malenia": "agile scout or duelist",
        "radahn": "mounted rider",
        "godfrey": "noble or commander",
        "maliketh": "lore-specific humanoid",
        "messmer": "noble or commander",
        "blaidd": "agile scout or duelist",
        "gurranq": "arcane or ritual figure",
        "black knife assassin": "agile scout or duelist",
        "elden beast": "creature",
    }
    archetype = archetypes.get(direction.canonical, "lore-specific humanoid")
    base_direction = ArtDirection(archetype, direction.scene, direction.faction,
                                  direction.action, direction.material, direction.canonical, direction.equipment)
    _draw_humanoid(canvas, base_direction, palette, rng)
    cx = 190
    if direction.canonical == "ranni":
        # Four arms, blue skin, red hair and the oversized lunar witch hat define the silhouette.
        _glow(canvas, (192, 146), 108, (100, 157, 229), 70, 1.35)
        canvas.ellipse((173, 108, 207, 146), fill=(133, 174, 213, 255), outline=(198, 219, 239, 225), width=2)
        canvas.polygon(((158,116),(145,42),(190,8),(237,42),(222,116),(206,93),(176,95)),
                       (24,39,74,255),(151,173,215,235),3)
        canvas.polygon(((105,112),(274,112),(255,130),(128,132)),
                       (19,29,55,255),(153,176,221,235),3)
        for x, y in ((156,137),(221,139)):
            canvas.line(((x, y),(x-9,205),(x-18,253)),(143,49,61,255),8)
            canvas.line(((x+6,y+4),(x+14,195),(x+24,241)),(174,57,69,255),5)
        # Lower pair of spectral arms, deliberately separated from the ordinary pair.
        for side in (-1,1):
            start=(cx+side*46,195)
            elbow=(cx+side*89,219)
            hand=(cx+side*112,181)
            canvas.line((start,elbow,hand),(130,167,208,245),10)
            canvas.ellipse((hand[0]-7,hand[1]-7,hand[0]+7,hand[1]+7),fill=(157,193,225,255),outline=(227,236,245,230),width=2)
        canvas.arc((128,62,257,192),190,340,(182,206,245,100),2)
        for _ in range(24):
            x,y=rng.randint(80,304),rng.randint(65,295)
            canvas.ellipse((x-1,y-1,x+1,y+1),(195,219,255,rng.randint(75,180)))
    elif direction.canonical == "malenia":
        # Copper hair, winged gold helm, prosthetic arm and rot petals.
        canvas.ellipse((170,106,211,151),(196,139,112,255),(232,194,145,230),2)
        canvas.line(((177,126),(186,124)),(48,30,26,255),2)
        canvas.line(((197,124),(207,126)),(48,30,26,255),2)
        canvas.polygon(((157,180),(225,180),(242,242),(192,269),(141,242)),
                       (130,94,48,255),(239,205,130,240),3)
        canvas.polygon(((164,190),(216,190),(223,232),(192,251),(156,232)),
                       (207,161,92,255),(255,230,165,240),2)
        canvas.polygon(((164,117),(154,67),(178,76),(192,46),(207,76),(230,64),(216,121)),
                       (180,132,72,255),(246,218,145,255),3)
        canvas.line(((162,89),(131,63),(143,115)),(215,167,103,245),5)
        canvas.line(((220,88),(251,59),(238,118)),(215,167,103,245),5)
        for side in (-1,1):
            for i in range(4):
                canvas.line(((cx+side*18,118+i*4),(cx+side*(38+i*4),178+i*12)),(158,44,52,245),5-i*.5)
        canvas.line(((249,177),(287,220),(301,269)),(203,169,106,255),10)
        canvas.line(((248,177),(287,220),(301,269)),(255,230,168,230),2)
        canvas.polygon(((299,269),(311,269),(321,281),(305,288)),(186,153,94,255),(244,211,150,255),2)
        for _ in range(28):
            x,y=rng.randint(80,305),rng.randint(190,380)
            angle=rng.random()*math.tau
            r=rng.randint(3,7)
            canvas.ellipse((x-r,y-r*.45,x+r,y+r*.45),(154,35,45,rng.randint(65,150)))
    elif direction.canonical == "radahn":
        # The general's red leonine mane and gravity weapons; small mount remains visible below.
        canvas.ellipse((145,83,235,147),fill=(94,31,25,155),outline=(180,75,53,150),width=2)
        for i in range(15):
            side = -1 if i%2==0 else 1
            x = 190 + side*rng.randint(15,42)
            y = rng.randint(91,134)
            canvas.line(((x,y),(x+side*rng.randint(15,35),y+rng.randint(18,62))),
                        (174,54,43,235),rng.randint(3,6))
        canvas.ellipse((172,105,210,149),(151,105,82,255),(215,165,122,230),2)
        canvas.line(((178,125),(188,123)),(29,22,20,255),2)
        canvas.line(((195,123),(205,125)),(29,22,20,255),2)
        # Lion pelt collar and embossed lion face on the chest.
        canvas.arc((118,140,263,250),185,355,(178,93,57,235),15)
        canvas.arc((125,151,256,241),185,355,(238,174,108,190),4)
        canvas.ellipse((177,188,205,218),(99,44,31,230),(219,155,94,230),2)
        canvas.polygon(((181,196),(170,185),(178,209),(192,216),(206,209),(214,185),(202,196)),
                       (180,108,62,225),(244,191,126,205),2)
        canvas.line(((270,260),(320,89)),(177,188,204,255),10)
        canvas.polygon(((309,83),(322,46),(334,88),(325,109)),(178,188,202,255),(240,230,207,255),2)
        canvas.line(((112,252),(54,107)),(177,188,204,255),10)
        canvas.polygon(((45,95),(55,59),(69,100),(57,122)),(178,188,202,255),(240,230,207,255),2)
        _glow(canvas,(191,214),100,(143,101,221),70,1.0)
        for _ in range(28):
            x,y=rng.randint(72,310),rng.randint(80,350)
            canvas.ellipse((x-2,y-2,x+2,y+2),(176,151,237,rng.randint(100,220)))
    elif direction.canonical == "godfrey":
        # Pale-gold hair and the spectral lion Serosh as a mantle-like presence.
        for side in (-1,1):
            canvas.line(((cx+side*18,112),(cx+side*42,170),(cx+side*47,220)),(214,194,143,245),7)
            canvas.line(((cx+side*25,123),(cx+side*52,158),(cx+side*60,197)),(245,225,178,220),3)
        canvas.ellipse((cx-104,135,cx-12,222),fill=(142,129,101,180),outline=(225,214,174,190),width=4)
        canvas.ellipse((cx-76,147,cx-24,196),fill=(198,187,153,150),outline=(241,225,184,205),width=3)
        for i in range(13):
            x=cx-102+i*6
            canvas.line(((x,153),(x-14,185+rng.randint(-8,10)),(x-7,219)),(218,205,169,190),3)
        canvas.polygon(((cx-90,170),(cx-116,133),(cx-101,191)),(189,177,140,110),(233,220,184,150),2)
        canvas.line(((288,263),(328,118)),(132,107,77,255),12)
        canvas.polygon(((310,110),(345,86),(356,143),(330,168),(305,144)),(181,159,116,255),(239,215,157,255),3)
    elif direction.canonical == "maliketh":
        # Beast-clergyman muzzle, pale mane, layered black wraps and destined-death blade.
        canvas.ellipse((163,105,218,149),fill=(70,62,60,255),outline=(192,176,164,235),width=3)
        canvas.polygon(((179,132),(204,132),(221,164),(192,179),(164,159)),(28,25,29,255),(158,143,132,220),2)
        canvas.polygon(((160,109),(147,73),(173,88),(191,69),(210,91),(229,76),(219,117)),
                       (219,210,193,255),(245,237,220,220),2)
        for i in range(8):
            x=157+i*8
            canvas.line(((x,100),(x-10,75-rng.randint(0,18))),(225,215,198,215),3)
        canvas.line(((270,255),(318,105)),(35,31,40,255),11)
        canvas.line(((270,255),(318,105)),(159,123,189,235),3)
        _glow(canvas,(302,169),54,(106,72,164),88)
    elif direction.canonical == "messmer":
        # Red hair, dark crimson armor, spear and a restrained serpent coil.
        canvas.polygon(((163,123),(153,74),(180,90),(192,52),(205,89),(231,68),(218,125)),
                       (119,34,31,255),(205,100,73,235),2)
        canvas.line(((286,372),(245,92)),(95,31,31,255),11)
        canvas.line(((286,372),(245,92)),(213,181,151,235),3)
        canvas.polygon(((227,93),(245,53),(263,95),(249,121)),(165,46,39,255),(238,183,137,240),2)
        canvas.arc((104,155,293,335),205,345,(173,58,47,195),11)
        canvas.ellipse((266,175,294,203),fill=(174,59,46,255),outline=(234,173,125,235),width=2)
        _glow(canvas,(242,300),92,(205,67,38),55,.8)
    elif direction.canonical == "blaidd":
        # Wolf head remains unmistakable; armor stays humanoid and upright.
        canvas.polygon(((160,121),(149,62),(181,90),(193,70),(205,91),(235,57),(220,128)),
                       (88,91,94,255),(201,206,200,235),3)
        canvas.polygon(((177,113),(212,112),(230,148),(212,174),(183,166),(163,143)),
                       (104,108,107,255),(206,210,201,230),2)
        canvas.polygon(((185,145),(211,145),(226,171),(194,189),(170,166)),
                       (65,69,73,255),(177,183,180,215),2)
        canvas.ellipse((177,129,184,135),fill=(244,194,94,255))
        canvas.ellipse((211,129,218,135),fill=(244,194,94,255))
        canvas.line(((268,258),(326,113)),(176,188,202,255),10)
        canvas.line(((276,242),(326,113)),(247,247,234,240),2)
    elif direction.canonical == "gurranq":
        # Hunched beast-cleric with a stony muzzle and deathroot tendrils.
        canvas.ellipse((151,108,225,167),fill=(88,81,72,255),outline=(194,179,153,220),width=3)
        canvas.polygon(((169,137),(205,137),(225,180),(190,197),(153,172)),(47,43,40,255),(175,158,135,225),2)
        canvas.polygon(((151,115),(141,77),(174,99),(190,74),(211,99),(230,76),(219,127)),
                       (38,37,35,255),(164,150,132,200),2)
        canvas.line(((105,301),(65,347),(84,390)),(45,39,35,240),7)
        canvas.line(((272,293),(319,340),(300,395)),(45,39,35,240),7)
        for side in (-1,1):
            canvas.line(((cx+side*43,308),(cx+side*70,358),(cx+side*88,389)),(83,66,49,225),4)
    elif direction.canonical in {"black knife assassin", "black blade wanderer"}:
        # Face is fully concealed; compact hood, dark fitted armor and curved blade.
        canvas.polygon(((143,134),(153,76),(193,55),(232,83),(240,150),(213,130),(178,140)),
                       (13,15,21,255),(105,115,131,210),3)
        canvas.ellipse((171,118,211,154),fill=(4,6,11,255),outline=(90,99,115,210),width=2)
        canvas.line(((262,260),(306,164),(300,133)),(92,105,123,255),8)
        canvas.arc((273,120,340,230),245,65,(193,205,216,255),5)
        canvas.line(((255,271),(282,281)),(130,48,58,240),7)
    elif direction.canonical == "fia":
        # Fia: véu negro sobre o rosto, tecido de luto e luz espectral baixa.
        _glow(canvas,(190,206),100,(119,157,207),66,1.1)
        canvas.polygon(((150,113),(157,66),(192,49),(228,68),(238,138),(215,126),(170,130)),
                       (17,21,31,255),(125,133,151,205),3)
        canvas.polygon(((163,109),(191,91),(220,111),(213,155),(190,173),(168,151)),
                       (21,24,34,255),(107,119,142,205),2)
        for i in range(6):
            x=166+i*9
            canvas.line(((x,144),(x-8,205+i*5),(x-14,271+i*7)),(101,119,148,125),2)
        for x,y in ((118,265),(261,286),(150,337),(239,350)):
            canvas.ellipse((x-5,y-10,x+5,y+10),(174,203,231,60),(207,220,238,100),1)
    elif direction.canonical == "marika":
        # Marika: diadema solar, cabelo dourado longo e vestes régias claras.
        _glow(canvas,(191,141),120,(249,219,151),90,1.2)
        canvas.ellipse((170,102,212,151),(215,177,137,255),(255,232,189,225),2)
        canvas.polygon(((156,116),(157,73),(176,84),(192,42),(208,84),(228,72),(226,120)),
                       (174,128,61,255),(255,226,160,250),3)
        canvas.line(((157,84),(192,47),(226,84)),(255,240,199,245),3)
        for side in (-1,1):
            canvas.polygon(((171+side*19,119),(160+side*23,170),(151+side*25,278),
                            (172+side*18,314),(180+side*13,198)),
                           (204,167,105,245),(251,220,157,205),2)
            canvas.line(((179+side*16,142),(166+side*31,242),(177+side*30,343)),(244,219,165,220),4)
        canvas.polygon(((151,176),(230,176),(269,408),(113,408)),
                       (224,214,176,235),(255,239,204,245),3)
        canvas.polygon(((180,180),(204,180),(218,400),(164,400)),
                       (181,139,77,180),(248,215,154,225),2)
        canvas.arc((140,155,245,260),190,350,(255,238,193,180),3)
    elif direction.canonical == "godwyn":
        # Godwyn, o Dourado: cabelo solar, armadura clara e presença principesca.
        _glow(canvas,(190,148),116,(244,210,124),83,1.25)
        canvas.ellipse((165,98,217,151),(202,163,123,255),(255,229,176,240),2)
        for side in (-1,1):
            canvas.polygon(((172+side*18,106),(164+side*25,139),(155+side*27,211),
                            (171+side*20,252),(183+side*13,166)),
                           (210,170,76,255),(255,228,148,235),2)
        canvas.polygon(((150,172),(232,172),(255,261),(192,288),(128,261)),
                       (165,139,87,255),(247,216,145,245),3)
        canvas.polygon(((160,186),(224,186),(218,239),(192,263),(166,239)),
                       (215,191,123,255),(255,237,181,240),2)
        canvas.arc((125,82,260,218),198,342,(255,224,142,170),4)
        canvas.line(((192,185),(192,257)),(255,246,205,180),2)


def _draw_special_event(canvas: _Painter, card: dict[str, Any], direction: ArtDirection, palette, rng: random.Random):
    top, mid, accent, metal = palette
    ident = _norm(" ".join((str(card.get("nome", "")), str(card.get("descricao", "")), str(card.get("habilidade", "")))))
    cx = 192
    if direction.subject == "primordial entity":
        # Mãe Sem Forma: escala cósmica, eclipse carmesim e tentáculos membranosos.
        # A entidade permanece abstrata e não é convertida em sacerdotisa humanoide.
        _glow(canvas,(193,170),185,(178,21,48),120,1.2)
        canvas.ellipse((91,48,293,250),(17,5,17,245),(147,19,48,230),5)
        canvas.ellipse((125,79,259,219),(5,3,12,255),(82,15,36,185),2)
        for side in (-1,1):
            for i in range(4):
                start_x=192+side*(75+i*12)
                start_y=169+i*18
                bend_x=192+side*(130+i*15)
                end_x=192+side*(155+i*19)
                end_y=260+i*35
                canvas.line(((start_x,start_y),(bend_x,start_y+35),(end_x,end_y)),
                            (48,9,25,245),13-i)
                canvas.line(((start_x,start_y),(bend_x,start_y+35),(end_x,end_y)),
                            (174,34,62,155),3)
                canvas.ellipse((end_x-5,end_y-5,end_x+5,end_y+5),(214,75,91,190))
        for _ in range(78):
            x,y=rng.randint(35,350),rng.randint(70,390)
            radius=rng.choice((1,2,3,4))
            canvas.ellipse((x-radius,y-radius,x+radius,y+radius),
                           (192,42,70,rng.randint(30,115)))
    elif direction.subject == "protective blessing":
        # Bênção: um escudo de luz envolve uma posição, não um raio de purificação genérico.
        _glow(canvas,(192,244),145,(245,214,132),104,1.0)
        canvas.arc((73,117,311,365),190,350,(255,235,179,210),5)
        canvas.arc((88,133,296,352),10,170,(255,239,197,175),4)
        canvas.polygon(((192,93),(274,157),(261,279),(192,352),(123,279),(110,157)),
                       (234,207,128,22),(255,238,183,175),3)
        canvas.ellipse((168,215,216,263),(249,226,151,120),(255,246,212,225),3)
        for i in range(12):
            angle=math.tau*i/12
            x=192+math.cos(angle)*118
            y=235+math.sin(angle)*142
            canvas.ellipse((x-3,y-3,x+3,y+3),(255,230,169,rng.randint(80,190)))
    elif direction.subject == "ancestral vow":
        # O Crisol: raízes antigas entrelaçam um selo gravado no chão.
        _glow(canvas,(192,273),122,(204,142,73),75,.8)
        for side in (-1,1):
            for i in range(4):
                canvas.line(((192+side*12,376),(192+side*(42+i*15),321-i*16),
                             (192+side*(75+i*19),267-i*9),(192+side*(88+i*19),192-i*8)),
                            (91,79,56,225),8-i)
                canvas.line(((192+side*12,376),(192+side*(42+i*15),321-i*16),
                             (192+side*(75+i*19),267-i*9)),(197,164,109,135),2)
        canvas.ellipse((119,158,265,304),(25,24,27,195),(207,176,124,230),4)
        for i in range(8):
            angle=math.tau*i/8
            x=192+math.cos(angle)*56
            y=231+math.sin(angle)*56
            canvas.line(((192,231),(x,y)),(226,196,135,165),2)
        canvas.ellipse((180,219,204,243),(220,171,97,200),(255,227,163,230),2)
    elif direction.subject == "ashfall":
        # The ash front is a physical weather event; strata, visibility falloff and deposit.
        for i in range(9):
            y = 90 + i*28
            canvas.ellipse((-80, y-12, 450, y+24), fill=(130,129,126,rng.randint(22,52)))
        for _ in range(260):
            x, y = rng.randint(0,384), rng.randint(75,410)
            r = rng.choice((.5,1,1.5,2.2))
            canvas.ellipse((x-r,y-r,x+r,y+r), fill=(218,211,194,rng.randint(55,170)))
        # Faint troops and broken stakes disappear into the storm.
        for x in (72,132,254,311):
            canvas.ellipse((x-7,268,x+7,282), fill=(20,23,27,155))
            canvas.polygon(((x-12,284),(x+12,284),(x+18,352),(x-17,352)), (20,23,27,150))
    elif direction.subject == "frost phenomenon":
        # Frozen shockwave, branching crystal growth and a frozen ground plane.
        _glow(canvas,(cx,250),150,(168,216,249),100,.65)
        canvas.ellipse((30,205,354,385), fill=(157,203,235,36), outline=(206,233,249,180), width=4)
        for i in range(13):
            x = rng.randint(18,366); y = rng.randint(190,340)
            canvas.line(((x,y),(x+rng.randint(-20,20),y-rng.randint(25,90))), (194,227,248,rng.randint(75,155)), 2)
            canvas.line(((x,y-35),(x-12,y-52)), (206,235,250,110), 2)
            canvas.line(((x,y-49),(x+12,y-65)), (206,235,250,110), 2)
        for _ in range(80):
            x,y=rng.randint(0,384),rng.randint(70,400)
            canvas.line(((x,y),(x+2,y-5)),(232,247,255,rng.randint(80,190)),1)
    elif direction.subject == "storm event":
        # Diagonal rain, cloud shelf and a single lightning branch.
        for y in (85,120,155):
            canvas.ellipse((-30,y-20,420,y+28), fill=(17,25,39,115))
        for _ in range(250):
            x,y=rng.randint(0,384),rng.randint(100,430)
            canvas.line(((x,y),(x-7,y+16)),(159,184,204,rng.randint(35,105)),1)
        if _contains(ident,"raio","relampago","lightning","trovao"):
            pts=((245,82),(215,160),(247,156),(192,269),(211,190),(180,195),(245,82))
            canvas.polygon(pts,(238,239,255,90),(238,245,255,235),3)
            _glow(canvas,(218,174),58,(190,207,255),110)
        for y in (340,370,400):
            canvas.arc((20,y-11,360,y+19),0,180,(118,155,180,75),2)
    elif direction.subject == "flame event":
        # A chama recebe linguagem visual própria: negra, frenética ou colossal.
        black_flame = _contains(ident, "chama negra", "black flame")
        frenzied = _contains(ident, "frenetica", "frenética", "frenzied flame")
        giant_fire = _contains(ident, "gigante", "fire giant")
        if black_flame:
            outer=(49,29,83); edge=(139,93,197); core=(224,207,255)
            glow_color=(105,67,164)
        elif frenzied:
            outer=(170,72,17); edge=(255,177,41); core=(255,240,142)
            glow_color=(255,156,42)
        else:
            outer=(145,39,20); edge=(255,132,45); core=(255,226,160)
            glow_color=(246,82,36)
        count=5 if giant_fire else 7
        for index in range(count):
            x=38+index*(308/max(1,count-1))
            height=rng.randint(155,270) if giant_fire else rng.randint(105,220)
            wobble=rng.randint(-15,15)
            outer_shape=((x-31,405),(x-26,371),(x-12,390-height*.48),
                         (x+wobble,390-height),(x+11,390-height*.59),
                         (x+31,405),(x+21,414),(x-20,414))
            canvas.smooth_polygon(outer_shape,(*outer,rng.randint(155,220)),(*edge,215),1.4,steps=4)
            inner_shape=((x-13,406),(x-8,379),(x+1,390-height*.39),
                         (x+7,390-height*.68),(x+17,407))
            canvas.smooth_polygon(inner_shape,(*edge,220),(*core,170),.8,steps=4)
            if black_flame or frenzied:
                # Filamentos tortos tornam as chamas negras/frenéticas imediatamente distintas.
                for tendril in range(2):
                    tx=x+rng.randint(-12,12); ty=390-height+rng.randint(10,50)
                    canvas.smooth_line(((tx,ty),(tx+rng.randint(-18,18),ty-25),
                                        (tx+rng.randint(-24,24),ty-58)),
                                       (*edge,190),rng.choice((1,1.5,2)),steps=6)
        for _ in range(115 if frenzied else 90):
            x,y=rng.randint(0,384),rng.randint(35,370)
            r=rng.randint(1,6 if black_flame else 8)
            if black_flame:
                color=(148,116,203,rng.randint(65,185))
            elif frenzied:
                color=(255,rng.randint(120,220),rng.randint(35,90),rng.randint(90,225))
            else:
                color=(255,148,60,rng.randint(90,210))
            canvas.ellipse((x-r,y-r,x+r,y+r),color)
        _glow(canvas,(190,330),180,glow_color,115,.58 if giant_fire else .55)
    elif direction.subject == "resurrection or summoning":
        # A clear focal aperture with spectral figures ascending from below.
        _glow(canvas,(cx,275),120,(167,211,236),110,1.1)
        canvas.ellipse((88,136,296,372), fill=(15,24,38,95), outline=(183,217,235,185), width=5)
        canvas.arc((101,148,283,360),220,318,(243,244,225,210),3)
        for x, y in ((142,292),(192,258),(240,304)):
            canvas.ellipse((x-10,y-39,x+10,y-19), fill=(190,220,232,170))
            canvas.polygon(((x-17,y-18),(x+16,y-18),(x+29,y+49),(x-29,y+49)),(176,214,231,95))
            canvas.line(((x-13,y-2),(x,y+23),(x+13,y-2)),(236,246,250,155),2)
    elif direction.subject == "purification phenomenon":
        _glow(canvas,(cx,205),100,(246,221,155),135,1.5)
        canvas.polygon(((170,45),(214,45),(282,383),(103,383)),(255,232,165,36),(255,236,188,100),2)
        for i in range(7):
            y=110+i*35
            canvas.arc((112-i*5,y,272+i*5,y+70),185,355,(255,238,190,180-i*14),2)
        canvas.ellipse((157,348,227,368),fill=(244,220,153,115),outline=(255,248,217,210),width=2)
    elif direction.subject == "wolf summoning":
        # Three separate spectral wolves, with distinct silhouettes and ground direction.
        _glow(canvas,(191,282),120,(162,203,234),85,.75)
        for x, y, scale in ((104,276,.72),(193,238,1.0),(282,282,.72)):
            canvas.ellipse((x-31*scale,y-17*scale,x+31*scale,y+18*scale),
                           (22,30,42,205),(174,204,223,190),2)
            canvas.polygon(((x+14*scale,y-11*scale),(x+33*scale,y-39*scale),
                            (x+42*scale,y-10*scale),(x+33*scale,y+8*scale)),
                           (24,32,44,220),(188,216,233,200),2)
            canvas.polygon(((x+36*scale,y-9*scale),(x+65*scale,y+2*scale),
                            (x+42*scale,y+12*scale)),(30,39,51,220),(190,219,236,175),2)
            canvas.ellipse((x+30*scale,y-12*scale,x+35*scale,y-7*scale),fill=(226,242,255,255))
            for side in (-1,1):
                canvas.line(((x-17*scale,y+12*scale),(x-22*scale,y+43*scale),
                             (x-12*scale,y+52*scale)),(178,207,225,190),5)
        for _ in range(60):
            x,y=rng.randint(35,350),rng.randint(160,380)
            canvas.ellipse((x-1,y-1,x+1,y+1),(194,223,241,rng.randint(65,180)))
    elif direction.subject == "scarlet bloom":
        # The flower is the subject, not a generic corruption cloud.
        _glow(canvas,(191,285),144,(184,35,57),95,1.0)
        canvas.line(((190,402),(193,300),(173,245)),(39,85,49,255),12)
        canvas.line(((192,343),(233,313),(259,322)),(43,103,57,245),7)
        for i in range(9):
            ang=math.tau*i/9
            x=192+math.cos(ang)*70; y=212+math.sin(ang)*66
            tipx=192+math.cos(ang)*151; tipy=212+math.sin(ang)*133
            canvas.polygon(((192,212),(x-21, y-12),(tipx,tipy),(x+24,y+17)),
                           (138+rng.randint(0,48),24,42,235),(231,104,110,225),3)
            canvas.line(((x,y),(tipx*.96+192*.04,tipy*.96+212*.04)),(249,174,153,160),2)
        canvas.ellipse((160,180,224,244),(56,13,27,255),(250,172,133,240),4)
        for _ in range(35):
            x,y=rng.randint(65,320),rng.randint(100,390)
            canvas.ellipse((x-2,y-3,x+2,y+3),(173,45,65,rng.randint(50,145)))
    elif direction.subject == "full moon phenomenon":
        _glow(canvas,(192,146),170,(167,194,245),100,1.1)
        canvas.ellipse((96,47,288,239),(196,207,229,230),(242,244,249,245),4)
        canvas.ellipse((130,67,164,105),(159,171,201,70))
        canvas.ellipse((202,147,248,190),(159,171,201,65))
        for x in (37,344):
            canvas.rect((x,227,x+25,377),(13,18,35,240),(129,143,192,130),2)
            canvas.polygon(((x-6,227),(x+12,190),(x+31,227)),(18,24,43,245),(161,174,211,145),2)
        for y in (291,317,343,369):
            canvas.arc((70,y-7,316,y+23),0,180,(164,186,224,55),2)
    elif direction.subject == "spectral dash":
        # Directional streaks, low camera angle and a hound afterimage.
        _glow(canvas,(190,302),132,(173,207,236),100,.55)
        for i in range(9):
            y=256+i*14
            canvas.line(((26,y+35),(144,y+11),(333,y-24)),(160,192,217,max(20,135-i*12)),3)
        canvas.ellipse((190,197,246,252),(10,15,23,190),(164,192,214,150),2)
        canvas.polygon(((217,203),(226,160),(246,195),(241,222)),(18,24,34,220),(187,214,234,160),2)
        canvas.polygon(((238,219),(282,231),(246,244)),(18,24,34,210),(187,214,234,160),2)
    elif direction.subject == "sonic shockwave":
        # A roar is expressed by pressure rings crossing the battlefield, not an orb.
        for i in range(7):
            inset = i*17
            canvas.arc((25+inset,70+inset,359-inset,392-inset),205,338,
                       (224,205,166,max(25,165-i*18)),3)
        for x in (70,314):
            canvas.polygon(((x-22,285),(x,245),(x+16,293),(x+11,361),(x-14,360)),
                           (21,26,30,180),(201,189,164,110),2)
        _glow(canvas,(192,241),86,(230,216,174),65)
    elif direction.subject == "fortification event":
        # A massive bastion dominates the frame; troop figures establish scale.
        canvas.polygon(((38,385),(38,164),(72,125),(110,164),(110,385)),
                       (48,49,50,255),(192,169,126,230),4)
        canvas.polygon(((274,385),(274,164),(312,125),(348,164),(348,385)),
                       (48,49,50,255),(192,169,126,230),4)
        canvas.rect((90,200,294,385),fill=(58,58,56,255),outline=(201,182,143,230),width=4)
        canvas.rect((164,285,220,385),fill=(12,16,20,255),outline=(206,185,145,210),width=3)
        for x in range(112,286,29):
            canvas.rect((x,226,x+15,258),fill=(14,18,22,255),outline=(183,165,132,155),width=1)
        for y in range(245,360,36):
            canvas.line(((102,y),(282,y)),(178,158,121,95),2)
        _glow(canvas,(192,200),115,accent,38)
    elif direction.subject == "corruption event":
        # A low, spreading stain with vapor layers, not a generic red spell sphere.
        for i in range(7):
            y=265+i*17
            canvas.ellipse((-30,y-20,415,y+20),fill=(89,24,53,35+i*4))
        for _ in range(110):
            x,y=rng.randint(0,384),rng.randint(195,410)
            r=rng.randint(2,9)
            canvas.ellipse((x-r,y-r,x+r,y+r),(90,24,52,rng.randint(25,85)))
        for x in (45,108,279,340):
            canvas.line(((x,285),(x+rng.randint(-12,12),370)),(115,76,62,95),3)
    else:
        # Spatial rupture or a source-locked one-off phenomenon.
        _glow(canvas,(cx,220),160,accent,115,1.2)
        canvas.polygon(((194,66),(226,167),(206,196),(258,260),(191,378),(165,263),(199,204),(155,163)),
                       (17,12,30,215),(*_mix(accent,(255,255,255),.28),230),4)
        for i in range(8):
            y=100+i*32
            canvas.arc((70-i*4,y,314+i*4,y+150),195,345,(*accent,120-i*9),2)
        for _ in range(35):
            x,y=rng.randint(25,359),rng.randint(90,370)
            canvas.polygon(((x,y-4),(x+3,y),(x,y+4),(x-3,y)),(*metal,rng.randint(65,150)))


def _apply_material_finish(canvas: _Painter, palette, rng: random.Random):
    top, mid, accent, metal = palette
    # Grão fino e irregular de pigmento/filme, calculado pela própria imagem Pillow.
    # A máscara é discreta para preservar leitura em miniatura e não virar ruído digital.
    try:
        # Noise procedural explícito com a RNG semeada: não usa Image.effect_noise,
        # que pode introduzir variação não controlada entre execuções.
        noise_size = (max(32, canvas.w//4), max(32, canvas.h//4))
        noise_rng = random.Random(canvas.rng.getrandbits(64))
        noise = Image.new("L", noise_size)
        noise.putdata([noise_rng.randrange(256) for _ in range(noise_size[0]*noise_size[1])])
        noise = noise.resize(canvas.image.size, Image.Resampling.BICUBIC)
        grain = ImageOps.colorize(noise, (18, 16, 18), (246, 235, 211)).convert("RGBA")
        grain.putalpha(noise.point(lambda value: 17 if 24 < value < 232 else 6))
        canvas.image = Image.alpha_composite(canvas.image, grain)
        canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")
    except (AttributeError, OSError):
        # Fallback determinístico já disponível: pinceladas de baixa opacidade abaixo.
        pass
    # Sparse directional brushwork, tiny edge scratches and grounded contact shadows.
    for _ in range(220):
        x = rng.randint(0, canvas.w-1)
        y = rng.randint(int(canvas.h*.42), canvas.h-1)
        n = rng.randint(1, 5)
        color = rng.choice(((235,222,194,18),(8,10,14,24),(*accent,18)))
        canvas.draw.line((x,y,x+n,y-rng.randint(0,2)), fill=color, width=max(1,canvas.width(.45)))
    # Soft vignette, preserving the center and card focal subject.
    vignette = Image.new("RGBA", canvas.image.size, (0,0,0,0))
    vd = ImageDraw.Draw(vignette, "RGBA")
    for i in range(13):
        alpha = int(4 + (12-i)*1.5)
        inset = int(i * min(canvas.w,canvas.h) * .018)
        vd.rounded_rectangle((inset,inset,canvas.w-inset,canvas.h-inset), radius=canvas.width(20),
                              outline=(2,4,8,alpha), width=max(1,canvas.width(3)))
    vignette = vignette.filter(ImageFilter.GaussianBlur(canvas.width(14)))
    canvas.image = Image.alpha_composite(canvas.image, vignette)


def renderizar_pintura_carta(card: dict[str, Any], size: tuple[int, int], palette,
                             *, seed: int | None = None) -> Image.Image:
    """Gera a janela de ilustração em RGBA usando somente Pillow e random da stdlib."""
    width, height = (max(96, int(size[0])), max(96, int(size[1])))
    seed = _seed(card) if seed is None else int(seed)
    rng = random.Random(seed ^ 0x534F554C53415254)
    direction = analisar_direcao(card)
    canvas = _Painter(width, height, seed)
    _draw_sky(canvas, direction, palette, rng)
    _draw_architecture(canvas, direction, palette, rng)
    _draw_fog_and_grain(canvas, palette[2], rng)
    # Atmosfera/arquitetura recuam um plano; o sujeito será pintado depois, mais nítido.
    canvas.image = canvas.image.filter(ImageFilter.GaussianBlur(canvas.width(.55)))
    canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")
    # Sombra de contato ancora personagens e objetos ao cenário.
    if direction.subject not in {"storm event", "frost phenomenon", "flame event", "corruption event",
                                 "purification phenomenon", "full moon phenomenon", "spatial rupture"}:
        shadow_layer = Image.new("RGBA", canvas.image.size, (0,0,0,0))
        sd = ImageDraw.Draw(shadow_layer, "RGBA")
        sd.ellipse(canvas.box((88, 386, 296, 432)), fill=(2,3,6,88))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(canvas.width(13)))
        canvas.image = Image.alpha_composite(canvas.image, shadow_layer)
        canvas.draw = ImageDraw.Draw(canvas.image, "RGBA")

    category = _norm(card.get("categoria"))
    if direction.subject == "named relic or weapon":
        _draw_relic(canvas, card, palette, rng, direction)
    elif direction.subject == "paired characters":
        _draw_twin_pair(canvas, direction, palette, rng)
    elif direction.subject == "necromancer":
        _draw_necromancer(canvas, direction, palette, rng)
    elif direction.subject == "battle group":
        _draw_group(canvas, card, direction, palette, rng)
    elif direction.subject == "primordial entity":
        _draw_special_event(canvas, card, direction, palette, rng)
    elif direction.subject == "winged celestial":
        _draw_winged_celestial(canvas, direction, palette, rng)
    elif direction.subject == "giant":
        _draw_giant(canvas, card, direction, palette, rng)
    elif direction.subject == "divine manifestation":
        _draw_divine_manifestation(canvas, direction, palette, rng)
    elif direction.subject == "oathbound champion":
        _draw_oathbound_champion(canvas, card, direction, palette, rng)
    elif direction.subject == "ancient dragon warrior":
        _draw_dragonbound_warrior(canvas, direction, palette, rng)
    elif direction.subject in {
        "ashfall", "frost phenomenon", "storm event", "flame event",
        "resurrection or summoning", "purification phenomenon", "corruption event",
        "spatial rupture", "sonic shockwave", "fortification event", "wolf summoning",
        "scarlet bloom", "full moon phenomenon", "spectral dash",
    } or category == "especial":
        _draw_special_event(canvas, card, direction, palette, rng)
    elif direction.subject == "creature" or direction.canonical in {"placidusax", "elden beast"}:
        _draw_beast(canvas, card, direction, palette, rng)
    elif direction.canonical:
        _draw_canonical_character(canvas, card, direction, palette, rng)
    else:
        _draw_humanoid(canvas, direction, palette, rng)

    _apply_material_finish(canvas, palette, rng)
    # Supersampling is resolved once at the art window's final dimensions.
    final = canvas.image.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
    return final.filter(ImageFilter.UnsharpMask(radius=1.1, percent=115, threshold=3))
