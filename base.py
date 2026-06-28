import time
import random
import game_state
from data_manager import load_json, save_player_data
from upgrade import add_xp, get_level
from audio import play_voice

BUILDING_DATA = load_json("buildings.json", {
    "default_levels": {
        "dock": 1,
        "tavern": 1,
        "workshop": 1,
        "training": 1,
        "intelligence": 1,
        "market": 1,
        "forge": 0
    },
    "building_costs": {
        "dock": {"money": 150, "wood": 20},
        "tavern": {"money": 120, "food": 25},
        "workshop": {"money": 100, "metal": 20},
        "training": {"money": 120, "food": 15, "wood": 10},
        "intelligence": {"money": 130, "intel": 0},
        "market": {"money": 150, "wood": 10, "metal": 10},
        "forge": {"money": 180, "wood": 15, "metal": 15}
    }
})

BASE_DEFINITIONS = {
    "resources": {
        "wood": 0,
        "food": 0,
        "metal": 0,
        "intel": 0,
        "fragments": 0
    },
    "buildings": BUILDING_DATA.get("default_levels", {}).copy(),
    "expeditions": [],
    "crafting_projects": [],
    "workers": 0,
    "worker_morale": 100,
    "worker_salary_cost": 20,
    "worker_salary_interval": 120,
    "last_salary_time": 0,
    "auto_build_last_time": 0,
    "last_collect_time": 0
}

BUILDING_COSTS = BUILDING_DATA.get("building_costs", {})

CRAFTING_RECIPES = load_json("crafting_recipes.json", [
    {
        "name": "簡易治癒藥水",
        "type": "item",
        "materials": {"food": 10, "metal": 2}
    },
    {
        "name": "補強護手",
        "type": "equipment",
        "materials": {"wood": 10, "metal": 10}
    },
    {
        "name": "水桶",
        "type": "item",
        "materials": {"wood": 5, "metal": 5}
    },
    {
        "name": "情報探測器",
        "type": "item",
        "materials": {"metal": 5, "intel": 15}
    },
    {
        "name": "鋼鐵護腕",
        "type": "equipment",
        "materials": {"metal": 15, "fragments": 2}
    }
])

BUILDING_LABELS = {
    "dock": "船塢",
    "tavern": "酒館",
    "workshop": "工坊",
    "training": "訓練場",
    "intelligence": "情報站",
    "market": "市集",
    "forge": "鍛造坊"
}

RESOURCE_LABELS = {
    "money": "貝里",
    "wood": "木材",
    "food": "食物",
    "metal": "金屬",
    "intel": "情報",
    "fragments": "碎片"
}

def label_building(name):
    return BUILDING_LABELS.get(name, name)


def label_resource(name):
    return RESOURCE_LABELS.get(name, name)

MISSION_TEMPLATES = [
    {
        "name": "簡易治癒藥水",
        "type": "item",
        "materials": {"food": 10, "metal": 2}
    },
    {
        "name": "補強護手",
        "type": "equipment",
        "materials": {"wood": 10, "metal": 10}
    },
    {
        "name": "水桶",
        "type": "item",
        "materials": {"wood": 5, "metal": 5}
    },
    {
        "name": "情報探測器",
        "type": "item",
        "materials": {"metal": 5, "intel": 15}
    },
    {
        "name": "鋼鐵護腕",
        "type": "equipment",
        "materials": {"metal": 15, "fragments": 2}
    }
]

MISSION_TEMPLATES = load_json("missions.json", [
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
])

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
    if "crafting_projects" not in base:
        base["crafting_projects"] = []
    if "workers" not in base:
        base["workers"] = 0
    if "worker_morale" not in base:
        base["worker_morale"] = 100
    if "worker_salary_cost" not in base:
        base["worker_salary_cost"] = 20
    if "worker_salary_interval" not in base:
        base["worker_salary_interval"] = 120
    if "last_salary_time" not in base:
        base["last_salary_time"] = 0
    if "auto_build_last_time" not in base:
        base["auto_build_last_time"] = 0
    if "last_collect_time" not in base:
        base["last_collect_time"] = 0
    if "last_hint_time" not in base:
        base["last_hint_time"] = 0
    if "inventory" not in pd:
        pd["inventory"] = {"items": {}, "equipment": []}
    save_player_data()
    return base


