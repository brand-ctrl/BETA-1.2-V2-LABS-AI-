# Re-run creation of the compact project zip
import os, io, zipfile, textwrap, base64

root = "/mnt/data/v2labs_suite"
os.makedirs(f"{root}/modules", exist_ok=True)
os.makedirs(f"{root}/assets", exist_ok=True)

app_py = """
import streamlit as st

st.set_page_config(page_title="V2 LABS AI BETA 1.1", page_icon="assets/logo_v2labs.svg", layout="wide")

st.markdown(\"\"\"
<style>
:root{ --bg1:#e9f5ff; --bg2:#e9f5ff; --ink:#0f172a; --line:rgba(15,23,42,.08); }
html, body, .stApp, [class*="css"]{
  background: linear-gradient(180deg,var(--bg1),var(--bg2)) !important;
  color:var(--ink); font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
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
\"\"\", unsafe_allow_html=True)

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
"""

conversor_py = """
import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def _resize_and_center(img: Image.Image, target_size, bg_color=(242,242,242)):
    w, h = img.size
    scale = min(target_size[0]/w, target_size[1]/h)
    new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", target_size, bg_color)
    off = ((target_size[0]-new_w)//2, (target_size[1]-new_h)//2)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    canvas.paste(img, off, img)
    return canvas

def render(ping_b64: str):
    b64_banner = None
    try:
        with open("assets/banner_resize.png","rb") as f:
            b64_banner = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

    st.markdown(\"\"\"
    <style>
    .hero{display:flex;flex-direction:column;align-items:flex-start;margin: 10px 6%;}
    .hero h1{font-size:28px;font-weight:800;margin:0 0 14px}
    .hero .ph{width:500px;height:500px;border-radius:16px;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,.08)}
    .hero .ph img{width:100%;height:100%;object-fit:cover}
    </style>
    \"\"\", unsafe_allow_html=True)

    st.markdown('<div class="hero"><h1>CONVERSOR DE IMAGEM</h1>' +
                (f'<div class="ph"><img src="data:image/png;base64,{b64_banner}"></div>' if b64_banner else '') +
                '</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        target_label = st.radio("Resolução", ("1080x1080","1080x1920"), horizontal=True)
        target = (1080,1080) if target_label=="1080x1080" else (1080,1920)
    with col2:
        hexcor = st.color_picker("Cor de fundo", "#f2f2f2")
        bg_rgb = tuple(int(hexcor.strip("#")[i:i+2],16) for i in (0,2,4))

    st.write("---")
    out_format = st.selectbox("Formato de saída", ("png","jpg","webp"), index=0)

    files = st.file_uploader("Envie imagens ou ZIP", type=["jpg","jpeg","png","webp","zip"], accept_multiple_files=True)
    if not files: st.info("👆 Envie suas imagens acima para começar."); st.stop()

    INP, OUT = "conv_in","conv_out"
    shutil.rmtree(INP, ignore_errors=True); shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(INP, exist_ok=True); os.makedirs(OUT, exist_ok=True)

    from zipfile import ZipFile, BadZipFile
    for f in files:
        if f.name.lower().endswith(".zip"):
            try:
                with ZipFile(io.BytesIO(f.read())) as z: z.extractall(INP)
            except BadZipFile: st.error(f"ZIP inválido: {f.name}")
        else:
            open(os.path.join(INP, f.name),"wb").write(f.read())

    paths = [p for p in Path(INP).rglob("*") if p.suffix.lower() in (".jpg",".jpeg",".png",".webp")]
    if not paths: st.warning("Nenhuma imagem encontrada."); st.stop()

    prog = st.progress(0.0); info = st.empty(); results = []

    def worker(p: Path):
        rel = p.relative_to(INP)
        raw = open(p,"rb").read()
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        composed = _resize_and_center(img, target, bg_color=bg_rgb)

        outp = (Path(OUT)/rel).with_suffix("." + out_format.lower())
        os.makedirs(outp.parent, exist_ok=True)
        bio = io.BytesIO()
        if out_format.lower()=="jpg":
            composed.convert("RGB").save(bio, format="JPEG", quality=92, optimize=True)
        elif out_format.lower()=="png":
            composed.save(bio, format="PNG", optimize=True)
        else:
            composed.save(bio, format="WEBP", quality=95)
        open(outp,"wb").write(bio.getvalue())

        prev_io = io.BytesIO()
        pv = composed.copy(); pv.thumbnail((360,360))
        if out_format.lower()=="jpg":
            pv.convert("RGB").save(prev_io, format="JPEG", quality=85); mime="image/jpeg"
        elif out_format.lower()=="png":
            pv.save(prev_io, format="PNG"); mime="image/png"
        else:
            pv.save(prev_io, format="WEBP", quality=90); mime="image/webp"
        return rel.as_posix(), prev_io.getvalue(), mime

    with ThreadPoolExecutor(max_workers=8) as ex:
        fut=[ex.submit(worker,p) for p in paths]; tot=len(fut)
        for i,f in enumerate(as_completed(fut),1):
            try: results.append(f.result())
            except Exception as e: st.error(f"Erro ao processar: {e}")
            prog.progress(i/tot); info.info(f"Processado {i}/{tot}")

    st.write("---"); st.subheader("Pré-visualizações")
    cols = st.columns(3)
    for idx,(name,data,mime) in enumerate(results[:6]):
        with cols[idx % 3]: st.image(data, caption=name, use_column_width=True)

    zbytes = io.BytesIO()
    with zipfile.ZipFile(zbytes,"w",zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk("conv_out"):
            for fn in files:
                fp=os.path.join(root,fn); arc=os.path.relpath(fp,"conv_out"); z.write(fp,arc)
    zbytes.seek(0)
    st.success("✅ Conversão concluída!")
    st.download_button("📦 Baixar imagens convertidas", data=zbytes, file_name=f"convertidas_{target_label}.zip", mime="application/zip")
"""

