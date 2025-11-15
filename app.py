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

# -------------------------------------------------------------
# CSS GLOBAL – LIMPEZA E AJUSTES
# -------------------------------------------------------------
custom_css = """
<style>

/* Remover ícones superiores do Streamlit */
header [data-testid="stToolbarActions"] { display: none !important; }
header [data-testid="stMainMenu"] { display: none !important; }

header {
    visibility: visible !important;
    height: auto !important;
}

/* Botão colapsar/expandir sidebar sempre visível */
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] {
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    transition: none !important;
}

[data-testid="stSidebarCollapseButton"] span,
[data-testid="stExpandSidebarButton"] span {
    opacity: 1 !important;
}

/* Ocultar botão "manage app" e badges */
button[data-testid="manage-app-button"],
a[class*="_viewerBadge"],
div[class*="_profileContainer"],
img[data-testid="appCreatorAvatar"] {
    display: none !important;
    visibility: hidden !important;
}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------
# SISTEMA DE AUTENTICAÇÃO
# -------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:

    st.markdown(
        """
        <h1 style="text-align:center; margin-top: 40px; margin-bottom: 0;">
            ContAI
        </h1>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        senha = st.text_input("Digite sua senha de acesso:", type="password")

        if senha == APP_PASSWORD:
            st.session_state.autenticado = True
            st.rerun()

    st.stop()

# -------------------------------------------------------------
# HEADER – NOME DA TURING NO TOPO
# -------------------------------------------------------------
st.markdown(
    """
    <div style="
        width: 100%;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 15px;
        font-size: 26px;
        font-weight: 600;
        letter-spacing: 0.3px;
        color: rgba(250, 250, 250, 0.90);
    ">
        Turing Tecnologia
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------
# FRASES INICIAIS
# -------------------------------------------------------------
frases_iniciais = [
    "Tudo pronto? Vamos começar!",
    "Olá! Como posso ajudar hoje?",
    "Sou a ContAI, como posso ajudar?",
    "O que você deseja analisar hoje?",
    "O que você precisa para hoje?",
    "Qual sua dúvida? Eu posso ajudar."
]

# -------------------------------------------------------------
# MENU LATERAL (FALTAVA!)
# -------------------------------------------------------------
menu = st.sidebar.radio(
    "Escolha uma funcionalidade:",
    ["Consultar ContAI", "Validar XML de NF-e"]
)

# -------------------------------------------------------------
# FUNÇÃO IA – OPENAI OFICIAL
# -------------------------------------------------------------
def consultar_ia(pergunta: str) -> str:
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é uma IA da Turing Tecnologia especializada em Direito Tributário do Distrito Federal. "
                        "Responda com precisão, clareza e sempre com base legal. "
                        "Se faltar a base legal, deixe claro para o usuário."
                    )
                },
                {"role": "user", "content": pergunta},
            ]
        )
        return resposta.choices[0].message.content

    except Exception as e:
        return f"Erro ao consultar a IA: {e}"

# -------------------------------------------------------------
# FUNÇÃO – VALIDAR XML
# -------------------------------------------------------------
def validar_xml(xml_file):
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

        tabela_icms = {"5101": "18", "5102": "18", "6102": "12"}
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
# ABA 1 – CONSULTAR IA (ENTER + BOTÃO À DIREITA)
# -------------------------------------------------------------
if menu == "Consultar ContAI":

    st.markdown(
        f"""
        <p style="text-align:center; font-size:18px; opacity:0.85;">
            {random.choice(frases_iniciais)}
        </p>
        """,
        unsafe_allow_html=True
    )

    if "pergunta" not in st.session_state:
        st.session_state.pergunta = ""

    nova_pergunta = st.text_area(
        "",
        value=st.session_state.pergunta,
        placeholder="Digite sua pergunta...",
        height=70,
        key="pergunta_input"
    )

    enviou_por_enter = False
    if len(nova_pergunta) > len(st.session_state.pergunta):
        if nova_pergunta.endswith("\n"):
            enviou_por_enter = True

    st.session_state.pergunta = nova_pergunta

    # Layout da caixa + botão perfeitamente alinhados
st.markdown(
    """
    <style>
        .input-button-container {
            display: flex;
            width: 100%;
            gap: 0px;  /* sem espaço entre caixa e botão */
        }
        .input-button-container textarea {
            border-radius: 6px 0px 0px 6px !important;
        }
        .send-button button {
            height: 70px;
            border-radius: 0px 6px 6px 0px !important;
            margin-left: 0px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Criar layout horizontal perfeito
caixa, botao = st.columns([10, 1])

with caixa:
    nova_pergunta = st.text_area(
        "",
        value=st.session_state.pergunta,
        placeholder="Digite sua pergunta...",
        height=70,
        key="pergunta_input"
    )

with botao:
    enviar = st.button("Enviar", use_container_width=True)

    if enviar or enviou_por_enter:
        pergunta = st.session_state.pergunta.strip()

        if pergunta == "":
            st.warning("Digite uma pergunta antes de consultar.")
        else:
            with st.spinner("Consultando..."):
                resposta = consultar_ia(pergunta)
            st.write(resposta)

        st.session_state.pergunta = st.session_state.pergunta.rstrip("\n")

# -------------------------------------------------------------
# RODAPÉ
# -------------------------------------------------------------
st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)

footer_html = """
<div style="
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    text-align: center;
    padding: 8px 0;
    font-size: 12px;
    color: rgba(250, 250, 250, 0.7);
    background-color: rgba(14, 17, 23, 0.95);
    z-index: 999;
">
    Desenvolvido pela Turing Tecnologia
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

