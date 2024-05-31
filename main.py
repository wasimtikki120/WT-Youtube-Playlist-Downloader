from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QComboBox,
    QPushButton, QProgressBar, QMessageBox, QTextEdit, QFileDialog
)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
import sys
from pytube import Playlist, YouTube
import os



class DownloadThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, playlist_url, quality, save_path, parent=None):
        super(DownloadThread, self).__init__(parent)
        self.playlist_url = playlist_url
        self.quality = quality
        self.save_path = save_path

    def run(self):
        try:
            playlist = Playlist(self.playlist_url)
            total_videos = len(playlist.video_urls)
            for index, video_url in enumerate(playlist.video_urls):
                yt = YouTube(video_url)
                stream = yt.streams.filter(res=self.quality, file_extension='mp4').first()
                if stream:
                    stream.download(output_path=self.save_path)
                    self.log.emit(f"Downloaded: {yt.title}")
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
        # self.setWindowIcon(QIcon("assets/logo.png"))
        self.main_layout = QVBoxLayout()

        self.header = QLabel("YouTube Playlist Downloader")
        self.header.setFont(QFont("Arial", 24, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("color: #3399FF;")  # Deep Sky Blue
        self.main_layout.addWidget(self.header)

        self.form_layout = QVBoxLayout()

        self.url_label = QLabel("YouTube Playlist URL:")
        self.url_label.setFont(QFont("Arial", 14))
        self.url_label.setStyleSheet("color: #000000;")  # Black
        self.form_layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        self.url_input.setFont(QFont("Arial", 12))
        self.url_input.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")
        self.form_layout.addWidget(self.url_input)

        self.quality_label = QLabel("Select Quality:")
        self.quality_label.setFont(QFont("Arial", 14))
        self.quality_label.setStyleSheet("color: #000000;")  # Black
        self.form_layout.addWidget(self.quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["1080p", "720p", "480p", "360p", "240p"])
        self.quality_combo.setFont(QFont("Arial", 12))
        self.quality_combo.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")
        self.form_layout.addWidget(self.quality_combo)

        self.save_path_label = QLabel("Save to:")
        self.save_path_label.setFont(QFont("Arial", 14))
        self.save_path_label.setStyleSheet("color: #000000;")  # Black
        self.form_layout.addWidget(self.save_path_label)

        self.save_path_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        self.save_path_input.setFont(QFont("Arial", 12))
        self.save_path_input.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 5px; border: 1px solid #3399FF; border-radius: 5px;")
        self.save_path_layout.addWidget(self.save_path_input)

        self.browse_button = QPushButton("Browse")
        self.browse_button.setFont(QFont("Arial", 12))
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #3399FF;  /* Deep Sky Blue */
                color: #FFFFFF;  /* White */
                padding: 5px 10px;
                border: 1px solid #3399FF;  /* Deep Sky Blue */
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0066CC;  /* Royal Blue */
            }
        """)
        self.browse_button.clicked.connect(self.browse_folder)
        self.save_path_layout.addWidget(self.browse_button)

        self.form_layout.addLayout(self.save_path_layout)

        self.download_button = QPushButton("Download Playlist")
        self.download_button.setFont(QFont("Arial", 14))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #33CC33;  /* Lime Green */
                color: #FFFFFF;  /* White */
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00FF00;  /* Green */
            }
        """)
        self.download_button.clicked.connect(self.start_download)
        self.form_layout.addWidget(self.download_button)

        self.main_layout.addLayout(self.form_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F0F8FF;  /* Alice Blue */
                color: #000000;  /* Black */
                border: 1px solid #3399FF;  /* Deep Sky Blue */
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #33CC33;  /* Lime Green */
            }
        """)
        self.main_layout.addWidget(self.progress_bar)

        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: #F0F8FF; color: #000000; padding: 10px; border: 1px solid #3399FF; border-radius: 5px;")
        self.main_layout.addWidget(self.log_window)

        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.setFont(QFont("Arial", 14))
        self.clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: #FF3333;  /* Red */
                color: #FFFFFF;  /* White */
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #CC0000;  /* Dark Red */
            }
        """)
        self.clear_log_button.clicked.connect(self.clear_log)
        self.main_layout.addWidget(self.clear_log_button)

        self.creator_layout = QHBoxLayout()
        self.creator_label = QLabel("Created by ")
        self.creator_label.setFont(QFont("Arial", 12))
        self.creator_label.setStyleSheet("color: #000000;")  # Black
        self.creator_layout.addWidget(self.creator_label)

        self.creator_link = QLabel('<a href="https://github.com/wasimtikki120" style="color: #FF4500; text-decoration: none;">Mohammad Wasim Tikki</a>')
        self.creator_link.setFont(QFont("Arial", 12))
        self.creator_link.setOpenExternalLinks(True)
        self.creator_layout.addWidget(self.creator_link)

        self.creator_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addLayout(self.creator_layout)

        self.footer = QLabel("© 2024 YouTube Playlist Downloader")
        self.footer.setFont(QFont("Arial", 12))
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setStyleSheet("color: #000000;")  # Black
        self.main_layout.addWidget(self.footer)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.setStyleSheet("background-color: #E0FFFF;")  # Light Cyan

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
        self.download_thread = DownloadThread(playlist_url, quality, save_path)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.log.connect(self.update_log)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_window.append(message)

    def clear_log(self):
        self.log_window.clear()

    def download_finished(self):
        QMessageBox.information(self, "Done", "All videos have been downloaded!")
        self.download_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

