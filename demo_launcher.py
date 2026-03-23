import pygame
import sys
import os
import json
import math

# 导入 pygame.mixer 用于音乐播放
import pygame.mixer

from core.asset_manager import AssetManager

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容 PyInstaller 打包。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 临时文件夹路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 正常运行模式
    return os.path.join(os.path.abspath("."), relative_path)

# 初始化 Pygame
pygame.init()
pygame.mixer.init() # 初始化 mixer 模块

# 用于缓存音效
sfx_cache = {}

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
is_fullscreen = False
original_screen_width = SCREEN_WIDTH
original_screen_height = SCREEN_HEIGHT
pygame.display.set_caption("苏府画影 - 演示")

# 游戏状态
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_CREDITS = "CREDITS" # 新增感谢名单状态
current_game_state = STATE_MENU

# 帧率控制
clock = pygame.time.Clock()
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SPEAKER_COLOR = (255, 200, 100) # 角色名颜色

# 初始化 AssetManager
current_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join("data", "assets_config.json")
asset_manager = AssetManager(config_file_path)

# 字体设置
# Initialize fonts to default system fonts as a safe fallback
dialogue_font = pygame.font.Font(None, 28)
speaker_font = pygame.font.Font(None, 32) # 角色名使用稍大字体
menu_title_font = pygame.font.Font(None, 60)
menu_prompt_font = pygame.font.Font(None, 30)

# Flag to track if Chinese font was successfully loaded for dialogue/speaker
chinese_font_loaded_for_dialogue = False

# Try loading Chinese font for dialogue and speaker
try:
    chinese_font_path = asset_manager.get_asset_path("FONT_chinese_dialogue")
    if os.path.exists(chinese_font_path) and os.path.getsize(chinese_font_path) > 0:
        dialogue_font = pygame.font.Font(chinese_font_path, 28)
        speaker_font = pygame.font.Font(chinese_font_path, 32)
        chinese_font_loaded_for_dialogue = True
        print(f"Successfully loaded Chinese font from {chinese_font_path} for dialogue and speaker.")
    else:
        print(f"Chinese font file missing or empty: {chinese_font_path}. Dialogue/speaker using system default.")
except Exception as e:
    print(f"Error loading Chinese font for dialogue/speaker: {e}. Dialogue/speaker using system default.")

# Try loading Chinese font for menu. If not available, fall back to pixel font, then system default.
try:
    if chinese_font_loaded_for_dialogue: # If Chinese font was loaded for dialogue, use it for menu as well
        menu_title_font = pygame.font.Font(chinese_font_path, 60)
        menu_prompt_font = pygame.font.Font(chinese_font_path, 30)
        print(f"Successfully used Chinese font for menu.")
    else: # Chinese font was not loaded, try pixel font for menu
        pixel_font_path = asset_manager.get_asset_path("FONT_pixel")
        if os.path.exists(pixel_font_path) and os.path.getsize(pixel_font_path) > 0:
            menu_title_font = pygame.font.Font(pixel_font_path, 60)
            menu_prompt_font = pygame.font.Font(pixel_font_path, 30)
            print(f"Successfully loaded custom pixel font from {pixel_font_path} for menu.")
        else:
            print(f"Custom pixel font file missing or empty: {pixel_font_path}. Menu using system default.")
except Exception as e:
    print(f"Error loading custom font for menu: {e}. Menu using system default.")

# Diagnostic prints for font loading
if chinese_font_loaded_for_dialogue:
    print(f"DEBUG: Dialogue and Speaker font is loaded from: {chinese_font_path}")
else:
    print("DEBUG: Dialogue and Speaker font is using system default.")

# Determine which font is actually being used for menu_title_font
try:
    # Attempt to get the filename of the loaded font, if it's a file-based font
    if hasattr(menu_title_font, 'fname') and menu_title_font.fname:
        print(f"DEBUG: Menu Title font is loaded from: {menu_title_font.fname}")
    else:
        print("DEBUG: Menu Title font is using system default.")
except Exception as e:
    print(f"DEBUG: Could not determine Menu Title font source: {e}. Assuming system default.")

