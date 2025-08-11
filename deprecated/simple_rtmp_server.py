#!/usr/bin/env python3
"""Simple RTMP relay server using subprocess"""

import subprocess
import sys

print("Starting simple RTMP server on rtmp://localhost/live/stream")
print("Press Ctrl+C to stop")

# Use ffmpeg to create a simple RTMP server
cmd = [
    'ffmpeg',
    '-listen', '1',
    '-i', 'rtmp://localhost/live/stream',
    '-c', 'copy',
    '-f', 'flv',
    'rtmp://localhost/live/stream_out'
]

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\nServer stopped")
    sys.exit(0)