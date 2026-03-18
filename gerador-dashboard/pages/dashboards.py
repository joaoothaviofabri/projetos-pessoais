import streamlit as st
import pandas as pd
import plotly.express as px
import json
from time import sleep
from screen import require_login
from database.connection import engine
from sqlalchemy import text

# If Login
require_login()

email = st.session_state["usuario"]["email"]

st.title("Meus Dashboards")

nome_dashboard = st.text_input("Nome do Dashboard", placeholder="Digite o nome do Dashboard")

if st.button("Salvar Dashboard"):
    if not nome_dashboard:
        st.error("Você precisa adicionar um nome para o Dashboard antes!")
        st.stop()

    config = {
        "tipo": "grafico_teste",
        "coluna_x": "idade",
        "coluna_y": "salario"
    }

    config_json = json.dumps(config)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM usuario WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if result is None:
            st.error("Usuário não encontrado.")
            st.stop()

        id_usuario = result[0]

        conn.execute(
            text("""
                INSERT INTO dashboard (id_usuario, nome, configuracao)
                VALUES (:id_usuario, :nome, :configuracao)
            """),
            {
                "id_usuario": id_usuario,
                "nome": nome_dashboard,
                "configuracao": config_json
            }
        )

        conn.commit()
        st.success("Dashboard salvo com sucesso!")

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT id FROM usuario WHERE email = :email"),
        {"email": email}
    ).fetchone()

    if result is None:
        st.error("Usuário não encontrado.")
        st.stop()

    id_usuario = result[0]

    result = conn.execute(
        text("SELECT id, nome, configuracao FROM dashboard WHERE id_usuario = :id_usuario"),
        {"id_usuario": id_usuario}
        ).fetchall()

    for row in result:
        st.subheader(row[1])

        config_json = row[2]

        if isinstance(config_json, str):
            config_loop = json.loads(config_json)
        else:
            config_loop = config_json

        if st.button("Abrir", key=f"abrir_{row[0]}"):
            st.session_state["dashboard_id"] = row[0]
            st.rerun()

        if st.session_state.get("dashboard_id") == row[0]:

            df = pd.DataFrame({
            "idade": [20, 30, 40],
            "salario": [2000, 3000, 4000]
            })

            with engine.connect() as conn:
                result_config = conn.execute(
                    text("SELECT configuracao FROM dashboard WHERE id = :id"),
                    {"id": row[0]}
                ).fetchone()

            config_json = result_config[0]

            if isinstance(config_json, str):
                config = json.loads(config_json)
            else:
                config = config_json

            st.write("ID Selecionado:", row[0])
            st.write("Config usada:", config)

            fig = px.bar(df, x=config["coluna_x"], y=config["coluna_y"])
            st.plotly_chart(fig)

        if st.button("Fechar", key=f"fechar_{row[0]}"):
            st.session_state["dashboard_id"] = None
            st.rerun()

    if not result:
        st.info("Você ainda não tem dashboards salvos!")