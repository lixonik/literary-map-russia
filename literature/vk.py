import html
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from django.core.exceptions import ValidationError

VK_HOSTS = {'vk.com', 'vk.ru', 'vkvideo.ru'}
PLAYER_HOST = 'vk.ru'
IFRAME_SRC = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
VIDEO_LINK = re.compile(r'video(-?\d+)_(\d+)')
OWNER_ID = re.compile(r'-?\d+')
VIDEO_ID = re.compile(r'\d+')
ACCESS_KEY = re.compile(r'[0-9A-Za-z]*')

INVALID_EMBED = (
    'Вставьте ссылку на видео ВКонтакте или код для встраивания: '
    'правый клик по видео, «Копировать код для встраивания».'
)


def normalize_vk_embed(value):
    value = value.strip()
    match = IFRAME_SRC.search(value)
    url = html.unescape(match.group(1) if match else value)
    if url.startswith('//'):
        url = f'https:{url}'

    parts = urlsplit(url)
    host = (parts.hostname or '').removeprefix('www.').removeprefix('m.')
    if parts.scheme not in ('http', 'https') or host not in VK_HOSTS:
        raise ValidationError(INVALID_EMBED)

    params = {key: values[0] for key, values in parse_qs(parts.query).items()}
    if parts.path == '/video_ext.php':
        owner_id, video_id, access_key = params.get('oid', ''), params.get('id', ''), params.get('hash', '')
    else:
        link = VIDEO_LINK.search(f"{parts.path} {params.get('z', '')}")
        if link is None:
            raise ValidationError(INVALID_EMBED)
        (owner_id, video_id), access_key, host = link.groups(), '', PLAYER_HOST

    if not (OWNER_ID.fullmatch(owner_id) and VIDEO_ID.fullmatch(video_id) and ACCESS_KEY.fullmatch(access_key)):
        raise ValidationError(INVALID_EMBED)

    query = {'oid': owner_id, 'id': video_id}
    if access_key:
        query['hash'] = access_key
    return f'https://{host}/video_ext.php?{urlencode(query)}'
