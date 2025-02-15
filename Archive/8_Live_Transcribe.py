import streamlit as st
import websockets
import asyncio
import base64
import json
import pyaudio
import os
from pathlib import Path
import ssl
import certifi

# Session state
if 'text' not in st.session_state:
    st.session_state['text'] = 'Listening...'
    st.session_state['run'] = False
    st.session_state['stream'] = None
    st.session_state['pyaudio'] = None

# Audio parameters 
st.sidebar.header('Audio Parameters')

FRAMES_PER_BUFFER = int(st.sidebar.text_input('Frames per buffer', 3200))
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = int(st.sidebar.text_input('Rate', 16000))

def initialize_audio():
    try:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER
        )
        st.session_state['stream'] = stream
        st.session_state['pyaudio'] = p
        return True
    except Exception as e:
        st.error(f"Error initializing audio: {str(e)}")
        return False

# Start/stop audio transmission
def start_listening():
    if initialize_audio():
        st.session_state['run'] = True
        if Path('transcription.txt').is_file():
            os.remove('transcription.txt')

def stop_listening():
    st.session_state['run'] = False
    if st.session_state['stream']:
        st.session_state['stream'].stop_stream()
        st.session_state['stream'].close()
    if st.session_state['pyaudio']:
        st.session_state['pyaudio'].terminate()

def download_transcription():
    try:
        with open('transcription.txt', 'r') as read_txt:
            st.download_button(
                label="Download transcription",
                data=read_txt,
                file_name='transcription_output.txt',
                mime='text/plain')
    except Exception as e:
        st.error(f"Error downloading transcription: {str(e)}")

# Web user interface
st.header("Meddor Transcript", divider="grey")

col1, col2 = st.columns(2)

col1.button('Start', on_click=start_listening)
col2.button('Stop', on_click=stop_listening)

# Replace the transcript container setup with this simpler version
transcript_placeholder = st.empty()
transcript_area = transcript_placeholder.text_area("Transcription", value="Waiting for speech...", height=300)

# Send audio (Input) / Receive transcription (Output)
async def send_receive():
    URL = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={RATE}"
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        async with websockets.connect(
            URL,
            extra_headers=(("Authorization", st.secrets['ASSEMBLYAI']),),
            ping_interval=5,
            ping_timeout=20,
            ssl=ssl_context
        ) as _ws:
            r = await asyncio.sleep(0.1)
            print("Receiving messages ...")

            session_begins = await _ws.recv()
            print(session_begins)
            print("Sending messages ...")

            async def send():
                while st.session_state['run']:
                    try:
                        data = st.session_state['stream'].read(FRAMES_PER_BUFFER)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data":str(data)})
                        await _ws.send(json_data)
                    except Exception as e:
                        st.error(f"Error sending audio data: {str(e)}")
                        break
                    await asyncio.sleep(0.01)

            async def receive():
                full_transcript = ""
                while st.session_state['run']:
                    try:
                        result_str = await _ws.recv()
                        result_json = json.loads(result_str)
                        
                        if result_json['message_type'] == 'FinalTranscript':
                            result = result_json['text']
                            print(result)
                            
                            # Append to full transcript and update display
                            full_transcript += result + " "
                            st.session_state['text'] = full_transcript
                            # Update existing text area instead of creating new one
                            transcript_placeholder.text_area("Transcription", value=full_transcript, height=300)
                            
                            # Write to file using context manager
                            with open('transcription.txt', 'a') as transcription_txt:
                                transcription_txt.write(result + ' ')

                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        print(e)
                        assert False, "Not a websocket 4008 error"
            
            send_result, receive_result = await asyncio.gather(send(), receive())

    except Exception as e:
        st.error(f"WebSocket connection error: {str(e)}")

asyncio.run(send_receive())

if Path('transcription.txt').is_file():
    st.markdown('### Download')
    download_transcription()

# Cleanup on app shutdown
if hasattr(st, 'session_state') and st.session_state.get('run'):
    stop_listening()

# References (Code modified and adapted from the following)
# 1. https://github.com/misraturp/Real-time-transcription-from-microphone
# 2. https://medium.com/towards-data-science/real-time-speech-recognition-python-assemblyai-13d35eeed226