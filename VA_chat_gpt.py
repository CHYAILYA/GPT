import speech_recognition as sr
import openai
import requests
import json
import os
# UwU MASTAHHHHH
# Set up OpenAI API key
openai.api_key = "your api in here"

messages = [{"role": "system", "content": "Your name is alexa and give answers in 2 lines"}]

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ChatGPT_reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": ChatGPT_reply})
    return ChatGPT_reply

def text_to_speech(text):
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1",
        "input": text,
        "voice": "alloy"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open("speech.mp3", "wb") as f:
            f.write(response.content)
        print("Audio has been saved as 'speech.mp3'")
    else:
        print(f"Error: {response.status_code} - {response.text}")
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
                response_from_openai = get_response(response)
                text_to_speech(response_from_openai)
                play_audio()

            else:
                print("Didn't recognize 'alexa'.")

        except sr.UnknownValueError:
            print("Didn't recognize anything.")
