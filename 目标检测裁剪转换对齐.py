import os
import json
import yaml
import shutil
import argparse
from tqdm import tqdm
from file_script import MkDir, FileList,Imread, Imwrite, ParseJson


def make_parser():
    parser = argparse.ArgumentParser("crop_trans")
    parser.add_argument("--task",      default=1, help="裁剪：0, txt2json:1, 图片标签对齐:2")
    # 数据集参数
    parser.add_argument("--data_dir",  default=r"F:\Image\车号\华兴\HXCRH", help="数据集路径")
    parser.add_argument("--img_cate",  default="jpg", help="图片后缀")
    parser.add_argument("--lab_cate",  default="txt", help="标签后缀")
    parser.add_argument("--yaml_dir",  default=r"E:\小程序\CVTools\Chehao.yaml", help="yaml路径")

    parser.add_argument("--pad_x",     default=0, help="x方向外扩像素数")       
    parser.add_argument("--pad_y",     default=0, help="y方向外扩像素数")

    parser.add_argument("--save_dir",  default=r"F:\Image\车号\华兴\json\json_labels", help="保存路径")

    return parser

def ImgKeepPaceWithLabel(data_dir, img_cate, lab_cate, save_dir):
    img_list = [i for i in os.listdir(data_dir) if i.endswith(img_cate)]
    lab_list = [i for i in os.listdir(data_dir) if i.endswith(lab_cate)]

    for img_name in img_list:
        lab_name = img_name.replace(img_cate, lab_cate)
        if not lab_name in lab_list:
            img_path = os.path.join(data_dir, img_name)
            move_img = os.path.join(save_dir, 'issue', img_name)
            MkDir(move_img)
            shutil.move(img_path, move_img)
    for lab_name in lab_list:
        img_name = lab_name.replace(lab_cate, img_cate)
        if not img_name in img_list:
            lab_path = os.path.join(data_dir, lab_name)
            move_lab = os.path.join(save_dir, 'issue', lab_name)
            MkDir(move_lab)
            shutil.move(lab_path, move_lab)


def CropImg(data_dir, img_cate, lab_cate, yaml_dir, pad_x, pad_y, save_dir):
    '''
    裁剪图片
    ·img_dir: 图片路径
    ·img_cate: 图片后缀
    ·lab_cate: 标签类型
    ·yaml_dir: yaml路径
    ·pad_x: x方向外扩像素数
    ·pad_y: y方向外扩像素数
    ·save_dir: 保存路径
    '''

    ImgKeepPaceWithLabel(data_dir, img_cate, lab_cate, save_dir)

    with open(yaml_dir, 'r', encoding='utf-8') as file:
        cfg_dict = yaml.safe_load(file)['names']

    img_list = FileList(data_dir, img_cate)
    lab_list = FileList(data_dir, lab_cate)

    for i in tqdm(range(len(img_list))):
        img_path = img_list[i]
        img_name = os.path.basename(img_path)
        lab_path = lab_list[i]
        img = Imread(img_path)
        h, w = img.shape[:2]
        if lab_cate == 'txt':
            with open(lab_path, 'r') as f:
                datas = f.readlines()
                for ind, data in enumerate(datas):
                    obj = data[:-1].split(' ')
                    name = str(cfg_dict[int(obj[0])])
                    cx = w * float(obj[1])
                    cy = h * float(obj[2])
                    ww = w * float(obj[3])
                    hh = h * float(obj[4])

                    xmin = max(0, int(cx - ww / 2 - pad_x))
                    ymin = max(0, int(cy - hh / 2 - pad_y))
                    xmax = min(w, int(cx + ww / 2 + pad_x))
                    ymax = min(h, int(cy + hh / 2 + pad_y))

                    crop_img = img[ymin:ymax, xmin:xmax]
                    save = os.path.join(save_dir, '裁剪图', name, '{0}_{1}.{2}'.format(img_name.split('.')[0], ind, img_cate))
                    MkDir(save)
                    Imwrite(save, crop_img)
        elif lab_cate == 'json':
            shapes = ParseJson(lab_path)['shapes']
            for ind, shape in enumerate(shapes):
                name = str(shape['label'])
                xmin = max(0, int(shape['points'][0][0] - pad_x))
                ymin = max(0, int(shape['points'][0][1] - pad_y))
                xmax = min(w, int(shape['points'][2][0] + pad_x))
                ymax = min(h, int(shape['points'][2][1] + pad_y))
                crop_img = img[ymin:ymax, xmin:xmax]
                save = os.path.join(save_dir, '裁剪图', name, '{0}_{1}.{2}'.format(img_name.split('.')[0], ind, img_cate))
                MkDir(save)
                Imwrite(save, crop_img)


def Txt2Json(data_dir, img_cate, yaml_dir, pad_x, pad_y, save_dir):
    '''
    txt标签转json标签
    ·img_dir: 图片路径
    ·img_cate: 图片后缀
    ·lab_cate: 标签类型
    ·yaml_dir: yaml路径
    ·pad_x: x方向外扩像素数
    ·pad_y: y方向外扩像素数
    ·save_dir: 保存路径
    '''
    ImgKeepPaceWithLabel(data_dir, img_cate, 'txt', save_dir)

    with open(yaml_dir, 'r', encoding='utf-8') as file:
        cfg_dict = yaml.safe_load(file)['names']

    img_list = FileList(data_dir, img_cate)
    lab_list = FileList(data_dir, 'txt')

    for i in tqdm(range(len(img_list))):
        img_path = img_list[i]
        img_name = os.path.basename(img_path)
        lab_path = lab_list[i]
        img = Imread(img_path)
        h, w = img.shape[:2]
        label = {'version': '2.3.6',
                 'flags': {},
                 'shapes': [],
                 "imagePath": img_name,
                 "imageData": None,
                 "imageHeight": h,
                 "imageWidth": w
                 }

        with open(lab_path, 'r') as f:
            datas = f.readlines()
            for ind, data in enumerate(datas):
                obj = data[:-1].split(' ')
                name = str(cfg_dict[int(obj[0])])
                cx = w * float(obj[1])
                cy = h * float(obj[2])
                ww = w * float(obj[3])
                hh = h * float(obj[4])

                xmin = float(max(0, int(cx - ww / 2 - pad_x)))
                ymin = float(max(0, int(cy - hh / 2 - pad_y)))
                xmax = float(min(w, int(cx + ww / 2 + pad_x)))
                ymax = float(min(h, int(cy + hh / 2 + pad_y)))

                shape = {
                    "label": name,
                    "points": [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]],
                    "group_id": None,
                    "description": "",
                    "difficult": False,
                    "shape_type": "rectangle",
                    "flags": {},
                    "attributes": {}
                }
                label['shapes'].append(shape)

        save_lab = os.path.join(save_dir, 'json标签', img_name.replace(img_cate, 'json'))
        MkDir(save_lab)
        with open(save_lab, 'w') as json_file:
            json.dump(label, json_file, indent=4)


if __name__ == '__main__':
    args = make_parser().parse_args()
    if args.task == 0:
        CropImg(args.data_dir, args.img_cate, args.lab_cate, args.yaml_dir, args.pad_x, args.pad_y, args.save_dir)
    elif args.task == 1:
        Txt2Json(args.data_dir, args.img_cate, args.yaml_dir, args.pad_x, args.pad_y, args.save_dir)
    elif args.task == 2:
        ImgKeepPaceWithLabel(args.data_dir, args.img_cate, args.lab_cate, args.ave_dir)