import re

from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse

RANGE_PATTERN = re.compile(r'^bytes=(\d*)-(\d*)$')
CHUNK_SIZE = 64 * 1024


def open_or_404(field_file):
    try:
        return field_file.storage.open(field_file.name, 'rb')
    except FileNotFoundError:
        raise Http404('Файл не найден')


def parse_range(header, size):
    match = RANGE_PATTERN.match(header.strip())
    if not match:
        return None
    first, last = match.groups()
    if first:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    elif last:
        start = max(size - int(last), 0)
        end = size - 1
    else:
        return None
    return start, end


def iter_chunks(handle, start, length):
    try:
        handle.seek(start)
        while length > 0:
            chunk = handle.read(min(CHUNK_SIZE, length))
            if not chunk:
                break
            length -= len(chunk)
            yield chunk
    finally:
        handle.close()


def ranged_file_response(request, field_file, content_type):
    handle = open_or_404(field_file)
    size = handle.size
    byte_range = parse_range(request.headers.get('Range', ''), size)

    if byte_range is None:
        response = FileResponse(handle, content_type=content_type)
    else:
        start, end = byte_range
        if start > end:
            handle.close()
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{size}'
            return response
        length = end - start + 1
        response = StreamingHttpResponse(iter_chunks(handle, start, length), status=206, content_type=content_type)
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'

    response['Accept-Ranges'] = 'bytes'
    return response
