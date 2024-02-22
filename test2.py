# -*- coding: utf-8 -*-

u"""
https://github.com/aronamao/PySide2-Collapsible-Widget

- Containerのcollapse/expandによるウィンドウの動的サイズ変更
- ウインドウの位置や大きさを保存する!!
####################################################
"""

# 標準ライブラリ
from importlib import reload
from functools import partial

# サードパーティライブラリ
from PySide2.QtWidgets import (QMainWindow, QWidget, QGridLayout,
                               QVBoxLayout, QPushButton, QApplication,
                               QComboBox, QSizePolicy, QSpacerItem
                               )
from PySide2.QtCore import Qt, QSettings
from maya import OpenMayaUI
from shiboken2 import wrapInstance

# ローカルで作成したモジュール
import Container
reload(Container)
from Container import Container


def maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QMainWindow)


# オリジナルメソッド
# メソッドの実行タイミングをプリントアウト出来るデコレーター用定義 関数
def check_domain(func):
    u""" < メソッドの実行タイミングをプリントアウト出来るデコレーター用定義 関数 です >

    オリジナルメソッド

    .. code::

        @check_domain
    を、実行メソッドのトップ行へ追加すると実現出来るようになります

    適宜、実行メソッドの実行タイミングを、
        プロンプト上にプリントアウト出来るようにする、
            デコレーター用の定義です
    """
    def wrapper(*args, **kwargs):
        print(f'\nstart --{func.__name__}')  # この時点から実行がスタートする、しるし
        result = func(*args, **kwargs)
        print(f"Function: {func.__name__}")  # 実行されるタイミングはここです！
        print(f'end --{func.__name__}\n')  # この時点で実行終わる、しるし
        return result
    return wrapper


