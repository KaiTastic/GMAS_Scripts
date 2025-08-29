# !/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   imageCutter.py
@Time    :   2024/12/10 15:03:00
@Author  :   Kai Cao 
@Version :   1.0.1
@Contact :   caokai_cgs@163.com
@License :   
@Copyright Statement:   Full Copyright
@Desc    :   Python==3.10
             tqdm==4.62.3
             Pillow==8.4.0
             numpy==1.21.4
'''

"""
    Version: 1.0.1
             Bug fix: 修复了无法保存日志文件的问题
"""

import os
from concurrent.futures import ThreadPoolExecutor
import argparse
import multiprocessing
from tqdm import tqdm
from PIL import Image


Image.MAX_IMAGE_PIXELS = None


def find_files_with_suffix(folder_path, suffix):
    files = []
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith(suffix):
                files.append(os.path.join(dirpath, filename))
    return files

def remove_files_with_string(files, string):
    files_to_remove = [file for file in files if string in os.path.basename(file)]
    prefixes_to_remove = {os.path.splitext(os.path.basename(file))[0].split('_split_')[0] for file in files_to_remove}
    
    filtered_files = []
    for file in files:
        basename = os.path.basename(file)
        prefix = os.path.splitext(basename)[0].split('_split_')[0]
        if prefix not in prefixes_to_remove:
            filtered_files.append(file)
    
    return filtered_files

def split_image(image_path, num_splits, inconsistent_files, auto_split):
    try:
        with Image.open(image_path) as img:
            width, height = img.size

            # 计算图像宽度除以6500并四舍五入
            # Calculate the number of splits based on the width of the image, rounded to the nearest integer
            # 6500 pixels is the approximate width of a single image of a thin section
            calculated_splits = max(1, round(width / 6500))  # 确保至少为1
            
            if calculated_splits != num_splits:
                print(f"警告: 图像 {image_path} 的设定的分割数 ({num_splits}) 和计算的分割数 ({calculated_splits}) 不一致")
                # 将不一致的文件记录到日志文件
                inconsistent_files.append(image_path)

                if auto_split:
                    print(f"将使用计算的分割数 ({calculated_splits})")
                    num_splits = calculated_splits
                else:
                    print(f"将使用设定的分割数 ({num_splits})")

            # 计算每个分割的宽度
            split_width = width // num_splits

            split_images = []

            for i in range(num_splits):
                left = i * split_width
                right = (i + 1) * split_width if i < num_splits - 1 else width
                box = (left, 0, right, height)
                split_image = img.crop(box)
                split_images.append((split_image, i, img.format))  # Pass the original image format

            return split_images
    except Exception as e:
        print(f"错误: 无法处理图像文件 {image_path}: {str(e)}")
        return []

def save_image(split_img, i, image_path, img_format):
    try:
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        newname = f'{name}_split_{i+1}{ext}'
        
        # 获取原始图像的目录
        dir_path = os.path.dirname(image_path)
        new_path = os.path.join(dir_path, newname)

        # 检查文件是否已经存在
        if os.path.exists(new_path):
            print(f'{new_path} 已经存在，不能覆盖，跳过保存')
            return

        # 获取原始图像的压缩参数
        save_params = {}
        if img_format == 'JPEG':
            save_params['quality'] = 95  # 保持高质量
        elif img_format == 'PNG':
            save_params['compress_level'] = 6  # 默认压缩级别

        split_img.save(new_path, img_format, **save_params)
    except Exception as e:
        print(f"错误: 无法保存图像文件 {new_path}: {str(e)}")
    finally:
        split_img.close()

def process_image(image_path, num_splits, executor, inconsistent_files, auto_split):
    if num_splits == 1:
        print(f"图像 {image_path} 的分割数为1，跳过处理")
        return

    split_images = split_image(image_path, num_splits, inconsistent_files, auto_split)
    if split_images:  # 只有成功分割的图像才提交保存任务
        for split_img, i, img_format in split_images:
            executor.submit(save_image, split_img, i, image_path, img_format)

def main(folder_path, num_splits, auto_split, suffix, string):

    if os.path.exists(folder_path) and os.path.isdir(folder_path):

        # 找出具有特定后缀名的文件
        files = find_files_with_suffix(folder_path, suffix)
        # 剔除包含特定字符串的文件及其前缀相同的文件
        files = remove_files_with_string(files, string)
        # 根据系统的 CPU 核心数来调整线程池的大小
        num_workers = multiprocessing.cpu_count()
        inconsistent_files = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for file in tqdm(files, desc="Processing images"):
                process_image(file, num_splits, executor, inconsistent_files, auto_split)
        
        print("所有图像处理完成, 请耐心等待线程池关闭,\n文件保存中...")
        
        # 将不一致的文件记录到日志文件
        # 检查该运行位置的目录
        currentFolder = os.getcwd()
        # 创建日志文件
        logFile = os.path.join(currentFolder, "inconsistent_files.log")
        if inconsistent_files:
            with open(logFile, "w", encoding='utf-8') as log_file:
                for file in inconsistent_files:
                    log_file.write(f"{file}\n")
            print(f"不一致的文件已记录到 'inconsistent_files.log' 文件中")

        print("线程池关闭, 文件保存完成, 可以退出程序")

    else:
        print(f"路径 '{folder_path}' 不是有效的文件目录，请检查路径是否正确")
        print("程序退出")
        exit()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Split images in a directory into multiple parts.')

    parser.add_argument('--folder_path', type=str, required=True, help='Root directory to search for images.')
    parser.add_argument('--num_splits', type=int, required=True, help='Number of splits.')
    parser.add_argument('--auto_split', action='store_true', help='Automatically use calculated split number if different from specified split number.')
    parser.add_argument('--suffix', type=str, default=".jpg", help='File suffix to search for.')
    parser.add_argument('--string', type=str, default="_split_", help='String to exclude from filenames.')

    args = parser.parse_args()

    # 参数验证
    if args.num_splits <= 0:
        print("错误: 分割数必须大于0")
        exit(1)

    main(args.folder_path, args.num_splits, args.auto_split, args.suffix, args.string)