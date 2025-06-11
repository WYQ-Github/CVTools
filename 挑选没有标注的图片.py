import os
import shutil
import argparse

def filter_images_without_json(src_folder, dst_folder, image_extensions=None):
    if image_extensions is None:
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
    
    # 如果目标文件夹不存在则创建
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
        
    for filename in os.listdir(src_folder):
        file_lower = filename.lower()
        file_path = os.path.join(src_folder, filename)
        # 若为图片文件
        if os.path.isfile(file_path) and any(file_lower.endswith(ext) for ext in image_extensions):
            # 拼接对应的 JSON 文件名（假设 JSON 文件名与图片文件名相同，只是后缀不同）
            base_name = os.path.splitext(filename)[0]
            json_filename = base_name + '.json'
            json_path = os.path.join(src_folder, json_filename)
            
            # 如果对应的 JSON 文件不存在，则移动该图片到目标文件夹
            if not os.path.exists(json_path):
                dst_path = os.path.join(dst_folder, filename)
                shutil.move(file_path, dst_path)
                print(f"Moved: {filename}")


def filter_json_without_images(src_folder, dst_folder, image_extensions=None):
    if image_extensions is None:
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
    
    # 如果目标文件夹不存在则创建
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
        
    for filename in os.listdir(src_folder):
        file_lower = filename.lower()
        file_path = os.path.join(src_folder, filename)
        
        # 若为 JSON 文件
        if os.path.isfile(file_path) and file_lower.endswith('.json'):
            # 获取基础文件名
            base_name = os.path.splitext(filename)[0]
            
            # 检查是否存在对应的图片文件
            has_image = False
            for ext in image_extensions:
                image_filename = base_name + ext
                image_path = os.path.join(src_folder, image_filename)
                if os.path.exists(image_path):
                    has_image = True
                    break
            
            # 如果没有找到对应的图片文件，则移动该 JSON 文件到目标文件夹
            if not has_image:
                dst_path = os.path.join(dst_folder, filename)
                shutil.move(file_path, dst_path)
                print(f"Moved: {filename}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="将没有对应 JSON 标注文件的图片移动到新文件夹"
        "或者将没有对应图片文件的 JSON 标注文件移动到新文件夹"
    )
    parser.add_argument("src_folder", help="源文件夹路径")
    parser.add_argument("dst_folder", help="目标文件夹路径")
    args = parser.parse_args()
    
    filter_images_without_json(args.src_folder, args.dst_folder)
    # filter_json_without_images(args.src_folder, args.dst_folder)