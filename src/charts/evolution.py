"""Gráficos de evolução mensal a partir de ``monthly_metrics`` (SQLite).

Elimina o formulário de digitação manual do código antigo: os valores dos meses
anteriores vêm direto do banco. Cada gráfico mantém o tipo visual original
(linha, barra, área, linha tracejada, barra horizontal).
"""

from __future__ import annotations

from .. import config
from ..data.repository import MonthlyMetrics
from ..domain.period import abrev_mes
from .base import limpar_spines, nova_figura


def _anota_pontos(ax, valores, unidade):
    max_val = max(valores) if max(valores) > 0 else 1
    for i, v in enumerate(valores):
        rotulo = str(int(v)) if unidade == "qtd" else f"{v:.1f}%"
        ax.text(i, v + max_val * 0.05, rotulo, ha="center", va="bottom",
                fontsize=12, fontweight="bold")


def _finaliza_eixo_x(ax, titulo, x_labels, unidade):
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, fontsize=16, fontweight="bold")
    ax.set_title(titulo, fontsize=18, fontweight="bold", pad=30)
    ax.set_ylabel("Quantidade" if unidade == "qtd" else "Percentual (%)", fontsize=12)
    ax.grid(True, alpha=0.3, linestyle="--")
    limpar_spines(ax, manter=("left", "bottom"))


def _box_resumo(fig, ax, descricoes):
    """Caixa de resumo à direita do gráfico (fora da área de plotagem).

    Por mês: categoria + percentual. Fica fora dos dados para não sobrepor a
    linha/barras — útil nas apresentações.
    """
    if not descricoes:
        return
    # Reserva margem direita e posiciona o box no espaço livre.
    fig.subplots_adjust(right=0.74)
    texto = "\n".join(descricoes)
    fig.text(0.76, 0.88, texto, fontsize=10, verticalalignment="top",
             horizontalalignment="left",
             bbox=dict(boxstyle="round", facecolor="#e0e0e0", edgecolor="#bdbdbd",
                       alpha=0.6))


def _grafico(titulo, valores, unidade, tipo, x_labels, descricoes=None):
    if all(v == 0 for v in valores):
        return None
    fig, ax = nova_figura(figsize=(10, 7))

    if tipo == "bar_horizontal":
        bars = ax.barh(range(len(valores)), valores, color=config.COR_PRIMARIA, height=0.4)
        ax.set_yticks(range(len(valores)))
        ax.set_yticklabels(x_labels, fontsize=16, fontweight="bold")
        for bar, v in zip(bars, valores):
            ax.text(bar.get_width() + max(valores) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    f"{v:.1f}%", ha="left", va="center", fontsize=14, fontweight="bold")
        ax.set_xlabel("Percentual (%)", fontsize=12)
        ax.set_title(titulo, fontsize=18, fontweight="bold", pad=30)
        ax.grid(True, alpha=0.3, linestyle="--", axis="x")
        limpar_spines(ax, manter=("bottom",))
        fig.tight_layout()
        return fig

    if tipo == "line":
        ax.plot(range(len(valores)), valores, marker="o", linewidth=4,
                markersize=14, color=config.COR_PRIMARIA)
        max_val = max(valores) if max(valores) > 0 else 1
        ax.set_ylim(0, max_val * 1.2)
    elif tipo == "bar":
        bars = ax.bar(range(len(valores)), valores, color=config.COR_PRIMARIA, width=0.5)
    elif tipo == "area":
        ax.fill_between(range(len(valores)), valores, alpha=0.3, color=config.COR_PRIMARIA)
        ax.plot(range(len(valores)), valores, marker="o", linewidth=3,
                markersize=12, color=config.COR_PRIMARIA)
    elif tipo == "line_dashed":
        ax.plot(range(len(valores)), valores, marker="s", linewidth=3,
                markersize=12, color=config.COR_PRIMARIA, linestyle="--")

    # Eixo de percentual ancorado em 0 para não exagerar diferenças pequenas
    # entre meses (ex.: 65%→67% deixa de ocupar a altura toda do gráfico).
    if unidade == "%":
        max_val = max(valores) if max(valores) > 0 else 1
        ax.set_ylim(0, max_val * 1.2)

    _anota_pontos(ax, valores, unidade)
    _finaliza_eixo_x(ax, titulo, x_labels, unidade)
    if descricoes:
        # subplots_adjust define o layout; tight_layout brigaria com ele.
        _box_resumo(fig, ax, descricoes)
    else:
        fig.tight_layout()
    return fig


