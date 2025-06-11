import os
import json
import cv2
import numpy as np
import re

def IsChineseCharacter(text):
    '''
    判断字符中是否含有中文
    ·text   输入的字符
    ·return 是否含有字符
    '''
    pattern = re.compile(r'[\u4e00-\u9fa5]')
    result = pattern.findall(text)
    return len(result) > 0

def Imread(path):
    '''
    读取图片，不用区分路径中是否含有中文
    ·path       图片路径
    ·return     读取的图片
    '''
    bool_val = IsChineseCharacter(path)
    if bool_val:
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)
    else:
        image = cv2.imread(path, 1)
    return image
# 定义输入和输出文件夹

input_dir = r'D:\22222'
output_dir = r'D:\1111'

# --- 新增处理选项配置 ---
# PROCESSING_OPTION = 1: 将区域外的像素点置为0 (黑色) - 原始行为
# PROCESSING_OPTION = 2: 将区域内的像素点置为255 (白色)，区域外保持不变
# PROCESSING_OPTION = 3: 将区域内的像素点置为255 (白色)，区域外的像素点置为0 (黑色) - 新增行为
PROCESSING_OPTION = 1  # 在这里修改选项：1, 2 或 3
# --- 结束配置 ---

# 创建输出文件夹
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"创建输出文件夹：{output_dir}")

# 统计处理的文件数
processed_count = 0
error_count = 0

# 遍历input_dir中的所有JSON文件
for json_file in os.listdir(input_dir):
    if json_file.endswith('.json'):
        try:
            json_path = os.path.join(input_dir, json_file)
            # 构造对应的图像文件路径（假设图像文件与JSON文件同名，扩展名为.jpg）
            image_file = os.path.splitext(json_file)[0] + '.jpg'
            image_path = os.path.join(input_dir, image_file)
            
            print(f"\n正在处理：{json_file}")
            
            # 检查对应的图像文件是否存在
            if not os.path.exists(image_path):
                print(f"错误：找不到对应的图像文件：{image_file}")
                error_count += 1
                continue
            
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 读取图像
            image = Imread(image_path)
            if image is None:
                print(f"错误：无法读取图像文件：{image_file}")
                error_count += 1
                continue
                
            # 创建一个与图像大小相同的掩码，初始值为0
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            
            # 从JSON中获取矩形框坐标并在掩码上绘制
            if 'shapes' in json_data:
                for shape in json_data['shapes']:
                    current_shape_type = shape.get('shape_type')
                    points_data = shape.get('points')

                    if not points_data:
                        print(f"警告：在 {json_file} 中，形状缺少 'points' 数据，已跳过。")
                        continue

                    # 支持 'rectangle' (矩形) 和 'polygon' (多边形) 类型
                    if current_shape_type == 'rectangle' or current_shape_type == 'polygon':
                        # LabelMe 的 'rectangle' 通常也是用四个点表示的多边形
                        # 'polygon' 可以有任意数量的点

                        # 转换坐标点为整数 numpy 数组
                        points_np_array = np.array(points_data, dtype=np.int32)
                        
                        # 确保点数组是二维的 (N, 2)，并且至少有3个顶点才能形成一个可填充的多边形
                        if points_np_array.ndim == 2 and points_np_array.shape[0] >= 3 and points_np_array.shape[1] == 2:
                            cv2.fillPoly(mask, [points_np_array], 255)
                            print(f"已处理 {current_shape_type} 区域，源数据点数: {len(points_data)}，位于 {json_file}。")
                        else:
                            print(f"警告：在 {json_file} 中，形状 '{current_shape_type}' 的点数据格式不正确或点数不足 (形状: {points_np_array.shape})，无法绘制。已跳过。")
                    # else: # 如果需要处理或记录其他类型，可以在这里添加逻辑
                        # print(f"信息：在 {json_file} 中跳过非矩形/多边形类型: '{current_shape_type}'。")
            
            # 使用掩码处理图像
            result = image.copy()

            if PROCESSING_OPTION == 3:
                # 新行为: 区域内像素为255 (白色)，区域外像素为0 (黑色)
                if len(image.shape) == 3 and image.shape[2] > 1: # 彩色图像
                    result[mask == 255] = [255, 255, 255] # 区域内白色
                    result[mask == 0] = [0, 0, 0]         # 区域外黑色
                else: # 灰度图像
                    result[mask == 255] = 255             # 区域内白色
                    result[mask == 0] = 0                 # 区域外黑色
                print(f"已将 {image_file} 标注区域内像素设置为白色，区域外像素设置为黑色。")
            elif PROCESSING_OPTION == 2:
                # 行为: 将区域内的像素点置为255 (白色)
                # 区域外的像素保持原样
                if len(image.shape) == 3 and image.shape[2] > 1: # 彩色图像
                    result[mask == 255] = [255, 255, 255]
                else: # 灰度图像
                    result[mask == 255] = 255
                print(f"已将 {image_file} 标注区域内像素设置为白色。")
            else: # PROCESSING_OPTION == 1 或其他值 (默认为原始行为)
                # 原始行为: 将掩码外的区域（值为0的区域）在原图中置0
                result[mask == 0] = 0
                print(f"已将 {image_file} 标注区域外像素设置为黑色。")
            
            # 保存处理后的图像
            output_path = os.path.join(output_dir, image_file)
            if cv2.imwrite(output_path, result):
                print(f"成功保存处理后的图像：{image_file}")
                processed_count += 1
            else:
                print(f"错误：保存图像失败：{image_file}")
                error_count += 1
                
        except Exception as e:
            print(f"处理 {json_file} 时发生错误：{str(e)}")
            error_count += 1
            continue

print(f"\n处理完成！")
print(f"成功处理：{processed_count} 个文件")
print(f"处理失败：{error_count} 个文件")