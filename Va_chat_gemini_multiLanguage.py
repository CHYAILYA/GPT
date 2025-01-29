import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import pygame
import sounddevice as sd
import os
import random

# Set up Gemini API key
genai.configure(api_key="")
model = genai.GenerativeModel("gemini-1.5-flash")

messages = [{"role": "system", "content": "Your name is alexa and give answers in 2 lines"}]

previous_file = None

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    response = model.generate_content(user_input)
    ChatGPT_reply = response.text
    messages.append({"role": "assistant", "content": ChatGPT_reply})
    return ChatGPT_reply

def text_to_speech(text):
    global previous_file
    random_number = random.randint(1000, 9999)
    filename = f"speech_{random_number}.mp3"
    tts = gTTS(text=text, lang='en')  # Default TTS language is English (en)
    tts.save(filename)
    print(f"Audio has been saved as '{filename}'")
    return filename

def play_audio(filename):
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
for index, name in enumerate(sd.query_devices()):
    if name['max_output_channels'] > 0:
        print(f"{index}: {name['name']}")

# Select a speaker
speaker_index = int(input("Select the speaker index: "))
speaker_name = sd.query_devices()[speaker_index]['name']

listening = True

while listening:
    with sr.Microphone(device_index=mic_index) as source:
        recognizer = sr.Recognizer()
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        try:
            print("Listening...")
            audio = recognizer.listen(source)
            response = recognizer.recognize_google(audio, language='en')  # Default STT language is English (en)
            print(response)

            if "alexa" in response.lower():
                response_from_openai = get_response(response)
                filename = text_to_speech(response_from_openai)
                play_audio(filename)

            else:
                print("Didn't recognize 'alexa'.")

        except sr.UnknownValueError:
            print("Didn't recognize anything.")
