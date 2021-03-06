import yaml
from utils import safe_load
import re
import sys
import os
import requests
from download_source import download
from magnet import download_magnet
import http.server
import socketserver
from multiprocessing import Process
import time

from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtNetwork import *

import markdown
import utils
import asyncio
import jinja2

url = sys.argv[1]
index_metadata = None
user_metadata = None
exec_ret = None
g = None
current_file = None
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

PORT = 8083
DIRECTORY = url

def set_current_file(tabs):
    def handler(index):
        global current_file
        current_file = tabs._files[index]

    return handler

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def f(name):
    server_class = http.server.HTTPServer
    handler_class=Handler
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

def main():
    global url
    global index_metadata
    global user_metadata
    global g

    app = QApplication(sys.argv)
    g = QApplication.desktop().availableGeometry()
    win = Window()
    QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
    sys.exit(app.exec_())

    # with open('downloads/test.py', 'w') as a_writer:
    #    a_writer.write(r.text)

    # os.system("python downloads/test.py")

class Window(QMainWindow):

    def createMenuBar(self):
        global user_metadata

        def edit():
            global current_file
            global user_metadata
            os.system(user_metadata["editor"] + " " + "server/" +  current_file + " &")

        def refresh():
            global url
            global index_metadata
            global user_metadata
            global g
            global set_current_file

            r = requests.get(url + "/index.yaml")
            index_metadata = safe_load(r.text)
            with open("user_metadata.yaml", 'r') as reader:
                user_metadata = safe_load(reader.read())
            r = requests.get(url + "/" + index_metadata["root"])
            root = r.text
            nodes = safe_load(root)["nodes"]
            tabs = QTabWidget()
            tabs.tabBarClicked.connect(set_current_file(tabs))
            tabs._files = [index_metadata["root"]]
            self.tabs = tabs

            self.index = Content(nodes, container=self.tabs)
            tabs.insertTab(0, self.index, index_metadata["root"])
            tabs.setCurrentIndex(0)
            self.setCentralWidget(tabs)

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        debugMenu = QMenu("&Controls", self)
        menuBar.addMenu(debugMenu)

        self.refreshAction = QAction(self)
        self.refreshAction.setText("&Refresh")
        debugMenu.addAction(self.refreshAction)
        self.refreshAction.triggered.connect(refresh)

        self.editAction = QAction(self)
        self.editAction.setText("&Edit")
        debugMenu.addAction(self.editAction)
        self.editAction.triggered.connect(edit)

        def custom_action(cmd):
            def handler():
                os.system(cmd["script"] + " " + current_file + " " + url)

            return handler

        for elem in user_metadata["menu"]:
            exec("""
self.%sAction = QAction(self)
self.%sAction.setText("&%s")
debugMenu.addAction(self.%sAction)
self.%sAction.triggered.connect(custom_action(%s))
            """ % (
                elem["name"], 
                elem["name"],
                elem["name"],
                elem["name"],
                elem["name"],
                "elem"
                )
            , globals()
            , {
                "elem": elem,
                "self": self,
                "debugMenu": debugMenu,
                "custom_action": custom_action
              }
            )


        with open("user_metadata.yaml", 'r') as reader:
            user_metadata = safe_load(reader.read())


    def load_page(self):
        url = self.web_address.text()
        global index_metadata
        global user_metadata
        global g
        global set_current_file

        r = requests.get(url + "/" + "index.yaml")
        index_metadata  = safe_load(r.text)

        with open("user_metadata.yaml", 'r') as reader:
            user_metadata = safe_load(reader.read())

        r = requests.get(url + "/" + index_metadata["root"])
        root = r.text
        nodes = safe_load(root)["nodes"]

        tabs = QTabWidget()
        tabs.tabBarClicked.connect(set_current_file(tabs))
        tabs._files = [index_metadata["root"]]
        self.tabs = tabs

        self.index = Content(nodes, container=self.tabs)
        tabs.insertTab(0, self.index, index_metadata["root"])
        tabs.setCurrentIndex(0)
        self.setCentralWidget(tabs)


    def __init__(self, parent=None):
        global url
        global index_metadata
        global user_metadata
        global g
        global current_file
        super().__init__(parent)

        r = requests.get(url + "/index.yaml")
        index_metadata = safe_load(r.text)

        with open("user_metadata.yaml", 'r') as reader:
            user_metadata = safe_load(reader.read())

        r = requests.get(url + "/" + index_metadata["root"])
        root = r.text
        nodes = safe_load(root)["nodes"]

        self.browser_toolbar = QToolBar()
        self.addToolBar(self.browser_toolbar)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Loaded")
        self.web_address = QLineEdit()
        self.web_address.returnPressed.connect(self.load_page)
        self.browser_toolbar.addWidget(self.web_address)
        self.web_address.setText(url)

        self.setWindowTitle("Index")
        self.setGeometry(g.x(), g.y(), 1152, g.height())

        tabs = QTabWidget()
        # https://gist.github.com/espdev/4f1565b18497a42d317cdf2531b7ef05
        # https://doc.qt.io/qt-5.12/style-reference.html
        self.tabs = tabs
        tabs.tabBarClicked.connect(set_current_file(tabs))
        tabs._files = [index_metadata["root"]]
        current_file = index_metadata["root"]
        self.tabs = tabs

        self.index = Content(nodes, container=tabs, file=index_metadata["root"])
        tabs.insertTab(0, self.index, index_metadata["root"])
        tabs.setCurrentIndex(0)
        # self.setStyleSheet("background-color: whitesmoke;");
        self.setCentralWidget(tabs)
        self.createMenuBar()
        self.show()