# 对话框位置和大小
DIALOGUE_BOX_HEIGHT = 150
DIALOGUE_BOX_MARGIN = 20 # 距离屏幕底部和左右的边距
DIALOGUE_BOX_RECT = pygame.Rect(DIALOGUE_BOX_MARGIN, SCREEN_HEIGHT - DIALOGUE_BOX_HEIGHT - DIALOGUE_BOX_MARGIN, SCREEN_WIDTH - 2 * DIALOGUE_BOX_MARGIN, DIALOGUE_BOX_HEIGHT)

# 文本内边距和行间距
TEXT_PADDING_X = 25
TEXT_PADDING_Y = 20
LINE_SPACING = 8 # 额外行间距

# 打字机效果延迟
TYPEWRITER_CHAR_DELAY_MS = 30 # 每个字符显示的毫秒数

# 加载对话框背景和Next Indicator
try:
    dialogue_box_bg_path = asset_manager.get_asset_path("UI_dialogue_box_bg")
    dialogue_box_image = pygame.image.load(dialogue_box_bg_path).convert_alpha()
    dialogue_box_image = pygame.transform.scale(dialogue_box_image, DIALOGUE_BOX_RECT.size)
except Exception as e:
    print(f"Error loading dialogue box background: {e}")
    dialogue_box_image = None # Fallback to no image

try:
    next_indicator_path = asset_manager.get_asset_path("UI_next_indicator")
    next_indicator_image = pygame.image.load(next_indicator_path).convert_alpha()
except Exception as e:
    print(f"Error loading next indicator: {e}")
    next_indicator_image = None # Fallback to no image

