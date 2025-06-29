import streamlit as st
import tempfile
import os
import json
from pathlib import Path
import shutil
import importlib.util

st.title("🎬 Jigsaw Puzzle Movie Generator")

st.write("""
Upload all required assets (images, audio, etc.), paste your JSON config, and generate a jigsaw puzzle reveal video!
""")

uploaded_files = st.file_uploader(
    "Upload all required files (images, audio, etc.)",
    type=None,
    accept_multiple_files=True,
    help="Upload all images, audio, and any assets referenced in your config."
)

config_text = st.text_area(
    "Paste your JSON config here:",
    height=200,
    placeholder='{"clips": [{"background": "bg.png", "image": "puzzle_image.png", "rows": 2, "columns": 2, "text": "This is a puzzle!"}]}'
)

fps = st.number_input("Frames per second (FPS)", min_value=1, max_value=60, value=24)

generate_btn = st.button("Generate Movie")

if generate_btn:
    if not uploaded_files or not config_text.strip():
        st.error("Please upload all required files and provide a valid JSON config.")
    else:
        with st.spinner("Generating movie, please wait..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                for file in uploaded_files:
                    file_path = os.path.join(tmpdir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                config_path = os.path.join(tmpdir, "config.json")
                try:
                    config_json = json.loads(config_text)
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
                    st.stop()
                with open(config_path, "w") as f:
                    json.dump(config_json, f)
                output_path = os.path.join(tmpdir, "output.mp4")
                # Import and call the entry function directly
                try:
                    spec = importlib.util.spec_from_file_location("jigsaw_puzzle_movie_generator", os.path.join(os.path.dirname(__file__), "jigsaw_puzzle_movie_generator.py"))
                    jigsaw_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(jigsaw_mod)
                    jigsaw_mod.generate_jigsaw_video(
                        input_dir=tmpdir,
                        output=output_path,
                        asset_path=None,
                        fps=fps,
                        compile=False
                    )
                except Exception as e:
                    st.error(f"Movie generation failed:\n{e}")
                if not os.path.exists(output_path):
                    st.error("Movie file was not created.")
                else:
                    st.success("Movie generated!")
                    with open(output_path, "rb") as f:
                        st.video(f.read())
