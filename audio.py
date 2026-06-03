# audio.py
import subprocess
import os
import game_state
import sys

# 取得遊戲根目錄（main.py 所在目錄）
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
FFPLAY_PATH = os.path.join(BASE_DIR, "bin", "ffplay.exe")

def play_voice(filename, block=True):
    """播放音效，使用內建的 ffplay.exe"""
    path = os.path.join(game_state.SOUND_FOLDER, filename)
    if not os.path.exists(path):
        print(f"(音效缺失: {path})")
        return None
    cmd = [FFPLAY_PATH, '-nodisp', '-autoexit']
    if not block:
        cmd.append('-loglevel')
        cmd.append('quiet')
    cmd.append(path)
    if block:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return None
    else:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc