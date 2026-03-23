import streamlit as st
import pandas as pd
import plotly.express as px
import json
from time import sleep
from sqlalchemy import text
from screen import require_login
from database.connection import engine
from screen import criar_grafico

# Estilização CSS
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        height: 2.8em;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

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

    cols = st.columns(3)
    for i, row in enumerate(result):
        col = cols[i % 3]

        with col:
            with st.container(border=True):
                st.subheader(row[1])

                config_json = row[2]

                if isinstance(config_json, str):
                    config_loop = json.loads(config_json)
                else:
                    config_loop = config_json

                st.caption(f"Eixo X: {config_loop['x']}")
                st.caption(f"Eixo Y: {config_loop['y']}")
                st.caption(f"Tipo: {config_loop['tipo_grafico']}")

                col1, col2, col3 = st.columns(3)

                with col1:
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

                with col2:
                    if st.button("Deletar Dashboard", key=f"exlcuir_{row[0]}"):
                        with engine.connect() as conn:
                            conn.execute(
                                text("DELETE FROM dashboard WHERE id = :id"),
                                {"id": row[0]}
                            )
                            conn.commit()

                        st.success("Dashboard deletado com sucesso!")
                        st.rerun()

                if "dashboard_id" in st.session_state and st.session_state["dashboard_id"]:
                    st.divider()
                    st.subheader("📈 Visualização do Dashboard")

                    dashboard_id = st.session_state["dashboard_id"] 

                    dashboard = next((r for r in result if r[0] == dashboard_id), None)

                    if dashboard:
                        config_json = dashboard[2]

                        if isinstance(config, str):
                            config = json.loads(config_json)
                        else:
                            config = config_json

                        df = pd.DataFrame(config_json["dados"])

                        fig = criar_grafico(
                            df,
                            config["x"],
                            config["y"],
                            config["tipo_grafico"]
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        if st.button("Fechar", key=f"fechar_{row[0]}"):
                            st.session_state["dashboard_id"] = None
                            st.rerun()

    if not result:
        st.info("Você ainda não tem dashboards salvos!")