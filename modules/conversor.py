import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64, csv, boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== CONFIGURAÇÃO AWS ==========
AWS_ACCESS_KEY_ID = "SUA_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY = "SUA_SECRET_KEY"
AWS_REGION = "us-east-1"
BUCKET_NAME = "seu-nome-do-bucket"

# Cria cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def upload_to_s3(file_path, key):
    """Faz upload para S3 e retorna URL pública."""
    s3.upload_file(file_path, BUCKET_NAME, key, ExtraArgs={"ACL": "public-read"})
    url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return url


# ========== FUNÇÕES DE IMAGEM ==========
def _resize_and_center(img: Image.Image, target_size, bg_color=None):
    w, h = img.size
    scale = min(target_size[0]/w, target_size[1]/h)
    new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if bg_color is None:
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    else:
        canvas = Image.new("RGB", target_size, bg_color)

    off = ((target_size[0]-new_w)//2, (target_size[1]-new_h)//2)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas.paste(img, off, img)
    return canvas


# ========== INTERFACE ==========
def render():
    st.set_page_config(page_title="Conversor e Upload S3", page_icon="📤", layout="wide")
    st.title("📤 Conversor de Imagem + Upload S3")

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

        # Upload para S3
        s3_key = f"{rel.parent.as_posix()}/{outp.name}" if rel.parent != Path('.') else outp.name
        url = upload_to_s3(str(outp), s3_key)

        folder_name = rel.parent.as_posix() if rel.parent != Path('.') else "(raiz)"
        return rel.as_posix(), url, folder_name

    with ThreadPoolExecutor(max_workers=6) as ex:
        fut = [ex.submit(worker, p) for p in paths]
        tot = len(fut)
        for i, f in enumerate(as_completed(fut), 1):
            try:
                results.append(f.result())
            except Exception as e:
                st.error(f"Erro: {e}")
            prog.progress(i / tot)
            info.info(f"Processado {i}/{tot}")

    st.write("---")
    st.subheader("Pré-visualizações (até 6)")
    cols = st.columns(3)
    for idx, (name, url, folder) in enumerate(results[:6]):
        with cols[idx % 3]:
            st.image(url, caption=f"{folder}/{Path(name).name}", use_column_width=True)

    # CSV
    csv_io = io.StringIO()
    writer = csv.writer(csv_io)
    writer.writerow(["pasta", "arquivo", "url"])
    for name, url, folder in results:
        writer.writerow([folder, Path(name).name, url])
    csv_bytes = io.BytesIO(csv_io.getvalue().encode("utf-8"))

    # ZIP
    zbytes = io.BytesIO()
    with zipfile.ZipFile(zbytes, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, OUT)
                z.write(fp, arc)
        z.writestr("links_upload.csv", csv_io.getvalue())
    zbytes.seek(0)

    st.success("✅ Conversão e upload concluídos!")
    st.download_button("📦 Baixar imagens convertidas (ZIP + CSV)", data=zbytes, file_name=f"convertidas_{target_label}.zip", mime="application/zip")
    st.download_button("📄 Baixar CSV de Uploads", data=csv_bytes, file_name="links_upload.csv", mime="text/csv")


if __name__ == "__main__":
    render()
