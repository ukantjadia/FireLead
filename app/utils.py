from urllib.parse import urlparse

def trim_and_format_url(url: str) -> str:
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    formatted_url = base_url + "*"
    return formatted_url