class CustomWebEnginePage(QWebEnginePage):

    def __init__(self, parent, webview, box):

        def contentsSizeChanged(size):
            nonlocal webview
            nonlocal box

            # def cb(v):
            #   print("#1" + str(v))

            # self.runJavaScript("document.documentElement.scrollHeight;", cb)
            webview.resize(int(size.width()), int(size.height()))
            # webview.update()
            webview.updateGeometry()
            # box.update()

        super().__init__(parent)
        self.contentsSizeChanged.connect(contentsSizeChanged)

    def acceptNavigationRequest(self, url,  _type, isMainFrame):
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url,  _type, isMainFrame)


def create_webview(par, box):
    global g
    web = QWebEngineView()
    web.setStyleSheet("""QWebEngineView::pane {
    margin: 0px,0px,0px,0px;
    border: 0px;
    padding: 0px;
    }""")

    web.setSizeIncrement(QSizePolicy.Expanding, QSizePolicy.Expanding)
    web.setPage(CustomWebEnginePage(par, web, box))
    web.setMinimumWidth(960)
    web.setMaximumHeight(640)
    return web

class Content(QWidget):

    def __init__(self, nodes, container=None, file=None):
        super(Content, self).__init__()
        self.nodes = nodes
        self.file = file

        self.container = container

        self.box = QVBoxLayout()
        self.box.setSpacing(0)
        self.widget = QWidget()
        self.widget.setStyleSheet("""QWidget::pane {
        margin: 0px,0px,0px,0px;
        border: 0px;
        padding: 0px;
        }""")

        scroll = QScrollArea()
        self.widget.setLayout(self.box)

        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(False)

        self.main_box = QVBoxLayout()
        self.main_box.setSpacing(0)
        self.setLayout(self.main_box)
        self.main_box.addWidget(scroll)

        self.initUI(container)
        scroll.setWidget(self.widget)

        # Layout - main_box has scroll which has widget which has a box which has contents

    def initUI(self, container):
        # sectionMap = { }
        global url
        global index_metadata
        global user_metadata
        global loop
        global g
        global current_file
        global set_current_file

        def download_source(file):
            global url
            global user_metadata
            def handler():
                c = os.getcwd()
                os.chdir(user_metadata["downloads_folder"])
                download(url, file, user_metadata["downloads_folder"])
                os.chdir(c)

            return handler

        def button_click(node):
            def handler():
                async def send_async():
                    to_email = index_metadata["form_email"]
                    from_email = user_metadata["email"]
                    utils.send_mail(to_email, user_metadata["name"], from_email, user_metadata["smtp_host"], user_metadata["password"], node["label"], node["id"])

                loop.run_until_complete(send_async())

            return handler

        def goto_tab_section(file, section):
            nonlocal container
            # nonlocal sectionMap
            def handler():
                i = container.currentIndex()
                label = container.tabText(i)
                found_tab = False

                while 1:
                    if i < container.count():
                        if label == file:
                            found_tab = True
                            break
                        else:
                            i += 1
                            label = container.tabText(i)
                    else:
                        break

                container.setCurrentIndex(i)

                #container.currentWidget().layout().itemAt(0).widget().widget().layout().itemAt(0)
                # container.currentWidget().layout().itemAt(0).widget().ensureWidgetVisible(container.currentWidget().layout().itemAt(0).widget().children()[1])
                # print([file, sectionMap[section]])

            return handler

        for node in self.nodes:
            if node["type"] == "source-file":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                r = requests.get(url + "/" + node["file"])
                file_text = r.text
                html = render_code(node["lang"], file_text)
                web.setHtml(html)
                self.box.addWidget(web)
            if node["type"] == "code":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))

                exec(node["text"], globals(), {
                    "nodes": self.nodes
                })
                web.setHtml(exec_ret)
                self.box.addWidget(web)
            if node["type"] == "snippet":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                html = render_code(node["lang"], node["text"])
                web.setHtml(html)
                self.box.addWidget(web)
            if node["type"] == "html":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                web.setUrl(QUrl(url + "/"  + node["url"]))
                self.box.addWidget(web)
            if node["type"] == "url":
                web = create_webview(self, self.box)
                web.setUrl(QUrl(node["url"]))
                web.setMaximumHeight(node.get("height", 640))
                self.box.addWidget(web)
            if node["type"] == "youtube":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 480))
                web.setUrl(QUrl("https://www.youtube.com/watch?v=" + node["id"]))
                self.box.addWidget(web)
            if node["type"] == "image":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                html = """<img src='""" + node["file"] + "'/>"
                web.setHtml(html)
                self.box.addWidget(web)
            if node["type"] == "literate":
                r = requests.get(url + "/" + node["file"])
                root = r.text
                lnodes = safe_load(root)["tangle"]

                for key, lnode in lnodes.items():
                    if lnode.get("from", None):
                        r = requests.get(url + "/" + lnode["from"]["file"])
                        root = r.text
                        nodes_recurse = safe_load(root)["tangle"]

                        lnodes[key]["text"] = nodes_recurse[key]["text"]

                md_section = []
                for key, lnode in lnodes.items():
                    if lnode.get("doc", None):
                        md_section.append(lnode["doc"])
                    if lnode.get("text", None):
                        md_section.append("```" + lnode.get("lang", "python") + "\n" + lnode["text"] + "\n" + "```")

                html = render_md(md_section)
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                web.setHtml(html)
                button = QPushButton("Download Source")
                button.setMaximumWidth(200)

                button.released.connect(download_source(node["file"]))
                self.box.addWidget(button)
                self.box.addWidget(web)
            if node["type"] == "md":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                html = render_md(node["text"])
                web.setHtml(html)
                self.box.addWidget(web)
            if node["type"] == "button":
                button = QPushButton(node["button"]["label"])
                button.setMaximumWidth(200)

                button.released.connect(button_click(node["button"]))
                self.box.addWidget(button)
            if node["type"] == "link":
                r = requests.get(url + "/" + node["link"]["file"])
                root = r.text
                nodes_recurse = safe_load(root)["nodes"]

                has_more = False
                for n in  nodes_recurse:
                    if n["type"] == "transclusion" or n["type"] == "link" :
                        has_more = True
                        break
                if has_more:
                    nested_container = QTabWidget()
                    nested_container.tabBarClicked.connect(set_current_file(nested_container))
                    nested_container._files = [node["link"]["file"]]
                    container._files.append(node["link"]["file"])
                    container.addTab(nested_container, node["link"]["file"])
                    web.__link =  nested_container
                    nested_container.insertTab(0, Content(nodes_recurse, container=nested_container), "Content")
                    nested_container.setCurrentIndex(0)
                else:
                    web.__link =  Content(nodes_recurse, container=container)
                    container.addTab(web.__link, node["link"]["file"])
                    container._files.append(node["link"]["file"])
            if node["type"] == "transclusion":
                web = create_webview(self, self.box)

                r = requests.get(url + "/" + node["transclusion"]["file"])
                root = r.text
                nodes_recurse = safe_load(root)["nodes"]


                has_more = False
                for n in  nodes_recurse:
                    if n["type"] == "transclusion" or n["type"] == "link" :
                        has_more = True
                        break

                transcluded_section = None
                for n in  nodes_recurse:
                    if n.get("section") == node["transclusion"]["section"]:
                        transcluded_section = n

                if transcluded_section:
                    html = render_md([transcluded_section["text"], node["transclusion"]["comment"]])
                    web.setHtml(html)
                    self.box.addWidget(web)
                    button = QPushButton("GOTO LINK")
                    web.setMinimumHeight(transcluded_section.get("height", 480))
                    button.released.connect(goto_tab_section(node["transclusion"]["file"], transcluded_section["section"]))
                    self.box.addWidget(button)
                    self.box.addWidget(web)
                    # sectionMap[transcluded_section["section"]] = web
                    button.setMaximumWidth(200)

                if has_more:
                    nested_container = QTabWidget()
                    nested_container.tabBarClicked.connect(set_current_file(nested_container))
                    nested_container._files = [node["transclusion"]["file"]]
                    container._files.append(node["transclusion"]["file"])
                    container.addTab(nested_container, node["transclusion"]["file"])
                    web.__link =  nested_container
                    nested_container.insertTab(0, Content(nodes_recurse, container=nested_container), "Content")
                    nested_container.setCurrentIndex(0)
                else:
                    web.__link =  Content(nodes_recurse, container=container)
                    container.addTab(web.__link, node["transclusion"]["file"])
                    container._files.append(node["transclusion"]["file"])
            if node["type"] == "text":
                web = create_webview(self, self.box)
                web.setMaximumHeight(node.get("height", 640))
                web.setHtml(node["text"])
                self.box.addWidget(web)

