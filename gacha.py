# gacha.py
import random
import time
import game_state
from audio import play_voice
from data_manager import save_player_data

def gacha():
    current_time = time.time()
    time_passed = current_time - game_state.player_data.get("last_free_gacha", 0)
    
    print(f"\n💰 目前錢包: {game_state.player_data['money']} 貝里")
    
    is_free = False
    if time_passed >= game_state.FREE_GACHA_COOLDOWN:
        print("🎁 喔！現在有一次【免費抽卡】的機會！")
        is_free = True
    else:
        remaining = int(game_state.FREE_GACHA_COOLDOWN - time_passed)
        print(f"⏳ 下次免費抽卡還需等待: {remaining // 60} 分 {remaining % 60} 秒")
        print(f"💡 或者你可以花費 {game_state.GACHA_COST} 貝里直接抽取。")

    if is_free:
        choice = input("確認使用免費次數抽卡嗎？ (y/n): ")
        if choice.lower() != 'y':
            return
        game_state.player_data["last_free_gacha"] = current_time
    else:
        if game_state.player_data["money"] < game_state.GACHA_COST:
            print("❌ 貝里不足！快去戰鬥賺錢吧！")
            return
        choice = input(f"確認花費 {game_state.GACHA_COST} 貝里抽卡嗎？ (y/n): ")
        if choice.lower() != 'y':
            return
        game_state.player_data["money"] -= game_state.GACHA_COST

    print("\n📦 正在開啟角色卡包...")
    play_voice("system/gacha_open.mp3")
    time.sleep(1.5)
    
    all_available = [char for char in game_state.SKILL_DATA.keys() if char not in game_state.NPC_ENEMY_BLACKLIST]
    if not all_available:
        print("❌ 角色卡池目前沒有可抽取的夥伴！")
        return

    new_char = random.choice(all_available)
    
    if new_char not in game_state.player_data["my_chars"]:
        game_state.player_data["my_chars"].append(new_char)
        print(f"🎊 恭喜！你抽到了新角色：【{new_char}】！")
    else:
        print(f"😅 抽到了重複的角色：【{new_char}】。轉換為補償金 20 貝里！")
        game_state.player_data["money"] += 20
    
    save_player_data()