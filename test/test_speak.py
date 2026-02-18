import httpx

OUTBOUND_PORT = 50200
SERVER_URL = f'http://127.0.0.1:{OUTBOUND_PORT}'


def speak(text: str) -> None:
    response = httpx.post(
        f'{SERVER_URL}/speak',
        json={'text': text},
        timeout=30.0,
    )
    response.raise_for_status()
    print(f"サーバー応答: {response.json()}")


if __name__ == '__main__':
    speak("私は博麗霊夢です。よろしくお願いします。")
