import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QCheckBox, QVBoxLayout, QWidget, QLineEdit, QLabel, QPushButton, QMessageBox, QRadioButton, QButtonGroup, QHBoxLayout, QGroupBox
from PyQt5.QtGui import QIcon, QFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from rectpack import newPacker
import webbrowser

class PalletizationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.standard_pallet_height = 150  # Standardisierte Höhe der Palette in mm
        self.pallet_width = 800  # Standardbreite der Euro-Palette in mm
        self.pallet_length = 1200   # Standardlänge der Euro-Palette in mm

    def initUI(self):
        self.setWindowTitle('PalPAL')
        self.setWindowIcon(QIcon('icon.ico'))  # Setzen des Fenstersymbols

        # Schriftgröße für Boxentitel
        font = QFont()
        font.setPointSize(12)

        # Palettenhöhe
        self.max_pallet_height = QLineEdit(self)
        self.max_pallet_height.setPlaceholderText('Maximale Palettenhöhe (mm)')
        self.max_pallet_height.returnPressed.connect(self.calculate_and_visualize_palletization)

        pallet_height_layout = QVBoxLayout()
        pallet_height_layout.addWidget(QLabel('Geben Sie die maximale Palettenhöhe ein:'))
        pallet_height_layout.addWidget(self.max_pallet_height)
        pallet_height_group = QGroupBox('Maximale Palettenhöhe')
        pallet_height_group.setFont(font)
        pallet_height_group.setLayout(pallet_height_layout)

        # Palettenauswahl
        self.pallet_radio_group = QButtonGroup(self)
        self.standard_pallet_radio = QRadioButton('Standardpalette (1200x800 mm)')
        self.double_pallet_radio = QRadioButton('Doppelpalette (2400x800 mm)')
        self.custom_pallet_radio = QRadioButton('Individuell')
        self.standard_pallet_radio.setChecked(True)

        self.pallet_radio_group.addButton(self.standard_pallet_radio)
        self.pallet_radio_group.addButton(self.double_pallet_radio)
        self.pallet_radio_group.addButton(self.custom_pallet_radio)

        self.custom_length = QLineEdit(self)
        self.custom_length.setPlaceholderText('Länge (mm)')
        self.custom_length.setEnabled(False)

        self.custom_width = QLineEdit(self)
        self.custom_width.setPlaceholderText('Breite (mm)')
        self.custom_width.setEnabled(False)

        self.pallet_radio_group.buttonClicked.connect(self.toggle_custom_pallet_input)

        pallet_selection_layout = QVBoxLayout()
        pallet_selection_layout.addWidget(self.standard_pallet_radio)
        pallet_selection_layout.addWidget(self.double_pallet_radio)
        
        custom_pallet_layout = QHBoxLayout()
        custom_pallet_layout.addWidget(self.custom_pallet_radio)
        custom_pallet_layout.addWidget(self.custom_length)
        custom_pallet_layout.addWidget(self.custom_width)
        pallet_selection_layout.addLayout(custom_pallet_layout)
        
        pallet_selection_group = QGroupBox('Palettenmaß')
        pallet_selection_group.setFont(font)
        pallet_selection_group.setLayout(pallet_selection_layout)

        # Teileabmessungen
        self.input_length = QLineEdit(self)
        self.input_length.setPlaceholderText('Länge des Teils (mm)')
        self.input_length.returnPressed.connect(self.calculate_and_visualize_palletization)

        self.input_width = QLineEdit(self)
        self.input_width.setPlaceholderText('Breite des Teils (mm)')
        self.input_width.returnPressed.connect(self.calculate_and_visualize_palletization)

        self.input_height = QLineEdit(self)
        self.input_height.setPlaceholderText('Höhe des Teils (mm)')
        self.input_height.returnPressed.connect(self.calculate_and_visualize_palletization)

        part_dimensions_layout = QVBoxLayout()
        part_dimensions_layout.addWidget(self.input_length)
        part_dimensions_layout.addWidget(self.input_width)
        part_dimensions_layout.addWidget(self.input_height)

        part_dimensions_group = QGroupBox('Teileabmessungen')
        part_dimensions_group.setFont(font)
        part_dimensions_group.setLayout(part_dimensions_layout)

        # Überstand
        self.overhang_checkbox = QCheckBox('Mit Überstand berechnen', self)
        self.overhang_checkbox.stateChanged.connect(self.toggle_overhang_input)

        self.overhang_input = QLineEdit(self)
        self.overhang_input.setPlaceholderText('Überstand in mm')
        self.overhang_input.setEnabled(False)

        overhang_layout = QVBoxLayout()
        overhang_layout.addWidget(self.overhang_checkbox)
        overhang_layout.addWidget(self.overhang_input)

        overhang_group = QGroupBox('Überstand')
        overhang_group.setFont(font)
        overhang_group.setLayout(overhang_layout)

        # Buttons
        self.calc_button = QPushButton('Palettierung kalkulieren', self)
        self.calc_button.clicked.connect(self.calculate_and_visualize_palletization)

        self.feedback_button = QPushButton('Feedback', self)
        self.feedback_button.clicked.connect(self.send_feedback)

        # Hauptlayout
        main_layout = QVBoxLayout()
        main_layout.addWidget(pallet_height_group)
        main_layout.addWidget(pallet_selection_group)
        main_layout.addWidget(part_dimensions_group)
        main_layout.addWidget(overhang_group)
        main_layout.addWidget(self.calc_button)
        main_layout.addWidget(self.feedback_button)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.part_width = 0
        self.part_length = 0
        self.pack_pieces_per_layer = 0
        self.total_layers = 0
        self.placements = []

    def toggle_overhang_input(self, state):
        self.overhang_input.setEnabled(state == 2)

    def toggle_custom_pallet_input(self):
        custom_enabled = self.custom_pallet_radio.isChecked()
        self.custom_width.setEnabled(custom_enabled)
        self.custom_length.setEnabled(custom_enabled)

    def calculate_and_visualize_palletization(self):
        try:
            max_height = float(self.max_pallet_height.text())
            part_height = float(self.input_height.text())
            part_width = float(self.input_width.text())
            part_length = float(self.input_length.text())
            overhang = float(self.overhang_input.text()) if self.overhang_checkbox.isChecked() else 0

            # Überprüfen, ob die Teileabmessungen gültig sind
            if part_height <= 0 or part_width <= 0 or part_length <= 0:
                QMessageBox.warning(self, 'Eingabefehler', 'Bitte geben Sie ein gültiges Maß größer 0 ein.')
                return
            
            # Abfrage, wenn Teilbreite oder -länge kleiner als 100mm sind
            if part_width < 100 or part_length < 100:
                reply = QMessageBox.question(self, 'Kleine Abmessungen',
                                            'Berechnungen für Teile mit diesen kleinen Maßen dauern unter Umständen etwas länger und benötigen viel Rechenleistung. Möchten Sie fortfahren?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            # Überprüfen der ausgewählten Palettenmaße
            if self.standard_pallet_radio.isChecked():
                self.pallet_width = 800
                self.pallet_length = 1200
            elif self.double_pallet_radio.isChecked():
                self.pallet_width = 800
                self.pallet_length = 2400
            elif self.custom_pallet_radio.isChecked():
                self.pallet_width = float(self.custom_width.text())
                self.pallet_length = float(self.custom_length.text())

            # Palettenmaße inklusive Überhang
            pallet_width_with_overhang = self.pallet_width + overhang * 2
            pallet_length_with_overhang = self.pallet_length + overhang * 2

            # Abfrage, wenn Teilmaße größer als Palettenmaße (inkl. Überhang) sind
            if part_width > pallet_width_with_overhang or part_length > pallet_length_with_overhang:
                QMessageBox.warning(self, 'Teil ist zu groß', 'Das Teil ist zu groß für den ausgewählten Palettentyp. Bitte wählen Sie einen anderen Palettentyp aus, oder benutzen Sie die Funktion "Überhang".')
                return

        except ValueError:
            QMessageBox.warning(self, 'Eingabefehler', 'Bitte geben Sie gültige Zahlen für alle Felder ein.')
            return

        if max_height < self.standard_pallet_height:
            QMessageBox.warning(self, 'Höhenfehler', 'Die maximale Palettenhöhe muss mindestens der Standardpalettenhöhe (150 mm) entsprechen.')
            return

        available_height = max_height - self.standard_pallet_height
        self.total_layers = int(available_height // part_height)

        if self.total_layers <= 0:
            QMessageBox.warning(self, 'Berechnungsfehler', 'Die Höhe des Teils ist zu groß für die angegebene maximale Palettenhöhe.')
            return

        # Berechnung der maximalen Anzahl an Teilen in beiden Orientierungen
        pallet_width = self.pallet_width + overhang * 2
        pallet_length = self.pallet_length + overhang * 2

        num_standard = int((pallet_width // part_width) * (pallet_length // part_length))
        num_rotated = int((pallet_width // part_length) * (pallet_length // part_width))

        # Wählen Sie die beste Option zwischen rotierten und standard-gelegten Teilen
        if num_standard >= num_rotated:
            self.part_width = part_width
            self.part_length = part_length
            allow_rotation = False
        else:
            self.part_width = part_length
            self.part_length = part_width
            allow_rotation = True

        self.placements = []
        packer = newPacker(rotation=True)

        # Palettenbereich hinzufügen
        packer.add_bin(pallet_width, pallet_length, count=1)

        # Teile zur Palette hinzufügen
        for _ in range(self.total_layers):
            for _ in range(max(num_standard, num_rotated)):
                packer.add_rect(self.part_width, self.part_length)

        # Packen
        packer.pack()

        # Ergebnisse sammeln
        self.placements = [(rect.x, rect.y, rect.width, rect.height) for abin in packer for rect in abin]

        total_pack_pieces = len(self.placements)
        if self.total_layers > 0:
            self.pack_pieces_per_layer = total_pack_pieces
            self.total_pack_pieces = total_pack_pieces * self.total_layers
        else:
            self.pack_pieces_per_layer = 0
            self.total_pack_pieces = 0

        self.visualize_palletization()

    def visualize_palletization(self):
        fig, ax = plt.subplots()

        pallet_width = self.pallet_width + (float(self.overhang_input.text()) if self.overhang_checkbox.isChecked() else 0) * 2
        pallet_length = self.pallet_length + (float(self.overhang_input.text()) if self.overhang_checkbox.isChecked() else 0) * 2

        ax.set_xlim(0, pallet_width)
        ax.set_ylim(0, pallet_length)
        ax.set_aspect('equal', 'box')  # Ensures equal scaling for both axes
        ax.set_title('Palettierungsvisualisierung')

        # Zeichnen Sie die ausgewählte Palette
        selected_pallet_rect = patches.Rectangle((0, 0), self.pallet_width, self.pallet_length, linewidth=2, edgecolor='red', facecolor='none', linestyle='dashed')
        ax.add_patch(selected_pallet_rect)

        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

        for idx, (x, y, w, h) in enumerate(self.placements):
            color = colors[idx % len(colors)]
            rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=color, alpha=0.5)
            ax.add_patch(rect)
            ax.text(x + w / 2, y + h / 2, f'{idx}', ha='center', va='center', color='black')

        plt.subplots_adjust(bottom=0.25)  # Platz für den Text unterhalb der Visualisierung

        # Ergebnisse unterhalb der Visualisierung anzeigen
        result_text = (
            f"Anzahl der Lagen: {self.total_layers}\n"
            f"Teile je Lage: {self.pack_pieces_per_layer}\n"
            f"Gesamtanzahl Teile: {self.total_pack_pieces}"
        )
        plt.figtext(0.5, 0.01, result_text, wrap=True, horizontalalignment='center', fontsize=12, bbox=dict(facecolor='white', alpha=0.5))

        plt.show()
 
    def send_feedback(self):
        subject = "PalPAL - Feedback: "
        recipient = "maximilian_seidlitz@icloud.com"
        url = f"mailto:{recipient}?subject={subject}"
        webbrowser.open(url)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))  # Setzen des Anwendungsicons
    ex = PalletizationApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
