
import httpx

sound_values = [
    15.0, 3717.0, 3769.0, 0.0, 1965.0, 1481.0, 4522.0, 295.0,
    4809.0, 4502.0, 12696.0, 12073.0, 24025.0, 1505.0, 1826.0, 9316.0, 231.0, 4107.0,
    1331.0, 0.0, 0.0, 0.0, 0.0, 0.0, 19150.0, 8597.0, 689.0, 5098.0, 3239.0,
    5576.0, 7402.0, 1770.0, 1070.0, 10795.0, 1562.0, 13946.0, 1156.0, 1661.0, 741.0, 0.0
]
sample_time = 0.1

SERVER_URL = 'http://127.0.0.1:5000'


def normalize(values: list[float]) -> list[float]:
    """sound_valuesを最大値で除算して0〜1に正規化する"""
    max_val = max(values)
    if max_val == 0:
        return [0.0] * len(values)
    return [v / max_val for v in values]


def send_sound(values: list[float], s_time: float) -> None:
    """正規化済みsound_valuesとsample_timeをサーバーに送信する"""
    normalized = normalize(values)
    print(
        f"再生時間: {len(normalized) * s_time:.1f} 秒（{len(normalized)} サンプル × {s_time} 秒）")
    print(f"正規化後の先頭10件: {[round(v, 3) for v in normalized[:10]]}")

    response = httpx.post(
        f'{SERVER_URL}/play_sound',
        json={'sound_values': normalized, 'sample_time': s_time},
        timeout=5.0,
    )
    response.raise_for_status()
    print(f"サーバー応答: {response.json()}")


if __name__ == '__main__':
    send_sound(sound_values, sample_time)
