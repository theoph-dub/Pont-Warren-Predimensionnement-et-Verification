# :bridge_at_night: Pont Warren — Calculateur

Application graphique et librairie de calcul/vérifications de pont de type Warren.

## :fr: Description

Cette application permet le pré-dimensionnement de pont Warren et la vérification du respect des normes définies dans le fichier `parameters.json`. On utilise la méthode des éléments finis pour calculer trois types de ponts :

- **rectangle** : hauteur constante
- **parabole symétrique** : partie supérieure suivant un polynôme du second degré
- **parabole non symétrique** : partie supérieur suivant un polynome du second degré avec des hauteurs aux extrémités différentes

## :warning: Pré-requis

- Python
- Librairies utilisées :
  - `Pyside6`
  - `matplotlib`
  - `numpy`
  - `scipy`

## :round_pushpin: Installation

```bash
pip install PySide6 matplotlib numpy scipy
```

Le fichier `parameters.json` et `Warren_lib.py`doivent être dans le même dossier que le fichier `interface_PySide6.py`.

## Utilisation

Lancez `interface_PySide6.py` depuis un IDE ou avec la commande :

```bash
python interface_PySide6.py
```

Dans l'application, vous pouvez suivre ces étapes :

1. **Unités** : changer les unités si besoin.
2. **Variables** : choisir le type de pont et entrer les paramètres structures (`L`, `n`, `h1`, et `h2`/`h3` selon le type), puis entrer les matériaux (E, rho) et mesures de la sections (tube ou rectangle) aux poutres supérieures, inférieures et diagonales.
3. Cliquer sur **Calculer structure** pour générer le pont (nœuds, poutres, supports).
4. **Graphiques** : visualiser le pont de base ou les résultats de vérification via le menu déroulant.
5. **Vérifications** : entrer la largeur du pont et le poids du plancher, choisir le type de charge d'exploitation, puis lancer les vérifications (flèche Q, flèche ELS, contrainte normale ELU).
6. **Analyse Modale** : entrer la masse surfacique de piéton ainsi que la classe du pont pour vérifier ses modes propres ainsi que leur forme.
7. **Réinitialiser** : remet le pont et les vérifications à zéro.

## :wrench: Fichier paramètres

Le fichier `parameters.json` contient les paramètres définis comme norme à suivre, celles-ci proviennent de l'Eurocode et peuvent être modifié en fonction. Le fichier contient :

- `coef_G_ELU` / `coef_Q_ELU` : coefficients des charges permanentes (G) et d'exploitation (Q) à l'ELU.
- `sigma_max_ELU` : contrainte normale admissible en MPa.
- `denominateur_fleche_max_Q` / `denominateur_fleche_max_ELS` : la flèche maximum est `L / denominateur`.
