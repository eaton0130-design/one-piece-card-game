import time
import random
import game_state
from data_manager import save_player_data
from upgrade import add_xp, get_level

BASE_DEFINITIONS = {
    "resources": {
        "wood": 0,
        "food": 0,
        "metal": 0,
        "intel": 0,
        "fragments": 0
    },
    "buildings": {
        "dock": 1,
        "tavern": 1,
        "workshop": 1,
        "training": 1,
        "intelligence": 1,
        "market": 1
    },
    "expeditions": [],
    "last_collect_time": 0
}

BUILDING_COSTS = {
    "dock": {"money": 150, "wood": 20},
    "tavern": {"money": 120, "food": 25},
    "workshop": {"money": 100, "metal": 20},
    "training": {"money": 120, "food": 15, "wood": 10},
    "intelligence": {"money": 130, "intel": 0},
    "market": {"money": 150, "wood": 10, "metal": 10}
}

MISSION_TEMPLATES = [
    {
        "name": "探索海域",
        "duration": 30,
        "reward": {"wood": 30, "food": 20},
        "xp": 10
    },
    {
        "name": "打撈沉船",
        "duration": 45,
        "reward": {"money": 80, "fragments": 2},
        "xp": 15
    },
    {
        "name": "情報蒐集",
        "duration": 40,
        "reward": {"intel": 20, "metal": 15},
        "xp": 12
    },
    {
        "name": "突襲海軍",
        "duration": 60,
        "reward": {"money": 120, "intel": 15},
        "xp": 18
    }
]

COLLECT_COOLDOWN = 60


def init_base():
    pd = game_state.player_data
    if "base" not in pd:
        pd["base"] = {}
    base = pd["base"]
    if "resources" not in base:
        base["resources"] = BASE_DEFINITIONS["resources"].copy()
    if "buildings" not in base:
        base["buildings"] = BASE_DEFINITIONS["buildings"].copy()
    if "expeditions" not in base:
        base["expeditions"] = []
    if "last_collect_time" not in base:
        base["last_collect_time"] = 0
    save_player_data()
    return base


def get_base():
    init_base()
    return game_state.player_data["base"]


def building_level(name):
    return get_base()["buildings"].get(name, 1)


def get_building_cost(name):
    level = building_level(name)
    base_cost = BUILDING_COSTS.get(name, {})
    cost = {}
    for key, value in base_cost.items():
        cost[key] = int(value * (1 + 0.35 * (level - 1)))
    return cost


def can_afford(cost):
    pd = game_state.player_data
    resources = pd["base"]["resources"]
    for key, value in cost.items():
        if key == "money":
            if pd.get("money", 0) < value:
                return False
        else:
            if resources.get(key, 0) < value:
                return False
    return True


def spend_resources(cost):
    pd = game_state.player_data
    resources = pd["base"]["resources"]
    for key, value in cost.items():
        if key == "money":
            pd["money"] = max(0, pd.get("money", 0) - value)
        else:
            resources[key] = max(0, resources.get(key, 0) - value)
    save_player_data()


def upgrade_building(name):
    cost = get_building_cost(name)
    if not can_afford(cost):
        print("❌ 資源不足，無法升級。")
        return False
    spend_resources(cost)
    game_state.player_data["base"]["buildings"][name] += 1
    save_player_data()
    print(f"✅ {name} 已升級到等級 {building_level(name)}！")
    return True


def calculate_collectable():
    base = get_base()
    resources = base["resources"]
    now = time.time()
    last = base.get("last_collect_time", 0)
    elapsed = now - last
    if elapsed < COLLECT_COOLDOWN:
        return None, int(COLLECT_COOLDOWN - elapsed)

    level = building_level("dock")
    resources_gain = {
        "wood": 10 * level,
        "food": 8 * level,
        "metal": 5 * level,
        "intel": 3 * level
    }
    tavern_level = building_level("tavern")
    resources_gain["food"] += 5 * tavern_level
    resources_gain["intel"] += 2 * building_level("intelligence")
    return resources_gain, 0


def collect_building_resources():
    gain, wait = calculate_collectable()
    if gain is None:
        print(f"⏳ 建築資源尚未準備好，還需等待 {wait} 秒。")
        return False
    base = get_base()
    for key, value in gain.items():
        base["resources"][key] = base["resources"].get(key, 0) + value
    base["last_collect_time"] = time.time()
    save_player_data()
    items = ", ".join([f"{k} +{v}" for k, v in gain.items()])
    print(f"✅ 已收集基地資源：{items}")
    return True


def list_expeditions():
    base = get_base()
    return base["expeditions"]


