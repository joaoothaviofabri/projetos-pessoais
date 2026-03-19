import streamlit as st
import pandas as pd
import plotly.express as px
import json
from time import sleep
from sqlalchemy import text
from screen import require_login
from database.connection import engine
from screen import criar_grafico

# If Login
require_login()

email = st.session_state["usuario"]["email"]

st.title("Meus Dashboards")

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

            if isinstance(config_json, str):
                config = json.loads(config_json)
            else:
                config = config_json

            config = config_loop
            df = pd.DataFrame(config["dados"])

            if config["tipo_grafico"] == "Barra":
                fig = criar_grafico(
                    df,
                    config["x"],
                    config["y"],
                    config["tipo_grafico"]
                )

                st.plotly_chart(fig)

            elif config["tipo_grafico"] == "Linha":
                fig = px.line(df, x=config["x"], y=config["y"])

            elif config["tipo_grafico"] == "Dispersão":
                fig = px.scatter(df, x=config["x"], y=config["y"])

        if st.button("Fechar", key=f"fechar_{row[0]}"):
            st.session_state["dashboard_id"] = None
            st.rerun()

        if st.button("Deletar Dashboard", key=f"exlcuir_{row[0]}"):
            with engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM dashboard WHERE id = :id"),
                    {"id": row[0]}
                )
                conn.commit()

            st.success("Dashboard deletado com sucesso!")
            st.rerun()

    if not result:
        st.info("Você ainda não tem dashboards salvos!")