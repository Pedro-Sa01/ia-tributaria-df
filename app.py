import os
import random
import streamlit as st
import xml.etree.ElementTree as ET
from openai import OpenAI

# -------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
APP_PASSWORD = os.getenv("APP_PASSWORD", "trocar-senha")

st.set_page_config(
    page_title="ContAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Remove elementos indesejados do Streamlit e mantém o botão do menu visível
custom_css = """
<style>

/* =============================== */
/* 1) REMOVER ÍCONES DO STREAMLIT  */
/* =============================== */

/* Remove botões do toolbar (caneta, estrela, share, github) */
header [data-testid="stToolbar"] button {
    display: none !important;
}

/* Remove a área do toolbar, mas SEM esconder o header */
header [data-testid="stToolbar"] {
    height: 0px !important;
    padding: 0px !important;
}

/* =============================== */
/* 2) MANTER O HEADER FUNCIONAL    */
/* =============================== */

/* Não esconde o header */
header {
    visibility: visible !important;
    height: auto !important;
}

/* =============================== */
/* 3) BOTÃO DO MENU SEMPRE VISÍVEL */
/* =============================== */

/* Botão de recolher/expandir sidebar */
button[kind="header"] {
    opacity: 1 !important;
    display: flex !important;
    visibility: visible !important;
}

/* Ícone do botão */
button[kind="header"] svg[data-testid="collapsedControl"] {
    opacity: 1 !important;
    visibility: visible !important;
}

/* Evitar desaparecer no hover */
button[kind="header"]:hover {
    opacity: 1 !important;
}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# -------------------------------------------------------------
# SISTEMA DE AUTENTICAÇÃO – TELA SEPARADA
# -------------------------------------------------------------

# Cria chave no estado da sessão (só na primeira execução)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Se NÃO autenticado → mostra apenas a tela de senha
if not st.session_state.autenticado:

    st.markdown(
        """
        <h1 style="text-align:center; margin-top: 40px; margin-bottom: 0px;">
            ContAI
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        senha = st.text_input(
            "Digite sua senha de acesso:",
            type="password"
        )

        if senha == APP_PASSWORD:
            st.session_state.autenticado = True
            st.rerun()  # troca de tela imediatamente

    st.stop()

# -------------------------------------------------------------
# APÓS A SENHA CORRETA → MOSTRAR FRASE ALEATÓRIA COMO O CHATGPT
# -------------------------------------------------------------

frases_iniciais = [
    "Tudo pronto? Vamos começar!",
    "Olá! Como posso ajudar hoje?",
    "Sou a ConAI, como posso ajudar?",
    "O que você deseja analisar hoje?",
    "O que você precisa para hoje?",
    "Qual sua dúvida? Eu posso ajudar."
]

# -------------------------------------------------------------
# FUNÇÃO IA – OPENAI API NOVA
# -------------------------------------------------------------
def consultar_ia(pergunta: str) -> str:
    """Envia a pergunta para a IA com o modelo novo da OpenAI."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é uma IA da Turing Tecnologia especializada em Direito Tributário do Distrito Federal. "
                        "Responda com precisão, clareza e sempre com base legal, caso não tenha acesso a base legal deixe isso claro para o usuário e sugira a ele que envie um feedback para Turing."
                    )
                },
                {"role": "user", "content": pergunta},
            ]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        return f"Erro ao consultar a IA: {e}"


# -------------------------------------------------------------
# FUNÇÃO PARA VALIDAR XML DE NF-e
# -------------------------------------------------------------
def validar_xml(xml_file):
    """Validação simples de CFOP e ICMS em um XML de NF-e."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        produto = root.find(".//nfe:prod/nfe:xProd", ns)
        cfop = root.find(".//nfe:prod/nfe:CFOP", ns)
        icms = root.find(".//nfe:ICMS//nfe:pICMS", ns)

        produto = produto.text if produto is not None else "Não encontrado"
        cfop = cfop.text if cfop is not None else "Não encontrado"
        icms = icms.text if icms is not None else "Não encontrado"

        tabela_icms = {
            "5101": "18",
            "5102": "18",
            "6102": "12"
        }

        esperado = tabela_icms.get(cfop, "Não mapeado")

        if esperado == "Não mapeado":
            resultado = f"CFOP {cfop} não mapeado."
        elif esperado == icms:
            resultado = f"ICMS correto ({icms}%)."
        else:
            resultado = f"Divergência: esperado {esperado}%, encontrado {icms}%."

        return {
            "Produto": produto,
            "CFOP": cfop,
            "ICMS informado": icms,
            "ICMS esperado": esperado,
            "Resultado": resultado
        }

    except Exception as e:
        return {"Erro": f"Não foi possível processar o XML: {e}"}


# -------------------------------------------------------------
# MENU LATERAL
# -------------------------------------------------------------
menu = st.sidebar.radio(
    "Escolha uma funcionalidade:",
    ["Consultar ContAI", "Validar XML de NF-e"]
)


# -------------------------------------------------------------
# ABA 1 – PERGUNTAS TRIBUTÁRIAS
# -------------------------------------------------------------
if menu == "Consultar ContAI":

    # Frase aleatória estilo ChatGPT
    st.markdown(
        f"""
        <p style="text-align:center; font-size:18px; opacity:0.85; margin-top:10px;">
            {random.choice(frases_iniciais)}
        </p>
        """,
        unsafe_allow_html=True
    )

    # Caixa de entrada sem título (apenas a caixa)
    pergunta = st.text_area(
        "",
        placeholder="Digite sua pergunta...",
        height=150
    )

    # Botão simples
    if st.button("Enviar"):
        if pergunta.strip() == "":
            st.warning("Digite uma pergunta antes de consultar.")
        else:
            with st.spinner("Consultando..."):
                resposta = consultar_ia(pergunta)
            st.write(resposta)


# -------------------------------------------------------------
# ABA 2 – VALIDAÇÃO DE XML
# -------------------------------------------------------------
elif menu == "Validar XML de NF-e":
    st.subheader("Validação de arquivo XML de NF-e")

    arquivo = st.file_uploader("Selecione o arquivo XML", type=["xml"])

    if arquivo is not None:
        with st.spinner("Processando XML..."):
            resultado = validar_xml(arquivo)

        st.markdown("### Resultado da análise")
        for chave, valor in resultado.items():
            st.write(f"**{chave}:** {valor}")


# Rodapé discreto
st.caption("Desenvolvido pela Turing Tecnologia")