extrair_py = """
import streamlit as st
import requests, pandas as pd, re, os, zipfile, concurrent.futures

def _shopify_request(url, token, params=None):
    headers={"X-Shopify-Access-Token":token,"Content-Type":"application/json"}
    r=requests.get(url, headers=headers, params=params, timeout=60)
    if r.status_code!=200:
        try: st.error(f"Erro {r.status_code}: {r.json()}")
        except Exception: st.error(f"Erro {r.status_code}: {r.text[:300]}")
        st.stop()
    return r

def _get_collection_id(shop_name, api_version, collection_input, token):
    if collection_input.isdigit(): return collection_input
    if collection_input.startswith("http"):
        m=re.search(r"/collections/([^/?#]+)", collection_input)
        handle=m.group(1) if m else None
        if not handle: st.error("URL de coleção inválida."); st.stop()
    else:
        handle=collection_input
    url=f"https://{shop_name}.myshopify.com/admin/api/{api_version}/custom_collections.json"
    r=_shopify_request(url, token, params={"handle":handle})
    items=r.json().get("custom_collections", [])
    if not items: st.error("Coleção não encontrada pelo handle informado."); st.stop()
    return str(items[0]["id"])

def _get_products_in_collection(shop_name, api_version, collection_id, token):
    produtos=[]; page_info=None
    while True:
        url=f"https://{shop_name}.myshopify.com/admin/api/{api_version}/products.json"
        params={"collection_id":collection_id,"limit":250}
        if page_info: params["page_info"]=page_info
        r=_shopify_request(url, token, params=params)
        produtos.extend(r.json().get("products",[]))
        link=r.headers.get("link","")
        if link and 'rel="next"' in link:
            try: page_info = link.split("page_info=")[-1].split(">")[0]
            except Exception: break
        else: break
    return produtos

def _baixar_imagem(url,caminho):
    try:
        import requests, os
        r=requests.get(url, timeout=20)
        if r.status_code==200:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            open(caminho,"wb").write(r.content)
    except Exception: pass

def render(ping_b64:str):
    st.markdown('<div style="margin:10px 6%"><h1>EXTRAIR IMAGENS CSV</h1></div>', unsafe_allow_html=True)

    colA,colB=st.columns(2)
    with colA:
        shop_name = st.text_input("Nome da Loja", placeholder="ex: a608d7-cf")
    with colB:
        api_version = st.text_input("API Version", value="2023-10")

    access_token = st.text_input("Access Token (shpat_...)", type="password")
    collection_input = st.text_input("Coleção (ID, handle ou URL)", placeholder="ex: dunk ou https://sualoja.myshopify.com/collections/dunk")

    st.markdown("### Opções")
    modo = st.radio("Selecione a ação:", ("🔗 Gerar apenas CSV com links", "📦 Baixar imagens e gerar ZIP por produto"), index=0, horizontal=True)
    turbo = st.toggle("Turbo (download paralelo)", value=True)

    st.write("---")
    if st.button("▶️ Iniciar Exportação", use_container_width=True):
        if not (shop_name and api_version and access_token and collection_input):
            st.warning("Preencha todos os campos."); st.stop()

        collection_id = collection_input if collection_input.isdigit() else _get_collection_id(shop_name, api_version, collection_input, access_token)
        produtos = _get_products_in_collection(shop_name, api_version, collection_id, access_token)
        if not produtos: st.warning("Nenhum produto encontrado nesta coleção."); st.stop()

        dados=[]; tarefas=[]
        import re, os
        for p in produtos:
            title=p.get("title","")
            imagens=[img["src"] for img in p.get("images",[])]
            item={"Título":title}
            for i,img in enumerate(imagens):
                item[f"Imagem {i+1}"]=img
                if "📦" in modo:
                    pasta=os.path.join("imagens_baixadas", re.sub(r'[\\/*?:\"<>|]', "_", title))
                    tarefas.append((img, os.path.join(pasta, f"{i+1}.jpg")))
            dados.append(item)

        if "📦" in modo and tarefas:
            st.info(f"Baixando {len(tarefas)} imagens...")
            if turbo:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=16) as ex:
                    list(ex.map(lambda x: _baixar_imagem(*x), tarefas))
            else:
                for t in tarefas: _baixar_imagem(*t)

            zip_name=f"imagens_colecao_{collection_id}.zip"
            import zipfile, os
            with zipfile.ZipFile(zip_name,"w",zipfile.ZIP_DEFLATED) as zipf:
                for root,_,files in os.walk("imagens_baixadas"):
                    for file in files:
                        path=os.path.join(root,file)
                        zipf.write(path, os.path.relpath(path,"imagens_baixadas"))
            st.download_button("📥 Baixar ZIP", open(zip_name,"rb"), file_name=zip_name, use_container_width=True)

        csv_name=f"imagens_colecao_{collection_id}.csv"
        import pandas as pd
        pd.DataFrame(dados).to_csv(csv_name, index=False, encoding="utf-8-sig")
        st.download_button("📥 Baixar CSV", open(csv_name,"rb"), file_name=csv_name, use_container_width=True)
        st.success("🎉 Exportação concluída!")
"""

