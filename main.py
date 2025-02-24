import streamlit as st
import requests
import json
import io
import base64
import time
# from pydub import AudioSegment
import os

st.title("Text to Speech Chunker")

# Add custom JavaScript to handle sequential playback
st.markdown("""
<script>
// Will store all audio elements
let audioElements = [];
let currentPlayingIndex = 0;
let autoplayEnabled = true;

// Function to set up the sequential playback
function setupSequentialPlayback() {
    // Find all audio elements that have been added to the page
    audioElements = Array.from(document.querySelectorAll('audio'));
    
    // Add event listeners to each audio element
    audioElements.forEach((audio, index) => {
        // When this audio ends, play the next one if autoplay is enabled
        audio.addEventListener('ended', function() {
            if (autoplayEnabled && index < audioElements.length - 1) {
                currentPlayingIndex = index + 1;
                audioElements[currentPlayingIndex].play();
            }
        });
    });
    
    // Add control button
    if (audioElements.length > 0) {
        const controlDiv = document.createElement('div');
        controlDiv.style.margin = '20px 0';
        controlDiv.innerHTML = `
            <button id="toggleAutoplay" style="background-color: #4CAF50; color: white; border: none; 
                    padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                Disable Autoplay
            </button>
            <span id="statusText" style="font-size: 14px;">Autoplay is enabled - chunks will play sequentially</span>
        `;
        
        // Insert before the first audio element
        const firstAudio = audioElements[0];
        firstAudio.parentNode.insertBefore(controlDiv, firstAudio);
        
        // Add event listener to the toggle button
        document.getElementById('toggleAutoplay').addEventListener('click', function() {
            autoplayEnabled = !autoplayEnabled;
            this.textContent = autoplayEnabled ? 'Disable Autoplay' : 'Enable Autoplay';
            this.style.backgroundColor = autoplayEnabled ? '#4CAF50' : '#f44336';
            document.getElementById('statusText').textContent = autoplayEnabled ? 
                'Autoplay is enabled - chunks will play sequentially' : 
                'Autoplay is disabled - chunks will not play automatically';
        });
    }
}

// Check periodically if new audio elements have been added
const checkInterval = setInterval(function() {
    const currentAudioCount = document.querySelectorAll('audio').length;
    if (currentAudioCount > audioElements.length) {
        setupSequentialPlayback();
    }
    
    // If we have audio elements and they're not playing, make the first one playable
    if (audioElements.length > 0 && !audioElements.some(a => !a.paused)) {
        audioElements[0].controls = true;
    }
}, 1000);

// Initial setup
document.addEventListener('DOMContentLoaded', setupSequentialPlayback);
</script>
""", unsafe_allow_html=True)

# Function to get TTS for a chunk of text
def get_tts_audio(text_chunk, api_key):
    url = "https://api.groq.com/openai/v1/audio/speech"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "play-tts",
        "input": text_chunk,
        "voice": "Arthur-PlayAI"  # Change as needed
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Request Error: {str(e)}")
        return None

# Function to chunk text by word count
def chunk_text(text, chunk_size=100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

# Main app
api_key = st.text_input("Enter your Groq API Key", type="password")
input_text = st.text_area("Enter the text you want to convert to speech", height=200)
chunk_size = st.number_input("Words per chunk", min_value=10, value=100, step=10)

if st.button("Generate Speech"):
    if not api_key:
        st.warning("Please enter your Groq API key")
    elif not input_text:
        st.warning("Please enter some text to convert")
    else:
        # Split text into chunks
        chunks = chunk_text(input_text, chunk_size)
        st.write(f"Text split into {len(chunks)} chunks")
        
        # Process each chunk
        progress_bar = st.progress(0)
        
        for i, chunk in enumerate(chunks):
            st.write(f"Processing chunk {i+1}/{len(chunks)}...")
            audio_content = get_tts_audio(chunk, api_key)
            if audio_content:
                # Display audio with sequential number
                st.subheader(f"Chunk {i+1}")
                st.audio(audio_content, format="audio/mp3")
            progress_bar.progress((i+1)/len(chunks))
        
        st.success("All chunks processed. Audio will play sequentially by default.")
        st.info("Use the control button above the first audio player to enable/disable autoplay.")