import os
import sys
import json
import glob
import shutil
from PIL import Image, ImageDraw
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox, QCheckBox, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QPen

class ImageCropper(QThread):
    progress_updated = pyqtSignal(int, int, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    preview_ready = pyqtSignal(str, list)

    def __init__(self, image_dir, label_dir, output_dir, label_type, preview_only, parent=None):
        super().__init__(parent)
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.output_dir = output_dir
        self.label_type = label_type
        self.preview_only = preview_only
        self.canceled = False

    def run(self):
        try:
            # 支持的图像扩展名
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            
            # 收集所有图像文件
            image_files = []
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(self.image_dir, f'*{ext}')))
            
            total_files = len(image_files)
            
            for i, image_path in enumerate(image_files):
                if self.canceled:
                    break
                
                self.progress_updated.emit(i + 1, total_files, f"处理中: {os.path.basename(image_path)}")
                
                # 获取文件名（不含扩展名）
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                
                # 构建标签文件路径
                if self.label_type == "auto":
                    # 尝试自动检测标签文件
                    label_path = None
                    for ext in ['.json', '.txt']:
                        test_path = os.path.join(self.label_dir, f"{base_name}{ext}")
                        if os.path.exists(test_path):
                            label_path = test_path
                            break
                else:
                    ext = '.json' if self.label_type == "json" else '.txt'
                    label_path = os.path.join(self.label_dir, f"{base_name}{ext}")
                
                if not label_path or not os.path.exists(label_path):
                    self.error_occurred.emit(f"找不到标签文件: {base_name}")
                    continue
                
                # 打开图像
                try:
                    image = Image.open(image_path)
                except Exception as e:
                    self.error_occurred.emit(f"无法打开图像: {image_path} - {str(e)}")
                    continue
                
                # 解析标签文件
                try:
                    if label_path.endswith('.json'):
                        targets = self.parse_json_label(label_path, image.width, image.height)
                    else:
                        targets = self.parse_txt_label(label_path, image.width, image.height)
                except Exception as e:
                    self.error_occurred.emit(f"解析标签失败: {label_path} - {str(e)}")
                    continue
                
                # 生成预览图
                preview_path = os.path.join(self.output_dir, "preview", f"{base_name}_preview.jpg")
                if self.preview_only:
                    preview_path = os.path.join(self.output_dir, f"{base_name}_preview.jpg")
                
                os.makedirs(os.path.dirname(preview_path), exist_ok=True)
                self.create_preview(image.copy(), targets, preview_path)
                
                # 发送预览信号
                self.preview_ready.emit(image_path, [t[0] for t in targets])
                
                if self.preview_only:
                    continue
                
                # 裁剪并保存目标区域
                for j, (label, bbox) in enumerate(targets):
                    # 创建类别目录
                    class_dir = os.path.join(self.output_dir, label)
                    os.makedirs(class_dir, exist_ok=True)
                    
                    # 裁剪图像
                    try:
                        cropped = image.crop(bbox)
                        # 保存裁剪后的图像
                        output_path = os.path.join(class_dir, f"{base_name}_{j}.jpg")
                        cropped.save(output_path)
                    except Exception as e:
                        self.error_occurred.emit(f"裁剪失败: {label} - {str(e)}")
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"处理过程中出错: {str(e)}")
            self.finished.emit()

    def parse_json_label(self, label_path, img_width, img_height):
        targets = []
        with open(label_path, 'r') as f:
            data = json.load(f)
        
        for shape in data.get('shapes', []):
            label = shape.get('label', 'unknown')
            points = shape.get('points', [])
            
            if not points:
                continue
                
            # 计算边界框
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            x_min = max(0, min(x_coords))
            y_min = max(0, min(y_coords))
            x_max = min(img_width, max(x_coords))
            y_max = min(img_height, max(y_coords))
            
            # 确保边界框有效
            if x_max > x_min and y_max > y_min:
                bbox = (x_min, y_min, x_max, y_max)
                targets.append((label, bbox))
        
        return targets

    def parse_txt_label(self, label_path, img_width, img_height):
        targets = []
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
                
            class_id = int(parts[0])
            center_x = float(parts[1]) * img_width
            center_y = float(parts[2]) * img_height
            width = float(parts[3]) * img_width
            height = float(parts[4]) * img_height
            
            # 计算边界框
            x_min = max(0, center_x - width / 2)
            y_min = max(0, center_y - height / 2)
            x_max = min(img_width, center_x + width / 2)
            y_max = min(img_height, center_y + height / 2)
            
            # 使用类ID作为标签
            label = f"class_{class_id}"
            bbox = (x_min, y_min, x_max, y_max)
            targets.append((label, bbox))
        
        return targets

    def create_preview(self, image, targets, output_path):
        draw = ImageDraw.Draw(image)
        
        for label, bbox in targets:
            # 绘制边界框
            draw.rectangle(bbox, outline="red", width=3)
            # 添加标签
            draw.text((bbox[0] + 5, bbox[1] + 5), label, fill="red")
        
        # 保存预览图
        image.save(output_path)

    def cancel(self):
        self.canceled = True


class ImageCropperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像目标裁剪工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置应用图标
        self.setWindowIcon(QIcon(self.create_icon()))
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("图像目标裁剪工具")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 15px 0;")
        main_layout.addWidget(title_label)
        
        # 设置区域
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 图像目录选择
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("图像目录:"))
        self.image_dir_edit = QLineEdit()
        self.image_dir_edit.setPlaceholderText("选择包含图像的目录")
        image_layout.addWidget(self.image_dir_edit)
        self.image_btn = QPushButton("浏览...")
        self.image_btn.clicked.connect(self.select_image_dir)
        image_layout.addWidget(self.image_btn)
        settings_layout.addLayout(image_layout)
        
        # 标签目录选择
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("标签目录:"))
        self.label_dir_edit = QLineEdit()
        self.label_dir_edit.setPlaceholderText("选择包含标签文件的目录")
        label_layout.addWidget(self.label_dir_edit)
        self.label_btn = QPushButton("浏览...")
        self.label_btn.clicked.connect(self.select_label_dir)
        label_layout.addWidget(self.label_btn)
        settings_layout.addLayout(label_layout)
        
        # 输出目录选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录")
        output_layout.addWidget(self.output_dir_edit)
        self.output_btn = QPushButton("浏览...")
        self.output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_btn)
        settings_layout.addLayout(output_layout)
        
        # 标签类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("标签类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["自动检测", "JSON格式", "TXT格式"])
        type_layout.addWidget(self.type_combo)
        
        # 预览模式
        self.preview_check = QCheckBox("仅生成预览图")
        type_layout.addWidget(self.preview_check)
        settings_layout.addLayout(type_layout)
        
        main_layout.addWidget(settings_group)
        
        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        
        # 图像预览
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 5px;
        """)
        preview_layout.addWidget(self.preview_label)
        
        # 类别标签
        self.classes_label = QLabel("检测到的类别: ")
        self.classes_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        preview_layout.addWidget(self.classes_label)
        
        main_layout.addWidget(preview_group)
        
        # 进度条
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        main_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                background-color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        button_layout.addWidget(self.cancel_btn)
        
        self.open_btn = QPushButton("打开输出目录")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.open_btn.clicked.connect(self.open_output_dir)
        button_layout.addWidget(self.open_btn)
        
        main_layout.addLayout(button_layout)
        
        # 底部状态栏
        self.status_label = QLabel("© 2023 图像处理工具 | 准备就绪")
        self.status_label.setStyleSheet("font-size: 10px; color: #95a5a6; margin-top: 10px;")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)
        
        self.thread = None
        self.last_preview = None

    def create_icon(self):
        # 创建一个简单的应用图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制裁剪图标
        painter.setBrush(QColor(52, 152, 219))
        painter.drawRect(10, 10, 44, 44)
        
        painter.setPen(QPen(Qt.white, 3))
        painter.drawLine(20, 20, 40, 40)
        painter.drawLine(20, 40, 40, 20)
        
        painter.end()
        return pixmap

    def select_image_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像目录")
        if path:
            self.image_dir_edit.setText(path)

    def select_label_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签目录")
        if path:
            self.label_dir_edit.setText(path)

    def select_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_dir_edit.setText(path)

    def open_output_dir(self):
        output_dir = self.output_dir_edit.text()
        if output_dir and os.path.exists(output_dir):
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                os.system(f'open "{output_dir}"')
            else:
                os.system(f'xdg-open "{output_dir}"')
        else:
            QMessageBox.warning(self, "警告", "输出目录不存在或未设置！")

    def start_processing(self):
        image_dir = self.image_dir_edit.text()
        label_dir = self.label_dir_edit.text()
        output_dir = self.output_dir_edit.text()
        
        if not all([image_dir, output_dir]):
            QMessageBox.warning(self, "警告", "请选择图像目录和输出目录！")
            return
            
        if not os.path.exists(image_dir):
            QMessageBox.warning(self, "警告", "图像目录不存在！")
            return
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 如果标签目录未设置，使用图像目录
        if not label_dir:
            label_dir = image_dir
            
        # 获取标签类型
        label_type_map = {
            "自动检测": "auto",
            "JSON格式": "json",
            "TXT格式": "txt"
        }
        label_type = label_type_map[self.type_combo.currentText()]
        
        # 预览模式
        preview_only = self.preview_check.isChecked()
        
        # 清理预览目录
        preview_dir = os.path.join(output_dir, "preview")
        if os.path.exists(preview_dir):
            shutil.rmtree(preview_dir)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("开始处理...")
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.preview_label.clear()
        self.classes_label.setText("检测到的类别: ")
        
        self.thread = ImageCropper(
            image_dir, label_dir, output_dir, label_type, preview_only
        )
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.finished.connect(self.processing_finished)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.preview_ready.connect(self.update_preview)
        self.thread.start()

    def update_progress(self, current, total, message):
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"{message} ({current}/{total})")
            self.status_label.setText(f"处理中: {percent}% 完成")

    def update_preview(self, image_path, classes):
        # 尝试加载预览图
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        preview_path = os.path.join(self.output_dir_edit.text(), f"{base_name}_preview.jpg")
        
        if not os.path.exists(preview_path):
            preview_path = os.path.join(self.output_dir_edit.text(), "preview", f"{base_name}_preview.jpg")
        
        if os.path.exists(preview_path):
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                # 缩放以适应预览区域
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width(), 
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.last_preview = preview_path
        
        # 更新类别信息
        if classes:
            unique_classes = list(set(classes))
            self.classes_label.setText(f"检测到的类别: {', '.join(unique_classes)}")

    def processing_finished(self):
        self.progress_label.setText("处理完成！")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("处理完成！")
        self.thread = None
        
        # 显示完成消息
        QMessageBox.information(self, "完成", "图像处理已完成！")

    def cancel_processing(self):
        if self.thread and self.thread.isRunning():
            self.thread.cancel()
            self.thread.wait()
            self.progress_label.setText("处理已取消")
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.status_label.setText("处理已取消")

    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)
        self.status_label.setText(f"错误: {message}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 重新加载预览图以适应新尺寸
        if self.last_preview and os.path.exists(self.last_preview):
            pixmap = QPixmap(self.last_preview)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width(), 
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置全局样式
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        QLineEdit:hover {
            border: 1px solid #3498db;
        }
        QLabel {
            color: #2c3e50;
        }
    """)
    
    window = ImageCropperApp()
    window.show()
    sys.exit(app.exec_())