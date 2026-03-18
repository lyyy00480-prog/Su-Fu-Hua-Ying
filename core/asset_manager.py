import json
import os
import sys

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径，兼容 PyInstaller 打包。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 临时文件夹路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 正常运行模式
    return os.path.join(os.path.abspath("."), relative_path)

class AssetManager:
    def __init__(self, config_path):
        """
        初始化资源管理器，加载素材配置。
        :param config_path: 素材配置文件（JSON格式）的路径。
        """
        self.config_path = get_resource_path(config_path)
        self.assets_config = {}
        self._load_config()

    def _load_config(self):
        """
        从JSON文件加载素材配置。
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Asset configuration file not found at: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.assets_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in asset configuration file: {e}")

    def get_asset_path(self, asset_id, variant_key=None):
        """
        根据素材ID和可选的变体键获取素材的实际文件路径。
        :param asset_id: 素材的唯一ID。
        :param variant_key: 可选的变体键（如 'ruined_dim', 'faint_light_strong'）。
        :return: 素材的绝对文件路径。
        :raises ValueError: 如果素材ID或变体键不存在。
        """
        asset_data = self.assets_config.get(asset_id)
        if not asset_data:
            raise ValueError(f"Asset ID not found in configuration: {asset_id}")

        if variant_key:
            # 检查是否有名为 variant_key 的直接键
            variant_path = asset_data.get(variant_key)
            if variant_path:
                return get_resource_path(os.path.join("data", "..", variant_path))
            
            # 如果没有直接找到，再尝试在 'variants' 字典中查找
            variant_path = asset_data.get("variants", {}).get(variant_key)
            if variant_path:
                return get_resource_path(variant_path)
            else:
                raise ValueError(f"Variant key '{variant_key}' not found for asset ID: {asset_id}")
        else:
            default_path = asset_data.get("default")
            if default_path:
                return get_resource_path(default_path)
            else:
                raise ValueError(f"Default path not found for asset ID: {asset_id}")

    # 简化的光影切换逻辑示例 (实际游戏中可能涉及更复杂的渲染逻辑)
    def get_shader_interface(self, asset_id, light_condition):
        """
        模拟一个获取Shader接口或透明度叠加方法的函数。
        实际的渲染逻辑会根据light_condition返回不同的shader或调整图片透明度等。
        这里仅作示意。
        :param asset_id: 素材ID。
        :param light_condition: 光照条件（例如 'dim', 'bright', 'warm'）。
        :return: 模拟的Shader指令或透明度值。
        """
        # 在实际游戏中，这里会根据 asset_id 和 light_condition 返回一个
        # 具体的渲染指令，例如一个 shader 对象，或者一个包含透明度、颜色叠加等信息的字典。
        # 为了简化，这里只是返回一个字符串。
        if light_condition == 'dim':
            return f"Apply_Dim_Shader_to_{asset_id}" # 示例：应用昏暗着色器
        elif light_condition == 'bright':
            return f"Apply_Bright_Shader_to_{asset_id}"
        elif light_condition == 'warm':
            return f"Apply_Warm_Shader_to_{asset_id}"
        else:
            return f"No_Special_Shader_for_{asset_id}" # 默认情况

# 示例用法
if __name__ == "__main__":
    # 假设 config.json 已经存在于 data 文件夹中
    current_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(current_dir, "..", "data", "assets_config.json")
    
    # 为了示例，创建一些虚拟文件路径以确保 os.path.abspath 返回正确结果
    # 在实际项目中，这些文件应该真实存在
    os.makedirs("assets/scenes", exist_ok=True)
    os.makedirs("assets/characters", exist_ok=True)
    os.makedirs("assets/ui", exist_ok=True)
    os.makedirs("assets/audio", exist_ok=True)
    with open("assets/scenes/A1_old_house_exterior_base.png", "w") as f: f.write("dummy")
    with open("assets/scenes/A1_old_house_exterior_ruined_dim.png", "w") as f: f.write("dummy")
    with open("assets/scenes/A1_attic_studio_faint_light_strong.png", "w") as f: f.write("dummy")
    with open("assets/characters/B1_linmo_fullbody.png", "w") as f: f.write("dummy")
    with open("assets/audio/bgm_chapter1.mp3", "w") as f: f.write("dummy")

    try:
        asset_manager = AssetManager(config_file_path)
        print("AssetManager 初始化成功！")

        # 获取基础素材路径
        path1 = asset_manager.get_asset_path("A1_old_house_exterior")
        print(f"A1_old_house_exterior (base): {path1}")

        # 获取变体素材路径
        path2 = asset_manager.get_asset_path("A1_old_house_exterior", "ruined_dim")
        print(f"A1_old_house_exterior (ruined_dim): {path2}")

        path3 = asset_manager.get_asset_path("A1_attic_studio", "faint_light_strong")
        print(f"A1_attic_studio (faint_light_strong): {path3}")

        # 获取没有变体的素材
        path4 = asset_manager.get_asset_path("B1_linmo_fullbody")
        print(f"B1_linmo_fullbody: {path4}")

        # 获取音频素材
        path5 = asset_manager.get_asset_path("AUDIO_bgm_chapter1")
        print(f"AUDIO_bgm_chapter1: {path5}")

        # 尝试获取不存在的素材ID
        try:
            asset_manager.get_asset_path("NON_EXISTENT_ASSET")
        except ValueError as e:
            print(f"错误测试 (不存在的素材ID): {e}")

        # 尝试获取不存在的变体
        try:
            asset_manager.get_asset_path("A1_old_house_exterior", "non_existent_variant")
        except ValueError as e:
            print(f"错误测试 (不存在的变体): {e}")

        # 模拟光影切换逻辑
        shader_instruction = asset_manager.get_shader_interface("A1_old_house_exterior", "dim")
        print(f"光影切换指令 (dim): {shader_instruction}")

        shader_instruction = asset_manager.get_shader_interface("A1_attic_studio", "warm")
        print(f"光影切换指令 (warm): {shader_instruction}")

    except (FileNotFoundError, ValueError) as e:
        print(f"AssetManager 错误: {e}")

    finally:
        # 清理虚拟文件
        os.remove("assets/scenes/A1_old_house_exterior_base.png")
        os.remove("assets/scenes/A1_old_house_exterior_ruined_dim.png")
        os.remove("assets/scenes/A1_attic_studio_faint_light_strong.png")
        os.remove("assets/characters/B1_linmo_fullbody.png")
        os.remove("assets/audio/bgm_chapter1.mp3")
        os.rmdir("assets/scenes")
        os.rmdir("assets/characters")
        os.rmdir("assets/ui")
        os.rmdir("assets/audio")
        os.rmdir("assets")
