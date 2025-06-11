import shutil
import random
import os
import argparse

# 检查文件夹是否存在
def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def main(data_dir, save_dir):
    # 创建文件夹
    mkdir(save_dir)
    images_dir = os.path.join(save_dir, 'images')
    labels_dir = os.path.join(save_dir, 'labels')

    img_train_path = os.path.join(images_dir, 'train')
    img_test_path = os.path.join(images_dir, 'test')
    img_val_path = os.path.join(images_dir, 'val')

    label_train_path = os.path.join(labels_dir, 'train')
    label_test_path = os.path.join(labels_dir, 'test')
    label_val_path = os.path.join(labels_dir, 'val')

    mkdir(images_dir)
    mkdir(labels_dir)
    mkdir(img_train_path)
    # mkdir(img_test_path)
    mkdir(img_val_path)
    mkdir(label_train_path)
    # mkdir(label_test_path)
    mkdir(label_val_path)

    # 数据集划分比例，训练集75%，验证集15%，测试集15%，按需修改
    train_percent = 0.8
    val_percent = 0.2

    all_files = os.listdir(data_dir)
    txt_files = [f for f in all_files if f.endswith('.txt')]
    num_txt = len(txt_files)
    list_all_txt = range(num_txt)  # 范围 range(0, num)

    num_train = int(num_txt * train_percent)
    num_val = int(num_txt * val_percent)

    train = random.sample(list_all_txt, num_train)
    # 在全部数据集中取出train
    val_test = [i for i in list_all_txt if i not in train]
    # 再从val_test取出num_val个元素，val_test剩下的元素就是test
    val = random.sample(val_test, num_val)

    print("训练集数目：{}, 验证集数目：{}".format(len(train), len(val)))

    for i in list_all_txt:
        txt_name = txt_files[i][:-4]  # 去掉.txt后缀
        img_name_jpg = txt_name + '.jpg'
        img_name_png = txt_name + '.png'

        srcImage_jpg = os.path.join(data_dir, img_name_jpg)
        srcImage_png = os.path.join(data_dir, img_name_png)
        srcLabel = os.path.join(data_dir, txt_files[i])

        if os.path.exists(srcImage_jpg):
            srcImage = srcImage_jpg
            img_name = img_name_jpg
        elif os.path.exists(srcImage_png):
            srcImage = srcImage_png
            img_name = img_name_png
        else:
            print(f"Image for {txt_files[i]} not found, skipping.")
            continue

        if i in train:
            dst_train_Image = os.path.join(img_train_path, img_name)
            dst_train_Label = os.path.join(label_train_path, txt_files[i])
            shutil.copyfile(srcImage, dst_train_Image)
            shutil.copyfile(srcLabel, dst_train_Label)
        elif i in val:
            dst_val_Image = os.path.join(img_val_path, img_name)
            dst_val_Label = os.path.join(label_val_path, txt_files[i])
            shutil.copyfile(srcImage, dst_val_Image)
            shutil.copyfile(srcLabel, dst_val_Label)
        # else:
        #     dst_test_Image = os.path.join(img_test_path, img_name)
        #     dst_test_Label = os.path.join(label_test_path, txt_files[i])
        #     shutil.copyfile(srcImage, dst_test_Image)
        #     shutil.copyfile(srcLabel, dst_test_Label)

if __name__ == '__main__':
    """
    python split_datasets.py --data-dir my_datasets/color_rings --save-dir my_datasets/color_rings/train_data
    """
    parser = argparse.ArgumentParser(description='split datasets to train, val, test params')
    parser.add_argument('--data-dir', type=str, default=r'F:\Image\车号\长春\侧部车号\侧部车号标注\CB02\02\labels', help='path to the directory containing images and labels')
    parser.add_argument('--save-dir', default=r'F:\Image\车号\长春\侧部车号\侧部车号标注\CB02\02\CB02', type=str, help='directory to save split datasets')
    args = parser.parse_args()
    data_dir = args.data_dir
    save_dir = args.save_dir

    main(data_dir, save_dir)
    print("done")
