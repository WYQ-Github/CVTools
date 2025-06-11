import os
import json
import glob
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image

class ConverterThread(QThread):
    progress_updated = pyqtSignal(int, int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, labels_path, txt_dir, json_dir, parent=None):
        super().__init__(parent)
        self.labels_path = labels_path
        self.txt_dir = txt_dir
        self.json_dir = json_dir
        self.canceled = False

    def run(self):
        try:
            # 读取标签文件
            with open(self.labels_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            
            # 获取所有txt文件
            txt_files = glob.glob(os.path.join(self.txt_dir, '*.txt'))
            total_files = len(txt_files)
            
            for i, txt_file in enumerate(txt_files):
                if self.canceled:
                    break
                
                self.progress_updated.emit(i + 1, total_files)
                
                # 获取对应的图片文件路径
                base_name = os.path.splitext(os.path.basename(txt_file))[0]
                image_path = self.find_image_file(os.path.dirname(txt_file), base_name)
                
                if not image_path:
                    self.error_occurred.emit(f"找不到图片文件: {base_name}")
                    continue
                
                # 获取图片尺寸
                try:
                    with Image.open(image_path) as img:
                        img_width, img_height = img.size
                except Exception as e:
                    self.error_occurred.emit(f"无法读取图片尺寸: {image_path} - {str(e)}")
                    continue
                
                # 创建JSON数据结构
                json_data = {
                    "version": "2.4.4",
                    "flags": {},
                    "shapes": [],
                    "imagePath": os.path.basename(image_path),
                    "imageData": None,
                    "imageHeight": img_height,
                    "imageWidth": img_width,
                    "description": ""
                }
                
                # 处理YOLO标签
                try:
                    with open(txt_file, 'r') as f:
                        lines = f.readlines()
                    
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) < 5:
                            continue
                            
                        class_id = int(parts[0])
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        # 转换为绝对坐标
                        abs_center_x = center_x * img_width
                        abs_center_y = center_y * img_height
                        abs_width = width * img_width
                        abs_height = height * img_height
                        
                        # 计算矩形框坐标
                        x_min = abs_center_x - (abs_width / 2)
                        y_min = abs_center_y - (abs_height / 2)
                        x_max = abs_center_x + (abs_width / 2)
                        y_max = abs_center_y + (abs_height / 2)
                        
                        # 创建矩形框
                        shape = {
                            "kie_linking": [],
                            "label": self.labels[class_id] if class_id < len(self.labels) else str(class_id),
                            "score": 1.0,
                            "points": [
                                [x_min, y_min],
                                [x_max, y_min],
                                [x_max, y_max],
                                [x_min, y_max]
                            ],
                            "group_id": None,
                            "description": None,
                            "difficult": False,
                            "shape_type": "rectangle",
                            "flags": {},
                            "attributes": {}
                        }
                        json_data["shapes"].append(shape)
                    
                    # 保存JSON文件
                    json_path = os.path.join(self.json_dir, f"{base_name}.json")
                    with open(json_path, 'w') as f:
                        json.dump(json_data, f, indent=2)
                        
                except Exception as e:
                    self.error_occurred.emit(f"处理文件失败: {txt_file} - {str(e)}")
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"转换过程中出错: {str(e)}")
            self.finished.emit()

    def find_image_file(self, directory, base_name):
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        for ext in image_extensions:
            image_path = os.path.join(directory, base_name + ext)
            if os.path.exists(image_path):
                return image_path
        return None

    def cancel(self):
        self.canceled = True

class YoloToJsonConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO 转 JSON 转换器")
        self.setGeometry(100, 100, 600, 300)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标签文件选择
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("Labels 文件:"))
        self.labels_path_edit = QLineEdit()
        self.labels_path_edit.setReadOnly(True)
        labels_layout.addWidget(self.labels_path_edit)
        self.labels_btn = QPushButton("浏览...")
        self.labels_btn.clicked.connect(self.select_labels_file)
        labels_layout.addWidget(self.labels_btn)
        layout.addLayout(labels_layout)
        
        # TXT目录选择
        txt_layout = QHBoxLayout()
        txt_layout.addWidget(QLabel("TXT 文件目录:"))
        self.txt_dir_edit = QLineEdit()
        self.txt_dir_edit.setReadOnly(True)
        txt_layout.addWidget(self.txt_dir_edit)
        self.txt_btn = QPushButton("浏览...")
        self.txt_btn.clicked.connect(self.select_txt_dir)
        txt_layout.addWidget(self.txt_btn)
        layout.addLayout(txt_layout)
        
        # JSON目录选择
        json_layout = QHBoxLayout()
        json_layout.addWidget(QLabel("JSON 保存目录:"))
        self.json_dir_edit = QLineEdit()
        self.json_dir_edit.setReadOnly(True)
        json_layout.addWidget(self.json_dir_edit)
        self.json_btn = QPushButton("浏览...")
        self.json_btn.clicked.connect(self.select_json_dir)
        json_layout.addWidget(self.json_btn)
        layout.addLayout(json_layout)
        
        # 进度条
        self.progress_label = QLabel("准备就绪")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.thread = None

    def select_labels_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择标签文件", "", "Text Files (*.txt)"
        )
        if path:
            self.labels_path_edit.setText(path)

    def select_txt_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择TXT文件目录")
        if path:
            self.txt_dir_edit.setText(path)

    def select_json_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择JSON保存目录")
        if path:
            self.json_dir_edit.setText(path)

    def start_conversion(self):
        labels_path = self.labels_path_edit.text()
        txt_dir = self.txt_dir_edit.text()
        json_dir = self.json_dir_edit.text()
        
        if not all([labels_path, txt_dir, json_dir]):
            QMessageBox.warning(self, "警告", "请先选择所有必要的文件和目录！")
            return
            
        if not os.path.exists(labels_path):
            QMessageBox.warning(self, "警告", "Labels文件不存在！")
            return
            
        if not os.path.exists(txt_dir):
            QMessageBox.warning(self, "警告", "TXT目录不存在！")
            return
            
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
            
        self.progress_bar.setValue(0)
        self.progress_label.setText("开始转换...")
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        self.thread = ConverterThread(labels_path, txt_dir, json_dir)
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.finished.connect(self.conversion_finished)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.start()

    def update_progress(self, current, total):
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"处理中: {current}/{total} 文件 ({percent}%)")

    def conversion_finished(self):
        self.progress_label.setText("转换完成！")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.thread = None

    def cancel_conversion(self):
        if self.thread and self.thread.isRunning():
            self.thread.cancel()
            self.thread.wait()
            self.progress_label.setText("转换已取消")
            self.convert_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    def show_error(self, message):
        QMessageBox.critical(self, "错误", message)

if __name__ == "__main__":
    app = QApplication([])
    window = YoloToJsonConverter()
    window.show()
    app.exec_()