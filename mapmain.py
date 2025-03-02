# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mapmain.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(754, 879)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.address_input = QtWidgets.QLineEdit(self.centralwidget)
        self.address_input.setGeometry(QtCore.QRect(130, 10, 421, 31))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.address_input.setFont(font)
        self.address_input.setObjectName("address_input")
        self.search_button = QtWidgets.QPushButton(self.centralwidget)
        self.search_button.setGeometry(QtCore.QRect(580, 10, 113, 32))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.search_button.setFont(font)
        self.search_button.setStyleSheet("QPushButton{\n"
"border-radius:10px;\n"
"border-color:gray;\n"
"border-style:solid;\n"
"border-width:3px;\n"
"background-color:gold;\n"
"color:back;\n"
"}\n"
"QPushButton:hover{\n"
"background-color:darkblue;\n"
"color:white;\n"
"}")
        self.search_button.setObjectName("search_button")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(130, 70, 611, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.result_label = QtWidgets.QLabel(self.centralwidget)
        self.result_label.setGeometry(QtCore.QRect(130, 40, 621, 31))
        self.result_label.setObjectName("result_label")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(20, 78, 101, 16))
        self.label_2.setObjectName("label_2")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 140, 731, 721))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.combB1 = QtWidgets.QComboBox(self.centralwidget)
        self.combB1.setGeometry(QtCore.QRect(435, 97, 140, 40))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.combB1.setFont(font)
        self.combB1.setObjectName("combB1")
        self.combB2 = QtWidgets.QComboBox(self.centralwidget)
        self.combB2.setGeometry(QtCore.QRect(585, 97, 140, 40))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.combB2.setFont(font)
        self.combB2.setObjectName("combB2")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.search_button.setText(_translate("MainWindow", "住所検索"))
        self.result_label.setText(_translate("MainWindow", "緯度経度"))
        self.label.setText(_translate("MainWindow", "住所を入力"))
        self.label_2.setText(_translate("MainWindow", "表示情報の選択"))