def graficos_evolucao(metrics: list[MonthlyMetrics]) -> list[tuple[str, object]]:
    """Monta os 5 gráficos de evolução. Retorna lista de ``(titulo, fig)``.

    ``metrics`` deve vir em ordem cronológica crescente
    (ver ``repository.obter_metrics_ultimos_meses``).
    """
    if not metrics:
        return []

    x_labels = [abrev_mes(m.period) for m in metrics]

    def descricoes(get_nome, get_perc):
        return [
            f"{abrev_mes(m.period)}: {get_perc(m):.1f}% ({get_nome(m)})"
            for m in metrics
        ]

    series = [
        ("Total de Tarefas", [m.total_atividades for m in metrics], "qtd", "line", None),
        ("Centro de Custo", [m.cc_top_perc for m in metrics], "%", "bar",
         descricoes(lambda m: m.cc_top_nome, lambda m: m.cc_top_perc)),
        ("Produto", [m.produto_top_perc for m in metrics], "%", "area",
         descricoes(lambda m: m.produto_top_nome, lambda m: m.produto_top_perc)),
        ("Tipo de Atividade", [m.tipo_top_perc for m in metrics], "%", "line_dashed",
         descricoes(lambda m: m.tipo_top_nome, lambda m: m.tipo_top_perc)),
    ]

    resultado = []
    for titulo, valores, unidade, tipo, descr in series:
        fig = _grafico(titulo, valores, unidade, tipo, x_labels, descr)
        if fig:
            resultado.append((titulo, fig))

    fig = _grafico_planejadas_empilhado(metrics, x_labels)
    if fig:
        resultado.append(("Atividades Planejadas", fig))

    return resultado


def _grafico_planejadas_empilhado(metrics, x_labels):
    """Barras empilhadas 100% Planejado×Não Planejado por mês, com linha de meta.

    Cada barra horizontal soma 100%: segmento Planejado (cor primária) +
    Não Planejado (cor secundária). Rótulos trazem % e quantidade.
    """
    plan_perc = [m.planejadas_perc for m in metrics]
    if all(v == 0 for v in plan_perc):
        return None

    fig, ax = nova_figura(figsize=(11, 7))
    y = range(len(metrics))
    nao_perc = [100 - p for p in plan_perc]

    ax.barh(y, plan_perc, color=config.COR_PRIMARIA, height=0.55, label="Planejado")
    ax.barh(y, nao_perc, left=plan_perc, color=config.COR_SECUNDARIA, height=0.55,
            label="Não Planejado")

    for i, m in enumerate(metrics):
        if plan_perc[i] > 8:
            ax.text(plan_perc[i] / 2, i, f"{plan_perc[i]:.0f}%\n({m.planejadas_qtd})",
                    ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        if nao_perc[i] > 8:
            ax.text(plan_perc[i] + nao_perc[i] / 2, i,
                    f"{nao_perc[i]:.0f}%\n({m.nao_planejadas_qtd})",
                    ha="center", va="center", color="white", fontsize=11, fontweight="bold")

    # Linha de meta de % planejado.
    ax.axvline(config.META_PLANEJADO, color="#c0392b", linestyle="--", linewidth=2)
    ax.text(config.META_PLANEJADO, len(metrics) - 0.4,
            f"meta {config.META_PLANEJADO:.0f}%", color="#c0392b", fontsize=10,
            fontweight="bold", ha="center", va="bottom")

    ax.set_yticks(list(y))
    ax.set_yticklabels(x_labels, fontsize=16, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentual (%)", fontsize=12)
    ax.set_title("Atividades Planejadas", fontsize=18, fontweight="bold", pad=30)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False,
              fontsize=11)
    limpar_spines(ax, manter=("bottom",))
    fig.tight_layout()
    return fig