class MainWindow(QMainWindow):
    u""" < *** です >

     .. note::
        従来の、
            UIのサイズを保存する、
                `windowPrefs.mel`
            Maya のさまざまな呼び出しに存在する変数を設定および照会できる、プリファレンスの一部である、
                maya独自規格｛optionVar」
        からの、代替え案である
            PySide2 規格 の .iniファイル
        を使用したやり方です。

    ::

        ファイルの保存先には、運用ルールが必要です。。。
        ここでは、「マイドキュメント/maya/versionNumber」に
            フォルダ「f'{prefix}_{commonName}'」を作り、
                設定ファイルが保存されていくようにしています。
        ファイル名はクラス変数にして、継承したクラスで変更できるようにします

    基本となるUI構成で不可欠となる要素 8つ は以下です
        - <UI要素 1>. UIを、Maya window 画面の前面にする
        - <UI要素 2>. UIの title設定 と、新規での ポジションとサイズ設定
        - <UI要素 3>. UI設定の 保存 と 復元 の機能を 何らかで実現する
        - <UI要素 4>. UI設定の 保存 と 復元 の機能
            Note): オリジナルメソッド ｛saveSettings」, 「restore」 で実現
        - <UI要素 5>. UIの 重複表示の回避
        - <UI要素 6>. UIの 見た目の統一
        - <UI要素 7>. -Pyside2特有事項- UI の close 時に delete されるようにする
        - <UI要素 8>. UIの window name (objectName) 設定
    #######################
    """
    # settingFileName = 'mainWindow.ini'
    prefix = 'test'
    commonName = 'MayaPySide2_windowPrefs_setting'

    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        u""" < initialize(初期化関数)コンストラクタ です >

        ::

          ここで定義されたインスタンス変数は、他のメソッドで上書き・参照が出来ます。

        基本となるUI構成で不可欠となる要素 8つ の内、以下 2つ を実行しています
            - <UI要素 1>. UIを、Maya window 画面の前面にする
            - <UI要素 3>. UI設定の保存と復元 の機能を 何らかで実現する
                .iniファイルを利用した、
                    - windowUIの、ポジションとサイズ、
                    - 他必要箇所となる 入力フィールドの要素、
                の、保存と復元 の機能を有効にする
        """
        # ######################################################################
        self.title = 'MainWindow'
        self.win = self.title + '_ui'
        self.size: Tuple[int] = (500, 300, 210, 270)  # x, y, width, height
        self.bgc = "background-color:gray; color: white"
        # ######################################################################

        # <UI要素 1>.
        # 当該window を Maya window 画面の前面に ######################################## start
        if parent is None:
            parent = maya_main_window()
        # 当該window を Maya window 画面の前面に ######################################## end

        super(MainWindow, self).__init__(parent, flags)

        # <UI要素 3>.
        # .iniファイルの設定 ########################################################### start
        self._iniFileSetting()
        # .iniファイルの設定 ########################################################### end

        # .iniファイルのパラメーター設定 ##################################### start
        self.iniFileParam = {'geo_iFP': 'geometry',
                             'contA_wid_expStat_iFP': 'contA_QWid_isExpand',
                             'contB_wid_expStat_iFP': 'contB_QWid_isExpand',
                             }
        # self.od = OrderedDict(self.iniFileParam)  # 順序付き辞書 定義
        # .iniファイルのパラメーター設定 ##################################### end

        # 作成された コンテナウィジェット の高さを辞書登録
        self.container_heights = {}
        self.containers = []

    # オリジナルメソッド
    # .iniファイルの設定 関数
    def _iniFileSetting(self):
        u""" < .iniファイルの設定 関数 です >

        オリジナルメソッド
        """
        folderName = f'{self.prefix}_{self.commonName}'
        maya_app_dir = os.getenv('MAYA_APP_DIR')  # user document maya directory
        maya_location = os.getenv('MAYA_LOCATION')  # pc maya directory(include version)
        maya_version = maya_location.split(r'/')[-1]  # get a maya version name
        deleteStr = 'Maya'
        versionNumber = maya_version.replace(deleteStr, '')  # get a maya version number only
        user_maya_document_dir = r'{}/{}'.format(maya_app_dir, versionNumber)

        # .iniファイル名
        settingFileName = self.win + '.ini'
        # 絶対パスを含むファイル名の設定
        self.filename = os.path.join(user_maya_document_dir,
                                     folderName,
                                     settingFileName
                                     )
        print('###' * 10)
        print(f'Preparing...')
        print(f'\t'
              f'Preparing a set of .INI file, at \n\t\t'
              f'{self.filename}\n'
              f'Note: It has not been saved yet.'
              )
        # QSettingsで、ファイル名 と、フォーマット を指定してインスタンスを作成
        self.__settings = QSettings(self.filename, QSettings.IniFormat)
        # 「setIniCodec」を使って文字コードを「utf-8」で指定すると、日本語にも威力発揮
        self.__settings.setIniCodec('utf-8')

    # オリジナルメソッド
    # 重複ウィンドウの回避関数
    def _duplicateWindowAvoidFunction(self, winName: str):
        u""" < 重複ウィンドウの回避関数 です >

        オリジナルメソッド
        """
        widgets = QApplication.allWidgets()
        for w in widgets:
            if w.objectName() == winName:
                # w.close()
                w.deleteLater()

    # オリジナルメソッド
    # Window基本設定
    def _windowBasicSettings(self):
        u""" < 当該window の、基本設定 をいっぺんに行う 関数 です >

        オリジナルメソッド

        .. note::
          - set window title と 新規のポジションとサイズ設定 : <UI要素 2>.
          - set window name : <UI要素 8>.
          はここで行っています
        基本となるUI構成で不可欠となる要素 8つ の内、以下 5つ を実行しています
            - <UI要素 2>. UIの title設定 と、新規での ポジションとサイズ設定
            - <UI要素 5>. UIの重複の回避
            - <UI要素 6>. UIの見た目の統一
            - <UI要素 7>. -Pyside2特有事項- UIのclose時にdeleteされるようにする
            - <UI要素 8>. UI window name (objectName) 設定
        """
        # <UI要素 2>.
        # UI設定の保存と復元 の機能 ###################################################### start
        self.setWindowTitle(self.title)  # <- window の title名 設定
        # ウィンドウが一度でも作成されているかどうかを確認
        # 純粋に初めてのUI作成時: False # 以下を実行
        # 次回再度ロード時は: True # ここをスキップし、前回の ポジションとサイズ が復元される
        if not self.isVisible():
            self.setGeometry(*self.size)  # 完全に新規にUI作成したときの初期値。アンパック(*)は重要
        # UI設定の保存と復元 の機能 ###################################################### end

        # <UI要素 5>.
        # UIの 重複表示の回避 ########################################################### start
        # old style ############################### start
        # child_list = self.parent().children()
        # for c in child_list:
        #     # 自分と同じ名前のUIのクラスオブジェクトが存在してたらCloseする
        #     if self.__class__.__name__ == c.__class__.__name__:
        #         c.close()
        # old style ############################### end
        self._duplicateWindowAvoidFunction(self.win)  # 重複ウィンドウの回避関数
        # UIの 重複表示の回避 ########################################################### end

        # <UI要素 6>.
        # UIの 見た目の統一 ############################################################# start
        # Windows用 window の見た目の制御を行います
        # # type1
        # # minimize, maximize , close 有り
        # self.setWindowFlags(Qt.Window)
        # # type2
        # # minimize のみ有り
        # self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint)
        # type3
        # close のみ有り
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # windowの右上にx印(close)のみ
        # UIの 見た目の統一 ############################################################# end

        # self.setUpdatesEnabled(True)  # デフォルトでTrueです

        # <UI要素 7>.
        # -Pyside2特有事項- UI の close 時に delete されるようにする ###################### start
        # PySideで作ったGUIは何もしてないと close しても delete はされません。
        # windowオブジェクト に `setAttribute` することで close 時に delete されるようになります。
        self.setAttribute(Qt.WA_DeleteOnClose)  # <- close 時に delete 設定
        # -Pyside2特有事項- UI の close 時に delete されるようにする ###################### end

        # <UI要素 8>.
        # UIの window name (objectName) 設定 ########################################## start
        # set window name
        self.setObjectName(self.win)  # <- window へobjectName 設定
        # UIの window name (objectName) 設定 ########################################## end

        # <UI要素 4>.
        # UI設定の保存と復元 の機能 の 一部 ############################################### start
        # different style ######################## start
        # Note: .iniファイルを使用せず、maya独自規格使用時 有効です
        #       但し、UIに入力フィールドとう存在した場合には、それらはここには含まれず、他のアプローチも必要
        # window を close したときのサイズ・位置のみが `windowPrefs.mel` に保存されるようになり、
        # 次回 show 時に復元されるようになります。
        # self.setProperty("saveWindowPref", True)
        # different style ######################## end
        #  UI設定の保存と復元 の機能 の 一部 ############################################### end                      )  # set window name, and save to windowPrefs ####################### end

    # UIの起動 関数
    def createUI(self):
        self._windowBasicSettings()  # Window基本設定

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
        self.containers.append(self.contA_wid)
        # シグナルとスロットを接続
        contA_clickableHeaderWid = self.contA_wid.contentHeader.clickableHeaderWidget
        contA_clickableHeaderWid.clicked.connect(partial(self.cal_alwaysHeight_containerAll
                                                         , self.contA_wid
                                                         )
                                                 )
        # doCollapseA
        # self.contA_wid.expand()  # initial operate expand/collapse

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
        self.containers.append(self.contB_wid)
        # シグナルとスロットを接続
        contB_clickableHeaderWid = self.contB_wid.contentHeader.clickableHeaderWidget
        contB_clickableHeaderWid.clicked.connect(partial(self.cal_alwaysHeight_containerAll
                                                         , self.contB_wid
                                                         )
                                                 )
        # doCollapseB
        # self.contB_wid.expand()  # initial operate expand/collapse

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
        self.contAll_vbxLay.addWidget(btnD_pbtnWid)
        btnD_pbtnWid.clicked.connect(self.contA_wid.toggle)

        # Reset ボタン のテスト
        btnE_reset_pbtnWid = QPushButton('Reset')
        self.contAll_vbxLay.addWidget(btnE_reset_pbtnWid)
        btnE_reset_pbtnWid.clicked.connect(partial(self.resetSettings, self.central_wid))

        self.show()
        # window の高さ編集をしてアップデートしてあげる
        self.cal_alwaysHeight_window()
        # print(self.geometry())
        # print(self.container_heights.values())

    # オーバーライド
    # show メソッド 組み込み関数
    def show(self):
        u""" < (オーバーライド) show メソッド 組み込み関数 です >

        オーバーライド

        .. note::
            当該 show メソッド は、基は組み込み関数です

        実行の手順
            #. 復元用のオリジナルメソッド「restore」を実行し、表示する前に設定を復元します
            #. 次に、メソッド「show」をオーバーライドし、表示する
        """
        self.restore()  # 復元用のオリジナルメソッド
        super(MainWindow, self).show()

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
        adjust = 20
        self.resize(current_width, final_height - adjust)
        # final_size = list(self.geometry().getRect())  # タプルをリストに変換
        # print(f'final_size: {final_size}')

    # 1. UI-1. メニュー コマンド群 ###################################################### start
    # メモ: (PyMel版)Model: editMenuSaveSettingsCmd に相当
    # オリジナルメソッド
    # 基本となるUI構成で不可欠となる要素 8つ の内、以下 1つ を実行しています
    # <UI要素 4>. UI設定の 保存 の機能
    # UI設定の保存用 関数
    def saveSettings(self):
        u""" < UI設定の保存用 関数 です >

        オリジナルメソッド

        基本となるUI構成で不可欠となる要素 8つ の内、以下 1つ を実行しています
            <UI要素 4>. UI設定の 保存 の機能
        """
        print('###' * 10)
        print(f'Save...'
              f'\nNote: always overwriting save.. mode'
              )
        # サイズ の情報を 保存
        self.__settings.setValue(self.iniFileParam['geo_iFP'], self.saveGeometry())  # ウインドウの位置と大きさを 可変byte配列 で 取得 し、iniFile へ 可変byte配列 を セット
        # print(f'\tSave a \n\t\t'
        #       f'{self.iniFileParam["geo_iFP"]} \n\t\t\t'
        #       f'param: {...}'
        #       )

        # ウィジェット(コンテナA用) の情報を 保存
        contA_wid_isExpand, _ = self.contA_wid.contentHeader.outPut_content_status()
        self.__settings.setValue(self.iniFileParam['contA_wid_expStat_iFP'], contA_wid_isExpand)
        # print(f'\tSave a \n\t\t'
        #       f'{self.iniFileParam["contA_wid_expStat_iFP"]} \n\t\t\t'
        #       f'param: {contA_wid_isExpand}'
        #       )

        # ウィジェット(コンテナB用) の情報を 保存
        contB_wid_isExpand, _ = self.contB_wid.contentHeader.outPut_content_status()
        self.__settings.setValue(self.iniFileParam['contB_wid_expStat_iFP'], contB_wid_isExpand)
        # print(f'\tSave a \n\t\t'
        #       f'{self.iniFileParam["contB_wid_expStat_iFP"]} \n\t\t\t'
        #       f'param: {contB_wid_isExpand}'
        #       )
        print(f'\tSave a .INI file, at \n\t\t{self.filename}')

    # Reset 実行 関数 #####################################
    # メモ: (PyMel版)Model: set_default_value_toOptionVar に相当
    # メモ: (PyMel版)View: editMenuReloadCmd に相当
    # オリジナルメソッド
    # Reset 実行 関数(UIのサイズは保持)
    def resetSettings(self, mainWidObjName):
        u""" < Reset 実行 関数 です >

        オリジナルメソッド

        .. note::
            UIの入力箇所を全てクリアーします
                見た目がUIの再描画リロードライクにしています
            因みに、UIのサイズは保持します

        :param mainWidObjName: central_wid # セントラルウィジェット に相当します
        """
        # print(args)
        # self.__init__()  # すべて、元の初期値に戻す
        # self.set_default_value_toOptionVar()  # optionVar の value を default に戻す操作
        # pm.evalDeferred(lambda *args: self.create())  # refresh UI <---- ここ重要!!

        # UIの入力フィールドを初期の空にリセット
        print('###' * 10)
        print(f'\nReset all input value...')
        # 入力フィールドを持つ子供Widgetのみのカレントの情報一括クリアー 関数 実行
        self.clearAllValue_toAllWidget(mainWidObjName)
        # Containerを使用した特殊なケース時に使用 #################################
        for eachCont in self.containers:
            eachCont.collapse()  # 一遍に全てのContainerを閉じます
            self.cal_alwaysHeight_containerAll(eachCont)
            self.cal_alwaysHeight_containerAll(eachCont)
        # Containerを使用した特殊なケース時に使用 #################################
        self.saveSettings()  # UI設定の保存用 関数 実行

    # オリジナルメソッド
    # 入力フィールドを持つ子供Widgetのみのカレントの情報一括クリアー 関数
    def clearAllValue_toAllWidget(self, mainWidObjName):
        u""" < 入力フィールドを持つ子供Widgetのみのカレントの情報一括クリアー 関数 です >

        オリジナルメソッド

        .. note:: 情報一括クリアー には以下の条件を満たす必要があります

            1.
                渡された mainWidObjName が clear メソッド を持ち、
                    かつそれが呼び出し可能である場合、clear メソッド を呼び出しています。
                これは、ウィジェットがテキストを表示するための メソッド で、
                    テキストをクリアする役割が期待されています。

            ↓

            1'. 特殊ケースに変更
                b.c.): Container の Header には、
                    QWidget, QLabel, QFont が在り、入力フィールドを持っているため
                        一括クリアーの実行には含めたく無い からです

                mainWidObjName が clearメソッド を持ち、
                    かつ呼び出し可能である場合に、
                        かつ mainWidObjName が Container でないか、
                            もしくは Container である場合でも
                QWidget、QLabel、QFontを全て持っている場合は
                    何もせずに終了します（pass文が実行されます）。
                それ以外の場合は mainWidObjName.clear() を実行します。

            2.
                渡された mainWidObjName が setChecke メソッド を持ち、
                    かつそれが呼び出し可能である場合、setChecked(False) を呼び出しています。
                これは、チェックボックスの状態を非選択に設定するためのメソッドです。

            3.
                もし mainWidObjName が QComboBox の インスタンス である場合、
                    setCurrentIndex(-1) を呼び出しています。
                これは、コンボボックス の現在の選択をクリアし、
                    何も選択されていない状態にします。

            4.
                最後に、mainWidObjName にぶら下がっている全ての子供の ウィジェット に対して
                    再帰的に同じ処理を行います。
                これにより、メインウィジェット の階層構造全体に対して
                    再帰的に クリア が行われます。

        メインとなる Widget(mainWidget) にぶら下がっている、
            入力フィールドを持つ 子供の Widget のみ、に特化しています
        それらに対して、カレントの情報を一括で クリアー する
            メソッドとなります

        :param mainWidObjName: central_wid # ここでは セントラルウィジェット に相当します
        """
        # 1.
        # Container を使用した特殊なケース時に使用 ############################ start
        # b.c.): Container の Header には、
        #       QWidget, QLabel, QFont が在り、入力フィールドを持っているため
        if (hasattr(mainWidObjName, 'clear')
                and callable(getattr(mainWidObjName, 'clear')))\
                :
            if (not isinstance(mainWidObjName, Container)
                    or all(hasattr(mainWidObjName, attr)
                           for attr in ['QWidget', 'QLabel', 'QFont']))\
                    :
                pass
            else:
                mainWidObjName.clear()
        # Container を使用した特殊なケース時に使用 ############################ end
        # # 通常は ########################################################## start
        # if hasattr(mainWidObjName, 'clear') and callable(getattr(mainWidObjName, 'clear')):
        #     mainWidObjName.clear()
        # # 通常は ########################################################## start

        # 2.
        if hasattr(mainWidObjName, 'setChecked') and callable(getattr(mainWidObjName, 'setChecked')):
            mainWidObjName.setChecked(False)
        # 3.
        if isinstance(mainWidObjName, QComboBox):
            mainWidObjName.setCurrentIndex(-1)
        # 4.
        for child in mainWidObjName.findChildren(QWidget):
            self.clearAllValue_toAllWidget(child)

    # Help 実行 関数 #####################################

    # Close 実行 関数 #####################################
    # メモ: (PyMel版)Model: editMenuSaveSettingsCmd に相当
    # メモ: (PyMel版)View: editMenuCloseCmd に相当
    # オーバーライド
    # closeEvent メソッド 組み込み関数
    def closeEvent(self, event):
        u""" < (オーバーライド) closeEvent メソッド 組み込み関数 です >

        オーバーライド

        .. note::
            当該 closeEvent メソッド は、基は組み込み関数であり、 イベントハンドラー です
                閉じる要求を受信したときにトップレベル ウィンドウに対してのみ呼び出されます
            self.close でも発動します

        実行の手順
            #. UI設定の保存用オリジナルメソッド「saveSettings」を実行し、設定を保存します
            #. 次に、閉じる要求を受信したときにトップレベル ウィンドウに対してのみ呼び出されます
        """
        # print(event)
        self.saveSettings()  # UI設定の保存用オリジナルメソッド
        # super(MainWindow, self).closeEvent(event)  # ここは無くても上手く発動するようです
    # 1. UI-1. メニュー コマンド群 ######################################################## end

    # def closeUI(self):
    #     print('2')
    #     # self.saveSettings()
    #     self.close()

    # 4. UI-4. OptionVar を利用したパラメータ管理 コマンド群 ############################### start
    # メモ: (PyMel版)Model: restoreOptionVarCmd に相当
    # オリジナルメソッド
    # 基本となるUI構成で不可欠となる要素 8つ の内、以下 1つ を実行しています
    # <UI要素 4>. UI設定の 復元 の機能
    # UI設定の復元用 関数
    def restore(self):
        u""" < UI設定の復元用 関数 です >

        オリジナルメソッド

        基本となるUI構成で不可欠となる要素 8つ の内、以下 1つ を実行しています
            <UI要素 4>. UI設定の 復元 の機能
        .. note::
            - 継承することを前提に考えると、「__init__」で復元するのは好ましくありません
            - self.__settings.value から取得するデータは、
                restoreGeometry以外は、型が string です！！
        """
        print('###' * 10)
        print(f'Restore...')

        # サイズの情報を 復元
        self.restoreGeometry(self.__settings.value(self.iniFileParam['geo_iFP']))  # iniFile から 可変byte配列 を ゲット し、サイズの情報 を 復元操作
        # print(f'\tRestore a \n\t\t'
        #       f'{self.iniFileParam["geo_iFP"]} \n\t\t\t'
        #       f'param: {...}'
        #       )

        # ウィジェット(コンテナA用) の情報を 復元
        contA_wid_isExpand: str = self.__settings.value(self.iniFileParam['contA_wid_expStat_iFP'])  # iniFile から isChecked を ゲット
        if contA_wid_isExpand is True:
            self.contA_wid.expand()
        else:
            self.contA_wid.collapse()
        # print(f'\tRestore a \n\t\t'
        #       f'{self.iniFileParam["contA_wid_expStat_iFP"]} \n\t\t\t'
        #       f'param: {contA_wid_isExpand}'
        #       )

        # ウィジェット(コンテナB用) の情報を 復元
        contB_wid_isExpand: str = self.__settings.value(self.iniFileParam['contB_wid_expStat_iFP'])  # iniFile から isChecked を ゲット
        if contB_wid_isExpand is True:
            self.contB_wid.expand()
        else:
            self.contB_wid.collapse()
        # print(f'\tRestore a \n\t\t'
        #       f'{self.iniFileParam["contB_wid_expStat_iFP"]} \n\t\t\t'
        #       f'param: {contB_wid_isExpand}'
        #       )

        print(f'\tRestore a .INI file, from \n\t\t{self.filename}')
    # 4. UI-4. OptionVar を利用したパラメータ管理 コマンド群 ################################# end


