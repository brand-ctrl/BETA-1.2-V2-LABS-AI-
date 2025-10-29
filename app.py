src = Path("/mnt/data/app.py")
dst_dir = Path("/mnt/data/app_header_reduced")
dst_dir.mkdir(exist_ok=True)

# Ler o conteúdo
content = src.read_text(encoding="utf-8")

# Novo bloco com logo menor (300px), alinhada à esquerda, e sem header branca
new_block = '''
st.markdown("""
<style>
/* === RESET GERAL === */
body,[class*="css"]{background:#f9fafb;color:#111;font-family:'Inter',sans-serif;margin:0;padding:0;}
header, .stApp header, .stApp [data-testid="stHeader"], .block-container {
    background:none !important;
    box-shadow:none !important;
    border:none !important;
}

/* === HEADER PERSONALIZADO === */
.v2-header-wrap{
    display:flex;
    align-items:center;
    justify-content:flex-start;
    padding:22px 45px 8px 45px;
    margin:0;
}
.v2-header img{
    width:300px;  /* Reduzido de 400px para 300px */
    height:auto;
    transition:.25s ease-in-out;
}
.v2-header img:hover{transform:scale(1.04);}
@media(max-width:768px){
    .v2-header-wrap{justify-content:center;padding:15px 0;}
    .v2-header img{width:65vw;}
}

/* === ELEMENTOS GERAIS === */
.v2-title{font-size:clamp(20px,3.4vw,36px);font-weight:800;color:#1e3a8a;margin:0;}
.v2-sub{font-size:clamp(13px,1.8vw,18px);color:#4b5563;margin-bottom:22px;}
.v2-card{display:flex;align-items:center;gap:16px;padding:20px;border-radius:16px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.04);margin-bottom:18px;}
.v2-icon img{width:70px;}
.v2-btn{background:#1e3a8a;color:#fff;padding:9px 16px;border-radius:8px;font-weight:600;border:none;cursor:pointer;}
.v2-btn:hover{background:#3743b0;}
.hr{height:1px;background:#e5e7eb;margin:18px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="v2-header-wrap fade-in">
  <div class="v2-header">
    <img src="assets/logo_v2labs.svg">
  </div>
</div>
""", unsafe_allow_html=True)
'''

# Substituir bloco antigo
pattern = re.compile(
    r'st\.markdown\("""<style>.*?</style>""", unsafe_allow_html=True\)\s*st\.markdown\("""<div class="v2-header-wrap fade-in">.*?</div>""", unsafe_allow_html=True\)',
    re.S
)
content_new = re.sub(pattern, new_block, content)

# Gravar novo arquivo
dst_file = dst_dir / "app.py"
dst_file.write_text(content_new, encoding="utf-8")

# Compactar em zip
zip_path = "/mnt/data/app_header_reduced.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(dst_file, "app.py")

zip_path