class MenuState:
    def __init__(self, asset_manager, screen_width, screen_height):
        self.asset_manager = asset_manager
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Load menu background
        try:
            menu_bg_path = self.asset_manager.get_asset_path("scene_menu_bg")
            self.background_image = pygame.image.load(menu_bg_path).convert_alpha()
            self.background_image = scale_image(self.background_image, screen_width, screen_height)
        except Exception as e:
            print(f"Error loading menu background: {e}. Falling back to solid color.")
            self.background_image = pygame.Surface((screen_width, screen_height))
            self.background_image.fill((0, 0, 0)) # Black fallback

        # Load menu BGM
        try:
            menu_bgm_path = self.asset_manager.get_asset_path("AUDIO_menu_bgm")
            full_menu_bgm_path = get_resource_path(menu_bgm_path) # Use get_resource_path here
            if os.path.exists(full_menu_bgm_path) and os.path.isfile(full_menu_bgm_path):
                pygame.mixer.music.load(full_menu_bgm_path)
                pygame.mixer.music.play(-1) # Loop indefinitely
            else:
                print(f"Warning: Menu BGM file not found or invalid: {full_menu_bgm_path}. Skipping BGM.")
        except Exception as e:
            print(f"Error loading menu BGM: {e}")

        self.title_text = "苏府画影"
        self.prompt_text = "Press Space to Start"

    def handle_event(self, event):
        global current_game_state
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                current_game_state = STATE_PLAYING
                pygame.mixer.music.stop() # Stop menu music when starting game

                # 播放游戏开始后的 BGM (第一个对话的 BGM)
                global current_bgm_id
                first_dialogue_bgm_id = dialogues[0].get("bgm")
                if first_dialogue_bgm_id:
                    bgm_path = self.asset_manager.get_asset_path(first_dialogue_bgm_id)
                    if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 0:
                        pygame.mixer.music.load(bgm_path)
                        pygame.mixer.music.play(-1)
                        current_bgm_id = first_dialogue_bgm_id
                        print(f"Successfully started BGM: {first_dialogue_bgm_id} from {bgm_path}")
                    else:
                        print(f"Warning: BGM file missing or empty: {bgm_path}. Skipping BGM.")
                else:
                    print("No BGM specified for the first dialogue entry.")

    def draw(self, screen):
        screen.blit(self.background_image, (0, 0))

        # Draw title
        title_surface = menu_title_font.render(self.title_text, True, WHITE)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 3))
        screen.blit(title_surface, title_rect)

        # Draw blinking prompt
        current_time = pygame.time.get_ticks()
        blink_interval = 700 # milliseconds
        if (current_time % (2 * blink_interval)) < blink_interval:
            prompt_surface = menu_prompt_font.render(self.prompt_text, True, WHITE)
            prompt_rect = prompt_surface.get_rect(center=(self.screen_width // 2, self.screen_height * 2 // 3))
            screen.blit(prompt_surface, prompt_rect)

# 缩放背景图片以适应窗口
def scale_image(image, target_width, target_height):
    image_width, image_height = image.get_size()

    # 计算需要保持的比例因子 (使图片完全覆盖目标区域)
    scale_factor = max(target_width / image_width, target_height / image_height)

    # 缩放图片
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    scaled_image = pygame.transform.scale(image, (new_width, new_height))

    # 计算裁剪区域，使图片居中
    crop_x = (new_width - target_width) // 2
    crop_y = (new_height - target_height) // 2

    # 裁剪图片
    cropped_image = scaled_image.subsurface((crop_x, crop_y, target_width, target_height))
    return cropped_image

# 加载对话数据
try:
    # Use get_resource_path for script.json
    script_json_path = get_resource_path(os.path.join("data", "script.json"))
    with open(script_json_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
    dialogues = script_data
except FileNotFoundError:
    print("Error: script.json not found. Using dummy dialogue.")
    dialogues = [
        {"text": "林墨：剧本文件未找到，使用默认台词。", "background": "scene_old_house"}
    ]

# 从 data/credits.json 加载感谢名单内容
try:
    credits_json_path = get_resource_path(os.path.join("data", "credits.json"))
    with open(credits_json_path, "r", encoding="utf-8") as f:
        CREDITS_CONTENT = json.load(f)["credits"]
    print(f"Successfully loaded credits from {credits_json_path}")
except Exception as e:
    print(f"Warning: Could not load credits.json: {e}. Using default.")
    CREDITS_CONTENT = ["感谢游玩", "", "希望您喜欢这个故事！"]

# 感谢名单滚动相关变量
credits_scroll_offset = 0
credits_scroll_speed = 50  # 像素/秒
credits_finished = False

# 初始背景加载
def load_background_image(background_id):
    try:
        background_path = asset_manager.get_asset_path(background_id)
        if not background_path:
            raise ValueError(f"Background ID '{background_id}' not found in assets_config.json")
        image = pygame.image.load(background_path).convert_alpha()
        return scale_image(image, SCREEN_WIDTH, SCREEN_HEIGHT)
    except Exception as e:
        print(f"Error loading background image '{background_id}': {e}")
        # Fallback to a solid color background
        fallback_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fallback_image.fill((50, 50, 50)) # Deep gray as fallback
        return fallback_image

def play_sfx(sfx_id):
    """
    根据 SFX ID 播放音效。
    """
    print(f"DEBUG: Attempting to play SFX with ID: {sfx_id}")
    if sfx_id not in sfx_cache:
        try:
            sfx_path = asset_manager.get_asset_path(sfx_id)
            print(f"DEBUG: Resolved SFX path: {sfx_path}")
            if os.path.exists(sfx_path) and os.path.getsize(sfx_path) > 0:
                sfx_cache[sfx_id] = pygame.mixer.Sound(sfx_path)
                print(f"Successfully loaded SFX from {sfx_path}")
            else:
                print(f"Warning: SFX file missing or empty: {sfx_path}. Skipping SFX.")
                return # 文件不存在或为空，不缓存也不播放
        except Exception as e:
            print(f"Error loading SFX {sfx_id}: {e}. Skipping SFX.")
            return # 加载失败，不缓存也不播放

    if sfx_id in sfx_cache:
        sfx_cache[sfx_id].play()
        print(f"DEBUG: Playing SFX: {sfx_id}")
    else:
        print(f"DEBUG: SFX {sfx_id} not in cache, not playing.")

# Instantiate game states
menu_state = MenuState(asset_manager, SCREEN_WIDTH, SCREEN_HEIGHT)

current_background_id = dialogues[0]["background"] if dialogues else "scene_old_house"
active_background_image = load_background_image(current_background_id)
next_background_image = None # 用于淡入的新背景

# 淡入淡出效果变量
fading_out = False
fading_in = False
fade_alpha = 0 # 0-255
fade_speed = 5 # 淡入淡出速度，每帧变化的alpha值

current_dialogue_index = 0

# BGM 播放相关变量
current_bgm_id = None # 用于跟踪当前播放的 BGM ID

# 打字机效果变量
typing_text_index = 0
typing_speed = 1 # 每帧增加的字符数
is_typing_finished = False

last_char_time = pygame.time.get_ticks() # 用于打字机效果的时间控制

# 游戏循环
running = True
while running:
    dt = clock.tick(FPS) / 1000.0 # 获取自上一帧以来的时间（秒），用于独立于帧率的动画

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Handle F11 for fullscreen toggle in all states
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            is_fullscreen = not is_fullscreen
            if is_fullscreen:
                screen = pygame.display.set_mode((original_screen_width, original_screen_height), pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode((original_screen_width, original_screen_height))
        
        if current_game_state == STATE_MENU:
            menu_state.handle_event(event)
        elif current_game_state == STATE_CREDITS:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and credits_finished:
                    current_game_state = STATE_MENU
                    credits_scroll_offset = 0
                    credits_finished = False
        elif current_game_state == STATE_PLAYING:
            # Existing game event handling
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not fading_out and not fading_in: # 避免在淡入淡出时切换
                        if not is_typing_finished:
                            # 如果还在打字，则立即显示完整文本
                            typing_text_index = len(dialogues[current_dialogue_index]["text"])
                            is_typing_finished = True
                        else:
                            # 如果已显示完整，则切换到下一句
                            if current_dialogue_index < len(dialogues) - 1: # 如果不是最后一句
                                next_dialogue_index = current_dialogue_index + 1
                                new_background_id = dialogues[next_dialogue_index]["background"]
                                if new_background_id != current_background_id:
                                    # 背景变化，触发淡出
                                    fading_out = True
                                    next_background_image = load_background_image(new_background_id)
                                    current_background_id = new_background_id # 更新背景ID
                                else:
                                    # 背景不变，直接切换台词
                                    current_dialogue_index = next_dialogue_index
                                    typing_text_index = 0 # 重置打字机进度
                                    is_typing_finished = False

                                    # 播放对话音效 (如果存在)
                                    sfx_id = dialogues[current_dialogue_index].get("sfx")
                                    if sfx_id:
                                        play_sfx(sfx_id)

                                    # 检查 BGM 是否需要切换
                                    new_bgm_id = dialogues[current_dialogue_index].get("bgm")
                                    if new_bgm_id and new_bgm_id != current_bgm_id:
                                        bgm_path = asset_manager.get_asset_path(new_bgm_id)
                                        if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 0:
                                            pygame.mixer.music.load(bgm_path)
                                            pygame.mixer.music.play(-1)
                                            current_bgm_id = new_bgm_id
                                            print(f"Successfully switched BGM to: {new_bgm_id} from {bgm_path}")
                                        else:
                                            print(f"Warning: BGM file missing or empty: {bgm_path}. Skipping BGM switch.")
                                    elif not new_bgm_id and current_bgm_id: # 如果新对话没有BGM但当前有，则停止
                                        pygame.mixer.music.stop()
                                        current_bgm_id = None
                                        print("Stopped BGM as new dialogue has no BGM.")

                                    last_char_time = pygame.time.get_ticks() # 重置打字机时间
                            else: # 已经是最后一句
                                print("所有对话已显示完毕。")
                                current_game_state = STATE_CREDITS # 切换到感谢名单状态
                                pygame.mixer.music.stop() # 停止所有背景音乐
                                continue # 停留在当前对话，不进行任何操作






            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 鼠标左键
                    if not fading_out and not fading_in: # 避免在淡入淡出时切换
                        if not is_typing_finished:
                            # 如果还在打字，则立即显示完整文本
                            typing_text_index = len(dialogues[current_dialogue_index]["text"])
                            is_typing_finished = True
                        else:
                            # 如果已显示完整，则切换到下一句
                            if current_dialogue_index < len(dialogues) - 1: # 如果不是最后一句
                                next_dialogue_index = current_dialogue_index + 1
                                new_background_id = dialogues[next_dialogue_index]["background"]
                                if new_background_id != current_background_id:
                                    # 背景变化，触发淡出
                                    fading_out = True
                                    next_background_image = load_background_image(new_background_id)
                                    current_background_id = new_background_id # 更新背景ID
                                else:
                                    # 背景不变，直接切换台词
                                    current_dialogue_index = next_dialogue_index
                                    typing_text_index = 0 # 重置打字机进度
                                    is_typing_finished = False

                                    # 播放对话音效 (如果存在)
                                    sfx_id = dialogues[current_dialogue_index].get("sfx")
                                    if sfx_id:
                                        play_sfx(sfx_id)

                                    # 检查 BGM 是否需要切换
                                    new_bgm_id = dialogues[current_dialogue_index].get("bgm")
                                    if new_bgm_id and new_bgm_id != current_bgm_id:
                                        bgm_path = asset_manager.get_asset_path(new_bgm_id)
                                        if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 0:
                                            pygame.mixer.music.load(bgm_path)
                                            pygame.mixer.music.play(-1)
                                            current_bgm_id = new_bgm_id
                                            print(f"Successfully switched BGM to: {new_bgm_id} from {bgm_path}")
                                        else:
                                            print(f"Warning: BGM file missing or empty: {bgm_path}. Skipping BGM switch.")
                                    elif not new_bgm_id and current_bgm_id: # 如果新对话没有BGM但当前有，则停止
                                        pygame.mixer.music.stop()
                                        current_bgm_id = None
                                        print("Stopped BGM as new dialogue has no BGM.")

                                    last_char_time = pygame.time.get_ticks() # 重置打字机时间
                            else: # 已经是最后一句
                                print("所有对话已显示完毕。")
                                current_game_state = STATE_CREDITS # 切换到感谢名单状态
                                pygame.mixer.music.stop() # 停止所有背景音乐
                                continue # 停留在当前对话，不进行任何操作

    # 逐字显示逻辑
    if current_game_state == STATE_PLAYING:
        if not is_typing_finished and not fading_out and not fading_in:
            current_time = pygame.time.get_ticks()
            if current_time - last_char_time > TYPEWRITER_CHAR_DELAY_MS:
                typing_text_index += 1
                last_char_time = current_time # 更新时间
                if typing_text_index >= len(dialogues[current_dialogue_index]["text"]):
                    typing_text_index = len(dialogues[current_dialogue_index]["text"])
                    is_typing_finished = True

        # 淡入淡出逻辑
        if fading_out:
            fade_alpha += fade_speed
            if fade_alpha >= 255:
                fade_alpha = 255
                fading_out = False
                active_background_image = next_background_image # 切换背景
                fading_in = True
        elif fading_in:
            fade_alpha -= fade_speed
            if fade_alpha <= 0:
                fade_alpha = 0
                fading_in = False
                next_background_image = None # 清除下一背景
                # 此时台词正式切换
                current_dialogue_index = next_dialogue_index
                typing_text_index = 0
                is_typing_finished = False
                last_char_time = pygame.time.get_ticks() # 重置打字机时间

    # 绘制所有内容
    screen.fill(BLACK) # 每次循环开始清屏

    if current_game_state == STATE_MENU:
        menu_state.draw(screen)
    elif current_game_state == STATE_PLAYING:
        # 绘制背景
        # 计算背景图片绘制的起始点，使其居中
        bg_x = (SCREEN_WIDTH - active_background_image.get_width()) // 2
        bg_y = (SCREEN_HEIGHT - active_background_image.get_height()) // 2
        screen.blit(active_background_image, (bg_x, bg_y))

        # 绘制淡入淡出覆盖层
        if fading_out or fading_in:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, fade_alpha))
            screen.blit(fade_surface, (0, 0))

        # 绘制对话框背景
        if dialogue_box_image:
            screen.blit(dialogue_box_image, DIALOGUE_BOX_RECT)
        else:
            pygame.draw.rect(screen, BLACK, DIALOGUE_BOX_RECT, 0, 10) # 黑色背景
            pygame.draw.rect(screen, WHITE, DIALOGUE_BOX_RECT, 3, 10) # 白色边框

        # 绘制台词 (打字机效果)
        # 只有在没有淡入淡出时才绘制台词，或者在淡入淡出完成后绘制新台词
        if not fading_out and not fading_in:
            current_dialogue_entry = dialogues[current_dialogue_index]
            speaker_name = current_dialogue_entry.get("speaker", "") # 使用.get避免KeyError
            dialogue_text_content = current_dialogue_entry["text"]

            # 绘制角色名
            speaker_x = DIALOGUE_BOX_RECT.x + TEXT_PADDING_X
            speaker_y = DIALOGUE_BOX_RECT.y + TEXT_PADDING_Y
            if speaker_name:
                speaker_surface = speaker_font.render(speaker_name, True, SPEAKER_COLOR)
                screen.blit(speaker_surface, (speaker_x, speaker_y))
                # 对话内容从角色名下方开始
                dialogue_start_y = speaker_y + speaker_surface.get_height() + LINE_SPACING
            else:
                # 如果没有角色名，对话内容从顶部内边距开始
                dialogue_start_y = DIALOGUE_BOX_RECT.y + TEXT_PADDING_Y

            # 绘制对话内容 (支持多行和打字机效果)
            displayed_dialogue = dialogue_text_content[:typing_text_index]
            words = displayed_dialogue.split(' ')
            
            # 可用的文本区域宽度
            text_area_width = DIALOGUE_BOX_RECT.width - 2 * TEXT_PADDING_X
            
            current_line = ""
            current_line_y = dialogue_start_y
            
            for word in words:
                # 尝试添加下一个单词到当前行
                test_line = current_line + word + " "
                # 检查当前行是否超出宽度限制
                if dialogue_font.size(test_line)[0] < text_area_width:
                    current_line = test_line
                else:
                    # 如果超出，渲染当前行并开始新行
                    line_surface = dialogue_font.render(current_line.strip(), True, WHITE)
                    screen.blit(line_surface, (DIALOGUE_BOX_RECT.x + TEXT_PADDING_X, current_line_y))
                    current_line_y += line_surface.get_height() + LINE_SPACING
                    current_line = word + " " # 新行从当前单词开始
            
            # 渲染最后一行（如果有剩余）
            if current_line.strip():
                line_surface = dialogue_font.render(current_line.strip(), True, WHITE)
                screen.blit(line_surface, (DIALOGUE_BOX_RECT.x + TEXT_PADDING_X, current_line_y))


            # 绘制跳动小箭头
            if is_typing_finished and next_indicator_image:
                # 小箭头跳动效果
                indicator_offset_y = int(5 * math.sin(pygame.time.get_ticks() / 200.0)) # 垂直跳动
                indicator_rect = next_indicator_image.get_rect(
                    bottomright=(DIALOGUE_BOX_RECT.right - 15, DIALOGUE_BOX_RECT.bottom - 10 + indicator_offset_y)
                )
                screen.blit(next_indicator_image, indicator_rect)
    elif current_game_state == STATE_CREDITS:
        # 更新感谢名单滚动
        credits_scroll_offset += credits_scroll_speed * dt
        
        # 计算所有文本的总高度
        total_credits_height = 0
        for line in CREDITS_CONTENT:
            text_surface = menu_prompt_font.render(line, True, WHITE)
            total_credits_height += text_surface.get_height() + 10
        
        # 检查是否滚动完成（所有内容都滚出屏幕）
        if credits_scroll_offset > total_credits_height + SCREEN_HEIGHT:
            credits_finished = True
        
        # 渲染感谢名单（支持滚动）
        y_offset = SCREEN_HEIGHT - credits_scroll_offset
        for line in CREDITS_CONTENT:
            text_surface = menu_prompt_font.render(line, True, WHITE)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            # 只绘制在屏幕范围内的文本
            if -text_surface.get_height() < y_offset < SCREEN_HEIGHT + text_surface.get_height():
                screen.blit(text_surface, text_rect)
            y_offset += text_surface.get_height() + 10
        
        # 显示返回提示
        if credits_finished:
            hint_text = "Press Space to Return to Menu"
            hint_surface = menu_prompt_font.render(hint_text, True, WHITE)
            hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            screen.blit(hint_surface, hint_rect)

    # 更新屏幕
    pygame.display.flip()

pygame.quit()
sys.exit()