removedor_py = """
import streamlit as st
from PIL import Image
import io, os, shutil, zipfile, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rembg import remove, new_session
    _HAS_REMBG=True
except Exception:
    _HAS_REMBG=False

def render(ping_b64:str):
    b64_banner=None
    try:
        with open("assets/removedor_banner.png","rb") as f:
            b64_banner=base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

    st.markdown(\"\"\"
    <style>
    .hero{display:flex;flex-direction:column;align-items:flex-start;margin:10px 6%}
    .hero h1{font-size:28px;font-weight:800;margin:0 0 14px}
    .hero .ph{width:500px;height:500px;border-radius:16px;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,.08)}
    .hero .ph img{width:100%;height:100%;object-fit:cover}
    </style>
    \"\"\", unsafe_allow_html=True)

    st.markdown('<div class="hero"><h1>REMOVEDOR DE FUNDO</h1>' +
                (f'<div class="ph"><img src="data:image/png;base64,{b64_banner}"></div>' if b64_banner else '') +
                '</div>', unsafe_allow_html=True)

    if not _HAS_REMBG: st.error("Biblioteca 'rembg' não encontrada. Instale com: pip install rembg onnxruntime"); st.stop()

    with st.expander("⚙️ Configurações avançadas", expanded=False):
        model = st.selectbox("Modelo", ("u2net_human_seg","u2net","isnet-general-use"), index=0)
        st.caption("💡 Dica: 'u2net_human_seg' é ideal para retratos humanos.")

    files = st.file_uploader("📂 Envie imagens ou um arquivo ZIP", type=["jpg","jpeg","png","webp","zip"], accept_multiple_files=True)
    if not files: st.info("👆 Envie suas imagens acima para começar."); st.stop()

    INP, OUT = "rm_in","rm_out"
    shutil.rmtree(INP, ignore_errors=True); shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(INP, exist_ok=True); os.makedirs(OUT, exist_ok=True)

    from zipfile import ZipFile, BadZipFile
    for f in files:
        if f.name.lower().endswith(".zip"):
            try:
                with ZipFile(io.BytesIO(f.read())) as z: z.extractall(INP)
            except BadZipFile: st.error(f"ZIP inválido: {f.name}")
        else:
            open(os.path.join(INP, f.name),"wb").write(f.read())

    paths=[p for p in Path(INP).rglob(\"*\") if p.suffix.lower() in (\".jpg\",\".jpeg\",\".png\",\".webp\")]
    if not paths: st.warning(\"Nenhuma imagem encontrada.\"); st.stop()

    session=new_session(model)
    prog=st.progress(0.0); info=st.empty(); previews=[]

    def worker(p:Path):
        rel=p.relative_to(INP)
        raw=open(p,\"rb\").read()
        out_bytes=remove(raw, session=session)
        outp=(Path(OUT)/rel).with_suffix(\".png\")
        os.makedirs(outp.parent, exist_ok=True)
        open(outp,\"wb\").write(out_bytes)
        return raw,out_bytes,rel.as_posix()

    with ThreadPoolExecutor(max_workers=4) as ex:
        fut=[ex.submit(worker,p) for p in paths]; tot=len(fut)
        for i,f in enumerate(as_completed(fut),1):
            try: previews.append(f.result())
            except Exception as e: st.error(f\"Erro ao processar: {e}\")
            prog.progress(i/tot); info.info(f\"Processado {i}/{tot}\")

    st.write(\"---\"); st.subheader(\"🖼️ Pré-visualização (Antes / Depois)\")
    alpha=st.slider(\"Comparação de mistura\",0,100,50,1); blend=alpha/100.0

    cols=st.columns(2)
    for orig_b,out_b,name in previews[:3]:
        with cols[0]: st.image(orig_b, caption=f\"ANTES — {name}\", use_column_width=True)
        with cols[1]:
            try:
                img_o=Image.open(io.BytesIO(orig_b)).convert(\"RGBA\")
                img_r=Image.open(io.BytesIO(out_b)).convert(\"RGBA\")
                w=min(img_o.width,img_r.width); h=min(img_o.height,img_r.height)
                img_o=img_o.resize((w,h)); img_r=img_r.resize((w,h))
                blended=Image.blend(img_o,img_r,blend)
                bio=io.BytesIO(); blended.save(bio, format=\"PNG\"); bio.seek(0)
                st.image(bio, caption=f\"DEPOIS — {name}\", use_column_width=True)
            except Exception:
                st.image(out_b, caption=f\"DEPOIS — {name}\", use_column_width=True)

    zbytes=io.BytesIO()
    with zipfile.ZipFile(zbytes,\"w\",zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk(OUT):
            for fn in files:
                fp=os.path.join(root,fn); arc=os.path.relpath(fp,OUT); z.write(fp,arc)
    zbytes.seek(0)
    st.success(\"✅ Remoção de fundo concluída!\")
    st.download_button(\"📦 Baixar PNGs sem fundo\", data=zbytes, file_name=\"sem_fundo.zip\", mime=\"application/zip\", use_container_width=True)
"""

