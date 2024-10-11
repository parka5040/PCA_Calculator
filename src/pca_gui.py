import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QTableView, QStyledItemDelegate,
                             QListWidget, QSplitter, QLineEdit, QListWidgetItem, QAbstractItemView,
                             QRadioButton, QButtonGroup, QDialog)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QMimeData
from PyQt6.QtGui import QColor, QBrush, QDrag
from pandas import read_csv, DataFrame
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from .pca_interface import PCAInterface
from .pca_visualizer import PCAVisualizer

class SelectableHeaderModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.selected_columns = set()
        self._filtered_columns = list(range(self._data.shape[1]))
        self.label_column = None

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return len(self._filtered_columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), self._filtered_columns[index.column()]])
        elif role == Qt.ItemDataRole.BackgroundRole:
            if self._filtered_columns[index.column()] in self.selected_columns:
                return QBrush(QColor(200, 200, 255))
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._data.columns[self._filtered_columns[section]])
            elif role == Qt.ItemDataRole.BackgroundRole:
                if self._filtered_columns[section] == self.label_column:
                    return QBrush(QColor(255, 200, 200))  # Light red for label column
        return None

    def toggle_column_selection(self, column):
        actual_column = self._filtered_columns[column]
        if actual_column == self.label_column:
            return  # Prevent reselection of label column
        if actual_column in self.selected_columns:
            self.selected_columns.remove(actual_column)
        else:
            self.selected_columns.add(actual_column)
        self.layoutChanged.emit()

    def filter_columns(self, filter_text):
        self._filtered_columns = [
            i for i, col in enumerate(self._data.columns)
            if filter_text.lower() in col.lower()
        ]
        self.layoutChanged.emit()

class DraggableTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragEnabled(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(self.model().headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.MoveAction)

class ColumnSelectDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if index.model()._filtered_columns[index.column()] in index.model().selected_columns:
            painter.fillRect(option.rect, QColor(200, 200, 255))
        super().paint(painter, option, index)

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        if event.source() == self:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            super().dropEvent(event)
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            item = self.currentItem()
            if item:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(item.text())
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.MoveAction)

class LabelDropWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setMaximumHeight(50)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            self.clear()  # Remove existing item if any
            self.addItem(event.mimeData().text())
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            item = self.currentItem()
            if item:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(item.text())
                drag.setMimeData(mime_data)
                if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.MoveAction:
                    self.clear()

