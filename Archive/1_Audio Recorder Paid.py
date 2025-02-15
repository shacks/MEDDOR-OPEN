import streamlit as st
from datetime import datetime
import time
import assemblyai as aai
from st_supabase_connection import SupabaseConnection
from components.generate_summary import generate_summary_claude

# Initialize connections
aai.settings.api_key = st.secrets["ASSEMBLYAI"]
conn = st.connection("supabase", type=SupabaseConnection)

def save_recording_to_db(file_name, storage_path, patient_name):
    """Save recording metadata to database"""
    try:
        recording_data = {
            "file_name": file_name,
            "file_path": storage_path,
            "patient_name": patient_name,
            "created_at": datetime.now().isoformat(),
            "summary": None,  # Initialize empty fields
            "transcript": None,
            "transcribed_at": None
        }
        # Use Supabase table insert
        result = conn.table("personal_recordings").insert(recording_data).execute()
        if hasattr(result, 'data'):
            return True
        return False
    except Exception as e:
        st.error(f"Error saving recording to database: {str(e)}")
        return False

def update_transcript_in_db(file_name, transcript, summary):
    """Update transcript and summary in database"""
    try:
        update_data = {
            "transcript": transcript,
            "summary": summary,
            "transcribed_at": datetime.now().isoformat()
        }
        conn.table("personal_recordings").update(update_data).eq("file_name", file_name).execute()
    except Exception as e:
        st.error(f"Error updating transcript in database: {str(e)}")

def get_recording_details(file_name):
    """Get recording details from database"""
    try:
        response = conn.table("personal_recordings").select("*").eq("file_name", file_name).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error fetching recording details: {str(e)}")
        return None

def delete_recording(file_name):
    """Delete recording from database and storage"""
    try:
        # Get file path from database
        response = conn.table("personal_recordings").select("file_path").eq("file_name", file_name).execute()
        if response.data:
            file_path = response.data[0]["file_path"]  # Changed from storage_path to file_path
            # Delete from Supabase storage
            conn.remove("audio_recordings", [file_path])
            # Delete from database
            conn.table("personal_recordings").delete().eq("file_name", file_name).execute()
            return True
    except Exception as e:
        st.error(f"Error deleting recording: {str(e)}")
    return False

def upload_to_storage(audio_bytes, patient_name):
    """Upload audio file to Supabase storage"""
    try:
        file_name = f"{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        storage_path = file_name  # Simplified path
        
        # Revert to working upload format
        conn.upload(
            "audio_recordings",     # bucket name (as first positional arg)
            "local",                # source path descriptor
            audio_bytes,            # file content
            storage_path,           # destination path
            "false"                 # upsert flag
        )
        return True, file_name, storage_path
    except Exception as e:
        st.error(f"Error uploading to storage: {str(e)}")
        return False, None, None

def download_audio(file_path):
    """Download audio file from Supabase storage"""
    try:
        file_name, mime, file_data = conn.download(
            "audio_recordings",  # bucket name
            file_path           # file path
        )
        return file_name, mime, file_data
    except Exception as e:
        st.error(f"Download error: {str(e)}")
        return None, None, None

def get_signed_url(file_path):
    """Get a signed URL for a file in Supabase storage"""
    try:
        bucket_name = "audio_recordings"
        # Create signed URL that expires in 1 hour (3600 seconds)
        response = conn.create_signed_urls(bucket_name, [file_path], 3600)
        
        if response and len(response) > 0:
            # Debug output
            #st.write(f"Debug - Signed URL response: {response}")
            signed_url = response[0].get("signedURL")
            if signed_url:
                return signed_url
        
        st.error("Failed to generate signed URL")
        return None
    except Exception as e:
        st.error(f"Error getting signed URL: {str(e)}")
        return None

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
                # Try uploading to Supabase
                success, file_name, storage_path = upload_to_storage(audio_bytes, patient_name)
                
                if success:
                    save_recording_to_db(file_name, storage_path, patient_name)
                    st.success("Recording saved to cloud storage")
                else:
                    # Improved fallback for failed uploads
                    st.error("Cloud storage failed - Download the recording below")
                    st.download_button(
                        "📥 Download Recording",
                        data=audio_bytes,
                        file_name=f"{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                        mime="audio/wav",
                        use_container_width=True
                    )

