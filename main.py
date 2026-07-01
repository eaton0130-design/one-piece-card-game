# main.py
import sys
import os
import time
if os.environ.get("LAUNCHED_FROM_BAT") != "TRUE":
    print(" ❌ 錯誤：請勿直接執行 main.py！")
    print("請使用遊戲資料夾內的開始遊戲.bat來啟動遊戲")
    time.sleep(3)
    sys.exit()

# 確保可以導入同目錄的其他模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import game_state
from data_manager import load_json, save_player_data
from story import play_story
from battle import battle
from gacha import gacha
from upgrade import init_characters, manage_chars
from base import init_base, show_base_menu

def init_data():
    """載入所有 JSON 設定與存檔，更新 game_state 中的全域變數"""
    # 載入設定檔
    game_state.config = load_json("config.json", {})
    
    # 載入玩家資料（並補上預設值）
    game_state.player_data.update(load_json("player_data.json", {
        "money": 200,
        "my_chars": ["魯夫"],
        "last_free_gacha": 0,
        # characters 結構會在啟動時補齊（等級、經驗、技能點、技能等級）
        "characters": {}
    }))
    
    # 載入技能與劇情資料
    game_state.SKILL_DATA.update(load_json("skills.json", {}))
    game_state.STORY_CHRONICLE.extend(load_json("story.json", []))
    
    # 從 config 讀取系統參數
    game_state.SOUND_FOLDER = game_state.config.get("SOUND_FOLDER", "sounds")
    game_state.GACHA_COST = game_state.config.get("GACHA_COST", 100)
    game_state.FREE_GACHA_COOLDOWN = game_state.config.get("FREE_GACHA_COOLDOWN", 3600)
    game_state.NPC_ENEMY_BLACKLIST = game_state.config.get("NPC_ENEMY_BLACKLIST", ["西格"])
    
    # 確保劇情進度欄位存在，避免不同模式互相衝突
    if "story_index" not in game_state.player_data:
        game_state.player_data["story_index"] = 0
    save_player_data()
    # 確保 characters 結構存在並為 my_chars 補上預設值
    init_characters()
    # 確保基地資料結構初始化
    init_base()

def main_menu():
    while True:
        current_team = ', '.join(game_state.player_data['my_chars'])
        print(f"\n===== 🏴‍☠️ 航海王音效卡牌遊戲 ===== (💰 {game_state.player_data['money']} 貝里)")
        print(f"目前夥伴: {current_team}")
        print("1. 觀看航海王劇情模式")
        print("2. 進入自由戰鬥 (贏取貝里)")
        print("3. 角色抽卡 (每小時免費一次)")
        print("4. 海賊基地 (建築、派遣、資源)")
        print("5. 角色管理與升級")
        print("6. 結束冒險")
        choice = input("請選擇: ")
        
        if choice == '1':
            play_story()
        elif choice == '2':
            battle()
        elif choice == '3':
            gacha()
        elif choice == '4':
            show_base_menu()
        elif choice == '5':
            manage_chars()
        elif choice == '6':
            print("期待下次與你航行！")
            break

if __name__ == "__main__":
    init_data()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n遊戲已關閉。")