# -*- coding: utf-8 -*-

u"""
Container.py

:Author:
    oki yoshihiro
    okiyoshihiro.job@gmail.com
:Version: -2.0-
:Date: 2024/02/09

.. note:: 当コード記述時の環境

    - Maya2022 python3系
    - Python version: 3.7.7
    - PySide2 version: 5.15.2

概要(overview):
    Simple collapsible widget for PySide2, made to mimic Maya's na-tive GUI'
        - 通称: コンテナー(Container)
        - 型: Union[QWidget, TypeOfSubclass]
            QWidgetクラス または、 その派生クラス(サブクラス) という意味です
詳細(details):
    mayaで言う、frameLayout に相当する ウィジェットが、PySide2 には存在しません。
        折りたためるUIです。
    そこで、PySide2で似たようなUIを作成する、独自モジュールが公開されていました。
        https://github.com/aronamao/PySide2-Collapsible-Widget
    当方でアレンジも加えていますが、追加要素があることの方が重要です。
        不足要素を補っています。
使用法(usage):
    ::

        # ローカルで作成したモジュール
        import Container
        reload(Container)
        from Container import Container, Header

        # 以下 e.g.):
        ############################################################
        layout = QtWidgets.QVBoxLayout()
        container = Container("Group")
        layout.addWidget(container)

        content_layout = QtWidgets.QGridLayout(container.contentWidget)
        content_layout.addWidget(QtWidgets.QPushButton("Button"))
        ##############################

        # or

        ############################################################
        layout = QtWidgets.QVBoxLayout()
        container = Container("Group")

        content_layout = QtWidgets.QGridLayout(container.contentWidget)
        content_layout.addWidget(QtWidgets.QPushButton("Button"))

        layout.addWidget(container)
        ##############################

-リマインダ-
    done: 2024/02/09
        - 追加箇所1(+)・変換箇所1(-/+)
            - 概要: 当モジュールの読み込み先での、シグナル と スロット 接続の実現の為
            - 詳細:
                ::

                    +   class ClickableWidget(QWidget):  # クリック信号を出すウィジェットを定義
                            ...

                    -   widget = QWidget()
                    +   self.widget = ClickableWidget()  # クリック信号を出すウィジェットへ変更と、コンストラクタ化

                    +   @property
                        def headerWidget(self):  # headerWidget プロパティを準備し、容易なアクセスを可にする
                            ...

                    -   header = Header(name, self._content_widget)
                    +   self.header = Header(name, self._content_widget)  # コンストラクタ化

                    +   @property
                        def contentHeader(self):  # container header プロパティを準備し、容易なアクセスを可にする
                            ...

        version = '-2.0-'
    done: 2024/01/29
        新規作成

        version = '-1.0-'
"""

from PySide2.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                               QLabel, QSpacerItem, QSizePolicy, QStackedLayout,
                               QGridLayout
                               )
from PySide2.QtGui import QPixmap, QFont
from PySide2.QtCore import QObject, Signal


# 追加箇所1
class ClickableWidget(QWidget):  # クリック信号を出すウィジェットを定義
    # カスタムシグナルの定義
    clicked = Signal()

    def __init__(self):
        super().__init__()

    def mouseReleaseEvent(self, event):
        # マウスがリリースされたときに発動する処理
        self.clicked.emit()


