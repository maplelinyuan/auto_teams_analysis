from PyQt5 import QtCore, QtGui, QtWidgets, QtSql
import time
import datetime
import json
import pdb

def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False

def is_float(aString):
    try:
        float(aString)
        return True
    except:
        return False

class Ui_MainWindow(object):

    risk_divisor = 3    # 风险除数，默认：中/3

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(70, 20, 113, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 20, 54, 21))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 60, 41, 21))
        self.label_2.setObjectName("label_2")
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setGeometry(QtCore.QRect(50, 60, 71, 20))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(140, 60, 41, 21))
        self.label_3.setObjectName("label_3")
        self.lineEdit_3 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_3.setGeometry(QtCore.QRect(180, 60, 71, 20))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(340, 60, 75, 23))
        self.pushButton.setObjectName("pushButton")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(10, 100, 71, 21))
        self.label_4.setObjectName("label_4")
        self.lineEdit_4 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_4.setGeometry(QtCore.QRect(80, 100, 113, 20))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(400, 10, 69, 22))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(340, 10, 51, 21))
        self.label_5.setObjectName("label_5")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.comboBox.activated[str].connect(self.onActivated)   ##用来将combobox关联的函数,改变风险等级，默认中，（/3）
        self.pushButton.clicked.connect(self.calculate_kaili)   ##开始计算

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "投注额-凯利公式"))
        self.label.setText(_translate("MainWindow", "目前资金:"))
        self.label_2.setText(_translate("MainWindow", "赔率:"))
        self.label_3.setText(_translate("MainWindow", "概率:"))
        self.pushButton.setText(_translate("MainWindow", "计算"))
        self.label_4.setText(_translate("MainWindow", "凯利投注额:"))
        self.comboBox.setItemText(0, _translate("MainWindow", "中"))
        self.comboBox.setItemText(1, _translate("MainWindow", "高"))
        self.comboBox.setItemText(2, _translate("MainWindow", "低"))
        self.comboBox.setItemText(3, _translate("MainWindow", "超高"))
        self.comboBox.setItemText(4, _translate("MainWindow", "超低"))
        self.label_5.setText(_translate("MainWindow", "风险等级:"))

    # 提示框
    def showdialog(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText(text)
        # msg.setInformativeText("This is additional information")
        msg.setWindowTitle("错误提示")
        # msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        # msg.buttonClicked.connect(msgbtn)
        retval = msg.exec_()
        print("value of pressed message box button:", retval)

    # 切换team name 中英文
    def calculate_kaili(self):
        current_risk_divisor = self.risk_divisor
        current_capital = self.lineEdit.text().strip()
        current_odds = self.lineEdit_2.text().strip()
        current_probability = self.lineEdit_3.text().strip()
        if (not is_float(current_capital)) or (not is_float(current_odds)) or (not is_float(current_probability)):
            self.showdialog('请完整输入信息')
            return False
        bet_propotion = (float(current_odds)*float(current_probability)-(1-float(current_probability)))/float(current_odds)
        bet_capital = round(bet_propotion*float(current_capital)/current_risk_divisor,2)
        self.lineEdit_4.setText(str(bet_capital))

    def onActivated(self, text):  ##用来实现combobox关联的函数
        if text == '中':
            new_risk_divisor = 3
        elif text == '高':
            new_risk_divisor = 2
        elif text == '低':
            new_risk_divisor = 4
        elif text == '超高':
            new_risk_divisor = 1
        elif text == '超低':
            new_risk_divisor = 5
        else:
            new_risk_divisor = 3
        self.risk_divisor = new_risk_divisor   # 改变风险值

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
