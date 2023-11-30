#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import re
import sys

from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
from youtube_dl.downloader.http import HttpFD
from youtube_dl.utils import encodeFilename
import threading
import pytest

httpFD = HttpFD()