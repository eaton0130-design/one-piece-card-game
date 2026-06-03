# minigames.py
import random
import time
from audio import play_voice

def timing_defense_game():
    """聽音格擋（第一集）"""
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
    """撞雕像小遊戲（第二集開頭）"""
    print("\n🚀 【橡膠火箭撞雕像】")
    print("魯夫將手臂向後伸長，準備發射橡膠火箭！")
    print("👂 仔細聽橡膠拉伸的音效，音效結束後『約 2 秒』魯夫就會飛出去！")
    print("⚡ 你必須在魯夫飛出去的『瞬間』按下 Enter！")
    print("⚠️  太早或太晚都會失敗，必須重來！")
    input("👉 準備好了嗎？按 Enter 開始...")

    delay = 2.0
    print(f"\n⏳ 橡膠伸長... 將在 {delay} 秒後射出！")
    
    charge_sound = "story/gomu_rocket_charge.mp3"
    proc = play_voice(charge_sound, block=False)
    if proc is None:
        print("⚠️ 橡膠拉伸音效遺失，仍可進行小遊戲（請自行計時）")
    
    time.sleep(delay)
    
    start_time = time.time()
    print("💥 現在！快按 Enter！")
    
    if proc:
        proc.terminate()
    
    try:
        input()
    except KeyboardInterrupt:
        raise
    
    end_time = time.time()
    delta = end_time - start_time
    
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
    """猜刀小遊戲（第二集後半）－ 溫和版，猜錯只重置當前刀"""
    print("\n🗡️ 【尋找索隆的刀】")
    print("魯夫面前有三個箱子，裡面只有一個藏有索隆的一把刀。")
    print("你必須連續選對三次，才能拿到全部三把刀（和道一文字、三代鬼徹、雪走）。")
    print("⚠️  猜錯的話，當前這把刀會重新洗牌，但不影響已經拿到的刀。")
    input("👉 按 Enter 開始...")
    
    swords = ["和道一文字", "三代鬼徹", "雪走"]
    found = 0
    
    while found < 3:
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
    
    print("\n🎉 太棒了！你成功拿到了索隆的全部三把刀！")
    print("索隆：『謝了，魯夫。我欠你一次。』")
    return True