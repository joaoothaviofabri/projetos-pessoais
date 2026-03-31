import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
from time import sleep
from sqlalchemy import text
from plotly.graph_objects import Figure
from database.connection import engine

# Configuração da Página
st.set_page_config(
    page_title="Gerador de Gráficos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS
st.markdown("""
<style>
    .stButton>button {
            border-radius: 10px;
            height: 3em;
            font-weight: bold;
    }

    .stMetric {
    text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def require_login():
    if "usuario" not in st.session_state:
        st.switch_page("pages/login.py")


def formatar_nome(col):
    return col.lower().replace(" ", "_")


def formatar_label(col):
    return col.replace("_", " ").title()


def converter_data(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Tentar converter coluna para datetime sem quebrar o app."""
    df_copy = df.copy()

    if not pd.api.types.is_datetime64_any_dtype(df_copy[col]):
        try:
            df_copy[col] = pd.to_datetime(df_copy[col], errors="raise")
        except Exception:
            pass

    return df_copy


def limpar_json(obj):
    import math

    if isinstance(obj,dict):
        return {k: limpar_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [limpar_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


def criar_grafico(df: pd.DataFrame, x: str, y: str, tipo: str) -> Figure:
    df_plot = df.copy()

    # Tentar converter para datas
    df_plot = converter_data(df_plot, x)

    x_is_datatime = pd.api.types.is_datetime64_any_dtype(df_plot[x])
    x_is_cat = df_plot[x].dtype == "object" or df_plot[x].nunique() < 30
    y_is_num = pd.api.types.is_numeric_dtype(df_plot[y])

    # Se for datetime vs numérico
    if x_is_datatime and y_is_num:
        df_plot = (
            df_plot
            .groupby(x, as_index=False)[y]
            .mean()
            .sort_values(x)
        )
        df_plot[x] = pd.to_datetime(df_plot[x])

    # Se for categórico vs numérico -> agrega
    elif x_is_cat and y_is_num:
        df_plot = (
            df_plot
            .groupby(x, as_index=False)[y]
            .mean()
            .sort_values(y, ascending=False)
        )

    # Criação do Gráfico
    if tipo == "Barra":
        fig = px.bar(
            df_plot,
            x=x,
            y=y,
            text_auto=".2f",
        )

    elif tipo == "Linha":
        fig = px.line(
            df_plot,
            x=x,
            y=y,
            markers=True,
        )

    elif tipo == "Dispersão":
        fig = px.scatter(
            df_plot,
            x=x,
            y=y,
        )

    else:
        fig = px.bar(df_plot, x=x, y=y)

    # Melhorias Visuais
    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        xaxis_title=formatar_label(x),
        yaxis_title=formatar_label(y),
    )

    # Hover
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>"
    )

    return fig


# Requisição Login
if "usuario" not in st.session_state:
    st.session_state.usuario = False

st.title("📊 Gerador Inteligente de Gráficos")
st.caption("Carregue um arquivo e explore os dados visualmente")

# Botões de interação (Logado)
if st.session_state.usuario:
    with st.sidebar:
        st.markdown(f"# 👤  {st.session_state['usuario']['nome']}")
        st.write(f"📧 {st.session_state['usuario']['email']}")

        col_sair, col_senha = st.columns(2)

        with col_sair:
            sair = st.button("Sair")
            if sair:
                with st.success("Saindo..."):
                    st.session_state.clear()
                    st.rerun()

        with col_senha:
            redefinir_senha = st.button("Redefinir minha Senha")

            if redefinir_senha:
                st.switch_page("pages/redefinir_senha.py")          

        st.divider()

        st.markdown("## 📈 Navegação")

        if st.button("📊 Criar Gráfico", use_container_width=True):
            st.switch_page("./screen.py")

        if st.button("📁 Meus Dashboards", use_container_width=True):
            st.switch_page("./pages/dashboards.py")

else:
    with st.sidebar:
        st.markdown("# Acesse sua Conta!")

        col_login, col_cadastrar = st.columns(2)

        with col_login:
            login = st.button("Login")
            if login:
                st.switch_page("pages/login.py")

        with col_cadastrar:
            cadastrar = st.button("Cadastrar")
            if cadastrar:
                st.switch_page("pages/cadastro.py")


# Prevenção de bug antes do clique
if 'coluna_x' not in st.session_state:
    st.session_state['coluna_x'] = []
if 'coluna_y' not in st.session_state:
    st.session_state['coluna_y'] = []

# Lista de Gráfico
lista_grafico = ['Barra', 'Linha', 'Dispersão']

# Upload de arquivo
with st.container(border=True):
    st.subheader("📤 Upload do arquivo")
    user_file_upload = st.file_uploader(
        "Faça Upload do seu arquivo aqui:",
        type=["csv", "xlsx", "tsv", "ods", "parquet", "json"]
    )

# Leitura do Tipo do arquivo
if user_file_upload:
    nome = user_file_upload.name.lower()

    if nome.endswith(".csv"):
        df = pd.read_csv(user_file_upload)

    elif nome.endswith(".xlsx"):
        df = pd.read_excel(user_file_upload)

    elif nome.endswith(".tsv"):
        df = pd.read_csv(user_file_upload, sep="\t")

    elif nome.endswith(".ods"):
        df = pd.read_excel(user_file_upload, engine="odf")

    elif nome.endswith(".parquet"):
        df = pd.read_parquet(user_file_upload)

    elif nome.endswith(".json"):
        df = pd.read_json(user_file_upload)

    else:
        st.error("Formato não Suportado!")
        st.stop()

    st.session_state['df'] = df

    # Formatando e capitalizando as colunas do dataframe
    formatacao_coluna = {
        formatar_label(col): col
        for col in df.columns
    }
    st.session_state["formatacao_coluna"] = formatacao_coluna

# Flag de carregamento
if 'df_carregado' not in st.session_state:
    st.session_state['df_carregado'] = False

# Carregamento do DF e conexão com n8n
if user_file_upload:
    with st.container(border=True):
        st.subheader("📁 Carregar dados")

        with st.spinner("Processando dados"):
            if st.button("Carregar Dados") and not st.session_state.get("ai_processando"):
                st.session_state["ai_processando"] = True

                # Conversão do DataFrame para arquivo "CSV" e "bytes" para ser enviado para o n8n
                csv_bytes = df.to_csv(index=False).encode('utf-8')

                # Enviando o arquivo e fazendo conexão com n8n
                try:
                    for tentativa in range(3):
                        response = requests.post(
                            "http://localhost:5678/webhook/webhook-analisar-dataframe",
                            files={
                                'file': ('dados.csv', csv_bytes, 'text/csv')
                            },
                            timeout=30
                        )

                        if response.status_code == 200:
                            break
                        sleep(2)

                    # Salvando o retorno do n8n
                    dados = response.json()
                    coluna_x = dados[0]['output']['x_candidates']
                    coluna_y = dados[0]['output']['y_candidates']

                    # Formatação das colunas
                    st.session_state['coluna_x'] = [
                        formatar_label(formatar_nome(c)) for c in coluna_x
                    ]
                    st.session_state['coluna_y'] = [
                        formatar_label(formatar_nome(c)) for c in coluna_y
                    ]
                    st.session_state['df_carregado'] = True

                except Exception as e:
                    st.error(f"Erro ao enviar para o n8n: {e}")

# Criação dos Selectboxes
    if 'df' in st.session_state:
        df_metricas = st.session_state['df']

        col1, col2, col3 = st.columns(3)
        col1.metric("Linhas", df_metricas.shape[0])
        col2.metric("Colunas", df_metricas.shape[1])
        col3.metric("Valores nulos", df_metricas.isna().sum().sum())

    col_controles, col_grafico = st.columns([1, 2])

    # Coluna de Controle
    with col_controles:
        st.subheader("⚙️ Configuração do Gráfico")

        if st.session_state['df_carregado']:
            colunas_formatadas_x = st.session_state['coluna_x']
            colunas_formatadas_y = st.session_state['coluna_y']

            if not colunas_formatadas_x or not colunas_formatadas_y:
                st.warning("O n8n não retornou colunas suficientes para gerar o gráfico.")
                st.stop()

        else:
            st.info("Carregue o DataFrame para configurar o gráfico.")
            st.stop()

        eixo_x_label = st.selectbox("Selecione o valor para o eixo X:", options=colunas_formatadas_x, key="select_x")
        eixo_y_label = st.selectbox("Selecione o valor para o eixo Y:", options=colunas_formatadas_y, key="select_y")

        coluna = st.session_state["formatacao_coluna"]
        x_coluna = coluna[eixo_x_label]
        y_coluna = coluna[eixo_y_label]

        colunas_numericas = df.select_dtypes(include="number").columns.tolist()
        colunas_categoricas = df.select_dtypes(exclude="number").columns.tolist()

        tipo_grafico = st.selectbox("Selecione um tipo de Gráfico", options=lista_grafico)
        gerar_grafico = st.button("Gerar gráfico", use_container_width=True, disabled=not st.session_state.get("df_carregado"))

    # Coluna de Geração de Gráfico
    with col_grafico:
        st.subheader("📈 Visualização")

        if gerar_grafico:

            with st.spinner("Gerando gráfico..."):
                fig = criar_grafico(
                    df,
                    x_coluna,
                    y_coluna,
                    tipo_grafico
                )

                st.plotly_chart(fig, use_container_width=True)

            st.session_state["config_grafico"] = {
                "x": x_coluna,
                "y": y_coluna,
                "tipo_grafico": tipo_grafico,
                "dados": df.to_dict()
            }

            st.session_state["grafico_gerado"] = True

    #Salvar Dashboard
    with col_controles:
        if st.session_state.get("grafico_gerado"):
            if st.button("Salvar Dashboard", use_container_width=True):
                st.session_state["salvar_dashboard_nome_input"] = True

            if "limpar_input" not in st.session_state:
                st.session_state["limpar_input"] = False

            if st.session_state.get("salvar_dashboard_nome_input"):
                nome_dashboard = st.text_input("Nome do Dashboard", key="nome_dashboard_key", placeholder="Digite o nome do Dashboard")
                st.session_state.nome_dashboard = nome_dashboard

                if st.button("Confirmar Salvar"):
                    if "config_grafico" not in st.session_state:
                        st.error("Nenhum gráfico foi gerado ainda.")
                        st.stop()

                    config = st.session_state["config_grafico"]
                    config_limpo = limpar_json(config)
                    config_json = json.dumps(config_limpo)

                    email = st.session_state["usuario"]["email"]

                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT id FROM usuario WHERE email = :email"),
                            {"email": email}
                        ).fetchone()

                        id_usuario = result[0]  

                        result = conn.execute(
                            text("""INSERT INTO dashboard (id_usuario, nome, configuracao)
                                VALUES (:id_usuario, :nome, :configuracao)
                            """),
                            {
                                "id_usuario": id_usuario,
                                "nome": nome_dashboard,
                                "configuracao": config_json
                            }
                        )

                        st.success("Gráfico salvo com sucesso!")
                        conn.commit()

                        st.session_state["limpar_input"] = True
                        st.session_state["salvar_dashboard_nome_input"] = False
                        st.rerun()

# Visualização do DataFrame
if 'df' in st.session_state:
    with st.expander("👀 Visualizar dados"):
        st.dataframe(st.session_state['df'].head(20), use_container_width=True)