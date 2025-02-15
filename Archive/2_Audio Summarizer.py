import streamlit as st
import assemblyai as aai
from components.generate_summary import generate_summary_claude
from st_copy_to_clipboard import st_copy_to_clipboard
import re

if not st.experimental_user.is_logged_in:
    st.warning("⚠️ Please log in to access the Audio Summarizer. Return to the main page to sign in.")
    st.page_link("Scribe.py", label="🏠 Return to Homepage", use_container_width=True)
else:
    # Initialize AssemblyAI
    aai.settings.api_key = st.secrets["ASSEMBLYAI"]

    st.header("Audio Summarizer", divider="grey")
    st.markdown("##### Upload a recorded audio file for transcription and summary")

    # File uploader with size validation (max 100MB)
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 100MB
    uploaded_file = st.file_uploader("Choose an audio file", type=['wav'])

    if uploaded_file:
        # Validate file size
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB")
        else:
            # Extract patient name and datetime from filename
            filename_pattern = r"(.+)__(\d{8})_(\d{6})\.wav"
            match = re.match(filename_pattern, uploaded_file.name)
            
            if not match:
                # Handle unknown format
                from datetime import datetime
                current_time = datetime.now()
                patient_name = "Unknown"
                date_str = current_time.strftime("%Y-%m-%d")
                time_str = current_time.strftime("%H:%M:%S")
                st.warning(f"Unrecognized filename format. Using default values.")
            else:
                patient_name = match.group(1)
                # Format date and time from filename
                date_str = f"{match.group(2)[:4]}-{match.group(2)[4:6]}-{match.group(2)[6:]}"
                time_str = f"{match.group(3)[:2]}:{match.group(3)[2:4]}:{match.group(3)[4:]}"
            
            # Display patient info with date and time
            st.info(f"""
            Patient: {patient_name}
            Date: {date_str}
            Time: {time_str}
            """)
                
            if st.button("🎯 Transcribe and Summarize", use_container_width=True):
                try:
                    progress_bar = st.progress(0)
                    with st.spinner("Transcribing audio..."):
                        # Create temp file for processing
                        with open("temp_audio.wav", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        progress_bar.progress(30)
                        
                        try:
                            # Configure transcription similar to paid version
                            config = aai.TranscriptionConfig(
                                speech_model=aai.SpeechModel.best,
                                language_detection=True
                            )
                            
                            transcriber = aai.Transcriber(config=config)
                            transcript = transcriber.transcribe("temp_audio.wav")
                            
                            # Check for transcription errors
                            if transcript.status == aai.TranscriptStatus.error:
                                raise ValueError(f"Transcription error: {transcript.error}")
                                
                            # Get transcript text directly from the transcript object
                            transcript_text = transcript.text
                            detected_language = getattr(transcript, 'language_code', 'unknown')
                            
                            if not transcript_text:
                                raise ValueError("No transcription text received from AssemblyAI")
                                
                            progress_bar.progress(60)
                            
                            # Check detected language
                            if detected_language not in ["en", "fr"]:
                                st.warning(f"Detected language is {detected_language}. This tool is optimized for English and French.")
                            
                            # Generate summary with text only
                            summary, input_tokens, output_tokens = generate_summary_claude(
                                input_text=transcript_text,
                                model="claude-3-5-sonnet-latest",
                                tag="audio_summary_manual"
                            )
                            
                            progress_bar.progress(100)
                            
                            # Display results
                            st.success("Processing complete!")
                            
                            # Display Summary first
                            st.subheader("Summary")
                            st.write(summary)
                            st_copy_to_clipboard(summary)  # Add copy button for summary
                            
                            # Display Transcript below
                            st.subheader("Transcript")
                            st.write(transcript_text)
                            
                        finally:
                            # Cleanup temp file
                            import os
                            if os.path.exists("temp_audio.wav"):
                                os.remove("temp_audio.wav")
                                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    progress_bar.empty()
