# ==== Base de Layout SaaS (não altera sua estrutura de navegação) ====
import streamlit as st
from contextlib import contextmanager

# Paleta/estilo leve — compatível com tema claro/escuro do Streamlit
_SAAS_CSS = """
<style>
:root{
  --radius:16px; --gap:1rem; --maxw:1200px;
  --surface:rgba(255,255,255,.65); --border:rgba(0,0,0,.06);
  --muted:rgba(0,0,0,.55);
}
.block-container{max-width:var(--maxw)!important;padding-top:1.1rem!important}
.saas-topbar{
  display:flex;align-items:center;gap:.75rem;justify-content:space-between;
  background:var(--surface);border:1px solid var(--border);
  padding:.6rem .9rem;border-radius:14px;margin-bottom:.75rem;
  backdrop-filter:saturate(140%) blur(6px);
}
.saas-topbar .brand{display:flex;align-items:center;gap:.6rem}
.saas-topbar img{height:24px;width:24px;display:block}
.saas-topbar .title{font-weight:600;letter-spacing:.1px}
.saas-topbar .meta{font-size:.85rem;opacity:.85}
.saas-section{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:1rem;margin:.5rem 0;
}
.saas-grid{
  display:grid;gap:var(--gap);
  grid-template-columns:repeat(auto-fit,minmax(var(--mincol,280px),1fr));
}
.saas-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:1rem;}
.saas-muted{color:var(--muted)}
@media (max-width:640px){
  :root{--gap:.75rem;--maxw:100%}
  .block-container{padding-left:.8rem!important;padding-right:.8rem!important}
}
@media (prefers-color-scheme:dark){
  :root{--surface:rgba(0,0,0,.25);--border:rgba(255,255,255,.08)}
}
</style>
"""

def bootstrap_saas_ui(title: str = "V2 LABS AI", subtitle: str | None = None):
    """
    Injeta CSS e exibe uma topbar estilo SaaS.
    Não altera sua navegação nem os módulos existentes.
    Use uma única vez no início do render (Etapa 2 eu mostro onde chamar).
    """
    st.markdown(_SAAS_CSS, unsafe_allow_html=True)
    topbar = f"""
    <div class="saas-topbar">
      <div class="brand">
        <img src="assets/logo_v2labs.svg" alt="logo"/>
        <div class="title">{title}</div>
      </div>
      <div class="meta">{subtitle or "Beta 1.1"}</div>
    </div>
    """
    st.markdown(topbar, unsafe_allow_html=True)

@contextmanager
def saas_section(title: str | None = None, subtitle: str | None = None):
    """
    Container de seção (card grande) para envolver conteúdos da página,
    mantendo a aparência SaaS. Ex.: 
        with saas_section("Conversor"):
            render_conversor()
    """
    st.markdown('<div class="saas-section">', unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**" + (f"<br><span class='saas-muted'>{subtitle}</span>" if subtitle else ""), unsafe_allow_html=True)
        st.markdown("---")
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

@contextmanager
def saas_grid(min_col_px: int = 300):
    """
    Grid responsiva para cards internos. Ex.:
        with saas_grid(320):
            saas_card(lambda: render_extrator(), "Extrair Imagens")
            saas_card(lambda: render_removedor(), "Removedor de Fundo")
    """
    st.markdown(f"<div class='saas-grid' style='--mincol:{min_col_px}px;'>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

def saas_card(render_fn, title: str | None = None, subtitle: str | None = None):
    """
    Card utilitário para pequenos blocos de UI. Passe uma função que desenha o conteúdo.
    """
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**" + (f"<br><span class='saas-muted'>{subtitle}</span>" if subtitle else ""), unsafe_allow_html=True)
        st.markdown("---")
    render_fn()
    st.markdown("</div>", unsafe_allow_html=True)
# ==== /Base de Layout SaaS ====
