# app_saas.py
# -----------------------------------------------------------
# Layout SaaS responsivo para Streamlit, mantendo sua estrutura.
# - Usa topbar, seções e grid responsivas (mobile-first).
# - Mantém módulos existentes se disponíveis (conversor, extrair_imagens_csv, removedor_fundo).
# - Se algum módulo não existir, exibe um placeholder sem quebrar a navegação.
#
# Execute com: streamlit run app_saas.py
# -----------------------------------------------------------

import importlib
from contextlib import contextmanager
import streamlit as st

# ===================== Config básica =======================
st.set_page_config(
    page_title="V² Labs AI — SaaS UI",
    page_icon="🧩",
    layout="wide"
)

# ======================= CSS SaaS ==========================
_SAAS_CSS = """
<style>
:root{
  --radius:16px; --gap:1rem; --maxw:1200px;
  --surface:rgba(255,255,255,.65); --border:rgba(0,0,0,.06);
  --muted:rgba(0,0,0,.60);
}
.block-container{max-width:var(--maxw)!important;padding-top:1.1rem!important}
.saas-topbar{
  display:flex;align-items:center;gap:.75rem;justify-content:space-between;
  background:var(--surface);border:1px solid var(--border);
  padding:.65rem 1rem;border-radius:14px;margin-bottom:.8rem;
  backdrop-filter:saturate(140%) blur(6px);
}
.saas-topbar .brand{display:flex;align-items:center;gap:.6rem}
.saas-topbar .logo{
  height:24px;width:24px;display:flex;align-items:center;justify-content:center;
  border-radius:8px;border:1px solid var(--border);padding:2px;font-size:14px;
}
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
hr{border:none;border-top:1px solid var(--border);margin:.6rem 0 .9rem}

@media (max-width:640px){
  :root{--gap:.75rem;--maxw:100%}
  .block-container{padding-left:.8rem!important;padding-right:.8rem!important}
}
@media (prefers-color-scheme:dark){
  :root{--surface:rgba(0,0,0,.25);--border:rgba(255,255,255,.08)}
}
</style>
"""

def _inject_css():
    st.markdown(_SAA​S_CSS if False else _SAAS_CSS, unsafe_allow_html=True)  # micro-noise guard

def bootstrap_saas_ui(title: str = "V² Labs AI", subtitle: str | None = None):
    """Injeta CSS e topbar estilo SaaS (chamar 1x no início do render)."""
    _inject_css()
    topbar = f"""
    <div class="saas-topbar">
      <div class="brand">
        <div class="logo">🔷</div>
        <div class="title">{title}</div>
      </div>
      <div class="meta">{subtitle or "Beta"}</div>
    </div>
    """
    st.markdown(topbar, unsafe_allow_html=True)

@contextmanager
def saas_section(title: str | None = None, subtitle: str | None = None):
    """Container grande de seção."""
    st.markdown('<div class="saas-section">', unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**" + (f"<br><span class='saas-muted'>{subtitle}</span>" if subtitle else ""), unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

@contextmanager
def saas_grid(min_col_px: int = 300):
    """Grid responsiva para dispor cards."""
    st.markdown(f"<div class='saas-grid' style='--mincol:{min_col_px}px;'>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

def saas_card(render_fn, title: str | None = None, subtitle: str | None = None):
    """Card utilitário: recebe uma função que desenha o conteúdo."""
    st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**" + (f"<br><span class='saas-muted'>{subtitle}</span>" if subtitle else ""), unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
    try:
        render_fn()
    finally:
        st.markdown("</div>", unsafe_allow_html=True)

# =================== Descoberta de Módulos ==================
def _try_import(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None

# Tenta ambos formatos: "modules.nome" e "nome"
_MODS = {
    "Conversor": _try_import("modules.conversor") or _try_import("conversor"),
    "Extrair Imagens CSV": _try_import("modules.extrair_imagens_csv") or _try_import("extrair_imagens_csv"),
    "Removedor de Fundo": _try_import("modules.removedor_fundo") or _try_import("removedor_fundo"),
}

def _has_callable(mod, names=("app", "main", "render", "run")):
    if mod is None:
        return None
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    return None

_RENDERERS = {label: _has_callable(mod) for label, mod in _MODS.items()}

# ======================= Navegação ==========================
with st.sidebar:
    st.header("🧭 Navegação")
    pages = list(_MODS.keys())
    # Garante pelo menos uma página genérica
    if not pages:
        pages = ["Dashboard"]
    page = st.radio("Escolha uma seção:", pages, index=0)
    st.markdown("---")
    st.caption("UI SaaS • grid auto-fit • cards • mobile-first")

# ========================= Render ===========================
bootstrap_saas_ui(title="V² Labs AI", subtitle="SaaS UI • v1")

def _placeholder(name: str):
    st.info(
        f"🔧 A seção **{name}** ainda não encontrou um módulo com função `app`, `main`, `render` ou `run`.\n\n"
        f"➜ Crie/ajuste o módulo correspondente e exponha uma dessas funções para integrá-lo automaticamente."
    )

if page in _MODS:
    fn = _RENDERERS.get(page)
    with saas_section(page):
        if fn:
            # Renderiza o módulo dentro de uma seção padronizada
            try:
                fn()
            except Exception as e:
                st.error(f"Erro ao renderizar **{page}**: {e}")
        else:
            _placeholder(page)
else:
    # Página genérica "Dashboard" (fallback caso nenhum módulo exista)
    with saas_section("Dashboard", "Exemplo de organização em grid"):
        with saas_grid(300):
            saas_card(lambda: st.metric("Conversões", "1.284", "+12%"), "Métrica")
            saas_card(lambda: st.write("Carregue seus módulos para ver as páginas aqui."), "Bem-vindo")
            def _tips():
