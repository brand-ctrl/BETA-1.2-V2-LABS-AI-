
import streamlit as st
import os
import zipfile
import shutil
from datetime import datetime
from moviepy.editor import VideoFileClip, concatenate_videoclips

def render_renderizador(ping_b64: str = ""):
    st.title("🎬 Renderizador de Vídeos com Sobreposição")
    st.caption("Adicione automaticamente uma sobreposição nos segundos finais de 1 ou vários vídeos.")

    st.markdown("### Etapa 1: Selecione o modo de operação")
    modo = st.radio("Escolha:", ["🎯 Um único vídeo", "📦 ZIP com vários vídeos"], horizontal=True)

    st.markdown("### Etapa 2: Envie os arquivos")

    if modo == "🎯 Um único vídeo":
        base_file = st.file_uploader("📥 Envie o vídeo base (.mp4)", type=["mp4"], key="base_single")
        if base_file:
            base_paths = [("video_base.mp4", base_file)]
        else:
            base_paths = []
    else:
        zip_file = st.file_uploader("📥 Envie um .zip com 1 ou mais vídeos base (.mp4)", type=["zip"], key="base_zip")
        base_paths = []
        if zip_file:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall("inputs")
            for root, _, files in os.walk("inputs"):
                for file in files:
                    if file.lower().endswith(".mp4"):
                        full_path = os.path.join(root, file)
                        base_paths.append((full_path, open(full_path, "rb")))

    overlay_file = st.file_uploader("🎞️ Envie o vídeo de sobreposição (.mp4)", type=["mp4"], key="overlay")

    st.markdown("### Etapa 3: Defina o tempo a ser substituído")
    segundos_finais = st.number_input("Quantos segundos finais você quer substituir?", min_value=1, max_value=30, value=5)

    if st.button("🚀 Renderizar agora", use_container_width=True):
        if not base_paths or not overlay_file:
            st.warning("Envie todos os arquivos necessários.")
            return

        overlay_clip = VideoFileClip(overlay_file)

        data_str = datetime.now().strftime("%Y-%m-%d")
        shutil.rmtree("outputs", ignore_errors=True)
        os.makedirs("outputs", exist_ok=True)

        for base_path, file_obj in base_paths:
            try:
                base_name = os.path.splitext(os.path.basename(base_path))[0]
                base_clip = VideoFileClip(file_obj)
                corte = max(0, base_clip.duration - segundos_finais)
                base_cortado = base_clip.subclip(0, corte)
                if overlay_clip.size != base_clip.size:
                    overlay_final = overlay_clip.resize(base_clip.size)
                else:
                    overlay_final = overlay_clip
                final_clip = concatenate_videoclips([base_cortado, overlay_final])
                outname = f"{base_name}__RENDERIZADO__{data_str}.mp4"
                final_clip.write_videofile(f"outputs/{outname}", codec="libx264", audio_codec="aac", verbose=False, logger=None)
            except Exception as e:
                st.error(f"Erro ao processar {base_path}: {e}")

        zip_final = f"renderizados_{data_str}.zip"
        shutil.make_archive(zip_final.replace(".zip", ""), 'zip', "outputs")
        with open(zip_final, "rb") as f:
            st.download_button("📥 Baixar tudo renderizado (.zip)", f, file_name=zip_final, use_container_width=True)
        st.success("✅ Finalizado com sucesso!")
