import speech_recognition as sr
import requests
import json
import os
from gtts import gTTS

LLAMA_API_URL = "https://api.llama.ai/v1/generate"
LLAMA_API_KEY = "your-llama-api-key"

def get_response(user_input):
    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "input": user_input,
        "max_tokens": 150
    }
    
    response = requests.post(LLAMA_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("text", "I'm not sure how to respond.")
    else:
        return "Error with the LLaMA API request."

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save("speech.mp3")

def play_audio():
    os.system("mpg123 speech.mp3")

listening = True

while listening:
    with sr.Microphone() as source:
        recognizer = sr.Recognizer()
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=5.0)
            response = recognizer.recognize_google(audio)
            print(response)

            if "alexa" in response.lower():
                response_from_llama = get_response(response)
                text_to_speech(response_from_llama)
                play_audio()

            else:
                print("Didn't recognize 'alexa'.")

        except sr.UnknownValueError:
            print("Didn't recognize anything.")
