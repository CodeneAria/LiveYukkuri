from openai import OpenAI

client = OpenAI(api_key="a", base_url="http://localhost:8080/v1")

# ストリーミングレスポンスを使用して音声データを取得し、WAVファイルに保存
with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="f1",
    input="私は博麗霊夢です。よろしくお願いします。",
) as response:
    response.stream_to_file("output.wav")
