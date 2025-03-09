import sys
import csv
from datetime import datetime, timedelta
import random
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                            QTableView, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLineEdit, QLabel, QFormLayout,
                            QComboBox, QDateEdit, QFileDialog)
from PyQt5.QtCore import Qt, QDate

class Tickets(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zarządzanie biletami")
        self.resize(800, 600)
        
        self.ticket_periods = {
            "Miesięczny": 30,
            "90-dniowy": 90,
            "Półroczny": 182,
            "Roczny": 365
        }

        self.ticket_prices = {
            "Miesięczny": {"Normalny": 120.00, "Ulgowy": 60.00},
            "90-dniowy": {"Normalny": 320.00, "Ulgowy": 160.00},
            "Półroczny": {"Normalny": 600.00, "Ulgowy": 300.00},
            "Roczny": {"Normalny": 1100.00, "Ulgowy": 550.00}
        }
        
        self.setup_ui()
        self.setup_database()
        # self.load_test_data()
        self.load_data()
    
    def setup_ui(self):
        """Tworzy interfejs użytkownika"""
        # Główny widget i layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Formularz
        self.form_layout = QFormLayout()
        
        # Pola formularza
        self.card_id = QLineEdit()
        self.card_id.setReadOnly(True)
        self.customer_name = QLineEdit()
        self.ticket_type = QComboBox()
        self.ticket_type.addItems(list(self.ticket_periods.keys()))
        self.ticket_discount = QComboBox()
        self.ticket_discount.addItems(["Normalny", "Ulgowy"])
        self.valid_from = QDateEdit()
        self.valid_from.setDate(QDate.currentDate())
        self.valid_from.setCalendarPopup(True)
        self.valid_to = QDateEdit()
        self.valid_to.setEnabled(False)
        self.price = QLineEdit()
        self.price.setEnabled(False)
        
        # Dodawanie pól do formularza
        self.form_layout.addRow("Nr karty:", self.card_id)
        self.form_layout.addRow("Nazwa klienta:", self.customer_name)
        self.form_layout.addRow("Typ biletu:", self.ticket_type)
        self.form_layout.addRow("Rodzaj biletu:", self.ticket_discount)
        self.form_layout.addRow("Ważny od:", self.valid_from)
        self.form_layout.addRow("Ważny do:", self.valid_to)
        self.form_layout.addRow("Cena:", self.price)
        
        # Przyciski
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Dodaj bilet")
        self.edit_button = QPushButton("Edytuj bilet")
        self.delete_button = QPushButton("Usuń bilet")
        self.clear_button = QPushButton("Wyczyść formularz")
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.clear_button)
        
        # Tabela
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        # Przyciski funkcjonalności dodatkowej
        buttons_down_layout = QHBoxLayout()
        self.export_CSV_button = QPushButton("Eksportuj do CSV")
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Wszystkie"] + list(self.ticket_periods.keys()))
        self.filter_discount = QComboBox()
        self.filter_discount.addItems(["Wszystkie", "Normalny", "Ulgowy"])
        self.show_valid = QComboBox()
        self.show_valid.addItems(["Wszystkie", "Ważne dzisiaj"])
        buttons_down_layout.addWidget(self.filter_type)
        buttons_down_layout.addWidget(self.filter_discount)
        buttons_down_layout.addWidget(self.show_valid)
        buttons_down_layout.addWidget(self.export_CSV_button)

        label_down_layout = QHBoxLayout()
        label_down_layout.setSpacing(5)  
        count_label = QLabel("Liczba biletów: ")
        self.count_label = QLabel("0")  
        label_down_layout.addWidget(count_label)
        label_down_layout.addWidget(self.count_label)
        label_down_layout.addStretch()  

        # Dodawanie wszystkich elementów do głównego layoutu
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(buttons_layout)
        self.layout.addWidget(self.table)
        self.layout.addLayout(buttons_down_layout)
        self.layout.addLayout(label_down_layout)
        
        # Połączenia sygnałów
        self.ticket_type.currentTextChanged.connect(self.update_price)
        self.ticket_type.currentTextChanged.connect(self.update_valid_to)
        self.ticket_discount.currentTextChanged.connect(self.update_price)
        self.valid_from.dateChanged.connect(self.update_valid_to)
        self.add_button.clicked.connect(self.add_ticket)
        self.edit_button.clicked.connect(self.edit_ticket)
        self.delete_button.clicked.connect(self.delete_ticket)
        self.table.clicked.connect(self.on_row_clicked)
        self.clear_button.clicked.connect(self.clear_form)
        self.export_CSV_button.clicked.connect(self.export_to_CSV)
        self.filter_type.currentTextChanged.connect(self.apply_filters)
        self.filter_discount.currentTextChanged.connect(self.apply_filters)
        self.show_valid.currentTextChanged.connect(self.apply_filters)


    def setup_database(self):
        """Tworzy tabelę w bazie danych SQLite"""
        query = QSqlQuery()
        query.exec_("""
            CREATE TABLE IF NOT EXISTS tickets (
                card_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                discount_type TEXT NOT NULL,
                valid_from DATE NOT NULL,
                valid_to DATE NOT NULL,
                price FLOAT NOT NULL
            )
        """)

    def generate_card_id(self):
        """Generuje 16-cyfrowy numer karty"""
        return ''.join([str(random.randint(0, 9)) for _ in range(16)])

    def update_price(self):
        """Aktualizuje cenę na podstawie wybranego typu biletu i rodzaju ulgi"""
        ticket_type = self.ticket_type.currentText()
        discount_type = self.ticket_discount.currentText()
        price = self.ticket_prices[ticket_type][discount_type]
        self.price.setText(f"{price:.2f}")

    def update_valid_to(self):
        """Aktualizuje datę końcową na podstawie typu biletu i daty początkowej"""
        start_date = self.valid_from.date().toPyDate()
        days = self.ticket_periods[self.ticket_type.currentText()]
        end_date = start_date + timedelta(days=days)
        self.valid_to.setDate(QDate.fromString(end_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))

    def update_ticket_count(self):
        """Aktualizuje licznik biletów"""
        count = self.model.rowCount()
        self.count_label.setText(str(count))

    def add_ticket(self):
        """Dodaje nowy bilet do bazy danych"""
        if not self.customer_name.text():
            QMessageBox.warning(self, "Błąd", "Pole nazwy klienta musi być wypełnione!")
            return
        
        try:
            price = float(self.price.text())
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Nieprawidłowa cena biletu!")
            return
        
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO tickets (card_id, customer_name, ticket_type, discount_type, 
                               valid_from, valid_to, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        card_id = self.generate_card_id()
        
        query.addBindValue(card_id)
        query.addBindValue(self.customer_name.text())
        query.addBindValue(self.ticket_type.currentText())
        query.addBindValue(self.ticket_discount.currentText())
        query.addBindValue(self.valid_from.date().toString("yyyy-MM-dd"))
        query.addBindValue(self.valid_to.date().toString("yyyy-MM-dd"))
        query.addBindValue(price)
        
        if query.exec_():
            QSqlDatabase.database().commit()
            self.model.select()
            self.clear_form()
            self.update_ticket_count()
            QMessageBox.information(self, "Sukces", f"Bilet został dodany!\nNumer karty: {card_id}")
        else:
            QMessageBox.critical(self, "Błąd", query.lastError().text())
    
    def load_data(self):
        """Wczytuje dane z bazy danych do tabeli"""
        self.model = QSqlTableModel(db=QSqlDatabase.database())
        self.model.setTable("tickets")
        
        self.model.setHeaderData(0, Qt.Horizontal, "Nr karty")
        self.model.setHeaderData(1, Qt.Horizontal, "Nazwa klienta")
        self.model.setHeaderData(2, Qt.Horizontal, "Typ biletu")
        self.model.setHeaderData(3, Qt.Horizontal, "Rodzaj biletu")
        self.model.setHeaderData(4, Qt.Horizontal, "Data od")
        self.model.setHeaderData(5, Qt.Horizontal, "Data do")
        self.model.setHeaderData(6, Qt.Horizontal, "Cena")
        
        self.table.setModel(self.model)
        self.model.select()
        self.update_ticket_count()

    def on_row_clicked(self, current):
        """Wczytuje dane z wybranego wiersza do formularza"""
        if not current.isValid():
            return
            
        self.clear_form()
        
        card_id = self.model.index(current.row(), 0).data()
        customer_name = self.model.index(current.row(), 1).data()
        ticket_type = self.model.index(current.row(), 2).data()
        discount_type = self.model.index(current.row(), 3).data()
        valid_from = self.model.index(current.row(), 4).data()
        valid_to = self.model.index(current.row(), 5).data()
        price = self.model.index(current.row(), 6).data()

        self.card_id.setText(str(card_id))
        self.customer_name.setText(customer_name)
        self.ticket_type.setCurrentText(ticket_type)
        self.ticket_discount.setCurrentText(discount_type)
        self.valid_from.setDate(QDate.fromString(valid_from, "yyyy-MM-dd"))
        self.valid_to.setDate(QDate.fromString(valid_to, "yyyy-MM-dd"))
        self.price.setText(str(price))

    def edit_ticket(self):
        """Zapisuje zmiany wprowadzone w formularzu"""
        if not self.card_id.text():
            QMessageBox.warning(self, "Błąd", "Najpierw wybierz bilet do edycji!")
            return

        if QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz zaktualizować ten bilet?") == QMessageBox.Yes:
            query = QSqlQuery()
            query.prepare("""
                UPDATE tickets
                SET customer_name = ?, ticket_type = ?, discount_type = ?,
                    valid_from = ?, valid_to = ?, price = ?
                WHERE card_id = ?
            """)
            
            query.addBindValue(self.customer_name.text())
            query.addBindValue(self.ticket_type.currentText())
            query.addBindValue(self.ticket_discount.currentText())
            query.addBindValue(self.valid_from.date().toString("yyyy-MM-dd"))
            query.addBindValue(self.valid_to.date().toString("yyyy-MM-dd"))
            query.addBindValue(float(self.price.text()))
            query.addBindValue(self.card_id.text())
            
            if query.exec_():
                QSqlDatabase.database().commit()
                self.model.select()
                self.clear_form()
                QMessageBox.information(self, "Sukces", "Bilet został zaktualizowany!")
            else:
                QMessageBox.critical(self, "Błąd", query.lastError().text())
    
    def delete_ticket(self):
        """Usuwa wybrany bilet"""
        current = self.table.currentIndex()
        if not current.isValid():
            QMessageBox.warning(self, "Błąd", "Wybierz bilet do usunięcia!")
            return
            
        if QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz usunąć ten bilet?") == QMessageBox.Yes:
            self.model.removeRow(current.row())
            self.model.submitAll()
            self.update_ticket_count()
            self.model.select()
    
    def clear_form(self):
        """Czyści formularz po dodaniu lub edycji biletu"""
        self.card_id.clear()
        self.customer_name.clear()
        self.ticket_type.setCurrentIndex(0)
        self.ticket_discount.setCurrentIndex(0)
        self.valid_from.setDate(QDate.currentDate())

    def export_to_CSV(self):
        """Eksportuje dane do pliku CSV"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Eksport do CSV", "", "Pliki CSV (*.csv)")
        if file_name:
            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                headers = [self.model.headerData(i, Qt.Horizontal) for i in range(self.model.columnCount())]
                writer.writerow(headers)
                for row in range(self.model.rowCount()):
                    row_data = [self.model.index(row, i).data() for i in range(self.model.columnCount())]
                    writer.writerow(row_data)
                QMessageBox.information(self, "Sukces", "Dane zostały wyeksportowane do pliku CSV!")

    def apply_filters(self):
        """Filtruje dane w tabeli na podstawie wybranych kryteriów"""
        filter_conditions = []
        
        if self.filter_type.currentText() != "Wszystkie":
            filter_conditions.append(f"ticket_type = '{self.filter_type.currentText()}'")
        
        if self.filter_discount.currentText() != "Wszystkie":
            filter_conditions.append(f"discount_type = '{self.filter_discount.currentText()}'")
        
        if self.show_valid.currentText() == "Ważne dzisiaj":
            current_date = datetime.now().strftime("%Y-%m-%d")
            filter_conditions.append(
                f"valid_from <= '{current_date}' AND valid_to >= '{current_date}'"
            )

        if filter_conditions:
            filter_string = " AND ".join(filter_conditions)
            self.model.setFilter(filter_string)
        else:
            self.model.setFilter("")
        
        self.model.select()
        self.update_ticket_count()

    def load_test_data(self):
        """Wczytuje przykładowe dane testowe do bazy danych"""
        query = QSqlQuery()
        
        test_data = [
            # Bilety ważne (aktualna data)
            ("1111222233334444", "Jan Kowalski", "Miesięczny", "Normalny", "2024-03-01", "2024-03-31", 120.00),
            ("2222333344445555", "Anna Nowak", "Miesięczny", "Ulgowy", "2024-03-01", "2024-03-31", 60.00),
            ("3333444455556666", "Piotr Wiśniewski", "90-dniowy", "Normalny", "2024-02-01", "2024-04-30", 320.00),
            ("4444555566667777", "Maria Kowalczyk", "Półroczny", "Ulgowy", "2024-01-01", "2024-06-30", 300.00),
            
            # Bilety przeterminowane
            ("5555666677778888", "Adam Nowicki", "Miesięczny", "Normalny", "2024-01-01", "2024-01-31", 120.00),
            ("6666777788889999", "Ewa Kaczmarek", "90-dniowy", "Ulgowy", "2023-12-01", "2024-02-28", 160.00),
            
            # Bilety przyszłe
            ("7777888899990000", "Tomasz Lewandowski", "Roczny", "Normalny", "2024-04-01", "2025-03-31", 1100.00),
            ("8888999900001111", "Katarzyna Zielińska", "Półroczny", "Normalny", "2024-04-01", "2024-09-30", 600.00),
            
            # Dodatkowe bilety różnego typu
            ("9999000011112222", "Marcin Szymański", "Miesięczny", "Ulgowy", "2024-03-15", "2024-04-14", 60.00),
            ("0000111122223333", "Alicja Dąbrowska", "90-dniowy", "Normalny", "2024-03-01", "2024-05-29", 320.00),
            ("1111222233334445", "Robert Wójcik", "Roczny", "Ulgowy", "2024-03-01", "2025-02-28", 550.00),
            ("3333444455556667", "Krzysztof Jasiński", "Miesięczny", "Normalny", "2024-03-01", "2024-03-31", 120.00),
            ("4444555566667778", "Karolina Zając", "Miesięczny", "Ulgowy", "2024-03-01", "2024-03-31", 60.00),
            ("5555666677778889", "Wojciech Kowalczyk", "90-dniowy", "Normalny", "2024-02-01", "2024-04-30", 320.00),
            ("6666777788889990", "Klaudia Wiśniewska", "Półroczny", "Ulgowy", "2024-01-01", "2024-06-30", 300.00),
            ("7777888899990001", "Michał Nowak", "Miesięczny", "Normalny", "2024-01-01", "2024-01-31", 120.00),
            ("8888999900001112", "Kamila Kowalczyk", "90-dniowy", "Ulgowy", "2023-12-01", "2024-02-28", 160.00),
            ("9999000011112223", "Kamil Nowicki", "Roczny", "Normalny", "2024-04-01", "2025-03-31", 1100.00),
            ("0000111122223334", "Klaudia Kaczmarek", "Półroczny", "Normalny", "2024-04-01", "2024-09-30", 600.00),
            ("1111222233334446", "Michał Lewandowski", "Miesięczny", "Ulgowy", "2024-03-15", "2024-04-14", 60.00),
            ("2222333344445557", "Kamila Zielińska", "90-dniowy", "Normalny", "2024-03-01", "2024-05-29", 320.00),
        ]
        
        query.prepare("""
            INSERT INTO tickets (card_id, customer_name, ticket_type, discount_type, 
                            valid_from, valid_to, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        for record in test_data:
            for value in record:
                query.addBindValue(value)
            if not query.exec_():
                print(f"Błąd podczas wstawiania rekordu: {query.lastError().text()}")
        
        QSqlDatabase.database().commit()

def createConnection():
    """Tworzy połączenie z bazą danych SQLite, metoda poza klasą"""
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName("tickets.sqlite")
    if not con.open():
        QMessageBox.critical(
            None,
            "Zarządzanie biletami - Błąd!",
            "Błąd bazy danych: %s" % con.lastError().databaseText(),
        )
        return False
    return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not createConnection():
        sys.exit(1)
    win = Tickets()
    win.show()
    sys.exit(app.exec_())