with transcribe_tab:
    st.subheader("📂 Pending Transcriptions")
    
    try:
        response = conn.table("personal_recordings").select("*").execute()
        untranscribed = [r for r in response.data if not r.get('transcript')]
        st.write(f"Untranscribed records: {len(untranscribed)}")
        
        if not untranscribed:
            st.info("No pending transcriptions found")
        else:
            for idx, recording in enumerate(untranscribed):
                created_date = datetime.fromisoformat(recording["created_at"]) if recording["created_at"] else "Unknown"
                display_date = created_date.strftime("%Y-%m-%d %H:%M") if isinstance(created_date, datetime) else created_date
                
                with st.expander(f"👤 {recording['patient_name']} - 📅 {display_date}"):
                    file_path = recording["file_path"]
                    file_name, mime, audio_bytes = download_audio(file_path)
                    
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/wav')
                        
                        # Define columns for buttons
                        action_col1, action_col2 = st.columns([3, 1])
                        
                        with action_col1:
                            if st.button("🎯 Transcribe", 
                                       key=f"transcribe_btn_{recording['file_name']}_{idx}", 
                                       use_container_width=True):
                                try:
                                    with st.spinner("Transcribing..."):
                                        # Get signed URL for the audio file
                                        signed_url = get_signed_url(file_path)
                                        if not signed_url:
                                            st.error("Failed to get secure URL for audio file")
                                        else:
                                            #st.write("Debug - Signed URL:", signed_url)  # Debug output
                                            
                                            # Configure and transcribe using signed URL
                                            config = aai.TranscriptionConfig(
                                                speech_model=aai.SpeechModel.best,
                                                language_detection=True
                                            )
                                            
                                            transcriber = aai.Transcriber(config=config)
                                            # Use the signed URL directly
                                            transcript = transcriber.transcribe(signed_url)
                                            
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
                                                    update_transcript_in_db(recording["file_name"], transcript.text, ai_output_text)
                                                    
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
                        
                        with action_col2:
                            if st.button("🗑️ Delete", 
                                       key=f"delete_btn_{recording['file_name']}_{idx}", 
                                       use_container_width=True):
                                try:
                                    delete_recording(recording["file_name"])
                                    st.success("Recording deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting recording: {str(e)}")
                    else:
                        st.error(f"Could not load audio for {file_path}")
                                
    except Exception as e:
        st.error(f"Error loading recordings: {str(e)}")

with view_tab:
    st.subheader("📚 Completed Transcriptions")
    
    try:
        # Get all records and filter in Python
        response = conn.table("personal_recordings").select("*").execute()
        
        # Filter transcribed records
        transcribed = [r for r in response.data if r.get('transcript')]
        
        if not transcribed:
            st.info("No transcribed recordings found")
        else:
            st.write(f"Found {len(transcribed)} completed transcriptions")
            for idx, recording in enumerate(transcribed):
                transcribed_found = True
                created_date = datetime.fromisoformat(recording["created_at"]) if recording["created_at"] else "Unknown"
                display_date = created_date.strftime("%Y-%m-%d %H:%M") if isinstance(created_date, datetime) else created_date
                
                with st.expander(f"👤 {recording['patient_name']} - 📅 {display_date}"):
                    storage_path = recording["file_path"]  # Changed from storage_path to file_path
                    
                    # Display creation and transcription times
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"Created: {display_date}")
                    with col2:
                        transcribed_date = datetime.fromisoformat(recording["transcribed_at"]) if recording["transcribed_at"] else "Unknown"
                        if isinstance(transcribed_date, datetime):
                            st.text(f"Transcribed: {transcribed_date.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Updated audio player without key parameter
                    file_name, mime, audio_bytes = download_audio(storage_path)
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/wav')
                    else:
                        st.error(f"Could not load audio for {storage_path}")
                    
                    st.markdown("### Transcription:")
                    st.write(recording["transcript"])
                    
                    if recording["summary"]:  # if summary exists
                        st.markdown("### Medical Summary:")
                        st.write(recording["summary"])
                    
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_view_{recording['file_name']}"):
                            try:
                                delete_recording(recording["file_name"])
                                st.success("Recording deleted successfully!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting recording: {str(e)}")
            
    except Exception as e:
        st.error(f"Error loading recordings: {str(e)}")
