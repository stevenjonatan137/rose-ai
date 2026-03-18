import streamlit as st
import google.generativeai as genai
import re

# --- 1. KONFIGURASI KEAMANAN & MODEL ---
# Mengambil API Key dari Streamlit Secrets (Aman untuk Deploy)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ API Key tidak ditemukan! Masukkan 'GEMINI_API_KEY' di Secrets Streamlit Cloud.")
    st.stop()

# Inisialisasi Model
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction="Nama Anda adalah Asdok Rose. Anda asisten medis virtual yang profesional, ramah, dan edukatif. Gunakan emoji kesehatan sesekali."
)

# --- 2. KONFIGURASI HALAMAN & UI ---
st.set_page_config(page_title="Asdok Rose - Virtual Medical Assistant", page_icon="🩺")

# CSS Kustom untuk Tema Ungu-Biru
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    }
    .chat-rose {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #6a11cb;
        color: #1e1b4b;
        margin-bottom: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .chat-user {
        background-color: #e0e7ff;
        padding: 15px;
        border-radius: 15px;
        color: #1e1b4b;
        margin-bottom: 10px;
        text-align: left;
        border-right: 5px solid #2575fc;
    }
    .stChatMessage { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIKA PENYIMPANAN (SESSION STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🩺 ASDOK ROSE")
    st.subheader("Asisten Medis Virtual")
    
    if st.button("Chat Baru ➕", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.info("""
    **Catatan Penting:**
    Informasi ini bersifat edukasi dan bukan pengganti diagnosa medis profesional. 
    Segera hubungi rumah sakit dalam keadaan darurat. 🚑
    """)

# --- 5. FUNGSI FORMATTING ---
def format_medical_text(text):
    """Mengonversi teks mentah menjadi HTML list dan paragraf yang rapi."""
    lines = text.split('\n')
    formatted = ""
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                formatted += "</ul>"
                in_list = False
            continue

        # Deteksi Bullet Points atau Penomoran
        if re.match(r'^[*-]\s|\d+\.\s', stripped):
            if not in_list:
                formatted += "<ul style='padding-left: 20px; margin: 5px 0;'>"
                in_list = True
            content = re.sub(r'^[*-]\s|\d+\.\s', '', stripped)
            formatted += f"<li>{content}</li>"
        else:
            if in_list:
                formatted += "</ul>"
                in_list = False
            formatted += f"<p style='margin-bottom: 8px;'>{stripped}</p>"
    
    if in_list: formatted += "</ul>"
    return formatted

# --- 6. TAMPILAN PERCAKAPAN ---
st.write("### Konsultasi dengan Asdok Rose")

# Render history chat dari session state
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-user"><b>Pasien:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
    else:
        formatted_res = format_medical_text(message["content"])
        st.markdown(f'<div class="chat-rose"><b>Asdok Rose:</b><br>{formatted_res}</div>', unsafe_allow_html=True)

# --- 7. INPUT CHAT ---
if prompt := st.chat_input("Tulis gejala atau pertanyaan medis di sini..."):
    # Simpan dan Tampilkan Input User
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="chat-user"><b>Pasien:</b><br>{prompt}</div>', unsafe_allow_html=True)

    # Kirim ke Gemini API
    with st.spinner("Asdok Rose sedang mengetik..."):
        try:
            # Bangun history untuk model
            history_gemini = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ]
            
            chat_session = model.start_chat(history=history_gemini)
            response = chat_session.send_message(prompt)
            
            # Simpan dan Tampilkan Respon AI
            ai_content = response.text
            st.session_state.messages.append({"role": "assistant", "content": ai_content})
            
            formatted_ai = format_medical_text(ai_content)
            st.markdown(f'<div class="chat-rose"><b>Asdok Rose:</b><br>{formatted_ai}</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Gagal mendapatkan respon: {str(e)}")