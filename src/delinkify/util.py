from pathlib import Path


def clean_url(url: str) -> str:
    """Clean a URL by removing query parameters and fragments."""
    cleaned_url = url.split('?', 1)[0].split('#', 1)[0]
    return cleaned_url.strip('/')


def get_cookie_file_path(handler: str) -> str | None:
    """Get the path to the cookie file if it exists."""

    cookie_path = Path(__file__).parent.parent.parent / 'cookies' / f'{handler}.txt'
    if cookie_path.exists():
        return str(cookie_path)
    return None
