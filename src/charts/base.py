"""Estilo comum aos gráficos.

Extrai a configuração repetida (spines, grid, rótulos) que estava duplicada nas
funções de gráfico do código antigo. Todos os builders retornam ``Figure`` em
memória — nada é salvo em disco.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # backend sem display, seguro em servidor/Streamlit
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.titleweight"] = "bold"


def nova_figura(figsize=(10, 6)):
    """Cria uma figura/eixo padrão."""
    return plt.subplots(figsize=figsize)


def limpar_spines(ax, manter=()):  # manter: iterável de lados a preservar
    """Remove spines e o respectivo eixo de ticks, exceto os lados em ``manter``."""
    for lado in ("top", "right", "left", "bottom"):
        if lado not in manter:
            ax.spines[lado].set_visible(False)


def fig_para_png(fig) -> bytes:
    """Serializa a figura como PNG (dpi 300, fundo branco) para download."""
    import io

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    return buffer.getvalue()