def render_md(text):
    output = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
        </head>
        <style>
body .octicon {
  display: inline-block;
  fill: currentColor;
  vertical-align: text-bottom;
}

body .anchor {
  float: left;
  line-height: 1;
  margin-left: -20px;
  padding-right: 4px;
}

body .anchor:focus {
  outline: none;
}

body h1 .octicon-link,
body h2 .octicon-link,
body h3 .octicon-link,
body h4 .octicon-link,
body h5 .octicon-link,
body h6 .octicon-link {
  color: #1b1f23;
  vertical-align: middle;
  visibility: hidden;
}

body h1:hover .anchor,
body h2:hover .anchor,
body h3:hover .anchor,
body h4:hover .anchor,
body h5:hover .anchor,
body h6:hover .anchor {
  text-decoration: none;
}

body h1:hover .anchor .octicon-link,
body h2:hover .anchor .octicon-link,
body h3:hover .anchor .octicon-link,
body h4:hover .anchor .octicon-link,
body h5:hover .anchor .octicon-link,
body h6:hover .anchor .octicon-link {
  visibility: visible;
}

body h1:hover .anchor .octicon-link:before,
body h2:hover .anchor .octicon-link:before,
body h3:hover .anchor .octicon-link:before,
body h4:hover .anchor .octicon-link:before,
body h5:hover .anchor .octicon-link:before,
body h6:hover .anchor .octicon-link:before {
  width: 16px;
  height: 16px;
  content: ' ';
  display: inline-block;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' version='1.1' width='16' height='16' aria-hidden='true'%3E%3Cpath fill-rule='evenodd' d='M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z'%3E%3C/path%3E%3C/svg%3E");
}body {
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  line-height: 1.5;
  color: #24292e;
  font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji;
  font-size: 16px;
  line-height: 1.5;
  word-wrap: break-word;
}

