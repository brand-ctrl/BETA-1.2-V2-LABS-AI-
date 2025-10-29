# layout_responsivo_app.py
# -----------------------------------------------------------
# App Streamlit com layout responsivo (mobile-first), autônomo.
# Basta rodar: streamlit run layout_responsivo_app.py
# -----------------------------------------------------------

from contextlib import contextmanager
import streamlit as st
import time
import pandas as pd

# ------------------------- Config --------------------------
st.set_page_config(page_title="Layout Responsivo", page_icon="🧩", layout="wide")

# -------------------------- CSS ----------------------------
_BASE_CSS = """
<style>
:root {
  --gap: 1rem;
  --radius: 16px;
  --maxw: 1200px; /* largura confortável em desktop */
  --card-bg: rgba(255,255,255,0.65);
  --card-border: rgba(0,0,0,0.05);
}
.block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2rem !important;
  max-width: var(--maxw) !important;
}

/* Tipografia principal */
h1.page-title {
  font-size: clamp(1.35rem, 2.4vw, 2rem);
  line-height: 1.15;
  margin: 0 0 0.75rem 0;
  letter-spacing: -0.2px;
}

/* Grid utilitária (auto-fit) */
.resp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(var(--mincol, 280px), 1fr));
  gap: var(--gap);
  margin: 0.25rem 0 0.5rem 0;
}

/* Card base */
.resp-card, .stMarkdown, .stDataFrame, .stPlotlyChart, .stAltairChart, .stImage, .stMetric, .stTable {
  background: var(--card-bg);
  backdrop-filter: saturate(140%) blur(6px);
  border-radius: var(--radius);
  padding: 1rem;
  margin: 0.4rem 0;
  border: 1px solid var(--card-border);
}

/* Colapsa padding lateral em telas bem pequenas */
@media (max-width: 640px) {
  :root { --gap: 0.75rem; --maxw: 100%; }
  .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
}

/* Tema escuro */
@media (prefers-color-scheme: dark) {
  :root {
    --card-bg: rgba(0,0,0,0.25);
    --card-border: rgba(255,255,255,0.08);
  }
}

/* Botões alinhados */
.btn-row {
  display: flex; gap: .5rem; flex-wrap: wrap;
}
</style>
"""

def _inject_css():
    st.markdown(_BASE_CSS, unsafe_allow_html=True)

@contextmanager
def render_layout(page_title: str | None = None, subtitle: str | None = None):
    """Context manager para padronizar o topo da página."""
    _inject_css()
    if page_title:
        st.markdown(f"<h1 class='page-title'>{page_title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)
    with st.container():
        yield

@contextmanager
def make_grid(min_col_px: int = 300):
    """Abre uma grade responsiva. Dentro, use `card()` para criar cartões."""
    st.markdown(f"<div class='resp-grid' style='--mincol:{min_col_px}px;'>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

def card(title: str | None = None, subtitle: str | None = None):
    """Cria um card estilizado e retorna um container para inserir conteúdo Streamlit."""
    st.markdown("<div class='resp-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**" + (f"<br><span style='opacity:.8'>{subtitle}</span>" if subtitle else ""), unsafe_allow_html=True)
        st.markdown("---")
    return st.container()

# --------------------------- UI ----------------------------
with st.sidebar:
    st.header("🧭 Navegação")
    page = st.radio(
        "Escolha uma seção:",
        ["Dashboard", "Uploads & Tabela", "Formulário & Ações"],
        index=0
    )
    st.markdown("---")
    st.caption("Layout responsivo: grid auto-fit, cards e estilo mobile-first.")

# ------------------------- Páginas -------------------------
if page == "Dashboard":
    with render_layout("📊 Dashboard", "Exemplo de cards métricos e gráfico tabular"):
        with make_grid(min_col_px=260):
            with card("Métricas Rápidas"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Conversões", "1.284", "+12%")
                col2.metric("Receita", "R$ 18.900", "+6%")
                col3.metric("Churn", "2,1%", "-0,3pp")

            with card("Tabela de Desempenho", "Dados simulados para visualização"):
                # dados de exemplo
                df = pd.DataFrame({
                    "Mês": ["Jul", "Ago", "Set", "Out"],
                    "Visitas": [12000, 14500, 13250, 15890],
                    "Conversões": [980, 1104, 1002, 1284],
                    "Receita (R$)": [15000, 16400, 17100, 18900],
                })
                st.dataframe(df, use_container_width=True)

            with card("Checklist"):
                a = st.checkbox("Ativar banner de campanha")
                b = st.checkbox("Sincronizar catálogo")
                c = st.checkbox("Liberar novo layout")
                st.success("Tudo pronto!") if all([a,b,c]) else st.info("Marque todas as opções para concluir.")

elif page == "Uploads & Tabela":
    with render_layout("📥 Uploads & Tabela", "Upload de arquivo e visualização organizada em grid"):
        with make_grid(min_col_px=320):
            with card("Upload de Arquivo", "CSV ou imagem para demonstração"):
                file = st.file_uploader("Solte aqui um CSV (ou imagem)", type=["csv", "png", "jpg", "jpeg"], accept_multiple_files=False)
                if file is not None:
                    if file.type == "text/csv":
                        df = pd.read_csv(file)
                        st.success(f"CSV carregado: {file.name}")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.image(file, caption=file.name, use_container_width=True)

            with card("Tabela Estática (Exemplo)"):
                df2 = pd.DataFrame(
                    [{"ID": i, "Status": "OK" if i % 2 == 0 else "Revisar"} for i in range(1, 13)]
                )
                st.dataframe(df2, use_container_width=True)

elif page == "Formulário & Ações":
    with render_layout("🧾 Formulário & Ações", "Exemplo de formulário simples + feedback visual"):
        with make_grid(min_col_px=300):
            with card("Formulário"):
                with st.form("form_demo", clear_on_submit=False):
                    nome = st.text_input("Nome")
                    email = st.text_input("Email")
                    qtd = st.number_input("Quantidade", min_value=1, max_value=100, value=5)
                    submitted = st.form_submit_button("Enviar")
                    if submitted:
                        st.success(f"Recebido: {nome} | {email} | qtd={qtd}")

            with card("Ações Rápidas"):
                st.markdown('<div class="btn-row">', unsafe_allow_html=True)
                colA, colB, colC = st.columns([1,1,1])
                with colA:
                    if st.button("Sincronizar"):
                        with st.spinner("Sincronizando..."):
                            time.sleep(1.2)
                        st.success("Sincronizado!")
                with colB:
                    if st.button("Reprocessar"):
                        with st.spinner("Reprocessando..."):
                            time.sleep(1.0)
                        st.info("Reprocesso concluído.")
                with colC:
                    if st.button("Publicar"):
                        with st.spinner("Publicando..."):
                            time.sleep(1.0)
                        st.success("Publicado com sucesso!")
                st.markdown('</div>', unsafe_allow_html=True)

# ------------------------ Rodapé ---------------------------
st.markdown("---")
st.caption("⚙️ Layout responsivo em Streamlit • Grid auto-fit • Cards com CSS leve • Compatível com tema claro/escuro")
