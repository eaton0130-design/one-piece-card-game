# game_state.py
# 所有模組共享的狀態與設定（初始為空，由 main.py 載入後填充）

player_data = {}
SKILL_DATA = {}
STORY_CHRONICLE = []
config = {}

# 以下會在 main.py 中從 config 讀取後覆寫
SOUND_FOLDER = "sounds"
GACHA_COST = 100
FREE_GACHA_COOLDOWN = 3600
NPC_ENEMY_BLACKLIST = []