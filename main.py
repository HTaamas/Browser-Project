import json
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtWidgets import QFileDialog, QMenu, QAction, QMenuBar, QTabBar
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


class CloseableTabWidget(QTabWidget):
    tabCloseRequestedCustom = pyqtSignal(int)

    def __init__(self, browser_window):
        super().__init__()
        self.browser_window = browser_window
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.emit_tab_close_request)
        self.user_made_change = False

        # Create hamburger menu button
        self.hamburger_button = QPushButton("☰")
        self.hamburger_button.setStyleSheet("background-color: #333; color: #eee; width: 24px; height: 24px;")
        # self.hamburger_button.setFixedSize(24, 24)
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

    def show_hamburger_menu(self):
        # Create context menu
        hamburger_menu = QMenu(self)

        # Create "Browsing History" action
        browsing_history_action = QAction("Browsing History", self)
        browsing_history_action.triggered.connect(self.browser_window.show_history)
        hamburger_menu.addAction(browsing_history_action)

        # Create "Download History" action
        download_history_action = QAction("Download History", self)
        download_history_action.triggered.connect(self.browser_window.show_download_history)
        hamburger_menu.addAction(download_history_action)

        # Show context menu
        hamburger_menu.exec_(QCursor.pos())

    def emit_tab_close_request(self, index):
        self.tabCloseRequestedCustom.emit(index)\


    def handle_url_change(self, url, url_bar):
        url_string = url.toString()
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
            # url_bar.setCursorPosition(0)


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Web Browser")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #222; color: #eee;")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        self.tab_widget = CloseableTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        self.tab_widget.create_tab()
        self.tab_widget.tabCloseRequestedCustom.connect(self.close_tab)

        # Set up download handler
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.handle_download)

        self.history = []
        self.download_history = []
        self.load_history()

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()

    def handle_download(self, download):
        # Prompt user to select download location
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            download.setPath(path)
            download.accept()
            self.download_history.append(path)

    def closeEvent(self, event):
        # Save history and download history when application is about to close
        self.save_history()
        event.accept()

    def save_history(self):
        # Save browsing history to a file
        with open('history.json', 'w') as f:
            json.dump(self.history, f)

        # Save download history to a file
        with open('download_history.json', 'w') as f:
            json.dump(self.download_history, f)

    def load_history(self):
        # Load browsing history from a file
        try:
            with open('history.json', 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            self.history = []

        # Load download history from a file
        try:
            with open('download_history.json', 'r') as f:
                self.download_history = json.load(f)
        except FileNotFoundError:
            self.download_history = []

    def show_history(self):
        # Display browsing history
        print("Browsing History:")
        for url in self.history:
            print(url)

    def show_download_history(self):
        # Display download history
        print("Download History:")
        for path in self.download_history:
            print(path)


if __name__ == "__main__":
    app = QApplication([])
    window = BrowserWindow()
    window.show()
    app.exec_()
