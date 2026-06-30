"""

################ CETTE CLASSE SERT SURTOUT POUR L'UTILISATION DE L'APPLICATION #########################

Librairie de calcul d'un pont Warren grâce à une classe Warren()
Vous pouvez crééer un objet Warren() avec comme argument le type de pont souhaité puis suivre ces étapes :

Utilisation:
    1. Implémenter la structure du pont : .set_structure
    2. Implémenter les matériaux : .set_materials
    3. Implémenter les sections : .set_section
    4. Implémenter les supports : .set_supports
    5. Implémenter les forces (pas obligatoire si vous voulez uniquement faire des vérifications): .set_forces

    Vous pouvez également changer les unités de bases avec .unites
    Les paramètres des normes pour les vérifications sont établies dans parameters.json

Vous pouvez ensuite récupérer :
    1. la matrice de rigidité : .matriceRigidite
    2. le vecteur de déplacements : .vecteursDeplacements
    3. le vecteur d'efforts normaux : .vecteurEfforts

Vous pouvez également afficher le pont :
    1. Pont avec juste poutres et noeuds : .plot_pont_noeud
    2. Pont de base avec forces et supports : .plot_pont
    3. Efforts normaux : .plot_efforts
    4. Déplacements : .plot_deplacements

"""



# #####################################################################################
#                              Librairies
# #####################################################################################



import json
import numpy as np
import scipy as scp
import matplotlib.pyplot as plt
import random as rd
import matplotlib.patches as mpatches



# #####################################################################################
#                              Classes
# #####################################################################################



class ParametersImport():
    def __init__(self, pathToFile=''):
        self.pathToFile = pathToFile

        self._parameters_init()


    def _parameters_init(self):
        with open(self.pathToFile) as file:
            self.parameters = json.load(file)



