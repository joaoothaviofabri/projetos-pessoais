import streamlit as st
import bcrypt
import datetime
from time import sleep
from sqlalchemy import text
from screen import require_login
from database.connection import engine
from pydantic import BaseModel, Field, ValidationError

# Estilização CSS
st.markdown("""
<style>
    .stTextInput>div>div>input {
        border-radius: 8px;
        padding: 10px;
    }
    
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

token_param = st.query_params.get("token")

class Senha(BaseModel):
    nova_senha: str = Field(min_length=8)
    confirmar_nova_senha: str = Field(min_length=8)

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
    st.error("Token expirado! Solicit novamente.")
    st.stop()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("🔑 Redefinir senha")
    st.caption("Crie sua nova senha")

with col2, st.form("form_resetar_senha"):
    nova_senha = st.text_input("Nova senha", type="password", key="nova_senha", placeholder="Digite sua nova senha")
    confirmar_nova_senha = st.text_input("Confirmar senha", type="password", key="confirmar_senha", placeholder="Confirme sua senha")
    enviar = st.form_submit_button("Resetar senha", use_container_width=True)

if enviar:
    try:
        senha = Senha(
            nova_senha=nova_senha,
            confirmar_nova_senha=confirmar_nova_senha
        )

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

            with col2, st.spinner("Atualizando senha..."):
                st.success("Senha redefinida com sucesso!")
                sleep(0.1)
                st.switch_page("pages/login.py")

    except ValidationError as e:
        with col2:
            erro = e.errors()[0]
            campo = erro["loc"][0]

            mensagem = {
                "nova_senha": "Senha precia ter pelo menos 8 caracteres"
            }

            st.error(mensagem.get(campo, erro["msg"]))