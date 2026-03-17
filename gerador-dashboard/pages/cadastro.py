import streamlit as st
import pandas as pd
import bcrypt
from time import sleep
from sqlalchemy import text
from pydantic import BaseModel, Field, EmailStr, ValidationError
from database.connection import engine

def limpar_form():
    st.session_state["nome_usuario"] = ""
    st.session_state["email_usuario"] = ""
    st.session_state["senha_usuario"] = ""


class Usuario(BaseModel):
    nome: str = Field(min_length=3)
    email: EmailStr
    senha: str = Field(min_length=8)

st.title("Criar Conta")

if st.session_state.get("limpar_form"):
    st.session_state.nome_usuario = ""
    st.session_state.email_usuario = ""
    st.session_state.senha_usuario = ""
    st.session_state["limpar_form"] = False

with st.form("cadastro_usuario"):
    nome = st.text_input('Nome:', key='nome_usuario' ,max_chars=50, placeholder='Crie seu nome de usuário')
    email = st.text_input('Email:', key='email_usuario', max_chars=100, placeholder='Digite seu email')
    senha = st.text_input('Senha:', key='senha_usuario', max_chars=30, type='password', placeholder='Crie sua senha')

    enviar = st.form_submit_button("Cadastrar")
    if st.form_submit_button("Possui uma conta? Logar!"):
        st.switch_page("./pages/login.py")

if enviar:
    try:
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha
        )

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM usuario WHERE email = :email"),
                {"email": email}
            ).fetchone()

        if result:
            st.error("Já existe um cadastro com esse email.")
            st.stop()

        senha_hash = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

        dados = usuario.dict()
        dados['senha'] = senha_hash

        dados_cadastro = pd.DataFrame([dados])

        dados_cadastro.to_sql(
            "usuario",
            engine,
            if_exists="append",
            index=False
        )

        with st.spinner("Carregando..."):
            sleep(2)
            st.success("Usuário Cadastrado!")
            sleep(0.8)

        st.session_state["limpar_form"] = True
        st.switch_page("./pages/login.py")
        st.rerun()

    except ValidationError as e:

        for erro in e.errors():
            campo = erro["loc"][0]
            mensagem = erro["msg"]

            mensagens = {
            "nome": "Nome precisa ter pelo menos 3 caracteres",
            "email": "Email inválido",
            "senha": "Senha precisa ter pelo menos 8 caracteres"
            }

            st.error(mensagens.get(campo, mensagem))