from ollama import chat
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import sounddevice as sd
import soundfile as sf
import threading
import queue
import time
import pyaudio

# Bahasa default untuk speech recognition
slang = "en-US"  # English (United States)

# Fungsi untuk menampilkan daftar mikrofon yang tersedia
def list_microphones():
    p = pyaudio.PyAudio()
    print("Available microphones:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["maxInputChannels"] > 0:  # Hanya tampilkan perangkat input
            print(f"{i}: {device_info['name']}")
    p.terminate()

# Fungsi untuk memilih mikrofon
def select_microphone():
    list_microphones()
    mic_index = int(input("Enter the index of the microphone you want to use: "))
    return mic_index

# Fungsi untuk menampilkan daftar speaker (output audio)
def list_speakers():
    devices = sd.query_devices()
    print("Available speakers:")
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:  # Tampilkan hanya perangkat output
            print(f"{i}: {device['name']}")

# Fungsi untuk memilih speaker
def select_speaker():
    list_speakers()
    speaker_index = int(input("Enter the index of the speaker you want to use: "))
    return speaker_index

# Fungsi untuk mengirim permintaan ke model LLM
def chatfun(request, text_queue, llm_finished):
    global messages

    messages.append({'role': 'user', 'content': request})

    response = chat(
        model='llama3',
        messages=messages,
        stream=True,
    )

    shortstring = ''
    reply = ''

    for chunk in response:
        ctext = chunk['message']['content']
        shortstring += ctext

        # Kirim teks ke antrian jika sudah cukup panjang
        if len(shortstring) > 100:  # Ubah batas ini sesuai kebutuhan
            print(shortstring, end='', flush=True)
            text_queue.put(shortstring.replace("*", ""))
            reply += shortstring
            shortstring = ''

        time.sleep(0.1)  # Kurangi penundaan jika diperlukan

    if shortstring:
        print(shortstring, end='', flush=True)
        text_queue.put(shortstring.replace("*", ""))
        reply += shortstring

    messages.append({'role': 'assistant', 'content': reply})
    llm_finished.set()  # Tandai bahwa generasi teks selesai

# Fungsi untuk mengonversi teks ke suara
def speak_text(text, speaker_index):
    # Buat file audio sementara dari teks
    mp3file = BytesIO()
    tts = gTTS(text, lang="en", tld='us', slow=False)  # Percepat konversi
    tts.write_to_fp(mp3file)
    mp3file.seek(0)

    try:
        # Muat file audio ke buffer
        audio_data, samplerate = sf.read(mp3file)
        # Putar audio melalui speaker pilihan
        sd.play(audio_data, samplerate=samplerate, device=speaker_index)
        sd.wait()
    except Exception as e:
        print(f"Error playing audio: {e}")
    finally:
        mp3file.close()

# Fungsi utama
def main():
    global messages

    # Inisialisasi variabel global
    messages = []

    # Memilih mikrofon
    mic_index = select_microphone()
    mic = sr.Microphone(device_index=mic_index)

    # Memilih speaker
    speaker_index = select_speaker()

    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400

    # Loop untuk percakapan
    while True:
        with mic as source:
            rec.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")

            try:
                audio = rec.listen(source, timeout=20, phrase_time_limit=30)
                text = rec.recognize_google(audio, language=slang)

                # Ambil permintaan langsung
                text = text.strip().lower()

                if text.startswith("alexa"):
                    # Hapus kata "alexa" dari teks sebelum dikirim ke AI
                    request = text.replace("alexa", "", 1).strip()
                    print(f"You: {text}\nAI: ", end='')

                    text_queue = queue.Queue()
                    audio_queue = queue.Queue()

                    llm_finished = threading.Event()
                    textdone = threading.Event()
                    stop_event = threading.Event()

                    llm_thread = threading.Thread(target=chatfun, args=(request, text_queue, llm_finished))
                    tts_thread = threading.Thread(target=text2speech, args=(text_queue, textdone, llm_finished, audio_queue, speaker_index, stop_event))
                    play_thread = threading.Thread(target=play_audio, args=(audio_queue, textdone, stop_event))

                    llm_thread.start()
                    tts_thread.start()
                    play_thread.start()

                    llm_finished.wait()
                    llm_thread.join()

                    stop_event.set()
                    tts_thread.join()
                    play_thread.join()

                    print('\n')

                else:
                    # Abaikan jika tidak dimulai dengan "alexa"
                    print(f"Ignored: {text}")

            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
            except sr.RequestError:
                print("Speech recognition service is down.")
            except Exception as e:
                print(f"Error: {e}")

# Fungsi untuk mengonversi teks ke suara dan memasukkannya ke dalam antrian audio
def text2speech(text_queue, textdone, llm_finished, audio_queue, speaker_index, stop_event):
    while not stop_event.is_set():
        if not text_queue.empty():
            text = text_queue.get(timeout=0.5)
            mp3file = BytesIO()
            tts = gTTS(text, lang="en", tld='us', slow=False)  # Percepat konversi
            tts.write_to_fp(mp3file)
            audio_queue.put((mp3file, speaker_index))
            text_queue.task_done()

        if llm_finished.is_set() and text_queue.empty():
            textdone.set()
            break

# Fungsi untuk memutar audio dari antrian audio
def play_audio(audio_queue, textdone, stop_event):
    while not stop_event.is_set():
        if not audio_queue.empty():
            mp3audio, speaker_index = audio_queue.get()
            mp3audio.seek(0)
            audio_data, samplerate = sf.read(mp3audio)
            sd.play(audio_data, samplerate=samplerate, device=speaker_index)
            sd.wait()
            audio_queue.task_done()

        if textdone.is_set() and audio_queue.empty():
            break

if __name__ == "__main__":
    main()
