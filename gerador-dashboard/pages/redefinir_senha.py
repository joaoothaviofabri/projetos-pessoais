import streamlit as st
import bcrypt
from time import sleep
from sqlalchemy import text
from database.connection import engine
from screen import require_login

st.title("Redefinier Senha")

require_login()

if "usuario" not in st.session_state:
    st.error("Você precisa estar logado em uma conta.")
    st.stop()

senha_atual = st.text_input("Senha atual", type="password", placeholder="Digite sua senha atual")
nova_senha = st.text_input("Nova Senha", type="password", placeholder="Digite sua nova senha")
confirmar_senha = st.text_input("Confirme sua senha", type="password", placeholder="Confirme sua senha")

if st.button("Redefinir senha"):

    email = st.session_state["usuario"]["email"]

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT senha FROM usuario WHERE email = :email"),
            {"email": email}
        ).fetchone()

    senha_hash = result[0]

    if not bcrypt.checkpw(senha_atual.encode(), senha_hash.encode()):
        st.error("Senha atual incorreta.")
        st.stop()

    if nova_senha != confirmar_senha:
        st.error("As senhas não coincidem.")
        st.stop()

    nova_senha = bcrypt.hashpw(
        nova_senha.encode(),
        bcrypt.gensalt()
    ).decode()

    with engine.connect() as conn:
        conn.execute(
            text("""
            UPDATE usuario 
            SET senha = :senha
            WHERE email = :email

            """),
            {
                "senha": nova_senha,
                "email": email
            }
        )
        conn.commit()

    with st.spinner("Carregando..."):
        st.success("Senha redefinida com sucesso.")
        sleep(0.6)
        st.session_state.clear()
        st.rerun()