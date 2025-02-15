import streamlit as st
from datetime import datetime
import time
import os
import assemblyai as aai
import sqlite3
from components.generate_summary import generate_summary_claude  # Add this import

# Initialize AssemblyAI
aai.settings.api_key = st.secrets["ASSEMBLYAI"]

# Configure directories and database
RECORDINGS_DIR = "Recordings"
DB_PATH = "recordings.db"

# Create directories if they don't exist
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create the initial table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            patient_name TEXT,
            transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transcribed_at TIMESTAMP
        )
    ''')
    
    # Check if summary column exists, if not add it
    cursor = c.execute('PRAGMA table_info(recordings)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'summary' not in columns:
        c.execute('ALTER TABLE recordings ADD COLUMN summary TEXT')
    
    conn.commit()
    conn.close()

# Initialize database on app start
init_db()

# Database helper functions
def save_recording_to_db(file_name, patient_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO recordings (file_name, patient_name) VALUES (?, ?)',
              (file_name, patient_name))
    conn.commit()
    conn.close()

def update_transcript_in_db(file_name, transcript, summary):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE recordings 
        SET transcript = ?, summary = ?, transcribed_at = CURRENT_TIMESTAMP 
        WHERE file_name = ?
    ''', (transcript, summary, file_name))
    conn.commit()
    conn.close()

def get_recording_details(file_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM recordings WHERE file_name = ?', (file_name,))
    result = c.fetchone()
    conn.close()
    return result

def delete_recording(file_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM recordings WHERE file_name = ?', (file_name,))
    conn.commit()
    conn.close()
    
    # Delete the file from filesystem
    file_path = os.path.join(RECORDINGS_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

st.header("Audio Recorder", divider="grey")
record_tab, transcribe_tab, view_tab = st.tabs(["🎙️ Record", "🗣️ Transcribe", "👀 View Transcriptions"])

with record_tab:
    # Patient information section
    st.markdown("##### Enter patient details below:")
    patient_name = st.text_input("👤 Patient Name")
    
    # Recording section
    audio_bytes = st.audio_input("Click to record audio")
    
    if audio_bytes:
        # Save file locally
        if st.button("💾 Save Recording", use_container_width=True):
            if not patient_name:
                st.warning("Please enter patient name before saving")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Use patient name in file name, replace spaces with underscores
                safe_patient_name = patient_name.replace(" ", "_")
                file_name = f"{safe_patient_name}_{timestamp}.wav"
                file_path = os.path.join(RECORDINGS_DIR, file_name)
                
                try:
                    audio_data = audio_bytes.read()
                    with open(file_path, "wb") as f:
                        f.write(audio_data)
                    
                    # Save to database
                    save_recording_to_db(file_name, patient_name)
                    st.success(f"Recording saved to {file_path}")
                except Exception as e:
                    st.error(f"Error saving recording: {str(e)}")

with transcribe_tab:
    st.subheader("📂 Pending Transcriptions")
    
    try:
        recordings = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.wav')]
        recordings.sort(reverse=True)
        
        untranscribed_found = False
        
        if recordings:
            for recording in recordings:
                details = get_recording_details(recording)
                
                # Only show recordings without transcripts
                if details and not details[3]:  # if no transcript
                    untranscribed_found = True
                    created_date = datetime.fromisoformat(details[4]) if details[4] else "Unknown"
                    display_date = created_date.strftime("%Y-%m-%d %H:%M") if isinstance(created_date, datetime) else created_date
                    
                    with st.expander(f"👤 {details[2]} - 📅 {display_date}"):
                        file_path = os.path.join(RECORDINGS_DIR, recording)
                        
                        # Display audio
                        with open(file_path, 'rb') as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format='audio/wav')
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.button("🎯 Transcribe", key=f"transcribe_{recording}", use_container_width=True):
                                try:
                                    with st.spinner("Transcribing..."):
                                        config = aai.TranscriptionConfig(
                                            speech_model=aai.SpeechModel.best,
                                            language_detection=True
                                        )
                                        
                                        transcriber = aai.Transcriber(config=config)
                                        transcript = transcriber.transcribe(file_path)
                                        
                                        if transcript.status == aai.TranscriptStatus.error:
                                            st.error(f"Transcription error: {transcript.error}")
                                        else:
                                            # Generate summary using Claude
                                            with st.spinner("Generating medical summary..."):
                                                prompt = f"La transcription suivante contient une conversation médicale... {transcript.text}"
                                                ai_output_text, input_tokens, output_tokens = generate_summary_claude(
                                                    prompt,
                                                    "claude-3-5-sonnet-latest",
                                                    "Transcribe"
                                                )
                                                
                                                # Save both transcript and summary
                                                update_transcript_in_db(recording, transcript.text, ai_output_text)
                                                
                                                st.success("Transcription and summary completed!")
                                                
                                                # Display results in tabs
                                                tab1, tab2 = st.tabs(["Transcription", "Medical Summary"])
                                                with tab1:
                                                    st.markdown("### Transcription:")
                                                    st.write(transcript.text)
                                                with tab2:
                                                    st.markdown("### Medical Summary:")
                                                    st.write(ai_output_text)
                                                
                                                time.sleep(2)
                                                st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Error during transcription: {str(e)}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_transcribe_{recording}", use_container_width=True):
                                try:
                                    delete_recording(recording)
                                    st.success("Recording deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting recording: {str(e)}")
            
            if not untranscribed_found:
                st.info("No pending transcriptions found")
        else:
            st.info("No recordings found in the directory")
            
    except Exception as e:
        st.error(f"Error loading recordings: {str(e)}")

with view_tab:
    st.subheader("📚 Completed Transcriptions")
    
    try:
        recordings = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.wav')]
        recordings.sort(reverse=True)
        
        transcribed_found = False
        
        if recordings:
            for recording in recordings:
                details = get_recording_details(recording)
                
                # Only show recordings with transcripts
                if details and details[3]:  # if transcript exists
                    transcribed_found = True
                    created_date = datetime.fromisoformat(details[4]) if details[4] else "Unknown"
                    display_date = created_date.strftime("%Y-%m-%d %H:%M") if isinstance(created_date, datetime) else created_date
                    
                    with st.expander(f"👤 {details[2]} - 📅 {display_date}"):
                        file_path = os.path.join(RECORDINGS_DIR, recording)
                        
                        # Display creation and transcription times
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text(f"Created: {display_date}")
                        with col2:
                            transcribed_date = datetime.fromisoformat(details[5]) if details[5] else "Unknown"
                            if isinstance(transcribed_date, datetime):
                                st.text(f"Transcribed: {transcribed_date.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Display audio and transcript
                        with open(file_path, 'rb') as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format='audio/wav')
                        
                        st.markdown("### Transcription:")
                        st.write(details[3])
                        
                        if details[4]:  # if summary exists
                            st.markdown("### Medical Summary:")
                            st.write(details[4])
                        
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_view_{recording}", use_container_width=True):
                                try:
                                    delete_recording(recording)
                                    st.success("Recording deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting recording: {str(e)}")
            
            if not transcribed_found:
                st.info("No transcribed recordings found")
        else:
            st.info("No recordings found in the directory")
            
    except Exception as e:
        st.error(f"Error loading recordings: {str(e)}")
