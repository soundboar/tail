import asyncio
import re
from pathlib import Path
from typing import Iterable, Collection
import http.client

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException


async def extract_meta(url, *meta_tags: str) -> dict[str, str | None] | None:
    try:
        tags = {}
        # Send a GET request to the URL
        response = await asyncio.to_thread(requests.get, url, headers={'User-Agent': 'Mozilla/5.0'})
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find the og:title meta tag
            for meta_tag in meta_tags:
                value = soup.find("meta", property=meta_tag)
                tags[meta_tag] = value.attrs.get("content") if value else None
            return tags
        else:
            print(f"Error fetching the URL: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def check_valid_audio_url(url: str | None, supported_file_endings: Iterable[str]) -> None:
    if not url:
        raise HTTPException(http.client.BAD_REQUEST, "No audio found.")
    if not url.startswith("http"):
        raise HTTPException(http.client.BAD_REQUEST, "Audio could not be extracted from the website.")
    if not any(map(lambda typ: url.endswith(typ), supported_file_endings)):
        raise HTTPException(http.client.BAD_REQUEST, "Audio file type provided by the site is not supported.")


def to_file_id(requested_id: str, current_filename: str, supported_files: Collection[str]):
    regex = re.compile(r'[^\w\.\-]')
    file_id = regex.sub('_', requested_id)
    if Path(file_id).suffix not in supported_files:
        new_suffix = Path(current_filename).suffix
        if new_suffix in supported_files:
            file_id += new_suffix
        else:
            raise HTTPException(http.client.BAD_REQUEST, "Unsupported file type. Only following are supported: " + ", ".join(supported_files))
    return file_id
