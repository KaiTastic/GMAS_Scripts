# !/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   imageCutter_gui.py
@Time    :   2025/08/29
@Author  :   Kai Cao 
@Version :   1.0.0
@Contact :   caokai_cgs@163.com
@License :   
@Copyright Statement:   Full Copyright
@Desc    :   图像切割工具 - 图形化界面版本
             Python==3.10
             tqdm==4.62.3
             Pillow==8.4.0
             numpy==1.21.4
             tkinter (内置)
'''

import os
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from PIL import Image
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 导入原有的核心函数
from imageCutter import find_files_with_suffix, remove_files_with_string, split_image, save_image

Image.MAX_IMAGE_PIXELS = None


class ImageCutterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("图像切割工具 - Image Cutter v1.0.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        # self.root.iconbitmap("icon.ico")
        
        # 变量定义
        self.folder_path = tk.StringVar()
        self.num_splits = tk.IntVar(value=5)
        self.auto_split = tk.BooleanVar(value=True)
        self.suffix = tk.StringVar(value=".jpg")
        self.exclude_string = tk.StringVar(value="_split_")
        
        # 处理状态
        self.is_processing = False
        self.current_executor = None
        
        # 创建队列用于线程间通信
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        self.setup_ui()
        self.check_queues()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="图像切割工具", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 文件夹选择
        ttk.Label(main_frame, text="图像文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_path, width=50)
        folder_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        browse_btn = ttk.Button(main_frame, text="浏览", command=self.browse_folder)
        browse_btn.grid(row=1, column=2, pady=5)
        
        # 分割数设置
        ttk.Label(main_frame, text="分割数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        splits_frame = ttk.Frame(main_frame)
        splits_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        splits_spinbox = ttk.Spinbox(splits_frame, from_=1, to=20, textvariable=self.num_splits, width=10)
        splits_spinbox.grid(row=0, column=0, sticky=tk.W)
        ttk.Label(splits_frame, text="（建议根据图像宽度自动计算）").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 自动分割选项
        auto_split_check = ttk.Checkbutton(main_frame, text="自动使用计算的分割数", variable=self.auto_split)
        auto_split_check.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # 文件后缀
        ttk.Label(main_frame, text="文件后缀:").grid(row=4, column=0, sticky=tk.W, pady=5)
        suffix_frame = ttk.Frame(main_frame)
        suffix_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        suffix_combo = ttk.Combobox(suffix_frame, textvariable=self.suffix, values=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"], width=15)
        suffix_combo.grid(row=0, column=0, sticky=tk.W)
        
        # 排除字符串
        ttk.Label(main_frame, text="排除字符串:").grid(row=5, column=0, sticky=tk.W, pady=5)
        exclude_entry = ttk.Entry(main_frame, textvariable=self.exclude_string, width=20)
        exclude_entry.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="开始处理", command=self.start_processing, style="Accent.TButton")
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止处理", command=self.stop_processing, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.grid(row=0, column=2, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.grid(row=0, column=1)
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="5")
        log_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择图像文件夹")
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"选择文件夹: {folder}")
            
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def update_progress(self, current, total, message=""):
        """更新进度条"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{current}/{total} ({progress:.1f}%)")
        else:
            self.progress_var.set(0)
            self.progress_label.config(text="0/0 (0%)")
            
        if message:
            self.status_var.set(message)
            
    def validate_inputs(self):
        """验证输入参数"""
        if not self.folder_path.get():
            messagebox.showerror("错误", "请选择图像文件夹")
            return False
            
        if not os.path.exists(self.folder_path.get()):
            messagebox.showerror("错误", "选择的文件夹不存在")
            return False
            
        if self.num_splits.get() <= 0:
            messagebox.showerror("错误", "分割数必须大于0")
            return False
            
        return True
        
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
            
        self.is_processing = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.log_message("开始处理图像...")
        
        # 在新线程中执行处理
        thread = threading.Thread(target=self.process_images_thread)
        thread.daemon = True
        thread.start()
        
    def process_images_thread(self):
        """处理图像的线程函数"""
        try:
            folder_path = self.folder_path.get()
            num_splits = self.num_splits.get()
            auto_split = self.auto_split.get()
            suffix = self.suffix.get()
            exclude_string = self.exclude_string.get()
            
            # 找出文件
            self.log_queue.put("正在搜索图像文件...")
            files = find_files_with_suffix(folder_path, suffix)
            self.log_queue.put(f"找到 {len(files)} 个 {suffix} 文件")
            
            # 过滤文件
            files = remove_files_with_string(files, exclude_string)
            self.log_queue.put(f"过滤后剩余 {len(files)} 个文件需要处理")
            
            if not files:
                self.log_queue.put("没有找到需要处理的文件")
                return
                
            # 初始化进度
            self.progress_queue.put((0, len(files), "准备处理..."))
            
            # 处理文件
            num_workers = multiprocessing.cpu_count()
            inconsistent_files = []
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                self.current_executor = executor
                
                for i, file_path in enumerate(files):
                    if not self.is_processing:  # 检查是否被停止
                        break
                        
                    self.log_queue.put(f"处理文件: {os.path.basename(file_path)}")
                    self.progress_queue.put((i, len(files), f"处理中: {os.path.basename(file_path)}"))
                    
                    try:
                        self.process_single_image(file_path, num_splits, executor, inconsistent_files, auto_split)
                    except Exception as e:
                        self.log_queue.put(f"处理文件 {file_path} 时出错: {str(e)}")
                        
                self.current_executor = None
                
            # 完成处理
            self.progress_queue.put((len(files), len(files), "处理完成"))
            self.log_queue.put("所有图像处理完成，正在保存文件...")
            
            # 保存日志文件
            if inconsistent_files:
                log_file = os.path.join(os.getcwd(), "inconsistent_files.log")
                with open(log_file, "w", encoding='utf-8') as f:
                    for file in inconsistent_files:
                        f.write(f"{file}\n")
                self.log_queue.put(f"不一致的文件已记录到: {log_file}")
                
            self.log_queue.put("处理完成！")
            
        except Exception as e:
            self.log_queue.put(f"处理过程中发生错误: {str(e)}")
        finally:
            self.is_processing = False
            
    def process_single_image(self, image_path, num_splits, executor, inconsistent_files, auto_split):
        """处理单个图像"""
        if num_splits == 1:
            self.log_queue.put(f"图像 {os.path.basename(image_path)} 的分割数为1，跳过处理")
            return
            
        split_images = split_image(image_path, num_splits, inconsistent_files, auto_split)
        if split_images:
            for split_img, i, img_format in split_images:
                if not self.is_processing:  # 检查是否被停止
                    split_img.close()
                    break
                executor.submit(save_image, split_img, i, image_path, img_format)
                
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.log_message("正在停止处理...")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("已停止")
        
    def check_queues(self):
        """检查队列中的消息"""
        # 检查日志队列
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_message(message)
        except queue.Empty:
            pass
            
        # 检查进度队列
        try:
            while True:
                current, total, message = self.progress_queue.get_nowait()
                self.update_progress(current, total, message)
        except queue.Empty:
            pass
            
        # 检查处理状态
        if not self.is_processing and self.start_btn['state'] == 'disabled':
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
        # 继续检查
        self.root.after(100, self.check_queues)


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题（如果支持）
    try:
        style = ttk.Style()
        if "winnative" in style.theme_names():
            style.theme_use("winnative")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except:
        pass
        
    app = ImageCutterGUI(root)
    
    # 设置关闭事件
    def on_closing():
        if app.is_processing:
            if messagebox.askokcancel("确认", "正在处理中，确定要退出吗？"):
                app.stop_processing()
                root.destroy()
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
