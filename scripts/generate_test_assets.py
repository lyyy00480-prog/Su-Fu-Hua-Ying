import os
from PIL import Image
from PIL import ImageFilter

def generate_test_assets(base_dir="assets"):
    print(f"正在生成测试素材到 {base_dir}...")

    # 确保 assets 目录存在
    os.makedirs(base_dir, exist_ok=True)

    # --- 场景背景 (assets/scenes) ---
    scenes_dir = os.path.join(base_dir, "scenes")
    os.makedirs(scenes_dir, exist_ok=True)

    # placeholder_scene.png (模拟老宅背景)
    img_scene = Image.new('RGBA', (1920, 1080), (70, 50, 40, 255)) # 暗棕色，不透明
    # 添加一些简单的图形来模拟场景
    for i in range(5):
        x1, y1 = (i * 300) % 1920, (i * 200) % 1080
        x2, y2 = x1 + 200, y1 + 150
        Image.Image.paste(img_scene, Image.new('RGBA', (x2 - x1, y2 - y1), (100, 80, 70, 255)), (x1, y1))
    img_scene.save(os.path.join(scenes_dir, "placeholder_scene.png"))
    print("  - 生成 assets/scenes/placeholder_scene.png")

    # placeholder_forest.png (模拟森林背景)
    img_forest = Image.new('RGBA', (1920, 1080), (40, 70, 50, 255)) # 暗绿色，不透明
    for i in range(5):
        x1, y1 = (i * 250) % 1920, (i * 150) % 1080
        x2, y2 = x1 + 180, y1 + 120
        Image.Image.paste(img_forest, Image.new('RGBA', (x2 - x1, y2 - y1), (60, 90, 70, 255)), (x1, y1))
    img_forest.save(os.path.join(scenes_dir, "placeholder_forest.png"))
    print("  - 生成 assets/scenes/placeholder_forest.png")

    # bg_menu.png (菜单背景)
    img_menu_bg = Image.new('RGBA', (1920, 1080), (20, 20, 30, 255)) # 深蓝色，不透明
    img_menu_bg.save(os.path.join(scenes_dir, "bg_menu.png"))
    print("  - 生成 assets/scenes/bg_menu.png")

    # --- UI 素材 (assets/ui) ---
    ui_dir = os.path.join(base_dir, "ui")
    os.makedirs(ui_dir, exist_ok=True)

    # ui_textbox.png (模拟对话框，半透明手写纸张纹理)
    img_textbox = Image.new('RGBA', (700, 150), (240, 230, 200, 200)) # 浅米色，半透明
    # 添加一些噪点模拟纸张纹理
    for x in range(700):
        for y in range(150):
            r, g, b, a = img_textbox.getpixel((x, y))
            # 颗粒感优化：降低噪点振幅并做轻微模糊，保留纸张质感但更细腻
            noise = int((os.urandom(1)[0] / 255.0 - 0.5) * 16) # -8 到 +8 的随机噪点
            img_textbox.putpixel((x, y), (max(0, min(255, r + noise)), max(0, min(255, g + noise)), max(0, min(255, b + noise)), a))
    img_textbox = img_textbox.filter(ImageFilter.GaussianBlur(radius=0.6))
    img_textbox.save(os.path.join(ui_dir, "ui_textbox.png"))
    print("  - 生成 assets/ui/ui_textbox.png")

    # placeholder_button.png (模拟按钮)
    img_button = Image.new('RGBA', (200, 80), (100, 100, 200, 255)) # 蓝色，不透明
    # 添加一个简单的文字
    # from PIL import ImageDraw, ImageFont
    # draw = ImageDraw.Draw(img_button)
    # font = ImageFont.truetype("arial.ttf", 30) # 需要系统中有arial字体
    # draw.text((50, 20), "按钮", font=font, fill=(255, 255, 255, 255))
    img_button.save(os.path.join(ui_dir, "placeholder_button.png"))
    print("  - 生成 assets/ui/placeholder_button.png")

    # next_indicator.png (模拟跳动小箭头)
    img_indicator = Image.new('RGBA', (30, 20), (255, 255, 255, 255)) # 白色小箭头
    # 绘制一个简单的三角形作为箭头
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img_indicator)
    draw.polygon([(0, 0), (30, 0), (15, 20)], fill=(255, 255, 255, 255))
    img_indicator.save(os.path.join(ui_dir, "next_indicator.png"))
    print("  - 生成 assets/ui/next_indicator.png")

    # --- 字体素材 (assets/fonts) ---
    fonts_dir = os.path.join(base_dir, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    # PixelOperator.ttf (模拟像素字体)
    # Create an empty placeholder file. In a real project, a proper TTF file should be placed here.
    with open(os.path.join(fonts_dir, "PixelOperator.ttf"), "w") as f:
        pass
    print("  - 生成 assets/fonts/PixelOperator.ttf (空占位符，请手动放置实际字体文件)")

    # --- 音频素材 (assets/audio) ---
    audio_dir = os.path.join(base_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    # menu_bgm.mp3 (菜单背景音乐)
    # with open(os.path.join(audio_dir, "menu_bgm.mp3"), "w") as f:
    #     f.write("""
    #     This is a placeholder for menu_bgm.mp3.
    #     In a real project, you would place the actual audio file here.
    #     """)
    print("  - 请手动放置 menu_bgm.mp3 到 assets/audio/ 目录，目前为一个空占位符。")

    print("测试素材生成完毕！")

if __name__ == "__main__":
    # 确保 assets/scenes 和 assets/ui 目录存在，因为 AssetManager 会用到
    os.makedirs(os.path.join("assets", "scenes"), exist_ok=True)
    os.makedirs(os.path.join("assets", "ui"), exist_ok=True)
    generate_test_assets()
