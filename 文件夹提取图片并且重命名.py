import os
import shutil

# 源目录和目标目录
source_dir = r'G:\Imgs\PlantsImages\changchun\imageResult'
target_dir = r'G:\Imgs\PlantsImages\changchun\imageResult\CC13'

# 创建目标目录（如果不存在的话）
os.makedirs(target_dir, exist_ok=True)

# 图片计数器
image_counter = 1

# 遍历源目录下的所有文件夹和文件
for root, dirs, files in os.walk(source_dir):
    for file in files:
        # 这里可以根据需要添加其他图片格式
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # 构建源文件的完整路径
            source_file = os.path.join(root, file)
            # 构建目标文件的重命名路径
            target_file = os.path.join(target_dir, f'{image_counter:05}.jpg')
            # 复制文件到目标路径并重命名
            shutil.copy2(source_file, target_file)
            # 增加计数器
            image_counter += 1

print(f'完成！共复制了 {image_counter - 1} 张图片。')
