from pathlib import Path

module_code = """
import os
import zipfile
import shutil
from datetime import datetime
from moviepy.editor import VideoFileClip, concatenate_videoclips
import streamlit as st

def render_renderizador(ping_b64):
    st.title("🧩 Renderizador de Vídeos em Massa")
    st.markdown("Adicione uma sobreposição nos últimos segundos de vídeos, individualmente ou em lote.")

    st.markdown("---")
    modo = st.radio("Escolha o modo de renderização:", ["🎞️ Um único vídeo base", "📁 Múltiplos vídeos base (ZIP)"])

    if modo == "🎞️ Um único vídeo base":
        base_video = st.file_uploader("Faça o upload do VÍDEO BASE (.mp4)", type=["mp4"], key="video_single")
    else:
        zip_file = st.file_uploader("Faça o upload do ZIP com os VÍDEOS BASE", type=["zip"], key="zip_multi")

    overlay_file = st.file_uploader("Agora envie o VÍDEO DE SOBREPOSIÇÃO (.mp4)", type=["mp4"], key="overlay")

    segundos = st.number_input("Quantos segundos finais deseja substituir pelo vídeo de sobreposição?", min_value=1, max_value=20, value=5)

    if st.button("🚀 Renderizar vídeo(s)"):
        if overlay_file is None:
            st.warning("Envie o vídeo de sobreposição para continuar.")
            return

        dt = datetime.now().strftime("%Y%m%d-%H%M%S")
        pasta_saida = f"renderizados_{dt}"
        os.makedirs(pasta_saida, exist_ok=True)

        # Salvar sobreposição
        overlay_path = os.path.join(pasta_saida, overlay_file.name)
        with open(overlay_path, "wb") as f:
            f.write(overlay_file.read())

        overlay_clip = VideoFileClip(overlay_path)

        if modo == "🎞️ Um único vídeo base":
            if base_video is None:
                st.warning("Envie o vídeo base para continuar.")
                return

            base_path = os.path.join(pasta_saida, base_video.name)
            with open(base_path, "wb") as f:
                f.write(base_video.read())

            saida = processar_video(base_path, overlay_clip, segundos, pasta_saida)
            st.success("✅ Vídeo renderizado!")
            st.download_button("📥 Baixar vídeo", open(saida, "rb"), file_name=os.path.basename(saida))

        else:
            if zip_file is None:
                st.warning("Envie o arquivo ZIP com os vídeos base.")
                return

            zip_path = os.path.join(pasta_saida, "entrada.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_file.read())

            pasta_zip = os.path.join(pasta_saida, "videos_base")
            os.makedirs(pasta_zip, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(pasta_zip)

            saidas = []
            for root, _, files in os.walk(pasta_zip):
                for file in files:
                    if file.lower().endswith(".mp4"):
                        base_path = os.path.join(root, file)
                        rel_path = os.path.relpath(base_path, pasta_zip)
                        out_dir = os.path.join(pasta_saida, os.path.dirname(rel_path))
                        os.makedirs(out_dir, exist_ok=True)
                        saida = processar_video(base_path, overlay_clip, segundos, out_dir)
                        saidas.append(saida)

            zip_saida = f"{pasta_saida}.zip"
            shutil.make_archive(pasta_saida, 'zip', pasta_saida)
            st.success("✅ Todos os vídeos foram renderizados!")
            st.download_button("📦 Baixar ZIP com renderizações", open(zip_saida, "rb"), file_name=os.path.basename(zip_saida))

def processar_video(base_path, overlay_clip, segundos, output_dir):
    base_clip = VideoFileClip(base_path)
    duracao = base_clip.duration
    segundos = min(segundos, duracao)
    base_trim = base_clip.subclip(0, duracao - segundos)

    if overlay_clip.size != base_clip.size:
        overlay_clip = overlay_clip.resize(newsize=base_clip.size)

    final = concatenate_videoclips([base_trim, overlay_clip])
    nome_base = os.path.basename(base_path)
    nome_saida = nome_base.replace(".mp4", f"_RENDERIZADO.mp4")
    caminho_saida = os.path.join(output_dir, nome_saida)
    final.write_videofile(caminho_saida, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    return caminho_saida
"""

path = Path("/mnt/data/renderizar_videos.py")
path.write_text(module_code.strip())
path.name
