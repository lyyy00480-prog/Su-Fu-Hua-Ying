import os
import json

class Sketchbook:
    def __init__(self, artwork_folder, comments_data_path=None):
        """
        初始化速写本系统。
        :param artwork_folder: 存放画作的文件夹路径。
        :param comments_data_path: 存放林墨画评的 JSON 文件路径。
        """
        self.artwork_folder = artwork_folder
        self.comments_data_path = comments_data_path
        self.artworks = []  # 存储画作路径和ID
        self.comments = {}  # 存储画评
        self._load_comments()
        self._scan_artworks()

    def _load_comments(self):
        """加载林墨画评数据。"""
        if self.comments_data_path and os.path.exists(self.comments_data_path):
            with open(self.comments_data_path, 'r', encoding='utf-8') as f:
                self.comments = json.load(f)

    def _scan_artworks(self):
        """扫描指定文件夹，读取所有画作文件（例如 PNG 格式）。"""
        self.artworks = []
        if not os.path.exists(self.artwork_folder):
            print(f"Warning: Artwork folder not found: {self.artwork_folder}")
            return

        for filename in os.listdir(self.artwork_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                artwork_path = os.path.join(self.artwork_folder, filename)
                artwork_id = os.path.splitext(filename)[0] # 使用文件名作为ID
                self.artworks.append({'id': artwork_id, 'path': artwork_path})
        self.artworks.sort(key=lambda x: x['id']) # 按ID排序，方便分页

    def get_paginated_artworks(self, page_size=5):
        """
        返回分页的画作列表。
        :param page_size: 每页显示的画作数量。
        :return: 包含多页画作的列表，每页是一个画作列表。
        """
        paginated_list = []
        for i in range(0, len(self.artworks), page_size):
            paginated_list.append(self.artworks[i:i + page_size])
        return paginated_list

    def get_artwork_comment(self, artwork_id):
        """
        获取指定画作的林墨画评。
        :param artwork_id: 画作的唯一ID。
        :return: 画作评论文本，如果不存在则返回 None。
        """
        return self.comments.get(artwork_id, "暂无画评。")

    def add_artwork(self, file_path, comment=None):
        """
        添加新画作到速写本并可附带画评。
        实际上这里只是更新内存中的列表，并不会移动文件。
        如果需要实际管理文件，需要额外的文件操作逻辑。
        :param file_path: 新画作的文件路径。
        :param comment: 林墨对该画作的评论。
        """
        artwork_id = os.path.splitext(os.path.basename(file_path))[0]
        self.artworks.append({'id': artwork_id, 'path': file_path})
        if comment:
            self.comments[artwork_id] = comment
        # 重新扫描并排序以确保最新添加的画作被正确处理
        self._scan_artworks()
        # 如果有画评文件，也应该更新
        self._save_comments()

    def _save_comments(self):
        """保存林墨画评数据到文件。"""
        if self.comments_data_path:
            with open(self.comments_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.comments, f, ensure_ascii=False, indent=4)

    def __repr__(self):
        return f"Sketchbook(artworks={len(self.artworks)}, comments={len(self.comments)})"

# 示例用法 (假设存在 artworks 文件夹和 comments.json 文件)
if __name__ == "__main__":
    # 创建一些虚拟文件用于测试
    os.makedirs("temp_artworks", exist_ok=True)
    with open("temp_artworks/artwork_01.png", "w") as f: f.write("dummy image data")
    with open("temp_artworks/artwork_02.jpg", "w") as f: f.write("dummy image data")
    with open("temp_artworks/artwork_03.png", "w") as f: f.write("dummy image data")

    # 创建虚拟画评文件
    dummy_comments = {
        "artwork_01": "林墨画评：这幅画充满了情感，线条流畅。",
        "artwork_02": "林墨画评：色彩运用大胆，引人深思。",
    }
    with open("temp_comments.json", "w", encoding="utf-8") as f:
        json.dump(dummy_comments, f, ensure_ascii=False, indent=4)

    sketchbook = Sketchbook("temp_artworks", "temp_comments.json")
    print(f"初始化速写本: {sketchbook}")

    # 获取分页画作
    for i, page in enumerate(sketchbook.get_paginated_artworks(page_size=2)):
        print(f"--- Page {i+1} ---")
        for artwork in page:
            print(f"  ID: {artwork['id']}, Path: {artwork['path']}")
            print(f"  评论: {sketchbook.get_artwork_comment(artwork['id'])}")

    # 添加新画作
    with open("temp_artworks/artwork_04.png", "w") as f: f.write("new dummy image data")
    sketchbook.add_artwork("temp_artworks/artwork_04.png", "林墨画评：这是最新的作品，风格独特。")
    print(f"添加新画作后: {sketchbook}")
    print(f"新画作评论: {sketchbook.get_artwork_comment('artwork_04')}")

    # 清理测试文件
    os.remove("temp_artworks/artwork_01.png")
    os.remove("temp_artworks/artwork_02.jpg")
    os.remove("temp_artworks/artwork_03.png")
    os.remove("temp_artworks/artwork_04.png")
    os.rmdir("temp_artworks")
    os.remove("temp_comments.json")
