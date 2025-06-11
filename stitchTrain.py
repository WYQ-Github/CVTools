import os
from PIL import Image
import re # 用于正则表达式解析文件名

def stitch_images_in_folder(folder_path, output_size=(1200, 800)):
    """
    读取指定文件夹中的图片，每三张横向拼接，并保存为新的图片。

    参数:
    folder_path (str): 包含图片的文件夹路径。
    output_size (tuple): 拼接后输出图片的尺寸 (宽度, 高度)。
    """
    print(f"开始处理文件夹: {folder_path}")

    try: # 兼容 Pillow 不同版本
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.LANCZOS

    # 1. 获取文件夹中所有的 JPG 图片文件名
    try:
        all_files = os.listdir(folder_path)
    except FileNotFoundError:
        print(f"错误：文件夹 {folder_path} 未找到。请检查路径是否正确。")
        return
    except Exception as e:
        print(f"错误：读取文件夹 {folder_path} 失败：{e}")
        return

    image_files = [f for f in all_files if f.lower().endswith('.jpg')]
    if not image_files:
        print("文件夹中没有找到 JPG 图片。")
        return

    # 2. 定义正则表达式来解析文件名并提取编号
    #    例如：105-000-x.jpg -> 提取 ("105", "000", "x")
    #    我们主要关心中间的数字编号 "000" 用于排序和命名输出文件
    #    这里的 (.*) 表示文件名中第二個连字符后的任意字符
    filename_pattern = re.compile(r"([^-]+)-(\d+)-(.*)\.jpg", re.IGNORECASE)

    parsed_files = []
    for filename in image_files:
        match = filename_pattern.match(filename)
        if match:
            prefix = match.group(1)      # 例如 "105"
            id_str = match.group(2)      # 例如 "000"
            suffix_part = match.group(3) # 例如 "x" 或其他字符
            id_num = int(id_str)         # 将编号转为整数，方便排序
            
            parsed_files.append({
                'filename': filename,
                'path': os.path.join(folder_path, filename),
                'id_num': id_num,
                'id_str': id_str, # 保留字符串形式的ID用于命名
                'prefix': prefix,
                'suffix': suffix_part
            })
        else:
            print(f"文件名 {filename} 不符合预期的格式 (例如 'prefix-NNN-suffix.jpg')，已跳过。")

    if not parsed_files:
        print("没有找到符合命名格式的图片文件。")
        return

    # 3. 根据提取的数字编号对图片信息进行排序
    parsed_files.sort(key=lambda x: x['id_num'])
    
    print(f"找到并排序了 {len(parsed_files)} 个符合格式的图片文件。")

    # 4. 遍历排序后的图片列表，以滑动窗口（每次3张）的方式进行拼接
    stitched_count = 0
    for i in range(len(parsed_files) - 2): # 减2确保总有3张图片可以取
        img_info1 = parsed_files[i]
        img_info2 = parsed_files[i+1]
        img_info3 = parsed_files[i+2]

        try:
            # 打开三张图片
            image1 = Image.open(img_info1['path']).convert('RGB') # 转换为RGB以统一格式
            image2 = Image.open(img_info2['path']).convert('RGB')
            image3 = Image.open(img_info3['path']).convert('RGB')


            # --- 新增步骤：将每张原始图像缩放为原来的一半 ---
            w1_orig, h1_orig = image1.size
            image1_scaled = image1.resize((w1_orig // 2, h1_orig // 2), resample_filter)
            image1.close() # 关闭原始图片，释放资源

            w2_orig, h2_orig = image2.size
            image2_scaled = image2.resize((w2_orig // 2, h2_orig // 2), resample_filter)
            image2.close()

            w3_orig, h3_orig = image3.size
            image3_scaled = image3.resize((w3_orig // 2, h3_orig // 2), resample_filter)
            image3.close()

            # 获取缩放后图片的尺寸
            w1, h1 = image1_scaled.size
            w2, h2 = image2_scaled.size
            w3, h3 = image3_scaled.size

            # # 获取图片原始尺寸
            # w1, h1 = image1.size
            # w2, h2 = image2.size
            # w3, h3 = image3.size

            # 计算拼接后图片的尺寸
            # 总宽度是三张图片宽度之和
            # 高度取三张图片中最高者，以容纳所有图片内容
            total_width = w1 + w2 + w3
            max_height = max(h1, h2, h3)

            # 创建一个新的空白图片，用于粘贴三张图片
            # 背景默认为黑色，如果需要白色或其他颜色，可以添加 color="white" 参数
            stitched_image = Image.new('RGB', (total_width, max_height))

            # 将三张图片依次粘贴到新图片上
            stitched_image.paste(image1_scaled, (0, 0))
            stitched_image.paste(image2_scaled, (w1, 0)) # 第二张图片粘贴在前一张的右边
            stitched_image.paste(image3_scaled, (w1 + w2, 0)) # 第三张图片再往右

            # 5. 将拼接成的图像调整到目标尺寸 (1200x800)
            # Image.LANCZOS (或 Image.Resampling.LANCZOS for Pillow >= 9.1.0) 是一种高质量的缩放算法

            final_image = stitched_image.resize(output_size, resample_filter)

            # 6. 确定输出文件名 (使用第一张图片的编号)
            output_filename = f"{img_info1['id_str']}.jpg"
            output_path = os.path.join(folder_path, output_filename)
            
            # (可选) 如果你想把拼接后的图片保存到单独的输出文件夹，可以取消下面这几行的注释
            output_dir = os.path.join(folder_path, "stitched_output2")
            os.makedirs(output_dir, exist_ok=True) # 创建输出文件夹，如果不存在的话
            output_path = os.path.join(output_dir, output_filename)

            # 7. 保存拼接并调整大小后的图片
            final_image.save(output_path, "JPEG", quality=90) # quality参数可以调整图片质量/文件大小
            print(f"成功拼接: {img_info1['filename']}, {img_info2['filename']}, {img_info3['filename']} -> 保存为: {output_path}")
            stitched_count += 1

            # 关闭图片文件，释放资源
            image1.close()
            image2.close()
            image3.close()

        except Exception as e:
            print(f"处理图片组 ({img_info1['filename']}, {img_info2['filename']}, {img_info3['filename']}) 时发生错误: {e}")

    if stitched_count > 0:
        print(f"\n处理完成！总共拼接并保存了 {stitched_count} 张图片。")
    else:
        print("\n处理完成，但没有图片被成功拼接。请检查文件数量或错误信息。")


# ---- 主程序入口 ----
if __name__ == "__main__":
    # 请将这里的路径替换成你实际的图片文件夹路径
    # 注意：Windows路径中的反斜杠 \ 可能需要转义 (例如 \\) 或者使用原始字符串 (r"...")
    image_folder_path = r"F:\Image\020250518150820"
    
    # 调用函数开始处理
    stitch_images_in_folder(image_folder_path)

