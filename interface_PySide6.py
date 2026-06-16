# Librairies

import sys

from Warren_lib import Warren

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QComboBox,
    QLabel,
    QLineEdit,
    QStackedLayout,
    QFrame
)

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def _fig_cla(self):
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ---- Paramètres de base
        self.setWindowTitle("Pont Warren Calculateur")
        self.resize(1300, 800)

        # ---- Valeurs par défaut
        self.supports = {}
        self.pont = Warren()

        # ---- Layout de la page
        self._init_ui()

    def _init_ui(self):

        # Définition de la base de la page
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        # Pour éviter que la page "flotte"
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Ajout d'un barre sur le coté
        self._init_sidebar() 
        # Ajout du contenu à droite de la barre
        self._init_content()
    
    def _init_sidebar(self):

        # Définition sidebar
        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(20)
        self.sidebar.setContentsMargins(0, 20, 0, 20)
        # Comportement de la sidebar
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(self.sidebar)
        self.sidebar_widget.setFixedWidth(225)
        self.sidebar_widget.setObjectName("sidebar")

        # Définition des boutons sidebar
        self.button_variables = QPushButton("Variables")
        self.button_plots = QPushButton("Graphiques")
        self.button_verification = QPushButton("Vérifications")
        self.button_unites = QPushButton("Unités")

        self.choix_graphique = QComboBox()

        self.compute_text = QLabel("En attente de calcul")
        self.compute_text.setObjectName("compute_text")
        self.compute_text.setWordWrap(True) # Retours à la ligne

        self.button_compute = QPushButton("Calculer structure")
        self.button_compute.clicked.connect(self._compute)
        self.button_compute.setObjectName("compute")

        self.button_clear = QPushButton("Réinitialiser")
        self.button_clear.clicked.connect(self._clear)
        self.button_clear.setObjectName("compute")

        # ajout des boutons dans la sidebar
        self.sidebar.addWidget(self.button_variables)
        self.sidebar.addWidget(self.button_plots)
        self.sidebar.addWidget(self.choix_graphique)
        self.sidebar.addWidget(self.button_verification)
        self.sidebar.addWidget(self.button_unites)

        self.sidebar_compute_widget = QWidget()
        self.sidebar_compute = QVBoxLayout()
        self.sidebar_compute_widget.setLayout(self.sidebar_compute)

        self.sidebar_compute.setSpacing(20)
        self.sidebar_compute.setContentsMargins(10, 20, 10, 20)

        self.sidebar_compute.addWidget(self.compute_text)
        self.sidebar_compute.addWidget(self.button_compute)
        self.sidebar_compute.addWidget(self.button_clear)

        self.sidebar.addWidget(self.sidebar_compute_widget)
        # Ajout au main_widget
        self.main_layout.addWidget(self.sidebar_widget)

        # Ajout des options dans le menu déroulant
        self.choix_graphique.addItem("Pont - Base")
        self.choix_graphique.addItem("Vérif - Déplacements Q")
        self.choix_graphique.addItem("Vérif - Déplacements ELS")
        self.choix_graphique.addItem("Vérif - Contraintes N ELU")

        # On leur associe des objets QSS
        self.button_variables.setObjectName("sidebar")
        self.button_plots.setObjectName("sidebar")
        self.button_verification.setObjectName("sidebar")
        self.button_unites.setObjectName("sidebar")

        # Ajout de la fonction du menu déroulant
        self.choix_graphique.currentTextChanged.connect(self._choix_graphique)

    def _clear(self):
        # Redéfinition du pont
        self.pont = Warren(self.choix_type.currentText())
        self.pont.unites(self.choix_unite_E.currentText(), self.choix_unite_rho.currentText(), self.choix_unite_section.currentText())

        # Clear le plot
        self.plot._fig_cla()
        self.plot.draw()

        # On remet tous par défaut
        self.compute_text.setText("Pont réinitialisé")
        self.supports = {}

        # Textes vides
        self.up_text = ""
        self.mid_text = ""
        self.bot_text = ""
        self.materiau_section_actuel.setText("Poutres supérieures : "+"\n"+"Poutres diagonales : "+"\n"+"Poutres inférieures : ")
        self.label_FQ.setText("En attente de vérification")
        self.label_ELS.setText("En attente de vérification")
        self.label_CNELU.setText("En attente de vérification")

        # on remet les couleurs de base pour les vérifications
        self.label_FQ.setProperty("active", "standBy")
        self.label_FQ.style().unpolish(self.label_FQ)
        self.label_FQ.style().polish(self.label_FQ)

        self.label_ELS.setProperty("active", "standBy")
        self.label_ELS.style().unpolish(self.label_ELS)
        self.label_ELS.style().polish(self.label_ELS)

        self.label_CNELU.setProperty("active", "standBy")
        self.label_CNELU.style().unpolish(self.label_CNELU)
        self.label_CNELU.style().polish(self.label_CNELU)

    def _choix_graphique(self, text):

        # Suppression des colorbars existantes
        for ax in self.plot.figure.axes:
            if ax != self.plot.axes:
                ax.remove()

        try:
            if text == "Pont - Base":
                self.plot._fig_cla()
                self.pont.ax_plot_pont_noeuds(self.plot.axes)
                self.plot.figure.tight_layout()
                self.plot.draw()
                self.compute_text.setText("Pont avec noeuds et poutres calculé")
        except (NotImplementedError, AttributeError):
            self.compute_text.setText("Structure non implémentée (h1, h2, h3, L, n)")

        try:
            if text == "Vérif - Déplacements Q":
                try:
                    self.largeur = float(self.input_largeur.text())
                except ValueError:
                    self.compute_text.setText("Valeur de largeur de pont non valide")
                self.plot._fig_cla()
                self.pont.ax_plot_deplacement_Q(self.plot.axes, self.largeur)
                self.plot.figure.tight_layout()
                self.plot.draw()
                self.compute_text.setText("Vérification des déplacements Q calculé")
        except (NotImplementedError, AttributeError):
            self.compute_text.setText("Structure, Supports, matériaux ou sections non implémentée (h1, h2, h3, L, n, largeur, poid plancher, section/matériau)")

        try:
            if text == "Vérif - Déplacements ELS":
                try:
                    self.largeur = float(self.input_largeur.text())
                    self.poid_plancher = float(self.input_poid_plancher.text())
                except ValueError:
                    self.compute_text.setText("Valeur de largeur de pont ou poid de plancher non valide")
                self.plot._fig_cla()
                self.pont.ax_plot_deplacement_ELS(self.plot.axes, self.largeur, self.poid_plancher)
                self.plot.figure.tight_layout()
                self.plot.draw()
                self.compute_text.setText("Vérification des déplacements ELS calculé")
        except (NotImplementedError, AttributeError):
            self.compute_text.setText("Structure, Supports, matériaux ou sections non implémentée (h1, h2, h3, L, n, largeur, poid plancher, section/matériau)")

        try:
            if text == "Vérif - Contraintes N ELU":
                try:
                    self.largeur = float(self.input_largeur.text())
                    self.poid_plancher = float(self.input_poid_plancher.text())
                except ValueError:
                    self.compute_text.setText("Valeur de largeur de pont ou poid de plancher non valide")
                self.plot._fig_cla()
                self.pont.ax_plot_contrainte_normale_ELU(self.plot.axes, self.largeur, self.poid_plancher)
                self.plot.figure.tight_layout()
                self.plot.draw()
                self.compute_text.setText("Vérification des contraintes normales ELU calculé")
        except (NotImplementedError, AttributeError):
            self.compute_text.setText("Structure, Supports, matériaux ou sections non implémentée (h1, h2, h3, L, n, largeur, poid plancher, section/matériau)")


    def _init_content(self):
        # Page 1
        self._init_content_variables()

        # Page 2
        self._init_content_plots()

        # Page 3
        self._init_content_verification()

        # Page 4
        self._init_content_unites()

        # Liens des tabs dans la sidebar
        self._init_tabs()

    def _init_tabs(self):
        # Création de l'élément des tabs
        self.tabs = QStackedLayout()

        # Création des pages
        self.page_variable = QWidget()
        self.page_variable.setObjectName("page_variable")
        self.page_variable.setLayout(self.content_variables)

        self.page_plots = QWidget()
        self.page_plots.setObjectName("page_plots")
        self.page_plots.setLayout(self.content_plots)

        self.page_verification = QWidget()
        self.page_verification.setObjectName("page_verification")
        self.page_verification.setLayout(self.content_verification)

        self.page_unites = QWidget()
        self.page_unites.setObjectName("page_unites")
        self.page_unites.setLayout(self.content_unites)

        # Création du tableau des pages pour les tabs
        self.tabs.addWidget(self.page_variable)
        self.tabs.addWidget(self.page_plots)
        self.tabs.addWidget(self.page_verification)
        self.tabs.addWidget(self.page_unites)

        # Assignation pages-boutons
        self.button_variables.clicked.connect(lambda: (self.tabs.setCurrentIndex(0), self._bouton_actif(self.button_variables)))
        self.button_plots.clicked.connect(lambda: (self.tabs.setCurrentIndex(1), self._bouton_actif(self.button_plots)))
        self.button_verification.clicked.connect(lambda: (self.tabs.setCurrentIndex(2), self._bouton_actif(self.button_verification)))
        self.button_unites.clicked.connect(lambda: (self.tabs.setCurrentIndex(3), self._bouton_actif(self.button_unites)))
        self._bouton_actif(self.button_variables)

        # Ajout au main_widget
        self.main_layout.addLayout(self.tabs)



    def _bouton_actif(self, bouton_actif):
        for bouton in [self.button_variables, self.button_plots, self.button_verification, self.button_unites]:
            bouton.setProperty("active", bouton == bouton_actif)
            bouton.style().unpolish(bouton)
            bouton.style().polish(bouton)



    def _init_content_variables(self):
        self.content_variables = QHBoxLayout()

        # Définition des deux tableau
        self.tableau1 = QVBoxLayout()
        self.tableau2 = QVBoxLayout()

        # Contenu premier tableau
        self._content_variables_tab1()
        
        # Contenu second tableau
        self._content_variables_tab2()

        # Comportement du tableau 1
        self.tableau1_widget = QWidget()
        self.tableau1_widget.setLayout(self.tableau1)
        self.tableau1_widget.setObjectName("tableau1")
        self.tableau1.setSpacing(10)
        self.tableau1.setContentsMargins(28, 10, 28, 10)
        self.tableau1_widget.setMaximumWidth(600)

        # Comportement du tableau 2
        self.tableau2_widget = QWidget()
        self.tableau2_widget.setLayout(self.tableau2)
        self.tableau2_widget.setObjectName("tableau2")
        self.tableau2.setSpacing(10)
        self.tableau2.setContentsMargins(28, 10, 28, 10)

        # Ajout dans content_variables
        self.content_variables.addWidget(self.tableau1_widget)
        self.content_variables.addWidget(self.tableau2_widget)

    def _init_content_plots(self):
        # Box vertical pour mettre la toolbar
        self.content_plots = QVBoxLayout()

        self.plot = MplCanvas(self, width=5, height=4, dpi=100)

        self.toolbar = NavigationToolbar2QT(self.plot, self)

        self.content_plots.addWidget(self.toolbar)
        self.content_plots.addWidget(self.plot)

    def _init_content_verification(self):
        self.content_verification = QVBoxLayout()

        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setObjectName("Section")

        row0 = QHBoxLayout()
        row0.addWidget(QLabel("Largeur du pont = "))
        self.input_largeur = QLineEdit()
        self.input_largeur.setPlaceholderText("Largeur du pont en m (ex: 4.0)")
        row0.addWidget(self.input_largeur)
        self.input_largeur.setMaximumWidth(250)
        row0.addStretch()

        row00 = QHBoxLayout()
        row00.addWidget(QLabel("Poid du plancher du pont = "))
        self.input_poid_plancher = QLineEdit()
        self.input_poid_plancher.setPlaceholderText("Poid du plancher du pont en kN/m^2")
        row00.addWidget(self.input_poid_plancher)
        self.input_poid_plancher.setMaximumWidth(300)
        row00.addStretch()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Type de charge surfacique d'exploitation : "))
        self.choix_charge = QComboBox()
        row1.addWidget(self.choix_charge)
        self.choix_charge.addItem("Standard (~5 kN/m^2)")
        self.choix_charge.addItem("Selon la longueur")
        row1.addStretch()

        row2 = QHBoxLayout()
        self.titre_FQ = QLabel("Flèche max sous charges d'exploitation")
        row2.addWidget(self.titre_FQ)
        self.titre_FQ.setObjectName("titre")
        self.titre_FQ.setMaximumHeight(100)
        self.titre_FQ.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        row3 = QHBoxLayout()
        self.button_FQ = QPushButton("Vérification flèche max sous charges d'exploitation")
        row3.addWidget(self.button_FQ)
        self.button_FQ.clicked.connect(self._verification_fleche_FQ)
        self.label_FQ = QLabel("En attente de vérification")
        self.label_FQ.setMaximumHeight(100)
        self.label_FQ.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row3.addWidget(self.label_FQ)
        self.label_FQ.setObjectName("verification")

        row4 = QHBoxLayout()
        self.titre_ELS = QLabel("Flèche max sous charge permanantes et charges d'exploitation")
        row4.addWidget(self.titre_ELS)
        self.titre_ELS.setObjectName("titre")
        self.titre_ELS.setMaximumHeight(100)
        self.titre_ELS.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        row5 = QHBoxLayout()
        self.button_ELS = QPushButton("Vérification flèche max sous charge permanantes \n et charges d'exploitation (ELS)")
        row5.addWidget(self.button_ELS)
        self.button_ELS.clicked.connect(self._verification_fleche_ELS)
        self.label_ELS = QLabel("En attente de vérification")
        self.label_ELS.setMaximumHeight(100)
        self.label_ELS.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row5.addWidget(self.label_ELS)
        self.label_ELS.setObjectName("verification")

        row6 = QHBoxLayout()
        self.titre_CNELU = QLabel("Contraintes normales sous charge permanantes et charges d'exploitation avec coefficients (ELU)")
        row6.addWidget(self.titre_CNELU)
        self.titre_CNELU.setObjectName("titre")
        self.titre_CNELU.setMaximumHeight(100)
        self.titre_CNELU.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)

        row7 = QHBoxLayout()
        self.button_CNELU = QPushButton("Vérification sigma max sous charge permanantes \n et charges d'exploitation avec coefficients (ELU)")
        row7.addWidget(self.button_CNELU)
        self.button_CNELU.clicked.connect(self._verification_CNELU)
        self.label_CNELU = QLabel("En attente de vérification")
        self.label_CNELU.setMaximumHeight(100)
        self.label_CNELU.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row7.addWidget(self.label_CNELU)
        self.label_CNELU.setObjectName("verification")

        self.content_verification_layout = QVBoxLayout()
        
        self.content_verification_layout.addWidget(line0)
        self.content_verification_layout.addLayout(row0)
        self.content_verification_layout.addLayout(row00)
        self.content_verification_layout.addLayout(row1)
        self.content_verification_layout.addLayout(row2)
        self.content_verification_layout.addLayout(row3)
        self.content_verification_layout.addLayout(row4)
        self.content_verification_layout.addLayout(row5)
        self.content_verification_layout.addLayout(row6)
        self.content_verification_layout.addLayout(row7)

        self.content_verification_widget = QWidget()
        self.content_verification_widget.setLayout(self.content_verification_layout)

        self.content_verification.addWidget(self.content_verification_widget)
        self.content_verification.setSpacing(10)
        self.content_verification.setContentsMargins(28, 10, 28, 10)



    def _init_content_unites(self):
        self.content_unites = QVBoxLayout()

        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setObjectName("Section")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Unité de mesure du module d'élasticité E : "))
        self.choix_unite_E = QComboBox()
        row1.addWidget(self.choix_unite_E)
        self.choix_unite_E.addItem("MPa")
        self.choix_unite_E.addItem("GPa")
        row1.addStretch()
        self.choix_unite_E.currentTextChanged.connect(self._changement_unite)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Unité de mesure de la masse volumique rho : "))
        self.choix_unite_rho = QComboBox()
        row2.addWidget(self.choix_unite_rho)
        self.choix_unite_rho.addItem("kg/m^3")
        self.choix_unite_rho.addItem("t/m^3")
        row2.addStretch()
        self.choix_unite_rho.currentTextChanged.connect(self._changement_unite)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Unité de mesure de la section du matériau d, e et h: "))
        self.choix_unite_section = QComboBox()
        row3.addWidget(self.choix_unite_section)
        self.choix_unite_section.addItem("mm")
        self.choix_unite_section.addItem("m")
        row3.addStretch()
        self.choix_unite_section.currentTextChanged.connect(self._changement_unite)

        self.content_unites.addWidget(line0)
        self.content_unites.addLayout(row1)
        self.content_unites.addLayout(row2)
        self.content_unites.addLayout(row3)

        self.content_unites.setSpacing(10)
        self.content_unites.setContentsMargins(28, 10, 28, 10)



    def _changement_unite(self):
        # On clear le pont pour le reprendre avec les bonnes unités
        self._clear()

        if self.choix_unite_E.currentText() == "MPa":
            self.input_E.setPlaceholderText("Module d'élasticité du matériau en MPa (ex: 70e3)")
        elif self.choix_unite_E.currentText() == "GPa":
            self.input_E.setPlaceholderText("Module d'élasticité du matériau en GPa (ex: 70)")

        if self.choix_unite_rho.currentText() == "kg/m^3":
            self.input_rho.setPlaceholderText("Masse volumique en kg/m^3 (ex: 2.7e3)")
        elif self.choix_unite_rho.currentText() == "t/m^3":
            self.input_rho.setPlaceholderText("Masse volumique en t/m^3 (ex: 2.7)")

        # on appelle la focntion des sections car elle change les placeholder
        self._choix_section(self.input_choix_section.currentText())



    def _verification_fleche_FQ(self):
        try:
            self.largeur = float(self.input_largeur.text())
        except ValueError:
            self.compute_text.setText("Valeur de la largeur non valide")
            
        try:
            if self.choix_charge.currentText() == "Standard (~5 kN/m^2)":
                maxFQ, is_good = self.pont.verification_fleche_Q(self.largeur)
            
            elif self.choix_charge.currentText() == "Selon la longueur":
                charge_exploitation = (2 + 120/(self.L+30))
                maxFQ, is_good = self.pont.verification_fleche_Q(self.largeur, charge_exploitation)

            maxi = self.pont.L/self.pont.denominateur_Q

            if is_good == True:
                self.label_FQ.setText(f"Flèche maximum : {maxFQ*10**3:.2f} mm < {maxi*10**3:.2f} mm")

                self.label_FQ.setProperty("active", "true")
                self.label_FQ.style().unpolish(self.label_FQ)
                self.label_FQ.style().polish(self.label_FQ)
            else:
                self.label_FQ.setText(f"Flèche maximum : {maxFQ*10**3:.2f} mm > {maxi*10**3:.2f} mm")

                self.label_FQ.setProperty("active", "false")
                self.label_FQ.style().unpolish(self.label_FQ)
                self.label_FQ.style().polish(self.label_FQ)

        except AttributeError:
            self.compute_text.setText("Vous devez implémenter la largeur du pont, la structure, les supports, les matériaux et les sections")



    def _verification_fleche_ELS(self):
        try:
            self.largeur = float(self.input_largeur.text())
            self.poid_plancher = float(self.input_poid_plancher.text())
        except ValueError:
            self.compute_text.setText("Valeur de la largeur ou du poid plancher non valide")
            
        try:
            if self.choix_charge.currentText() == "Standard (~5 kN/m^2)":
                maxFELS, is_good = self.pont.verification_fleche_ELS(self.largeur, self.poid_plancher)
            
            elif self.choix_charge.currentText() == "Selon la longueur":
                charge_exploitation = (2 + 120/(self.L+30))
                maxFELS, is_good = self.pont.verification_fleche_ELS(self.largeur, self.poid_plancher, charge_exploitation)

            maxi = self.pont.L/self.pont.denominateur_ELS

            if is_good == True:
                self.label_ELS.setText(f"Flèche maximum : {maxFELS*10**3:.2f} mm < {maxi*10**3:.2f} mm")

                self.label_ELS.setProperty("active", "true")
                self.label_ELS.style().unpolish(self.label_ELS)
                self.label_ELS.style().polish(self.label_ELS)
            else:
                self.label_ELS.setText(f"Flèche maximum : {maxFELS*10**3:.2f} mm > {maxi*10**3:.2f} mm")

                self.label_ELS.setProperty("active", "false")
                self.label_ELS.style().unpolish(self.label_ELS)
                self.label_ELS.style().polish(self.label_ELS)

        except AttributeError:
            self.compute_text.setText("Vous devez implémenter la largeur du pont, le poid du plancher, la structure, les supports, les matériaux et les sections")



    def _verification_CNELU(self):
        try:
            self.largeur = float(self.input_largeur.text())
            self.poid_plancher = float(self.input_poid_plancher.text())
        except ValueError:
            self.compute_text.setText("Valeur de la largeur ou du poid plancher non valide")
                
        try:
            if self.choix_charge.currentText() == "Standard (~5 kN/m^2)":
                maxsigma, is_good = self.pont.verification_contrainte_normale_ELU(self.largeur, self.poid_plancher)
            
            elif self.choix_charge.currentText() == "Selon la longueur":
                charge_exploitation = (2 + 120/(self.L+30))*10**3
                maxsigma, is_good = self.pont.verification_contrainte_normale_ELU(self.largeur, self.poid_plancher, charge_exploitation)

            maxi = self.pont.sigma_max_ELU
            
            if is_good == True:
                self.label_CNELU.setText(f"Sigma maximum : {maxsigma:.2f} MPa < {maxi:.2f} MPa")

                self.label_CNELU.setProperty("active", "true")
                self.label_CNELU.style().unpolish(self.label_CNELU)
                self.label_CNELU.style().polish(self.label_CNELU)
            else:
                self.label_CNELU.setText(f"Sigma maximum : {maxsigma:.2f} MPa > {maxi:.2f} MPa")

                self.label_CNELU.setProperty("active", "false")
                self.label_CNELU.style().unpolish(self.label_CNELU)
                self.label_CNELU.style().polish(self.label_CNELU)

        except AttributeError:
            self.compute_text.setText("Vous devez implémenter la largeur du pont, le poid du plancher, la structure, les supports, les matériaux et les sections")



    def _content_variables_tab1(self):
        # Menu déroulant type
        row0 = QHBoxLayout()
        row0.addWidget(QLabel("Pont de type : "))
        self.choix_type = QComboBox()
        row0.addWidget(self.choix_type)
        row0.addStretch()
        
        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setObjectName("Section")

        # Entrée texte h1
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("h1 ="))
        self.input_h1 = QLineEdit()
        self.input_h1.setPlaceholderText("hauteur à la flèche en m (ex: 5.0) ")
        row1.addWidget(self.input_h1)   

        # Entrée texte h2
        row12 = QHBoxLayout()
        row12.addWidget(QLabel("h2 ="))
        self.input_h2 = QLineEdit()
        self.input_h2.setPlaceholderText("hauteur basse des extrémitées de la partie parabolique en m (ex: 3.5)")
        row12.addWidget(self.input_h2)    

        # Entrée texte h3
        row13 = QHBoxLayout()
        row13.addWidget(QLabel("h3 ="))
        self.input_h3 = QLineEdit()
        self.input_h3.setPlaceholderText("hauteur de l'extrémité droite de la parabole non sym en m (ex: 3.5)")
        row13.addWidget(self.input_h3)   
        
        # Entrée texte L
        row14 = QHBoxLayout()
        row14.addWidget(QLabel("L ="))
        self.input_L = QLineEdit()
        self.input_L.setPlaceholderText("Longueur du pont en m (ex: 10.0)")
        row14.addWidget(self.input_L)   

        # Entrée texte n
        row15 = QHBoxLayout()
        row15.addWidget(QLabel("n ="))
        self.input_n = QLineEdit()
        self.input_n.setPlaceholderText("nombre de noeuds sur la partie inférieure du pont (ex: 7)")
        row15.addWidget(self.input_n)  

        
        

        # Ajoute au premier tableau
        self.tableau1.addWidget(line0)
        self.tableau1.addLayout(row0)
        self.tableau1.addLayout(row1)
        self.tableau1.addLayout(row12)
        self.tableau1.addLayout(row13)
        self.tableau1.addLayout(row14)
        self.tableau1.addLayout(row15)

        # Appel des fonctions qui vont lier nos entrées
        self._init_choix_type()


    def _choix_section(self, text):
        if text == "tube" and self.choix_unite_section.currentText() == "mm":
            self.input_h.setDisabled(True)
            self.input_h.setPlaceholderText("Vous êtes en section de type tube")
            self.input_d.setPlaceholderText("diamètre du tube en mm (ex: 200)")
            self.input_e.setPlaceholderText("épaisseur du tube en mm (ex: 8)")
        elif text == "rectangle" and self.choix_unite_section.currentText() == "mm":
            self.input_h.setDisabled(False)
            self.input_h.setPlaceholderText("largeur du rectangle en mm (ex: 150)")
            self.input_d.setPlaceholderText("longueur du rectangle en mm (ex: 200)")
            self.input_e.setPlaceholderText("épaisseur du rectangle en mm (ex: 10)")

        if text == "tube" and self.choix_unite_section.currentText() == "m":
            self.input_h.setDisabled(True)
            self.input_h.setPlaceholderText("Vous êtes en section de type tube")
            self.input_d.setPlaceholderText("diamètre du tube en m (ex: 0.2)")
            self.input_e.setPlaceholderText("épaisseur du tube en m (ex: 8e-3)")
        elif text == "rectangle" and self.choix_unite_section.currentText() == "m":
            self.input_h.setDisabled(False)
            self.input_h.setPlaceholderText("largeur du rectangle en m (ex: 0.15)")
            self.input_d.setPlaceholderText("longueur du rectangle en m (ex: 0.2)")
            self.input_e.setPlaceholderText("épaisseur du rectangle en m (ex: 1e-2)")

    def _add_material_section(self):
        
        try:
            if self.input_choix_endroit.currentText() == "inférieures":
                self.pont.set_materials_bottom(float(self.input_E.text()), float(self.input_rho.text()))
                
                if self.input_choix_section.currentText() == "tube":
                    self.pont.set_section_bottom(float(self.input_d.text()), float(self.input_e.text()))
                
                elif self.input_choix_section.currentText() == "rectangle":
                    self.pont.set_section_bottom(float(self.input_d.text()), float(self.input_e.text()), float(self.input_h.text()), "rectangle")
                
                self.compute_text.setText("Matériau/Section des poutres basses ajoutées.")
                self.bot_text = f"E = {self.pont.E_vector[0]:.1f} MPa, A = {self.pont.A_vector[0]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.materiau_section_actuel.setText("Poutres supérieures : "+self.up_text+"\n"+"Poutres diagonales : "+self.mid_text+"\n"+"Poutres inférieures : "+self.bot_text)
            
            if self.input_choix_endroit.currentText() == "diagonales":
                self.pont.set_materials_diagonal(float(self.input_E.text()), float(self.input_rho.text()))
                
                if self.input_choix_section.currentText() == "tube":
                    self.pont.set_section_diagonal(float(self.input_d.text()), float(self.input_e.text()))
                
                elif self.input_choix_section.currentText() == "rectangle":
                    self.pont.set_section_diagonal(float(self.input_d.text()), float(self.input_e.text()), float(self.input_h.text()), "rectangle")
                
                self.compute_text.setText("Matériau/Section des poutres diagonales ajoutées.")
                self.mid_text = f"E = {self.pont.E_vector[1]:.1f} MPa, A = {self.pont.A_vector[1]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.materiau_section_actuel.setText("Poutres supérieures : "+self.up_text+"\n"+"Poutres diagonales : "+self.mid_text+"\n"+"Poutres inférieures : "+self.bot_text)
            
            if self.input_choix_endroit.currentText() == "supérieures":
                self.pont.set_materials_top(float(self.input_E.text()), float(self.input_rho.text()))
                
                if self.input_choix_section.currentText() == "tube":
                    self.pont.set_section_top(float(self.input_d.text()), float(self.input_e.text()))
                
                elif self.input_choix_section.currentText() == "rectangle":
                    self.pont.set_section_top(float(self.input_d.text()), float(self.input_e.text()), float(self.input_h.text()), "rectangle")
                
                self.compute_text.setText("Matériau/Section des poutres supérieures ajoutées.")
                self.up_text = f"E = {self.pont.E_vector[2]:.1f} MPa, A = {self.pont.A_vector[2]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.materiau_section_actuel.setText("Poutres supérieures : "+self.up_text+"\n"+"Poutres diagonales : "+self.mid_text+"\n"+"Poutres inférieures : "+self.bot_text)

            if self.input_choix_endroit.currentText() == "toutes":
                self.pont.set_materials_all(float(self.input_E.text()), float(self.input_rho.text()))
                
                if self.input_choix_section.currentText() == "tube":
                    self.pont.set_section_all(float(self.input_d.text()), float(self.input_e.text()))
                
                elif self.input_choix_section.currentText() == "rectangle":
                    self.pont.set_section_all(float(self.input_d.text()), float(self.input_e.text()), float(self.input_h.text()), "rectangle")
                
                self.compute_text.setText("Matériau/Section de toutes les poutres ajoutées.")
                self.up_text = f"E = {self.pont.E_vector[2]:.1f} MPa, A = {self.pont.A_vector[2]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.mid_text = f"E = {self.pont.E_vector[2]:.1f} MPa, A = {self.pont.A_vector[2]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.bot_text = f"E = {self.pont.E_vector[2]:.1f} MPa, A = {self.pont.A_vector[2]:.1f} mm^2 et rho = {self.pont.rho_vector[0]:.1f} kg/m^3."
                self.materiau_section_actuel.setText("Poutres supérieures : "+self.up_text+"\n"+"Poutres diagonales : "+self.mid_text+"\n"+"Poutres inférieures : "+self.bot_text)

        except ValueError:
            self.compute_text.setText("Valeurs de E, rho, d, h ou e invalide.")

    def _content_variables_tab2(self):

        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setObjectName("Section")

        # Entrée choix section
        row16 = QHBoxLayout()
        row16.addWidget(QLabel("Type de section :"))
        self.input_choix_section = QComboBox()
        self.input_choix_section.addItem("tube")
        self.input_choix_section.addItem("rectangle")
        row16.addWidget(self.input_choix_section) 
        self.input_choix_endroit = QComboBox()
        self.input_choix_endroit.addItem("toutes")
        self.input_choix_endroit.addItem("inférieures")
        self.input_choix_endroit.addItem("diagonales")
        self.input_choix_endroit.addItem("supérieures")
        row16.addWidget(QLabel(" aux poutres :"))
        row16.addWidget(self.input_choix_endroit)
        row16.addStretch()
        self.input_choix_section.currentTextChanged.connect(self._choix_section)

        # Entrée texte d
        row17 = QHBoxLayout()
        row17.addWidget(QLabel("d ="))
        self.input_d = QLineEdit()
        self.input_d.setPlaceholderText("diamètre du tube en mm (ex: 200)")
        row17.addWidget(self.input_d) 

        # Entrée texte e
        row18 = QHBoxLayout()
        row18.addWidget(QLabel("e ="))
        self.input_e = QLineEdit()
        self.input_e.setPlaceholderText("épaisseur du tube en mm (ex: 8)")
        row18.addWidget(self.input_e) 

        # Entrée texte h
        row19 = QHBoxLayout()
        row19.addWidget(QLabel("h ="))
        self.input_h = QLineEdit()
        self.input_h.setPlaceholderText("Vous êtes en type de section tube")
        row19.addWidget(self.input_h) 
        self.input_h.setDisabled(True)

        # Entrée texte E
        row20 = QHBoxLayout()
        row20.addWidget(QLabel("E ="))
        self.input_E = QLineEdit()
        self.input_E.setPlaceholderText("Module d'elasticité du matériau en MPa (ex: 70e3)")
        row20.addWidget(self.input_E) 

        # Entrée texte rho
        row21 = QHBoxLayout()
        row21.addWidget(QLabel("rho ="))
        self.input_rho = QLineEdit()
        self.input_rho.setPlaceholderText("Masse volumique en kg/m^3 (ex: 2.7e3)")
        row21.addWidget(self.input_rho) 

        # Bouton ajouter les matériaux/sections
        row22 = QHBoxLayout()
        self.compute_section = QPushButton("Ajouter matériau/section")
        row22.addWidget(self.compute_section) 
        self.compute_section.clicked.connect(self._add_material_section)

        # Affichage des matériaux/sections
        row23 = QHBoxLayout()
        self.up_text = ""
        self.mid_text = ""
        self.bot_text = ""
        self.materiau_section_actuel = QLabel("Poutres supérieures : "+self.up_text+"\n"+"Poutres diagonales : "+self.mid_text+"\n"+"Poutres inférieures : "+self.bot_text)
        row23.addWidget(self.materiau_section_actuel)
        self.materiau_section_actuel.setWordWrap(True)
        self.materiau_section_actuel.setMaximumHeight(100)  
        self.materiau_section_actuel.setObjectName("materiau_section")

        

        # Ajout au second tableau
        self.tableau2.addWidget(line0)
        self.tableau2.addLayout(row16)
        self.tableau2.addLayout(row17)
        self.tableau2.addLayout(row18)
        self.tableau2.addLayout(row19)
        self.tableau2.addLayout(row20)
        self.tableau2.addLayout(row21)
        self.tableau2.addLayout(row22)
        self.tableau2.addLayout(row23)

          

    def _init_choix_type(self):
        # Ajout des choix
        self.choix_type.addItem("rectangle")
        self.choix_type.addItem("parabole sym")
        self.choix_type.addItem("parabole non sym")

        # Boucle pour les choix
        self.choix_type.currentTextChanged.connect(self._change_type)
        # Choix de base
        self.input_h2.setDisabled(True)
        self.input_h3.setDisabled(True)
        self.input_h2.setPlaceholderText("Vous êtes en type de pont rectangle")
        self.input_h3.setPlaceholderText("Vous êtes en type de pont rectangle")

    def _change_type(self, text):
        # Récupération du choix
        if text == "rectangle":
            self.input_h2.setDisabled(True)
            self.input_h3.setDisabled(True)
            self.input_h2.setPlaceholderText("Vous êtes en type de pont rectangle")
            self.input_h3.setPlaceholderText("Vous êtes en type de pont rectangle")
        elif text == "parabole sym":
            self.input_h2.setDisabled(False)
            self.input_h3.setDisabled(True)
            self.input_h2.setPlaceholderText("hauteur basse des extrémitées de la partie parabolique en m (ex: 3.0)")
            self.input_h3.setPlaceholderText("Vous êtes en type de pont parabole sym")
        elif text == "parabole non sym":
            self.input_h2.setDisabled(False)
            self.input_h3.setDisabled(False)
            self.input_h2.setPlaceholderText("hauteur de l'extrémité gauche de la parabole non sym en m (ex: 6.0)")
            self.input_h3.setPlaceholderText("hauteur de l'extrémité droite de la parabole non sym en m (ex: 2.5)")
        
        # ---- Redéfinition du pont
        self._clear()

    def _compute(self):        

        try:
            self.L = float(self.input_L.text())
        except ValueError:
            self.compute_text.setText("Valeur de L non valide")

        try:
            self.n = int(self.input_n.text())
        except ValueError:
            self.compute_text.setText("Valeur de n non valide")
        
        try:
            self.h1 = float(self.input_h1.text())
        except ValueError:
            self.compute_text.setText("Valeur de h1 non valide")

        if self.choix_type.currentText() == "rectangle":
            
            try:
                self.pont.set_structure(self.L, self.n, self.h1)
                self.supports = {(0, 0) : "Appui simple", (self.L, 0) : "Articulation"}
                self.pont.set_supports(self.supports)

                self._choix_graphique(self.choix_graphique.currentText())

            except AttributeError:
                self.compute_text.setText("Vous devez rentrer des valeurs pour L, h1, n ainsi que les matériaux et les sections")

        elif self.choix_type.currentText() == "parabole sym":
            try:
                try:
                    self.h2 = float(self.input_h2.text())
                    self.pont.set_structure(self.L, self.n, self.h1, self.h2)
                    self.supports = {(0, 0) : "Appui simple", (self.L, 0) : "Articulation"}
                    self.pont.set_supports(self.supports)

                    self._choix_graphique(self.choix_graphique.currentText())
                except ValueError:
                    self.compute_text.setText("Valeur de h2 non valide")
            except AttributeError:
                self.compute_text.setText("Vous devez rentrer des valeurs pour L, h1, h2, n ainsi que les matériaux et les sections")

        elif self.choix_type.currentText() == "parabole non sym":
            try:
                try:
                    self.h2 = float(self.input_h2.text())
                    self.h3 = float(self.input_h3.text())
                    self.pont.set_structure(self.L, self.n, self.h1, self.h2, self.h3)
                    self.supports = {(0, 0) : "Appui simple", (self.L, 0) : "Articulation"}
                    self.pont.set_supports(self.supports)

                    self._choix_graphique(self.choix_graphique.currentText())
                except ValueError:
                    self.compute_text.setText("Valeur de h2 ou h3 non valide")
            except AttributeError:
                self.compute_text.setText("Vous devez rentrer des valeurs pour L, h1, h2, h3, n ainsi que les matériaux et les sections")
        
          
          
if __name__ == "__main__":
    # ---- Appel de la classe et affichage
    app = QApplication(sys.argv)

    # ---- Style de la page, ressemble à du .css
    app.setStyleSheet("""
                   
                      
                    QMainWindow {
                      background: #1e1e2e;
                      }
                    
                      
                    NavigationToolbar2QT {
                     background: #313244;
                     border-radius: 6px;
                     padding: 12px 12px;
                     }

                      
                    QLabel#compute_text {
                      font-size: 15px;
                     }
                      

                    QWidget#tableau1 {
                      border-right: 2px solid #313244;
                      }

                    
                    QFrame#Section {
                      border: none;
                      border-top: 2px solid #313244;
                      max-height: 2px;
                      }

                      
                    QLabel {
                      font-family: "Consolas";
                      color: #cdd6f4;
                      }

                    QLabel#titre {
                      font-family: "Consolas";
                      color: #cdd6f4;
                      font-size: 14px;
                      border-bottom: 2px solid #313244;
                      border-top: 2px solid transparent;
                      border-left: 2px solid transparent;
                      border-right: 2px solid transparent;
                      }
                    QLabel#verification[active="true"] {
                      border: 2px solid #A8D5BA;
                      }
                    QLabel#verification[active="false"] {
                      border: 2px solid #F4A6A6;
                      }
                    QLabel#verification[active="standBy"] {
                      border: 2px solid transparent;
                      }
                    
                    QLabel#materiau_section {
                      font-family: "Consolas";
                      font-size: 13px;
                      }
                   
                      
                    QWidget#sidebar {
                      background: #181825;
                      }

                      
                    QPushButton {
                      padding: 8px 10px;
                      font-size: 14px;
                      font-family: "Consolas";
                      background: #1e1e2e;
                      color: #cdd6f4;
                      border: 2px solid #89b4fa;
                      border-radius: 8px;
                      }
                    QPushButton:hover {
                      background: #74c7ec;
                      }
                    QPushButton:pressed {
                      background: #b4befe;
                      }

                    QPushButton#sidebar {
                      font-family: "Consolas";
                      background: #181825;
                      border: 2px solid transparent;
                      border-left: 6px solid #313244;
                      padding: 20px 20px;
                      border-radius: 0px;
                      color: #cdd6f4;
                      }
                    QPushButton#sidebar:hover {
                      background: #45475a;
                      }
                    QPushButton#sidebar:pressed {
                      background: #585b70;
                      }
                    QPushButton#sidebar[active="true"] {
                      background: #1e1e2e;
                      border-left: 6px solid #89b4fa;
                      }

                    QPushButton#compute {
                      border: 4px solid #89b4fa;
                      padding: 15px 20px
                      }

                      
                    QLineEdit {
                     padding: 4px 10px;
                     font-size: 12px;
                     font-family: "Consolas";
                     color: #cdd6f4;
                     background: #11111b;
                     border: 1px solid #f5c2e7;
                     border-radius: 8px;
                     }
                    QLineEdit:focus {
                     border: 2px solid #313244;
                     }
                    QLineEdit:disabled {
                     background: #181825;
                     color: #6c7086;
                     border: 2px solid #45475a;
                     }
                      

                    QComboBox {
                     padding: 4px 18px;
                     font-size: 12px;
                     font-family: "Consolas";
                     color: #cdd6f4;
                     background: #1e1e2e;
                     border: 2px solid #313244;
                     border-radius: 8px;
                     }
                    QComboBox:hover {
                     border: 2px solid #89b4fa;
                     }
                    QComboBox:focus {
                     border: 2px solid #89b4fa;
                     }
                    QComboBox::drop-down {
                     border: none;
                     width: 20px;
                     }
                    QComboBox::down-arrow {
                     image: none;
                     border-left: 2px solid transparent;
                     border-right: 2px solid transparent;
                     border-top: 8px solid #6c7086;
                     width: 0px;
                     height: 0px;
                     }
                    QComboBox QAbstractItemView {
                     background: #1e1e2e;
                     color: #cdd6f4;
                     border: 2px solid #313244;
                     border-radius: 8px;
                     selection-background-color: #45475a;
                     selection-color: #89b4fa;
                     padding: 4px;
                     }
                      


                    """)
    
    Main = MainWindow()
    Main.show()

    sys.exit(app.exec())