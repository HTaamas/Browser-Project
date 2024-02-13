from PyQt5.QtCore import QUrl, pyqtSignal
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

        layout.addLayout(url_layout)

        self.addTab(tab, "Untitled")
        self.setCurrentWidget(tab)

        web_engine_page.titleChanged.connect(lambda title: self.setTabText(self.currentIndex(), title or "Untitled"))
        web_engine_page.urlChanged.connect(lambda url: self.handle_url_change(url, url_bar))
        url_bar.returnPressed.connect(lambda: self.handle_search(url_bar, web_engine_page))

        url_bar.setStyleSheet("color: white; background-color: #333;")
        url_bar.setFixedHeight(24)

        self.setStyleSheet("QTabBar::tab { color: black; }")

    def emit_tab_close_request(self, index):
        self.tabCloseRequestedCustom.emit(index)\


    def handle_url_change(self, url, url_bar):
        if not self.user_made_change:
            url_bar.setCursorPosition(0)
        url_bar.setText(url.toString())
        self.user_made_change = False

    def handle_search(self, url_bar, web_engine_page):
        text = url_bar.text()
        if text:
            self.user_made_change = True  # Add this line
            formatted_url = QUrl.fromUserInput(text)
            if formatted_url.isValid() and "." in text:
                web_engine_page.load(formatted_url)
            else:
                search_query = text.strip()
                url = f"https://www.google.com/search?q={'+'.join(search_query.split())}"
                web_engine_page.load(QUrl(url))
            url_bar.setCursorPosition(0)


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

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()


if __name__ == "__main__":
    app = QApplication([])
    window = BrowserWindow()
    window.show()
    app.exec_()
