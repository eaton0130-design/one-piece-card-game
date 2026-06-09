# battle.py
import random
import time
import game_state
from audio import play_voice
from data_manager import save_player_data
from upgrade import add_xp, get_level, get_skill_level, get_mp, get_max_mp, add_mp, consume_mp, add_kp, get_kp, consume_kp

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
    # 初始 HP 可視等級調整（基準 500，每等 +20）
    p_level = get_level(p_char)
    p_hp = 500 + (p_level - 1) * 20
    p_max_mp = get_max_mp(p_char)
    p_mp = get_mp(p_char)
    p_effects = []
    e_effects = []

    print(f"\n⚔️ 戰鬥開始：{p_char} VS 【{e_name}】")

    def apply_dot(effects, owner_name):
        total = 0
        for eff in effects[:]:
            if eff["type"] in ("sandstorm", "poison", "quicksand"):
                dmg = eff.get("damage_per_turn", 0)
                total += dmg
                display = eff.get("display", eff["type"])
                print(f"💨 {owner_name} 受到 {display} 影響，損失 {dmg} HP！")
        return total

    def add_unique_effect(effects_list, new_effect, owner_name):
        """將效果加入 effects_list，但若已存在相同 type 則不再加入。"""
        new_type = new_effect.get("type") or new_effect.get("display")
        # 若 effects_list 中已存在相同 type，就跳過
        for eff in effects_list:
            if eff.get("type") == new_type:
                display = new_effect.get("display", new_type)
                print(f"（提示）{owner_name} 已有 {display} 效果，無法重複套用。")
                return False
        effects_list.append(new_effect)
        display = new_effect.get("display", new_type)
        print(f"✨ {owner_name} 中了 {display} 效果！")
        return True

    def update_effects(effects):
        for eff in effects[:]:
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                display = eff.get("display", eff["type"])
                print(f"✅ {display} 效果消失了。")
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
                # 檢查是否被禁止攻擊的效果（例如流沙）
                if any(eff.get("disable_attack") for eff in p_effects):
                    display = next((eff.get("display", eff["type"]) for eff in p_effects if eff.get("disable_attack")), "特殊效果")
                    print(f"❌ 你被 {display} 限制，無法攻擊！")
                    player_turn_active = False
                    # 攻擊被禁止，視為回合結束
                    continue
                # 讓玩家選擇技能（包含基本攻擊）
                available_skills = []
                # 基本攻擊
                available_skills.append({"skill": "普通攻擊", "dmg": 10, "mp_cost": 0})
                for s in game_state.SKILL_DATA.get(p_char, []):
                    s_copy = s.copy()
                    s_copy.setdefault('mp_cost', 0)
                    available_skills.append(s_copy)

                # 列出技能與 MP/可用性
                print("\n--- 技能清單 ---")
                for si, s in enumerate(available_skills):
                    name = s.get('skill')
                    cost = s.get('mp_cost', 0)
                    # 特殊檢查：魯夫的連段技能需要 KP
                    locked = False
                    lock_reason = ''
                    if p_char == '魯夫' and name == '橡膠鐘、子彈、機關槍':
                        if get_kp(p_char) < 100:
                            locked = True
                            lock_reason = '(需要 KP 100)'
                    if cost > p_mp:
                        locked = True
                        lock_reason = f'(需要 {cost} MP)'
                    print(f"{si}. {name}  MP:{cost} {lock_reason}")

                try:
                    choice_idx = int(input("選擇技能編號: "))
                    p_card = available_skills[choice_idx]
                except Exception:
                    print("無效選擇，攻擊被跳過。")
                    p_card = {"skill": "普通攻擊", "dmg": 10, "mp_cost": 0}

                # 檢查 KP 與 MP
                if p_char == '魯夫' and p_card.get('skill') == '橡膠鐘、子彈、機關槍':
                    if get_kp(p_char) < 100:
                        print("KP 未滿，無法施放該技能，改為普通攻擊。")
                        p_card = {"skill": "普通攻擊", "dmg": 10, "mp_cost": 0}
                    else:
                        # 消耗 KP
                        consume_kp(p_char)

                mp_cost = p_card.get('mp_cost', 0)
                if mp_cost > 0:
                    if not consume_mp(p_char, mp_cost):
                        print("MP 不足，改為普通攻擊。")
                        p_card = {"skill": "普通攻擊", "dmg": 10, "mp_cost": 0}
                    else:
                        p_mp -= mp_cost

                print(f"🃏 你使用 {p_card['skill']}！")
                if 'audio' in p_card:
                    play_voice(p_card['audio'])
                base_dmg = sum(p_card['dmg_list']) if "dmg_list" in p_card else p_card['dmg']
                # 技能等級加成與角色等級加成
                skill_lv = get_skill_level(p_char, p_card['skill'])
                level_multiplier = 1 + 0.05 * (p_level - 1)
                skill_multiplier = 1 + 0.10 * skill_lv
                p_dmg = int(base_dmg * level_multiplier * skill_multiplier)
                # 檢查敵方是否處於不可被命中（invulnerable）狀態，例如克洛克達爾的砂畫
                if any(eff.get("invulnerable") for eff in e_effects):
                    display = next((eff.get("display", eff["type"]) for eff in e_effects if eff.get("invulnerable")), "特殊狀態")
                    print(f"💨 {e_name} 處於 {display}，攻擊無效！")
                else:
                    e_hp -= p_dmg
                    print(f"💥 造成 {p_dmg} 傷害！")

                # 增加 KP（若為魯夫，且不是使用需要 KP 的特殊技）
                if p_char == '魯夫' and p_card.get('skill') != '橡膠鐘、子彈、機關槍':
                    add_kp(p_char, 25)
                    print(f"✨ 魯夫獲得 25 KP（目前 {get_kp(p_char)} /100）")

                # 吸血效果
                if p_card.get("life_steal"):
                    heal_amount = int(p_dmg * p_card["life_steal"])
                    p_hp += heal_amount
                    print(f"💚 吸血效果！{p_char} 回復了 {heal_amount} HP！")

                # 附加效果
                if "effects" in p_card:
                    for effect in p_card["effects"]:
                        new_effect = effect.copy()
                        add_unique_effect(e_effects, new_effect, e_name)

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
            if any(eff.get("disable_attack") for eff in e_effects):
                display = next((eff.get("display", eff["type"]) for eff in e_effects if eff.get("disable_attack")), "特殊效果")
                print(f"\n🛑 {e_name} 被 {display} 限制，無法攻擊！")
            else:
                print(f"\n🌀 {e_name} 反擊！")
                time.sleep(1)

                enemy_skills = game_state.SKILL_DATA.get(e_name, [])
                # 電腦也可以使用普通攻擊，避免某些敵人成為無敵魔王
                enemy_choices = enemy_skills.copy()
                enemy_choices.append({"skill": "普通攻擊", "dmg": 10})
                e_card = random.choice(enemy_choices)
                print(f"💢 使用了 {e_card['skill']}！")
                if 'audio' in e_card:
                    play_voice(e_card['audio'])
                e_dmg = sum(e_card['dmg_list']) if "dmg_list" in e_card else e_card['dmg']
                # 若敵人是克洛克達爾，使用非普通攻擊技能後進入「砂畫」狀態，持續 2 回合且不可被攻擊
                if e_name == '克洛克達爾' and e_card.get('skill') and e_card.get('skill') != '普通攻擊':
                    sand_effect = {"type": "sand_paint", "display": "砂畫狀態", "duration": 2, "invulnerable": True}
                    add_unique_effect(e_effects, sand_effect, e_name)
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
                        add_unique_effect(p_effects, new_effect, p_char)
        else:
            print("\n💨 敵人被擊飛，無法反擊！")

        # 回合結束：減少效果持續時間
        update_effects(p_effects)
        update_effects(e_effects)

    # 戰鬥結算
    if p_hp > 0:
        reward = random.randint(50, 150)
        game_state.player_data["money"] += reward
        # 經驗獎勵：根據敵人初始 HP 與隨機性
        xp_reward = random.randint(20, 40)
        add_xp(p_char, xp_reward)
        # 戰鬥結束後自動補滿 MP
        add_mp(p_char, get_max_mp(p_char))
        print(f"\n🏆 勝利！成功打飛了 {e_name}！獲得戰利品 {reward} 貝里，並獲得 {xp_reward} 經驗值！(MP 已補滿)")
        play_voice("system/victory.mp3")
        save_player_data()
        return True
    else:
        print(f"\n💀 你被 {e_name} 擊敗了...")
        # 戰鬥結束後自動補滿 MP
        try:
            add_mp(p_char, get_max_mp(p_char))
            print("(戰鬥結束，MP 已補滿)")
        except Exception:
            pass
        return False