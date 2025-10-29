
import streamlit as st


}
.v2-header{ display:flex; align-items:center; justify-content:flex-start; padding:18px 6% 4px; }
.v2-header img{ width:300px; height:auto; display:block; }
.block-container{ padding-top:0 !important; max-width:1280px; }
h1,h2,h3{ font-weight:800; letter-spacing:.4px; margin:0 0 10px; }
.hr{ border:0; border-top:1px solid var(--line); margin: 14px 0 18px; }
.v2-card{ display:flex; gap:16px; align-items:center; padding:16px; border-radius:18px;
         background: rgba(173,216,255,.30);
         box-shadow: 0 10px 26px rgba(173,216,255,.18); }
.v2-card:hover{ box-shadow: 0 12px 30px rgba(173,216,255,.26); transform: translateY(-1px); }
.v2-icon{ width:94px; height:94px; display:flex; align-items:center; justify-content:center; border-radius:16px;
          background: rgba(21,170,255,.10); flex:0 0 94px; }
.v2-icon img{ width:64px; height:64px; object-fit:contain; }
.v2-title{ margin:0; font-size:18px; font-weight:800; color:var(--ink); }
.v2-desc{ margin:2px 0 0; color:#445267; font-size:14px; }
.v2-btn .stButton>button{ border-radius:10px; }
.section{ margin:10px 6%; }
</style>
<div class="v2-header">
  <img src="assets/logo_v2labs.svg" alt="V2 Labs">
</div>
""", unsafe_allow_html=True)

route = st.session_state.get("route","home")

if route == "home":
    st.markdown('<div class="section"><h2>FERRAMENTAS</h2></div>', unsafe_allow_html=True)
    def card(icon, title, desc, btn_label, key):
        st.markdown('<div class="section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,6,2])
        with col1:
            st.markdown(f'<div class="v2-icon"><img src="{icon}"></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="v2-card"><div class="v2-icon"><img src="{icon}"></div>'
                        f'<div><p class="v2-title">{title}</p><p class="v2-desc">{desc}</p></div></div>', unsafe_allow_html=True)
        with col3:
            if st.button(btn_label, key=key, use_container_width=True):
                st.session_state.route = key
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    card("assets/icon_conversor.svg","CONVERSOR DE IMAGENS",
         "Redimensione para 1080×1080 ou 1080×1920 preenchendo com cor.",
         "Abrir Conversor","conversor")

    card("assets/icon_extrator.svg","EXTRATOR DE IMAGENS CSV",
         "Baixe imagens diretamente de URLs listadas em um arquivo CSV.",
         "Abrir Extrator CSV","extrator")

    card("assets/icon_removedor.svg","REMOVEDOR DE FUNDO",
         "Remova fundos em lote com preview antes/depois e PNG de alta qualidade.",
         "Abrir Removedor de Fundo","removedor")

elif route == "conversor":
    from modules.conversor_imagem import render
    render(ping_b64="")
elif route == "extrator":
    from modules.extrair_imagens_csv import render
    render(ping_b64="")
elif route == "removedor":
    from modules.removedor_fundo import render
    render(ping_b64="")