def collect_expeditions():
    base = get_base()
    now = time.time()
    finished = [exp for exp in base["expeditions"] if exp["end_time"] <= now]
    if not finished:
        print("⏳ 目前沒有完成的派遣任務。")
        return False
    for exp in finished:
        reward = exp["reward"]
        for key, value in reward.items():
            if key == "money":
                game_state.player_data["money"] += value
            else:
                game_state.player_data["base"]["resources"][key] = game_state.player_data["base"]["resources"].get(key, 0) + value
        add_xp(exp["character"], exp["xp"])
        print(f"🎉 {exp['character']} 的任務「{exp['mission_name']}」完成，獲得: {reward_description(reward)}，並獲得 {exp['xp']} XP。")
    base["expeditions"] = [exp for exp in base["expeditions"] if exp["end_time"] > now]
    save_player_data()
    return True


def reward_description(reward):
    return ", ".join([f"{k} +{v}" for k, v in reward.items()])


def create_expedition(character_name, mission_index):
    if mission_index < 0 or mission_index >= len(MISSION_TEMPLATES):
        return False
    mission = MISSION_TEMPLATES[mission_index]
    duration = mission["duration"]
    level = get_level(character_name)
    multiplier = 1 + (level - 1) * 0.05
    reward = {}
    for key, amount in mission["reward"].items():
        reward[key] = int(amount * multiplier)
    expedition = {
        "character": character_name,
        "mission_name": mission["name"],
        "end_time": time.time() + duration,
        "reward": reward,
        "xp": mission["xp"]
    }
    get_base()["expeditions"].append(expedition)
    save_player_data()
    print(f"🚢 {character_name} 已派遣至「{mission['name']}」，預計 {duration} 秒後返回。")
    return True


def format_resources(resources):
    return ", ".join([f"{k}:{v}" for k, v in resources.items()])


def show_base_status():
    base = get_base()
    print("\n--- 海賊基地狀態 ---")
    print(f"資源：{format_resources(base['resources'])}")
    print(f"貝里：{game_state.player_data.get('money', 0)}")
    print("建築等級：")
    for name, level in base["buildings"].items():
        print(f"  {name}: Lv{level}")
    print("進行中派遣：")
    if not base["expeditions"]:
        print("  無")
    else:
        now = time.time()
        for exp in base["expeditions"]:
            remaining = max(0, int(exp["end_time"] - now))
            print(f"  {exp['character']} - {exp['mission_name']} (剩餘 {remaining} 秒)")


def choose_character():
    chars = game_state.player_data.get("my_chars", [])
    ongoing = {exp["character"] for exp in get_base()["expeditions"]}
    available = [name for name in chars if name not in ongoing]
    if not available:
        print("❌ 目前沒有可派遣的角色，因為所有角色都已在執行中。")
        return None
    print("\n--- 可派遣角色 ---")
    for i, name in enumerate(available):
        print(f"{i}. {name} (Lv{get_level(name)})")
    try:
        index = int(input("輸入要派遣角色編號: "))
        return available[index]
    except Exception:
        print("無效選擇。")
        return None


def choose_mission():
    print("\n--- 選擇派遣任務 ---")
    for i, mission in enumerate(MISSION_TEMPLATES):
        reward = reward_description(mission["reward"])
        print(f"{i}. {mission['name']} (時間 {mission['duration']} 秒, 獎勵: {reward}, XP: {mission['xp']})")
    try:
        index = int(input("輸入任務編號: "))
        return index
    except Exception:
        print("無效選擇。")
        return None


def dispatch_menu():
    print("\n--- 派遣任務 ---")
    character = choose_character()
    if not character:
        return
    mission_index = choose_mission()
    if mission_index is None:
        return
    create_expedition(character, mission_index)


def show_upgrade_menu():
    print("\n--- 升級建築 ---")
    buildings = get_base()["buildings"]
    for i, name in enumerate(buildings.keys()):
        level = buildings[name]
        cost = get_building_cost(name)
        detail = ", ".join([f"{k}:{v}" for k, v in cost.items()])
        print(f"{i}. {name} (Lv{level}) 升級成本: {detail}")
    try:
        idx = int(input("輸入要升級的建築編號: "))
        name = list(buildings.keys())[idx]
    except Exception:
        print("無效選擇。")
        return
    upgrade_building(name)


def show_base_menu():
    init_base()
    while True:
        print("\n===== 🏝️ 海賊基地 =====")
        print("1. 查看基地狀態")
        print("2. 收集建築資源")
        print("3. 升級建築")
        print("4. 派遣角色任務")
        print("5. 收取完成派遣")
        print("6. 返回主選單")
        choice = input("請選擇: ")
        if choice == '1':
            show_base_status()
        elif choice == '2':
            collect_building_resources()
        elif choice == '3':
            show_upgrade_menu()
        elif choice == '4':
            dispatch_menu()
        elif choice == '5':
            collect_expeditions()
        elif choice == '6':
            break
        else:
            print("❌ 無效選擇。")
