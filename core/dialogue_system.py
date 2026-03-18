import json

class DialogueSystem:
    def __init__(self, ui_manager=None):
        """
        初始化对话框系统。
        :param ui_manager: 负责渲染的 UI 管理器实例，此处为预留接口。
        """
        self.ui_manager = ui_manager
        self.current_dialogue_data = None

    def load_dialogue_data(self, dialogue_json_path):
        """
        加载对话数据。
        :param dialogue_json_path: 包含对话数据的 JSON 文件路径。
        """
        try:
            with open(dialogue_json_path, 'r', encoding='utf-8') as f:
                self.current_dialogue_data = json.load(f)
            print(f"Dialogue data loaded from {dialogue_json_path}")
        except FileNotFoundError:
            print(f"Error: Dialogue JSON file not found at {dialogue_json_path}")
            self.current_dialogue_data = None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {dialogue_json_path}")
            self.current_dialogue_data = None

    def display_dialogue(self, character_name, text):
        """
        显示对话。
        :param character_name: 说话的角色名称。
        :param text: 对话内容。
        """
        print(f"对话框 (对话): [{character_name}] {text}")
        # 实际游戏中，这里会调用 UI 管理器来渲染对话框
        if self.ui_manager:
            self.ui_manager.render_dialogue(character_name, text, style='dialogue')
        self._render_background()

    def display_narration(self, text):
        """
        显示心理描写或旁白。
        :param text: 心理描写或旁白内容。
        """
        print(f"对话框 (心理描写/旁白): *{text}*")
        # 实际游戏中，这里会调用 UI 管理器来渲染心理描写
        if self.ui_manager:
            self.ui_manager.render_dialogue(None, text, style='narration')
        self._render_background()

    def display_options(self, options):
        """
        显示选项列表，并返回玩家的选择。
        :param options: 选项列表，每个选项是一个字典 {'text': '选项文本', 'effect': '效果ID'}
        :return: 玩家选择的选项索引或效果ID（取决于具体实现）。
        """
        print("对话框 (选项): ")
        for i, option in enumerate(options):
            print(f"  {i + 1}. {option['text']}")
        
        # 实际游戏中，这里会等待玩家输入并返回选择
        if self.ui_manager:
            chosen_option_index = self.ui_manager.render_options(options)
            return options[chosen_option_index]['effect'] if chosen_option_index is not None else None
        else:
            # 简单模拟用户输入
            while True:
                try:
                    choice = int(input("请选择一个选项: "))
                    if 1 <= choice <= len(options):
                        return options[choice - 1]['effect']
                    else:
                        print("无效的选择，请重新输入。")
                except ValueError:
                    print("请输入数字。")
        self._render_background()
        return None

    def _render_background(self):
        """
        预留一个渲染对话框背景的接口，以适配“手写纸张纹理”和半透明效果。
        这个方法通常会由底层的图形渲染引擎或 UI 框架调用。
        """
        # print("(渲染对话框背景: 手写纸张纹理，半透明)")
        if self.ui_manager:
            self.ui_manager.render_dialogue_background(texture='handwritten_paper', transparency=0.7)

# 示例用法
if __name__ == "__main__":
    # 假设有一个简单的 UI 管理器（在实际项目中会更复杂）
    class SimpleUIManager:
        def render_dialogue(self, character_name, text, style):
            if style == 'dialogue':
                print(f"[UI Manager] 渲染对话: {character_name} - {text}")
            elif style == 'narration':
                print(f"[UI Manager] 渲染旁白: {text}")

        def render_options(self, options):
            print("[UI Manager] 渲染选项并等待用户选择...")
            # 模拟用户选择第一个选项
            return 0
        
        def render_dialogue_background(self, texture, transparency):
            print(f"[UI Manager] 渲染对话背景: 纹理={texture}, 透明度={transparency}")

    ui_manager_instance = SimpleUIManager()
    dialogue_system = DialogueSystem(ui_manager=ui_manager_instance)

    # 创建一个虚拟的对话数据文件
    dummy_dialogue_data = [
        {"type": "dialogue", "character": "林墨", "text": "你好，苏府的画影。"},
        {"type": "narration", "text": "他温柔的声音回荡在空旷的房间里。"},
        {"type": "dialogue", "character": "苏清妍", "text": "...... (沉默)"},
        {"type": "options", "options": [
            {"text": "递速写稿", "effect": "show_cg_1"},
            {"text": "默默陪伴", "effect": "stay_quiet"}
        ]}
    ]
    with open("temp_dialogue.json", "w", encoding="utf-8") as f:
        json.dump(dummy_dialogue_data, f, ensure_ascii=False, indent=4)

    dialogue_system.load_dialogue_data("temp_dialogue.json")

    # 模拟游戏流程
    if dialogue_system.current_dialogue_data:
        for entry in dialogue_system.current_dialogue_data:
            if entry['type'] == "dialogue":
                dialogue_system.display_dialogue(entry['character'], entry['text'])
            elif entry['type'] == "narration":
                dialogue_system.display_narration(entry['text'])
            elif entry['type'] == "options":
                chosen_effect = dialogue_system.display_options(entry['options'])
                print(f"玩家选择了: {chosen_effect}")

    # 清理测试文件
    os.remove("temp_dialogue.json")
