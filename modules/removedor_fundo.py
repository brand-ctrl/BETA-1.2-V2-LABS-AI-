import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ====== DEPENDÊNCIA REMBG ======
try:
    from rembg import remove, new_session
    _HAS_REMBG = True
except Exception:
    _HAS_REMBG = False


def render(ping_b64: str = ""):
    # ====== CSS ENXUTO ======
    st.markdown("""
    <style>
    body,[class*="css"]{background:#f9fafb;color:#111;font-family:'Inter',sans-serif;}
    .stApp header,[data-testid="stHeader"],.block-container{background:none!important;box-shadow:none!important;border:none!important;}
    .hero{display:flex;flex-direction:column;align-items:flex-start;margin: 16px 6% 10px;}
    .hero h1{font-size:28px;font-weight:800;margin:0 0 14px;}
    .hero .ph{width:500px;height:500px;border-radius:16px;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,.08)}
    .hero .ph img{width:100%;height:100%;object-fit:cover}
    .card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:14px}
    </style>
    """, unsafe_allow_html=True)

    # ====== HERO (banner opcional) ======
    b64_banner = None
    banner_path = "assets/removedor_banner.png"
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            b64_banner = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        '<div class="hero"><h1>REMOVEDOR DE FUNDO</h1>'
        + (f'<div class="ph"><img src="data:image/png;base64,{b64_banner}"></div>' if b64_banner else '')
        + '</div>',
        unsafe_allow_html=True
    )

    # ====== CHECAGEM REMBG ======
    if not _HAS_REMBG:
        st.error("Biblioteca 'rembg' não encontrada. Instale com:  `pip install rembg onnxruntime`")
        st.stop()

    # ====== CONFIGURAÇÕES ======
    with st.expander("⚙️ Configurações avançadas", expanded=False):
        model = st.selectbox(
            "Modelo",
            ("u2net_human_seg", "u2net", "isnet-general-use"),
            index=0,
            help="u2net_human_seg costuma ir melhor para pessoas."
        )

    # ====== UPLOAD (imagens ou ZIP com subpastas) ======
    files = st.file_uploader(
        "📂 Envie imagens ou um arquivo ZIP",
        type=["jpg", "jpeg", "png", "webp", "zip"],
        accept_multiple_files=True
    )
    if not files:
        st.info("👆 Envie imagens (ou um ZIP com pastas) para começar.")
        st.stop()

    INP, OUT = "rm_in", "rm_out"
    shutil.rmtree(INP, ignore_errors=True)
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(INP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}

    def _safe_write(base: Path, relpath: Path, data: bytes):
        """Evita zip-slip e recria diretórios preservando a árvore do ZIP."""
        dest = (base / relpath).resolve()
        if not str(dest).startswith(str(base.resolve())):
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)

    from zipfile import ZipFile, BadZipFile

    for up in files:
        name_lower = up.name.lower()

        # Caso ZIP (pode ter subpastas)
        if name_lower.endswith(".zip"):
            try:
                with ZipFile(io.BytesIO(up.read())) as z:
                    for info in z.infolist():
                        if info.is_dir():
                            continue
                        # ignora artefatos comuns
                        if "__macosx" in info.filename.lower() or info.filename.lower().endswith(".ds_store"):
                            continue
                        ext = Path(info.filename).suffix.lower()
                        if ext not in ALLOWED:
                            continue
                        rel = Path(info.filename)
                        with z.open(info) as src:
                            _safe_write(Path(INP), rel, src.read())
            except BadZipFile:
                st.error(f"ZIP inválido: {up.name}")
        else:
            # Arquivo de imagem solto
            ext = Path(name_lower).suffix.lower()
            if ext in ALLOWED:
                _safe_write(Path(INP), Path(up.name), up.read())

    # Coleta final (inclui subpastas)
    paths = [p for p in Path(INP).rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED]
    if not paths:
        st.warning("Nenhuma imagem válida encontrada dentro do ZIP/pastas.")
        st.stop()

    # ====== PROCESSAMENTO REMBG ======
    session = new_session(model)
    prog = st.progress(0.0)
    info = st.empty()
    previews = []

    def worker(p: Path):
        rel = p.relative_to(INP)
        raw = p.read_bytes()
        out_bytes = remove(raw, session=session)
        outp = (Path(OUT) / rel).with_suffix(".png")
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_bytes(out_bytes)
        return raw, out_bytes, rel.as_posix()

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(worker, p) for p in paths]
        total = len(futs)
        for i, f in enumerate(as_completed(futs), 1):
            try:
                previews.append(f.result())
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
            prog.progress(i / total)
            info.info(f"Processado {i}/{total}")

    # ====== PRÉ-VISUALIZAÇÃO ======
    st.write("---")
    st.subheader("🖼️ Pré-visualização (Antes / Depois)")
    alpha = st.slider("Comparação de mistura", 0, 100, 50, 1)
    blend = alpha / 100.0
    cols = st.columns(2)
    for orig_b, out_b, name in previews[:3]:
        with cols[0]:
            st.image(orig_b, caption=f"ANTES — {name}", use_column_width=True)
        with cols[1]:
            try:
                img_o = Image.open(io.BytesIO(orig_b)).convert("RGBA")
                img_r = Image.open(io.BytesIO(out_b)).convert("RGBA")
                w = min(img_o.width, img_r.width)
                h = min(img_o.height, img_r.height)
                img_o = img_o.resize((w, h))
                img_r = img_r.resize((w, h))
                blended = Image.blend(img_o, img_r, blend)
                bio = io.BytesIO()
                blended.save(bio, format="PNG")
                bio.seek(0)
                st.image(bio, caption=f"DEPOIS — {name}", use_column_width=True)
            except Exception:
                st.image(out_b, caption=f"DEPOIS — {name}", use_column_width=True)

    # ====== EMPACOTAMENTO ======
    zbytes = io.BytesIO()
    with zipfile.ZipFile(zbytes, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, OUT)  # preserva estrutura de pastas
                z.write(fp, arc)
    zbytes.seek(0)

    st.success("✅ Remoção de fundo concluída!")
    if ping_b64:
        st.markdown(f'<audio autoplay src="data:audio/wav;base64,{ping_b64}"></audio>', unsafe_allow_html=True)

    st.download_button(
        "📦 Baixar PNGs sem fundo",
        data=zbytes,
        file_name="sem_fundo.zip",
        mime="application/zip",
        use_container_width=True
    )


# Se quiser testar esta página isolada:
if __name__ == "__main__":
    st.set_page_config(page_title="Removedor de Fundo", page_icon="🖼️", layout="wide")
    render()