class Header(QWidget):
    """Header class for a collapsible group"""

    def __init__(self, name, content_widget):
        """Header Class Constructor to initialize the object.

        Args:
            name (str): Name for the header
            content_widget (QWidget): Widget containing child elements
        """
        super(Header, self).__init__()
        self.content = content_widget
        self.expand_ico = QPixmap(":teDownArrow.png")
        self.collapse_ico = QPixmap(":teRightArrow.png")
        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Fixed
                           )

        # print('execute, Header')

        stacked = QStackedLayout(self)
        stacked.setStackingMode(QStackedLayout.StackAll)
        background = QLabel()
        background.setStyleSheet(
            "QLabel{ background-color: rgb(93, 93, 93); border-radius:2px}"
            )

        self.widget = ClickableWidget()  # 変換箇所1: クリック信号を出すウィジェットへ変更と、コンストラクタ化
        layout = QHBoxLayout(self.widget)

        self.icon = QLabel()
        self.icon.setPixmap(self.expand_ico)
        layout.addWidget(self.icon)
        layout.setContentsMargins(11, 0, 11, 0)

        font = QFont()
        font.setBold(True)
        label = QLabel(name)
        label.setFont(font)

        layout.addWidget(label)
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding,
                        QSizePolicy.Expanding
                        )
            )

        stacked.addWidget(self.widget)
        stacked.addWidget(background)
        background.setMinimumHeight(layout.sizeHint().height() * 1.5)

        # testで追加 ################################ start
        self.content_ = None
        self.toggle_ = None
        self.height_ = None
        # testで追加 ################################ end
        # print(self.content)

    def mousePressEvent(self, *args):  # ボタンをクリックした時に、発動させたい
        """Handle mouse events, call the function to toggle groups"""
        # self.expand() if not self.content.isVisible() else self.collapse()
        if not self.content.isVisible():
            self.expand()
        else:
            self.collapse()
        # self.content.isVisible()  # : True -expand-
        #                           # : False -collapse-
        # return self.content_, self.toggle_, self.height_
        # self.outPut_content_status()
        # print(type(self.height_))
        # print(self.outPut_content_status())
        # print(self.height_)

    def expand(self):
        self.content.setVisible(True)
        self.icon.setPixmap(self.expand_ico)
        # testで追加 ################################ start
        height = self.content.geometry().getRect()[3]
        self.height_ = height
        self.content_ = self.content
        self.toggle_ = self.content.isVisible()
        # testで追加 ################################ end

    def collapse(self):
        self.content.setVisible(False)
        self.icon.setPixmap(self.collapse_ico)
        # testで追加 ################################ start
        self.height_ = 0
        self.content_ = self.content
        self.toggle_ = self.content.isVisible()
        # testで追加 ################################ end

    # 追加箇所1
    @property
    def headerWidget(self):  # headerWidget プロパティを準備し、容易なアクセスを可にする
        """Getter for the header widget

        Returns: widget header
        """
        return self.widget


class Container(QWidget):
    """Class for creating a collapsible group similar to how it is implement in Maya

        Examples:
            Simple example of how to add a Container to a QVBoxLayout and attach a QGridLayout

            >>> layout = QVBoxLayout()
            >>> container = Container("Group")
            >>> layout.addWidget(container)
            >>> content_layout = QGridLayout(container.contentWidget)
            >>> content_layout.addWidget(QPushButton("Button"))
    """

    def __init__(self, name, color_background = False):
        """Container Class Constructor to initialize the object

        Args:
            name (str): Name for the header
            color_background (bool): whether or not to color the background lighter like in maya
        """
        super(Container, self).__init__()

        # print('execute, Container')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._content_widget = QWidget()
        if color_background:
            self._content_widget.setStyleSheet(
                "QWidget{background-color: rgb(73, 73, 73); "
                "margin-left: 2px; margin-right: 2px}"
                )
        self.header = Header(name, self._content_widget)  # 変換箇所1
        layout.addWidget(self.header)
        layout.addWidget(self._content_widget)

        # assign self.header methods to instance attributes so they can be called outside of this class
        # ヘッダー メソッドをインスタンス属性に割り当てて、このクラスの外部でヘッダー メソッドを呼び出せるようにします。
        self.collapse = self.header.collapse
        self.expand = self.header.expand
        self.toggle = self.header.mousePressEvent

        # # testで追加 ################################ start
        # self.outPut_content_status = self.header.outPut_content_status
        # # testで追加 ################################ end

    @property
    def contentWidget(self):
        """Getter for the content widget

        Returns: Content widget
        """
        # print('execute, contentWidget')
        return self._content_widget

    # 追加箇所1
    @property
    def contentHeader(self):  # container header プロパティを準備し、容易なアクセスを可にする
        """Getter for the content header

        Returns: Content header
        """
        return self.header

    # @property
    # def outPut_container_height(self):
    #     return self._content_widget.height()
