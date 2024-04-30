import pyaudio
import wave
import os
from openai import OpenAI

import speech_recognition as sr
import pyttsx3

# 从环境变量中获取API密钥
api_key = os.getenv('OPENAI_API_KEY')

# 设置OpenAI API密钥
client = OpenAI(api_key=api_key)

def list_audio_devices():
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {device_info['name']}")

def select_audio_device():
    audio = pyaudio.PyAudio()
    device_index = None
    while device_index is None:
        try:
            device_index = int(input("Enter the device number for the microphone you want to use: "))
            if device_index < 0 or device_index >= audio.get_device_count():
                print("Invalid device number. Please enter a valid device number.")
                device_index = None
        except ValueError:
            print("Invalid input. Please enter a valid device number.")
    return device_index

def record_audio(file_path, device_index, duration=5, sample_rate=44100, chunk_size=1024):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1,
                        rate=sample_rate, input=True,
                        frames_per_buffer=chunk_size,
                        input_device_index=device_index)
    print("Recording...")
    frames = []
    for i in range(0, int(sample_rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(data)
    print("Recording done.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def recognize_speech(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language='zh-CN')
        return text
    except sr.UnknownValueError:
        return "无法识别的语音"
    except sr.RequestError as e:
        return f"语音服务出错; {e}"

def speak_text(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        # 解码bytes类型到str类型
        language = voice.languages[0].decode('utf-8') if isinstance(voice.languages[0], bytes) else voice.languages[0]
        
        # 检查语言代码是否为中文
        if 'chinese' in voice.name.lower() or 'zh' in language:
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)  # 设置语速
    engine.say(text)
    engine.runAndWait()

def chat_with_gpt(prompt):
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ])
    return response.choices[0].message.content.strip()

def main():
    list_audio_devices()
    device_index = select_audio_device()
    while True:
        try:
            user_input = input(">>> ")
            if user_input.lower() == 'exit':
                break
            audio_file = 'user_audio.wav'
            record_audio(audio_file, device_index)
            user_input = recognize_speech(audio_file)
            print(f"Recognized: {user_input}")
            if user_input.lower() == 'exit':
                break
            prompt = f"User: {user_input} Assistant:"
            response = chat_with_gpt(prompt)
            print("GPT-4:", response)
            #speak_text(response)  # 播放回答
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