def get_base():
    init_base()
    return game_state.player_data["base"]


def building_level(name):
    return get_base()["buildings"].get(name, 1)


def get_building_cost(name):
    level = max(1, building_level(name))
    base_cost = BUILDING_COSTS.get(name, {})
    cost = {}
    for key, value in base_cost.items():
        cost[key] = int(value * (1 + 0.35 * (level - 1)))
    return cost


def process_worker_building():
    base = get_base()
    workers = base.get("workers", 0)
    if workers <= 0:
        return

    now = time.time()
    last_salary = base.get("last_salary_time", now)
    if now - last_salary >= base.get("worker_salary_interval", 120):
        salary_cost = base.get("worker_salary_cost", 20) * workers
        if can_afford({"money": salary_cost}):
            game_state.player_data["money"] = max(0, game_state.player_data.get("money", 0) - salary_cost)
            base["worker_morale"] = min(100, base.get("worker_morale", 100) + 8)
            print(f"💵 工人領到薪水 {salary_cost} 貝里，士氣提升。")
        else:
            base["worker_morale"] = max(0, base.get("worker_morale", 100) - 25)
            print("⚠️ 工人沒拿到薪水，士氣下降。")
            if base["worker_morale"] < 40 or random.random() < 0.5:
                base["workers"] = max(0, base["workers"] - 1)
                print("👋 一名工人因為不滿而辭職。")
        base["last_salary_time"] = now
        save_player_data()

    if random.random() < 0.2 and base.get("workers", 0) > 0:
        base["worker_morale"] = max(0, base.get("worker_morale", 100) - 3)

    projects = base.get("crafting_projects", [])
    if not projects:
        base["auto_build_last_time"] = now
        save_player_data()
        return

    last = base.get("auto_build_last_time", now)
    elapsed = now - last
    if elapsed < 60:
        return

    morale = base.get("worker_morale", 100)
    if morale >= 80:
        multiplier = 1.0
    elif morale >= 50:
        multiplier = 0.8
    elif morale >= 25:
        multiplier = 0.6
    else:
        multiplier = 0.4

    ticks = int(elapsed // 60)
    points = max(1, int(ticks * workers * 5 * multiplier))
    remaining = points
    for project in projects:
        if remaining <= 0:
            break
        to_add = min(remaining, project["target"] - project["progress"])
        project["progress"] += to_add
        remaining -= to_add
        print(f"👷 工人自動建造：{project['name']} 進度 +{to_add}。")
        if project["progress"] >= project["target"]:
            complete_crafting_project(project)
    base["crafting_projects"] = [p for p in base["crafting_projects"] if p["progress"] < p["target"]]
    base["auto_build_last_time"] = now - (elapsed % 60)
    save_player_data()


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


def get_worker_cost():
    return {"money": 120, "wood": 5}


def hire_worker():
    cost = get_worker_cost()
    if not can_afford(cost):
        print("❌ 資源不足，無法招募工人。需要 120 貝里和 5 木材。")
        return False
    spend_resources(cost)
    base = get_base()
    base["workers"] += 1
    base["worker_morale"] = 80
    base["last_salary_time"] = time.time()
    base["auto_build_last_time"] = time.time()
    save_player_data()
    print(f"👷 工人招募成功！目前工人人數：{base['workers']}。")
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
    print(f"✅ {label_building(name)} 已升級到等級 {building_level(name)}！")
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
    items = ", ".join([f"{label_resource(k)} +{v}" for k, v in gain.items()])
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
        if exp.get("task_type") == "crafting":
            project = find_crafting_project(exp.get("project_id"))
            if project:
                project["progress"] += exp.get("build_points", 0)
                add_xp(exp["character"], exp.get("xp", 0))
                print(f"🛠️ {exp['character']} 的建造任務「{exp['mission_name']}」完成，{project['name']} 進度 +{exp.get('build_points', 0)}。")
                if project["progress"] >= project["target"]:
                    complete_crafting_project(project)
                    base["crafting_projects"] = [p for p in base["crafting_projects"] if p["project_id"] != project["project_id"]]
            else:
                print(f"⚠️ 找不到對應的製造專案：{exp['mission_name']}。")
        else:
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
        "xp": mission["xp"],
        "task_type": "mission"
    }
    get_base()["expeditions"].append(expedition)
    save_player_data()
    print(f"🚢 {character_name} 已派遣至「{mission['name']}」，預計 {duration} 秒後返回。")
    return True


