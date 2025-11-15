import os
import streamlit as st
import xml.etree.ElementTree as ET
from openai import OpenAI

# -------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
APP_PASSWORD = os.getenv("APP_PASSWORD", "trocar-senha")

st.set_page_config(
    page_title="IA Tributária DF – Turing Tecnologia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar elementos padrão do Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# -------------------------------------------------------------
# TELA DE SENHA (ANTES DE TUDO)
# -------------------------------------------------------------
st.title("IA Tributária DF – Turing Tecnologia")

senha = st.text_input(
    "Acesso restrito – digite a senha:",
    type="password",
    help="Informe a senha fornecida pela Turing Tecnologia."
)

if senha != APP_PASSWORD:
    st.stop()

st.write("---")


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
                        "Responda com precisão, clareza e base legal sempre que possível."
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
    ["Fazer Pergunta Tributária", "Validar XML de NF-e"]
)


# -------------------------------------------------------------
# ABA 1 – PERGUNTAS TRIBUTÁRIAS
# -------------------------------------------------------------
if menu == "Fazer Pergunta Tributária":
    st.subheader("Perguntas Tributárias – Distrito Federal")

    pergunta = st.text_area(
        "Digite sua dúvida:",
        placeholder="Ex.: Qual a alíquota de ICMS na prestação de serviço de transporte de cargas no DF?",
        height=150
    )

    if st.button("Consultar"):
        if pergunta.strip() == "":
            st.warning("Digite uma pergunta antes de consultar.")
        else:
            with st.spinner("Consultando IA..."):
                resposta = consultar_ia(pergunta)
            st.markdown("### Resposta")
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
st.markdown("---")
st.caption("IA Tributária DF • Desenvolvido pela Turing Tecnologia")
