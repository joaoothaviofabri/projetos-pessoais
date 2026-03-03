import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

def formatar_nome(col):
    return col.lower().replace(" ", "_")

st.title('Gerador de Dashboards')

# Prevenção de bug antes do clique
if 'coluna_x' not in st.session_state:
    st.session_state['coluna_x'] = []
if 'coluna_y' not in st.session_state:
    st.session_state['coluna_y'] = []

# Upload de arquivo
user_file_upload = st.file_uploader(
    "Faça Upload do seu arquivo aqui:",type=["csv", "xlsx", "tsv", "ods", "parquet", "json"]
)

# Lista de Gráfico
lista_grafico = ['Barra', 'Linha']

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
    carregar_dataframe = st.button('Carregar DataFrame')

    if carregar_dataframe:
        # Conversão do DataFrame para arquivo "CSV" e "bytes" para ser enviado para o n8n
        csv_bytes = df.to_csv(index=False).encode('utf-8')

        # Enviando o arquivo e fazendo conexão com n8n
        try:
            response = requests.post(
                "http://localhost:5678/webhook-test/webhook-analisar-dataframe",
                files={
                    'file': ('dados.csv', csv_bytes, 'text/csv')
                },
                timeout=30
            )

            # Salvando o retorno do n8n
            dados = response.json()
            coluna_x = dados[0]['output']['x_candidates']
            coluna_y = dados[0]['output']['y_candidates']

            st.session_state['coluna_x'] = [formatar_nome(c) for c in coluna_x]
            st.session_state['coluna_y'] = [formatar_nome(c) for c in coluna_y]
            st.session_state['df_carregado'] = True

        except Exception as e:
            st.error(f"Erro ao enviar para o n8n: {e}")

# Criação dos Selectboxes
    if st.session_state['df_carregado']:
        colunas_formatadas_x = st.session_state['coluna_x']
        colunas_formatadas_y = st.session_state['coluna_y']

        if not colunas_formatadas_x or not colunas_formatadas_y:
            st.warning("O n8n não retornou colunas suficientes para gerar o gráfico.")
            st.stop()

        eixo_x_label = st.selectbox("Selecione o valor para o eixo X:", options=colunas_formatadas_x, key="select_x")
        eixo_y_label = st.selectbox("Selecione o valor para o eixo Y:", options=colunas_formatadas_y, key="select_y")

        eixo_x = eixo_x_label
        eixo_y = eixo_y_label

        selecao_grafico = st.selectbox("Selecione um tipo de Gráfico", options=lista_grafico)

        botao_gerar_grafico = st.button('Gerar Gráfico')

        if botao_gerar_grafico:
            if selecao_grafico == lista_grafico[0]:
                # Gráfico de barra
                fig_bar = px.bar(st.session_state['df'], x=eixo_x, y=eixo_y)
                st.plotly_chart(fig_bar)

            elif selecao_grafico == lista_grafico[1]:
                # Gráfico de linha
                fig_line = px.line(st.session_state['df'], x=eixo_x, y=eixo_y)
                st.plotly_chart(fig_line)