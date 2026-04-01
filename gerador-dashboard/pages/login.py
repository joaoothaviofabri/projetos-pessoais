import streamlit as st
import bcrypt
import secrets
import datetime
from time import sleep
from sqlalchemy import text
from database.connection import engine

# Estilização CSS
st.markdown("""
<style>
    .stTextInput>div>div>input {
        border-radius: 8px;
        padding: 10px;
    }

        stButton>button {
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

if "recuperar_senha" not in st.session_state:
    st.session_state["recuperar_senha"] = False

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title('Fazer Login')
    st.caption("Acesse sua conta")

with col2, st.form("login_usuario", border=True):
    email = st.text_input("Email", key='email_usuario', max_chars=100, placeholder='Digite seu email')
    senha = st.text_input("Senha", key='senha_usuario', max_chars=30, type='password', placeholder='Digite sua senha')

    col_btn1, col_btn2 = st.columns(2)

    # Botão de Entrar na Conta
    with col_btn1:
        enviar = st.form_submit_button("Entrar", use_container_width=True)

    # Botão de Cadastrar
    with col_btn2:
        cadastro = st.form_submit_button("Criar Conta", use_container_width=True)
        if cadastro:
            st.switch_page("./pages/cadastro.py")

    # Botão de Esqueci minha senha
    esqueci_senha = st.form_submit_button("Esqueci minha senha", use_container_width=True)
    if esqueci_senha:
            st.session_state["recuperar_senha"] = True

with col2:
    if st.session_state.get("recuperar_senha"):
        with st.container(border=True):
            st.subheader("🔑 Recuperar minha senha")

            with st.form("form_recuperar_senha"):
                email_recuperacao = st.text_input("Email", key="email_recuperacao", placeholder="Digite seu email")
                enviar_recuperacao = st.form_submit_button("Enviar recuperação", use_container_width=True)

            if enviar_recuperacao:
                st.session_state["recuperar_senha"] = True
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT email FROM usuario WHERE email = :email"),
                        {"email": email_recuperacao}
                    ).fetchone()

                if result:
                    st.success("Seu email foi válidado. Um link de recuperação de senha gerado!")

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
                                "token": token.strip(),
                                "expira": expira
                            }
                        )
                        conn.commit()

                        link = f"http://localhost:8501/resetar_senha?token={token.strip()}"
                        st.markdown(f"[Clique aqui para redefinir sua senha]({link})")

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

            with col2, st.spinner("Entrando..."):
                sleep(0.1)
                st.success("Login realizado!")
                sleep(0.1)
                st.switch_page("screen.py")

        else:
            with col2:
                st.error("Usuário ou senha inválidos!")