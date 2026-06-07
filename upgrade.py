import game_state
from data_manager import save_player_data

def ensure_characters_initialized():
    """確保 player_data 中有 characters 結構，並為 my_chars 中的角色建立預設資料。"""
    pd = game_state.player_data
    if "characters" not in pd:
        pd["characters"] = {}
    for name in pd.get("my_chars", []):
        if name not in pd["characters"]:
            level = 1
            max_mp = 100 + (level - 1) * 10
            pd["characters"][name] = {
                "level": level,
                "xp": 0,
                "skill_points": 0,
                "skills": {},  # skill_name -> level
                "max_mp": max_mp,
                "mp": max_mp,
                "kp": 0
            }
    save_player_data()

def xp_to_level_req(level):
    # 分段成長曲線：
    # 等級 1-5：每級需求 100 * level（新手友好）
    # 等級 6-10：每級需求 150 * level（進階）
    # 等級 11 起：每級需求 250 * level（高級）
    if level <= 5:
        return 100 * level
    elif level <= 10:
        return 150 * level
    else:
        return 250 * level

def add_xp_to_char(name, amount):
    pd = game_state.player_data
    ensure_characters_initialized()
    chars = pd["characters"]
    if name not in chars:
        return
    entry = chars[name]
    entry["xp"] += amount
    leveled = False
    # 迴圈處理可能的多重升級
    while entry["xp"] >= xp_to_level_req(entry["level"]):
        req = xp_to_level_req(entry["level"])
        entry["xp"] -= req
        entry["level"] += 1
        entry["skill_points"] += 1
        leveled = True
    if leveled:
        print(f"🎉 {name} 升級了！ 現在等級 {entry['level']}，可獲得技能點數。")
        # 每升一級，增加最大 MP 並補滿 MP
        entry["max_mp"] = 100 + (entry["level"] - 1) * 10
        entry["mp"] = entry["max_mp"]
    save_player_data()

def get_mp(name):
    ensure_characters_initialized()
    return game_state.player_data["characters"].get(name, {}).get("mp", 0)

def get_max_mp(name):
    ensure_characters_initialized()
    return game_state.player_data["characters"].get(name, {}).get("max_mp", 100)

def consume_mp(name, amount):
    ensure_characters_initialized()
    entry = game_state.player_data["characters"].get(name)
    if not entry:
        return False
    if entry["mp"] < amount:
        return False
    entry["mp"] -= amount
    save_player_data()
    return True

def add_mp(name, amount):
    ensure_characters_initialized()
    entry = game_state.player_data["characters"].get(name)
    if not entry:
        return
    entry["mp"] = min(entry["max_mp"], entry["mp"] + amount)
    save_player_data()

def get_kp(name):
    ensure_characters_initialized()
    return game_state.player_data["characters"].get(name, {}).get("kp", 0)

def add_kp(name, amount):
    ensure_characters_initialized()
    entry = game_state.player_data["characters"].get(name)
    if not entry:
        return
    entry["kp"] = min(100, entry.get("kp", 0) + amount)
    save_player_data()

def consume_kp(name):
    ensure_characters_initialized()
    entry = game_state.player_data["characters"].get(name)
    if not entry:
        return False
    if entry.get("kp", 0) < 100:
        return False
    entry["kp"] = 0
    save_player_data()
    return True

def get_char_level(name):
    ensure_characters_initialized()
    return game_state.player_data["characters"].get(name, {}).get("level", 1)

def get_skill_level(name, skill_name):
    ensure_characters_initialized()
    return game_state.player_data["characters"].get(name, {}).get("skills", {}).get(skill_name, 0)

def spend_skill_point(name, skill_name):
    ensure_characters_initialized()
    chars = game_state.player_data["characters"]
    entry = chars.get(name)
    if not entry:
        print("找不到該角色資料。")
        return False
    if entry["skill_points"] <= 0:
        print("沒有可用的技能點數。")
        return False
    entry["skills"][skill_name] = entry["skills"].get(skill_name, 0) + 1
    entry["skill_points"] -= 1
    save_player_data()
    print(f"✅ 已為 {name} 的技能 '{skill_name}' 提升到等級 {entry['skills'][skill_name]}。")
    return True

def manage_characters_cli():
    ensure_characters_initialized()
    pd = game_state.player_data
    while True:
        print("\n--- 角色管理與升級 ---")
        for i, name in enumerate(pd.get("my_chars", [])):
            info = pd["characters"].get(name, {})
            print(f"{i}. {name} (Lv{info.get('level',1)} XP:{info.get('xp',0)} SP:{info.get('skill_points',0)})")
        print("b. 返回主選單")
        choice = input("選擇要管理的角色編號 (或 b 返回): ")
        if choice.lower() == 'b':
            break
        try:
            idx = int(choice)
            name = pd.get("my_chars", [])[idx]
        except Exception:
            print("無效選擇。")
            continue

        entry = pd["characters"][name]
        next_req = xp_to_level_req(entry['level'])
        remaining = max(0, next_req - entry['xp'])
        print(f"\n{name} - 等級 {entry['level']} / XP {entry['xp']} / 可用技能點 {entry['skill_points']} / 到下一級還需 {remaining} XP")
        # 列出該角色所有可升級技能（從 SKILL_DATA 來源）
        skills_available = game_state.SKILL_DATA.get(name, [])
        if not skills_available:
            print("此角色沒有可升級的技能資料。")
            input("[按 Enter 返回]")
            continue
        print("技能列表：")
        for si, s in enumerate(skills_available):
            sname = s.get('skill')
            slevel = entry['skills'].get(sname, 0)
            print(f"{si}. {sname} (等級 {slevel})")
        print("u. 升級技能  q. 返回角色選單")
        cmd = input("輸入指令: ")
        if cmd == 'q':
            continue
        if cmd == 'u':
            try:
                si = int(input("輸入要升級的技能編號: "))
                sname = skills_available[si].get('skill')
            except Exception:
                print("無效技能編號。")
                continue
            spend_skill_point(name, sname)
        else:
            print("未知指令。")