class Warren():
    """
    Calcul des efforts normaux et déplacement d'un pont Warren

    Parameters
    ----------
    type(default="rectangle"): "rectangle", "parabole sym", "parabole non sym"
        type de pont warren

    """
    def __init__(self, Type="rectangle"):
        types = ["rectangle", "parabole sym", "parabole non sym"]
        if Type not in types:
            raise ValueError("Type mismatch : le type de pont n'est pas pris en charge")
        self.type = Type
        self.nodes = np.array([])
        self.nodes_list = []
        self.nodes_after = []
        self.supports = {}
        self.forces = {}
        self.K = []
        self.F = []
        self.u = []
        self.N = []
        self.N_ELU = []
        self.E_vector = np.zeros(3)
        self.A_vector = np.zeros(3)
        self.rho_vector = np.zeros(3)

        self.unite_E = 1
        self.unite_rho = 1
        self.unite_section = 1
        self.unite_force = 1

        self._init_params()

    def _init_params(self):
        # Configure les paramètres définis dans le json

        file = ParametersImport('parameters.json')
        param = file.parameters
        self.denominateur_Q = param['denominateur_fleche_max_Q']
        self.denominateur_ELS = param['denominateur_fleche_max_ELS']
        self.coef_G_ELU = param['coef_G_ELU']
        self.coef_Q_ELU = param['coef_Q_ELU']
        self.sigma_max_ELU = param['sigma_max_ELU']

        self.classe_I_II_verti_longi_lim_basse = param['classe_I_II_verti_longi_lim_basse']
        self.classe_I_II_verti_longi_lim_haute = param['classe_I_II_verti_longi_lim_haute']

        self.classe_III_verti_longi_lim_basse = param['classe_III_verti_longi_lim_basse']
        self.classe_III_verti_longi_lim_haute = param['classe_III_verti_longi_lim_haute']


    def unites(self, E="MPa", rho="kg/m^3", section="mm", force="N"):
        """
        Permet de changer les unités d'entrée pour la classe

        Parameters
        ----------
        E : str ("MPa" or "GPa")
            Unité du module d'élasticité
        rho : str ("kg/m^3" or "t/m^3")
            Unité de la masse volumique
        section : str ("mm" or "m")
            Unité des mesures de la section du matériau
        force : str ("N" or "kN")
            Unité des forces

        Returns  
        ----------
        None
        """

        if E not in ["MPa", "GPa"]:
            raise ValueError("Type d'unité de E non prise en charge")
        
        if rho not in ["kg/m^3", "t/m^3"]:
            raise ValueError("Type d'unité de rho non prise en charge")

        if section not in ["mm", "m"]:
            raise ValueError("Type d'unité pour les section des matériaux non prise en charge")
        
        if force not in ["kN", "N"]:
            raise ValueError("Type d'unité des forces non prise en charge")


        if E == "GPa":
            self.unite_E = 10**3
        elif E == "MPa":
            self.unite_E = 1

        if rho == "t/m^3":
            self.unite_rho = 10**3
        elif rho == "kg/m^3":
            self.unite_rho = 1

        if section == "m":
            self.unite_section = 10**3
        elif section == "mm":
            self.unite_section = 1
        
        if force == "kN":
            self.unite_force = 10**3
        elif force == "N":
            self.unite_force = 1



    def set_materials_all(self, E, rho):
        """
        Définit le type de matériaux utilisées de la structure 

        Parameters
        ----------
        E : int or float
            Module d'Elasticité en MPa
        rho : int or float
            Masse Volumique en kg/m^3

        Returns  
        ----------
        None

        """
        self.E_vector[0] = E*self.unite_E
        self.E_vector[1] = E*self.unite_E
        self.E_vector[2] = E*self.unite_E
        self.rho_vector[0] = rho*self.unite_rho
        self.rho_vector[1] = rho*self.unite_rho
        self.rho_vector[2] = rho*self.unite_rho
    


    def set_materials_bottom(self, E, rho):
        """
        Définit le type de matériaux utilisées des poutres inférieures

        Parameters
        ----------
        E : int or float
            Module d'Elasticité en MPa
        rho : int or float
            Masse Volumique en kg/m^3

        Returns  
        ----------
        None

        """
        self.E_vector[0] = E*self.unite_E
        self.rho_vector[0] = rho*self.unite_rho



    def set_materials_diagonal(self, E, rho):
        """
        Définit le type de matériaux utilisées des poutres en diagonales

        Parameters
        ----------
        E : int or float
            Module d'Elasticité en MPa
        rho : int or float
            Masse Volumique en kg/m^3

        Returns  
        ----------
        None

        """
        self.E_vector[1] = E*self.unite_E
        self.rho_vector[1] = rho*self.unite_rho



    def set_materials_top(self, E, rho):
        """
        Définit le type de matériaux utilisées des poutres supérieures

        Parameters
        ----------
        E : int or float
            Module d'Elasticité en MPa
        rho : int or float
            Masse Volumique en kg/m^3

        Returns  
        ----------
        None

        """
        self.E_vector[2] = E*self.unite_E
        self.rho_vector[2] = rho*self.unite_rho



    def set_section_bottom(self, d, e, h=None, Type="tube"):
        """
        Définit le type de sections utilisées A par partie de la structure 

        Parameters
        ----------
        d : int or float
            diamètre du tube ou longueur du rectangle en mm
        e : into or float
            épaisseur de la section en mm
        h(default=None) : int or float
            si type="rectangle" : largeur de la section rectangulaire en mm
        type(default="tube") : str
            type de section ("rectangle" or "tube")

        Returns  
        ----------
        None
        """
        types = ["rectangle", "tube"]
        if Type not in types:
            raise ValueError("Type de section non pris en charge")
        
        if Type=="rectangle" and h==None:
            raise ValueError("Vous devez rentrer une valeur de largeur pour une section rectangulaire")
        elif Type=="rectangle" and h!=None:
            d=d*self.unite_section
            e=e*self.unite_section
            h=h*self.unite_section
            self.A_vector[0] = d*h - (d-2*e)*(h-2*e)
        
        if Type=="tube":
            d=d*self.unite_section
            e=e*self.unite_section
            r=d/2
            self.A_vector[0] = np.pi*r**2 - np.pi*(r-e)**2



    def set_section_diagonal(self, d, e, h=None, Type="tube"):
        """
        Définit le type de sections utilisées A par partie de la structure 

        Parameters
        ----------
        d : int or float
            diamètre du tube ou longueur du rectangle en mm
        e : into or float
            épaisseur de la section en mm
        h(default=None) : int or float
            si type="rectangle" : largeur de la section rectangulaire en mm
        type(default="tube") : str
            type de section ("rectangle" or "tube")

        Returns  
        ----------
        None
        """
        types = ["rectangle", "tube"]
        if Type not in types:
            raise ValueError("Type de section non pris en charge")
        
        if Type=="rectangle" and h==None:
            raise ValueError("Vous devez rentrer une valeur de largeur pour une section rectangulaire")
        elif Type=="rectangle" and h!=None:
            d=d*self.unite_section
            e=e*self.unite_section
            h=h*self.unite_section
            self.A_vector[1] = d*h - (d-2*e)*(h-2*e)
        
        if Type=="tube":
            d=d*self.unite_section
            e=e*self.unite_section
            r=d/2
            self.A_vector[1] = np.pi*r**2 - np.pi*(r-e)**2



    def set_section_top(self, d, e, h=None, Type="tube"):
        """
        Définit le type de sections utilisées A par partie de la structure

        Parameters
        ----------
        d : int or float
            diamètre du tube ou longueur du rectangle en mm
        e : into or float
            épaisseur de la section en mm
        h(default=None) : int or float
            si type="rectangle" : largeur de la section rectangulaire en mm
        type(default="tube") : str
            type de section ("rectangle" or "tube")

        Returns  
        ----------
        None
        """
        types = ["rectangle", "tube"]
        if Type not in types:
            raise ValueError("Type de section non pris en charge")
        
        if Type=="rectangle" and h==None:
            raise ValueError("Vous devez rentrer une valeur de largeur pour une section rectangulaire")
        elif Type=="rectangle" and h!=None:
            d=d*self.unite_section
            e=e*self.unite_section
            h=h*self.unite_section
            self.A_vector[2] = d*h - (d-2*e)*(h-2*e)
        
        if Type=="tube":
            d=d*self.unite_section
            e=e*self.unite_section
            r=d/2
            self.A_vector[2] = np.pi*r**2 - np.pi*(r-e)**2



    def set_section_all(self, d, e, h=None, Type="tube"):
        """
        Définit le type de sections utilisées A par partie de la structure 

        Parameters
        ----------
        d : int or float
            diamètre du tube ou longueur du rectangle en mm
        e : into or float
            épaisseur de la section en mm
        h(default=None) : int or float
            si type="rectangle" : largeur de la section rectangulaire en mm
        type(default="tube") : str
            type de section ("rectangle" or "tube")

        Returns  
        ----------
        None
        """
        types = ["rectangle", "tube"]
        if Type not in types:
            raise ValueError("Type de section non pris en charge")
        
        if Type=="rectangle" and h==None:
            raise ValueError("Vous devez rentrer une valeur de largeur pour une section rectangulaire")
        elif Type=="rectangle" and h!=None:
            d=d*self.unite_section
            e=e*self.unite_section
            h=h*self.unite_section
            A = d*h - (d-2*e)*(h-2*e)
            self.A_vector[0] = A
            self.A_vector[1] = A
            self.A_vector[2] = A
        
        if Type=="tube":
            d=d*self.unite_section
            e=e*self.unite_section
            r=d/2
            A = np.pi*r**2 - np.pi*(r-e)**2
            self.A_vector[0] = A
            self.A_vector[1] = A
            self.A_vector[2] = A



    def set_structure(self, L, n, h1=None, h2=None, h3=None):
        """
        Définit le type de pont et les paramètres

        Parameters
        ----------
        L : int or float
            Longueur du pont en mètre
        n : int
            nombre de noeud sur la poutre inférieure
        h1(default=None) : int or float
            si type="rectangle" : hauteur à la flèche de la structure
        h2(default=None) : int or float
            si type="parabole sym" : hauteur des extrémitées du pont pour le calcul de la parabole sym
            si type="parabole non sym" : hauteur de l'extrémité droite pour le calcul de la parabole
        h3(default=None) : int or float
            si type="parabole non sym" : hauteur de l'extrémité droite pour le calcul de la parabole

        Returns  
        ----------
        None

        """
        self.L = L
        self.n_nodes_bottom = n

        if self.type=="parabole sym" and h2 == None:
            raise ValueError("Missing argument h2 : Pas de valeur pour la hauteur des côtés de la parabole sym")
        if self.type=="parabole sym" and h1 == None:
            raise ValueError("Missing argument h1 : Pas de valeur pour la hauteur à la flèche de la parabole sym")
        elif h2 != None and h1 != None:
            self.h1 = h1
            self.h2 = h2
            self.polynome = np.array([h2, -(4/L)*(h2-h1), (4/L**2)*(h2-h1)])

        if self.type=="parabole non sym" and h3 == None:
            raise ValueError("Missing argument h3 : Pas de valeur pour la hauteur du côté droit de la parabole non sym")
        elif self.type=="parabole non sym" and h2 == None:
            raise ValueError("Missing argument h2 : Pas de valeur pour la hauteur du côté gauche de la parabole non sym")
        elif self.type=="parabole non sym" and h1 == None:
            raise ValueError("Missing argument h1 : Pas de valeur pour la hauteur à la flèche de la parabole non sym")
        elif h1!= None and h2 != None and h3 != None:
            self.h1 = h1
            self.h2 = h2
            self.h3 = h3
            self.a=(2/self.L**2)*(self.h3-2*self.h1+self.h2)
            self.polynome = np.array([self.h2, (2/L)*(self.h1-self.h2-self.a*(L**2/4)), self.a])

        if self.type=="rectangle" and h1==None:
            raise ValueError("Missing argument h1 : Pas de valeur pour la hauteru à la flèche")
        elif h1 != None:
            self.h1 = h1

        self._nodes_compute()
    


    def _nodes_compute(self):
        # (Mon choix arbitraire pour simplifier est de noter le noeud en bas a gauche le noeud 0 puis de faire en zig-zag le long des poutres diagonales 
        # c'est a dire que le noeud 1 est celui en haut a gauche puis le noeud 2 est celui a droite du noeud 0...)
        
        length_horizontal_beams = self.L/(self.n_nodes_bottom-1)
        self.length_horizontal_beams = length_horizontal_beams

        self.n_nodes_top = self.n_nodes_bottom - 1
        self.n_nodes_total = self.n_nodes_bottom + self.n_nodes_top

        self.nodes_list = []

        if self.type=="rectangle":
            for i in range(self.n_nodes_total):
                if i%2 == 0:
                    self.nodes_list.append([i//2*length_horizontal_beams, 0]) # si le noeud est paire il est sur la partie inférieure
                else:
                    self.nodes_list.append([length_horizontal_beams/2 + i//2*length_horizontal_beams, self.h1]) # si le noeud est impaire il est sur la partie supérieure

        elif self.type=="parabole sym":
            for i in range(self.n_nodes_total):
                if i%2 == 0:
                    x=i//2*length_horizontal_beams
                    self.nodes_list.append([x, 0]) # si le noeud est paire il est sur la partie inférieure
                else:
                    x=length_horizontal_beams/2 + i//2*length_horizontal_beams
                    y= self.polynome[0]+self.polynome[1]*x+self.polynome[2]*x**2
                    self.nodes_list.append([x, y]) # si le noeud est impaire il est sur la partie supérieure

        elif self.type == "parabole non sym":
            for i in range(self.n_nodes_total):
                if i%2 == 0:
                    x=i//2*length_horizontal_beams
                    self.nodes_list.append([x, 0]) # si le noeud est paire il est sur la partie inférieure
                else:
                    x=length_horizontal_beams/2 + i//2*length_horizontal_beams
                    y= self.polynome[0]+self.polynome[1]*x+self.polynome[2]*x**2
                    self.nodes_list.append([x, y]) # si le noeud est impaire il est sur la partie supérieure

        # Pour calculer la matrice K, il nous faut calculer ki pour chaque poutre et donc chaque couple de noeuds
        # en interaction. Pour cela j'ai choisi de crééer une liste avec chaque couple de noeuds en indiquant leur numéro (0, 1), (0, 2), (1, 2)...
        
        self.beams_nodes = []

        for i in range(self.n_nodes_total-1):
            self.beams_nodes.append([i, i+1])
            if i+2 <= self.n_nodes_total-1:
                self.beams_nodes.append([i, i+2])

        self.beams_nodes = np.array(self.beams_nodes)
        self.nodes = np.array(self.nodes_list)

        self.beams = self.nodes[self.beams_nodes]



    def set_supports(self, supports):
        """
        Définit l'emplacement et le type de support

        Parameters
        ----------
        supports : dict
            keys : tuple avec les coordonnées du noeud (x, y) en m
            values : type de support : "Articulation", "Appui simple"

        Returns  
        ----------
        None

        """
        if len(self.nodes_list) == 0:
            raise NotImplementedError("Vous devez définir la structure du pont avant d'ajouter des supports")
        
        for node in supports:
            if [node[0], node[1]] not in self.nodes_list:
                raise ValueError("Les coordonnées des supports doivent concorder avec les noeuds") 
        
        self.supports = supports



    def set_forces_punc(self, forces):
        """
        Définit l'emplacement et la valeur de la force ponctuelle

        Parameters
        ----------
        dict : dict
            keys : tuple avec les coordonnées du noeud (x, y) en m
            values : puissance de la force (Fx, Fy) en N  

        Returns  
        ----------
        None

        """
        if len(self.nodes_list) == 0:
            raise NotImplementedError("Vous devez définir la structure du pont avant d'ajouter des forces ponctuelles")
        
        force_updated = {}

        for node in forces:
            if [node[0], node[1]] not in self.nodes_list:
                raise ValueError("Les coordonnées des forces ponctuelles doivent concorder avec les noeuds")
            
            force = forces.get(node)
            force_updated.update({(node[0], node[1]) : (force[0]*self.unite_force, force[1]*self.unite_force)})


        self.forces = force_updated

        self._matriceForce()

    

    def _matriceForce(self):
        self.F=np.zeros((2*self.n_nodes_total,1))

        for node in self.forces:
            ni=self.nodes_list.index([node[0], node[1]])
            self.F[2*ni] = self.forces.get(node)[0] # Coordonnées Ux
            self.F[2*ni+1] = self.forces.get(node)[1] # Coordonnées Uy



    def matriceRigidite(self):
        """
        Calcule la matrice de rigidité

        Parameters
        ----------
        None

        Returns
        ----------
        K : np.array
            matrice de rigidité de la structure
        """
        self._matriceRigidite()
        return self.K
    


    def _matriceRigidite(self):
        if self.nodes_list == [] or np.any(self.E_vector == 0) or np.any(self.A_vector == 0):
            raise NotImplementedError("Vous devez implémenter les matériaux, les sections et la structure avant de calculer la matrice K")
        
        K=np.zeros((2*self.n_nodes_total, 2*self.n_nodes_total))

        for node_combo in self.beams_nodes:
            n1i = node_combo[0] # numéro du premier noeud
            n2i = node_combo[1] # numéro du second noeud

            node1 = self.nodes[n1i] # coordonnées du premier noeud
            node2 = self.nodes[n2i] # coordonnées du second noeud

            Li=np.linalg.norm(node2-node1) # taille de la poutre

            c=(node2[0]-node1[0])/Li # cosinus associé à la poutre
            s=(node2[1]-node1[1])/Li # sinus associé à la poutre

            # coefficient devant la matrice K
            if n1i%2 == 0: # premier noeud en bas
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[0]*self.A_vector[0]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
            else: # premier noeud en haut
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[2]*self.A_vector[2]/Li

            # Pour le calcul de la matrice K on a besoin des coordonnées Ux et Uy de chaque noeud car 5 noeuds = 10 vecteurs
            # On multiplie donc par 2 pour les coordonnées Ux et on rajoute 1 pour les coordonnées Uy
            n1i = 2*n1i # coordonnée Ux du premier noeud
            n2i = 2*n2i # coordonnée Ux du second noeud

            # On rajoute directement dans la matrice globale K
            oneone = alpha*c**2
            onetwo = alpha*c*s
            twotwo = alpha*s**2
            # Quadrant 1
            K[n1i, n1i] += oneone
            K[n1i, n1i+1] += onetwo
            K[n1i+1, n1i] += onetwo
            K[n1i+1, n1i+1] += twotwo
            # Quadrant 2
            K[n2i, n1i] -= oneone
            K[n2i, n1i+1] -= onetwo
            K[n2i+1, n1i] -= onetwo
            K[n2i+1, n1i+1] -= twotwo
            # Quadrant 3
            K[n1i, n2i] -= oneone
            K[n1i, n2i+1] -= onetwo
            K[n1i+1, n2i] -= onetwo
            K[n1i+1, n2i+1] -= twotwo
            # Quadrant 4
            K[n2i, n2i] += oneone
            K[n2i, n2i+1] += onetwo
            K[n2i+1, n2i] += onetwo
            K[n2i+1, n2i+1] += twotwo

        self.K = K
    


    def vecteurDeplacement(self):
        """
        Calcule le déplacement des noeuds

        Parameters
        ----------
        None

        Returns
        ----------
        u : np.array
            vecteur de déplacement des noeuds
        """
        self._vecteurDeplacement()
        return self.u
    


    def _vecteurDeplacement(self):
        reduction=[]

        for node in self.supports:
            ni=self.nodes_list.index([node[0], node[1]])
            if self.supports.get(node) == "Appui simple": # Si appui simple seulement Uy = 0
                reduction.append(2*ni+1)
            elif self.supports.get(node) == "Articulation": # Si Articulation alors Ux = Uy = 0
                reduction.append(2*ni)
                reduction.append(2*ni+1)
            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        reduction.sort(reverse=True) 

        self._matriceRigidite()
        
        if len(self.F) == 0:
            raise ValueError("Vous n'avez pas implémenté de forces ponctuelles !")
        
        K_red = np.copy(self.K)
        F_red = np.copy(self.F)

        for i in reduction:
            K_red = np.delete(K_red, i, 0) # suppression de la ligne
            K_red = np.delete(K_red, i, 1) # suppression de la colonne
            F_red = np.delete(F_red, i, 0) # suppression du terme (ligne)

        # vérification
        rank = np.linalg.matrix_rank(K_red)
        if rank < K_red.shape[0]:
            raise ValueError("La matrice K est une singularité, vérifiez les supports")
        
        u = np.linalg.solve(K_red, F_red)

        # On fait maintenant l'inverse de la réduction pour retrouver la taille de base  
        reduction.sort(reverse=False) 
        for i in reduction:
            u = np.insert(u, i, 0)

        self.nodes_after = self.nodes + u.reshape(-1, 2)

        self.u = u



    def vecteurEfforts(self):
        """
        Calcule les efforts normaux des poutres

        Parameters
        ----------
        None

        Returns
        ----------
        N : np.array
            vecteur des efforts normaux des poutres
        """
        self._vecteurEfforts()
        return self.N



    def _vecteurEfforts(self):
        
        self._vecteurDeplacement()

        N=[]

        for node_combo in self.beams_nodes:
            n1i = node_combo[0] # numéro du premier noeud
            n2i = node_combo[1] # numéro du second noeud

            node1 = self.nodes[n1i] # coordonnées du premier noeud
            node2 = self.nodes[n2i] # coordonnées du second noeud

            Li=np.linalg.norm(node2-node1) # taille de la poutre

            c=(node2[0]-node1[0])/Li # cosinus associé à la poutre
            s=(node2[1]-node1[1])/Li # sinus associé à la poutre

            # coefficient
            if n1i%2 == 0: # premier noeud en bas
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[0]*self.A_vector[0]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
            else: # premier noeud en haut
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[2]*self.A_vector[2]/Li

            x1 = 2*n1i
            y1 = x1+1
            x2 = 2*n2i
            y2 = x2+1

            Vect = np.array([-c, -s, c, s])
            Vect = Vect.reshape((1, 4))

            U = np.array([self.u[x1],
                        self.u[y1],
                        self.u[x2],
                        self.u[y2]])
            U = U.reshape((4,1))

            Ni = alpha * Vect@U

            N.append(Ni[0][0])

        self.N = N



    def plot_pont_noeuds(self):
        """
        Affichage des poutres et des noeuds (noeuds, poutres)
        """
        plt.figure()

        if len(self.nodes) == 0:
            raise NotImplementedError("Afin d'afficher le pont, vous devez implémenter la structure.")

        # Plot des noeuds
        plt.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=20, color="r")
        for n, node in enumerate(self.nodes):
            plt.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des poutres
        for n, beam in enumerate(self.beams):
            plt.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.6)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            plt.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color="b", size=6, ha="left") # annotation du numéro des poutres

        plt.grid(True)
        plt.title("Pont en treillis warren")
        
        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()



    def ax_plot_pont_noeuds(self, ax):
        """
        Affichage des poutres et des noeuds sur un axe définit sur un axe donné (noeuds, poutres)

        Parameters
        ------------
        ax : class
            axe matplotlib ou dessiner la figure

        Returns
        ------------
        None
        """

        if len(self.nodes) == 0:
            raise NotImplementedError("Afin d'afficher le pont, vous devez implémenter la structure.")

        # Plot des noeuds
        ax.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=20, color="r")
        for n, node in enumerate(self.nodes):
            ax.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des poutres
        for n, beam in enumerate(self.beams):
            ax.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.6)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            ax.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color="b", size=6, ha="left") # annotation du numéro des poutres

        ax.grid(True)
        ax.set_title("Pont en treillis warren")

        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")

        

    def plot_pont(self):
        """
        Affichage du pont de base (noeuds, poutres, forces et supports)
        """
        plt.figure()

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher le pont, vous devez implémenter la structure, les forces et les supports.")

        # Plot des noeuds
        plt.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=20, color="r")
        for n, node in enumerate(self.nodes):
            plt.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des poutres
        for n, beam in enumerate(self.beams):
            plt.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.6)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            plt.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color="b", size=6, ha="left") # annotation du numéro des poutres

        # Plot des forces
        for node in self.forces:
            if self.type=="parabole non sym":
                scale = max(self.h1, self.h2, self.h3)*2 / 3  / max(np.linalg.norm(force) for force in self.forces.values())
            else:
                scale = self.h1*2 / 3  / max(np.linalg.norm(force) for force in self.forces.values())
            Fi = self.forces.get(node)
            plt.annotate(f"", xytext=(node[0]-Fi[0]*scale, node[1]-Fi[1]*scale), xy=node, arrowprops=dict(arrowstyle='-|>', color='red', linewidth=1.8, linestyle="--"), size=6)
            if self.unite_force == 10**3:
                plt.annotate(f"({Fi[0]*10**(-3):.2f}, {Fi[1]*10**(-3):.2f}) kN", (node[0]-Fi[0]*scale, node[1]-Fi[1]*scale+0.1), size=5, ha="center")
            elif self.unite_force == 1:
                plt.annotate(f"({Fi[0]:.2f}, {Fi[1]:.2f}) N", (node[0]-Fi[0]*scale, node[1]-Fi[1]*scale+0.1), size=5, ha="center")

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = plt.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    plt.gca().add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        plt.grid(True)
        plt.title("Pont en treillis warren")

        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()
    


    def ax_plot_pont(self, ax):
        """
        Affichage du pont de base sur un axe définit sur un axe donné (noeuds, poutres, forces et supports)

        Parameters
        ------------
        ax : class
            axe matplotlib ou dessiner la figure

        Returns
        ------------
        None
        """

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher le pont, vous devez implémenter la structure, les forces et les supports.")

        # Plot des noeuds
        ax.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=20, color="r")
        for n, node in enumerate(self.nodes):
            ax.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des poutres
        for n, beam in enumerate(self.beams):
            ax.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.6)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            ax.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color="b", size=6, ha="left") # annotation du numéro des poutres

        # Plot des forces
        for node in self.forces:
            if self.type=="parabole non sym":
                scale = max(self.h1, self.h2, self.h3)*2 / 3  / max(np.linalg.norm(force) for force in self.forces.values())
            else:
                scale = self.h1*2 / 3  / max(np.linalg.norm(force) for force in self.forces.values())
            Fi = self.forces.get(node)
            ax.annotate(f"", xytext=(node[0]-Fi[0]*scale, node[1]-Fi[1]*scale), xy=node, arrowprops=dict(arrowstyle='-|>', color='red', linewidth=1.8, linestyle="--"), size=6)
            if self.unite_force == 10**3:
                ax.annotate(f"({Fi[0]*10**(-3):.2f}, {Fi[1]*10**(-3):.2f}) kN", (node[0]-Fi[0]*scale, node[1]-Fi[1]*scale+0.1), size=5, ha="center")
            elif self.unite_force == 1:
                ax.annotate(f"({Fi[0]:.2f}, {Fi[1]:.2f}) N", (node[0]-Fi[0]*scale, node[1]-Fi[1]*scale+0.1), size=5, ha="center")

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = mpatches.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    ax.add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        ax.grid(True)
        ax.set_title("Pont en treillis warren")

        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")



    def plot_efforts(self):
        """
        Affichage des efforts normaux des poutres du pont (noeuds, poutres, efforts normaux)
        """
        plt.figure()

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les matériaux, les forces et les supports.")

        self._vecteurEfforts()

        # Plot de l'effort normal des poutres avec colormap
        cmap = plt.cm.jet # jet : bleu -> vert -> rouge
        values_map = plt.Normalize(vmin=min(self.N), vmax=max(self.N)) # création de l'échelle du colorbar

        for n, beam in enumerate(self.beams): 
            plt.plot(beam[:, 0], beam[:, 1], color=cmap(values_map(self.N[n])), linewidth=2.4)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            plt.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color=cmap(values_map(self.N[n])), size=6, ha="left") # annotation du numéro des poutres
            if self.unite_force == 10**3:
                plt.annotate(f"{self.N[n]*10**(-3):.2f} kN", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(self.N[n])), size=5, ha="right")
            elif self.unite_force == 1:
                plt.annotate(f"{self.N[n]:.2f} N", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(self.N[n])), size=5, ha="right") # annotation de l'effort 
        colorbar = plt.cm.ScalarMappable(norm=values_map, cmap=cmap)
        plt.colorbar(colorbar, ax=plt.gca(), label="Effort normal (en N)") # barre à droite

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = plt.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    plt.gca().add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        plt.grid(True)
        plt.title("Efforts normaux des poutres d'un pont en treillis warren")

        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()



    def ax_plot_efforts(self, ax):
        """
        Affichage des efforts normaux des poutres du pont sur un axe donné (noeuds, poutres, efforts normaux)

        Parameters
        ------------
        ax : class
            axe matplotlib ou dessiner la figure

        Returns
        ------------
        None
        """

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les matériaux, les forces et les supports.")

        self._vecteurEfforts()

        # Plot de l'effort normal des poutres avec colormap
        cmap = plt.cm.jet # jet : bleu -> vert -> rouge
        values_map = plt.Normalize(vmin=min(self.N), vmax=max(self.N)) # création de l'échelle du colorbar

        for n, beam in enumerate(self.beams): 
            ax.plot(beam[:, 0], beam[:, 1], color=cmap(values_map(self.N[n])), linewidth=2.4)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            ax.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color=cmap(values_map(self.N[n])), size=6, ha="left") # annotation du numéro des poutres
            if self.unite_force == 10**3:
                ax.annotate(f"{self.N[n]*10**(-3):.2f} kN", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(self.N[n])), size=5, ha="right")
            elif self.unite_force == 1:
                ax.annotate(f"{self.N[n]:.2f} N", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(self.N[n])), size=5, ha="right") # annotation de l'effort 
        colorbar = plt.cm.ScalarMappable(norm=values_map, cmap=cmap)
        plt.colorbar(colorbar, ax=ax, label="Effort normal (en N)") # barre à droite

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = mpatches.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    ax.add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        ax.grid(True)
        ax.set_title("Efforts normaux des poutres d'un pont en treillis warren")
        
        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")



    def plot_deplacements(self):
        """
        Affichage des déplacements des noeuds du ponts (noeuds, poutres, déplacements)
        """
        plt.figure()

        max_u = np.max(np.abs(self.u))
        scale = self.L / (max_u*20)
        nodes_after_scale = self.nodes+self.u.reshape(-1, 2)*scale

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher les déplacements, vous devez implémenter la structure, les matériaux, les forces et les supports.")
        
        self._vecteurDeplacement()

        # Plot des noeuds avant/après
        plt.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=25, c="r")

        plt.scatter(nodes_after_scale[:, 0], nodes_after_scale[:, 1], marker="o", s=25, c="r")
        for n, node in enumerate(nodes_after_scale):
            plt.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des flèches de mesures du déplacement
        for i in range(self.n_nodes_total):
            node = self.nodes[i]
            node_after = self.nodes_after[i]
            node_after_scale = nodes_after_scale[i]
            if np.linalg.norm(node_after-node) != 0:
                plt.annotate("", xytext=node, xy=node_after_scale, arrowprops=dict(arrowstyle='->', color='black', linewidth=1.5, linestyle="--"), size=6)
                plt.annotate(f"({(node_after[0]-node[0])*10**3:.2f}, {(node_after[1]-node[1])*10**3:.2f}) mm", (node_after_scale[0]-0.1, node_after_scale[1]+rd.uniform(0.05, 0.15)), size=5, ha="right")

        # Plot des poutres avant.après
        for n, beam in enumerate(self.beams):
            plt.plot(beam[:, 0], beam[:, 1], "b--", linewidth=0.2)

        beams_after = nodes_after_scale[self.beams_nodes]
        for n, beam in enumerate(beams_after):
            plt.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.8)

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # On récupère le décalage en x
                new_x_pos = self.nodes_list.index([x, y])
                new_x = self.nodes_after[new_x_pos][0]

                # triangle vert
                polygon = np.array([[new_x, y],
                                    [new_x-0.5, y-0.5],
                                    [new_x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)
                # deux rouleaux
                for i in [new_x-0.25, new_x+0.25]:
                    circle = plt.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    plt.gca().add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        plt.grid(True)
        plt.title("Déplacement des noeuds d'un pont en treillis warren")

        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()



    def ax_plot_deplacements(self, ax):
        """
        Affichage des déplacements des noeuds du ponts sur un axe donné (noeuds, poutres, déplacements)

        Parameters
        ------------
        ax : class
            axe matplotlib ou dessiner la figure

        Returns
        ------------
        None
        """

        if len(self.nodes) == 0 or len(self.forces) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin d'afficher les déplacements, vous devez implémenter la structure, les matériaux, les forces et les supports.")
        
        self._vecteurDeplacement()

        max_u = np.max(np.abs(self.u))
        scale = self.L / (max_u*20)
        nodes_after_scale = self.nodes+self.u.reshape(-1, 2)*scale

        # Plot des noeuds avant/après
        ax.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=25, c="r")

        ax.scatter(nodes_after_scale[:, 0], nodes_after_scale[:, 1], marker="o", s=25, c="r")
        for n, node in enumerate(nodes_after_scale):
            ax.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des flèches de mesures du déplacement
        for i in range(self.n_nodes_total):
            node = self.nodes[i]
            node_after = self.nodes_after[i]
            node_after_scale = nodes_after_scale[i]
            if np.linalg.norm(node_after-node) != 0:
                ax.annotate("", xytext=node, xy=node_after_scale, arrowprops=dict(arrowstyle='->', color='black', linewidth=1.5, linestyle="--"), size=6)
                ax.annotate(f"({(node_after[0]-node[0])*10**3:.2f}, {(node_after[1]-node[1])*10**3:.2f}) mm", (node_after_scale[0]-0.1, node_after_scale[1]+rd.uniform(0.05, 0.15)), size=5, ha="right")

        # Plot des poutres avant.après
        for n, beam in enumerate(self.beams):
            ax.plot(beam[:, 0], beam[:, 1], "b--", linewidth=0.2)

        beams_after = nodes_after_scale[self.beams_nodes]
        for n, beam in enumerate(beams_after):
            ax.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.8)

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # On récupère le décalage en x
                new_x_pos = self.nodes_list.index([x, y])
                new_x = self.nodes_after[new_x_pos][0]

                # triangle vert
                polygon = np.array([[new_x, y],
                                    [new_x-0.5, y-0.5],
                                    [new_x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)
                # deux rouleaux
                for i in [new_x-0.25, new_x+0.25]:
                    circle = mpatches.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    ax.add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        ax.grid(True)
        ax.set_title("Déplacement des noeuds d'un pont en treillis warren")

        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")



    def _calcul_force_permanantes(self, largeur, poids_plancher):
        
        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Afin de calculer les forces permanantes, vous devez implémenter la structure, les supports et les matériaux/sections.")
        
        self.F_G = np.zeros((2*self.n_nodes_total, 1))

        for node_combo in self.beams_nodes:
            n1i = node_combo[0] # numéro du premier noeud
            n2i = node_combo[1] # numéro du second noeud

            node1 = self.nodes[n1i] # coordonnées du premier noeud
            node2 = self.nodes[n2i] # coordonnées du second noeud

            Li=np.linalg.norm(node2-node1) # taille de la poutre

            if n1i%2 == 0: # premier noeud en bas
                if n2i%2 == 0: # second noeud en bas
                    section = self.A_vector[0]
                    masse_v = self.rho_vector[0]
                else: # second noeud en haut
                    section = self.A_vector[1]
                    masse_v = self.rho_vector[1]
            else: # premier noeud en haut
                if n2i%2 == 0: # second noeud en bas
                    section = self.A_vector[1]
                    masse_v = self.rho_vector[1]
                else: # second noeud en haut
                    section = self.A_vector[2]
                    masse_v = self.rho_vector[2]

            y1 = 2*n1i+1
            y2 = 2*n2i+1

            P = masse_v*(section*10**(-6))*Li*9.81

            self.F_G[y1] -= P/2
            self.F_G[y2] -= P/2 

        F_p = self.length_horizontal_beams*(largeur/2)*poids_plancher*10**3 # Conversion en N/m^2

        for n in range(len(self.nodes)):
            y=2*n+1

            if n%2==0: # noeud sur la partie basse
                if n==0: # premier noeud du pont
                    self.F_G[y] -= F_p/2
                elif n == self.n_nodes_total-1: # dernier noeud du pont
                    self.F_G[y] -= F_p/2
                else: # noeud au milieu du pont
                    self.F_G[y] -= F_p



    def _calcul_force_exploitation(self, largeur, charge_exploitation):

        if len(self.nodes) == 0 or len(self.supports) == 0:
            raise NotImplementedError("Afin de calculer les forces d'exploitations, vous devez implémenter la structure et les supports.")
            
        self.F_Q = np.zeros((2*self.n_nodes_total, 1))

        F = self.length_horizontal_beams*(largeur/2)*charge_exploitation*10**3 # Conversion en N/m^2

        for n in range(len(self.nodes)):
            y=2*n+1

            if n%2==0: # noeud sur la partie basse
                if n==0: # premier noeud du pont
                    self.F_Q[y] -= F/2
                elif n == self.n_nodes_total-1: # dernier noeud du pont
                    self.F_Q[y] -= F/2
                else: # noeud au milieu du pont
                    self.F_Q[y] -= F



    def _calcul_force_ELS(self, largeur, poids_plancher, charge_exploitation):
        self._calcul_force_exploitation(largeur, charge_exploitation)
        self._calcul_force_permanantes(largeur, poids_plancher)

        self.F_ELS = np.zeros((2*self.n_nodes_total, 1))

        self.F_ELS = self.F_G + self.F_Q



    def _calcul_force_ELU(self, largeur, poids_plancher, charge_exploitation):

        self._calcul_force_exploitation(largeur, charge_exploitation)
        self._calcul_force_permanantes(largeur, poids_plancher)

        self.F_ELU = np.zeros((2*self.n_nodes_total, 1))

        self.F_ELU = self.coef_G_ELU*self.F_G + self.coef_Q_ELU*self.F_Q



    def _vecteurEfforts_general(self, u):

        N=[]

        for node_combo in self.beams_nodes:
            n1i = node_combo[0] # numéro du premier noeud
            n2i = node_combo[1] # numéro du second noeud

            node1 = self.nodes[n1i] # coordonnées du premier noeud
            node2 = self.nodes[n2i] # coordonnées du second noeud

            Li=np.linalg.norm(node2-node1) # taille de la poutre

            c=(node2[0]-node1[0])/Li # cosinus associé à la poutre
            s=(node2[1]-node1[1])/Li # sinus associé à la poutre

            # coefficient
            if n1i%2 == 0: # premier noeud en bas
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[0]*self.A_vector[0]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
            else: # premier noeud en haut
                if n2i%2 == 0: # second noeud en bas
                    alpha = self.E_vector[1]*self.A_vector[1]/Li
                else: # second noeud en haut
                    alpha = self.E_vector[2]*self.A_vector[2]/Li

            x1 = 2*n1i
            y1 = x1+1
            x2 = 2*n2i
            y2 = x2+1

            Vect = np.array([-c, -s, c, s])
            Vect = Vect.reshape((1, 4))

            U = np.array([u[x1],
                        u[y1],
                        u[x2],
                        u[y2]])
            U = U.reshape((4,1))

            Ni = alpha * Vect@U

            N.append(Ni[0][0])

        return N



    def _vecteurDeplacement_general(self, F):
        reduction=[]

        if len(self.supports) == 0:
            raise ValueError("Vous devez implémenter les supports pour effectuer les vérifications !")
        
        for node in self.supports:
            ni=self.nodes_list.index([node[0], node[1]])
            if self.supports.get(node) == "Appui simple": # Si appui simple seulement Uy = 0
                reduction.append(2*ni+1)
            elif self.supports.get(node) == "Articulation": # Si Articulation alors Ux = Uy = 0
                reduction.append(2*ni)
                reduction.append(2*ni+1)
            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        reduction.sort(reverse=True) 

        self._matriceRigidite()

        K_red = np.copy(self.K)
        F_red = np.copy(F)

        for i in reduction:
            K_red = np.delete(K_red, i, 0) # suppression de la ligne
            K_red = np.delete(K_red, i, 1) # suppression de la colonne
            F_red = np.delete(F_red, i, 0) # suppression du terme (ligne)

        # vérification
        rank = np.linalg.matrix_rank(K_red)
        if rank < K_red.shape[0]:
            raise ValueError("La matrice K est une singularité, vérifiez les supports")
        
        u = np.linalg.solve(K_red, F_red)

        # On fait maintenant l'inverse de la réduction pour retrouver la taille de base  
        reduction.sort(reverse=False) 
        for i in reduction:
            u = np.insert(u, i, 0)

        return u           



    def _fleche_max_ELS(self, largeur, poids_plancher, charge_exploitation):

            self._calcul_force_ELS(largeur, poids_plancher, charge_exploitation)

            self.u_ELS = self._vecteurDeplacement_general(self.F_ELS)

            self.val_fleche_max_ELS = max(abs(self.u_ELS))



    def _fleche_max_Q(self, largeur, charge_exploitation):

            self._calcul_force_exploitation(largeur, charge_exploitation)
            
            self.u_Q = self._vecteurDeplacement_general(self.F_Q)

            self.val_fleche_max_Q = max(abs(self.u_Q))



    def verification_fleche_Q(self, largeur, charge_exploitation=5):
        """
        Calcule et vérifie si la flèche max sous charge d'exploitation est dans les normes

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_Q(largeur, charge_exploitation)

        is_respected = self.val_fleche_max_Q <= (self.L/self.denominateur_Q)

        return self.val_fleche_max_Q, is_respected



    def verification_fleche_ELS(self, largeur, poids_plancher, charge_exploitation=5):
        """
        Calcule et vérifie si la flèche max sous charge d'exploitation est dans les normes

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_ELS(largeur, poids_plancher, charge_exploitation)

        is_respected = self.val_fleche_max_ELS <= (self.L/self.denominateur_ELS)

        return self.val_fleche_max_ELS, is_respected
    


    def _calcul_contrainte_normale_ELU(self, largeur, poids_plancher, charge_exploitation):

        self._calcul_force_ELU(largeur, poids_plancher, charge_exploitation)
        self.N_ELU =    self._vecteurEfforts_general(self._vecteurDeplacement_general(self.F_ELU))

        self.sigma = np.zeros(len(self.N_ELU))

        was_bot = 0
        for n, N in enumerate(self.N_ELU):
            if n%2==0: # poutres diagonales 
                self.sigma[n] = N/self.A_vector[1]
            else: # poutres hautes ou basses
                if was_bot: # poutre haute car on a fait une basse avant
                    was_bot=0
                    self.sigma[n] = N/self.A_vector[2]
                else: # poutre basse
                    was_bot=1
                    self.sigma[n] = N/self.A_vector[0]

        self.sigma_max = max(abs(self.sigma))



    def verification_contrainte_normale_ELU(self, largeur, poids_plancher, charge_exploitation=5):
        """
        Calcule et vérifie si les contraintes normales sont dans les normes

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_effort_max_ELS : float
            valeur absolue de la contrainte normale la plus grande en MPa
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._calcul_contrainte_normale_ELU(largeur, poids_plancher, charge_exploitation)

        is_respected = self.sigma_max < self.sigma_max_ELU

        return self.sigma_max, is_respected



        
    def _plot_deplacements_general(self, u, show_nodes=True, show_arrows=True):

        plt.figure()

        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les supports et les matériaux/sections.")
        
        max_u = np.max(np.abs(u))
        scale = self.L / (max_u*20)
        nodes_after = self.nodes+u.reshape(-1, 2)
        nodes_after_scale = self.nodes+u.reshape(-1, 2)*scale

        # Plot des noeuds avant/après
        if show_nodes:
            plt.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=25, c="r")

            plt.scatter(nodes_after_scale[:, 0], nodes_after_scale[:, 1], marker="o", s=25, c="r")
            for n, node in enumerate(nodes_after_scale):
                plt.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des flèches de mesures du déplacement
        if show_arrows:
            for i in range(self.n_nodes_total):
                node = self.nodes[i]
                node_after = nodes_after[i]
                node_after_scale = nodes_after_scale[i]
                if np.linalg.norm(node_after-node) != 0:
                    plt.annotate("", xytext=node, xy=node_after_scale, arrowprops=dict(arrowstyle='->', color='black', linewidth=1.5, linestyle="--"), size=6)
                    plt.annotate(f"({(node_after[0]-node[0])*10**3:.2f}, {(node_after[1]-node[1])*10**3:.2f}) mm", (node_after_scale[0]-0.1, node_after_scale[1]+rd.uniform(0.05, 0.15)), size=5, ha="right")

        # Plot des poutres avant.après
        for n, beam in enumerate(self.beams):
            plt.plot(beam[:, 0], beam[:, 1], "b--", linewidth=0.2)

        beams_after = nodes_after_scale[self.beams_nodes]
        for n, beam in enumerate(beams_after):
            plt.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.8)

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # On récupère le décalage en x
                new_x_pos = self.nodes_list.index([x, y])
                new_x = nodes_after[new_x_pos][0]

                # triangle vert
                polygon = np.array([[new_x, y],
                                    [new_x-0.5, y-0.5],
                                    [new_x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)
                # deux rouleaux
                for i in [new_x-0.25, new_x+0.25]:
                    circle = plt.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    plt.gca().add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        plt.grid(True)
        plt.title("Déplacement des noeuds d'un pont en treillis warren")

        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()



    def _ax_plot_deplacements_general(self, ax, u, show_nodes=True, show_arrows=True):

        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les supports et les matériaux/sections.")

        max_u = np.max(np.abs(u))
        scale = self.L / (max_u*20)
        nodes_after = self.nodes+u.reshape(-1, 2)
        nodes_after_scale = self.nodes+u.reshape(-1, 2)*scale

        # Plot des noeuds avant/après
        if show_nodes:
            ax.scatter(self.nodes[:, 0], self.nodes[:, 1], marker="o", s=25, c="r")

            ax.scatter(nodes_after_scale[:, 0], nodes_after_scale[:, 1], marker="o", s=25, c="r")
            for n, node in enumerate(nodes_after_scale):
                ax.annotate(f"N{n}", (node[0]+0.1, node[1]+0.1), color="r", size=6, ha="left") # annotation du numéro du noeud

        # Plot des flèches de mesures du déplacement
        if show_arrows:
            for i in range(self.n_nodes_total):
                node = self.nodes[i]
                node_after = nodes_after[i]
                node_after_scale = nodes_after_scale[i]
                if np.linalg.norm(node_after-node) != 0:
                    ax.annotate("", xytext=node, xy=node_after_scale, arrowprops=dict(arrowstyle='->', color='black', linewidth=1.5, linestyle="--"), size=6)
                    ax.annotate(f"({(node_after[0]-node[0])*10**3:.2f}, {(node_after[1]-node[1])*10**3:.2f}) mm", (node_after_scale[0]-0.1, node_after_scale[1]+rd.uniform(0.05, 0.15)), size=5, ha="right")

        # Plot des poutres avant.après
        for n, beam in enumerate(self.beams):
            ax.plot(beam[:, 0], beam[:, 1], "b--", linewidth=0.2)

        beams_after = nodes_after_scale[self.beams_nodes]
        for n, beam in enumerate(beams_after):
            ax.plot(beam[:, 0], beam[:, 1], "b", linewidth=0.8)

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # On récupère le décalage en x
                new_x_pos = self.nodes_list.index([x, y])
                new_x = nodes_after[new_x_pos][0]

                # triangle vert
                polygon = np.array([[new_x, y],
                                    [new_x-0.5, y-0.5],
                                    [new_x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)
                # deux rouleaux
                for i in [new_x-0.25, new_x+0.25]:
                    circle = mpatches.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    ax.add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        ax.grid(True)
        ax.set_title("Déplacement des noeuds d'un pont en treillis warren")
        
        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")
        


    def plot_deplacement_Q(self, largeur, charge_exploitation=5):
        """
        Affiche le déplacement du pont sous les charges d'exploitations

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_Q(largeur, charge_exploitation)

        self._plot_deplacements_general(self.u_Q)


    def ax_plot_deplacement_Q(self, ax, largeur, charge_exploitation=5):
        """
        Affiche le déplacement du pont sous les charges d'exploitations sur un axe donné

        Parameters
        ----------
        ax : class
            axe matplotlib ou dessiner la figure
        largeur : int or float
            largeur du pont en m
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_Q(largeur, charge_exploitation)

        self._ax_plot_deplacements_general(ax, self.u_Q)



    def plot_deplacement_ELS(self, largeur, poids_plancher, charge_exploitation=5):
        """
        Affiche le déplacement du pont sous les charges d'exploitations et permanantes

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_ELS(largeur, poids_plancher, charge_exploitation)

        self._plot_deplacements_general(self.u_ELS)


    def ax_plot_deplacement_ELS(self, ax, largeur, poids_plancher, charge_exploitation=5):
        """
        Affiche le déplacement du pont sous les charges d'exploitations sur un axe donné

        Parameters
        ----------
        ax : class
            axe matplotlib ou dessiner la figure
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        val_fleche_max_Q : float
            valeur absolue de la flèche max sous charge d'exploitation en m
        is_respected : bool
            renvoie si la valeur est dans les normes (True) ou hors normes (False)
        """

        self._fleche_max_ELS(largeur, poids_plancher, charge_exploitation)

        self._ax_plot_deplacements_general(ax, self.u_ELS)



    def _plot_contraintes_general(self, N):

        plt.figure()

        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les supports et les matériaux/sections.")

        # Plot de l'effort normal des poutres avec colormap
        cmap = plt.cm.jet # jet : bleu -> vert -> rouge
        values_map = plt.Normalize(vmin=min(N), vmax=max(N)) # création de l'échelle du colorbar

        for n, beam in enumerate(self.beams): 
            plt.plot(beam[:, 0], beam[:, 1], color=cmap(values_map(N[n])), linewidth=2.4)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            plt.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color=cmap(values_map(N[n])), size=6, ha="left") # annotation du numéro des poutres
            plt.annotate(f"{N[n]:.2f} MPa", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(N[n])), size=5, ha="right") # annotation de l'effort 
        colorbar = plt.cm.ScalarMappable(norm=values_map, cmap=cmap)
        plt.colorbar(colorbar, ax=plt.gca(), label="Contrainte normale (en MPa)") # barre à droite

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = plt.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    plt.gca().add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = plt.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                plt.gca().add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        plt.grid(True)
        plt.title("Contraintes normales des poutres d'un pont en treillis warren")

        if self.type=="parabole non sym":
            maxh = max(self.h1, self.h2, self.h3)
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*maxh, 1.2*maxh)
        else:
            plt.xlim(-0.1*self.L, 1.1*self.L)
            plt.ylim(-0.2*self.h1, 1.2*self.h1)

        plt.axis("equal")
        plt.xlabel("en m")
        plt.ylabel("en m")
        plt.show()



    def _ax_plot_contraintes_general(self, ax, N):
        """
        Affichage des efforts normaux des poutres du pont sur un axe donné (noeuds, poutres, efforts normaux)
        """

        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Afin d'afficher les efforts, vous devez implémenter la structure, les supports et les matériaux/sections.")

        # Plot de l'effort normal des poutres avec colormap
        cmap = plt.cm.jet # jet : bleu -> vert -> rouge
        values_map = plt.Normalize(vmin=min(N), vmax=max(N)) # création de l'échelle du colorbar

        for n, beam in enumerate(self.beams): 
            ax.plot(beam[:, 0], beam[:, 1], color=cmap(values_map(N[n])), linewidth=2.4)
            mid = (beam[:][1]-beam[:][0])/2+beam[:][0]
            ax.annotate(f"P{n}", (mid[0]+0.1, mid[1]+rd.uniform(0.05, 0.15)), color=cmap(values_map(N[n])), size=6, ha="left") # annotation du numéro des poutres
            ax.annotate(f"{N[n]:.2f} MPa", (mid[0]-0.25, mid[1]-rd.uniform(0.25, 0.35)), color=cmap(values_map(N[n])), size=5, ha="right") # annotation de l'effort 
        colorbar = plt.cm.ScalarMappable(norm=values_map, cmap=cmap)
        plt.colorbar(colorbar, ax=ax, label="Contrainte normale (en MPa)") # barre à droite

        # Plot des appuis
        for node in self.supports:
            x=node[0]
            y=node[1]
            if self.supports.get(node) == "Appui simple":
                # triangle vert
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="g", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)
                # deux rouleaux
                for i in [x-0.25, x+0.25]:
                    circle = mpatches.Circle((i, y-0.65), 0.15, facecolor="g", edgecolor="k", linewidth=0.8)
                    ax.add_patch(circle)

            elif self.supports.get(node) == "Articulation":
                # triangle rouge
                polygon = np.array([[x, y],
                                    [x-0.5, y-0.5],
                                    [x+0.5, y-0.5]])
                triangle = mpatches.Polygon(polygon, facecolor="r", edgecolor="k", linewidth=0.8)
                ax.add_patch(triangle)

            else: #Vérification
                raise ValueError("Format de support non pris en charge")

        ax.grid(True)
        ax.set_title("Efforts normaux des poutres d'un pont en treillis warren")
        
        ax.relim()
        ax.autoscale_view()
        ax.margins(0.2)

        ax.set_aspect("equal")
        ax.set_xlabel("en m")
        ax.set_ylabel("en m")



    def plot_contrainte_normale_ELU(self, largeur, poids_plancher, charge_exploitation=5):
        """
        Affiche les contraintes normales de chaque poutre

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        None
        """

        self._calcul_contrainte_normale_ELU(largeur, poids_plancher, charge_exploitation)

        self._plot_contraintes_general(self.sigma)



    def ax_plot_contrainte_normale_ELU(self, ax, largeur, poids_plancher, charge_exploitation=5):
        """
        Affiche les contraintes normales de chaque poutre sur un axe donné

        Parameters
        ----------
        ax : class
            axe matplotlib ou dessiner la figure
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        charge_exploitation : int or float
            charge surfacique d'exploitation en kN/m^2

        Returns  
        ----------
        None
        """

        self._calcul_contrainte_normale_ELU(largeur, poids_plancher, charge_exploitation)

        self._ax_plot_contraintes_general(ax, self.sigma)



    def _matriceMasse(self, largeur, poids_plancher, masse_surfacique_pietons):

        if len(self.nodes) == 0 or len(self.supports) == 0 or np.any(self.A_vector) == 0 or np.any(self.rho_vector) == 0:
            raise NotImplementedError("Pour calculer la matrice de masse, vous devez implémenter la structure, les supports et les matériaux/sections.")
        
        self.M = np.zeros((2*self.n_nodes_total, 2*self.n_nodes_total))

        for node_combo in self.beams_nodes:
            n1i = node_combo[0] # numéro du premier noeud
            n2i = node_combo[1] # numéro du second noeud

            node1 = self.nodes[n1i] # coordonnées du premier noeud
            node2 = self.nodes[n2i] # coordonnées du second noeud

            Li=np.linalg.norm(node2-node1) # taille de la poutre

            if n1i%2 == 0: # premier noeud en bas
                if n2i%2 == 0: # second noeud en bas
                    section = self.A_vector[0]
                    masse_v = self.rho_vector[0]
                else: # second noeud en haut
                    section = self.A_vector[1]
                    masse_v = self.rho_vector[1]
            else: # premier noeud en haut
                if n2i%2 == 0: # second noeud en bas
                    section = self.A_vector[1]
                    masse_v = self.rho_vector[1]
                else: # second noeud en haut
                    section = self.A_vector[2]
                    masse_v = self.rho_vector[2]

            x1 = 2*n1i
            y1 = 2*n1i+1
            x2 = 2*n2i
            y2 = 2*n2i+1

            m = masse_v*(section*10**(-6))*Li

            self.M[x1][x1] += m/2
            self.M[y1][y1] += m/2
            self.M[x2][x2] += m/2
            self.M[y2][y2] += m/2 

        masse_surfacique_plancher = (poids_plancher*10**3)/9.81 # Conversion en kg/m^2

        m_plancher = self.length_horizontal_beams*(largeur/2)*(masse_surfacique_plancher+masse_surfacique_pietons)

        for n in range(len(self.nodes)):
            x=2*n
            y=2*n+1

            if n%2==0: # noeud sur la partie basse
                if n==0: # premier noeud du pont
                    self.M[x][x] += m_plancher/2
                    self.M[y][y] += m_plancher/2
                elif n == self.n_nodes_total-1: # dernier noeud du pont
                    self.M[x][x] += m_plancher/2
                    self.M[y][y] += m_plancher/2
                else: # noeud au milieu du pont
                    self.M[x][x] += m_plancher
                    self.M[y][y] += m_plancher


    def matriceMasse(self, largeur, poids_plancher, masse_surfacique_pietons):
        """
        Calcule la matrice de masse de la structure selon les charges permanantes et la masse surfacique de pietons

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2

        Returns  
        ----------
        M : np.array
            matrice de rigidité

        """

        self._matriceMasse(largeur, poids_plancher, masse_surfacique_pietons)   

        return self.M
    

    def _freqs_propre(self, largeur, poids_plancher, masse_surfacique_pietons, n=10):

        self._matriceMasse(largeur, poids_plancher, masse_surfacique_pietons)

        reduction=[]

        for node in self.supports:
            ni=self.nodes_list.index([node[0], node[1]])
            if self.supports.get(node) == "Appui simple": # Si appui simple seulement Uy = 0
                reduction.append(2*ni+1)
            elif self.supports.get(node) == "Articulation": # Si Articulation alors Ux = Uy = 0
                reduction.append(2*ni)
                reduction.append(2*ni+1)
            else: #Vérification
                raise ValueError("Format de support non pris en charge")
        
        reduction.sort(reverse=True) 

        self._matriceRigidite()
        
        K_red = np.copy(self.K)
        M_red = np.copy(self.M)

        for i in reduction:
            K_red = np.delete(K_red, i, 0) # suppression de la ligne
            K_red = np.delete(K_red, i, 1) # suppression de la colonne
            M_red = np.delete(M_red, i, 0) # suppression de la ligne
            M_red = np.delete(M_red, i, 1) # suppression de la colonne

        # vérification
        rank = np.linalg.matrix_rank(K_red)
        if rank < K_red.shape[0]:
            raise ValueError("La matrice K est une singularité, vérifiez les supports")
        
        self.eigvals, self.eigvecs = scp.linalg.eigh(K_red, M_red)

        self.freqs = np.sqrt(self.eigvals) / (2*np.pi)

        self.freq_n_max = n
        self.freqs = self.freqs[:n]



    def freqs_propre(self, largeur, poids_plancher, masse_surfacique, n=10):
        """
        Calcule toutes les fréquences propres et les trie dans l'ordre croissant

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2
        n : int
            nombre de fréquences à garder

        Returns  
        ----------
        freqs : np.array
            vecteur contenant toutes les fréquences propres dans l'ordre croissant

        """

        self._freqs_propre(largeur, poids_plancher, masse_surfacique, n)

        return self.freqs



    def plot_mode_n(self, n, largeur, poids_plancher, masse_surfacique_pietons):
        """
        Affiche la déformation lié à la fréquence propre numéro n (ordre croissant)

        Parameters
        ----------
        n : int
            numéro du mode a afficher (démarre à 1)
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2

        Returns  
        ----------
        None

        """

        if n>self.freq_n_max:
            raise IndexError("Vous avez calculé trop peu de fréquences, le numéro du mode dépasse celui des fréquences gardés !")

        self._freqs_propre(largeur, poids_plancher, masse_surfacique_pietons)

        if n<=0:
            raise ValueError("Le numéro du mode a afficher doit être strictement positif")
        n-=1
        mode = self.eigvecs[:, n]

        reduction=[]

        for node in self.supports:
            ni=self.nodes_list.index([node[0], node[1]])
            if self.supports.get(node) == "Appui simple": # Si appui simple seulement Uy = 0
                reduction.append(2*ni+1)
            elif self.supports.get(node) == "Articulation": # Si Articulation alors Ux = Uy = 0
                reduction.append(2*ni)
                reduction.append(2*ni+1)
            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        # On fait maintenant l'inverse de la réduction pour retrouver la taille de base 
        reduction.sort(reverse=False) 
        for i in reduction:
            mode = np.insert(mode, i, 0)

        self._plot_deplacements_general(mode, False, False)



    def ax_plot_mode_n(self, ax, n, largeur, poids_plancher, masse_surfacique_pietons): 
        """
        Affiche la déformation lié à la fréquence propre numéro n sur un axe donné (ordre croissant)

        Parameters
        ----------
        n : int
            numéro du mode a afficher (démarre à 1)
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2

        Returns  
        ----------
        None

        """
        self._freqs_propre(largeur, poids_plancher, masse_surfacique_pietons)

        if n<=0:
            raise ValueError("Le numéro du mode a afficher doit être strictement positif")
        n-=1
        mode = self.eigvecs[:, n]

        reduction=[]

        for node in self.supports:
            ni=self.nodes_list.index([node[0], node[1]])
            if self.supports.get(node) == "Appui simple": # Si appui simple seulement Uy = 0
                reduction.append(2*ni+1)
            elif self.supports.get(node) == "Articulation": # Si Articulation alors Ux = Uy = 0
                reduction.append(2*ni)
                reduction.append(2*ni+1)
            else: #Vérification
                raise ValueError("Format de support non pris en charge")
            
        # On fait maintenant l'inverse de la réduction pour retrouver la taille de base 
        reduction.sort(reverse=False) 
        for i in reduction:
            mode = np.insert(mode, i, 0)

        self._ax_plot_deplacements_general(ax, mode, False, False)

    

    def analyse_modale(self, classe, largeur, poids_plancher, masse_surfacique_pietons, n):
        """
        Affiche la déformation lié à la fréquence propre numéro n (ordre croissant)

        Parameters
        ----------
        classe : int
            Classe du pont (1, 2 ou 3)
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2
        n : int
            nombre de fréquences à garder

        Returns  
        ----------
        result : list
            liste de string avec les informations sur les fréquences dangereuses et le numéro du node pour affichage

        """

        if classe not in [1, 2, 3]:
            raise ValueError("Classe invalide (doit être 1, 2 ou 3)")
    
        self._freqs_propre(largeur, poids_plancher, masse_surfacique_pietons, n)

        result = []

        if classe==1 or classe==2:
            lim_freq_haute = self.classe_I_II_verti_longi_lim_haute
            lim_freq_basse = self.classe_I_II_verti_longi_lim_basse
            
        elif classe==3:
            lim_freq_haute = self.classe_III_verti_longi_lim_haute
            lim_freq_basse = self.classe_III_verti_longi_lim_basse
        
        for n, val in enumerate(self.freqs):
            if  lim_freq_basse <= val <= lim_freq_haute:
                result.append(f"mode n°{n+1} : {lim_freq_basse} Hz <= {val:.2f} Hz <= {lim_freq_haute} Hz DANGER")
        
        
        if len(result)==0:
            result.append("Tous les modes OK")

        return result
    


    def masse_pont_totale(self, largeur, poids_plancher, masse_surfacique_pietons):
        """
        Calcule la masse totale du pont en X et en Y

        Parameters
        ----------
        largeur : int or float
            largeur du pont en m
        poids_plancher : int or float
            poid du plancher du pont en kN/m^2
        masse_surfacique_pietons : int or float
            masse surfacique des piétons en kg/m^2

        Returns  
        ----------
        masse_x : int or float
            masse totale du pont en x
        masse_y : int or float
            masse totale du pont en y

        """
        
        self.masse_x = 0
        self.masse_y = 0

        self._matriceMasse(largeur, poids_plancher, masse_surfacique_pietons)

        for n, masse in enumerate(np.diag(self.M)):
            if n%2==0:
                self.masse_x += masse
            else:
                self.masse_y += masse
        
        return self.masse_x, self.masse_y