import streamlit as st
from datetime import datetime

def get_file_size_mb(audio_bytes):
    """Calculate file size in MB"""
    return len(audio_bytes) / (1024 * 1024)

st.header("Audio Recorder", divider="grey")

# Patient information section
st.markdown("##### Enter patient details below:")
patient_name = st.text_input("👤 Patient Name", help="Data saved only your PC ONLY")

# Recording section
audio_bytes = st.audio_input("Click to record audio")

if audio_bytes and patient_name:
    file_name = f"{patient_name}__{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    st.download_button(
        "💾 Save Recording",
        data=audio_bytes,
        file_name=file_name,
        mime="audio/wav",
        use_container_width=True
    )
elif audio_bytes and not patient_name:
    st.warning("Please enter patient name before saving")
