import streamlit as st
import requests
import pandas as pd
import re
import os
import io
import shutil
import zipfile
import concurrent.futures
from PIL import Image, ImageOps

# =====================================
# 💎 CONFIGURAÇÕES DE ESTILO
# =====================================
def _header():
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">V2 LABS — EXTRAIR IMAGENS CSV</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================
# ⚙️ FUNÇÕES AUXILIARES
# =====================================
def _shopify_request(url, token, params=None):
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers, params=params, timeout=60)
    if r.status_code != 200:
        try:
            st.error(f"Erro {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"Erro {r.status_code}: {r.text[:300]}")
        st.stop()
    return r


def _get_collection_id(shop_name, api_version, collection_input, token):
    # Se for ID direto
    if collection_input.isdigit():
        return collection_input

    # Se for URL
    if collection_input.startswith("http"):
        m = re.search(r"/collections/([^/?#]+)", collection_input)
        if m:
            handle = m.group(1)
        else:
            st.error("URL de coleção inválida."); st.stop()
    else:
        handle = collection_input

    # Buscar coleção pelo handle
    url = f"https://{shop_name}.myshopify.com/admin/api/{api_version}/custom_collections.json"
    r = _shopify_request(url, token, params={"handle": handle})
    items = r.json().get("custom_collections", [])
    if not items:
        st.error("Coleção não encontrada pelo handle informado."); st.stop()
    return str(items[0]["id"])


def _get_products_in_collection(shop_name, api_version, collection_id, token):
    produtos = []
    page_info = None
    while True:
        url = f"https://{shop_name}.myshopify.com/admin/api/{api_version}/products.json"
        params = {"collection_id": collection_id, "limit": 250}
        if page_info:
            params["page_info"] = page_info
        r = _shopify_request(url, token, params=params)
        produtos.extend(r.json().get("products", []))
        link = r.headers.get("link", "")
        if link and 'rel="next"' in link:
            try:
                page_info = link.split("page_info=")[-1].split(">")[0]
            except Exception:
                break
        else:
            break
    return produtos


def resize_image_keep_center(img_bytes, mode="1080x1080"):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    if mode == "1080x1080":
        target = (1080, 1080)
    elif mode == "9:16":
        target = (1080, 1920)
    else:
        return io.BytesIO(img_bytes)

    thumb = img.resize((50, 50))
    bg_color = tuple(map(int, thumb.getpixel((25, 25))))[:3]

    canvas = Image.new("RGB", target, bg_color)
    img_resized = ImageOps.contain(img, (int(target[0]*0.9), int(target[1]*0.9)))
    x = (target[0] - img_resized.width) // 2
    y = (target[1] - img_resized.height) // 2
    canvas.paste(img_resized, (x, y))
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=90)
    buf.seek(0)
    return buf


def upload_imgbb(image_bytes, api_key):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": api_key}
    files = {"image": image_bytes}
    r = requests.post(url, data=payload, files=files)
    if r.status_code == 200:
        return r.json()["data"]["url"]
    else:
        st.warning(f"Erro ao enviar imagem: {r.text}")
        return None


def _baixar_imagem(url, caminho, resize_mode=None, imgbb_key=None):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            if resize_mode and resize_mode != "Original":
                buf = resize_image_keep_center(r.content, resize_mode)
            else:
                buf = io.BytesIO(r.content)

            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "wb") as f:
                f.write(buf.getvalue())

            if imgbb_key:
                return upload_imgbb(buf, imgbb_key)
    except Exception as e:
        st.write("⚠️", e)
    return None


# =====================================
# 🖥️ INTERFACE STREAMLIT
# =====================================
def render():
    _header()

    st.markdown("### Configuração de Acesso")

    colA, colB = st.columns(2)
    with colA:
        shop_name = st.text_input("Nome da Loja", placeholder="ex: a608d7-cf")
    with colB:
        api_version = st.text_input("API Version", value="2023-10")

    access_token = st.text_input("Access Token (shpat_...)", type="password")
    collection_input = st.text_input("Coleção (ID, handle ou URL)", placeholder="ex: dunk ou https://sualoja.myshopify.com/collections/dunk")

    resize_mode = st.selectbox("Tamanho das imagens ao importar:", ["Original", "1080x1080", "9:16"], index=0)
    imgbb_key = st.text_input("ImgBB API Key (opcional, para gerar URLs)", type="password")

    modo = st.radio("Selecione a ação:", ("🔗 Gerar apenas CSV com links", "📦 Baixar imagens e gerar ZIP por produto"), index=0, horizontal=True)
    turbo = st.toggle("Turbo (download paralelo)", value=True)
    st.write("---")

    if st.button("▶️ Iniciar Exportação", use_container_width=True):
        if not (shop_name and api_version and access_token and collection_input):
            st.warning("Preencha todos os campos obrigatórios.")
            st.stop()

        if os.path.exists("imagens_baixadas"):
            shutil.rmtree("imagens_baixadas")
        for file in os.listdir():
            if file.endswith(".zip") or file.endswith(".csv"):
                os.remove(file)

        collection_id = _get_collection_id(shop_name, api_version, collection_input, access_token)
        produtos = _get_products_in_collection(shop_name, api_version, collection_id, access_token)

        if not produtos:
            st.warning("Nenhum produto encontrado nesta coleção.")
            st.stop()

        dados, tarefas = [], []
        for p in produtos:
            title = p.get("title", "")
            imagens = [img["src"] for img in p.get("images", [])]
            item = {"Título": title}
            for i, img in enumerate(imagens):
                item[f"Imagem {i+1}"] = img
                if "📦" in modo:
                    pasta = os.path.join("imagens_baixadas", re.sub(r'[\\/*?:\"<>|]', "_", title))
                    caminho = os.path.join(pasta, f"{i+1}.jpg")
                    tarefas.append((img, caminho, resize_mode, imgbb_key))
            dados.append(item)

        links_gerados = []
        if "📦" in modo and tarefas:
            st.info(f"Baixando e redimensionando {len(tarefas)} imagens...")
            if turbo:
                with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
                    for url in ex.map(lambda x: _baixar_imagem(*x), tarefas):
                        if url: links_gerados.append(url)
            else:
                for t in tarefas:
                    url = _baixar_imagem(*t)
                    if url: links_gerados.append(url)

            zip_name = f"imagens_colecao_{collection_id}.zip"
            with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk("imagens_baixadas"):
                    for file in files:
                        path = os.path.join(root, file)
                        zipf.write(path, os.path.relpath(path, "imagens_baixadas"))

            with open(zip_name, "rb") as f:
                st.download_button("📥 Baixar ZIP", f, file_name=zip_name, use_container_width=True)

        csv_name = f"imagens_colecao_{collection_id}.csv"
        pd.DataFrame(dados).to_csv(csv_name, index=False, encoding="utf-8-sig")
        with open(csv_name, "rb") as f:
            st.download_button("📥 Baixar CSV", f, file_name=csv_name, use_container_width=True)

        st.success("🎉 Exportação concluída!")
        if links_gerados:
            st.write("✅ Links gerados no ImgBB:")
            for link in links_gerados[:10]:
                st.markdown(f"- {link}")

if __name__ == "__main__":
    render()