class PCAPlotWindow(QDialog):
    def __init__(self, figure, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PCA Plot")
        self.setGeometry(100, 100, 1000, 600)
        layout = QVBoxLayout()
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        self.setLayout(layout)
        
class PCACalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCA Calculator")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.df = None
        self.pca_interface = PCAInterface()
        self.pca_visualizer = None
        self.last_pca_columns = None
        self.setup_ui()

    def setup_ui(self):
        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_button = QPushButton("Select File")
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)
        self.layout.addLayout(file_layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search columns...")
        self.search_bar.textChanged.connect(self.filter_columns)
        self.layout.addWidget(self.search_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Data view
        self.table_view = DraggableTableView()
        self.table_view.horizontalHeader().sectionClicked.connect(self.toggle_column_selection)
        splitter.addWidget(self.table_view)

        # Right side layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Selected columns view
        self.selected_columns_list = DraggableListWidget()
        self.selected_columns_list.setMaximumWidth(250)
        self.selected_columns_list.model().rowsMoved.connect(self.update_column_order)
        right_layout.addWidget(QLabel("Selected Columns:"))
        right_layout.addWidget(self.selected_columns_list)

        # Select/Deselect All buttons
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_columns)
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_columns)
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)
        right_layout.addLayout(button_layout)


        # Label Box
        right_layout.addWidget(QLabel("Label Column (Drag and Drop from Table or above Column View):"))
        self.label_drop_area = LabelDropWidget()
        self.label_drop_area.itemChanged.connect(self.label_drop_event)
        right_layout.addWidget(self.label_drop_area)

        splitter.addWidget(right_widget)

        self.layout.addWidget(splitter)

        # Selector buttons
        self.dimension_selector = QButtonGroup(self)
        dimension_layout = QHBoxLayout()
        self.radio_2d = QRadioButton("2D")
        self.radio_3d = QRadioButton("3D")
        self.radio_2d.setChecked(True)
        self.dimension_selector.addButton(self.radio_2d)
        self.dimension_selector.addButton(self.radio_3d)
        self.dimension_selector.buttonClicked.connect(self.update_n_components)
        dimension_layout.addWidget(QLabel("Select visualization dimension:"))
        dimension_layout.addWidget(self.radio_2d)
        dimension_layout.addWidget(self.radio_3d)
        self.layout.addLayout(dimension_layout)

        # Analyze buttons
        analysis_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Run PCA")
        self.analyze_button.clicked.connect(self.run_pca)
        self.visualize_button = QPushButton("Visualize PCA")
        self.visualize_button.clicked.connect(self.visualize)
        analysis_layout.addWidget(self.analyze_button)
        analysis_layout.addWidget(self.visualize_button)
        self.layout.addLayout(analysis_layout)

        self.results_label = QLabel("PCA Information and Results")
        self.layout.addWidget(self.results_label)

    def update_n_components(self, button):
        self.n_components = 3 if button.text() == "3D" else 2

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            self.file_label.setText(file_name)
            self.load_data(file_name)
            
    def label_drop_event(self, event):
        if event.mimeData().hasText():
            label_column = event.mimeData().text()
            self.label_drop_area.clear()
            self.label_drop_area.addItem(label_column)
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

            model = self.table_view.model()
            if isinstance(model, SelectableHeaderModel):
                if model.label_column is not None:
                    model.selected_columns.add(model.label_column)
                if self.label_drop_area.count() > 0:
                    new_label_column = self.df.columns.get_loc(self.label_drop_area.item(0).text())
                    model.label_column = new_label_column
                    model.selected_columns.discard(new_label_column)
                else:
                    model.label_column = None
                model.layoutChanged.emit()
                self.update_selected_columns_list()
        else:
            event.ignore()


    def load_data(self, file_name):
        try:
            self.df = read_csv(file_name)
            model = SelectableHeaderModel(self.df)
            self.table_view.setModel(model)
            delegate = ColumnSelectDelegate(self.table_view)
            self.table_view.setItemDelegate(delegate)
            self.update_selected_columns_list()
            
            self.label_drop_area.dropEvent = self.label_drop_event
        except Exception as e:
            self.results_label.setText(f"Error loading file: {str(e)}")

    def toggle_column_selection(self, logical_index):
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel):
            actual_column = model._filtered_columns[logical_index]
            if actual_column == model.label_column:
                self.label_drop_area.clear()
                model.selected_columns.add(model.label_column)
                model.label_column = None
            else:
                model.toggle_column_selection(logical_index)
            model.layoutChanged.emit()
            self.update_selected_columns_list()
        self.last_pca_columns = None

    def update_selected_columns_list(self):
        self.selected_columns_list.clear()
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel) and self.df is not None:
            selected_column_names = [self.df.columns[i] for i in sorted(model.selected_columns)]
            self.selected_columns_list.addItems(selected_column_names)
        self.last_pca_columns = None


    def update_column_order(self):
        new_order = [self.selected_columns_list.item(i).text() for i in range(self.selected_columns_list.count())]
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel) and self.df is not None:
            model.selected_columns = set(self.df.columns.get_loc(col) for col in new_order)
            model.layoutChanged.emit()

    def filter_columns(self, filter_text):
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel):
            model.filter_columns(filter_text)

    def select_all_columns(self):
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel):
            model.selected_columns = set(range(self.df.shape[1])) - {model.label_column}
            model.layoutChanged.emit()
            self.update_selected_columns_list()

    def deselect_all_columns(self):
        model = self.table_view.model()
        if isinstance(model, SelectableHeaderModel):
            model.selected_columns.clear()
            if model.label_column is not None:
                self.label_drop_area.clear()
                model.label_column = None
            model.layoutChanged.emit()
            self.update_selected_columns_list()

    def run_pca(self, n_components=None):
        if self.df is None:
            self.results_label.setText("No data loaded")
            return False

        model = self.table_view.model()
        if not isinstance(model, SelectableHeaderModel):
            self.results_label.setText("Invalid data model")
            return False

        selected_column_names = [self.df.columns[i] for i in model.selected_columns]
        if not selected_column_names:
            self.results_label.setText("No columns selected for analysis")
            return False

        n_components = 3 if self.radio_3d.isChecked() else 2

        if len(selected_column_names) < n_components:
            self.results_label.setText(f"Not enough columns selected. Please select at least {n_components} columns for {n_components}D PCA.")
            return False

        label_column = self.label_drop_area.item(0).text() if self.label_drop_area.count() > 0 else None
        
        self.pca_interface.load_data(self.df, selected_column_names, label_column)
        results = self.pca_interface.run_pca(n_components)
        
        if results is None or 'n_components' not in results or 'explained_variance_ratio' not in results:
            self.results_label.setText("PCA calculation failed. Please check your data and try again.")
            return False

        analysis_text = f"PCA completed.\n"
        analysis_text += f"Number of components: {results['n_components']}\n"
        analysis_text += f"Explained variance ratio: {[f'{var:.4f}' for var in results['explained_variance_ratio']]}"
        
        self.results_label.setText(analysis_text)
        
        self.pca_visualizer = PCAVisualizer(self.pca_interface)
        self.last_pca_columns = set(selected_column_names)
        return True

    def visualize(self):
        is_3d = self.radio_3d.isChecked()
        n_components = 3 if is_3d else 2

        model = self.table_view.model()
        if not isinstance(model, SelectableHeaderModel):
            self.results_label.setText("Invalid data model")
            return

        current_columns = set([self.df.columns[i] for i in model.selected_columns])
        
        if len(current_columns) < n_components:
            self.results_label.setText(f"Insufficient data for visualization. Select at least {n_components} columns for {n_components}D PCA visualization.")
            return

        # Check if columns have changed or if PCA hasn't been run yet
        if self.pca_visualizer is None or self.last_pca_columns != current_columns or self.pca_interface.pca_calculator.get_n_components() != n_components:
            if not self.run_pca(n_components):
                return

        figure, variance_text = self.pca_visualizer.visualize(is_3d)
        if figure:
            plot_window = PCAPlotWindow(figure, self)
            plot_window.show()
            
            current_text = self.results_label.text()
            self.results_label.setText(f"{current_text}\n\n{variance_text}")
        else:
            self.results_label.setText(f"Unable to create visualization.\n\n{variance_text}")
            