import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt


class YOLOAnnotationProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO标注批处理工具")
        self.setGeometry(300, 300, 600, 500)
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout()
        
        # 输入文件夹选择
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入文件夹:"))
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setReadOnly(True)
        input_layout.addWidget(self.input_folder_edit)
        self.input_browse_btn = QPushButton("浏览...")
        self.input_browse_btn.clicked.connect(self.select_input_folder)
        input_layout.addWidget(self.input_browse_btn)
        
        # 输出文件夹选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件夹:"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setReadOnly(True)
        output_layout.addWidget(self.output_folder_edit)
        self.output_browse_btn = QPushButton("浏览...")
        self.output_browse_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_browse_btn)
        
        # 处理选项
        self.overwrite_check = QCheckBox("覆盖原始文件（不创建新副本）")
        self.overwrite_check.stateChanged.connect(self.toggle_overwrite)
        
        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.process_btn.clicked.connect(self.process_files)
        
        # 日志显示
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("处理日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 添加到主布局
        main_layout.addLayout(input_layout)
        main_layout.addLayout(output_layout)
        main_layout.addWidget(self.overwrite_check)
        main_layout.addWidget(self.process_btn)
        main_layout.addLayout(log_layout)
        
        self.setLayout(main_layout)
        
        # 状态变量
        self.input_folder = ""
        self.output_folder = ""
    
    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_folder = folder
            self.input_folder_edit.setText(folder)
            if not self.output_folder_edit.text():
                self.output_folder = os.path.join(folder, "processed")
                self.output_folder_edit.setText(self.output_folder)
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.output_folder_edit.setText(folder)
    
    def toggle_overwrite(self, state):
        if state == Qt.Checked:
            self.output_folder_edit.setEnabled(False)
            self.output_browse_btn.setEnabled(False)
        else:
            self.output_folder_edit.setEnabled(True)
            self.output_browse_btn.setEnabled(True)
    
    def process_files(self):
        if not self.input_folder:
            QMessageBox.warning(self, "警告", "请先选择输入文件夹！")
            return
        
        if not self.overwrite_check.isChecked() and not self.output_folder:
            QMessageBox.warning(self, "警告", "请选择输出文件夹！")
            return
        
        overwrite = self.overwrite_check.isChecked()
        self.log_text.clear()
        
        try:
            # 创建输出文件夹（如果不是覆盖模式）
            if not overwrite and not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
                self.log_text.append(f"创建输出文件夹: {self.output_folder}")
            
            # 获取所有txt文件
            files = [f for f in os.listdir(self.input_folder) if f.lower().endswith('.txt')]
            if not files:
                self.log_text.append("未找到任何txt文件！")
                return
            
            self.log_text.append(f"找到 {len(files)} 个txt文件")
            processed_count = 0
            
            for filename in files:
                input_path = os.path.join(self.input_folder, filename)
                output_path = input_path if overwrite else os.path.join(self.output_folder, filename)
                
                try:
                    with open(input_path, 'r') as f:
                        lines = f.readlines()
                    
                    processed_lines = []
                    for line in lines:
                        parts = line.strip().split()
                        if parts:
                            try:
                                label = int(parts[0])
                                # 如果标签值 >= 15，则减1
                                if label >= 15:
                                    parts[0] = str(label - 1)
                                processed_lines.append(" ".join(parts) + "\n")
                            except ValueError:
                                processed_lines.append(line)  # 保留无法解析的行
                    
                    with open(output_path, 'w') as f:
                        f.writelines(processed_lines)
                    
                    processed_count += 1
                    self.log_text.append(f"处理完成: {filename}")
                
                except Exception as e:
                    self.log_text.append(f"处理 {filename} 时出错: {str(e)}")
            
            self.log_text.append("\n处理完成！")
            self.log_text.append(f"成功处理 {processed_count}/{len(files)} 个文件")
            
            if not overwrite:
                self.log_text.append(f"处理后的文件已保存到: {self.output_folder}")
        
        except Exception as e:
            self.log_text.append(f"处理过程中发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理过程中发生错误:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YOLOAnnotationProcessor()
    window.show()
    sys.exit(app.exec_())