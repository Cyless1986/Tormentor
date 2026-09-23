"""Checks for the loopback portal behind a trusted HTTPS reverse proxy."""
import os
import time
import threading
from collections import deque
from urllib.parse import urlsplit

PUBLIC_ORIGIN=os.environ.get('TORMENTOR_PUBLIC_ORIGIN','').rstrip('/')
if PUBLIC_ORIGIN and (urlsplit(PUBLIC_ORIGIN).scheme!='https' or not urlsplit(PUBLIC_ORIGIN).netloc or urlsplit(PUBLIC_ORIGIN).path):
    raise ValueError('TORMENTOR_PUBLIC_ORIGIN muss eine HTTPS-Origin ohne Pfad sein.')
_requests={}
_lock=threading.Lock()

def cookie(value):
    return value+('; Secure' if PUBLIC_ORIGIN and 'Secure' not in value else '')

def allowed_post(headers):
    if headers.get('Sec-Fetch-Site')=='cross-site':return False
    expected=PUBLIC_ORIGIN or 'http://'+headers.get('Host','')
    origin=headers.get('Origin')
    if origin:return origin==expected
    referer=headers.get('Referer')
    if referer:
        p=urlsplit(referer)
        return p.scheme+'://'+p.netloc==expected
    return not PUBLIC_ORIGIN

def allow_auth(address,headers):
    # Only trust the proxy header in the explicitly configured production mode.
    key=headers.get('X-Forwarded-For',address).split(',')[-1].strip() if PUBLIC_ORIGIN and address in ('127.0.0.1','::1') else address
    now=time.monotonic()
    with _lock:
        for old in list(_requests):
            if not _requests[old] or _requests[old][-1]<now-300:del _requests[old]
        if key not in _requests and len(_requests)>=4096:return False
        q=_requests.setdefault(key,deque())
        while q and q[0]<now-300:q.popleft()
        if len(q)>=15:return False
        q.append(now)
        return True
