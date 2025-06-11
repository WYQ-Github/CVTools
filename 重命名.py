import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QFileDialog, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt


class ImageRenamer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("图片批量重命名工具")
        self.setGeometry(100, 100, 400, 300)

        # 主布局
        main_layout = QVBoxLayout()

        # 文件夹选择部分
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("请选择图片文件夹路径")
        self.folder_path.setReadOnly(True)
        btn_select_folder = QPushButton("选择文件夹")
        btn_select_folder.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(btn_select_folder)
        main_layout.addLayout(folder_layout)

        # 命名规则部分
        rule_layout = QVBoxLayout()

        # 前缀输入框
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("前缀:")
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("例如: image_")
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.prefix_input)
        rule_layout.addLayout(prefix_layout)

        # 后缀输入框
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("后缀:")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("例如: _final")
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_input)
        rule_layout.addLayout(suffix_layout)

        # 起始序号输入框
        start_number_layout = QHBoxLayout()
        start_number_label = QLabel("起始序号:")
        self.start_number_input = QLineEdit()
        self.start_number_input.setPlaceholderText("例如: 00073 或 1")
        start_number_layout.addWidget(start_number_label)
        start_number_layout.addWidget(self.start_number_input)
        rule_layout.addLayout(start_number_layout)

        # 新增选项：从 00001 开始重新排序
        self.reorder_checkbox = QCheckBox("从指定序号开始重新排序")
        rule_layout.addWidget(self.reorder_checkbox)

        main_layout.addLayout(rule_layout)

        # 执行按钮
        btn_rename = QPushButton("开始重命名")
        btn_rename.clicked.connect(self.rename_images)
        main_layout.addWidget(btn_rename, alignment=Qt.AlignCenter)

        # 设置主布局
        self.setLayout(main_layout)

    def select_folder(self):
        """选择图片文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.folder_path.setText(folder)

    def rename_images(self):
        """重命名图片"""
        folder = self.folder_path.text()
        if not folder:
            QMessageBox.warning(self, "警告", "请先选择图片文件夹！")
            return

        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        reorder_enabled = self.reorder_checkbox.isChecked()

        # 获取起始序号
        start_number_text = self.start_number_input.text().strip()
        try:
            start_number = int(start_number_text) if start_number_text else 1
        except ValueError:
            QMessageBox.warning(self, "警告", "起始序号必须是有效的数字！")
            return

        # 获取文件夹中的所有图片文件
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in valid_extensions]

        if not files:
            QMessageBox.warning(self, "警告", "文件夹中没有找到图片文件！")
            return

        # 开始重命名
        try:
            # 如果启用重新排序，则按顺序排列文件名
            if reorder_enabled:
                files.sort()  # 按文件名排序

            for i, file in enumerate(files, start=start_number):
                old_path = os.path.join(folder, file)
                # 根据是否启用重新排序，调整序号格式
                sequence_number = str(i).zfill(5 if reorder_enabled else 3)
                new_name = f"{prefix}{sequence_number}{suffix}{os.path.splitext(file)[1]}"
                new_path = os.path.join(folder, new_name)
                os.rename(old_path, new_path)
            QMessageBox.information(self, "成功", "图片重命名完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重命名过程中发生错误：{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageRenamer()
    window.show()
    sys.exit(app.exec_())