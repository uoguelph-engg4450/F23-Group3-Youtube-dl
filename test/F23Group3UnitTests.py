#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import re
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import (
    FakeLogger,
    http_server_port,
    try_rm,
)
from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
from youtube_dl.downloader.http import HttpFD
from youtube_dl.utils import encodeFilename
from youtube_dl.utils import DownloadError
import threading

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


TEST_SIZE = 10 * 1024


class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    
    # Predefined functions to setup HttpFD and youtube_dl's parameters
    def log_message(self, format, *args):
        pass

    def send_content_range(self, total=None):
        range_header = self.headers.get('Range')
        start = end = None
        if range_header:
            mobj = re.search(r'^bytes=(\d+)-(\d+)', range_header)
            if mobj:
                start = int(mobj.group(1))
                end = int(mobj.group(2))
        valid_range = start is not None and end is not None
        if valid_range:
            content_range = 'bytes %d-%d' % (start, end)
            if total:
                content_range += '/%d' % total
            self.send_header('Content-Range', content_range)
        return (end - start + 1) if valid_range else total

    def serve(self, range=True, content_length=True):
        self.send_response(200)
        self.send_header('Content-Type', 'video/mp4')
        size = TEST_SIZE
        if range:
            size = self.send_content_range(TEST_SIZE)
        if content_length:
            self.send_header('Content-Length', size)
        self.end_headers()
        self.wfile.write(b'#' * size)

    def do_GET(self):
        if self.path == '/regular':
            self.serve()
        elif self.path == '/no-content-length':
            self.serve(content_length=False)
        elif self.path == '/no-range':
            self.serve(range=False)
        elif self.path == '/no-range-no-content-length':
            self.serve(range=False, content_length=False)
        else:
            assert False


class TestHttpFD(unittest.TestCase):
    #Predefined setup using previously made unit tests
    def setUp(self):
        self.httpd = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), HTTPTestRequestHandler)
        self.port = http_server_port(self.httpd)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def download(self, params, ep):
        params['logger'] = FakeLogger()
        ydl = YoutubeDL(params)
        downloader = HttpFD(ydl, params)
        
        #Custom unit test
        filename = '2 Second Timer-H3dJWJ2pE9U.mp4'
        try_rm(encodeFilename(filename))

        # Test if a DownloadError is raised during download with slow speed (Can be forced if delay is set to 0 and minimum download
        # rate is set to high in http.py)
        #Takes 100 seconds to run
        with self.assertRaises(DownloadError):
            downloader.real_download(filename, {
                'url': 'https://www.youtube.com/watch?v=H3dJWJ2pE9U',
            })

    def download_all(self, params):
        for ep in ('regular'):
            self.download(params, ep)

    def test_regular(self):
        self.download_all({})