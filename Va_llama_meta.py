import requests
from gtts import gTTS
import pygame
import sounddevice as sd
import os
import random
import speech_recognition as sr

# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": "Bearer hf_xxxxxx"}

previous_file = None

def query(payload):
    """Send a request to Hugging Face API and return the response."""
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def get_response(user_input):
    """Get a response from the Hugging Face model."""
    payload = {
        "inputs": user_input,
        "parameters": {"max_new_tokens": 50}
    }
    output = query(payload)
    if output and isinstance(output, list) and "generated_text" in output[0]:
        return output[0]["generated_text"]
    else:
        return "I couldn't process your request."

def text_to_speech(text):
    """Convert text to speech and save it as an MP3 file."""
    global previous_file
    random_number = random.randint(1000, 9999)
    filename = f"speech_{random_number}.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    print(f"Audio has been saved as '{filename}'")
    return filename

def play_audio(filename):
    """Play the audio file using pygame."""
    global previous_file
    pygame.mixer.init(devicename=speaker_name)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    if previous_file and os.path.exists(previous_file):
        try:
            os.remove(previous_file)
            print(f"Deleted previous file '{previous_file}'")
        except PermissionError:
            print(f"Failed to delete previous file '{previous_file}'")
    previous_file = filename

# List available microphones
print("Available microphones:")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"{index}: {name}")

# Select a microphone
mic_index = int(input("Select the microphone index: "))

# List available speakers
print("Available speakers:")
speakers = sd.query_devices()
for index, device in enumerate(speakers):
    if device['max_output_channels'] > 0:
        print(f"{index}: {device['name']}")

# Select a speaker
speaker_index = int(input("Select the speaker index: "))
speaker_name = speakers[speaker_index]['name']

listening = True

while listening:
    with sr.Microphone(device_index=mic_index) as source:
        recognizer = sr.Recognizer()
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        try:
            print("Listening...")
            audio = recognizer.listen(source)
            response = recognizer.recognize_google(audio)
            print(f"You said: {response}")

            # If "alexa" is found at the start, remove it from the response
            if "alexa" in response.lower():
                response = response.lower().replace("alexa", "").strip()  # Remove "alexa" and extra spaces
                print(f"Processed input (without 'alexa'): {response}")
            else:
                print("No 'alexa' detected, processing the full input.")

            response_from_model = get_response(response)
            print(f"Response: {response_from_model}")
            filename = text_to_speech(response_from_model)
            play_audio(filename)

        except sr.UnknownValueError:
            print("Didn't recognize anything.")

