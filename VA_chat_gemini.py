import speech_recognition as sr
import requests
import json
import os
from google.cloud import texttospeech

# Set up Gemini Cloud API key
gemini_api_key = "your_gemini_api_key_here"

messages = [{"role": "system", "content": "Your name is alexa and give answers in 2 lines"}]

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    response = requests.post(
        "https://api.geminicloud.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {gemini_api_key}"},
        json={"model": "gemini-3.5-turbo", "messages": messages}
    )
    response_data = response.json()
    ChatGPT_reply = response_data["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": ChatGPT_reply})
    return ChatGPT_reply

def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D"  # Custom voice
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    with open("speech.mp3", "wb") as out:
        out.write(response.audio_content)
    print("Audio content written to file 'speech.mp3'")

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
                response_from_gemini = get_response(response)
                text_to_speech(response_from_gemini)
                play_audio()
            else:
                print("Didn't recognize 'alexa'.")

        except sr.UnknownValueError:
            print("Didn't recognize anything.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")