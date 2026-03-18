import os
from PIL import Image

class ImageValidator:
    def __init__(self, assets_root_dir, dpi_threshold=300):
        self.assets_root_dir = assets_root_dir
        self.dpi_threshold = dpi_threshold
        self.feedback = []

    def _check_alpha_channel(self, image_path):
        try:
            img = Image.open(image_path)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                return True, ""
            else:
                return False, "图片不是透明背景（缺少Alpha通道或透明度信息）。"
        except Exception as e:
            return False, f"无法打开或检查Alpha通道: {e}"

    def _check_dpi(self, image_path):
        try:
            img = Image.open(image_path)
            if 'dpi' in img.info and len(img.info['dpi']) == 2:
                # PIL的dpi是一个元组 (x_dpi, y_dpi)
                x_dpi, y_dpi = img.info['dpi']
                # 通常我们只关心其中一个，或者取平均值，这里简化为检查x_dpi
                if x_dpi >= self.dpi_threshold:
                    return True, ""
                else:
                    return False, f"DPI ({x_dpi}) 低于要求 ({self.dpi_threshold}dpi)。"
            else:
                # 如果没有dpi信息，我们假设其不符合要求或者需要手动检查
                return False, "图片缺少DPI元数据，无法自动检查分辨率。"
        except Exception as e:
            return False, f"无法打开或检查DPI: {e}"

    def validate_assets(self):
        self.feedback = []
        all_image_files_count = 0
        for root, _, files in os.walk(self.assets_root_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    all_image_files_count += 1

                if file.lower().endswith(('.png')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.assets_root_dir)
                    
                    issues = []

                    # 检查 Alpha 通道
                    has_alpha, alpha_msg = self._check_alpha_channel(file_path)
                    if not has_alpha:
                        issues.append(f"透明背景检查失败: {alpha_msg}")

                    # 检查 DPI
                    is_high_dpi, dpi_msg = self._check_dpi(file_path)
                    if not is_high_dpi:
                        issues.append(f"DPI检查失败: {dpi_msg}")

                    if issues:
                        self.feedback.append(f"文件: {relative_path}\n  问题:\n    - " + "\n    - ".join(issues))
                
                elif file.lower().endswith(('.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.assets_root_dir)
                    self.feedback.append(f"文件: {relative_path}\n  问题:\n    - 文件格式不符合要求。请使用PNG格式。")

        return len(self.feedback) == 0, all_image_files_count

    def generate_feedback_report(self, output_file="feedback.txt", all_image_files_count=0):
        if not self.feedback:
            if all_image_files_count == 0:
                report_content = "assets 目录下没有找到任何图片素材，等待素材输入。\n"
            else:
                report_content = "所有PNG素材均符合分辨率和透明背景要求。\n"
        else:
            report_content = "--- 素材校验反馈报告 ---\n\n"
            report_content += "以下文件不符合要求：\n\n"
            report_content += "\n\n".join(self.feedback)
            report_content += "\n\n请根据以上问题修改素材，确保分辨率达到300dpi且为透明背景的PNG格式。"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"反馈报告已生成: {output_file}")

# 示例用法
if __name__ == "__main__":
        assets_to_validate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

        validator = ImageValidator(assets_to_validate)
        print(f"正在扫描 {assets_to_validate} 目录下的素材...")

        is_valid, all_image_files_count = validator.validate_assets()

        if is_valid:
            if all_image_files_count == 0:
                print("assets 目录下没有找到任何图片素材，等待素材输入。")
            else:
                print("所有PNG素材均符合要求！")
        else:
            print("发现不符合要求的素材，正在生成反馈报告...")
            validator.generate_feedback_report("validation_feedback.txt", all_image_files_count)