if __name__ == '__main__':
    print(u'{}.py: loaded as script file'.format(__name__))
    test = MainWindow()
    test.createUI()
else:
    print(u'{}.py: loaded as module file'.format(__name__))
    print('{}'.format(__file__))  # 実行したモジュールフルパスを表示する
# pprint.pprint(RT4_UI_PyMel.mro())  # メソッドを呼び出す順番が解ります

print(u'モジュール名:{}\n'.format(__name__))  # 実行したモジュール名を表示する


# 0): QMainWindow
# |
# |-- 1): QWidget (self.central_wid) -Widget-
#   |
#   |-- 2): QVBoxLayout (self.main_vbxLay) -Layout-
#     |
#     |-- 3): QVBoxLayout (self.contAll_vbxLay) -Layout- (コンテナ群まとめレイアウト)
#       |
#       |-- #): Container (self.contA_wid) -Widget- (コンテナA用)
#       | |
#       | |-- #): QHBoxLayout (self.contentA_gLay) -Layout- (コンテナA用の水平レイアウト)
#       |   |
#       |   |-- #): QPushButton -Widget- (self.btnA_pbtnWid)
#       |   |
#       |   |-- #): QPushButton -Widget- (self.btnB_pbtnWid)
#       |   |
#       |   |-- #): QPushButton -Widget- (self.btnC_pbtnWid)
#       |
#       |-- #): Container (self.contB_wid) -Widget- (コンテナA用)
#       | |
#       | |-- #): QHBoxLayout (self.contentB_gLay) -Layout- (コンテナB用の水平レイアウト)
#       |   |
#       |   |-- #): QPushButton -Widget- (self.btnD_pbtnWid)
#       |
#       |-- #): QPushButton (self.contE_wid) -Widget- コンテナA toggle
#       |-- #): QPushButton (self.contF_wid) -Widget- Reset