body details {
  display: block;
}

body summary {
  display: list-item;
}

body a {
  background-color: initial;
}

body a:active,
body a:hover {
  outline-width: 0;
}

body strong {
  font-weight: inherit;
  font-weight: bolder;
}

body h1 {
  font-size: 2em;
  margin: .67em 0;
}

body img {
  border-style: none;
}

body code,
body kbd,
body pre {
  font-family: monospace,monospace;
  font-size: 1em;
}

body hr {
  box-sizing: initial;
  height: 0;
  overflow: visible;
}

body input {
  font: inherit;
  margin: 0;
}

body input {
  overflow: visible;
}

body [type=checkbox] {
  box-sizing: border-box;
  padding: 0;
}

body * {
  box-sizing: border-box;
}

body input {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

body a {
  color: #0366d6;
  text-decoration: none;
}

body a:hover {
  text-decoration: underline;
}

body strong {
  font-weight: 600;
}

body hr {
  height: 0;
  margin: 15px 0;
  overflow: hidden;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #dfe2e5;
}

body hr:after,
body hr:before {
  display: table;
  content: "";
}

body hr:after {
  clear: both;
}

body table {
  border-spacing: 0;
  border-collapse: collapse;
}

body td,
body th {
  padding: 0;
}

body details summary {
  cursor: pointer;
}

body kbd {
  display: inline-block;
  padding: 3px 5px;
  font: 11px SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  line-height: 10px;
  color: #444d56;
  vertical-align: middle;
  background-color: #fafbfc;
  border: 1px solid #d1d5da;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #d1d5da;
}

body h1,
body h2,
body h3,
body h4,
body h5,
body h6 {
  margin-top: 0;
  margin-bottom: 0;
}

body h1 {
  font-size: 32px;
}

body h1,
body h2 {
  font-weight: 600;
}

body h2 {
  font-size: 24px;
}

body h3 {
  font-size: 20px;
}

body h3,
body h4 {
  font-weight: 600;
}

body h4 {
  font-size: 16px;
}

body h5 {
  font-size: 14px;
}

body h5,
body h6 {
  font-weight: 600;
}

body h6 {
  font-size: 12px;
}

body p {
  margin-top: 0;
  margin-bottom: 10px;
}

body blockquote {
  margin: 0;
}

body ol,
body ul {
  padding-left: 0;
  margin-top: 0;
  margin-bottom: 0;
}

body ol ol,
body ul ol {
  list-style-type: lower-roman;
}

body ol ol ol,
body ol ul ol,
body ul ol ol,
body ul ul ol {
  list-style-type: lower-alpha;
}

body dd {
  margin-left: 0;
}

body code,
body pre {
  font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  font-size: 12px;
}

body pre {
  margin-top: 0;
  margin-bottom: 0;
}

body input::-webkit-inner-spin-button,
body input::-webkit-outer-spin-button {
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
}

body :checked+.radio-label {
  position: relative;
  z-index: 1;
  border-color: #0366d6;
}

body .border {
  border: 1px solid #e1e4e8!important;
}

body .border-0 {
  border: 0!important;
}

body .border-bottom {
  border-bottom: 1px solid #e1e4e8!important;
}

body .rounded-1 {
  border-radius: 3px!important;
}

body .bg-white {
  background-color: #fff!important;
}

body .bg-gray-light {
  background-color: #fafbfc!important;
}

body .text-gray-light {
  color: #6a737d!important;
}

body .mb-0 {
  margin-bottom: 0!important;
}

body .my-2 {
  margin-top: 8px!important;
  margin-bottom: 8px!important;
}

body .pl-0 {
  padding-left: 0!important;
}

body .py-0 {
  padding-top: 0!important;
  padding-bottom: 0!important;
}

body .pl-1 {
  padding-left: 4px!important;
}

body .pl-2 {
  padding-left: 8px!important;
}

body .py-2 {
  padding-top: 8px!important;
  padding-bottom: 8px!important;
}

body .pl-3,
body .px-3 {
  padding-left: 16px!important;
}

body .px-3 {
  padding-right: 16px!important;
}

body .pl-4 {
  padding-left: 24px!important;
}

body .pl-5 {
  padding-left: 32px!important;
}

body .pl-6 {
  padding-left: 40px!important;
}

body .f6 {
  font-size: 12px!important;
}

body .lh-condensed {
  line-height: 1.25!important;
}

body .text-bold {
  font-weight: 600!important;
}

body .pl-c {
  color: #6a737d;
}

body .pl-c1,
body .pl-s .pl-v {
  color: #005cc5;
}

body .pl-e,
body .pl-en {
  color: #6f42c1;
}

body .pl-s .pl-s1,
body .pl-smi {
  color: #24292e;
}

body .pl-ent {
  color: #22863a;
}

body .pl-k {
  color: #d73a49;
}

body .pl-pds,
body .pl-s,
body .pl-s .pl-pse .pl-s1,
body .pl-sr,
body .pl-sr .pl-cce,
body .pl-sr .pl-sra,
body .pl-sr .pl-sre {
  color: #032f62;
}

body .pl-smw,
body .pl-v {
  color: #e36209;
}

body .pl-bu {
  color: #b31d28;
}

body .pl-ii {
  color: #fafbfc;
  background-color: #b31d28;
}

body .pl-c2 {
  color: #fafbfc;
  background-color: #d73a49;
}

body .pl-c2:before {
  content: "^M";
}

body .pl-sr .pl-cce {
  font-weight: 700;
  color: #22863a;
}

body .pl-ml {
  color: #735c0f;
}

body .pl-mh,
body .pl-mh .pl-en,
body .pl-ms {
  font-weight: 700;
  color: #005cc5;
}

body .pl-mi {
  font-style: italic;
  color: #24292e;
}

body .pl-mb {
  font-weight: 700;
  color: #24292e;
}

body .pl-md {
  color: #b31d28;
  background-color: #ffeef0;
}

body .pl-mi1 {
  color: #22863a;
  background-color: #f0fff4;
}

body .pl-mc {
  color: #e36209;
  background-color: #ffebda;
}

body .pl-mi2 {
  color: #f6f8fa;
  background-color: #005cc5;
}

body .pl-mdr {
  font-weight: 700;
  color: #6f42c1;
}

body .pl-ba {
  color: #586069;
}

body .pl-sg {
  color: #959da5;
}

body .pl-corl {
  text-decoration: underline;
  color: #032f62;
}

body .mb-0 {
  margin-bottom: 0!important;
}

body .my-2 {
  margin-bottom: 8px!important;
}

body .my-2 {
  margin-top: 8px!important;
}

body .pl-0 {
  padding-left: 0!important;
}

body .py-0 {
  padding-top: 0!important;
  padding-bottom: 0!important;
}

body .pl-1 {
  padding-left: 4px!important;
}

body .pl-2 {
  padding-left: 8px!important;
}

body .py-2 {
  padding-top: 8px!important;
  padding-bottom: 8px!important;
}

body .pl-3 {
  padding-left: 16px!important;
}

body .pl-4 {
  padding-left: 24px!important;
}

body .pl-5 {
  padding-left: 32px!important;
}

body .pl-6 {
  padding-left: 40px!important;
}

body .pl-7 {
  padding-left: 48px!important;
}

body .pl-8 {
  padding-left: 64px!important;
}

body .pl-9 {
  padding-left: 80px!important;
}

body .pl-10 {
  padding-left: 96px!important;
}

body .pl-11 {
  padding-left: 112px!important;
}

body .pl-12 {
  padding-left: 128px!important;
}

body hr {
  border-bottom-color: #eee;
}

body kbd {
  display: inline-block;
  padding: 3px 5px;
  font: 11px SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  line-height: 10px;
  color: #444d56;
  vertical-align: middle;
  background-color: #fafbfc;
  border: 1px solid #d1d5da;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #d1d5da;
}

body:after,
body:before {
  display: table;
  content: "";
}

body:after {
  clear: both;
}

body>:first-child {
  margin-top: 0!important;
}

body>:last-child {
  margin-bottom: 0!important;
}

body a:not([href]) {
  color: inherit;
  text-decoration: none;
}

body blockquote,
body details,
body dl,
body ol,
body p,
body pre,
body table,
body ul {
  margin-top: 0;
  margin-bottom: 16px;
}

body hr {
  height: .25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}

body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: .25em solid #dfe2e5;
}

