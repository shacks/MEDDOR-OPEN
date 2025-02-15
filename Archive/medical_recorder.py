from components.generate_summary import generate_summary_claude
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import streamlit as st
import time
from deepgram import (
    DeepgramClient,
    FileSource,
    PrerecordedOptions,
)
import os

deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
conn = st.connection("supabase",type=SupabaseConnection)


class MedicalRecorder:
    def render(self):
        # Add local save directory configuration
        LOCAL_SAVE_DIR = "Recordings"
        if not os.path.exists(LOCAL_SAVE_DIR):
            os.makedirs(LOCAL_SAVE_DIR)
            
        # Initialize session states
        if 'transcription_result' not in st.session_state:
            st.session_state.transcription_result = None
        if 'current_file' not in st.session_state:
            st.session_state.current_file = None
        if 'uploaded_audio' not in st.session_state:
            st.session_state.uploaded_audio = None
        if 'current_record_id' not in st.session_state:
            st.session_state.current_record_id = None
            
        st.header("Meddor Transcript", divider="grey")
        record_tab, history_tab = st.tabs(["🎙️ Record", "📜 History"])
        
        with record_tab:
            # Add patient name input
            patient_name = st.text_input("👤 Patient Name", key="patient_name")
            patient_note = st.text_area("📝 Patient Notes", key="patient_note", height=100)

            # Record and Download section
            audio_bytes = st.audio_input("Record a voice message")
            if audio_bytes:
                st.audio(audio_bytes)
                st.download_button(
                    label="💾 Download Recording",
                    data=audio_bytes,
                    file_name="recording.wav",
                    mime="audio/wav",
                    use_container_width=True
                )

            # Separate Upload section
            uploaded_file = st.file_uploader("Upload audio file", type=['wav'])
            if uploaded_file:
                if st.button("📤 Upload to Server", use_container_width=True):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"audio_recording_{timestamp}.wav"
                        
                        # Upload the selected file to Supabase
                        conn.upload(
                            "audio_recordings", "local", uploaded_file,
                            "recordings" + "/" + file_name, "false",
                        )

                        initial_recording_data = {
                            "file_name": file_name,
                            "file_path": f"recordings/{file_name}",
                            "patient_name": patient_name,
                            "patient_note": patient_note,
                            "created_at": datetime.now().isoformat(),
                        }
                        
                        result = conn.table("personal_recordings").insert(initial_recording_data).execute()
                        if hasattr(result, 'data'):
                            st.session_state.current_record_id = result.data[0]['id']
                            st.session_state.uploaded_audio = uploaded_file
                            st.session_state.current_file_name = file_name
                            st.session_state.current_patient = patient_name
                            st.success("Audio uploaded successfully")
                        else:
                            st.error("Failed to create database entry")
                            
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

            # Transcribe section
            if st.session_state.uploaded_audio and st.session_state.current_record_id:
                transcribe_clicked = st.button("🪄 Transcribe", use_container_width=True, type="primary")
                if transcribe_clicked:
                    options = PrerecordedOptions(
                        model= "nova-2-medical",
                        detect_topics=True,
                        diarize=True,
                        detect_entities=True,
                        multichannel=True,
                        summarize='v2',
                        utterances=True,
                        utt_split=0.8,
                    )
                    
                    source = {
                        "buffer": st.session_state.uploaded_audio,
                    }
                    
                    try:
                        self.prerecorded(source, options, st.session_state.current_file_name)
                    except Exception as e:
                        st.error(str(e))

        with history_tab:
            st.subheader("📚 Saved Recordings")
            
            try:
                response = conn.table("personal_recordings").select("*").order('created_at', desc=True).execute()
                
                if response.data:
                    for record in response.data:
                        with st.expander(
                            f"{record['created_at'][:16]} - {record.get('patient_name', record['file_name'])}"
                        ):
                            # Display all available data
                            if record.get('summary'):
                                st.write("Summary")
                                st.markdown(record['summary'])
                                
                            if record.get('transcript'):
                                st.write("Full Transcript")
                                st.text_area(
                                    label="Transcript",  # Add label here
                                    value=record['transcript'],
                                    height=100,
                                    key=f"transcript_{record['id']}"
                                )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(
                                    label="⬇️ Download",  # Add label here
                                    key=f"download_{record['id']}", 
                                    use_container_width=True
                                ):
                                    with st.spinner("Downloading..."):
                                        file_name, mime, data = self.download_audio(record['file_path'])
                                        if data:
                                            st.download_button(
                                                label="📥 Save File",  # Add label here
                                                data=data,
                                                file_name=file_name,
                                                mime=mime,
                                                key=f"save_{record['id']}",
                                                use_container_width=True
                                            )
                                        else:
                                            st.error("Failed to download audio file")
                            
                            with col2:
                                if st.button(
                                    label="🗑️ Delete",  # Add label here
                                    key=f"delete_{record['id']}", 
                                    use_container_width=True
                                ):
                                    if self.delete_recording(record['id']):
                                        st.success("Recording deleted!")
                                        st.rerun()
                else:
                    st.info("No recordings found")
                    
            except Exception as e:
                st.error(f"Error loading recordings: {str(e)}")
                st.exception(e)

    # Add these helper functions from Personal_transcriber
    def delete_recording(self, record_id):
        try:
            conn.table("personal_recordings").delete().eq("id", record_id).execute()
            return True
        except Exception as e:
            st.error(f"Error deleting recording: {str(e)}")
            return False

    def download_audio(self, file_path):
        try:
            file_name, mime, file_data = conn.download(
                "audio_recordings",
                file_path
            )
            return file_name, mime, file_data
        except Exception as e:
            st.error(f"Download error: {str(e)}")
            return None, None, None

    # Update prerecorded method signature to accept file_name
    def prerecorded(self, source, options: PrerecordedOptions, file_name: str) -> None:
        payload: FileSource = {"buffer": source["buffer"]}
        response = (
                deepgram.listen.prerecorded.v("1")
                .transcribe_file(
                    payload,
                    options,
                )
                .to_dict()
            )
        
        # Create tabs with full width container
        with st.container():
            tab1, tab2, tab3, tab4 = st.tabs(["📝Medical Note","🤏Summary", "🗒️Transcript", "{💻}Response"])
            transcribe = response["results"]["channels"][0]["alternatives"][0]["transcript"]

            try:
                prompt = f"La réponse suivante de DeepgramAPI contient des balises médicales clés, des scores de confiance et une transcription complète ... {response}"
                ai_output_text, input_tokens, output_tokens = generate_summary_claude(prompt,"claude-3-5-sonnet-latest","Trascribe")
                tab1.markdown(ai_output_text)
                
                # Update existing database entry
                updated_recording_data = {
                    "transcript": transcribe,
                    "summary": ai_output_text
                }
                
                # Update the existing record instead of creating a new one
                result = conn.table("personal_recordings").update(updated_recording_data).eq("id", st.session_state.current_record_id).execute()
                
                if hasattr(result, 'data'):
                    st.success("✅ Transcription saved!")
                    st.session_state.transcription_result = result.data[0]
                else:
                    st.error("Failed to update recording: No data returned")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.transcription_result = None

            # Display other tabs
            with tab2:
                st.write(response["results"]["summary"]["short"])
            with tab3:
                st.write(transcribe)
            with tab4:
                st.write(response)

