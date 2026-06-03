# battle.py
import random
import time
import game_state
from audio import play_voice
from data_manager import save_player_data

def battle(specific_enemy=None, specific_hp=None):
    """戰鬥函式，回傳是否勝利（True=勝利）"""
    if not game_state.player_data["my_chars"]:
        print("你沒有可以上場的角色！")
        return False

    # 選擇出戰角色
    print("\n--- 選擇你的出戰角色 ---")
    for i, char in enumerate(game_state.player_data["my_chars"]):
        print(f"{i}. {char}")
    try:
        char_idx = int(input("請輸入編號: "))
        p_char = game_state.player_data["my_chars"][char_idx]
    except (ValueError, IndexError):
        print("❌ 無效的選擇。")
        return False

    # 決定敵人
    if specific_enemy and specific_hp:
        e_name = specific_enemy
        e_hp = specific_hp
    else:
        enemies = [enemy for enemy in game_state.SKILL_DATA.keys() if enemy not in game_state.NPC_ENEMY_BLACKLIST]
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

    # 戰鬥初始值
    p_hp = 500
    p_effects = []
    e_effects = []

    print(f"\n⚔️ 戰鬥開始：{p_char} VS 【{e_name}】")

    def apply_dot(effects, owner_name):
        total = 0
        for eff in effects[:]:
            if eff["type"] in ("sandstorm", "poison"):
                dmg = eff.get("damage_per_turn", 0)
                total += dmg
                print(f"💨 {owner_name} 受到 {eff['type']} 影響，損失 {dmg} HP！")
        return total

    def update_effects(effects):
        for eff in effects[:]:
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                print(f"✅ {eff['type']} 效果消失了。")
                effects.remove(eff)

    # ---------- 戰鬥主迴圈 ----------
    while e_hp > 0 and p_hp > 0:
        # 回合開始：持續傷害
        p_dot = apply_dot(p_effects, p_char)
        p_hp -= p_dot
        if p_hp <= 0:
            break
        e_dot = apply_dot(e_effects, e_name)
        e_hp -= e_dot
        if e_hp <= 0:
            break

        print(f"\n【{p_char}】HP: {p_hp} | 【{e_name}】HP: {e_hp}")

        # ----- 玩家回合（可能包含多次行動）-----
        extra_actions = 0               # 額外行動次數
        skip_enemy_turn = False         # 是否跳過本回合敵人反擊
        in_knockback_sequence = False   # 是否正在連段中（禁止再次觸發擊飛）
        player_turn_active = True

        while player_turn_active:
            # 玩家行動選單
            action = input("👉 請選擇：1. 攻擊  2. 防禦 : ")
            defending = (action == "2")
            if defending:
                print(f"🛡️ {p_char} 採取防禦姿態，本回合受到的傷害減半！")

            # 玩家攻擊（若不防禦）
            if not defending:
                p_skills = game_state.SKILL_DATA.get(p_char, [{"skill": "普通攻擊", "dmg": 10}])
                p_card = random.choice(p_skills)
                print(f"🃏 你使用 {p_card['skill']}！")
                if 'audio' in p_card:
                    play_voice(p_card['audio'])
                p_dmg = sum(p_card['dmg_list']) if "dmg_list" in p_card else p_card['dmg']
                e_hp -= p_dmg
                print(f"💥 造成 {p_dmg} 傷害！")

                # 附加效果
                if "effects" in p_card:
                    for effect in p_card["effects"]:
                        new_effect = effect.copy()
                        e_effects.append(new_effect)
                        print(f"✨ {e_name} 中了 {new_effect['type']} 效果！")

                # 擊飛判定：技能帶有 knockback 標記、不在連段中、且隨機機率 30%
                if not in_knockback_sequence and p_card.get("knockback") and random.random() < 0.3:
                    extra_actions = 2
                    skip_enemy_turn = True
                    in_knockback_sequence = True
                    print(f"\n💥 擊飛！{e_name} 被轟到空中，無法反擊！")
                    print(f"⚡ 魯夫獲得 {extra_actions} 次追加攻擊機會！")

            # 若敵人已死，跳出所有循環
            if e_hp <= 0:
                break

            # 處理額外行動
            if extra_actions > 0:
                extra_actions -= 1
                print(f"\n🔥 連段中！剩餘 {extra_actions} 次追加攻擊！")
                # 繼續玩家回合，不退出
                continue
            else:
                # 沒有額外行動了，退出玩家行動階段
                player_turn_active = False

        # 若敵人已死，跳出主迴圈
        if e_hp <= 0:
            break

        # ----- 敵人反擊（僅當 skip_enemy_turn 為 False 時執行）-----
        if not skip_enemy_turn:
            print(f"\n🌀 {e_name} 反擊！")
            time.sleep(1)

            enemy_skills = game_state.SKILL_DATA.get(e_name, [{"skill": "普通攻擊", "dmg": 10}])
            e_card = random.choice(enemy_skills)
            print(f"💢 使用了 {e_card['skill']}！")
            if 'audio' in e_card:
                play_voice(e_card['audio'])
            e_dmg = sum(e_card['dmg_list']) if "dmg_list" in e_card else e_card['dmg']
            # 防禦效果：只在普通回合有效（非連段），且用於該次反擊
            if defending:   # defending 是最後一次行動的防禦狀態
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
        else:
            print("\n💨 敵人被擊飛，無法反擊！")

        # 回合結束：減少效果持續時間
        update_effects(p_effects)
        update_effects(e_effects)

    # 戰鬥結算
    if p_hp > 0:
        reward = random.randint(50, 150)
        game_state.player_data["money"] += reward
        print(f"\n🏆 勝利！成功打飛了 {e_name}！獲得戰利品 {reward} 貝里！")
        play_voice("system/victory.mp3")
        save_player_data()
        return True
    else:
        print(f"\n💀 你被 {e_name} 擊敗了...")
        return False