import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def _resize_and_center(img: Image.Image, target_size, bg_color=None):
    """Redimensiona e centraliza a imagem, opcionalmente com cor de fundo."""
    w, h = img.size
    scale = min(target_size[0]/w, target_size[1]/h)
    new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Se bg_color for None → manter transparência
    if bg_color is None:
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    else:
        canvas = Image.new("RGB", target_size, bg_color)

    off = ((target_size[0]-new_w)//2, (target_size[1]-new_h)//2)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas.paste(img, off, img)
    return canvas


def _play_ping(ping_b64: str):
    st.markdown(f'<audio autoplay src="data:audio/wav;base64,{ping_b64}"></audio>', unsafe_allow_html=True)


def render(ping_b64: str):
    # ====== Banner ======
    banner_path = "assets/banner_resize.png"
    try:
        with open(banner_path, "rb") as f:
            b64_banner = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        st.error("❌ Imagem de banner não encontrada em 'assets/banner_resize.png'")
        st.stop()

    # ====== CSS ======
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
    </style>
    """, unsafe_allow_html=True)

    # ====== Hero Section ======
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">CONVERSOR DE IMAGEM</div>
        <div class="hero">
            <img src="data:image/png;base64,{b64_banner}" class="bg" alt="banner">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ====== Configurações ======
    col1, col2 = st.columns(2)
    with col1:
        target_label = st.radio("Resolução", ("1080x1080", "1080x1920"), horizontal=True)
        target = (1080, 1080) if target_label == "1080x1080" else (1080, 1920)
    with col2:
        usar_cor = st.toggle("Usar cor de fundo personalizada", value=False)
        bg_rgb = None
        if usar_cor:
            hexcor = st.color_picker("Cor de fundo", "#f2f2f2")
            bg_rgb = tuple(int(hexcor.strip("#")[i:i+2], 16) for i in (0, 2, 4))

    st.write("---")
    out_format = st.selectbox("Formato de saída", ("png", "jpg", "webp"), index=0)

    # ====== Upload ======
    files = st.file_uploader("Envie imagens ou ZIP", type=["jpg", "jpeg", "png", "webp", "zip"], accept_multiple_files=True)
    if not files:
        st.info("👆 Envie suas imagens acima para começar.")
        st.stop()

    INP, OUT = "conv_in", "conv_out"
    shutil.rmtree(INP, ignore_errors=True)
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(INP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    from zipfile import ZipFile, BadZipFile
    for f in files:
        if f.name.lower().endswith(".zip"):
            try:
                with ZipFile(io.BytesIO(f.read())) as z:
                    z.extractall(INP)
            except BadZipFile:
                st.error(f"ZIP inválido: {f.name}")
        else:
            open(os.path.join(INP, f.name), "wb").write(f.read())

    paths = [p for p in Path(INP).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not paths:
        st.warning("Nenhuma imagem encontrada.")
        st.stop()

    # ====== Processamento ======
    prog = st.progress(0.0)
    info = st.empty()
    results = []

    def worker(p: Path):
        rel = p.relative_to(INP)
        raw = open(p, "rb").read()
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        composed = _resize_and_center(img, target, bg_color=bg_rgb)
        outp = (Path(OUT) / rel).with_suffix("." + out_format.lower())
        os.makedirs(outp.parent, exist_ok=True)

        bio = io.BytesIO()
        if out_format.lower() == "jpg":
            composed.convert("RGB").save(bio, format="JPEG", quality=92, optimize=True)
        elif out_format.lower() == "png":
            composed.save(bio, format="PNG", optimize=True)
        else:
            composed.save(bio, format="WEBP", quality=95)
        open(outp, "wb").write(bio.getvalue())

        prev_io = io.BytesIO()
        pv = composed.copy()
        pv.thumbnail((360, 360))
        if out_format.lower() == "jpg":
            pv.convert("RGB").save(prev_io, format="JPEG", quality=85)
            mime = "image/jpeg"
        elif out_format.lower() == "png":
            pv.save(prev_io, format="PNG")
            mime = "image/png"
        else:
            pv.save(prev_io, format="WEBP", quality=90)
            mime = "image/webp"
        return rel.as_posix(), prev_io.getvalue(), mime

    with ThreadPoolExecutor(max_workers=8) as ex:
        fut = [ex.submit(worker, p) for p in paths]
        tot = len(fut)
        for i, f in enumerate(as_completed(fut), 1):
            try:
                results.append(f.result())
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
            prog.progress(i / tot)
            info.info(f"Processado {i}/{tot}")

    st.write("---")
    st.subheader("Pré-visualizações")
    cols = st.columns(3)
    for idx, (name, data, mime) in enumerate(results[:6]):
        with cols[idx % 3]:
            st.image(data, caption=name, use_column_width=True)

    # ====== ZIP ======
    zbytes = io.BytesIO()
    with zipfile.ZipFile(zbytes, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, OUT)
                z.write(fp, arc)
    zbytes.seek(0)

    st.success("✅ Conversão concluída!")
    _play_ping(ping_b64)
    st.download_button("📦 Baixar imagens convertidas", data=zbytes, file_name=f"convertidas_{target_label}.zip", mime="application/zip")


if __name__ == "__main__":
    render("")
    
# =======================
# 🔽 UPLOAD PARA GOOGLE DRIVE + CSV
# =======================
import pandas as pd
from google.colab import drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.colab import auth
import os

with st.expander("☁️ Enviar imagens convertidas para o Google Drive"):
    st.markdown("Após converter suas imagens, você pode enviá-las para o Google Drive e gerar um CSV com links públicos.")

    if st.button("🚀 Fazer upload para o Google Drive"):
        try:
            # Autenticação
            st.info("🔗 Conectando ao Google Drive...")
            auth.authenticate_user()
            drive.mount('/content/drive')
            service = build('drive', 'v3')

            # Cria pasta no Drive
            folder_name = "imagens_publicas_streamlit"
            folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')

            st.success(f"📁 Pasta criada: {folder_name}")

            # Upload das imagens convertidas
            uploads = []
            for root, _, files in os.walk("conv_out"):
                for fn in files:
                    filepath = os.path.join(root, fn)
                    file_metadata = {'name': fn, 'parents': [folder_id]}
                    media = MediaFileUpload(filepath, resumable=True)
                    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    uploads.append({
                        "nome_do_arquivo": fn,
                        "url_publica": f"https://drive.google.com/uc?export=view&id={file['id']}"
                    })
            # Torna a pasta pública
            service.permissions().create(fileId=folder_id, body={'type': 'anyone', 'role': 'reader'}).execute()

            # Gera CSV com os links públicos
            df = pd.DataFrame(uploads)
            csv_path = "links_drive.csv"
            df.to_csv(csv_path, index=False)

            st.success("✅ Upload concluído e CSV gerado!")
            st.download_button("📥 Baixar CSV de Links", data=open(csv_path, "rb").read(), file_name="links_drive.csv", mime="text/csv")

        except Exception as e:
            st.error(f"❌ Erro: {e}")
