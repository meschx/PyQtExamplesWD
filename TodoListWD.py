import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QLabel, QListWidgetItem, QInputDialog, QComboBox
from PyQt6.QtGui import QColor

class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadTasks()

    def initUI(self):
        self.setWindowTitle('Menadżer zadań')

        #Layouty
        mainLayout = QVBoxLayout()
        inputLayout = QHBoxLayout()
        buttonLayout = QHBoxLayout()
        filterLayout = QHBoxLayout()

        #Widgety
        self.taskInput = QLineEdit(self)
        self.priorityInput = QComboBox(self)
        self.priorityInput.addItems(['Niski', 'Średni', 'Wysoki'])
        self.addButton = QPushButton('Dodaj zadanie', self)
        self.deleteButton = QPushButton('Usuń zaznaczone zadanie', self)
        self.editButton = QPushButton('Edytuj zaznaczone zadanie', self)
        self.taskList = QListWidget(self)
        self.messageLabel = QLabel('', self)
        self.taskCountLabel = QLabel('Liczba zadań: 0', self)
        self.filterInput = QComboBox(self)
        self.filterInput.addItems(['Wszystkie', 'Niski', 'Średni', 'Wysoki'])
        self.filterButton = QPushButton('Filtruj', self)

        #Dodanie widgetów do layoutów
        inputLayout.addWidget(self.taskInput)
        inputLayout.addWidget(self.priorityInput)
        inputLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addWidget(self.editButton)
        filterLayout.addWidget(self.filterInput)
        filterLayout.addWidget(self.filterButton)
        mainLayout.addLayout(inputLayout)
        mainLayout.addWidget(self.taskList)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(filterLayout)
        mainLayout.addWidget(self.messageLabel)
        mainLayout.addWidget(self.taskCountLabel)
        
        self.setLayout(mainLayout)

        #Połączenie sygnałów ze slotami
        self.addButton.clicked.connect(self.addTask)
        self.deleteButton.clicked.connect(self.deleteTask)
        self.editButton.clicked.connect(self.editTask)
        self.filterButton.clicked.connect(self.filterTasks)

    def addTask(self):
        task = self.taskInput.text().strip()
        priority = self.priorityInput.currentText()
        if task:
            item = QListWidgetItem(task)
            item.setData(1, priority)
            self.setItemColor(item, priority)
            self.taskList.addItem(item)
            self.taskInput.clear()
            self.messageLabel.setText('Dodano zadanie!')
            self.updateTaskCount()
            self.saveTasks()
        else:
            self.messageLabel.setText('Nie można dodać pustego zadania!')

    def deleteTask(self):
        selectedTask = self.taskList.currentItem()
        if selectedTask:
            self.taskList.takeItem(self.taskList.row(selectedTask))
            self.messageLabel.setText('Usunięto zadanie!')
            self.updateTaskCount()
            self.saveTasks()
        else:
            self.messageLabel.setText('Nie zaznaczono zadania do usunięcia!')

    def editTask(self):
        selectedTask = self.taskList.currentItem()
        if selectedTask:
            text, ok = QInputDialog.getText(self, 'Edytuj zadanie', 'Zmień nazwę zadania:', text=selectedTask.text())
            if ok and text:
                selectedTask.setText(text)
                self.messageLabel.setText('Zaktualizowano zadanie!')
                self.saveTasks()
            else:
                self.messageLabel.setText('Nie można ustawić pustego zadania!')
        else:
            self.messageLabel.setText('Nie zaznaczono zadania do edycji!')

    def filterTasks(self):
        filterPriority = self.filterInput.currentText()
        for i in range(self.taskList.count()):
            item = self.taskList.item(i)
            if filterPriority == 'Wszystkie' or filterPriority == item.data(1):
                item.setHidden(False)
            else:
                item.setHidden(True)

    def setItemColor(self, item, priority):
        if priority == 'Niski':
            item.setBackground(QColor('darkGreen'))
        elif priority == 'Średni':
            item.setBackground(QColor('#B8860B'))
        elif priority == 'Wysoki':
            item.setBackground(QColor('darkRed'))

    def updateTaskCount(self):
        self.taskCountLabel.setText(f'Liczba zadań: {self.taskList.count()}')

    def saveTasks(self):
        with open('tasks.txt', 'w') as file:
            for i in range(self.taskList.count()):
                item = self.taskList.item(i)
                file.write(f'{item.text()}|{item.data(1)}\n')

    def loadTasks(self):
        try:
            with open('tasks.txt', 'r') as file:
                for line in file:
                    task, priority = line.strip().split('|')
                    item = QListWidgetItem(task)
                    item.setData(1, priority)
                    self.setItemColor(item, priority)
                    self.taskList.addItem(item)
            self.updateTaskCount()
        except FileNotFoundError:
            pass

def darkMode(app):
    dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QLineEdit {
            background-color: #3b3b3b;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 4px;
            color: #ffffff;
        }
        QPushButton {
            background-color: #444444;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
            min-width: 80px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #333333;
        }
        QListWidget {
            background-color: #3b3b3b;
            border: 1px solid #555555;
            border-radius: 3px;
            color: #ffffff;
        }
        QComboBox {
            background-color: #3b3b3b;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 4px;
            color: #ffffff;
        }}
        QComboBox::down-arrow {
            background-color: #444444;
            width: 16px;
            height: 16px;
        }
        QLabel {
            color: #ffffff;
        }
    """
    app.setStyleSheet(dark_style)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    darkMode(app)
    window = TaskManager()
    window.show()
    sys.exit(app.exec())