import requests
import os
import json
from moviepy import *

VIDEO_SIZE = (1920, 1080)

# 音声合成を行う関数
def synthesize_voice(text, speaker=1, speed=1, filename="output.wav"):
    # 1. テキストから音声合成のためのクエリを作成
    query_payload = {'text': text, 'speaker': speaker}
    query_response = requests.post(f'http://localhost:50021/audio_query', params=query_payload)

    if query_response.status_code != 200:
        print(f"Error in audio_query: {query_response.text}")
        return

    query = query_response.json()
    #トークスピードを設定
    query["speedScale"] = speed

    # 2. クエリを元に音声データを生成
    synthesis_payload = {'speaker': speaker}
    synthesis_response = requests.post(f'http://localhost:50021/synthesis', params=synthesis_payload, json=query)

    if synthesis_response.status_code == 200:
        # 音声ファイルとして保存
        with open(filename, 'wb') as f:
            f.write(synthesis_response.content)
        print(f"音声が {filename} に保存されました。")
    else:
        print(f"Error in synthesis: {synthesis_response.text}")

if __name__ == "__main__":
    i = 0
    f = open('input.txt', 'r', encoding="utf-8")
    data = f.read()
    silence_duration = 1  # 音声合成の間の無音時間（秒）
    start_time = 2  # テロップの開始時間（秒）
    speed = 1 #喋るスピード
    speaker = 10 #話者
    f.close()

    print("音声合成を開始します")
    
    #1行ずつ音声合成を実施
    wav_files = []
    sentences = [line for line in data.split('\n') if line.strip()]
    for sentence in sentences:
        i += 1
        # 音声合成の実行
        synthesize_voice(sentence, speaker=speaker,speed=speed, filename=f"src/voiceVox_output_{i}.wav")
        wav_files.append(f"src/voiceVox_output_{i}.wav")
    
    i = 0
    
    # 音声クリップと無音クリップを交互にリスト化
    audio_clips = []
    audio_clips.append(AudioClip(lambda t: 0, duration=start_time, fps=44100))
    for idx, wav in enumerate(wav_files):
        audio_clips.append(AudioFileClip(wav))
        # 最後以外に無音を挟む
        if idx != len(wav_files) - 1:
            silence = AudioClip(lambda t: 0, duration=silence_duration, fps=44100)
            audio_clips.append(silence)
    audio_clips.append(AudioClip(lambda t: 0, duration=start_time, fps=44100))
            
    # 音声をすべて結合
    final_audio = concatenate_audioclips(audio_clips)
            
    # テロップ用クリップを作成
    text_clips = []
    current_time = start_time
    for idx, wav in enumerate(wav_files):
        audio = AudioFileClip(wav)
        duration = audio.duration
        sentence = sentences[idx]
        # テロップクリップ作成
        txt_clip = TextClip(text=sentence, font="fonts/Corporate-Logo-Rounded-Bold-ver3.otf", color='blue', stroke_color='white', stroke_width=3, font_size=40, size=(1700, 100), method='caption')
        txt_clip = txt_clip.with_start(current_time).with_duration(duration).with_position(('center', 'bottom'))
        text_clips.append(txt_clip)
        current_time += duration
        if idx != len(wav_files) - 1:
            current_time += silence_duration

    # 背景画像クリップ
    img_clip = ImageClip("background/image.jpg").resized(VIDEO_SIZE).with_duration(final_audio.duration+start_time*2)

    # テロップを背景と重ねる
    video = CompositeVideoClip([img_clip] + text_clips, size=VIDEO_SIZE)
    
    #BGMをループ化して音声に設定
    bgms = []
    bgm = AudioFileClip("background/bgm.mp3").with_volume_scaled(0.2)
    bgm_loop = bgm.with_effects([afx.AudioLoop(duration=final_audio.duration+start_time*2)])
    final_audio = CompositeAudioClip([final_audio, bgm_loop])
    
    # 音声を動画に設定
    video = video.with_audio(final_audio)
    
    print("動画を出力します")

    #動画を出力
    video.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("動画が final_video.mp4 に保存されました。")
    
