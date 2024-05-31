from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QProgressBar, QMessageBox, QTextEdit, QFileDialog
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import sys
from pytube import Playlist, YouTube
import os
import ffmpeg  # Import ffmpeg

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    resume_download = pyqtSignal(int)
    video_downloaded = pyqtSignal(str)

    def __init__(self, playlist_url, quality, save_path, start_index=0, parent=None):
        super(DownloadThread, self).__init__(parent)
        self.playlist_url = playlist_url
        self.quality = quality
        self.save_path = save_path
        self.start_index = start_index
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            playlist = Playlist(self.playlist_url)
            total_videos = len(playlist.video_urls)
            for index, video_url in enumerate(playlist.video_urls):
                if not self._is_running:
                    self.resume_download.emit(index)
                    return

                yt = YouTube(video_url)
                stream = yt.streams.filter(res=self.quality, file_extension='mp4').first()
                if stream:
                    output_path = stream.download(output_path=self.save_path)
                    self.log.emit(f"Downloaded: {yt.title}")
                    self.video_downloaded.emit(output_path)  # Emit signal when download is finished
                else:
                    self.log.emit(f"No stream found for {yt.title} at {self.quality}")
                self.progress.emit(int((index + 1) / total_videos * 100))
            self.finished.emit()
        except Exception as e:
            self.log.emit(f"Error: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WT YouTube Playlist Downloader")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets/logo.png")))

        self.init_ui()
        self.center_window()
        self.download_thread = None
        self.resume_index = 0

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        self.header = QLabel("YouTube Playlist Downloader")
        self.header.setFont(QFont("Arial", 24, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("color: #3399FF;")

        self.form_layout = QVBoxLayout()

        self.url_label = QLabel("YouTube Playlist URL:")
        self.url_label.setFont(QFont("Arial", 14))
        self.url_label.setStyleSheet("color: #000000;")

        self.url_input = QLineEdit()
        self.url_input.setFont(QFont("Arial", 12))
        self.url_input.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")

        self.quality_label = QLabel("Select Quality:")
        self.quality_label.setFont(QFont("Arial", 14))
        self.quality_label.setStyleSheet("color: #000000;")

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["1080p", "720p", "480p", "360p", "240p"])
        self.quality_combo.setFont(QFont("Arial", 12))
        self.quality_combo.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")

        self.save_path_label = QLabel("Save to:")
        self.save_path_label.setFont(QFont("Arial", 14))
        self.save_path_label.setStyleSheet("color: #000000;")

        self.save_path_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        self.save_path_input.setFont(QFont("Arial", 12))
        self.save_path_input.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")

        self.browse_button = QPushButton("Browse")
        self.browse_button.setFont(QFont("Arial", 12))
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #3399FF;
                color: #FFFFFF;
                padding: 5px 10px;
                border: 1px solid #3399FF;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
        """)
        self.browse_button.clicked.connect(self.browse_folder)
        self.save_path_layout.addWidget(self.save_path_input)
        self.save_path_layout.addWidget(self.browse_button)

        self.form_layout.addWidget(self.url_label)
        self.form_layout.addWidget(self.url_input)
        self.form_layout.addWidget(self.quality_label)
        self.form_layout.addWidget(self.quality_combo)
        self.form_layout.addWidget(self.save_path_label)
        self.form_layout.addLayout(self.save_path_layout)

        self.download_button = QPushButton("Download Playlist")
        self.download_button.setFont(QFont("Arial", 14))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #33CC33;
                color: #FFFFFF;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00FF00;
            }
        """)
        self.download_button.clicked.connect(self.start_download)

        self.stop_button = QPushButton("Stop Download")
        self.stop_button.setFont(QFont("Arial", 14))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF3333;
                color: #FFFFFF;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_download)

        self.resume_button = QPushButton("Resume Download")
        self.resume_button.setFont(QFont("Arial", 14))
        self.resume_button.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #000000;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        self.resume_button.setEnabled(False)
        self.resume_button.clicked.connect(self.resume_download)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F0F8FF;
                color: #000000;
                border: 1px solid #3399FF;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #33CC33;
            }
        """)

        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 10px; border: 1px solid #3399FF; border-radius: 5px;")

        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.setFont(QFont("Arial", 14))
        self.clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: #FF3333;
                color: #FFFFFF;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
        """)
        self.clear_log_button.clicked.connect(self.clear_log)

        self.creator_layout = QHBoxLayout()
        self.creator_label = QLabel('Created By <a href="https://github.com/wasimtikki120" style="color: #FF4500; text-decoration: none;">Mohammad Wasim Tikki</a>')
        self.creator_label.setFont(QFont("Arial", 12))
        self.creator_label.setOpenExternalLinks(True) 
        self.creator_label.setStyleSheet("color: #000000;")
        self.creator_label.setAlignment(Qt.AlignCenter)

        self.creator_layout.addWidget(self.creator_label)
        self.creator_layout.setAlignment(Qt.AlignCenter)

        self.footer = QLabel("© 2024 YouTube Playlist Downloader")
        self.footer.setFont(QFont("Arial", 12))
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setStyleSheet("color: #000000;")

        self.main_layout.addWidget(self.header)
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.download_button)
        self.main_layout.addWidget(self.stop_button)
        self.main_layout.addWidget(self.resume_button)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.log_window)
        self.main_layout.addWidget(self.clear_log_button)
        self.main_layout.addLayout(self.creator_layout)
        self.main_layout.addWidget(self.footer)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #E0FFFF;
            }
            QLabel {
                color: #3399FF;
            }
            QLineEdit, QComboBox {
                background-color: #F0F8FF;
                color: #000000;
                padding: 5px;
                border: 1px solid #3399FF;
                border-radius: 5px;
            }
            QPushButton {
                padding: 10px;
                border-radius: 5px;
            }
        """)

    def center_window(self):
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        # Adjust the y-coordinate by subtracting a value (e.g., 100) to move the window higher
        center_point.setY(center_point.y() - 100)
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.save_path_input.setText(folder)

    def start_download(self):
        playlist_url = self.url_input.text()
        quality = self.quality_combo.currentText()
        save_path = self.save_path_input.text()

        if not playlist_url:
            QMessageBox.warning(self, "Error", "Please enter a playlist URL")
            return

        if not save_path:
            QMessageBox.warning(self, "Error", "Please select a folder to save videos")
            return

        self.download_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.download_thread = DownloadThread(playlist_url, quality, save_path)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.log.connect(self.update_log)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.resume_download.connect(self.set_resume_index)
        self.download_thread.video_downloaded.connect(self.enhance_video)  # Connect signal to enhance video
        self.download_thread.start()

    def stop_download(self):
        if self.download_thread:
            self.download_thread.stop()
            self.stop_button.setEnabled(False)
            self.resume_button.setEnabled(True)

    def resume_download(self):
        if self.download_thread:
            playlist_url = self.url_input.text()
            quality = self.quality_combo.currentText()
            save_path = self.save_path_input.text()

            self.download_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.resume_button.setEnabled(False)
            self.download_thread = DownloadThread(playlist_url, quality, save_path, start_index=self.resume_index)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.log.connect(self.update_log)
            self.download_thread.finished.connect(self.download_finished)
            self.download_thread.resume_download.connect(self.set_resume_index)
            self.download_thread.video_downloaded.connect(self.enhance_video)  # Connect signal to enhance video
            self.download_thread.start()

    def set_resume_index(self, index):
        self.resume_index = index

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_window.append(message)

    def clear_log(self):
        self.log_window.clear()

    def enhance_video(self, video_path):
        try:
            if not os.path.exists(video_path):
                self.update_log(f"Error: Video file not found at {video_path}")
                return

            # Set the output path for the enhanced video
            output_path = os.path.splitext(video_path)[0] + "_enhanced.mp4"

            # Use ffmpeg to upscale the video to 1080p
            ffmpeg.input(video_path).output(
                output_path, vf='scale=1920:1080', vcodec='libx264', acodec='aac'
            ).run(overwrite_output=True)

            os.replace(output_path, video_path)
            self.update_log(f"Enhanced quality of: {os.path.basename(video_path)}")
        except Exception as e:
            self.update_log(f"Enhancement error: {e}")

    def download_finished(self):
        QMessageBox.information(self, "Done", "All videos have been downloaded!")
        self.download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.resume_button.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

