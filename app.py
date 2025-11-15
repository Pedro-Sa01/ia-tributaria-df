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

/* ============================================= */
/* 1) Remover todos os ícones do Streamlit        */
/* ============================================= */

header [data-testid="stToolbarActions"] {
    display: none !important;
}

header [data-testid="stMainMenu"] {
    display: none !important;
}

/* ============================================= */
/* 2) Garantir que o header continue existindo    */
/* ============================================= */

header {
    visibility: visible !important;
    height: auto !important;
}

/* ============================================= */
/* 3) Botão de colapsar/expandir sempre visível   */
/* ============================================= */

[data-testid="stSidebarCollapseButton"] {
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
    transition: none !important;
}

[data-testid="stSidebarCollapseButton"] span {
    opacity: 1 !important;
}

[data-testid="stExpandSidebarButton"] {
    opacity: 1 !important;
    visibility: visible !important;
    display: flex !important;
}

[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
    opacity: 1 !important;
}

/* ============================================= */
/* 4) Ocultar botão "Manage app" do rodapé        */
/* ============================================= */

button[data-testid="manage-app-button"] {
    display: none !important;
    visibility: hidden !important;
}

/* Remover botão "Manage app" fora do iframe */
button[data-testid="manage-app-button"],
._terminalButton_rix23_138 {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* REMOVER selo do Streamlit e avatar do autor */
a[class*="_viewerBadge"],
div[class*="_profileContainer"],
div[class*="_profilePreview"],
img[data-testid="appCreatorAvatar"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
    pointer-events: none !important;
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
# CAPTURAR TECLA ENTER (ENVIO AUTOMÁTICO)
# -------------------------------------------------------------
enter_js = """
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === "Enter") {
        window.parent.postMessage({type: "ENTER_PRESSED"}, "*");
    }
});
</script>
"""
st.markdown(enter_js, unsafe_allow_html=True)

# Escutar mensagens do frontend
js_event = st.experimental_get_query_params().get("js_event", [None])[0]
if js_event:
    handle_js_event()

# Ouvir evento do front-end
def handle_js_event():
    if st.session_state.get("js_event") == "ENTER_PRESSED":
        st.session_state.enter_pressed = True

st.session_state.enter_pressed = False

# -------------------------------------------------------------
# MENU LATERAL
# -------------------------------------------------------------
menu = st.sidebar.radio(
    "Escolha uma funcionalidade:",
    ["Consultar ContAI", "Validar XML de NF-e"]
)

# -------------------------------------------------------------
# LOGO CENTRALIZADO NO TOPO
# -------------------------------------------------------------
top_col1, top_col2, top_col3 = st.columns([1, 2, 1])

with top_col2:
    try:
        st.image("turing_logo.png", use_column_width=False)
    except Exception:
    # Se a imagem não existir, não quebra o app
    st.markdown(
        "<h2 style='text-align:center; margin-top: 10px;'>Turing Tecnologia</h2>",
        unsafe_allow_html=True
    )

# -------------------------------------------------------------
# HEADER – TURING TECNOLOGIA NO TOPO (SEM POLUIR)
# -------------------------------------------------------------
st.markdown(
    """
    <div style="
        width: 100%;
        text-align: center;
        margin-top: -15px;
        margin-bottom: 10px;
        font-size: 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: rgba(250, 250, 250, 0.85);
    ">
        Turing Tecnologia
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# ABA 1 – PERGUNTAS TRIBUTÁRIAS
# -------------------------------------------------------------
if menu == "Consultar ContAI":

    # Frase inicial estilo ChatGPT
    st.markdown(
        f"""
        <p style="text-align:center; font-size:18px; opacity:0.85; margin-top:5px;">
            {random.choice(frases_iniciais)}
        </p>
        """,
        unsafe_allow_html=True
    )

    # Ajuste automático do text_area
    if "pergunta" not in st.session_state:
        st.session_state.pergunta = ""

    pergunta = st.text_area(
        "",
        value=st.session_state.pergunta,
        placeholder="Digite sua pergunta...",
        height=70,
        key="pergunta_input"
    )

    col_enviar, col_vazio = st.columns([1, 8])
    with col_enviar:
        enviar = st.button("Enviar")

    # ENTER envia automaticamente
    if st.session_state.pergunta != pergunta:
        st.session_state.pergunta = pergunta

    if enviar or st.session_state.get("enter_pressed", False):

        if pergunta.strip() == "":
            st.warning("Digite uma pergunta antes de consultar.")
        else:
            with st.spinner("Consultando..."):
                resposta = consultar_ia(pergunta)
            st.write(resposta)

        st.session_state.enter_pressed = False

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


# Espaço final para não esconder conteúdo atrás do rodapé
st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)

# Rodapé fixo e centralizado
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
















