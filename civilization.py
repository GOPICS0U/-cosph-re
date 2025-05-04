#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de civilisation pour la simulation Écosphère.
Gère l'émergence et l'évolution des civilisations issues d'espèces intelligentes.
"""

import random
import numpy as np
import logging
from enum import Enum
from collections import defaultdict

class TechLevel(Enum):
    """Niveaux technologiques possibles pour une civilisation."""
    PRIMITIVE = 0  # Outils rudimentaires, feu
    AGRICULTURAL = 1  # Agriculture, villages
    MEDIEVAL = 2  # Métallurgie, villes
    INDUSTRIAL = 3  # Machines, énergie
    INFORMATION = 4  # Informatique, réseaux
    SPACE = 5  # Voyage spatial
    ADVANCED = 6  # Technologies avancées (IA, manipulation génétique)
    STELLAR = 7  # Voyage interstellaire

class GovernmentType(Enum):
    """Types de gouvernement possibles."""
    TRIBAL = 0
    MONARCHY = 1
    OLIGARCHY = 2
    REPUBLIC = 3
    DEMOCRACY = 4
    TECHNOCRACY = 5
    HIVE_MIND = 6
    AI_GOVERNANCE = 7

class Civilization:
    """Classe représentant une civilisation issue d'une espèce intelligente."""
    
    def __init__(self, manager, species, name=None):
        """
        Initialise une nouvelle civilisation.
        
        Args:
            manager: Le gestionnaire de civilisations.
            species: L'espèce à l'origine de la civilisation.
            name: Nom de la civilisation (généré si None).
        """
        self.manager = manager
        self.logger = logging.getLogger('ecosphere')
        
        # Espèce fondatrice
        self.founding_species = species
        self.species = [species]  # Liste des espèces participant à la civilisation
        
        # Caractéristiques de base
        self.name = name if name else self._generate_name()
        self.age = 0  # Âge en années
        self.population = int(species.population * 0.1)  # Initialement 10% de la population de l'espèce
        
        # Niveau technologique
        self.tech_level = TechLevel.PRIMITIVE
        self.tech_progress = 0.0  # Progression vers le niveau suivant (0-1)
        
        # Gouvernement
        self.government = GovernmentType.TRIBAL
        
        # Attributs sociaux
        self.stability = random.uniform(0.5, 0.9)  # Stabilité sociale (0-1)
        self.aggression = random.uniform(0.2, 0.8)  # Tendance à l'agression (0-1)
        self.cooperation = random.uniform(0.3, 0.9)  # Tendance à la coopération (0-1)
        self.creativity = random.uniform(0.4, 0.9)  # Créativité (0-1)
        
        # Culture
        self.language = self._generate_language()
        self.religion = self._generate_religion() if random.random() < 0.8 else None
        self.art_focus = random.choice(["visuel", "auditif", "conceptuel", "performatif"])
        
        # Économie
        self.economy_type = "subsistance"  # subsistance, troc, monétaire, etc.
        self.resources = {}  # Ressources contrôlées
        
        # Territoire
        self.territory = np.zeros((manager.world.geography.grid_size, 
                                  manager.world.geography.grid_size), dtype=bool)
        self._initialize_territory()
        
        # Relations avec d'autres civilisations
        self.relations = {}  # {civ_id: relation_value}
        
        # Historique
        self.history = []
        self.add_history_event("Fondation", f"Émergence de la civilisation {self.name}")
        
        # Technologies découvertes
        self.technologies = set()
        
        # État
        self.is_extinct = False
        self.extinction_cause = None
    
    def _generate_name(self):
        """Génère un nom pour la civilisation."""
        prefixes = ["Ar", "Bel", "Civ", "Dor", "El", "Fal", "Gal", "Hy", "Il", "Jor", 
                   "Kal", "Lum", "Mer", "Neb", "Orb", "Prim", "Qua", "Rim", "Sol", "Ter"]
        suffixes = ["ia", "or", "an", "ium", "aria", "alis", "oria", "ium", "aris", "on"]
        
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def _generate_language(self):
        """Génère une langue pour la civilisation."""
        vowels = "aeiouy"
        consonants = "bcdfghjklmnpqrstvwxz"
        
        # Caractéristiques de la langue
        language = {
            "name": f"{self.name}an",
            "vowels": ''.join(random.sample(vowels, k=random.randint(3, 6))),
            "consonants": ''.join(random.sample(consonants, k=random.randint(10, 15))),
            "syllable_structure": random.choice(["CV", "CVC", "VC", "CVVC"]),
            "tone": random.random() < 0.3,  # 30% de chance d'être tonale
            "writing": None  # Pas d'écriture au début
        }
        
        return language
    
    def _generate_religion(self):
        """Génère une religion pour la civilisation."""
        types = ["animisme", "polythéisme", "monothéisme", "dualisme", "philosophie naturelle"]
        focuses = ["nature", "ancêtres", "astres", "éléments", "cycle de vie", "ordre cosmique"]
        
        religion = {
            "type": random.choice(types),
            "focus": random.choice(focuses),
            "name": f"Culte de {self._generate_deity_name()}",
            "practices": []
        }
        
        # Pratiques religieuses
        possible_practices = ["prière", "méditation", "sacrifice", "rituel", "pèlerinage", "jeûne"]
        num_practices = random.randint(1, 3)
        religion["practices"] = random.sample(possible_practices, k=num_practices)
        
        return religion
    
    def _generate_deity_name(self):
        """Génère un nom de divinité."""
        prefixes = ["Anu", "Bel", "Cro", "Dra", "Eos", "Fyr", "Gai", "Hel", "Ish", "Jor"]
        suffixes = ["os", "us", "a", "is", "ar", "on", "oth", "um", "ax", "ir"]
        
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def _initialize_territory(self):
        """Initialise le territoire de la civilisation."""
        grid_size = self.manager.world.geography.grid_size
        biomes = self.manager.world.geography.biomes
        
        # Recherche des zones les plus peuplées par l'espèce fondatrice
        species_pop = self.founding_species.population_map
        
        # Sélection d'un point de départ (zone la plus peuplée)
        start_y, start_x = np.unravel_index(np.argmax(species_pop), species_pop.shape)
        
        # Expansion initiale autour du point de départ
        radius = 3  # Rayon initial
        
        for y in range(grid_size):
            for x in range(grid_size):
                # Distance au centre
                dx = min(abs(x - start_x), grid_size - abs(x - start_x))
                dy = min(abs(y - start_y), grid_size - abs(y - start_y))
                distance = np.sqrt(dx**2 + dy**2)
                
                # Territoire initial
                if distance <= radius and biomes[y, x] > 1:  # Pas dans l'océan
                    self.territory[y, x] = True
    
    def add_history_event(self, event_type, description):
        """
        Ajoute un événement à l'historique de la civilisation.
        
        Args:
            event_type: Type d'événement.
            description: Description de l'événement.
        """
        event = {
            "year": self.manager.world.age,
            "type": event_type,
            "description": description
        }
        
        self.history.append(event)
        self.logger.info(f"[{self.name}] Année {self.manager.world.age}: {event_type} - {description}")
    
    def update(self):
        """Met à jour la civilisation pour une année de simulation."""
        if self.is_extinct:
            return
        
        self.age += 1
        
        # Mise à jour de la population
        self._update_population()
        
        # Vérification de l'extinction
        if self.population <= 100:
            self._go_extinct("Population trop faible")
            return
        
        # Développement technologique
        self._advance_technology()
        
        # Évolution sociale et culturelle
        self._evolve_society()
        
        # Expansion territoriale
        self._expand_territory()
        
        # Relations avec d'autres civilisations
        self._manage_relations()
        
        # Événements aléatoires
        self._random_events()
    
    def _update_population(self):
        """Met à jour la population de la civilisation."""
        # Facteurs de croissance
        base_growth = 0.01  # 1% de croissance annuelle de base
        
        # Modificateurs selon le niveau technologique
        tech_modifiers = {
            TechLevel.PRIMITIVE: 0.005,
            TechLevel.AGRICULTURAL: 0.015,
            TechLevel.MEDIEVAL: 0.01,
            TechLevel.INDUSTRIAL: 0.02,
            TechLevel.INFORMATION: 0.015,
            TechLevel.SPACE: 0.01,
            TechLevel.ADVANCED: 0.005,
            TechLevel.STELLAR: 0.003
        }
        
        tech_modifier = tech_modifiers.get(self.tech_level, 0.01)
        
        # Modificateur de stabilité
        stability_modifier = self.stability * 0.01
        
        # Calcul de la croissance
        growth_rate = base_growth + tech_modifier + stability_modifier
        
        # Facteurs limitants
        carrying_capacity = self._calculate_carrying_capacity()
        
        if self.population > carrying_capacity:
            # Croissance négative si au-dessus de la capacité de charge
            growth_rate = -0.01
        elif self.population > carrying_capacity * 0.8:
            # Ralentissement de la croissance près de la capacité
            growth_rate *= (1 - (self.population / carrying_capacity))
        
        # Application de la croissance
        self.population = int(self.population * (1 + growth_rate))
    
    def _calculate_carrying_capacity(self):
        """Calcule la capacité de charge du territoire."""
        # Capacité de base selon le niveau technologique
        base_capacities = {
            TechLevel.PRIMITIVE: 10000,
            TechLevel.AGRICULTURAL: 100000,
            TechLevel.MEDIEVAL: 1000000,
            TechLevel.INDUSTRIAL: 10000000,
            TechLevel.INFORMATION: 100000000,
            TechLevel.SPACE: 1000000000,
            TechLevel.ADVANCED: 10000000000,
            TechLevel.STELLAR: 100000000000
        }
        
        base_capacity = base_capacities.get(self.tech_level, 10000)
        
        # Ajustement selon la taille du territoire
        territory_size = np.sum(self.territory)
        territory_factor = territory_size / 100  # Facteur d'échelle
        
        return base_capacity * territory_factor
    
    def _advance_technology(self):
        """Fait progresser le développement technologique."""
        # Facteurs influençant le progrès technologique
        base_progress = 0.001  # Progrès de base par an
        
        # Modificateurs
        intelligence_modifier = self.founding_species.intelligence * 0.01
        creativity_modifier = self.creativity * 0.005
        population_modifier = min(0.01, self.population / 1000000 * 0.005)
        stability_modifier = self.stability * 0.002
        
        # Calcul du progrès
        progress = base_progress + intelligence_modifier + creativity_modifier + population_modifier + stability_modifier
        
        # Ralentissement aux niveaux supérieurs
        if self.tech_level.value >= 4:  # À partir du niveau Information
            progress *= 0.5
        
        # Mise à jour du progrès
        self.tech_progress += progress
        
        # Passage au niveau suivant si le seuil est atteint
        if self.tech_progress >= 1.0:
            self._advance_tech_level()
    
    def _advance_tech_level(self):
        """Fait passer la civilisation au niveau technologique suivant."""
        old_level = self.tech_level
        
        # Vérification que ce n'est pas déjà le niveau maximum
        if self.tech_level.value < len(TechLevel) - 1:
            # Passage au niveau suivant
            self.tech_level = TechLevel(self.tech_level.value + 1)
            self.tech_progress = 0.0
            
            # Enregistrement de l'événement
            self.add_history_event("Avancée technologique", 
                                  f"Passage du niveau {old_level.name} au niveau {self.tech_level.name}")
            
            # Découverte de technologies spécifiques
            self._discover_technologies()
            
            # Effets sur la société
            self._tech_advancement_effects()
    
    def _discover_technologies(self):
        """Découvre des technologies spécifiques au niveau technologique actuel."""
        # Technologies par niveau
        tech_discoveries = {
            TechLevel.PRIMITIVE: ["Feu", "Outils en pierre", "Langage écrit"],
            TechLevel.AGRICULTURAL: ["Agriculture", "Poterie", "Domestication", "Métallurgie de base"],
            TechLevel.MEDIEVAL: ["Architecture", "Mathématiques", "Astronomie", "Navigation"],
            TechLevel.INDUSTRIAL: ["Machine à vapeur", "Électricité", "Chimie", "Transport mécanisé"],
            TechLevel.INFORMATION: ["Informatique", "Télécommunications", "Médecine avancée", "Énergie nucléaire"],
            TechLevel.SPACE: ["Voyage spatial", "Robotique", "Intelligence artificielle", "Biotechnologie"],
            TechLevel.ADVANCED: ["Manipulation génétique", "Nanotechnologie", "Fusion nucléaire", "Réalité virtuelle"],
            TechLevel.STELLAR: ["Propulsion FTL", "Terraformation", "Conscience numérique", "Manipulation quantique"]
        }
        
        # Découverte des technologies du niveau actuel
        techs = tech_discoveries.get(self.tech_level, [])
        
        for tech in techs:
            if tech not in self.technologies:
                self.technologies.add(tech)
                self.add_history_event("Découverte technologique", f"Découverte de: {tech}")
    
    def _tech_advancement_effects(self):
        """Applique les effets d'une avancée technologique sur la société."""
        # Changements sociaux selon le niveau technologique
        if self.tech_level == TechLevel.AGRICULTURAL:
            # Passage à l'agriculture: sédentarisation, hiérarchie sociale
            if self.government == GovernmentType.TRIBAL:
                self.government = GovernmentType.MONARCHY
                self.add_history_event("Évolution politique", 
                                     f"Établissement d'une {self.government.name}")
            
            self.economy_type = "troc"
            
        elif self.tech_level == TechLevel.MEDIEVAL:
            # Développement des villes, commerce
            if random.random() < 0.5:
                self.government = GovernmentType.OLIGARCHY
                self.add_history_event("Évolution politique", 
                                     f"Transition vers une {self.government.name}")
            
            self.economy_type = "monétaire"
            
            # Développement de l'écriture si pas encore présent
            if not self.language.get("writing"):
                self.language["writing"] = random.choice(["pictographique", "idéographique", "alphabétique"])
                self.add_history_event("Développement culturel", 
                                     f"Création d'un système d'écriture {self.language['writing']}")
            
        elif self.tech_level == TechLevel.INDUSTRIAL:
            # Révolution industrielle
            if random.random() < 0.7:
                self.government = random.choice([GovernmentType.REPUBLIC, GovernmentType.OLIGARCHY])
                self.add_history_event("Évolution politique", 
                                     f"Transition vers une {self.government.name}")
            
            self.economy_type = "industrielle"
            
        elif self.tech_level == TechLevel.INFORMATION:
            # Ère de l'information
            if random.random() < 0.6:
                self.government = random.choice([GovernmentType.DEMOCRACY, GovernmentType.TECHNOCRACY])
                self.add_history_event("Évolution politique", 
                                     f"Transition vers une {self.government.name}")
            
            self.economy_type = "information"
            
        elif self.tech_level == TechLevel.ADVANCED:
            # Technologies avancées
            if random.random() < 0.5:
                self.government = random.choice([GovernmentType.TECHNOCRACY, GovernmentType.AI_GOVERNANCE])
                self.add_history_event("Évolution politique", 
                                     f"Transition vers une {self.government.name}")
            
            self.economy_type = "post-rareté"
    
    def _evolve_society(self):
        """Fait évoluer la société et la culture."""
        # Évolution lente des attributs sociaux
        if random.random() < 0.05:  # 5% de chance par an
            # Sélection d'un attribut à faire évoluer
            attribute = random.choice(["stability", "aggression", "cooperation", "creativity"])
            old_value = getattr(self, attribute)
            
            # Amplitude du changement
            change = random.uniform(-0.05, 0.05)
            
            # Application du changement
            new_value = max(0.01, min(0.99, old_value + change))
            setattr(self, attribute, new_value)
            
            # Événements significatifs pour les grands changements
            if abs(new_value - old_value) > 0.03:
                direction = "augmentation" if change > 0 else "diminution"
                self.add_history_event("Évolution sociale", 
                                     f"{direction.capitalize()} de {attribute} ({old_value:.2f} → {new_value:.2f})")
        
        # Évolution religieuse
        if self.religion and random.random() < 0.02:  # 2% de chance par an
            change_type = random.choice(["réforme", "schisme", "syncrétisme"])
            
            if change_type == "réforme":
                self.religion["name"] = f"Réforme de {self.religion['name']}"
                self.add_history_event("Évolution religieuse", f"Réforme religieuse: {self.religion['name']}")
            
            elif change_type == "schisme":
                old_name = self.religion["name"]
                self.religion["name"] = f"Nouveau {old_name}"
                self.add_history_event("Évolution religieuse", f"Schisme religieux: {old_name} → {self.religion['name']}")
            
            elif change_type == "syncrétisme":
                self.religion["name"] = f"{self.religion['name']} Universel"
                self.add_history_event("Évolution religieuse", f"Syncrétisme religieux: {self.religion['name']}")
    
    def _expand_territory(self):
        """Gère l'expansion territoriale de la civilisation."""
        # Probabilité d'expansion basée sur la population et le niveau technologique
        expansion_probability = 0.1 * (self.tech_level.value + 1) * min(1.0, self.population / 10000)
        
        if random.random() < expansion_probability:
            grid_size = self.manager.world.geography.grid_size
            biomes = self.manager.world.geography.biomes
            
            # Recherche des frontières actuelles
            border_cells = []
            
            for y in range(grid_size):
                for x in range(grid_size):
                    if not self.territory[y, x]:
                        continue
                    
                    # Vérification des cellules adjacentes
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            
                            nx, ny = (x + dx) % grid_size, (y + dy) % grid_size
                            
                            # Si c'est une cellule non-territoire adjacente à notre territoire
                            if not self.territory[ny, nx] and biomes[ny, nx] > 1:  # Pas dans l'océan
                                border_cells.append((nx, ny))
            
            # Expansion vers une cellule frontalière aléatoire
            if border_cells:
                num_expansions = min(len(border_cells), random.randint(1, 3))
                expansion_cells = random.sample(border_cells, num_expansions)
                
                for x, y in expansion_cells:
                    self.territory[y, x] = True
                
                # Enregistrement de l'expansion
                if num_expansions > 0:
                    self.add_history_event("Expansion territoriale", 
                                         f"Expansion vers {num_expansions} nouvelles régions")
    
    def _manage_relations(self):
        """Gère les relations avec d'autres civilisations."""
        # Mise à jour des relations existantes
        for civ_id, relation in list(self.relations.items()):
            # Vérification que la civilisation existe toujours
            other_civ = None
            for civ in self.manager.civilizations:
                if id(civ) == civ_id:
                    other_civ = civ
                    break
            
            if not other_civ or other_civ.is_extinct:
                del self.relations[civ_id]
                continue
            
            # Évolution naturelle des relations
            drift = random.uniform(-0.05, 0.05)
            
            # Facteurs d'influence
            if self.government == other_civ.government:
                drift += 0.01  # Gouvernements similaires
            
            if abs(self.tech_level.value - other_civ.tech_level.value) > 2:
                drift -= 0.01  # Grand écart technologique
            
            # Influence de l'agressivité
            drift -= (self.aggression - 0.5) * 0.02
            
            # Mise à jour de la relation
            self.relations[civ_id] = max(-1.0, min(1.0, relation + drift))
            
            # Événements basés sur les relations
            self._check_relation_events(other_civ)
        
        # Établissement de relations avec de nouvelles civilisations
        for other_civ in self.manager.civilizations:
            if other_civ == self or other_civ.is_extinct:
                continue
            
            civ_id = id(other_civ)
            
            if civ_id not in self.relations:
                # Vérification de la proximité
                if self._are_civilizations_close(other_civ):
                    # Établissement d'une relation initiale
                    initial_relation = random.uniform(-0.3, 0.3)
                    
                    # Ajustement selon les facteurs de compatibilité
                    if self.government == other_civ.government:
                        initial_relation += 0.2
                    
                    if abs(self.tech_level.value - other_civ.tech_level.value) <= 1:
                        initial_relation += 0.1
                    
                    # Influence de l'agressivité et de la coopération
                    initial_relation += (self.cooperation - 0.5) * 0.2
                    initial_relation -= (self.aggression - 0.5) * 0.2
                    
                    # Enregistrement de la relation
                    self.relations[civ_id] = max(-1.0, min(1.0, initial_relation))
                    
                    relation_type = "amicale" if initial_relation > 0 else "hostile"
                    self.add_history_event("Contact", 
                                         f"Premier contact avec {other_civ.name} - Relation {relation_type}")
    
    def _are_civilizations_close(self, other_civ):
        """Vérifie si deux civilisations sont géographiquement proches."""
        # Vérification de la proximité des territoires
        grid_size = self.manager.world.geography.grid_size
        
        for y in range(grid_size):
            for x in range(grid_size):
                if not self.territory[y, x]:
                    continue
                
                # Vérification des cellules dans un rayon
                for dy in range(-5, 6):
                    for dx in range(-5, 6):
                        nx, ny = (x + dx) % grid_size, (y + dy) % grid_size
                        
                        if other_civ.territory[ny, nx]:
                            return True
        
        return False
    
    def _check_relation_events(self, other_civ):
        """Vérifie si des événements se produisent basés sur les relations."""
        relation = self.relations[id(other_civ)]
        
        # Événements positifs
        if relation > 0.7 and random.random() < 0.1:
            event_type = random.choice(["alliance", "traité commercial", "échange culturel"])
            
            self.add_history_event("Diplomatie positive", 
                                 f"{event_type.capitalize()} avec {other_civ.name}")
            
            # Effets de l'événement
            if event_type == "alliance":
                self.relations[id(other_civ)] = min(1.0, relation + 0.1)
                self.stability += 0.05
            
            elif event_type == "traité commercial":
                self.tech_progress += 0.01
            
            elif event_type == "échange culturel":
                self.creativity += 0.02
        
        # Événements négatifs
        elif relation < -0.7 and random.random() < 0.1:
            event_type = random.choice(["conflit", "guerre", "embargo"])
            
            self.add_history_event("Diplomatie négative", 
                                 f"{event_type.capitalize()} avec {other_civ.name}")
            
            # Effets de l'événement
            if event_type == "guerre":
                self._handle_war(other_civ)
            
            elif event_type == "embargo":
                self.tech_progress -= 0.01
            
            elif event_type == "conflit":
                self.stability -= 0.05
    
    def _handle_war(self, other_civ):
        """Gère une guerre entre deux civilisations."""
        # Facteurs de puissance
        self_power = (self.population / 1000000) * (self.tech_level.value + 1)
        other_power = (other_civ.population / 1000000) * (other_civ.tech_level.value + 1)
        
        # Facteurs aléatoires
        self_power *= random.uniform(0.8, 1.2)
        other_power *= random.uniform(0.8, 1.2)
        
        # Détermination du vainqueur
        if self_power > other_power * 1.5:
            # Victoire décisive
            outcome = "victoire décisive"
            self.relations[id(other_civ)] = -0.5  # Amélioration relative
            
            # Gains territoriaux
            self._gain_territory_from(other_civ, 0.2)
            
            # Pertes de population
            self.population = int(self.population * 0.95)
            other_civ.population = int(other_civ.population * 0.7)
            
        elif self_power > other_power:
            # Victoire mineure
            outcome = "victoire mineure"
            self.relations[id(other_civ)] = -0.7
            
            # Gains territoriaux limités
            self._gain_territory_from(other_civ, 0.1)
            
            # Pertes de population
            self.population = int(self.population * 0.9)
            other_civ.population = int(other_civ.population * 0.85)
            
        elif other_power > self_power * 1.5:
            # Défaite majeure
            outcome = "défaite majeure"
            self.relations[id(other_civ)] = -0.5
            
            # Pertes territoriales
            other_civ._gain_territory_from(self, 0.2)
            
            # Pertes de population
            self.population = int(self.population * 0.7)
            other_civ.population = int(other_civ.population * 0.95)
            
        elif other_power > self_power:
            # Défaite mineure
            outcome = "défaite mineure"
            self.relations[id(other_civ)] = -0.7
            
            # Pertes territoriales limitées
            other_civ._gain_territory_from(self, 0.1)
            
            # Pertes de population
            self.population = int(self.population * 0.85)
            other_civ.population = int(other_civ.population * 0.9)
            
        else:
            # Match nul
            outcome = "match nul"
            self.relations[id(other_civ)] = -0.8
            
            # Pertes de population des deux côtés
            self.population = int(self.population * 0.85)
            other_civ.population = int(other_civ.population * 0.85)
        
        # Enregistrement du résultat
        self.add_history_event("Guerre", f"Guerre contre {other_civ.name}: {outcome}")
        
        # Impact sur la stabilité
        self.stability -= 0.1
        other_civ.stability -= 0.1
    
    def _gain_territory_from(self, other_civ, percentage):
        """
        Gagne du territoire d'une autre civilisation.
        
        Args:
            other_civ: La civilisation perdant du territoire.
            percentage: Le pourcentage de territoire à prendre (0-1).
        """
        grid_size = self.manager.world.geography.grid_size
        
        # Identification des cellules frontalières
        border_cells = []
        
        for y in range(grid_size):
            for x in range(grid_size):
                if not other_civ.territory[y, x]:
                    continue
                
                # Vérification des cellules adjacentes
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        
                        nx, ny = (x + dx) % grid_size, (y + dy) % grid_size
                        
                        # Si c'est une cellule de notre territoire adjacente à leur territoire
                        if self.territory[ny, nx]:
                            border_cells.append((x, y))
                            break
                    else:
                        continue
                    break
        
        # Calcul du nombre de cellules à prendre
        num_cells = int(len(border_cells) * percentage)
        
        if num_cells > 0 and border_cells:
            # Sélection aléatoire des cellules à prendre
            cells_to_take = random.sample(border_cells, min(num_cells, len(border_cells)))
            
            # Transfert du territoire
            for x, y in cells_to_take:
                self.territory[y, x] = True
                other_civ.territory[y, x] = False
    
    def _random_events(self):
        """Génère des événements aléatoires pour la civilisation."""
        # Probabilité de base pour un événement
        event_probability = 0.05  # 5% par an
        
        if random.random() < event_probability:
            # Sélection d'un type d'événement
            event_types = ["culturel", "politique", "économique", "catastrophe", "découverte"]
            weights = [1, 1, 1, 0.5, 0.8]  # Les catastrophes sont moins fréquentes
            
            event_type = random.choices(event_types, weights=weights)[0]
            
            # Génération de l'événement
            if event_type == "culturel":
                self._generate_cultural_event()
            elif event_type == "politique":
                self._generate_political_event()
            elif event_type == "économique":
                self._generate_economic_event()
            elif event_type == "catastrophe":
                self._generate_disaster_event()
            elif event_type == "découverte":
                self._generate_discovery_event()
    
    def _generate_cultural_event(self):
        """Génère un événement culturel."""
        events = [
            "Âge d'or artistique",
            "Révolution culturelle",
            "Mouvement philosophique majeur",
            "Réforme linguistique",
            "Festival traditionnel institutionnalisé"
        ]
        
        event = random.choice(events)
        self.add_history_event("Culture", event)
        
        # Effets de l'événement
        if event == "Âge d'or artistique":
            self.creativity += 0.1
        elif event == "Révolution culturelle":
            self.stability -= 0.1
            self.creativity += 0.15
        elif event == "Mouvement philosophique majeur":
            self.tech_progress += 0.05
        elif event == "Réforme linguistique":
            pass  # Effet symbolique
        elif event == "Festival traditionnel institutionnalisé":
            self.stability += 0.05
    
    def _generate_political_event(self):
        """Génère un événement politique."""
        events = [
            "Révolution",
            "Réforme gouvernementale",
            "Guerre civile",
            "Unification",
            "Sécession"
        ]
        
        event = random.choice(events)
        self.add_history_event("Politique", event)
        
        # Effets de l'événement
        if event == "Révolution":
            old_gov = self.government
            possible_govs = list(GovernmentType)
            self.government = random.choice(possible_govs)
            self.stability -= 0.2
            self.add_history_event("Changement de régime", 
                                 f"{old_gov.name} → {self.government.name}")
            
        elif event == "Réforme gouvernementale":
            self.stability += 0.1
            
        elif event == "Guerre civile":
            self.population = int(self.population * 0.85)
            self.stability -= 0.3
            
        elif event == "Unification":
            self.stability += 0.15
            
        elif event == "Sécession":
            # Perte de territoire
            territory_count = np.sum(self.territory)
            lost_percentage = random.uniform(0.1, 0.3)
            
            # Sélection aléatoire de cellules à perdre
            territory_indices = np.where(self.territory)
            indices_to_lose = random.sample(range(len(territory_indices[0])), 
                                          int(territory_count * lost_percentage))
            
            for idx in indices_to_lose:
                y, x = territory_indices[0][idx], territory_indices[1][idx]
                self.territory[y, x] = False
            
            self.population = int(self.population * (1 - lost_percentage))
            self.stability -= 0.1
    
    def _generate_economic_event(self):
        """Génère un événement économique."""
        events = [
            "Boom économique",
            "Récession",
            "Découverte de ressources",
            "Innovation commerciale",
            "Famine"
        ]
        
        event = random.choice(events)
        self.add_history_event("Économie", event)
        
        # Effets de l'événement
        if event == "Boom économique":
            self.tech_progress += 0.05
            self.stability += 0.05
            
        elif event == "Récession":
            self.tech_progress -= 0.03
            self.stability -= 0.1
            
        elif event == "Découverte de ressources":
            resource = random.choice(["minéraux", "énergie", "nourriture", "matériaux rares"])
            self.add_history_event("Ressources", f"Découverte de {resource}")
            self.tech_progress += 0.02
            
        elif event == "Innovation commerciale":
            self.tech_progress += 0.03
            
        elif event == "Famine":
            self.population = int(self.population * 0.9)
            self.stability -= 0.15
    
    def _generate_disaster_event(self):
        """Génère un événement catastrophique."""
        events = [
            "Épidémie",
            "Catastrophe naturelle",
            "Accident technologique",
            "Conflit interne",
            "Crise environnementale"
        ]
        
        event = random.choice(events)
        severity = random.uniform(0.1, 0.5)  # Sévérité de la catastrophe
        
        self.add_history_event("Catastrophe", f"{event} (Sévérité: {severity:.2f})")
        
        # Effets de l'événement
        if event == "Épidémie":
            self.population = int(self.population * (1 - severity * 0.3))
            self.stability -= severity * 0.2
            
        elif event == "Catastrophe naturelle":
            self.population = int(self.population * (1 - severity * 0.2))
            
            # Perte de territoire
            territory_indices = np.where(self.territory)
            indices_to_lose = random.sample(range(len(territory_indices[0])), 
                                          int(np.sum(self.territory) * severity * 0.1))
            
            for idx in indices_to_lose:
                y, x = territory_indices[0][idx], territory_indices[1][idx]
                self.territory[y, x] = False
            
        elif event == "Accident technologique":
            if self.tech_level.value >= 3:  # À partir du niveau industriel
                self.population = int(self.population * (1 - severity * 0.1))
                self.stability -= severity * 0.15
            
        elif event == "Conflit interne":
            self.stability -= severity * 0.3
            
        elif event == "Crise environnementale":
            if self.tech_level.value >= 2:  # À partir du niveau médiéval
                self.stability -= severity * 0.1
    
    def _generate_discovery_event(self):
        """Génère un événement de découverte."""
        if self.tech_level.value < 7:  # Pas au niveau maximum
            # Chance de découverte technologique anticipée
            tech_boost = random.uniform(0.1, 0.3)
            self.tech_progress += tech_boost
            
            self.add_history_event("Découverte", 
                                 f"Avancée scientifique majeure (+{tech_boost:.2f} progrès tech)")
            
            # Possibilité de découvrir une technologie spécifique
            next_level = TechLevel(min(7, self.tech_level.value + 1))
            tech_discoveries = {
                TechLevel.PRIMITIVE: ["Feu", "Outils en pierre", "Langage écrit"],
                TechLevel.AGRICULTURAL: ["Agriculture", "Poterie", "Domestication", "Métallurgie de base"],
                TechLevel.MEDIEVAL: ["Architecture", "Mathématiques", "Astronomie", "Navigation"],
                TechLevel.INDUSTRIAL: ["Machine à vapeur", "Électricité", "Chimie", "Transport mécanisé"],
                TechLevel.INFORMATION: ["Informatique", "Télécommunications", "Médecine avancée", "Énergie nucléaire"],
                TechLevel.SPACE: ["Voyage spatial", "Robotique", "Intelligence artificielle", "Biotechnologie"],
                TechLevel.ADVANCED: ["Manipulation génétique", "Nanotechnologie", "Fusion nucléaire", "Réalité virtuelle"],
                TechLevel.STELLAR: ["Propulsion FTL", "Terraformation", "Conscience numérique", "Manipulation quantique"]
            }
            
            possible_techs = tech_discoveries.get(next_level, [])
            if possible_techs and random.random() < 0.3:
                tech = random.choice(possible_techs)
                if tech not in self.technologies:
                    self.technologies.add(tech)
                    self.add_history_event("Découverte anticipée", f"Découverte de: {tech}")
    
    def _go_extinct(self, cause):
        """Marque la civilisation comme éteinte."""
        if not self.is_extinct:
            self.is_extinct = True
            self.extinction_cause = cause
            
            self.logger.warning(f"Extinction de la civilisation {self.name} - Cause: {cause} - "
                              f"Âge atteint: {self.age} ans")
            
            # Effets sur l'espèce fondatrice
            if not self.founding_species.is_extinct:
                # Réduction de la population de l'espèce
                self.founding_species.population = max(100, self.founding_species.population // 2)
                
                # Mise à jour de la carte de population
                self.founding_species.population_map *= 0.5

class CivilizationManager:
    """
    Classe gérant l'ensemble des civilisations de la planète.
    Coordonne leur émergence, leurs interactions et leur évolution.
    """
    
    def __init__(self, world):
        """
        Initialise le gestionnaire de civilisations.
        
        Args:
            world: L'instance du monde auquel ce gestionnaire appartient.
        """
        self.world = world
        self.logger = logging.getLogger('ecosphere')
        
        # Liste des civilisations
        self.civilizations = []
        self.extinct_civilizations = []
        
        # Statistiques
        self.total_civilizations_created = 0
        self.total_extinctions = 0
        
        # Paramètres
        self.emergence_probability = 0.001  # Probabilité de base pour l'émergence d'une civilisation
    
    def create_civilization(self, species):
        """
        Crée une nouvelle civilisation à partir d'une espèce intelligente.
        
        Args:
            species: L'espèce à l'origine de la civilisation.
        """
        # Vérification que l'espèce n'a pas déjà une civilisation
        for civ in self.civilizations:
            if species in civ.species:
                return None
        
        # Création de la civilisation
        civilization = Civilization(self, species)
        self.civilizations.append(civilization)
        self.total_civilizations_created += 1
        
        self.logger.warning(f"ÉVÉNEMENT MAJEUR: Émergence de la civilisation {civilization.name} "
                          f"issue de l'espèce {species.name}")
        
        return civilization
    
    def simulate_year(self):
        """Simule une année complète pour toutes les civilisations."""
        # Mise à jour de chaque civilisation
        for civilization in self.civilizations[:]:  # Copie pour éviter les problèmes de modification pendant l'itération
            civilization.update()
            
            # Vérification de l'extinction
            if civilization.is_extinct:
                self.civilizations.remove(civilization)
                self.extinct_civilizations.append(civilization)
                self.total_extinctions += 1
        
        # Vérification de l'émergence de nouvelles civilisations
        self._check_civilization_emergence()
        
        # Journalisation périodique
        if self.world.age % 100 == 0 and self.civilizations:
            self._log_civilizations_status()
    
    def _check_civilization_emergence(self):
        """Vérifie si de nouvelles civilisations émergent."""
        # Vérification pour chaque espèce intelligente
        for species in self.world.ecosystem.species:
            # Vérification des critères d'intelligence et de complexité
            if (species.intelligence >= 0.7 and 
                species.complexity >= 0.6 and 
                not species.is_extinct):
                
                # Vérification que l'espèce n'a pas déjà une civilisation
                has_civilization = False
                for civ in self.civilizations:
                    if species in civ.species:
                        has_civilization = True
                        break
                
                if not has_civilization:
                    # Probabilité d'émergence basée sur l'intelligence et la population
                    emergence_chance = self.emergence_probability * species.intelligence * (species.population / 10000)
                    
                    if random.random() < emergence_chance:
                        self.create_civilization(species)
    
    def _log_civilizations_status(self):
        """Enregistre l'état actuel des civilisations dans les logs."""
        self.logger.info(f"État des civilisations - Année {self.world.age}:")
        self.logger.info(f"  Civilisations actives: {len(self.civilizations)} - Disparues: {self.total_extinctions}")
        
        for civ in self.civilizations:
            self.logger.info(f"  {civ.name}: Niveau {civ.tech_level.name}, Population {civ.population:,}, "
                           f"Âge {civ.age} ans")
    
    def apply_catastrophe(self, event_type, severity):
        """
        Applique les effets d'une catastrophe sur les civilisations.
        
        Args:
            event_type: Type de catastrophe (meteorite, supervolcano, etc.)
            severity: Sévérité de la catastrophe (0-1)
        """
        self.logger.warning(f"Catastrophe {event_type} affecte les civilisations (sévérité: {severity:.2f})")
        
        # Impact sur chaque civilisation
        for civilization in self.civilizations:
            # Calcul de la vulnérabilité selon le niveau technologique
            vulnerability = 1.0 - (civilization.tech_level.value / 7) * 0.7
            vulnerability = max(0.3, vulnerability)  # Même les civilisations avancées sont affectées
            
            # Ajustement selon le type d'événement
            if event_type == "meteorite":
                # Impact de météorite: moins d'effet sur les civilisations spatiales
                if civilization.tech_level.value >= 5:  # Niveau spatial ou supérieur
                    vulnerability *= 0.5
                
            elif event_type == "supervolcano":
                # Éruption volcanique: moins d'effet sur les civilisations avancées
                if civilization.tech_level.value >= 4:  # Niveau information ou supérieur
                    vulnerability *= 0.7
                
            elif event_type == "solar_flare":
                # Éruption solaire: plus d'effet sur les civilisations technologiques
                if civilization.tech_level.value >= 3:  # Niveau industriel ou supérieur
                    vulnerability *= 1.3
                
            elif event_type == "pandemic":
                # Pandémie: moins d'effet sur les civilisations médicalement avancées
                if civilization.tech_level.value >= 4:  # Niveau information ou supérieur
                    vulnerability *= 0.6
            
            # Calcul de l'impact
            impact = severity * vulnerability
            
            # Application de l'impact
            if impact > 0.7:
                # Risque d'effondrement
                if random.random() < impact - 0.7:
                    civilization._go_extinct(f"Catastrophe: {event_type}")
                else:
                    # Régression technologique possible
                    if random.random() < impact - 0.5 and civilization.tech_level.value > 0:
                        old_level = civilization.tech_level
                        civilization.tech_level = TechLevel(civilization.tech_level.value - 1)
                        civilization.add_history_event("Régression", 
                                                    f"Régression technologique: {old_level.name} → {civilization.tech_level.name}")
                    
                    # Réduction drastique de la population
                    civilization.population = int(civilization.population * (1 - impact * 0.5))
                    civilization.stability -= impact * 0.3
            else:
                # Réduction de la population et de la stabilité
                civilization.population = int(civilization.population * (1 - impact * 0.3))
                civilization.stability -= impact * 0.2
            
            # Enregistrement de l'événement
            civilization.add_history_event("Catastrophe globale", 
                                         f"Impact de {event_type} (Sévérité: {severity:.2f})")
    
    def get_summary(self):
        """Retourne un résumé de l'état actuel des civilisations."""
        if not self.civilizations and not self.extinct_civilizations:
            return {
                "total_civilizations": 0,
                "active_civilizations": 0,
                "extinct_civilizations": 0,
                "details": []
            }
        
        # Détails des civilisations actives
        civ_details = []
        for civ in self.civilizations:
            civ_details.append({
                "name": civ.name,
                "age": civ.age,
                "population": civ.population,
                "tech_level": civ.tech_level.name,
                "government": civ.government.name,
                "territory_size": int(np.sum(civ.territory))
            })
        
        return {
            "total_civilizations": self.total_civilizations_created,
            "active_civilizations": len(self.civilizations),
            "extinct_civilizations": self.total_extinctions,
            "details": civ_details
        }