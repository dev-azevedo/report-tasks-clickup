import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configuração da página
st.set_page_config(
    page_title="Filtro de Tarefas",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuração de estilo para gráficos
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.titleweight'] = 'bold'

def criar_pasta_graficos():
    """Cria a pasta para salvar os gráficos se não existir"""
    pasta = "graficos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    return pasta

def gerar_grafico_barras(df, coluna, titulo, nome_arquivo):
    """Gera um gráfico de barras e salva na pasta de gráficos"""
    if coluna not in df.columns:
        return None
    
    # Conta os valores
    contagem = df[coluna].value_counts().sort_values(ascending=False)
    
    # Cria o gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(contagem)), contagem.values, color='#101C35', width=0.6)
    
    # Adiciona os valores em cima das barras
    for i, (bar, valor) in enumerate(zip(bars, contagem.values)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                str(valor), ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Configurações do gráfico
    ax.set_xticks(range(len(contagem)))
    ax.set_xticklabels(contagem.index, rotation=45, ha='right')
    ax.set_title(titulo, pad=20)
    ax.set_ylabel('')
    ax.set_ylim(0, max(contagem.values) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # Salva o gráfico
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta = criar_pasta_graficos()
    caminho = os.path.join(pasta, f"{nome_arquivo}_{timestamp}.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return caminho

def gerar_grafico_pizza(df, coluna, titulo, nome_arquivo, top_n=5):
    """Gera um gráfico de pizza com os top N valores"""
    if coluna not in df.columns:
        return None
    
    contagem = df[coluna].value_counts()
    
    # Pega apenas os top N e agrupa o resto como "Outros"
    if len(contagem) > top_n:
        top_valores = contagem.head(top_n)
        outros = contagem.iloc[top_n:].sum()
        contagem = pd.concat([top_valores, pd.Series({'Outros': outros})])
    
    # Define cores - todas em tons de #101C35
    cores = ['#101C35', '#1a2a47', '#243859', '#2e466b', '#38547d', '#42628f']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    wedges, texts, autotexts = ax.pie(contagem.values, labels=contagem.index, autopct='%1.1f%%',
                                        startangle=90, colors=cores[:len(contagem)],
                                        textprops={'fontsize': 10, 'weight': 'bold'})
    
    # Ajusta cor do texto percentual
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
    
    ax.set_title(titulo, pad=20, fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta = criar_pasta_graficos()
    caminho = os.path.join(pasta, f"{nome_arquivo}_{timestamp}.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return caminho

def gerar_grafico_barras_horizontal(df, coluna, titulo, nome_arquivo):
    """Gera um gráfico de barras horizontais"""
    if coluna not in df.columns:
        return None
    
    contagem = df[coluna].value_counts().sort_values(ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(contagem)), contagem.values, color='#101C35', height=0.6)
    
    # Adiciona os valores ao lado das barras
    for i, (bar, valor) in enumerate(zip(bars, contagem.values)):
        ax.text(bar.get_width() + max(contagem.values) * 0.02, bar.get_y() + bar.get_height()/2,
                str(valor), ha='left', va='center', fontsize=10, fontweight='bold')
    
    ax.set_yticks(range(len(contagem)))
    ax.set_yticklabels(contagem.index)
    ax.set_title(titulo, pad=20)
    ax.set_xlabel('')
    ax.set_xlim(0, max(contagem.values) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta = criar_pasta_graficos()
    caminho = os.path.join(pasta, f"{nome_arquivo}_{timestamp}.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return caminho

def gerar_grafico_comparativo(df, coluna, titulo, nome_arquivo):
    """Gera um gráfico comparativo (para Planejamento) com cores corretas"""
    if coluna not in df.columns:
        return None

    contagem = df[coluna].value_counts()

    # Normaliza os rótulos para garantir que o mapeamento funcione
    def normalizar(label):
        if pd.isna(label):
            return 'Desconhecido'
        label_str = str(label).strip().lower()
        if 'planej' in label_str and 'não' not in label_str and 'nao' not in label_str:
            return 'Planejado'
        elif 'não' in label_str or 'nao' in label_str:
            return 'Não Planejado'
        else:
            return 'Outros'

    # Aplica normalização
    df_norm = df.copy()
    df_norm['temp_label'] = df_norm[coluna].apply(normalizar)
    contagem = df_norm['temp_label'].value_counts()

    # Ordem desejada: Planejado primeiro, depois Não Planejado
    ordem = ['Planejado', 'Não Planejado']
    contagem = contagem.reindex(ordem, fill_value=0)

    # Cores fixas na ordem correta
    cores = ['#101C35', '#777777']  # Planejado: azul escuro | Não Planejado: vermelho

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(contagem)), contagem.values, color=cores, width=0.5)

    # Adiciona valores + percentuais
    total = contagem.sum()
    for i, (bar, valor) in enumerate(zip(bars, contagem.values)):
        percentual = (valor / total) * 100 if total > 0 else 0
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(contagem.values) * 0.02,
                f'{valor}\n({percentual:.1f}%)', ha='center', va='bottom',
                fontsize=12, fontweight='bold', color='black')

    # Rótulos no eixo X
    ax.set_xticks(range(len(contagem)))
    ax.set_xticklabels(['Planejado', 'Não Planejado'], fontsize=13, fontweight='bold')

    ax.set_title(titulo, pad=20, fontsize=16, fontweight='bold')
    ax.set_ylabel('')
    ax.set_ylim(0, max(contagem.values) * 1.25)
    
    # Remove bordas desnecessárias
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    # Salva
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta = criar_pasta_graficos()
    caminho = os.path.join(pasta, f"{nome_arquivo}_{timestamp}.png")
    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    return caminho

def gerar_todos_graficos(df):
    """Gera todos os gráficos principais"""
    graficos_gerados = []
    
    # Gráficos principais (barras verticais)
    configuracoes_barras = [
        ("Centro de Custo (drop down)", "Centro de Custo", "centro_custo"),
        ("Produto (drop down)", "Produto", "produto")
    ]
    
    for coluna, titulo, nome_arquivo in configuracoes_barras:
        caminho = gerar_grafico_barras(df, coluna, titulo, nome_arquivo)
        if caminho:
            graficos_gerados.append((titulo, caminho))
    
    # Gráfico comparativo para Planejamento
    caminho = gerar_grafico_comparativo(df, "Planejamento (drop down)", "Planejadas", "planejamento_comparativo")
    if caminho:
        graficos_gerados.append(("Planejamento", caminho))
    
    # Gráfico de barras horizontais para tipos
    caminho = gerar_grafico_barras_horizontal(df, "Tipo (drop down)", "Distribuição por Tipo", "tipo_horizontal")
    if caminho:
        graficos_gerados.append(("Tipo", caminho))
    
    return graficos_gerados

def calcular_indicadores(df):
    """Calcula os principais indicadores do dataset (com normalização consistente para Planejamento)"""
    indicadores = {}
    
    # Total de atividades
    indicadores['total_atividades'] = len(df)
    
    # Centro de Custo mais frequente (percentual relativo ao total de linhas não-nulas da coluna)
    if 'Centro de Custo (drop down)' in df.columns:
        centro_custo = df['Centro de Custo (drop down)'].dropna().value_counts()
        if len(centro_custo) > 0:
            top_centro = centro_custo.index[0]
            percentual = (centro_custo.iloc[0] / centro_custo.sum()) * 100
            indicadores['centro_custo'] = f"{top_centro}: {percentual:.2f}%"
        else:
            indicadores['centro_custo'] = "N/A"
    
    # Produto mais frequente (percentual relativo ao total de linhas não-nulas da coluna)
    if 'Produto (drop down)' in df.columns:
        produto = df['Produto (drop down)'].dropna().value_counts()
        if len(produto) > 0:
            top_produto = produto.index[0]
            percentual = (produto.iloc[0] / produto.sum()) * 100
            indicadores['produto'] = f"{top_produto}: {percentual:.2f}%"
        else:
            indicadores['produto'] = "N/A"
    
    # Atividades Planejadas (usando a mesma normalização do gráfico comparativo)
    if 'Planejamento (drop down)' in df.columns:
        def normalizar(label):
            if pd.isna(label):
                return 'Outros'
            label_str = str(label).strip().lower()
            if 'planej' in label_str and 'não' not in label_str and 'nao' not in label_str:
                return 'Planejado'
            elif 'não' in label_str or 'nao' in label_str:
                return 'Não Planejado'
            else:
                return 'Outros'

        df_norm = df.copy()
        df_norm['temp_label'] = df_norm['Planejamento (drop down)'].apply(normalizar)
        contagem = df_norm['temp_label'].value_counts().reindex(['Planejado', 'Não Planejado', 'Outros'], fill_value=0)

        # se você quer o percentual considerando apenas Planejado + Não Planejado (como no gráfico que soma 100%),
        # use esse denominador:
        denom = contagem['Planejado'] + contagem['Não Planejado']
        if denom > 0:
            perc_planejado = (contagem['Planejado'] / denom) * 100
        else:
            perc_planejado = 0.0

        indicadores['planejadas'] = f"Planejadas: {contagem['Planejado']} ({perc_planejado:.2f}%)"
    
    # Tipo mais frequente (percentual relativo ao total de linhas não-nulas da coluna)
    if 'Tipo (drop down)' in df.columns:
        tipo = df['Tipo (drop down)'].dropna().value_counts()
        if len(tipo) > 0:
            top_tipo = tipo.index[0]
            percentual = (tipo.iloc[0] / tipo.sum()) * 100
            indicadores['tipo'] = f"{top_tipo}: {percentual:.2f}%"
        else:
            indicadores['tipo'] = "N/A"
    
    return indicadores

st.title("📋 Filtro de Tarefas - By ClickUp - Tributo Justo")
st.markdown("---")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha o arquivo CSV", type=['csv'])

if uploaded_file is not None:
    try:
        # Lê o CSV
        df = pd.read_csv(uploaded_file)
        
        # Converte colunas de data
        date_columns = ['Due Date', 'Start Date', 'Date Created', 'Date Updated', 'Date Closed', 'Date Done']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        st.success(f"✅ Arquivo carregado com sucesso! Total de {len(df)} tarefas.")
        
        # Gera os gráficos principais automaticamente (apenas uma vez por upload)
        if 'ultimo_upload' not in st.session_state or st.session_state.ultimo_upload != uploaded_file.name:
            with st.spinner("📊 Gerando gráficos principais..."):
                graficos = gerar_todos_graficos(df)
                if graficos:
                    st.session_state.graficos_principais = graficos
                    st.session_state.ultimo_upload = uploaded_file.name
                    st.success(f"✅ {len(graficos)} gráficos gerados e salvos na pasta 'graficos/'!")
        
        # Sidebar com filtros
        st.sidebar.header("🔍 Filtros")
        
        # Período
        st.sidebar.subheader("Período")
        date_column = st.sidebar.selectbox(
            "Filtrar por data de:",
            ['Selecione...'] + date_columns,
            index=0
        )
        
        if date_column != 'Selecione...':
            col1, col2 = st.sidebar.columns(2)
            default_end = datetime.now().date()
            default_start = default_end - timedelta(days=30)
            start_date = col1.date_input("Data inicial", value=default_start)
            end_date = col2.date_input("Data final", value=default_end)
            
            mask = (df[date_column].dt.date >= start_date) & (df[date_column].dt.date <= end_date)
            df = df[mask]
        
        # Função auxiliar de filtro
        def aplicar_filtro(label, coluna, default='Todos'):
            if coluna in df.columns:
                options = [default] + sorted(df[coluna].dropna().unique().tolist())
                selected = st.sidebar.multiselect(label, options, default=[default])
                if default not in selected and len(selected) > 0:
                    return df[df[coluna].isin(selected)]
            return df
        
        # Filtros principais
        df = aplicar_filtro("Status", "Status")
        df = aplicar_filtro("Prioridade", "Priority", default="Todas")
        df = aplicar_filtro("Responsável", "Assignee")
        df = aplicar_filtro("Tipo de Tarefa", "Task Type")
        
        # Novos filtros com nomes reais do CSV
        df = aplicar_filtro("Centro de Custo", "Centro de Custo (drop down)")
        df = aplicar_filtro("Planejamento", "Planejamento (drop down)")
        df = aplicar_filtro("Produto", "Produto (drop down)")
        df = aplicar_filtro("Tipo", "Tipo (drop down)")
        
        # Busca por nome
        st.sidebar.subheader("🔎 Busca")
        search_text = st.sidebar.text_input("Buscar no nome da tarefa")
        if search_text:
            df = df[df['Task Name'].str.contains(search_text, case=False, na=False)]
        
        # === AGORA SIM: calcular indicadores com o DataFrame já filtrado! ===
        indicadores = calcular_indicadores(df)
        
        # Seção de Indicadores
        st.markdown("---")
        st.markdown("## 🎯 Impacto dos Indicadores")
        
        # Obter mês e ano atual
        mes_ano = datetime.now().strftime("%B / %Y")
        meses_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        for en, pt in meses_pt.items():
            mes_ano = mes_ano.replace(en, pt)
        
        # Primeira linha com 3 cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="color: #1a3a52; margin-bottom: 10px;">Atividades</h3>
                <p style="font-size: 18px; color: #666; margin: 0;">Total: {indicadores['total_atividades']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="color: #1a3a52; margin-bottom: 10px;">Centro de Custo</h3>
                <p style="font-size: 18px; color: #666; margin: 0;">{indicadores.get('centro_custo', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="color: #1a3a52; margin-bottom: 10px;">Produto</h3>
                <p style="font-size: 18px; color: #666; margin: 0;">{indicadores.get('produto', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Segunda linha com 2 cards centralizados
        col_spacer1, col4, col5, col_spacer2 = st.columns([0.5, 1, 1, 0.5])
        
        with col4:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="color: #1a3a52; margin-bottom: 10px;">Atividades Planejadas</h3>
                <p style="font-size: 18px; color: #666; margin: 0;">{indicadores.get('planejadas', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="color: #1a3a52; margin-bottom: 10px;">Atividades por Tipo</h3>
                <p style="font-size: 18px; color: #666; margin: 0;">{indicadores.get('tipo', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Data de referência
        st.markdown(f"""
        <p style="text-align: left; color: #888; margin-top: 20px; font-size: 16px;">
            {mes_ano}
        </p>
        """, unsafe_allow_html=True)
        
        # Resultados
        st.markdown("---")
        st.subheader(f"📊 Resultados: {len(df)} tarefas encontradas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Tarefas", len(df))
        with col2:
            if 'Status' in df.columns:
                prod = len(df[df['Status'].str.contains('Produção', case=False, na=False)])
                st.metric("Produção", prod)
        with col3:
            if 'Priority' in df.columns:
                high = len(df[df['Priority'].str.contains('urgent|high', case=False, na=False)])
                st.metric("Alta Prioridade", high)
        with col4:
            if 'Assignee' in df.columns:
                st.metric("Responsáveis", df['Assignee'].nunique())
        
        # Contagens extras
        st.markdown("### 📂 Informações Relevantes")
        
        def mostrar_contagem(coluna, titulo):
            if coluna in df.columns:
                count_df = df[coluna].value_counts().reset_index()
                count_df.columns = [coluna, "Quantidade"]
                st.markdown(f"#### {titulo}")
                st.dataframe(count_df, use_container_width=True, height=200)
        
        colA, colB = st.columns(2)
        
        with colA:
            mostrar_contagem("Centro de Custo (drop down)", "Atividades por Centro de Custo")
            mostrar_contagem("Planejamento (drop down)", "Atividades por Planejamento")
        
        with colB:
            mostrar_contagem("Produto (drop down)", "Atividades por Produto")
            mostrar_contagem("Tipo (drop down)", "Atividades por Tipo")
        
        # Exibição personalizada
        st.markdown("---")
        with st.expander("⚙️ Configurar colunas visíveis"):
            default_cols = ['Task Name', 'Status', 'Assignee', 'Priority', 'Due Date', 
                          'Centro de Custo (drop down)', 'Planejamento (drop down)', 
                          'Produto (drop down)', 'Tipo (drop down)']
            available = df.columns.tolist()
            selected = st.multiselect(
                "Selecione as colunas para exibir",
                available,
                default=[c for c in default_cols if c in available]
            )
        
        df_display = df[selected] if selected else df
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Exportação
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"tarefas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # ====================== GRÁFICOS PRINCIPAIS - EXIBIÇÃO AUTOMÁTICA ======================
        st.markdown("---")
        st.markdown("## 📊 Gráficos Principais")
        
        # Mostra os gráficos se já foram gerados
        if 'graficos_principais' in st.session_state:
            st.markdown("### 📈 Gráficos Gerados")
            cols = st.columns(2)
            for idx, (titulo, caminho) in enumerate(st.session_state.graficos_principais):
                with cols[idx % 2]:
                    st.image(caminho, caption=titulo, use_container_width=True)

        # ====================== EVOLUÇÃO MENSAL - USANDO OS INDICADORES CORRETOS ======================
        st.markdown("---")
        st.subheader("📈 Evolução Mensal - 5 Gráficos Individuais")

        from dateutil.relativedelta import relativedelta
        from datetime import datetime, timedelta

        # --- Meses ---
        hoje = datetime.now()
        mes_atual_dt     = hoje.replace(day=1) - timedelta(days=1)
        mes_passado_dt   = mes_atual_dt - relativedelta(months=1)
        mes_retrasado_dt = mes_atual_dt - relativedelta(months=2)

        def nome_mes(dt):
            return dt.strftime("%B / %Y")\
                .replace("January","Janeiro").replace("February","Fevereiro").replace("March","Março")\
                .replace("April","Abril").replace("May","Maio").replace("June","Junho")\
                .replace("July","Julho").replace("August","Agosto").replace("September","Setembro")\
                .replace("October","Outubro").replace("November","Novembro").replace("December","Dezembro")

        mes_retrasado = nome_mes(mes_retrasado_dt)
        mes_passado   = nome_mes(mes_passado_dt)
        mes_atual     = nome_mes(mes_atual_dt)

        # --- Valores atuais ---
        total_atual = indicadores['total_atividades']

        cc_atual_nome = indicadores.get('centro_custo', 'N/D').split(':')[0].strip()
        cc_atual_perc = float(indicadores.get('centro_custo', '0: 0%').split(':')[1].replace('%',''))

        prod_atual_nome = indicadores.get('produto', 'N/D').split(':')[0].strip()
        prod_atual_perc = float(indicadores.get('produto', '0: 0%').split(':')[1].replace('%',''))

        plan_str = indicadores.get('planejadas', 'Planejadas: 0 (0.00%)')
        plan_qtd = int(plan_str.split(':')[1].split('(')[0].strip())
        # Extrair percentual do indicador
        plan_perc_atual = float(plan_str.split('(')[1].replace('%)', '').strip())

        tipo_atual_nome = indicadores.get('tipo', 'N/D').split(':')[0].strip()
        tipo_atual_perc = float(indicadores.get('tipo', '0: 0%').split(':')[1].replace('%',''))

        # =====================================================================
        # FORMULÁRIO
        # =====================================================================
        with st.form("form_evolucao_graficos"):

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown("**Total de Tarefas**")
                st.markdown(f"*{mes_retrasado}*")
                tot_ret = st.number_input("Quantidade", value=0, step=1, key="tot_ret")
                
                st.markdown(f"*{mes_passado}*")
                tot_pass = st.number_input("Quantidade", value=0, step=1, key="tot_pass")
                
                st.markdown(f"**{mes_atual}**")
                st.success(f"**{total_atual}** tarefas")

            with col2:
                st.markdown("**Centro de Custo**")
                st.markdown(f"*{mes_retrasado}*")
                cc_ret = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Centro de Custo (drop down)'].dropna().unique()), key="cc_ret", label_visibility="collapsed")
                cc_val_ret = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="cc_val_ret")
                
                st.markdown(f"*{mes_passado}*")
                cc_pass = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Centro de Custo (drop down)'].dropna().unique()), key="cc_pass", label_visibility="collapsed")
                cc_val_pass = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="cc_val_pass")
                
                st.markdown(f"**{mes_atual}**")
                st.success(f"**{cc_atual_nome}**\n{cc_atual_perc:.1f}%")

            with col3:
                st.markdown("**Produto**")
                st.markdown(f"*{mes_retrasado}*")
                prod_ret = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Produto (drop down)'].dropna().unique()), key="prod_ret", label_visibility="collapsed")
                prod_val_ret = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="prod_val_ret")
                
                st.markdown(f"*{mes_passado}*")
                prod_pass = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Produto (drop down)'].dropna().unique()), key="prod_pass", label_visibility="collapsed")
                prod_val_pass = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="prod_val_pass")
                
                st.markdown(f"**{mes_atual}**")
                st.success(f"**{prod_atual_nome}**\n{prod_atual_perc:.1f}%")

            with col4:
                st.markdown("**Tipo de Atividade**")
                st.markdown(f"*{mes_retrasado}*")
                tipo_ret = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Tipo (drop down)'].dropna().unique()), key="tipo_ret", label_visibility="collapsed")
                tipo_val_ret = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="tipo_val_ret")
                
                st.markdown(f"*{mes_passado}*")
                tipo_pass = st.selectbox("Categoria", ["Nenhum"] + sorted(df['Tipo (drop down)'].dropna().unique()), key="tipo_pass", label_visibility="collapsed")
                tipo_val_pass = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="tipo_val_pass")
                
                st.markdown(f"**{mes_atual}**")
                st.success(f"**{tipo_atual_nome}**\n{tipo_atual_perc:.1f}%")

            with col5:
                st.markdown("**Atividades Planejadas**")
                st.markdown(f"*{mes_retrasado}*")
                plan_ret = st.number_input("Quantidade", value=0, step=1, key="plan_ret")
                plan_perc_ret = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="plan_perc_ret")
                
                st.markdown(f"*{mes_passado}*")
                plan_pass = st.number_input("Quantidade", value=0, step=1, key="plan_pass")
                plan_perc_pass = st.number_input("Percentual (%)", value=0.0, step=0.1, format="%.1f", key="plan_perc_pass")
                
                st.markdown(f"**{mes_atual}**")
                st.success(f"**{plan_qtd}** planejadas\n({plan_perc_atual:.1f}%)")

            # Botão submit fora das colunas, mas dentro do formulário
            st.markdown("")  # Espaço
            gerar = st.form_submit_button(
                "🎨 Gerar 5 Gráficos de Evolução",
                use_container_width=True
            )

        # =====================================================================
        # GERAÇÃO DOS GRÁFICOS
        # =====================================================================
        if gerar:

            meses_abrev = {
                'Janeiro':'Jan','Fevereiro':'Fev','Março':'Mar','Abril':'Abr',
                'Maio':'Mai','Junho':'Jun','Julho':'Jul','Agosto':'Ago',
                'Setembro':'Set','Outubro':'Out','Novembro':'Nov','Dezembro':'Dez'
            }

            def label(m):
                return meses_abrev.get(m.split(" / ")[0], m[:3])

            x_labels = [label(mes_retrasado), label(mes_passado), label(mes_atual)]

            pasta = criar_pasta_graficos()
            caminhos = []

            # Construir títulos com os nomes fornecidos
            titulo_cc = f"Centro de Custo"
            descricoes_cc = []
            if cc_ret and cc_ret != "Nenhum":
                descricoes_cc.append(f"{label(mes_retrasado)}: {cc_val_ret:.1f}% ({cc_ret})")
            if cc_pass and cc_pass != "Nenhum":
                descricoes_cc.append(f"{label(mes_passado)}: {cc_val_pass:.1f}% ({cc_pass})")
            descricoes_cc.append(f"{label(mes_atual)}: {cc_atual_perc:.1f}% ({cc_atual_nome})")
            
            titulo_prod = f"Produto"
            descricoes_prod = []
            if prod_ret and prod_ret != "Nenhum":
                descricoes_prod.append(f"{label(mes_retrasado)}: {prod_val_ret:.1f}% ({prod_ret})")
            if prod_pass and prod_pass != "Nenhum":
                descricoes_prod.append(f"{label(mes_passado)}: {prod_val_pass:.1f}% ({prod_pass})")
            descricoes_prod.append(f"{label(mes_atual)}: {prod_atual_perc:.1f}% ({prod_atual_nome})")
            
            titulo_tipo = f"Tipo de Atividade"
            descricoes_tipo = []
            if tipo_ret and tipo_ret != "Nenhum":
                descricoes_tipo.append(f"{label(mes_retrasado)}: {tipo_val_ret:.1f}% ({tipo_ret})")
            if tipo_pass and tipo_pass != "Nenhum":
                descricoes_tipo.append(f"{label(mes_passado)}: {tipo_val_pass:.1f}% ({tipo_pass})")
            descricoes_tipo.append(f"{label(mes_atual)}: {tipo_atual_perc:.1f}% ({tipo_atual_nome})")

            graficos = [
                ("Total de Tarefas", [tot_ret, tot_pass, total_atual], "qtd", "line", None),
                (titulo_cc, [cc_val_ret, cc_val_pass, cc_atual_perc], "%", "bar", descricoes_cc),
                (titulo_prod, [prod_val_ret, prod_val_pass, prod_atual_perc], "%", "area", descricoes_prod),
                (titulo_tipo, [tipo_val_ret, tipo_val_pass, tipo_atual_perc], "%", "line_dashed", descricoes_tipo),
                ("Atividades Planejadas", [plan_perc_ret, plan_perc_pass, plan_perc_atual], "%", "bar_horizontal", None),
            ]

            for titulo, valores, unidade, tipo_grafico, descricoes in graficos:
                if all(v == 0 for v in valores):
                    continue

                fig, ax = plt.subplots(figsize=(10, 7))
                
                # Diferentes tipos de gráficos
                if tipo_grafico == "line":
                    # Gráfico de linha padrão
                    ax.plot(range(3), valores, marker='o', linewidth=4, markersize=14, color='#101C35')
                    # Ajustar posição dos valores para não sobrepor o título
                    max_val = max(valores) if max(valores) > 0 else 1
                    for i, v in enumerate(valores):
                        label_valor = str(int(v)) if unidade == "qtd" else f"{v}%"
                        ax.text(i, v + max_val*0.05, label_valor, ha='center', va='bottom', fontsize=12, fontweight='bold')
                
                elif tipo_grafico == "bar":
                    # Gráfico de barras verticais
                    bars = ax.bar(range(3), valores, color='#101C35', width=0.5)
                    for i, (bar, v) in enumerate(zip(bars, valores)):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(valores)*0.02, 
                                f"{v}%", ha='center', va='bottom', fontsize=14, fontweight='bold')
                
                elif tipo_grafico == "area":
                    # Gráfico de área
                    ax.fill_between(range(3), valores, alpha=0.3, color='#101C35')
                    ax.plot(range(3), valores, marker='o', linewidth=3, markersize=12, color='#101C35')
                    for i, v in enumerate(valores):
                        ax.text(i, v + max(valores)*0.03, f"{v}%", ha='center', va='bottom', fontsize=14, fontweight='bold')
                
                elif tipo_grafico == "bar_horizontal":
                    # Gráfico de barras horizontais
                    bars = ax.barh(range(3), valores, color='#101C35', height=0.4)
                    ax.set_yticks(range(3))
                    ax.set_yticklabels(x_labels, fontsize=16, fontweight='bold')
                    for i, (bar, v) in enumerate(zip(bars, valores)):
                        ax.text(bar.get_width() + max(valores)*0.02, bar.get_y() + bar.get_height()/2,
                                f"{v}%", ha='left', va='center', fontsize=14, fontweight='bold')
                    ax.set_xlabel("Percentual (%)", fontsize=12)
                    ax.set_title(titulo, fontsize=18, fontweight='bold', pad=30)
                    ax.grid(True, alpha=0.3, linestyle='--', axis='x')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_visible(False)
                    plt.tight_layout()
                    nome_seguro = "".join(c for c in titulo if c.isalnum() or c in " _->")
                    caminho = os.path.join(
                        pasta,
                        f"Evolucao_{nome_seguro[:50]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
                    plt.close()
                    caminhos.append((titulo, caminho))
                    continue  # Pula o resto do código pois já foi formatado
                
                elif tipo_grafico == "line_dashed":
                    # Gráfico de linha tracejada
                    ax.plot(range(3), valores, marker='s', linewidth=3, markersize=12, 
                            color='#101C35', linestyle='--')
                    for i, v in enumerate(valores):
                        ax.text(i, v + max(valores)*0.03, f"{v}%", ha='center', va='bottom', fontsize=14, fontweight='bold')
                
                # Configurações comuns (exceto para bar_horizontal que já foi processado)
                if tipo_grafico != "bar_horizontal":
                    ax.set_xticks(range(3))
                    ax.set_xticklabels(x_labels, fontsize=16, fontweight='bold')
                    ax.set_title(titulo, fontsize=18, fontweight='bold', pad=30)
                    ax.set_ylabel("Quantidade" if unidade == "qtd" else "Percentual (%)", fontsize=12)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    
                    # Adicionar legenda com as descrições
                    if descricoes:
                        legenda_texto = "\n".join(descricoes)
                        ax.text(0.02, 0.98, legenda_texto, transform=ax.transAxes,
                                fontsize=9, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
                    
                    # Ajustar ylim para gráficos de linha para evitar sobreposição
                    if tipo_grafico == "line":
                        max_val = max(valores) if max(valores) > 0 else 1
                        ax.set_ylim(0, max_val * 1.2)

                    plt.tight_layout()
                    nome_seguro = "".join(c for c in titulo if c.isalnum() or c in " _->")
                    caminho = os.path.join(
                        pasta,
                        f"Evolucao_{nome_seguro[:50]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white')
                    plt.close()
                    caminhos.append((titulo, caminho))

            if caminhos:
                st.success(f"✅ {len(caminhos)} gráficos de evolução gerados com sucesso!")
                cols = st.columns(2)
                for i, (tit, cam) in enumerate(caminhos):
                    with cols[i % 2]:
                        st.image(cam, caption=tit, use_container_width=True)
            else:
                st.warning("⚠️ Preencha ao menos um valor para gerar gráficos.")
        # =====================================================================
        
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
else:
    st.info("👆 Por favor, faça o upload de um arquivo CSV para começar.")

with st.expander("ℹ️ Como usar"):
    st.markdown('''
    1. Faça upload do CSV exportado do ClickUp (os gráficos principais serão gerados automaticamente)
    2. Use a barra lateral para aplicar filtros (incluindo Centro de Custo, Planejamento, Produto e Tipo)
    3. Veja os gráficos principais gerados automaticamente
    4. Preencha o formulário de "Evolução Mensal" com dados dos meses anteriores e clique em "Gerar 5 Gráficos de Evolução"
    5. Veja as contagens e detalhes abaixo
    6. Exporte as tarefas filtradas em CSV
    ''')

st.markdown("---")
st.markdown("### 💻 Desenvolvido por [Jhonatan Azevedo](https://linkedin.com/in/dev-azevedo)")