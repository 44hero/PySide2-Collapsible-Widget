# https://github.com/aronamao/PySide2-Collapsible-Widget
# Container
# Containerのcollapse/expandによるウィンドウの動的サイズ変更
####################################################
# #######################################################################
# 標準ライブラリ
from importlib import reload
from functools import partial

# サードパーティライブラリ
from PySide2.QtWidgets import (QGridLayout, QMainWindow, QPushButton, QSizePolicy,
                               QSpacerItem, QVBoxLayout, QWidget
                               )
from PySide2.QtCore import QTimer, Qt
from maya import OpenMayaUI
from shiboken2 import wrapInstance

# ローカルで作成したモジュール
import Container
reload(Container)
from Container import Container, Header
# ########################################################################


def maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QMainWindow)


class Test(QMainWindow):
    def __init__(self, parent = maya_main_window(), *args, **kwargs):
        super(Test, self).__init__(parent, *args, **kwargs)

        self.title = 'Test'
        self.win = self.title + '_ui'
        self.size: Tuple[int] = (500, 300, 210, 270)  # x, y, width, height

        self.bgc = "background-color:gray; color: white"

        # 作成された コンテナウィジェット の高さを辞書登録
        self.container_heights = {}

    def _makeMayaStandaloneWindow(self):
        self.setWindowTitle(self.title)  # <- window の title名 設定
        if not self.isVisible():
            self.setGeometry(*self.size)  # 完全に新規にUI作成したときの初期値。アンパック(*)は重要

        child_list = self.parent().children()
        for c in child_list:
            # 自分と同じ名前のUIのクラスオブジェクトが存在してたらCloseする
            if self.__class__.__name__ == c.__class__.__name__:
                c.close()

        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        self.setObjectName(self.win)  # <- objectName 設定
        # ポジションとサイズ の保存と復元機能 を有効にする
        self.setProperty("saveWindowPref", True
                         )  # set window name, and save to windowPrefs ####################### end

    # UIの起動 関数
    def createUI(self):
        self._makeMayaStandaloneWindow()  # 当該window の設定をいっぺんに行う 関数

        # 1):###############################################################################
        # 概要: メインウィンドウ の中央に配置される セントラルウィジェット です
        # 1): QWidget -Widget- ############################################## -Widget- start
        self.central_wid = QWidget(self)  # セントラルウィジェット
        self.setCentralWidget(self.central_wid)  # 中央に配置
        # 1): QWidget -Widget- ############################################## -Widget- end
        # 1):###############################################################################

        # 2):###############################################################################
        # 概要: セントラルウィジェット 内の メインレイアウト です
        # 2): QVBoxLayout -Layout- ########################################## -Layout- start
        self.main_vbxLay = QVBoxLayout()  # メインレイアウト
        self.central_wid.setLayout(self.main_vbxLay)  # メインレイアウト
        # 2): QVBoxLayout -Layout- ########################################## -Layout- end
        # 2):###############################################################################

        # 3):###############################################################################
        # 概要: メインレイアウト 内には、コンテナ群まとめ が縦に配置されます
        # 3.1): コンテナ群まとめレイアウト -Layout- ################################# -Layout- start
        # セントラルウィジェット 内に 水平レイアウト(コンテナ群まとめ用)
        # を 直接 作成 追加 ###################################### 一遍に行えます
        self.contAll_vbxLay = QVBoxLayout()  # レイアウト(コンテナ群まとめ用)
        self.central_wid.setLayout(self.contAll_vbxLay)

        # ######################################################################################
        # ウィジェット(コンテナA用)
        # を作成 ###################################### 作成しただけでは表示されません -Widget-
        self.contA_wid = Container("GroupA")  # ウィジェット(コンテナA用)
        # シグナルとスロットを接続
        contA_headerWid = self.contA_wid.contentHeader.headerWidget
        contA_headerWid.clicked.connect(partial(self.cal_alwaysHeight_containerAll
                                                , self.contA_wid
                                                )
                                        )
        # Save the initial height of the self.contA_wid
        # self.container_heights[self.contA_wid] = self.contA_wid.geometry().height()
        # 縦のレイアウト(コンテナA用)
        # を作成 ###################################### 作成しただけでは表示されません -Layout-
        self.contentA_gLay = QGridLayout(self.contA_wid.contentWidget
                                         )  # default: QGridLayout

        # # ウィジェット(プッシュボタンA用) を レイアウト(コンテナA用)
        # # を 直接 作成 追加 ###################################### 一遍に行っています
        self.btnA_pbtnWid = QPushButton('ButtonA')  # 1
        # print(type(self.btnA_pbtnWid))
        self.contentA_gLay.addWidget(self.btnA_pbtnWid, 0, 0)  # 2
        # self.contentA_gLay.addWidget(QPushButton("ButtonA"), 0, 0)  # 1, 2 を ワイライナーで実行しています

        # # ウィジェット(プッシュボタンB用) を レイアウト(コンテナA用)
        # # を 直接 作成 追加 ###################################### 一遍に行っています
        self.btnB_pbtnWid = QPushButton('ButtonB')  # 1
        self.contentA_gLay.addWidget(self.btnB_pbtnWid, 0, 1)  # 2
        # self.contentA_gLay.addWidget(QPushButton("ButtonB"), 0, 1)  # 1, 2 を ワイライナーで実行しています

        # # ウィジェット(プッシュボタンC用) を レイアウト(コンテナA用)
        # # を 直接 作成 追加 ###################################### 一遍に行っています
        self.btnC_pbtnWid = QPushButton('ButtonC')  # 1
        self.contentA_gLay.addWidget(self.btnC_pbtnWid, 1, 0)  # 2
        # self.contentA_gLay.addWidget(QPushButton("ButtonC"), 1, 0)  # 1, 2 を ワイライナーで実行しています

        # ウィジェット(コンテナA用) を レイアウト(コンテナ群まとめ用)
        # に追加 ######################################
        self.contAll_vbxLay.addWidget(self.contA_wid)
        # ######################################################################################

        # ######################################################################################
        # ウィジェット(コンテナB用)
        # を作成 ###################################### 作成しただけでは表示されません -Widget-
        self.contB_wid = Container("GroupB")  # ウィジェット(コンテナA用)
        # シグナルとスロットを接続
        contB_headerWid = self.contB_wid.contentHeader.headerWidget
        contB_headerWid.clicked.connect(partial(self.cal_alwaysHeight_containerAll
                                                , self.contB_wid
                                                )
                                        )
        # Save the initial height of the self.contA_wid
        # self.container_heights[self.contB_wid] = self.contB_wid.geometry().height()
        # 縦のレイアウト(コンテナA用)
        # を作成 ###################################### 作成しただけでは表示されません -Layout-
        self.contentB_gLay = QGridLayout(self.contB_wid.contentWidget
                                         )  # default: QGridLayout

        # # ウィジェット(プッシュボタンB用) を レイアウト(コンテナB用)
        # # を 直接 作成 追加 ###################################### 一遍に行っています
        self.btnB_pbtnWid = QPushButton('ButtonB')  # 1
        self.contentB_gLay.addWidget(self.btnB_pbtnWid, 0, 0)  # 2
        # self.contentB_gLay.addWidget(QPushButton("ButtonB"), 0, 0)  # 1, 2 を ワイライナーで実行しています

        # ウィジェット(コンテナB用) を レイアウト(コンテナ群まとめ用)
        # に追加 ######################################
        self.contAll_vbxLay.addWidget(self.contB_wid)
        # ######################################################################################

        # 常に、*** のトップ に順番に配置されるようにするため、垂直スペーサーを追加して間隔を制御
        # レイアウト(コンテナ群まとめ用) を装飾
        # 設定を施す ###################################
        spacer = QSpacerItem(20, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.contAll_vbxLay.addItem(spacer)

        # レイアウト(コンテナ群まとめ用) を メインレイアウト
        # に追加 ###################################### 初めて表示されます     -表示-
        self.main_vbxLay.addLayout(self.contAll_vbxLay)
        # 3.1): コンテナ群まとめレイアウト -Layout- ################################# -Layout- end
        # 3):###############################################################################

        # container A Toggle ボタン のテスト
        btnD_pbtnWid = QPushButton('container A Toggle')
        # btnD_pbtnLay = QVBoxLayout(btnD_pbtnWid)
        # btnD_pbtnLay.addWidget(btnD_pbtnWid)
        self.contAll_vbxLay.addWidget(btnD_pbtnWid)
        btnD_pbtnWid.clicked.connect(self.contA_wid.toggle)

        self.show()

        # window の高さ編集をしてアップデートしてあげる
        self.cal_alwaysHeight_window()

        print(self.geometry())

        print(self.container_heights.values())

    def cal_alwaysHeight_window(self):
        # x, y, width, height: Tuple[int, int, int, int]
        # 初期： QMainWindow のサイズ
        start_size = list(self.geometry().getRect())  # タプルをリストに変換

        # 縦のみの合計サイズを抽出
        # Calculate the total height of all containers
        total_height = sum(self.container_heights.values())
        # Set the new height
        start_size[3] = total_height
        # アップデート： 全ての コンテナー が解放されている時、ぴったりと QMainWindow の最低限必要なサイズにフィットさせるサイズ
        upDate_size = tuple(start_size)  # リストをタプルに変換
        self.setGeometry(*upDate_size)

    def cal_alwaysHeight_containerAll(self, container_geo_name):
        # x, y, width, height: Tuple[int, int, int, int]

        # # check
        # # current： container_geo_name のサイズ
        # print(f'I am \n\t{container_geo_name}')
        # print(f'type is \n\t{type(container_geo_name)}')
        currentSize_frame_list = list(container_geo_name.geometry().getRect())  # タプルをリストに変換
        currentHeight_frame_ = currentSize_frame_list[3]
        # print(f'currentFrame_currentHeight: {currentHeight_frame_}')

        # Save the new height of the frame
        self.container_heights[container_geo_name] = currentHeight_frame_
        # print(self.container_heights)

        # Calculate the total height of all frames
        total_height = sum(self.container_heights.values())
        # print(f'total_height: {total_height}')

        # temp
        # Get the current width size of the window
        current_width = self.geometry().width()
        # Set the new height
        temp_height = total_height
        # Resize the window, keeping the current width and changing the height
        self.resize(current_width, temp_height)
        # temp_size = list(self.geometry().getRect())  # タプルをリストに変換
        # print(f'temp_size: {temp_size}')

        # final
        # 一旦フィットさせる。但し、全体的にフィットしてしまうので、ここで終わりにはしない！
        self.adjustSize()
        # Get the final height size of the window
        final_height = self.geometry().height()
        self.resize(current_width, final_height)
        # final_size = list(self.geometry().getRect())  # タプルをリストに変換
        # print(f'final_size: {final_size}')

    # Reload 実行 関数
    def editMenuReloadCmd(self, *args):
        u""" < Reload 実行 関数 です > """
        QTimer.singleShot(0, self.createUI)  # refresh UI <---- ここ重要!!


if __name__ == "__main__":
    test = Test()
    test.createUI()


# 0): QMainWindow
# |
# |-- 1): QWidget (self.central_wid) -Widget-
#   |
#   |-- 2): QVBoxLayout (self.main_vbxLay) -Layout-
#     |
#     |-- 3): QVBoxLayout (self.contAll_vbxLay) -Layout- (コンテナ群まとめレイアウト)
#       |
#       |-- #): Container (self.contA_wid) -Widget- (コンテナA用)
#         |
#         |-- #): QHBoxLayout (self.contentA_gLay) -Layout- (コンテナA用の水平レイアウト)
#           |
#           |-- #): QPushButton -Widget- (self.btnA_pbtnWid)
#           |
#           |-- #): QPushButton -Widget- (self.btnB_pbtnWid)
