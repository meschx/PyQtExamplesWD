import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QComboBox, QFileDialog, 
                            QLineEdit, QLabel, QTabWidget, QCheckBox, QMessageBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.stats import linregress

class PlotTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.data_sets = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        control_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Wczytaj dane")
        self.load_button.clicked.connect(self.load_data)
        control_layout.addWidget(self.load_button)
        
        self.plot_type = QComboBox()
        self.plot_type.addItems(["Liniowy", "Punktowy", "Słupkowy", "Histogram"])
        self.plot_type.currentIndexChanged.connect(self.update_plot)
        control_layout.addWidget(self.plot_type)
        
        self.regression_check = QCheckBox("Regresja liniowa")
        self.regression_check.stateChanged.connect(self.update_plot)
        control_layout.addWidget(self.regression_check)
        
        layout.addLayout(control_layout)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Tytuł wykresu")
        self.x_label = QLineEdit()
        self.x_label.setPlaceholderText("Etykieta osi X")
        self.y_label = QLineEdit()
        self.y_label.setPlaceholderText("Etykieta osi Y")
        
        layout.addWidget(self.title_edit)
        layout.addWidget(self.x_label)
        layout.addWidget(self.y_label)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
    def load_data(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Wybierz pliki", "", 
                                                  "Pliki tekstowe (*.txt *.csv)")
        if filenames:
            colors = ['red', 'blue', 'green', 'orange', 'purple']
            for i, filename in enumerate(filenames):
                try:
                    df = pd.read_csv(filename, header=None)
                    self.data_sets[filename] = {
                        'data': df,
                        'color': colors[i % len(colors)]
                    }
                except Exception as e:
                    QMessageBox.critical(self, "Błąd", f"Nie można wczytać pliku {filename}: {e}")
            self.update_plot()
    
    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self.stats_label.clear()
        
        plot_type = self.plot_type.currentText()
        
        for name, dataset in self.data_sets.items():
            df = dataset['data']
            color = dataset['color']
            
            if plot_type == "Liniowy":
                ax.plot(df[0], df[1], color=color, label=name)
            elif plot_type == "Punktowy":
                ax.scatter(df[0], df[1], color=color, label=name)
            elif plot_type == "Słupkowy":
                ax.bar(df[0], df[1], color=color, label=name)
            elif plot_type == "Histogram":
                ax.hist(df[1], bins=20, color=color, alpha=0.5, label=name)
                
            if self.regression_check.isChecked() and plot_type in ["Liniowy", "Punktowy"]:
                x = df[0].values
                y = df[1].values
                try:
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)
                    ax.plot(x, slope*x + intercept, color='black', linestyle='--')
                    self.stats_label.setText(
                        f"Regresja: y = {slope:.2f}x + {intercept:.2f}\n"
                        f"R² = {r_value**2:.2f}"
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Błąd regresji", str(e))
        
        ax.set_title(self.title_edit.text())
        ax.set_xlabel(self.x_label.text())
        ax.set_ylabel(self.y_label.text())
        if len(self.data_sets) > 1:
            ax.legend()
            
        self.canvas.draw()
    
    def cleanup(self):
        self.figure.clf()
        self.canvas.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard analityczny")
        self.setGeometry(100, 100, 1000, 800)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True) 
        self.tabs.tabCloseRequested.connect(self.close_tab) 
        self.setCentralWidget(self.tabs)
        
        self.add_tab()
        
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        
        add_tab_button = QPushButton("+")
        add_tab_button.clicked.connect(self.add_tab)
        corner_layout.addWidget(add_tab_button)
        
        emergency_btn = QPushButton("X")
        emergency_btn.clicked.connect(lambda: sys.exit(1))
        corner_layout.addWidget(emergency_btn)
        
        self.tabs.setCornerWidget(corner_widget)
        
    def add_tab(self):
        tab = PlotTab(self)
        self.tabs.addTab(tab, f"Zakładka {self.tabs.count()+1}")
    
    def close_tab(self, index):
        if self.tabs.count() > 1: 
            tab = self.tabs.widget(index)
            tab.cleanup()
            self.tabs.removeTab(index)
    
    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, 'cleanup'):
                tab.cleanup()
        
        QApplication.quit()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())