def format_resources(resources):
    return ", ".join([f"{label_resource(k)}:{v}" for k, v in resources.items()])


def reward_description(reward):
    return ", ".join([f"{label_resource(k)} +{v}" for k, v in reward.items()])


def format_recipe_materials(materials):
    return ", ".join([f"{label_resource(k)}:{v}" for k, v in materials.items()])


def show_base_status():
    base = get_base()
    # 查看基地時播放翻書音效（非阻塞）
    try:
        play_voice("system/book_flip.mp3", block=False)
    except Exception:
        pass
    print("\n--- 海賊基地狀態 ---")
    print(f"資源：{format_resources(base['resources'])}")
    print(f"貝里：{game_state.player_data.get('money', 0)}")
    print("建築等級：")
    for name, level in base["buildings"].items():
        if name == "forge" and level == 0:
            print(f"  {label_building(name)}: 未建造")
        else:
            print(f"  {label_building(name)}: Lv{level}")
    print("進行中派遣：")
    if not base["expeditions"]:
        print("  無")
    else:
        now = time.time()
        for exp in base["expeditions"]:
            remaining = max(0, int(exp["end_time"] - now))
            print(f"  {exp['character']} - {exp['mission_name']} (剩餘 {remaining} 秒)")
    print(f"工人人數：{base.get('workers', 0)}")
    print(f"工人士氣：{base.get('worker_morale', 100)}")
    print("製造專案：")
    if not base["crafting_projects"]:
        print("  無")
    else:
        for project in base["crafting_projects"]:
            print(f"  {project['name']} - 進度 {project['progress']} / {project['target']}")


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


def get_crafting_recipes():
    return CRAFTING_RECIPES


def has_forge():
    return building_level("forge") > 0


def list_crafting_projects():
    return get_base()["crafting_projects"]


def find_crafting_project(project_id):
    for project in list_crafting_projects():
        if project.get("project_id") == project_id:
            return project
    return None


def show_crafting_project_status():
    base = get_base()
    projects = base["crafting_projects"]
    print("\n--- 製造專案進度 ---")
    if not projects:
        print("  目前沒有進行中的製造專案。")
        return
    for i, project in enumerate(projects):
        print(f"  {i}. {project['name']} ({project['type']}) - 進度 {project['progress']} / {project['target']}")


def choose_crafting_project():
    projects = list_crafting_projects()
    if not projects:
        print("❌ 目前沒有可派遣建造的專案。")
        return None
    print("\n--- 選擇製造專案 ---")
    for i, project in enumerate(projects):
        print(f"{i}. {project['name']} - 進度 {project['progress']} / {project['target']}")
    try:
        index = int(input("輸入專案編號: "))
        return projects[index]
    except Exception:
        print("無效選擇。")
        return None


