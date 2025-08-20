# import streamlit as st
# import json 
# import marisa_trie

# data = json.load(open("index.json"))
# keys = list(data.keys())
# values = list(data.values())
# values = [v.encode("utf-8") for v in values]
# trie = marisa_trie.Trie(keys)

# # Prefix search
# matches = trie.keys("ap")
# values = [trie[key] for key in matches]

# def search(query: str) -> list[str]:
#     return [(key, data[key]) for key in trie.keys(query)]
# # --- Streamlit UI ---
# st.set_page_config(page_title="BailGaadi", page_icon="🔍")

# st.title("📚 BailGaadi - Oxford Dictionary")

# # Search bar with debounce
# query = st.text_input("Enter word or prefix", "")

# # Run search
# if query.strip():
#     matches = search(query.strip())

#     if matches:
#         st.subheader(f"Results for '{query}'")
#         for key, code in matches:
#             st.markdown(f"- **[{key}]({code})**")
#     else:
#         st.warning("No matches found.")

import streamlit as st
import json
import marisa_trie
import os
import requests
import httpx

# --- Load dictionary ---
data = json.load(open("index.json"))
keys = list(data.keys())
trie = marisa_trie.Trie(keys)

# uri = "https://www.dropbox.com/scl/fi/d8dj72dcydgivv0vklvia/processed.json?rlkey=kbjfwo3qnucguakjho9b9goyl&st=n5mik6px&dl=1"
# local = "processed.json"

# DOWNLOAD_URL = "https://example.com/processed.json"
# LOCAL_PATH = "data/processed.json"


CHUNK_DIR = "data"
CHUNK_PREFIX = "processed_chunk_"
REBUILT_PATH = "processed.json"

@st.cache_resource(show_spinner="Downloading data…")
def load_full_json():
    if not os.path.exists(REBUILT_PATH):
        chunk_files = sorted(
            f for f in os.listdir(CHUNK_DIR)
            if f.startswith(CHUNK_PREFIX)
        )
        print(chunk_files)
        with open(REBUILT_PATH, "wb") as outfile:
            for fname in chunk_files:
                with open(os.path.join(CHUNK_DIR, fname), "rb") as infile:
                    outfile.write(infile.read())

    with open(REBUILT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    if not os.path.exists(LOCAL_PATH):
        os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)

        with st.progress(0, text="Downloading...") as progress_bar:
            with httpx.Client() as client:
                with client.stream("GET", DOWNLOAD_URL) as response:
                    response.raise_for_status()
                    total = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(LOCAL_PATH, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total:
                                    progress_bar.progress(min(downloaded / total, 1.0))

    # Load JSON
    with open(LOCAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

# ✅ Usage
all_defs = load_full_json()

def inject_css():
    st.markdown(f"""
    <style>
                {open("oed2.css").read()}
    </style>
""", unsafe_allow_html=True)

# --- Placeholder: Fetch definition HTML ---
def definition(code: str) -> str:
    # Replace with your actual logic to return an HTML string
    word = all_defs[code]['word']
    pronounciation = all_defs[code]['pronounciation']
    html = all_defs[code]['definition']

    return f"""
    <p class=lgSect><em>Pronunciation: {pronounciation}</em></p>
    <div>{html}</div>
    """
    return f"<h3>Definition for code: {code}</h3><p>This is a placeholder definition.</p>"

# --- Search logic ---
def search(query: str) -> list[tuple[str, str]]:
    return [(key, data[key]) for key in trie.keys(query)]

# --- Streamlit app setup ---
st.set_page_config(page_title="BailGaadi", page_icon="🔍")
inject_css()

# --- Session state to track selected word/code ---
if "page" not in st.session_state:
    st.session_state.page = "search"
if "selected_code" not in st.session_state:
    st.session_state.selected_code = None
if "selected_word" not in st.session_state:
    st.session_state.selected_word = None

# --- Navigation helper ---
def go_to_definition(word, code):
    st.session_state.selected_word = word
    st.session_state.selected_code = code
    st.session_state.page = "definition"

def go_back():
    st.session_state.page = "search"
    st.session_state.selected_code = None
    st.session_state.selected_word = None

# --- UI Rendering ---
if st.session_state.page == "search":
    st.title("📚 BailGaadi - Oxford Dictionary")

    query = st.text_input("Enter word or prefix", "")

    if query.strip():
        matches = search(query.strip())

        if matches:
            st.subheader(f"Results for '{query}'")
            for word, code in matches:
                if st.button(word):
                    go_to_definition(word, code)
        else:
            st.warning("No matches found.")

elif st.session_state.page == "definition":
    word = st.session_state.selected_word
    code = st.session_state.selected_code

    st.button("🔙 Back to search", on_click=go_back)

    if word and code:
        st.markdown(f"## {word}")
        st.markdown(definition(code), unsafe_allow_html=True)


if __name__ == "__main__":
    load_full_json()