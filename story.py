# story.py
import time
import game_state
from audio import play_voice
from data_manager import save_player_data
from battle import battle
from minigames import timing_game, rocket_game, sword_game


def get_story_progress_key():
    return "story_index"


def get_story_data():
    return game_state.STORY_CHRONICLE


def get_story_label():
    return "原本劇情模式"


def trigger_story_battle(scene):
    enemy_name = scene.get("target_enemy", "隨機對手")
    enemy_hp = scene.get("target_hp", 500)
    ally_name = scene.get("target_player", "魯夫")
    ally_hp = scene.get("target_player_hp")
    print(f"\n🔥 [警告] 劇情觸發戰鬥！我方【{ally_name}】迎擊【{enemy_name}】！")
    time.sleep(1)
    victory = battle(
        specific_enemy=enemy_name,
        specific_hp=enemy_hp,
        specific_player=ally_name,
        specific_player_hp=ally_hp,
    )
    if not victory:
        print("戰鬥失敗，劇情無法推進。請重新挑戰。")
        return False
    return True


def play_story():
    story_label = get_story_label()
    progress_key = get_story_progress_key()
    story_data = get_story_data()

    print(f"\n📖 --- 進入{story_label} ---")

    if not story_data:
        print("🎉 目前沒有可播放的劇情資料。")
        return

    start_idx = game_state.player_data.get(progress_key, 0)
    if start_idx >= len(story_data):
        print("🎉 你已經看完所有目前的劇情！等待後續更新～")
        return

    if start_idx > 0:
        choice = input(f"上次你玩到第 {start_idx} 段劇情，要從頭開始嗎？(y/n，預設 n): ")
        if choice.lower() == 'y':
            start_idx = 0
            game_state.player_data[progress_key] = 0
            save_player_data()

    idx = start_idx
    while idx < len(story_data):
        scene = story_data[idx]

        # 特殊處理 id=3（聽音格擋）
        if scene.get("id") == 3:
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過此段劇情直接進入格擋: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                audio_file = scene.get('audio')
                if audio_file:
                    play_voice(audio_file)
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")

            success = False
            while not success:
                success = timing_game()
                if not success:
                    retry = input("\n🔄 重來一次？(y/n): ").lower()
                    if retry != 'y':
                        print("你選擇中斷劇情，返回主選單。")
                        return

            next_idx = idx + 1
            while next_idx < len(story_data) and story_data[next_idx].get("id") != 4:
                next_idx += 1
            if next_idx < len(story_data):
                scene4 = story_data[next_idx]
                print(f"\n🎬 {scene4['title']}")
                print(f"💬 {scene4['desc']}")
                audio_file = scene4.get('audio')
                if audio_file:
                    play_voice(audio_file)
                input("\n[按 Enter 繼續...]")
                idx = next_idx + 1
            else:
                print("\n⚠️  找不到 id4 的劇情，但小遊戲成功結束。")
                idx += 1

            game_state.player_data[progress_key] = idx
            save_player_data()
            continue

        # 特殊處理 id=8（撞雕像）
        if scene.get("id") == 8:
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過直接開始撞雕像: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                audio_file = scene.get('audio')
                if audio_file:
                    play_voice(audio_file)
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")

            success = False
            while not success:
                success = rocket_game()
                if not success:
                    retry = input("\n🔄 重來一次？(y/n): ").lower()
                    if retry != 'y':
                        print("你選擇中斷劇情，返回主選單。")
                        return

            idx += 1
            game_state.player_data[progress_key] = idx
            save_player_data()
            print("\n✅ 雕像粉碎！魯夫抓住了貝魯梅伯，逼問索隆的刀藏在哪裡...")
            input("[按 Enter 繼續]")
            continue

        # 特殊處理 id=9（猜刀小遊戲）
        if scene.get("id") == 9:
            choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看劇情，輸入 s 跳過直接開始找刀: ")
            if choice.lower() != 's':
                print(f"\n🎬 {scene['title']}")
                print(f"💬 {scene['desc']}")
                audio_file = scene.get('audio')
                if audio_file:
                    play_voice(audio_file)
            else:
                print(f"⏩ 跳過「{scene['title']}」的劇情內容。")

            sword_game()

            idx += 1
            game_state.player_data[progress_key] = idx
            save_player_data()
            print("\n✅ 成功取得三把刀，索隆被釋放，決定跟隨魯夫！")
            input("[按 Enter 繼續]")
            continue

        # ---------- 一般劇情處理 ----------
        choice = input(f"\n🎬 即將播放：{scene['title']} - 按 Enter 觀看，輸入 s 跳過此段劇情: ")
        if choice.lower() == 's':
            print(f"⏩ 跳過「{scene['title']}」的劇情內容。")
            if scene.get("trigger_battle") == True:
                if not trigger_story_battle(scene):
                    return
            idx += 1
            game_state.player_data[progress_key] = idx
            save_player_data()
            continue

        # 正常觀看
        print(f"\n🎬 {scene['title']}")
        print(f"💬 {scene['desc']}")
        audio_file = scene.get('audio')
        if audio_file:
            play_voice(audio_file)
        # 觀看劇情也可獲得少量經驗，分配給目前隊伍所有成員
        try:
            from upgrade import add_xp
            for name in game_state.player_data.get('my_chars', []):
                add_xp(name, 5)
        except Exception:
            pass

        if scene.get("trigger_battle") == True:
            if not trigger_story_battle(scene):
                return
        else:
            input("\n[按 Enter 繼續下一段劇情...]")

        idx += 1
        game_state.player_data[progress_key] = idx
        save_player_data()

    print("\n✅ 目前劇情已播放完畢，期待後續更新！")