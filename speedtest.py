import sys
from http.client import IncompleteRead
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen


URL_SCHEME = ("http", "https")
TIMEOUT = 30
REQUEST_COUNT = 10


def main() -> int:
    address = sys.argv[1] if len(sys.argv) > 1 else ""

    if not validate_address(address):
        return 1

    try:
        total_bytes, average_ms, speed_mbps = measure_downloads(address)
    except (OSError, IncompleteRead, ValueError) as error:
        print(f"Ошибка скачивания — {error}", file=sys.stderr)
        return 1

    print(f"Общий объём — {total_bytes} байт")
    print(f"Среднее время запроса — {average_ms:.2f} мс")
    print(f"Скорость скачивания — {speed_mbps:.2f} Мбит/с")
    return 0


def validate_address(address: str) -> bool:
    try:
        url = urlsplit(address)
    except ValueError:
        url = None

    if url is None:
        print("Не удалось разобрать URL.", file=sys.stderr)
        return False

    if url.scheme not in URL_SCHEME:
        print("Допустимы только схемы HTTP и HTTPS.", file=sys.stderr)
        return False

    if not url.hostname:
        print("В URL отсутствует имя хоста.", file=sys.stderr)
        return False

    return True


def measure_downloads(address: str) -> tuple[int, float, float]:
    total_bytes = 0
    total_seconds = 0.0

    for _ in range(REQUEST_COUNT):
        downloaded_bytes, elapsed_seconds = download_once(address)
        total_bytes += downloaded_bytes
        total_seconds += elapsed_seconds
        print(f"Скачано {downloaded_bytes} байт за {elapsed_seconds:.3f} с")

    if total_seconds <= 0:
        raise ValueError("Суммарное время замера должно быть положительным.")

    average_ms = total_seconds * 1000 / REQUEST_COUNT
    speed_mbps = total_bytes * 8 / total_seconds / 1_000_000
    return total_bytes, average_ms, speed_mbps


def download_once(address: str) -> tuple[int, float]:
    started_at = perf_counter()
    downloaded_bytes = 0

    try:
        response = urlopen(address, timeout=TIMEOUT)
    except HTTPError as error:
        error.close()
        raise

    with response:
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            downloaded_bytes += len(chunk)

        content_length = response.headers.get("Content-Length")
        if content_length and content_length.isdecimal():
            if downloaded_bytes != int(content_length):
                raise OSError("Ответ получен не полностью.")

        return downloaded_bytes, perf_counter() - started_at


if __name__ == "__main__":
    raise SystemExit(main())
