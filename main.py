import json
import os
from urllib.parse import urlparse
import subprocess
import warnings
import requests
from dotenv import load_dotenv

from PyQt5.QtCore import QUrl, pyqtSignal, Qt
from PyQt5.QtGui import QCursor, QFont, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtWidgets import QFileDialog, QMenu, QAction, QTabBar, QListWidget, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QMainWindow,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

class DownloadHistoryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser_window = parent

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        open_file_action = menu.addAction("Open file")
        open_file_location_action = menu.addAction("Open files location")
        delete_action = menu.addAction("Delete")
        delete_file_action = menu.addAction("Delete File")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        current_item = self.currentItem()
        if current_item is not None:
            row = self.row(current_item)
            item_text = current_item.text()
            if action == delete_action:
                self.takeItem(row)
                item_text = item_text[2:] if item_text.startswith('X ') else item_text
                if item_text in self.browser_window.download_history:
                    self.browser_window.download_history.remove(item_text)
                    self.browser_window.browser_window.save_download_history()
            elif action == delete_file_action:
                reply = QMessageBox.question(self, 'Delete Confirmation',
                                             "Are you sure you want to delete the file?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    item_text = item_text[2:] if item_text.startswith('X ') else item_text
                    if os.path.exists(item_text):
                        os.remove(item_text)
                        if item_text in self.browser_window.download_history:
                            self.browser_window.download_history.remove(item_text)
                            self.browser_window.save_download_history()
                            self.takeItem(row)
            elif action == open_file_location_action:
                item_text = item_text[2:] if item_text.startswith('X ') else item_text
                if os.path.exists(item_text):
                    subprocess.Popen(f'explorer /select,"{os.path.abspath(item_text)}"')
            elif action == open_file_action:
                item_text = item_text[2:] if item_text.startswith('X ') else item_text
                if os.path.exists(item_text):
                    os.startfile(item_text)

class DownloadHistoryWindow(QMainWindow):
    def __init__(self, download_history, browser_window):
        super().__init__()
        self.download_history = download_history
        self.browser_window = browser_window
        self.setWindowTitle("Download History")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #222; color: #eee;")

        self.main_layout = QVBoxLayout()

        if download_history:
            self.list_widget = DownloadHistoryListWidget(self)
            self.list_widget.setStyleSheet("background-color: #333; color: #eee;")
            for path in download_history:
                if not os.path.exists(path):
                    path = 'X ' + path
                self.list_widget.addItem(path)
            self.main_layout.addWidget(self.list_widget)
            self.clear_all_button = QPushButton("Clear All")
            self.clear_all_button.clicked.connect(self.clear_all)
            self.main_layout.addWidget(self.clear_all_button)
        else:
            self.label = QLabel("There aren't any downloads to display", self)
            self.label.setAlignment(Qt.AlignCenter)
            self.main_layout.addWidget(self.label)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(self.main_layout)

    def clear_all(self):
        self.list_widget.clear()
        self.download_history.clear()
        self.browser_window.save_download_history()


class HistoryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser_window = parent

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        current_item = self.currentItem()
        if current_item is not None:
            row = self.row(current_item)
            item_text = current_item.text()
            if action == delete_action:
                self.takeItem(row)
                if item_text in self.browser_window.history:
                    self.browser_window.history.remove(item_text)
                    self.browser_window.browser_window.save_history()


class HistoryWindow(QMainWindow):
    def __init__(self, history, browser_window):
        super().__init__()
        self.history = history
        self.browser_window = browser_window
        self.setWindowTitle("Browsing History")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #222; color: #eee;")

        self.main_layout = QVBoxLayout()

        if history:
            self.list_widget = HistoryListWidget(self)
            self.list_widget.setStyleSheet("background-color: #333; color: #eee;")
            for url in history:
                self.list_widget.addItem(url)
            self.main_layout.addWidget(self.list_widget)
            self.clear_all_button = QPushButton("Clear All")
            self.clear_all_button.clicked.connect(self.clear_all)
            self.main_layout.addWidget(self.clear_all_button)
        else:
            self.label = QLabel("There aren't any history to display", self)
            self.label.setAlignment(Qt.AlignCenter)
            self.main_layout.addWidget(self.label)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(self.main_layout)

    def clear_all(self):
        self.list_widget.clear()
        self.history.clear()
        self.browser_window.save_history()


class CloseableTabWidget(QTabWidget):
    tabCloseRequestedCustom = pyqtSignal(int)

    def __init__(self, browser_window):
        super().__init__()
        self.browser_window = browser_window
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.emit_tab_close_request)
        self.user_made_change = False

        self.hamburger_button = QPushButton("☰")
        self.hamburger_button.setStyleSheet("background-color: #333; color: #eee; width: 24px; height: 24px;")
        self.hamburger_button.setContentsMargins(0, 0, 0, 0)
        self.hamburger_button.clicked.connect(self.show_hamburger_menu)
        self.setCornerWidget(self.hamburger_button)

        self.tabBar().setTabButton(0, QTabBar.RightSide, self.hamburger_button)

    def create_tab(self, url=""):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        web_engine_view = QWebEngineView()
        web_engine_page = QWebEnginePage()
        web_engine_view.setPage(web_engine_page)
        layout.addWidget(web_engine_view)

        url_bar = QLineEdit()
        plus_button = QPushButton("+")
        url_bar.setStyleSheet("color: white;")
        plus_button.setStyleSheet("background-color: #333; color: #eee;")
        plus_button.clicked.connect(self.create_tab)

        url_layout = QHBoxLayout()
        url_layout.addWidget(url_bar)
        url_layout.addWidget(plus_button)

        web_engine_page.urlChanged.connect(lambda url: self.handle_url_change(url, url_bar))

        layout.addLayout(url_layout)

        self.addTab(tab, "Untitled")
        self.setCurrentWidget(tab)

        web_engine_page.titleChanged.connect(lambda title: self.setTabText(self.currentIndex(), title or "Untitled"))
        web_engine_page.urlChanged.connect(lambda url: self.handle_url_change(url, url_bar))
        url_bar.returnPressed.connect(lambda: self.handle_search(url_bar, web_engine_page))

        url_bar.setStyleSheet("color: white; background-color: #333;")
        url_bar.setFixedHeight(24)

        self.setStyleSheet("QTabBar::tab { color: black; }")

        if not url:
            def get_random_nature_image():
                load_dotenv()
                access_key = os.getenv("UNSPLASH_ACCESS_KEY")
                response = requests.get(f"https://api.unsplash.com/photos/random?query=nature&client_id={access_key}")
                data = response.json()
                image_url = data['urls']['full']
                return image_url

            html = (f"""
            <html>
            <head>
            <title>Untitled</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300&display=swap" rel="stylesheet">
            </head>
            <body style='background: #333; color: #eee;'>
            <img src='{get_random_nature_image()}' style='height: 100%; width: 100%;' alt='Image could not be loaded.'>
            <h1 style='font-weight: 200; -webkit-text-stroke: 0.5px black; color: white; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; font-family: Roboto; position: absolute; top: 5%; left: 5%; transform: translate(-5%, -5%);'>Welcome to Pytser <br> Use the url bar to search </h1>
            </body>
            </html>
            """)

            web_engine_page.setHtml(html)

    def show_hamburger_menu(self):
        hamburger_menu = QMenu(self)

        browsing_history_action = QAction("Browsing History", self)
        browsing_history_action.triggered.connect(self.browser_window.show_history)
        hamburger_menu.addAction(browsing_history_action)

        download_history_action = QAction("Download History", self)
        download_history_action.triggered.connect(self.browser_window.show_download_history)
        hamburger_menu.addAction(download_history_action)

        hamburger_menu.exec_(QCursor.pos())

    def emit_tab_close_request(self, index):
        self.tabCloseRequestedCustom.emit(index)

    def handle_url_change(self, url, url_bar):
        url_string = url.toString()
        if url_string.startswith("data:text/html"):
            url_bar.clear()
        else:
            if not self.browser_window.history or self.browser_window.history[-1] != url_string:
                self.browser_window.history.append(url_string)
                self.browser_window.save_history()
            url_bar.setText(url_string)
            url_bar.setCursorPosition(0)
        self.user_made_change = False

    def handle_search(self, url_bar, web_engine_page):
        text = url_bar.text()
        if text:
            self.user_made_change = True
            formatted_url = QUrl.fromUserInput(text)
            if formatted_url.isValid() and "." in text:
                web_engine_page.load(formatted_url)
            else:
                search_query = text.strip()
                url = f"https://www.google.com/search?q={'+'.join(search_query.split())}"
                web_engine_page.load(QUrl(url))


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pytser")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #222; color: #eee;")
        self.setWindowIcon(QIcon('icon.ico'))
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        font = QFont("Roboto", 11)
        QApplication.setFont(font)

        self.tab_widget = CloseableTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        self.tab_widget.create_tab()
        self.tab_widget.tabCloseRequestedCustom.connect(self.close_tab)

        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.handle_download)

        self.history = []
        self.download_history = []
        self.load_history()

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()

    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            original_url = download.url().toString()
            parsed_url = urlparse(original_url)
            file_extension = os.path.splitext(parsed_url.path)[1]
            path += file_extension
            download.setPath(path)
            download.accept()
            self.download_history.append(path)
        self.save_download_history()

    def closeEvent(self, event):
        self.save_history()
        event.accept()

    def save_history(self):
        directory = os.path.expanduser('~\\AppData\\Roaming\\htaamas\\browser')
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, 'history.json'), 'w') as f:
            json.dump(self.history, f)

    def load_history(self):
        directory = os.path.expanduser('~\\AppData\\Roaming\\htaamas\\browser')
        os.makedirs(directory, exist_ok=True)

        try:
            with open(os.path.join(directory, 'history.json'), 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = []

        try:
            with open(os.path.join(directory, 'download_history.json'), 'r') as f:
                self.download_history = json.load(f)
        except FileNotFoundError:
            self.download_history = []

    def show_download_history(self):
        self.download_history_window = DownloadHistoryWindow(self.download_history, self)
        self.download_history_window.show()

    def show_history(self):
        self.history_window = HistoryWindow(self.history, self)
        self.history_window.show()

    def save_download_history(self):
        directory = os.path.expanduser('~\\AppData\\Roaming\\htaamas\\browser')
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, 'download_history.json'), 'w') as f:
            json.dump(self.download_history, f)

    def open_history_window(self):
        self.history_window = HistoryWindow(self.history, self)
        self.history_window.show()


if __name__ == "__main__":
    app = QApplication([])
    window = BrowserWindow()
    window.show()
    app.exec_()
