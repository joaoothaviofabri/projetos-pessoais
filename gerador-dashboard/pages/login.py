import streamlit as st
import bcrypt
import secrets
import datetime
from time import sleep
from sqlalchemy import text
from database.connection import engine
from utils.email_service import enviar_email

st.title('Fazer Login')

with st.form("login_usuario"):
    email = st.text_input("Email", key='email_usuario', max_chars=100, placeholder='Digite seu email')
    senha = st.text_input("Senha", key='senha_usuario', max_chars=30, type='password', placeholder='Digite sua senha')
    enviar = st.form_submit_button("Logar")

if st.button("Não tem uma conta? Cadastre-se!"):
    st.switch_page("./pages/cadastro.py")

if st.button("Esqueci minha senha!"):
    st.session_state["recuperar_senha"] = True

if st.session_state.get("recuperar_senha"):
    st.header("🔑 Recuperar minha senha")

    email_recuperacao = st.text_input("Email: ", placeholder="Digite seu email")

    if st.button("Enviar recuperação"):
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT email FROM usuario WHERE email = :email"),
                {"email": email_recuperacao}
            ).fetchone()

        if result:
            st.success("Seu email foi válidado, enviaremos intruções para redefinir sua senha!")

            token = secrets.token_urlsafe(32)

            expira = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

            with engine.connect() as conn:

                conn.execute(
                    text("DELETE FROM password_reset WHERE email = :email"),
                    {"email": email_recuperacao}
                )

                conn.execute(
                    text("""
                    INSERT INTO password_reset (email, token, expira_em)
                    VALUES (:email, :token, :expira)
                    """),

                    {
                        "email": email_recuperacao,
                        "token": token,
                        "expira": expira
                    }
                )
                conn.commit()

                link = f"http://localhost:8501/resetar_senha?token={token.strip()}"
                enviar_email(email_recuperacao, link)

        else:
            st.error("Esse email não foi encontrado!")
if enviar:

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT nome, senha FROM usuario WHERE email = :email LIMIT 1"),
            {"email": email}
        ).fetchone()

    if result is None:
        st.error("Usuário ou senha inválidos")

    else:
        nome = result[0]
        senha_hash = result[1]

        if bcrypt.checkpw(
            senha.encode(),
            senha_hash.encode()
        ):

            st.session_state["usuario"] = {
                "nome": nome,
                "email": email
            }

            with st.spinner("Carregando..."):
                sleep(2)
                st.success("Login realizado!")
                sleep(0.8)
                st.switch_page("screen.py")

        else:
            st.error("Usuário ou senha inválidos!")