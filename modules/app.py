
import streamlit as st

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
