import streamlit as st
import requests
import pandas as pd
import re
import os
import zipfile
import concurrent.futures

# ----------------------------
# Estilos mínimos e consistentes
# ----------------------------
_MIN_CSS = """
<style>
:root {
  --accent: #0ea5e9;        /* azul leve */
  --ink: #0f172a;           /* quase preto */
  --muted: #475569;         /* cinza texto secundário */
  --line: #e2e8f0;          /* linhas sutis */
  --bg: #ffffff;            /* fundo branco */
}
html, body, [class*="css"] {
  background: var(--bg) !important;
  color: var(--ink) !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji","Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
}
.block-container { padding-top: 1.5rem !important; max-width: 1100px; }
h1, h2, h3, h4 { letter-spacing: .2px; }
h1 { font-size: 28px; font-weight: 800; margin: 0 0 .75rem 0; }
.section-title {
  font-size: 14px; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .6px; margin: 16px 0 6px 0;
}
.divider
