import random
import subprocess
import time
import os
import threading
import json

# --- JSON 檔案唯讀與寫入管理 ---
def load_json(filepath, default_data):
    """讀取 JSON，如果檔案不存在則自動建立並寫入預設值"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """將資料寫入 JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_player_data():
    """快速儲存玩家進度"""
    save_json("player_data.json", player_data)

# --- 讀取所有 JSON 資料 ---
# 修正黑名單重複：config.json 不存在時只給空字典，預設值在後續用 get 提供
config = load_json("config.json", {})
player_data = load_json("player_data.json", {"money": 200, "my_chars": ["魯夫"], "last_free_gacha": 0})
SKILL_DATA = load_json("skills.json", {})
STORY_CHRONICLE = load_json("story.json", [])

# 基礎系統設定解析（提供預設值）
SOUND_FOLDER = config.get("SOUND_FOLDER", "sounds")
GACHA_COST = config.get("GACHA_COST", 100)
FREE_GACHA_COOLDOWN = config.get("FREE_GACHA_COOLDOWN", 3600)
NPC_ENEMY_BLACKLIST = config.get("NPC_ENEMY_BLACKLIST", ["西格"])

# 確保 player_data 有 story_index 欄位（劇情進度）
if "story_index" not in player_data:
    player_data["story_index"] = 0
    save_player_data()

