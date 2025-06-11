import os
import random
import shutil

def copy_random_images(source_folder, destination_folder, num_images=100):
    # 检查源文件夹是否存在
    if not os.path.exists(source_folder):
        print(f"源文件夹 {source_folder} 不存在")
        return
    
    # 获取源文件夹中的所有图片文件
    image_files = [f for f in os.listdir(source_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    # 检查是否有足够的图片文件
    if len(image_files) < num_images:
        print(f"源文件夹中只有 {len(image_files)} 张图片，少于所需的 {num_images} 张图片")
        return
    
    # 随机选择指定数量的图片
    selected_images = random.sample(image_files, num_images)
    
    # 创建目标文件夹（如果不存在）
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    # 复制选中的图片到目标文件夹
    for image in selected_images:
        source_path = os.path.join(source_folder, image)
        destination_path = os.path.join(destination_folder, image)
        shutil.copy2(source_path, destination_path)
        print(f"已复制: {image}")
    
    print(f"成功复制 {num_images} 张图片到 {destination_folder}")

# 示例用法
source_folder = './机车'  # 替换为你的源文件夹路径
destination_folder = './100'  # 替换为你的目标文件夹路径

copy_random_images(source_folder, destination_folder, num_images=100)