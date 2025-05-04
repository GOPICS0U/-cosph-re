# Écosphère - Simulation Procédurale d'un Monde Alien

Écosphère est une simulation auto-entretenue d'un monde alien généré de façon procédurale. Le programme simule l'évolution complète d'un écosystème et de civilisations conscientes sans aucune intervention extérieure.

## Caractéristiques

- **Génération procédurale** d'une planète avec géographie, climat et biomes uniques
- **Modélisation climatique** incluant vents, saisons et courants océaniques
- **Écosystème évolutif** avec chaînes trophiques complexes (herbivores, prédateurs, décomposeurs)
- **Évolution basée sur la sélection naturelle** (mutation, adaptation, extinction)
- **Émergence de civilisations** à partir d'espèces intelligentes
- **Développement socio-culturel** des espèces intelligentes (langue, religion, technologie)
- **Chronologie accélérée** : 1 seconde = 1 an dans la simulation
- **Visualisation interactive** de la planète et de son évolution

## Installation

1. Clonez ce dépôt
2. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

## Utilisation

Lancez la simulation avec :
```
python main.py
```

L'interface graphique vous permettra de :
- Visualiser différents aspects de la planète (géographie, climat, population, civilisations)
- Suivre l'évolution des espèces et des civilisations
- Ajuster la vitesse de simulation
- Capturer des images de la planète

## Structure du projet

- `main.py` : Point d'entrée principal
- `requirements.txt` : bibliothèques pour le jeu
- `simulation/` : Modules de simulation
  - `world.py` : Gestion globale du monde
  - `geography.py` : Génération et gestion du terrain
  - `climate.py` : Simulation climatique
  - `ecosystem.py` : Évolution des espèces
  - `civilization.py` : Développement des civilisations
  - `visualization.py` : Interface graphique
  - `logger.py` : Journalisation des événements

## Fonctionnement

La simulation fonctionne de manière entièrement autonome, sans intervention humaine. Chaque aspect du monde évolue selon des règles et des probabilités définies :

1. Une planète est générée avec sa géographie, son climat et ses biomes
2. Des espèces primitives apparaissent et évoluent par sélection naturelle
3. Des chaînes alimentaires complexes se forment
4. Certaines espèces peuvent développer une intelligence supérieure
5. Des civilisations émergent et évoluent à travers différents stades technologiques
6. Des événements aléatoires (catastrophes, découvertes) influencent l'évolution du monde

Tous les événements sont enregistrés dans un journal historique détaillé.

## Personnalisation

Vous pouvez modifier les paramètres de simulation dans les fichiers correspondants :
- Taille de la planète et composition atmosphérique dans `world.py`
- Paramètres climatiques dans `climate.py`
- Taux d'évolution et de mutation dans `ecosystem.py`
- Probabilités d'émergence de civilisations dans `civilization.py`

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
