import os
import streamlit as st
import xml.etree.ElementTree as ET
from openai import OpenAI

# -------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------------------------------

# Lê a chave da OpenAI e a senha do app das variáveis do Streamlit Cloud
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
APP_PASSWORD = os.getenv("APP_PASSWORD", "trocar-senha")

# Configurações da página
st.set_page_config(page_title="IA Tributária DF – Turing Tecnologia", layout="wide")
st.title("⚖️ IA Tributária DF – Turing Tecnologia")


# -------------------------------------------------------------
# BLOQUEIO POR SENHA (Controle de acesso simples)
# -------------------------------------------------------------
with st.sidebar:
    st.subheader("Acesso restrito")
    senha = st.text_input("Digite a senha:", type="password")

if senha != APP_PASSWORD:
    st.warning("🔒 Acesso negado. Digite a senha correta para continuar.")
    st.stop()


# -------------------------------------------------------------
# FUNÇÃO PARA CHAMAR A IA (API NOVA DA OPENAI)
# -------------------------------------------------------------
def consultar_ia(pergunta: str) -> str:
    """Envia a pergunta para a IA e retorna a resposta usando a API nova da OpenAI."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é uma IA da Turing Tecnologia, especializada em Direito Tributário do Distrito Federal. "
                        "Responda de forma objetiva, cite a legislação relevante quando possível e indique quando a "
                        "informação depender de interpretação."
                    )
                },
                {"role": "user", "content": pergunta},
            ]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        return f"❌ Erro ao consultar a IA: {e}"


# -------------------------------------------------------------
# FUNÇÃO PARA VALIDAR XML DE NF-e (MVP)
# -------------------------------------------------------------
def validar_xml(xml_file):
    """Validação simples de CFOP e ICMS em um XML de NF-e (MVP)."""
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

        # Tabela de exemplo (apenas MVP)
        tabela_icms = {
            "5101": "18",
            "5102": "18",
            "6102": "12"
        }

        esperado = tabela_icms.get(cfop, "Não mapeado")

        if esperado == "Não mapeado":
            resultado = f"⚠️ CFOP {cfop} não está mapeado no MVP."
        elif esperado == icms:
            resultado = f"✅ ICMS correto ({icms}%)."
        else:
            resultado = f"❌ Divergência: esperado {esperado}%, encontrado {icms}%."

        return {
            "Produto": produto,
            "CFOP": cfop,
            "ICMS informado": icms,
            "ICMS esperado": esperado,
            "Resultado": resultado
        }

    except Exception as e:
        return {"Erro": f"Não foi possível ler o XML: {e}"}


# -------------------------------------------------------------
# INTERFACE (MENU LATERAL)
# -------------------------------------------------------------
menu = st.sidebar.radio(
    "Escolha uma opção:",
    ["💬 Fazer Pergunta à IA", "📂 Validar XML de NF-e"]
)


# -------------------------------------------------------------
# ABA 1 – IA TRIBUTÁRIA
# -------------------------------------------------------------
if menu == "💬 Fazer Pergunta à IA":
    st.subheader("💬 Perguntas Tributárias – DF")

    pergunta = st.text_area(
        "Digite sua dúvida tributária:",
        placeholder="Ex.: Qual a alíquota de ISS para consultoria no DF?",
        height=150
    )

    if st.button("Consultar IA"):
        if pergunta.strip() == "":
            st.warning("Digite uma pergunta antes de enviar.")
        else:
            with st.spinner("Consultando IA..."):
                resposta = consultar_ia(pergunta)

            st.markdown("### 📌 Resposta da IA")
            st.write(resposta)


# -------------------------------------------------------------
# ABA 2 – VALIDAÇÃO DE XML
# -------------------------------------------------------------
elif menu == "📂 Validar XML de NF-e":
    st.subheader("📂 Validação simples de XML – MVP")

    arquivo = st.file_uploader("Selecione um arquivo XML", type=["xml"])

    if arquivo is not None:
        with st.spinner("Analisando XML..."):
            resultado = validar_xml(arquivo)

        st.markdown("### 📊 Resultado da Análise")
        for chave, valor in resultado.items():
            st.write(f"**{chave}:** {valor}")


# Rodapé
st.markdown("---")
st.caption("MVP IA Tributária DF • Desenvolvido pela Turing Tecnologia 💼")
