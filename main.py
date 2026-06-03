# main.py
import sys
import os

# 確保可以導入同目錄的其他模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import game_state
from data_manager import load_json, save_player_data
from story import play_story_mode
from battle import battle
from gacha import gacha

def load_all_data():
    """載入所有 JSON 設定與存檔，更新 game_state 中的全域變數"""
    # 載入設定檔
    game_state.config = load_json("config.json", {})
    
    # 載入玩家資料（並補上預設值）
    game_state.player_data.update(load_json("player_data.json", {
        "money": 200,
        "my_chars": ["魯夫"],
        "last_free_gacha": 0
    }))
    
    # 載入技能與劇情資料
    game_state.SKILL_DATA.update(load_json("skills.json", {}))
    game_state.STORY_CHRONICLE.extend(load_json("story.json", []))
    
    # 從 config 讀取系統參數
    game_state.SOUND_FOLDER = game_state.config.get("SOUND_FOLDER", "sounds")
    game_state.GACHA_COST = game_state.config.get("GACHA_COST", 100)
    game_state.FREE_GACHA_COOLDOWN = game_state.config.get("FREE_GACHA_COOLDOWN", 3600)
    game_state.NPC_ENEMY_BLACKLIST = game_state.config.get("NPC_ENEMY_BLACKLIST", ["西格"])
    
    # 確保 story_index 存在
    if "story_index" not in game_state.player_data:
        game_state.player_data["story_index"] = 0
        save_player_data()

def main_menu():
    while True:
        current_team = ', '.join(game_state.player_data['my_chars'])
        print(f"\n===== 🏴‍☠️ 航海王音效卡牌遊戲 ===== (💰 {game_state.player_data['money']} 貝里)")
        print(f"目前夥伴: {current_team}")
        print("1. 觀看劇情模式")
        print("2. 進入自由戰鬥 (贏取貝里)")
        print("3. 角色抽卡 (每小時免費一次)")
        print("4. 結束冒險")
        choice = input("請選擇: ")
        
        if choice == '1':
            play_story_mode()
        elif choice == '2':
            battle()
        elif choice == '3':
            gacha()
        elif choice == '4':
            print("期待下次與你航行！")
            break

if __name__ == "__main__":
    load_all_data()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n遊戲已關閉。")