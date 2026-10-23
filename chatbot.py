
import os
import uuid
import json
import streamlit as st

from groq import Groq
from dotenv import load_dotenv

from database import (
    salvar_conversa,
    carregar_conversas,
    excluir_conversa
)


# ==================================================
# 1. CONFIGURAÇÃO
# ==================================================

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

MODELO = "openai/gpt-oss-120b"

st.set_page_config(
    page_title="Chatbot IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# 2. ESTILO VISUAL
# ==================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #081321, #101d30);
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background-color: #101d30;
    border-right: 1px solid #263950;
}

h1, h2, h3, p, label {
    color: #f1f5f9;
}

.stChatMessage {
    border: 1px solid #263950;
    border-radius: 16px;
    padding: 16px;
}

.stChatInput textarea {
    color: #ffffff;
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 10px;
    border: 1px solid #315478;
    transition: 0.2s;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #38bdf8;
    color: #38bdf8;
}

.status-online {
    color: #34d399;
    font-weight: bold;
}

div[data-testid="stMetric"] {
    background: #14253b;
    border: 1px solid #263950;
    padding: 16px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. FUNÇÕES
# ==================================================

def criar_nova_conversa():
    return {
        "id": str(uuid.uuid4()),
        "titulo": "Nova conversa",
        "mensagens": []
    }


def obter_conversa():
    for conversa in st.session_state.conversas:
        if conversa["id"] == st.session_state.conversa_atual:
            return conversa

    # Se a conversa atual não existir, cria outra
    conversa = criar_nova_conversa()
    st.session_state.conversas.insert(0, conversa)
    st.session_state.conversa_atual = conversa["id"]

    return conversa


def nova_conversa():
    conversa = criar_nova_conversa()

    st.session_state.conversas.insert(0, conversa)
    st.session_state.conversa_atual = conversa["id"]
    st.session_state.secao = "Chat"


def salvar_se_existir(conversa):
    # Não grava conversas vazias no banco
    if conversa["mensagens"]:
        salvar_conversa(conversa)


# ==================================================
# 4. INICIALIZAÇÃO DO HISTÓRICO
# ==================================================

if "conversas" not in st.session_state:
    st.session_state.conversas = carregar_conversas()

    if not st.session_state.conversas:
        st.session_state.conversas = [
            criar_nova_conversa()
        ]

    st.session_state.conversa_atual = (
        st.session_state.conversas[0]["id"]
    )

if "instrucao_ia" not in st.session_state:
    st.session_state.instrucao_ia = (
        "Você é um assistente virtual inteligente, "
        "educado e útil. Responda em português brasileiro "
        "por padrão. Explique assuntos com clareza e "
        "adapte suas respostas ao nível de conhecimento "
        "do usuário."
    )

if "temperatura" not in st.session_state:
    st.session_state.temperatura = 0.7

if "secao" not in st.session_state:
    st.session_state.secao = "Chat"


# ==================================================
# 5. CLIENTE GROQ
# ==================================================

client = None

if API_KEY:
    client = Groq(api_key=API_KEY)


# ==================================================
# 6. MENU LATERAL
# ==================================================

with st.sidebar:
    st.markdown("# 🤖 Chatbot IA")
    st.caption("Seu assistente virtual pessoal")

    st.markdown("---")

    if st.button(
        "＋ Nova conversa",
        use_container_width=True
    ):
        nova_conversa()
        st.rerun()

    st.markdown("### Navegação")

    secao = st.radio(
        "Menu principal",
        ["Chat", "Histórico", "Configurações"],
        label_visibility="collapsed",
        key="menu_navegacao"
    )

    st.session_state.secao = secao

    st.markdown("---")
    st.markdown("### Conversas recentes")

    for conversa_item in st.session_state.conversas[:6]:
        titulo = conversa_item["titulo"]

        if len(titulo) > 27:
            titulo = titulo[:27] + "..."

        if st.button(
            "💬 " + titulo,
            key="conv_" + conversa_item["id"],
            use_container_width=True
        ):
            st.session_state.conversa_atual = (
                conversa_item["id"]
            )
            st.session_state.secao = "Chat"
            st.rerun()

    st.markdown("---")

    if client:
        st.markdown(
            '<p class="status-online">● IA configurada</p>',
            unsafe_allow_html=True
        )
    else:
        st.warning("Configure sua chave da Groq.")

    st.caption("Powered by Groq")


# ==================================================
# 7. PÁGINA DE CONFIGURAÇÕES
# ==================================================

if st.session_state.secao == "Configurações":

    st.title("⚙️ Configurações")
    st.write("Personalize o comportamento da sua IA.")

    st.session_state.instrucao_ia = st.text_area(
        "Personalidade e instruções da IA",
        value=st.session_state.instrucao_ia,
        height=180,
        help="Defina como sua IA deve responder."
    )

    st.session_state.temperatura = st.slider(
        "Criatividade das respostas",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperatura,
        step=0.1
    )

    st.info(
        "Valores menores tendem a produzir respostas "
        "mais previsíveis. Valores maiores permitem "
        "mais variedade."
    )

    if st.button("Restaurar configurações padrão"):
        st.session_state.instrucao_ia = (
            "Você é um assistente virtual inteligente, "
            "educado e útil. Responda em português brasileiro "
            "por padrão. Explique assuntos com clareza e "
            "adapte suas respostas ao nível de conhecimento "
            "do usuário."
        )

        st.session_state.temperatura = 0.7
        st.rerun()


# ==================================================
# 8. PÁGINA DE HISTÓRICO
# ==================================================

elif st.session_state.secao == "Histórico":

    st.title("📚 Histórico de conversas")
    st.write("Abra, exporte ou exclua suas conversas.")

    if not st.session_state.conversas:
        st.info("Você ainda não possui conversas.")

    else:
        for conversa_item in st.session_state.conversas:

            with st.container(border=True):

                st.subheader(conversa_item["titulo"])

                quantidade = len(
                    conversa_item["mensagens"]
                )

                st.caption(f"{quantidade} mensagens")

                col1, col2, col3 = st.columns([2, 1, 2])

                with col1:
                    if st.button(
                        "Abrir conversa",
                        key="abrir_" + conversa_item["id"],
                        use_container_width=True
                    ):
                        st.session_state.conversa_atual = (
                            conversa_item["id"]
                        )
                        st.session_state.secao = "Chat"
                        st.rerun()

                with col2:
                    if st.button(
                        "Excluir",
                        key="excluir_" + conversa_item["id"],
                        use_container_width=True
                    ):
                        excluir_conversa(conversa_item["id"])

                        st.session_state.conversas = [
                            c for c in st.session_state.conversas
                            if c["id"] != conversa_item["id"]
                        ]

                        if (
                            st.session_state.conversa_atual
                            == conversa_item["id"]
                        ):
                            conversa_nova = criar_nova_conversa()
                            st.session_state.conversas.insert(
                                0, conversa_nova
                            )
                            st.session_state.conversa_atual = (
                                conversa_nova["id"]
                            )

                        st.rerun()

                with col3:
                    st.download_button(
                        "📥 Exportar JSON",
                        data=json.dumps(
                            conversa_item["mensagens"],
                            ensure_ascii=False,
                            indent=2
                        ),
                        file_name=(
                            f"conversa_{conversa_item['id'][:8]}.json"
                        ),
                        mime="application/json",
                        key="exportar_" + conversa_item["id"],
                        use_container_width=True
                    )


# ==================================================
# 9. PÁGINA PRINCIPAL DO CHAT
# ==================================================

else:

    conversa = obter_conversa()

    col_titulo, col_status = st.columns([4, 1])

    with col_titulo:
        st.title("🤖 Chatbot IA")
        st.caption(
            "Converse, aprenda e explore ideias com inteligência artificial."
        )

    with col_status:
        if client:
            st.success("IA conectada")
        else:
            st.error("API não configurada")

    st.markdown("---")

    # MENSAGEM INICIAL E SUGESTÕES
    if not conversa["mensagens"]:

        st.markdown("### Olá! 👋")

        st.write(
            "Sou seu assistente virtual. Pergunte sobre "
            "programação, estudos, tecnologia ou outros assuntos."
        )

        st.markdown("#### Experimente perguntar:")

        sugestoes = [
            "Explique Python para iniciantes",
            "Crie um código Python simples",
            "Me ajude a organizar meus estudos"
        ]

        colunas = st.columns(3)

        for i, sugestao in enumerate(sugestoes):

            with colunas[i]:

                if st.button(
                    sugestao,
                    key=f"sugestao_{i}"
                ):
                    st.session_state.pergunta_sugerida = sugestao
                    st.rerun()

    # EXIBIR AS MENSAGENS ANTERIORES
    for mensagem in conversa["mensagens"]:

        with st.chat_message(
            mensagem["role"],
            avatar=(
                "🤖"
                if mensagem["role"] == "assistant"
                else "👤"
            )
        ):
            st.markdown(mensagem["content"])

    # CAMPO DE TEXTO
    pergunta = st.chat_input("Digite sua mensagem...")

    # Recupera uma sugestão clicada
    if (
        not pergunta
        and "pergunta_sugerida" in st.session_state
    ):
        pergunta = st.session_state.pop("pergunta_sugerida")

    # PROCESSAR A PERGUNTA
    if pergunta:

        if not client:
            st.error(
                "Configure GROQ_API_KEY no arquivo .env "
                "para conversar com a IA."
            )
            st.stop()

        # SALVAR A PERGUNTA
        conversa["mensagens"].append({
            "role": "user",
            "content": pergunta
        })

        if conversa["titulo"] == "Nova conversa":
            conversa["titulo"] = pergunta[:35]

        salvar_se_existir(conversa)

        with st.chat_message("user", avatar="👤"):
            st.markdown(pergunta)

        # CONSULTAR A IA
        with st.chat_message("assistant", avatar="🤖"):

            with st.spinner("A IA está pensando..."):

                try:

                    mensagens_api = [
                        {
                            "role": "system",
                            "content": st.session_state.instrucao_ia
                        }
                    ] + conversa["mensagens"]

                    resposta = client.chat.completions.create(
                        model=MODELO,
                        messages=mensagens_api,
                        temperature=st.session_state.temperatura
                    )

                    texto = (
                        resposta.choices[0].message.content
                        or "Não recebi uma resposta em texto."
                    )

                    st.markdown(texto)

                    # SALVAR A RESPOSTA
                    conversa["mensagens"].append({
                        "role": "assistant",
                        "content": texto
                    })

                    salvar_se_existir(conversa)

                except Exception as erro:

                    st.error(
                        "Não foi possível consultar a IA. "
                        "Confira sua conexão, sua chave e "
                        "a mensagem de erro abaixo."
                    )

                    st.caption(str(erro))