body blockquote>:first-child {
  margin-top: 0;
}

body blockquote>:last-child {
  margin-bottom: 0;
}

body h1,
body h2,
body h3,
body h4,
body h5,
body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

body h1 {
  font-size: 2em;
}

body h1,
body h2 {
  padding-bottom: .3em;
  border-bottom: 1px solid #eaecef;
}

body h2 {
  font-size: 1.5em;
}

body h3 {
  font-size: 1.25em;
}

body h4 {
  font-size: 1em;
}

body h5 {
  font-size: .875em;
}

body h6 {
  font-size: .85em;
  color: #6a737d;
}

body ol,
body ul {
  padding-left: 2em;
}

body ol ol,
body ol ul,
body ul ol,
body ul ul {
  margin-top: 0;
  margin-bottom: 0;
}

body li {
  word-wrap: break-all;
}

body li>p {
  margin-top: 16px;
}

body li+li {
  margin-top: .25em;
}

body dl {
  padding: 0;
}

body dl dt {
  padding: 0;
  margin-top: 16px;
  font-size: 1em;
  font-style: italic;
  font-weight: 600;
}

body dl dd {
  padding: 0 16px;
  margin-bottom: 16px;
}

body table {
  display: block;
  width: 100%;
  overflow: auto;
}

body table th {
  font-weight: 600;
}

