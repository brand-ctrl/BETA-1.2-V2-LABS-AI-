import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rembg import remove, new_session
    _HAS_REMBG = True
except Exception:
    _HAS_REMBG = False


def _play_ping(ping_b64: str):
    st.markdown(f'<audio autoplay src="data:audio/wav;base64,{ping_b64}"></audio>', unsafe_allow_html=True)


def _remove_bg_bytes(img_bytes: bytes, session=None) -> bytes:
    return remove(img_bytes, session=session)


def render(ping_b64: str):
    # ====== CARREGAR IMAGEM COMO BASE64 ======
    banner_path = "assets/removedor_banner.png"
    try:
        with open(banner_path, "rb") as f:
            b64_banner = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        st.error("❌ Imagem de banner não encontrada em 'assets/removedor_banner.png'")
        st.stop()

    # ====== CSS GLOBAL ======
    st.markdown("""
    <style>
    body,[class*="css"] {
        background-color: #f9fafb !important;
        color: #111 !important;
        font-family: 'Inter', sans-serif;
    }
    .stApp header, .stApp [data-testid="stHeader"], .block-container {
        background: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* HERO SECTION */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-left: 10%;
        margin-top: 20px;
    }
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 32px;
        color: #111;
    }
    .hero {
        position: relative;
        width: 500px;
        height: 500px;
        border-radius: 20px;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .hero img.bg {
        width: 500px;
        height: 500px;
        object-fit: cover;
        border-radius: 18px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }

    /* EXPANDER E UPLOAD */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] button {
        color: #111 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stFileUploader"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
    }

    /* ALERT HARMONIZADO */
    .custom-alert {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        color: #111;
        font-size: 15px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ====== HERO SECTION ======
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">REMOVEDOR DE FUNDO</div>
        <div class="hero">
            <img src="data:image/png;base64,{b64_banner}" class="bg" alt="background">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ====== VERIFICAÇÃO DE BIBLIOTECA ======
    if not _HAS_REMBG:
        st.error("Biblioteca 'rembg' não encontrada. Instale com: pip install rembg onnxruntime")
        st.stop()

    # ====== CONFIGURAÇÕES ======
    with st.expander("⚙️ Configurações avançadas", expanded=False):
        model = st.selectbox(
            "Modelo",
            ("u2net_human_seg", "u2net", "isnet-general-use"),
            index=0,
            help="Escolha o modelo de recorte — o padrão é otimizado para pessoas."
        )
        st.caption("💡 Dica: 'u2net_human_seg' é ideal para retratos humanos.")

   # ====== UPLOAD ======
files = st.file_uploader(
    "📂 Envie imagens ou um arquivo ZIP",
    type=["jpg", "jpeg", "png", "webp", "zip"],
    accept_multiple_files=True
)
if not files:
    st.markdown('<div class="custom-alert">👆 Envie suas imagens acima para começar.</div>', unsafe_allow_html=True)
    st.stop()

INP, OUT = "rm_in", "rm_out"
shutil.rmtree(INP, ignore_errors=True)
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(INP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}

def _safe_write(base: Path, relpath: Path, data: bytes):
    """Garante que o arquivo será gravado dentro de `base` (evita zip-slip)."""
    dest = (base / relpath).resolve()
    if not str(dest).startswith(str(base.resolve())):
        # caminho malicioso tentando sair da pasta base
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)

from zipfile import ZipFile, BadZipFile

for up in files:
    name = up.name.lower()

    # CASO 1: ZIP com pastas/subpastas
    if name.endswith(".zip"):
        try:
            with ZipFile(io.BytesIO(up.read())) as z:
                for info in z.infolist():
                    # pula diretórios e lixos comuns do macOS
                    if info.is_dir():
                        continue
                    if "__macosx" in info.filename.lower() or info.filename.lower().endswith(".ds_store"):
                        continue

                    ext = Path(info.filename).suffix.lower()
                    if ext not in ALLOWED:
                        # não é imagem -> ignorar silenciosamente
                        continue

                    # normaliza/corrige caminho relativo do arquivo dentro do zip
                    rel = Path(info.filename)
                    # escreve com segurança preservando a estrutura
                    with z.open(info) as src:
                        _safe_write(Path(INP), rel, src.read())

        except BadZipFile:
            st.error(f"ZIP inválido: {up.name}")
    else:
        # CASO 2: Arquivo de imagem solto
        ext = Path(name).suffix.lower()
        if ext in ALLOWED:
            _safe_write(Path(INP), Path(up.name), up.read())

# Lista final de imagens, incluindo subpastas
paths = [p for p in Path(INP).rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED]
if not paths:
    st.warning("Nenhuma imagem encontrada dentro do ZIP/pastas.")
    st.stop()
