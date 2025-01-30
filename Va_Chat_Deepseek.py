import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import pygame
import sounddevice as sd
import os
import random

# Setup OpenAI API
client = OpenAI(
    base_url="https://huggingface.co/api/inference-proxy/together",
    api_key="hf_xxxxxxxxx"
)

messages = [{"role": "system", "content": "Your name is Alexa and give answers in 2 lines"}]

previous_file = None

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    
    stream = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=messages,
        max_tokens=500,
        stream=True
    )
    
    response_text = ""
    print("AI Response:", end=" ")
    for chunk in stream:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                text_part = delta.content
                print(text_part, end="", flush=True)
                response_text += text_part
    
    print("\n")  # Tambahkan newline setelah respons selesai
    messages.append({"role": "assistant", "content": response_text})
    return response_text

def text_to_speech(text):
    global previous_file
    random_number = random.randint(1000, 9999)
    filename = f"speech_{random_number}.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(filename)
    print(f"Audio saved as '{filename}'")
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

mic_index = int(input("Select the microphone index: "))

# List available speakers
print("Available speakers:")
for index, device in enumerate(sd.query_devices()):
    if device['max_output_channels'] > 0:
        print(f"{index}: {device['name']}")

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
            response = recognizer.recognize_google(audio, language='en')
            print(f"You said: {response}")

            if "alexa" in response.lower():
                response_from_ai = get_response(response)
                filename = text_to_speech(response_from_ai)
                play_audio(filename)
            else:
                print("Didn't recognize 'alexa'.")

        except sr.UnknownValueError:
            print("Didn't recognize anything.")
