# Validação do staging histórico Card Engine v2 v0.2

**Status:** PASS  
**Modelos históricos:** 137  
**Alpha-only:** 27  
**Bloqueados:** 110

Foram verificados IDs únicos, igualdade com o snapshot histórico, partição exata da allowlist, bloqueadores presentes nos registros bloqueados, resumo e SHA-256 das três fontes. Este staging é review-only e não é carregado como catálogo de runtime.

O script `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py` regenera este relatório.
