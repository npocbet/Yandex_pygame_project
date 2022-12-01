import sqlite3
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QTableWidgetItem

HEADERS = {'results': ['date', 'score']}


class ResultWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("./ui/results.ui", self)
        self.result = []
        self.update_table()

    def update_table(self):
        con = sqlite3.connect('./db/results.sqlite')
        cur = con.cursor()
        self.result = cur.execute(f"""SELECT date, score FROM results ORDER BY score DESC;""").fetchall()

        self.tableWidget.setRowCount(len(self.result))
        self.tableWidget.setColumnCount(len(self.result[0]))

        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

        con.close()

def paste_score_into_db(score):
    con = sqlite3.connect('db/results.sqlite')
    cur = con.cursor()
    request = f'INSERT INTO results (' + \
              ', '.join(HEADERS['results']) + \
              ') VALUES ( ' + \
              ', '.join([datetime.now().strftime("'%A %d-%B-%y %H:%M'"), str(score)]) + \
              ')'
    print(request)
    cur.execute(request).fetchall()

    con.commit()
    con.close()