# --- 音效播放模組 ---
def play_voice(filename, block=True):
    path = os.path.join(SOUND_FOLDER, filename)
    if not os.path.exists(path):
        print(f"(音效缺失: {path})")
        return None
    if block:
        cmd = ['ffplay', '-nodisp', '-autoexit', path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return None
    else:
        cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc

# --- 小遊戲：聽音格擋 ---
def timing_defense_game():
    attack_sound = "story/attack_1.mp3"
    print("\n⚔️ 【魯夫挺身保護克比！】")
    print("👂 仔細聽！士兵的吶喊與刀砍聲出現時，『立刻』按 Enter！")
    print("⚠️  太早或太晚都會失敗，必須重來！")
    input("👉 準備好了嗎？按 Enter 開始...")
    
    delay = random.uniform(1.0, 3.0)
    print(f"\n⏳ 敵人舉起刀... 隨時會砍下！（{delay:.1f} 秒後）")
    time.sleep(delay)
    
    proc = play_voice(attack_sound, block=False)
    if proc is None:
        print("❌ 攻擊音效遺失！請確認 sounds/story/attack_1.mp3 存在")
        return False
    start_time = time.time()
    
    try:
        input()
    except KeyboardInterrupt:
        proc.terminate()
        raise
    end_time = time.time()
    proc.terminate()
    
    delta = end_time - start_time
    if 0.15 <= delta <= 0.7:
        print(f"\n✨ 漂亮！魯夫精準格擋！ (反應時間 {delta:.2f} 秒)")
        return True
    else:
        print(f"\n💥 格擋失敗！ (反應時間 {delta:.2f} 秒)")
        if delta < 0.15:
            print("   你按得太早了，刀還沒落下！")
        else:
            print("   你按得太慢了，克比被砍中了！")
        return False

def rocket_statue_game():
    """橡膠火箭撞雕像：聽音效後等待固定秒數，按 Enter 撞擊"""
    print("\n🚀 【橡膠火箭撞雕像】")
    print("魯夫將手臂向後伸長，準備發射橡膠火箭！")
    print("👂 仔細聽橡膠拉伸的音效，音效結束後『約 2 秒』魯夫就會飛出去！")
    print("⚡ 你必須在魯夫飛出去的『瞬間』按下 Enter！")
    print("⚠️  太早或太晚都會失敗，必須重來！")
    input("👉 準備好了嗎？按 Enter 開始...")

    # 固定延遲 2 秒（可改為 random.uniform(1.5, 2.5) 增加變化）
    delay = 2.0
    print(f"\n⏳ 橡膠伸長... 將在 {delay} 秒後射出！")
    
    # 播放橡膠拉伸音效（背景播放）
    charge_sound = "story/gomu_rocket_charge.mp3"
    proc = play_voice(charge_sound, block=False)
    if proc is None:
        print("⚠️ 橡膠拉伸音效遺失，仍可進行小遊戲（請自行計時）")
    
    # 等待指定秒數
    time.sleep(delay)
    
    # 到達射出瞬間，記錄時間
    start_time = time.time()
    print("💥 現在！快按 Enter！")
    
    # 如果音效還在播放，強制終止（避免干擾）
    if proc:
        proc.terminate()
    
    try:
        input()
    except KeyboardInterrupt:
        raise
    
    end_time = time.time()
    delta = end_time - start_time
    
    # 成功窗口：0.2 秒內
    if delta <= 0.2:
        print(f"\n✨ 漂亮！橡膠火箭精準撞毀雕像！ (反應時間 {delta:.2f} 秒)")
        return True
    else:
        print(f"\n💥 撞歪了！ (反應時間 {delta:.2f} 秒，要在 0.2 秒內)")
        if delta < 0:
            print("   你按得太早了，魯夫還沒飛出去！")
        else:
            print("   你按得太慢了，撞到旁邊的牆壁！")
        return False

def sword_pick_game():
    """猜刀小游戏（温和版）：从三个箱子中连续猜对三次，每次猜错只重置当前这把刀"""
    print("\n🗡️ 【尋找索隆的刀】")
    print("魯夫面前有三個箱子，裡面只有一個藏有索隆的一把刀。")
    print("你必須連續選對三次，才能拿到全部三把刀（和道一文字、三代鬼徹、雪走）。")
    print("⚠️  猜錯的話，當前這把刀會重新洗牌，但不影響已經拿到的刀。")
    input("👉 按 Enter 開始...")
    
    swords = ["和道一文字", "三代鬼徹", "雪走"]
    found = 0  # 已成功拿到的刀數
    attempts = 0  # 記錄總嘗試次數（可選）
    
    while found < 3:
        # 隨機決定真刀的位置 (0, 1, 2)
        true_pos = random.randint(0, 2)
        print(f"\n🔍 尋找第 {found+1} 把刀（{swords[found]}）")
        print("   [1] ？   [2] ？   [3] ？")
        try:
            choice = int(input("你要選哪一個？ (1-3): "))
            if choice not in [1, 2, 3]:
                print("請輸入 1、2 或 3。")
                continue
        except ValueError:
            print("請輸入數字。")
            continue
        
        idx = choice - 1
        if idx == true_pos:
            print(f"\n✨ 恭喜！你拿到了 {swords[found]}！")
            found += 1
        else:
            print("\n❌ 可惜，這只是個空箱子。三個箱子重新洗牌，再試一次！")
            # 温和版：只重置当前这把刀，不减少 found
            # 继续循环，重新随机 true_pos
    
    print("\n🎉 太棒了！你成功拿到了索隆的全部三把刀！")
    print("索隆：『謝了，魯夫。我欠你一次。』")
    return True

# --- 戰鬥函數，回傳是否勝利 ---
def battle(specific_enemy=None, specific_hp=None):
    if not player_data["my_chars"]:
        print("你沒有可以上場的角色！")
        return False

    # ---------- 選擇出戰角色 ----------
    print("\n--- 選擇你的出戰角色 ---")
    for i, char in enumerate(player_data["my_chars"]):
        print(f"{i}. {char}")
    try:
        char_idx = int(input("請輸入編號: "))
        p_char = player_data["my_chars"][char_idx]
    except (ValueError, IndexError):
        print("❌ 無效的選擇。")
        return False

    # ---------- 決定敵人 ----------
    if specific_enemy and specific_hp:
        e_name = specific_enemy
        e_hp = specific_hp
    else:
        enemies = [enemy for enemy in SKILL_DATA.keys() if enemy not in NPC_ENEMY_BLACKLIST]
        if not enemies:
            print("❌ 目前沒有可挑戰的自由對手！")
            return False
        print("\n--- 選擇你的對手 ---")
        for i, enemy in enumerate(enemies):
            print(f"{i}. {enemy}")
        try:
            enemy_idx = int(input("請輸入編號: "))
            e_name = enemies[enemy_idx]
        except (ValueError, IndexError):
            print("❌ 無效的選擇。")
            return False
        e_hp = 500

    # ---------- 戰鬥初始值 ----------
    p_hp = 500
    p_effects = []   # 玩家身上的持續效果
    e_effects = []   # 敵人身上的持續效果

    print(f"\n⚔️ 戰鬥開始：{p_char} VS 【{e_name}】")

    # ---------- 輔助函式：處理持續傷害 ----------
    def apply_dot(effects, owner_name):
        """回傳總傷害值"""
        total = 0
        for eff in effects[:]:   # 遍歷副本，以便移除
            if eff["type"] in ("sandstorm", "poison"):
                dmg = eff.get("damage_per_turn", 0)
                total += dmg
                print(f"💨 {owner_name} 受到 {eff['type']} 影響，損失 {dmg} HP！")
            # 未來可擴充其他效果（如回血、麻痺等）
        return total

    def update_effects(effects):
        """減少持續回合，移除過期效果"""
        for eff in effects[:]:
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                print(f"✅ {eff['type']} 效果消失了。")
                effects.remove(eff)

    # ---------- 戰鬥主迴圈 ----------
    while e_hp > 0 and p_hp > 0:
        # ----- 回合開始：處理持續傷害 -----
        p_dot = apply_dot(p_effects, p_char)
        p_hp -= p_dot
        if p_hp <= 0:
            break
        e_dot = apply_dot(e_effects, e_name)
        e_hp -= e_dot
        if e_hp <= 0:
            break

        # ----- 顯示血量 -----
        print(f"\n【{p_char}】HP: {p_hp} | 【{e_name}】HP: {e_hp}")

        # ----- 玩家行動選單 -----
        action = input("👉 請選擇：1. 攻擊  2. 防禦 : ")
        defending = (action == "2")
        if defending:
            print(f"🛡️ {p_char} 採取防禦姿態，本回合受到的傷害減半！")

        # ----- 玩家攻擊（若不防禦）-----
        if not defending:
            p_skills = SKILL_DATA.get(p_char, [{"skill": "普通攻擊", "dmg": 10}])
            p_card = random.choice(p_skills)
            print(f"🃏 你使用 {p_card['skill']}！")
            if 'audio' in p_card:
                play_voice(p_card['audio'])
            # 計算傷害
            p_dmg = sum(p_card['dmg_list']) if "dmg_list" in p_card else p_card['dmg']
            e_hp -= p_dmg
            print(f"💥 造成 {p_dmg} 傷害！")

            # 附加效果（若有）
            if "effects" in p_card:
                for effect in p_card["effects"]:
                    # 複製一份，避免修改原始資料
                    new_effect = effect.copy()
                    e_effects.append(new_effect)
                    print(f"✨ {e_name} 中了 {new_effect['type']} 效果！")

        # 若敵人已死，跳出
        if e_hp <= 0:
            break

        # ----- 敵人反擊 -----
        print(f"\n🌀 {e_name} 反擊！")
        time.sleep(1)

        enemy_skills = SKILL_DATA.get(e_name, [{"skill": "普通攻擊", "dmg": 10}])
        e_card = random.choice(enemy_skills)
        print(f"💢 使用了 {e_card['skill']}！")
        if 'audio' in e_card:
            play_voice(e_card['audio'])
        e_dmg = sum(e_card['dmg_list']) if "dmg_list" in e_card else e_card['dmg']
        if defending:
            e_dmg = e_dmg // 2
            print(f"🛡️ 防禦成功！實際傷害減半為 {e_dmg}")
        p_hp -= e_dmg
        print(f"💥 受到 {e_dmg} 傷害！")

        # 敵人附加效果
        if "effects" in e_card:
            for effect in e_card["effects"]:
                new_effect = effect.copy()
                p_effects.append(new_effect)
                print(f"✨ {p_char} 中了 {new_effect['type']} 效果！")

        # ----- 回合結束：減少效果持續時間 -----
        update_effects(p_effects)
        update_effects(e_effects)

    # ---------- 戰鬥結算 ----------
    if p_hp > 0:
        reward = random.randint(50, 150)
        player_data["money"] += reward
        print(f"\n🏆 勝利！成功打飛了 {e_name}！獲得戰利品 {reward} 貝里！")
        play_voice("system/victory.mp3")
        save_player_data()
        return True
    else:
        print(f"\n💀 你被 {e_name} 擊敗了...")
        return False

# --- 劇情模式（支援進度記錄，戰鬥勝利才推進）---
def play_story_mode():
    print("\n📖 --- 進入劇情模式 ---")
    
    # 讀取上次進度
    start_idx = player_data.get("story_index", 0)
    if start_idx >= len(STORY_CHRONICLE):
        print("🎉 你已經看完所有目前的劇情！等待後續更新～")
        return
    
    # 詢問是否從頭開始
    if start_idx > 0:
        choice = input(f"上次你玩到第 {start_idx} 段劇情，要從頭開始嗎？(y/n，預設 n): ")
        if choice.lower() == 'y':
            start_idx = 0
            player_data["story_index"] = 0
            save_player_data()
    
    idx = start_idx
    while idx < len(STORY_CHRONICLE):
        scene = STORY_CHRONICLE[idx]
        
        # 特殊處理 id=3 的小遊戲
        if scene.get("id") == 3:
            # 詢問是否跳過劇情文字
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過此段劇情直接進入格擋: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                play_voice(scene['audio'])
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")
            
            # 進行小遊戲直到成功
            success = False
            while not success:
                success = timing_defense_game()
                if not success:
                    retry = input("\n🔄 重來一次？(y/n): ").lower()
                    if retry != 'y':
                        print("你選擇中斷劇情，返回主選單。")
                        return
            
            # 小遊戲成功後，自動跳到 id4 劇情
            next_idx = idx + 1
            while next_idx < len(STORY_CHRONICLE) and STORY_CHRONICLE[next_idx].get("id") != 4:
                next_idx += 1
            if next_idx < len(STORY_CHRONICLE):
                scene4 = STORY_CHRONICLE[next_idx]
                print(f"\n🎬 {scene4['title']}")
                print(f"💬 {scene4['desc']}")
                play_voice(scene4['audio'])
                input("\n[按 Enter 繼續...]")
                # 進度推進到 id4 之後
                idx = next_idx + 1
            else:
                print("\n⚠️  找不到 id4 的劇情，但小遊戲成功結束。")
                idx += 1
            
            # 儲存進度
            player_data["story_index"] = idx
            save_player_data()
            continue

        # 撞雕像小遊戲（第二集）
        if scene.get("id") == 8:
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過直接開始撞雕像: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                if scene.get('audio'):
                    play_voice(scene['audio'])
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")
            
            success = False
            while not success:
                success = rocket_statue_game()
                if not success:
                    retry = input("\n🔄 重來一次？(y/n): ").lower()
                    if retry != 'y':
                        print("你選擇中斷劇情，返回主選單。")
                        return
            
            idx += 1
            player_data["story_index"] = idx
            save_player_data()
            print("\n✅ 雕像粉碎！魯夫抓住了貝魯梅伯，逼問索隆的刀藏在哪裡...")
            input("[按 Enter 繼續]")
            continue

        # 猜刀小遊戲（第二集，溫和版）
        if scene.get("id") == 9:
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過直接開始找刀: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                if scene.get('audio'):
                    play_voice(scene['audio'])
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")
            
            # 進行小遊戲直到成功
            success = sword_pick_game()
            # 游戏内部循环直到成功，所以这里直接继续
            
            idx += 1
            player_data["story_index"] = idx
            save_player_data()
            print("\n✅ 成功取得三把刀，索隆被釋放，決定跟隨魯夫！")
            input("[按 Enter 繼續]")
            continue
        
        # 一般劇情處理（含戰鬥）
        choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看，輸入 s 跳過此段劇情: ")
        if choice.lower() == 's':
            print(f"⏩ 跳過「{scene['title']}」的劇情內容。")
            # 如果有戰鬥，仍需進行戰鬥（跳過劇情文字與音效）
            if scene.get("trigger_battle") == True:
                enemy_name = scene.get("target_enemy", "隨機對手")
                enemy_hp = scene.get("target_hp", 500)
                print(f"\n🔥 [警告] 劇情觸發戰鬥！正面迎擊【{enemy_name}】！")
                time.sleep(1)
                victory = battle(specific_enemy=enemy_name, specific_hp=enemy_hp)
                if not victory:
                    print("戰鬥失敗，劇情無法推進。請重新挑戰。")
                    return   # 戰鬥失敗，不推進進度，直接返回主選單
            # 跳過且無戰鬥，或戰鬥勝利，則推進進度
            idx += 1
            player_data["story_index"] = idx
            save_player_data()
            continue
        
        # 正常觀看：顯示標題、描述、播放音效
        print(f"\n🎬 {scene['title']}")
        print(f"💬 {scene['desc']}")
        play_voice(scene['audio'])
        
        # 戰鬥處理
        if scene.get("trigger_battle") == True:
            enemy_name = scene.get("target_enemy", "隨機對手")
            enemy_hp = scene.get("target_hp", 500)
            print(f"\n🔥 [警告] 劇情觸發戰鬥！正面迎擊【{enemy_name}】！")
            time.sleep(1)
            victory = battle(specific_enemy=enemy_name, specific_hp=enemy_hp)
            if not victory:
                print("戰鬥失敗，劇情無法推進。請重新挑戰。")
                return
        else:
            input("\n[按 Enter 繼續下一段劇情...]")
        
        # 完成此段劇情（戰鬥勝利或無戰鬥），推進索引
        idx += 1
        player_data["story_index"] = idx
        save_player_data()
    
    # 所有劇情播放完畢
    print("\n✅ 目前劇情已播放完畢，期待後續更新！")
    # 可選擇重置進度（讓玩家再看時從頭），這裡不自動重置，保留在結尾
    # 如果想讓玩家重看，手動從主選單重置？可以之後加功能。

# --- 抽卡系統（不變，但已使用黑名單）---
def gacha():
    current_time = time.time()
    time_passed = current_time - player_data.get("last_free_gacha", 0)
    
    print(f"\n💰 目前錢包: {player_data['money']} 貝里")
    
    is_free = False
    if time_passed >= FREE_GACHA_COOLDOWN:
        print("🎁 喔！現在有一次【免費抽卡】的機會！")
        is_free = True
    else:
        remaining = int(FREE_GACHA_COOLDOWN - time_passed)
        print(f"⏳ 下次免費抽卡還需等待: {remaining // 60} 分 {remaining % 60} 秒")
        print(f"💡 或者你可以花費 {GACHA_COST} 貝里直接抽取。")

    if is_free:
        choice = input("確認使用免費次數抽卡嗎？ (y/n): ")
        if choice.lower() != 'y': return
        player_data["last_free_gacha"] = current_time
    else:
        if player_data["money"] < GACHA_COST:
            print("❌ 貝里不足！快去戰鬥賺錢吧！")
            return
        choice = input(f"確認花費 {GACHA_COST} 貝里抽卡嗎？ (y/n): ")
        if choice.lower() != 'y': return
        player_data["money"] -= GACHA_COST

    print("\n📦 正在開啟角色卡包...")
    play_voice("system/gacha_open.mp3")
    time.sleep(1.5)
    
    all_available = [char for char in SKILL_DATA.keys() if char not in NPC_ENEMY_BLACKLIST]
    if not all_available:
        print("❌ 角色卡池目前沒有可抽取的夥伴！")
        return

    new_char = random.choice(all_available)
    
    if new_char not in player_data["my_chars"]:
        player_data["my_chars"].append(new_char)
        print(f"🎊 恭喜！你抽到了新角色：【{new_char}】！")
    else:
        print(f"😅 抽到了重複的角色：【{new_char}】。轉換為補償金 20 貝里！")
        player_data["money"] += 20
    
    save_player_data()

# --- 主選單 ---
def main_menu():
    while True:
        current_team = ', '.join(player_data['my_chars'])
        print(f"\n===== 🏴‍☠️ 航海王音效卡牌遊戲 ===== (💰 {player_data['money']} 貝里)")
        print(f"目前夥伴: {current_team}")
        print("1. 觀看劇情模式")
        print("2. 進入自由戰鬥 (贏取貝里)")
        print("3. 角色抽卡 (每小時免費一次)")
        print("4. 結束冒險")
        choice = input("請選擇: ")

        if choice == '1':
            play_story_mode()
        elif choice == '2':
            battle()  # 自由戰鬥，不影響劇情進度
        elif choice == '3':
            gacha()
        elif choice == '4':
            print("期待下次與你航行！")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n遊戲已關閉。")