"""Normalização única de rótulos de Planejamento.

No código antigo essa lógica estava duplicada em `gerar_grafico_comparativo` e
`calcular_indicadores`, com NaN mapeado de forma inconsistente (`'Desconhecido'`
num lugar, `'Outros'` no outro). Aqui há uma única fonte de verdade.
"""

import pandas as pd

PLANEJADO = "Planejado"
NAO_PLANEJADO = "Não Planejado"
OUTROS = "Outros"


def normalizar_planejamento(label) -> str:
    """Normaliza um rótulo de Planejamento para uma de três categorias.

    NaN/vazio → ``'Outros'`` (decisão única, resolvendo a inconsistência antiga).
    """
    if pd.isna(label):
        return OUTROS
    texto = str(label).strip().lower()
    tem_nao = "não" in texto or "nao" in texto
    if "planej" in texto and not tem_nao:
        return PLANEJADO
    if tem_nao:
        return NAO_PLANEJADO
    return OUTROS