body table td,
body table th {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

body img {
  max-width: 100%;
  box-sizing: initial;
  background-color: #fff;
}

body img[align=right] {
  padding-left: 20px;
}

body img[align=left] {
  padding-right: 20px;
}

body code {
  padding: .2em .4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,.05);
  border-radius: 3px;
}

body pre {
  word-wrap: normal;
}

body pre>code {
  padding: 0;
  margin: 0;
  font-size: 100%;
  word-break: normal;
  white-space: pre;
  background: transparent;
  border: 0;
}

body .highlight {
  margin-bottom: 16px;
}

body .highlight pre {
  margin-bottom: 0;
  word-break: normal;
}

body .highlight pre,
body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}

body pre code {
  display: inline;
  max-width: auto;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: initial;
  border: 0;
}

body .commit-tease-sha {
  display: inline-block;
  font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  font-size: 90%;
  color: #444d56;
}

body .full-commit .btn-outline:not(:disabled):hover {
  color: #005cc5;
  border-color: #005cc5;
}

body .blob-wrapper {
  overflow-x: auto;
  overflow-y: hidden;
}

body .blob-wrapper-embedded {
  max-height: 240px;
  overflow-y: auto;
}

body .blob-num {
  width: 1%;
  min-width: 50px;
  padding-right: 10px;
  padding-left: 10px;
  font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  font-size: 12px;
  line-height: 20px;
  color: rgba(27,31,35,.3);
  text-align: right;
  white-space: nowrap;
  vertical-align: top;
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

body .blob-num:hover {
  color: rgba(27,31,35,.6);
}

body .blob-num:before {
  content: attr(data-line-number);
}

body .blob-code {
  position: relative;
  padding-right: 10px;
  padding-left: 10px;
  line-height: 20px;
  vertical-align: top;
}

body .blob-code-inner {
  overflow: visible;
  font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
  font-size: 12px;
  color: #24292e;
  word-wrap: normal;
  white-space: pre;
}

body .pl-token.active,
body .pl-token:hover {
  cursor: pointer;
  background: #ffea7f;
}

body .tab-size[data-tab-size="1"] {
  -moz-tab-size: 1;
  tab-size: 1;
}

body .tab-size[data-tab-size="2"] {
  -moz-tab-size: 2;
  tab-size: 2;
}

body .tab-size[data-tab-size="3"] {
  -moz-tab-size: 3;
  tab-size: 3;
}

body .tab-size[data-tab-size="4"] {
  -moz-tab-size: 4;
  tab-size: 4;
}

body .tab-size[data-tab-size="5"] {
  -moz-tab-size: 5;
  tab-size: 5;
}

body .tab-size[data-tab-size="6"] {
  -moz-tab-size: 6;
  tab-size: 6;
}

body .tab-size[data-tab-size="7"] {
  -moz-tab-size: 7;
  tab-size: 7;
}

body .tab-size[data-tab-size="8"] {
  -moz-tab-size: 8;
  tab-size: 8;
}

body .tab-size[data-tab-size="9"] {
  -moz-tab-size: 9;
  tab-size: 9;
}

body .tab-size[data-tab-size="10"] {
  -moz-tab-size: 10;
  tab-size: 10;
}

body .tab-size[data-tab-size="11"] {
  -moz-tab-size: 11;
  tab-size: 11;
}

body .tab-size[data-tab-size="12"] {
  -moz-tab-size: 12;
  tab-size: 12;
}

body .task-list-item {
  list-style-type: none;
}

body .task-list-item+.task-list-item {
  margin-top: 3px;
}

body .task-list-item input {
  margin: 0 .2em .25em -1.6em;
  vertical-align: middle;
}
        </style>
<body>
        """

    if isinstance(text, list):
        for t in text:
            html = markdown.markdown(t, extensions=[
                    "nl2br",
                    "md_in_html",
                    "fenced_code",
                    "tables",
                    "codehilite",
                    "mdx_linkify",
                    "markdown_checklist.extension"
                ])

            output += html
    else:
        html = markdown.markdown(text, extensions=[
                "nl2br",
                "md_in_html",
                "fenced_code",
                "tables",
                "codehilite",
                "mdx_linkify",
                "markdown_checklist.extension"
            ])

        output += html



    output += """</body>
</html>
"""
    return output


def render_code(lang, text):
    output = """<!DOCTYPE html>
        <html lang="en">

        <head>
            <meta charset="utf-8">
            <style type="text/css">
pre { line-height: 125%; }
td.linenos .normal { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
span.linenos { color: inherit; background-color: transparent; padding-left: 5px; padding-right: 5px; }
td.linenos .special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
span.linenos.special { color: #000000; background-color: #ffffc0; padding-left: 5px; padding-right: 5px; }
.codehilite .hll { background-color: #ffffcc }
.codehilite { background: #f8f8f8; }
.codehilite .c { color: #408080; font-style: italic } /* Comment */
.codehilite .err { border: 1px solid #FF0000 } /* Error */
.codehilite .k { color: #008000; font-weight: bold } /* Keyword */
.codehilite .o { color: #666666 } /* Operator */
.codehilite .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
.codehilite .cm { color: #408080; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #BC7A00 } /* Comment.Preproc */
.codehilite .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
.codehilite .c1 { color: #408080; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #408080; font-style: italic } /* Comment.Special */
.codehilite .gd { color: #A00000 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .gr { color: #FF0000 } /* Generic.Error */
.codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #00A000 } /* Generic.Inserted */
.codehilite .go { color: #888888 } /* Generic.Output */
.codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #0044DD } /* Generic.Traceback */
.codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #008000 } /* Keyword.Pseudo */
.codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #B00040 } /* Keyword.Type */
.codehilite .m { color: #666666 } /* Literal.Number */
.codehilite .s { color: #BA2121 } /* Literal.String */
.codehilite .na { color: #7D9029 } /* Name.Attribute */
.codehilite .nb { color: #008000 } /* Name.Builtin */
.codehilite .nc { color: #0000FF; font-weight: bold } /* Name.Class */
.codehilite .no { color: #880000 } /* Name.Constant */
.codehilite .nd { color: #AA22FF } /* Name.Decorator */
.codehilite .ni { color: #999999; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #0000FF } /* Name.Function */
.codehilite .nl { color: #A0A000 } /* Name.Label */
.codehilite .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #008000; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #19177C } /* Name.Variable */
.codehilite .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #bbbbbb } /* Text.Whitespace */
.codehilite .mb { color: #666666 } /* Literal.Number.Bin */
.codehilite .mf { color: #666666 } /* Literal.Number.Float */
.codehilite .mh { color: #666666 } /* Literal.Number.Hex */
.codehilite .mi { color: #666666 } /* Literal.Number.Integer */
.codehilite .mo { color: #666666 } /* Literal.Number.Oct */
.codehilite .sa { color: #BA2121 } /* Literal.String.Affix */
.codehilite .sb { color: #BA2121 } /* Literal.String.Backtick */
.codehilite .sc { color: #BA2121 } /* Literal.String.Char */
.codehilite .dl { color: #BA2121 } /* Literal.String.Delimiter */
.codehilite .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #BA2121 } /* Literal.String.Double */
.codehilite .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #BA2121 } /* Literal.String.Heredoc */
.codehilite .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
.codehilite .sx { color: #008000 } /* Literal.String.Other */
.codehilite .sr { color: #BB6688 } /* Literal.String.Regex */
.codehilite .s1 { color: #BA2121 } /* Literal.String.Single */
.codehilite .ss { color: #19177C } /* Literal.String.Symbol */
.codehilite .bp { color: #008000 } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #0000FF } /* Name.Function.Magic */
.codehilite .vc { color: #19177C } /* Name.Variable.Class */
.codehilite .vg { color: #19177C } /* Name.Variable.Global */
.codehilite .vi { color: #19177C } /* Name.Variable.Instance */
.codehilite .vm { color: #19177C } /* Name.Variable.Magic */
.codehilite .il { color: #666666 } /* Literal.Number.Integer.Long */
</style>
</head>
<body>
        """

    html = markdown.markdown("```" + lang + "\n" + text + "\n" + "```", extensions=[
            "nl2br",
            "md_in_html",
            "fenced_code",
            "tables",
            "codehilite",
            "mdx_linkify",
            "markdown_checklist.extension"
        ])

    output += html

    output += """</body>
</html>
"""
    return output
if __name__ == '__main__':
    if url.startswith("http"):
        main()
    else:
        url = "http://127.0.0.1:" + str(PORT)

        p = Process(target=f, args=('bob',))
        p.start()
        time.sleep(2)
        main()