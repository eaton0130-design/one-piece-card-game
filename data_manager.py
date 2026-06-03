# data_manager.py
import json
import os
import game_state

def load_json(filepath, default_data):
    """讀取 JSON，若不存在則以預設值建立"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """寫入 JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_player_data():
    """快速儲存玩家進度"""
    save_json("player_data.json", game_state.player_data)