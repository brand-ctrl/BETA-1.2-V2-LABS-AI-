import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd

# =============================
# 🎨 Função auxiliar de redimensionamento
# =============================
def _resize_and_center(img: Image.Image, target_size, bg_color=None):
    w, h = img.size
    scale = min(target_size[0] / w, target_size[1] / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA" if bg_color is None else "RGB", target_size,
                       (0, 0, 0, 0) if bg_color is None else bg_color)
    off = ((target_size[0] - new_w) // 2, (target_size[1] - new_h) // 2)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas.paste(img, off, img)
    return canvas

# =============================
# 🔊 Som de conclusão
# =============================
def _play_ping(ping_b64: str):
    st.markdown(f'<audio autoplay src="data:audio/wav;base64,{ping_b64}"></audio>', unsafe_allow_html=True)

# =============================
# 🧠 App principal
# =============================
def render(ping_b64: str):
    st.set_page_config(page_title="Conversor + Drive", layout="wide")

    # ----- Banner -----
    st.markdown("""
    <style>
    body,[class*="css"]{background-color:#f9fafb!important;color:#111!important;font-family:'Inter',sans-serif;}
    .stApp header,.stApp [data-testid="stHeader"],.block-container{background:none!important;box-shadow:none!important;border:none!important;}
    .hero-container{display:flex;flex-direction:column;align-items:flex-start;margin-left:10%;margin-top:20px;}
    .hero-title{font-size:34px;font-weight:800;margin-bottom:32px;color:#111;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='hero-title'>🖼️ CONVERSOR DE IMAGEM + UPLOAD GOOGLE DRIVE</div>", unsafe_allow_html=True)

    # ----- Configurações -----
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

    # ----- Upload -----
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

    # ----- Processamento -----
    prog = st.progress(0.0)
    info = st.empty()
    results = []

    def worker(p: Path):
        rel = p.relative_to(INP)
        img = Image.open(p).convert("RGBA")
        composed = _resize_and_center(img, target, bg_color=bg_rgb)
        outp = (Path(OUT) / rel).with_suffix("." + out_format.lower())
        os.makedirs(outp.parent, exist_ok=True)
        composed.save(outp, format=out_format.upper())
        prev_io = io.BytesIO()
        pv = composed.copy()
        pv.thumbnail((360, 360))
        pv.save(prev_io, format=out_format.upper())
        mime = f"image/{out_format.lower()}"
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

    # ----- ZIP -----
    zbytes = io.BytesIO()
    with zipfile.ZipFile(zbytes, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, OUT)
                z.write(fp, arc)
    zbytes.seek(0)

    st.success("✅ Conversão concluída!")
    st.download_button("📦 Baixar imagens convertidas",
                       data=zbytes,
                       file_name=f"convertidas_{target_label}.zip",
                       mime="application/zip")

    # ==========================================================
    # ☁️ UPLOAD PARA GOOGLE DRIVE (com login via código)
    # ==========================================================
    with st.expander("☁️ Enviar imagens convertidas para o Google Drive"):
        st.markdown("Faça login com sua conta Google e escolha uma pasta para salvar os arquivos convertidos.")

        creds_path = "credentials_oauth.json"
        if not os.path.exists(creds_path):
            st.warning("⚠️ Envie seu arquivo `credentials_oauth.json` (OAuth 2.0 Desktop App) para o diretório do app.")
            st.stop()

        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)

        st.info("💡 Ambiente sem navegador detectado: use autenticação via código.")
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f"👉 [Clique aqui para abrir o login do Google]({auth_url})")
        auth_code = st.text_input("Cole aqui o código exibido após o login:")

        if not auth_code:
            st.stop()

        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            service = build("drive", "v3", credentials=creds)

            # listar pastas
            st.info("📂 Listando pastas do Drive...")
            results = service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                fields="files(id, name)"
            ).execute()
            pastas = results.get("files", [])
            pasta_nomes = [p["name"] for p in pastas] + ["(Criar nova pasta)"]
            pasta_escolhida = st.selectbox("Selecione uma pasta de destino:", pasta_nomes)

            if st.button("🚀 Enviar para o Drive"):
                if pasta_escolhida == "(Criar nova pasta)":
                    nova = service.files().create(
                        body={"name": "imagens_publicas_streamlit", "mimeType": "application/vnd.google-apps.folder"},
                        fields="id"
                    ).execute()
                    folder_id = nova["id"]
                else:
                    folder_id = [p["id"] for p in pastas if p["name"] == pasta_escolhida][0]

                # cria subpasta automática
                data_label = datetime.now().strftime("%Y-%m-%d")
                subpasta = service.files().create(
                    body={"name": data_label, "mimeType": "application/vnd.google-apps.folder", "parents": [folder_id]},
                    fields="id"
                ).execute()
                subpasta_id = subpasta["id"]

                uploads = []
                for root, _, files in os.walk("conv_out"):
                    for fn in files:
                        fp = os.path.join(root, fn)
                        meta = {"name": fn, "parents": [subpasta_id]}
                        media = MediaFileUpload(fp, resumable=True)
                        f = service.files().create(body=meta, media_body=media, fields="id").execute()
                        uploads.append({
                            "nome_do_arquivo": fn,
                            "url_publica": f"https://drive.google.com/uc?export=view&id={f['id']}"
                        })

                service.permissions().create(fileId=subpasta_id, body={"type": "anyone", "role": "reader"}).execute()
                df = pd.DataFrame(uploads)
                csv_path = "links_drive.csv"
                df.to_csv(csv_path, index=False)

                st.success(f"✅ Upload concluído em: {pasta_escolhida}/{data_label}")
                st.download_button("📥 Baixar CSV de Links",
                                   data=open(csv_path, "rb").read(),
                                   file_name="links_drive.csv",
                                   mime="text/csv")
        except Exception as e:
            st.error(f"❌ Erro: {e}")

# =============================
# ▶️ Execução
# =============================
if __name__ == "__main__":
    render("")
