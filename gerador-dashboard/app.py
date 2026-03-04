import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.graph_objects import Figure
import requests
import time

def formatar_nome(col):
    return col.lower().replace(" ", "_")

def criar_grafico(df: pd.DataFrame, x: str, y: str, tipo: str) -> Figure:
    df=df.groupby(x).mean()


    if tipo == "Barra":
        fig = px.bar(df, x=x, y=y)

    elif tipo == "Linha":
        fig = px.line(df, x=x, y=y)

    elif tipo == "Dispersão":
        fig = px.scatter(df, x=x, y=y)

    else:
        fig = px.bar(df, x=x, y=y)

    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

st.set_page_config(
    page_title="Gerador de Gráficos",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Gerador Inteligente de Gráficos")
st.caption("Carregue um arquivo e explore os dados visualmente")

# Prevenção de bug antes do clique
if 'coluna_x' not in st.session_state:
    st.session_state['coluna_x'] = []
if 'coluna_y' not in st.session_state:
    st.session_state['coluna_y'] = []

# Upload de arquivo
with st.container(border=True):
    st.subheader("📤 Upload do arquivo")
    user_file_upload = st.file_uploader(
        "Faça Upload do seu arquivo aqui:",
        type=["csv", "xlsx", "tsv", "ods", "parquet", "json"]
    )

# Lista de Gráfico
lista_grafico = ['Barra', 'Linha', 'Dispersão']

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

    # Arrumando as colunas do dataframe
    colunas_formatadas = {
        col: col.replace("_", " ").title()
        for col in df.columns
    }

# Flag de carregamento
if 'df_carregado' not in st.session_state:
    st.session_state['df_carregado'] = False

# Botão de gerar gráfico
if user_file_upload:
    with st.container(border=True):
        st.subheader("📁 Carregar dados")

        with st.spinner("Processando dados"):
            if st.button("Carregar DataFrame") and not st.session_state.get("ai_processando"):
                st.session_state["ia_processando"] = True

                # Conversão do DataFrame para arquivo "CSV" e "bytes" para ser enviado para o n8n
                csv_bytes = df.to_csv(index=False).encode('utf-8')

                # Enviando o arquivo e fazendo conexão com n8n
                try:
                    # Salvando o retorno do n8n
                    for tentativa in range(3):
                        response = requests.post(
                            "http://localhost:5678/webhook-test/webhook-analisar-dataframe",
                            files={
                                'file': ('dados.csv', csv_bytes, 'text/csv')
                            },
                            timeout=30
                        )

                        if response.status_code == 200:
                            break
                        time.sleep(2)

                    dados = response.json()
                    coluna_x = dados[0]['output']['x_candidates']
                    coluna_y = dados[0]['output']['y_candidates']

                    st.session_state['coluna_x'] = [formatar_nome(c) for c in coluna_x]
                    st.session_state['coluna_y'] = [formatar_nome(c) for c in coluna_y]
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

        eixo_x = eixo_x_label
        eixo_y = eixo_y_label

        colunas_numericas = df.select_dtypes(include="number").columns.tolist()
        colunas_categoricas = df.select_dtypes(exclude="number").columns.tolist()

        tipo_grafico = st.selectbox("Selecione um tipo de Gráfico", options=lista_grafico)
        gerar_grafico = st.button("Gerar gráfico", use_container_width=True)

    with col_grafico:
        st.subheader("📈 Visualização")

        if gerar_grafico:
            fig = criar_grafico(
                df,
                eixo_x_label,
                eixo_y_label,
                tipo_grafico
            )

            st.plotly_chart(fig, use_container_width=True)


if 'df' in st.session_state:
    with st.expander("👀 Visualizar dados"):
        st.dataframe(st.session_state['df'].head(), use_container_width=True)