def start_crafting_project():
    if not has_forge():
        print("❌ 你尚未建造工坊，無法開始製作裝備或道具。")
        return
    recipes = get_crafting_recipes()
    print("\n--- 可製作配方 ---")
    for i, recipe in enumerate(recipes):
        print(f"{i}. {recipe['name']} ({recipe['type']}) - 材料: {format_recipe_materials(recipe['materials'])}")
    try:
        index = int(input("輸入要製作的配方編號: "))
        recipe = recipes[index]
    except Exception:
        print("無效選擇。")
        return
    resources = get_base()["resources"]
    for key, amount in recipe["materials"].items():
        if resources.get(key, 0) < amount:
            print(f"❌ 材料不足：需要 {label_resource(key)} {amount}，目前只有 {resources.get(key, 0)}。")
            return
    for key, amount in recipe["materials"].items():

        resources[key] -= amount
    project = {
        "project_id": int(time.time() * 1000),
        "name": recipe["name"],
        "type": recipe["type"],
        "progress": 0,
        "target": 100,
        "materials": recipe["materials"]
    }
    get_base()["crafting_projects"].append(project)
    save_player_data()
    print(f"✅ 已啟動製造專案：{recipe['name']}。請派人建造以提升進度。")


def create_crafting_assignment(character_name, project):
    duration = 30
    expedition = {
        "character": character_name,
        "mission_name": f"建造 {project['name']}",
        "end_time": time.time() + duration,
        "task_type": "crafting",
        "project_id": project["project_id"],
        "build_points": 10,
        "xp": 5
    }
    get_base()["expeditions"].append(expedition)
    save_player_data()
    print(f"🚧 {character_name} 已派遣建造 {project['name']}，預計 {duration} 秒後回報。")


def dispatch_crafting_menu():
    if not has_forge():
        print("❌ 你尚未建造工坊，請先升級建築並建造工坊。")
        return
    project = choose_crafting_project()
    if not project:
        return
    character = choose_character()
    if not character:
        return
    create_crafting_assignment(character, project)


def show_crafting_menu():
    init_base()
    while True:
        print("\n--- 製作裝備／道具 ---")
        print("1. 查看製造專案進度")
        print("2. 開始新製作專案")
        print("3. 派人建造專案")
        print("4. 返回基地選單")
        choice = input("請選擇: ")
        if choice == '1':
            show_crafting_project_status()
        elif choice == '2':
            start_crafting_project()
        elif choice == '3':
            dispatch_crafting_menu()
        elif choice == '4':
            break
        else:
            print("❌ 無效選擇。")


def complete_crafting_project(project):
    inventory = game_state.player_data.get("inventory", {"items": {}, "equipment": []})
    if project["type"] == "equipment":
        inventory["equipment"].append(project["name"])
        print(f"🎉 製作完成！你獲得了裝備：{project['name']}。")
    else:
        inventory["items"][project["name"]] = inventory["items"].get(project["name"], 0) + 1
        print(f"🎉 製作完成！你獲得了道具：{project['name']}。")
    game_state.player_data["inventory"] = inventory
    save_player_data()


def show_upgrade_menu():
    # 開啟升級建築時播放開門/敲門音效（非阻塞）
    try:
        play_voice("system/door_knock.mp3", block=False)
    except Exception:
        pass
    print("\n--- 升級建築 ---")
    buildings = get_base()["buildings"]
    for i, name in enumerate(buildings.keys()):
        level = buildings[name]
        cost = get_building_cost(name)
        detail = ", ".join([f"{label_resource(k)}:{v}" for k, v in cost.items()])
        print(f"{i}. {label_building(name)} (Lv{level}) 升級成本: {detail}")
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
        process_worker_building()
        # 每隔 COLLECT_COOLDOWN 秒播放基地提示音（非阻塞）
        base = get_base()
        now = time.time()
        last_hint = base.get("last_hint_time", 0)
        if now - last_hint >= COLLECT_COOLDOWN:
            base["last_hint_time"] = now
            save_player_data()
            try:
                play_voice("system/base_hint.mp3", block=False)
            except Exception:
                pass
        print("\n===== 🏝️ 海賊基地 =====")
        print("1. 查看基地狀態")
        print("2. 收集建築資源")
        print("3. 升級建築")
        print("4. 派遣角色任務")
        print("5. 收取完成派遣")
        print("6. 製作裝備／道具")
        print("7. 招募工人")
        print("8. 返回主選單")
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
            show_crafting_menu()
        elif choice == '7':
            hire_worker()
        elif choice == '8':
            break
        else:
            print("❌ 無效選擇。")
