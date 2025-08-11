#!/usr/bin/env python3
"""
Simple streaming solution using direct FFmpeg screen capture
More reliable than piping frames through Python
"""

import subprocess
import time
import signal
import sys

class SimpleStreamer:
    """Direct FFmpeg screen capture to RTSP/RTMP/HLS"""
    
    def __init__(self):
        # Default glasses stream position
        self.x = 40
        self.y = 330
        self.width = 340
        self.height = 230
        self.process = None
        
    def stream_rtsp(self, output_url="rtsp://localhost:8554/glasses"):
        """Stream via RTSP using FFmpeg directly"""
        print(f"Starting RTSP stream to: {output_url}")
        print("Make sure mediamtx is running (mediamtx in another terminal)")
        
        command = [
            'ffmpeg',
            '-f', 'avfoundation',  # macOS screen capture
            '-capture_cursor', '0',  # Don't capture cursor
            '-framerate', '30',
            '-pix_fmt', 'uyvy422',  # Native pixel format
            '-i', '3:none',  # Capture screen 0, NO audio
            '-vf', f'crop={self.width}:{self.height}:{self.x}:{self.y},format=yuv420p',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-b:v', '2M',  # Bitrate limit
            '-maxrate', '2M',
            '-bufsize', '4M',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            output_url
        ]
        
        self.process = subprocess.Popen(command)
        print(f"\n✅ Streaming! Connect with VLC: {output_url}")
        return self.process
        
    def stream_hls(self, output_dir="./hls"):
        """Stream as HLS (HTTP Live Streaming) for web browsers"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Starting HLS stream to: {output_dir}")
        
        command = [
            'ffmpeg',
            '-f', 'avfoundation',
            '-i', '3:0',
            '-vf', f'crop={self.width}:{self.height}:{self.x}:{self.y}',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-pix_fmt', 'yuv420p',
            '-hls_time', '2',  # 2 second segments
            '-hls_list_size', '10',  # Keep 10 segments
            '-hls_flags', 'delete_segments',
            '-hls_segment_filename', f'{output_dir}/segment_%03d.ts',
            f'{output_dir}/stream.m3u8'
        ]
        
        self.process = subprocess.Popen(command)
        print(f"\n✅ HLS Streaming! Serve {output_dir} with any HTTP server")
        print("Example: python3 -m http.server 8000 --directory hls")
        print("Then open: http://localhost:8000/stream.m3u8 in Safari or with VLC")
        return self.process
        
    def stream_file(self, output_file="glasses_stream.mp4"):
        """Record stream to file"""
        print(f"Recording to: {output_file}")
        
        command = [
            'ffmpeg',
            '-f', 'avfoundation',
            '-i', '3:0',
            '-vf', f'crop={self.width}:{self.height}:{self.x}:{self.y}',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-pix_fmt', 'yuv420p',
            output_file
        ]
        
        self.process = subprocess.Popen(command)
        print(f"\n✅ Recording! Press Ctrl+C to stop")
        return self.process
        
    def stream_udp(self, output_url="udp://localhost:1234"):
        """Stream via UDP (lowest latency)"""
        print(f"Starting UDP stream to: {output_url}")
        
        command = [
            'ffmpeg',
            '-f', 'avfoundation',
            '-i', '3:0',
            '-vf', f'crop={self.width}:{self.height}:{self.x}:{self.y}',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-pix_fmt', 'yuv420p',
            '-f', 'mpegts',
            output_url
        ]
        
        self.process = subprocess.Popen(command)
        print(f"\n✅ UDP Streaming!")
        print(f"View with: ffplay {output_url}")
        return self.process
        
    def stop(self):
        """Stop streaming"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("\nStream stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nStopping stream...")
    sys.exit(0)

def main():
    """Interactive streaming menu"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=== Simple Glasses Streamer ===")
    print("\n1. RTSP Stream (VLC, OBS)")
    print("2. HLS Stream (Web browsers)")
    print("3. UDP Stream (Ultra low latency)")
    print("4. Record to File")
    print("5. Custom FFmpeg command")
    
    choice = input("\nSelect option (1-5): ")
    
    streamer = SimpleStreamer()
    
    if choice == '1':
        # First ensure mediamtx is running
        print("\nChecking for RTSP server...")
        try:
            subprocess.run(['pgrep', 'mediamtx'], check=True, capture_output=True)
            print("✅ RTSP server running")
        except:
            print("Starting RTSP server...")
            subprocess.Popen(['mediamtx'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            
        process = streamer.stream_rtsp()
        
    elif choice == '2':
        process = streamer.stream_hls()
        
    elif choice == '3':
        process = streamer.stream_udp()
        
    elif choice == '4':
        filename = input("Output filename (default: glasses_stream.mp4): ") or "glasses_stream.mp4"
        process = streamer.stream_file(filename)
        
    elif choice == '5':
        print("\nCustom FFmpeg command")
        print("Base: ffmpeg -f avfoundation -i 3:0 -vf crop=340:230:40:330 ...")
        extra = input("Add your FFmpeg options: ")
        
        command = f"ffmpeg -f avfoundation -i 3:0 -vf crop=340:230:40:330 {extra}"
        print(f"\nRunning: {command}")
        process = subprocess.Popen(command, shell=True)
    else:
        print("Invalid option")
        return
        
    # Wait for process
    try:
        process.wait()
    except KeyboardInterrupt:
        streamer.stop()

if __name__ == "__main__":
    main()