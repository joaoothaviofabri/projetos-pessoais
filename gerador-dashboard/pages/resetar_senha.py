import streamlit as st
import bcrypt
import datetime
from time import sleep
from sqlalchemy import text
from database.connection import engine

token_param = st.query_params.get("token")

if not token_param:
    st.error("Token não encontrado.")
    st.stop()

token = token_param

with engine.connect() as conn:
    result = conn.execute(
        text("""
        SELECT email, expira_em
        FROM password_reset
        WHERE token = :token
        """),
        {"token": token}
    ).fetchone()

if result is None:
    st.error("Token inválido.")
    st.stop()

email = result[0]
expira = result[1]

if datetime.datetime.utcnow() > expira:
    st.error("Token expirado!")
    st.stop()

st.title("🔑 Redefinir senha")

nova_senha = st.text_input("Nova senha", type="password", placeholder="Digite sua nova senha")
confirmar_nova_senha = st.text_input("Confirmar senha", type="password", placeholder="Confirme sua senha")

if st.button("Redefinir senha"):

    if nova_senha != confirmar_nova_senha:
        st.error("As senhas não coincidem!")

    else:
        senha_hash = bcrypt.hashpw(
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
                    "senha": senha_hash,
                    "email": email
                }
            )

            conn.execute(
                text("DELETE FROM password_reset WHERE token = :token"),
                {"token": token.strip()}
            )

            conn.commit()

        st.success("Senha redefinida com sucesso!")
        sleep(0.6)
        st.switch_page("pages/login.py")