# assets minimal svgs
logo_svg = '<svg viewBox="0 0 256 64" xmlns="http://www.w3.org/2000/svg"><rect rx="12" width="256" height="64" fill="#157aff"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Inter, Arial" font-size="28" fill="#fff">V2 LABS AI</text></svg>'
icon_conv = '<svg viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg"><rect rx="16" width="96" height="96" fill="#8ec7ff"/><path d="M22 48h52" stroke="#fff" stroke-width="10" stroke-linecap="round"/></svg>'
icon_ext = '<svg viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg"><rect rx="16" width="96" height="96" fill="#a7d7ff"/><circle cx="48" cy="48" r="18" fill="#fff"/></svg>'
icon_rem = '<svg viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg"><rect rx="16" width="96" height="96" fill="#7dc8ff"/><path d="M24 60 L48 28 L72 60" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/></svg>'

open(f"{root}/app.py","w").write(app_py)
open(f"{root}/modules/conversor_imagem.py","w").write(conversor_py)
open(f"{root}/modules/extrair_imagens_csv.py","w").write(extrair_py)
open(f"{root}/modules/removedor_fundo.py","w").write(removedor_py)
open(f"{root}/assets/logo_v2labs.svg","w").write(logo_svg)
open(f"{root}/assets/icon_conversor.svg","w").write(icon_conv)
open(f"{root}/assets/icon_extrator.svg","w").write(icon_ext)
open(f"{root}/assets/icon_removedor.svg","w").write(icon_rem)
open(f"{root}/requirements.txt","w").write("streamlit\nPillow\nrequests\npandas\nrembg\nonnxruntime\n")

zip_path = "/mnt/data/V2-LABS-compact.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for base,_,files in os.walk(root):
        for fn in files:
            fp = os.path.join(base, fn)
            z.write(fp, os.path.relpath(fp, root))

zip_path
