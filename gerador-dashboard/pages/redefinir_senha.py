import streamlit as st
import bcrypt
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

# Requisição
if not st.session_state.get('usuario', False):
    st.warning("Você precisa estar logado.")
    st.stop()
    require_login()


class Senha(BaseModel):
    nova_senha: str = Field(min_length=8)
    confirmar_senha: str = Field(min_length=8)


if "usuario" not in st.session_state:
    st.error("Você precisa estar logado em uma conta.")
    st.stop()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("Redefinier Senha")

with col2, st.form("form_redefinir_senha"):
    senha_atual = st.text_input("Senha atual", type="password", placeholder="Digite sua senha atual")
    nova_senha = st.text_input("Nova Senha", type="password", placeholder="Digite sua nova senha")
    confirmar_senha = st.text_input("Confirme sua senha", type="password", placeholder="Confirme sua senha")
    enviar = st.form_submit_button("Redefinir Senha", use_container_width=True)
    voltar = st.form_submit_button("Voltar", use_container_width=True)

if voltar:
    st.switch_page("./screen.py")

if enviar:
    try:
        senha = Senha(
            nova_senha=nova_senha,
            confirmar_senha=confirmar_senha
        )

        email = st.session_state["usuario"]["email"]

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT senha FROM usuario WHERE email = :email"),
                {"email": email}
            ).fetchone()

        if result is None:
            st.error("Usuário não encontrado.")
            st.stop()

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

        with col2, st.spinner("Carregando..."):
            st.success("Senha redefinida com sucesso.")
            sleep(0.6)
            st.session_state.clear()
            st.switch_page("./screen.py")

    except ValidationError as e:
        with col2:
            erro = e.errors()[0]
            campo = erro["loc"][0]

            mensagem = {
            "nova_senha": "Senha precisa ter pelo menos 8 caracteres"
            }

            st.error(mensagem.get(campo, erro["msg"]))