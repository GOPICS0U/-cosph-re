#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'écosystème pour la simulation Écosphère.
Gère l'évolution des espèces, les chaînes alimentaires et les interactions écologiques.
"""

import random
import numpy as np
import logging
from enum import Enum
from collections import defaultdict

class TrophicLevel(Enum):
    """Niveaux trophiques des espèces."""
    PRODUCER = 0  # Producteurs (plantes, etc.)
    HERBIVORE = 1  # Herbivores
    OMNIVORE = 2  # Omnivores
    CARNIVORE = 3  # Carnivores
    DECOMPOSER = 4  # Décomposeurs

class Species:
    """Classe représentant une espèce vivante dans l'écosystème."""
    
    next_id = 1  # ID auto-incrémenté pour les espèces
    
    def __init__(self, ecosystem, name=None, trophic_level=None, parent_species=None):
        """
        Initialise une nouvelle espèce.
        
        Args:
            ecosystem: L'écosystème auquel appartient cette espèce.
            name: Nom de l'espèce (généré si None).
            trophic_level: Niveau trophique de l'espèce.
            parent_species: Espèce parente (si issue d'une spéciation).
        """
        self.id = Species.next_id
        Species.next_id += 1
        
        self.ecosystem = ecosystem
        self.logger = logging.getLogger('ecosphere')
        
        # Caractéristiques de base
        self.name = name if name else self._generate_name()
        self.trophic_level = trophic_level if trophic_level else random.choice(list(TrophicLevel))
        self.parent_species = parent_species
        
        # Attributs évolutifs
        self.size = random.uniform(0.1, 1.0)  # Taille relative (0-1)
        self.complexity = random.uniform(0.1, 0.5)  # Complexité biologique (0-1)
        self.intelligence = random.uniform(0.01, 0.1)  # Intelligence (0-1)
        self.adaptability = random.uniform(0.3, 0.7)  # Capacité d'adaptation (0-1)
        self.reproduction_rate = random.uniform(0.3, 0.8)  # Taux de reproduction (0-1)
        self.lifespan = random.uniform(0.2, 0.8)  # Durée de vie relative (0-1)
        
        # Si l'espèce a un parent, elle hérite de certaines caractéristiques
        if parent_species:
            self._inherit_traits()
        
        # Attributs écologiques
        self.population = random.randint(100, 1000)
        self.habitat_preference = {}  # Préférences de biome
        self.predators = []  # Espèces qui chassent celle-ci
        self.prey = []  # Espèces chassées par celle-ci
        
        # Attributs de suivi
        self.age = 0  # Âge de l'espèce en années
        self.is_extinct = False
        self.extinction_cause = None
        
        # Génération des préférences d'habitat
        self._generate_habitat_preferences()
        
        # Distribution de la population
        self.population_map = np.zeros((ecosystem.world.geography.grid_size, 
                                       ecosystem.world.geography.grid_size))
        
        # Initialisation de la distribution
        self._initialize_population_distribution()
    
    def _generate_name(self):
        """Génère un nom aléatoire pour l'espèce."""
        prefixes = ["Xeno", "Neo", "Mega", "Micro", "Macro", "Poly", "Crypto", "Pseudo", "Proto", "Meta"]
        middle = ["morph", "pod", "derm", "saur", "phyll", "zoa", "theri", "cephal", "branch", "cyst"]
        suffixes = ["us", "a", "um", "is", "ae", "idae", "oides", "ella", "ium", "on"]
        
        return f"{random.choice(prefixes)}{random.choice(middle)}{random.choice(suffixes)}"
    
    def _inherit_traits(self):
        """Hérite des traits de l'espèce parente avec des mutations."""
        # Fonction pour muter un trait
        def mutate(value):
            mutation = random.uniform(-0.1, 0.1)
            return max(0.01, min(0.99, value + mutation))
        
        # Héritage avec mutations
        self.size = mutate(self.parent_species.size)
        self.complexity = mutate(self.parent_species.complexity)
        self.intelligence = mutate(self.parent_species.intelligence)
        self.adaptability = mutate(self.parent_species.adaptability)
        self.reproduction_rate = mutate(self.parent_species.reproduction_rate)
        self.lifespan = mutate(self.parent_species.lifespan)
        
        # Le niveau trophique peut parfois changer
        if random.random() < 0.1:
            possible_levels = list(TrophicLevel)
            current_index = possible_levels.index(self.trophic_level)
            
            # Limitation des changements à +/-1 niveau
            min_index = max(0, current_index - 1)
            max_index = min(len(possible_levels) - 1, current_index + 1)
            
            self.trophic_level = possible_levels[random.randint(min_index, max_index)]
    
    def _generate_habitat_preferences(self):
        """Génère les préférences d'habitat de l'espèce."""
        from simulation.geography import BiomeType
        
        # Initialisation des préférences (valeurs entre 0 et 1)
        for biome_type in BiomeType:
            self.habitat_preference[biome_type.value] = random.uniform(0, 0.3)
        
        # Sélection de biomes préférés
        num_preferred = random.randint(1, 3)
        preferred_biomes = random.sample(list(BiomeType), num_preferred)
        
        for biome in preferred_biomes:
            self.habitat_preference[biome.value] = random.uniform(0.7, 1.0)
        
        # Ajustements selon le niveau trophique
        if self.trophic_level == TrophicLevel.PRODUCER:
            # Les producteurs ont besoin de lumière et d'eau
            self.habitat_preference[BiomeType.DESERT.value] *= 0.5
            self.habitat_preference[BiomeType.OCEAN.value] *= 1.5
            self.habitat_preference[BiomeType.SHALLOW_WATER.value] *= 1.5
            
        elif self.trophic_level == TrophicLevel.DECOMPOSER:
            # Les décomposeurs préfèrent les environnements humides
            self.habitat_preference[BiomeType.FOREST.value] *= 1.5
            self.habitat_preference[BiomeType.JUNGLE.value] *= 1.5
            self.habitat_preference[BiomeType.SWAMP.value] *= 2.0
            
        elif self.trophic_level == TrophicLevel.CARNIVORE:
            # Les carnivores suivent leurs proies
            self.habitat_preference[BiomeType.DESERT.value] *= 0.7
    
    def _initialize_population_distribution(self):
        """Initialise la distribution de la population sur la carte."""
        grid_size = self.ecosystem.world.geography.grid_size
        biomes = self.ecosystem.world.geography.biomes
        
        # Distribution initiale basée sur les préférences d'habitat
        total_suitability = 0
        suitability_map = np.zeros((grid_size, grid_size))
        
        for y in range(grid_size):
            for x in range(grid_size):
                biome_type = biomes[y, x]
                suitability = self.habitat_preference.get(biome_type, 0)
                suitability_map[y, x] = suitability
                total_suitability += suitability
        
        # Si aucun habitat n'est adapté, distribution uniforme
        if total_suitability <= 0:
            self.population_map.fill(self.population / (grid_size * grid_size))
        else:
            # Distribution proportionnelle à l'adéquation de l'habitat
            for y in range(grid_size):
                for x in range(grid_size):
                    self.population_map[y, x] = (suitability_map[y, x] / total_suitability) * self.population
    
    def update(self):
        """Met à jour l'espèce pour une année de simulation."""
        if self.is_extinct:
            return
        
        self.age += 1
        
        # Mise à jour de la population
        self._update_population()
        
        # Vérification de l'extinction
        if self.population <= 10:
            self._go_extinct("Population trop faible")
            return
        
        # Possibilité de spéciation (création d'une nouvelle espèce)
        self._check_speciation()
        
        # Évolution des traits
        self._evolve_traits()
    
    def _update_population(self):
        """Met à jour la population de l'espèce."""
        grid_size = self.ecosystem.world.geography.grid_size
        biomes = self.ecosystem.world.geography.biomes
        climate = self.ecosystem.world.climate
        
        # Facteurs globaux affectant la population
        base_growth_rate = self.reproduction_rate * 0.2  # Croissance de base (0-20%)
        carrying_capacity = 1000000 * self.size  # Capacité de charge
        
        # Nouvelle carte de population
        new_population_map = np.zeros((grid_size, grid_size))
        total_population = 0
        
        for y in range(grid_size):
            for x in range(grid_size):
                local_pop = self.population_map[y, x]
                
                if local_pop <= 0:
                    continue
                
                # Facteurs environnementaux
                biome_type = biomes[y, x]
                habitat_suitability = self.habitat_preference.get(biome_type, 0)
                
                # Influence du climat
                temp_factor = 1.0
                precip_factor = 1.0
                
                # Ajustement selon les préférences climatiques
                if self.trophic_level == TrophicLevel.PRODUCER:
                    # Les producteurs ont besoin d'eau et de chaleur modérée
                    temp_preference = 0.5  # Température idéale
                    temp_tolerance = 0.3  # Tolérance à la température
                    
                    temp_diff = abs(climate.temperature[y, x] - temp_preference)
                    if temp_diff > temp_tolerance:
                        temp_factor = 1 - (temp_diff - temp_tolerance)
                    
                    precip_factor = climate.precipitation[y, x] * 2
                
                # Calcul de la croissance locale
                growth_rate = base_growth_rate * habitat_suitability * temp_factor * precip_factor
                
                # Ajustement par la compétition (densité-dépendance)
                competition_factor = 1 - (local_pop / carrying_capacity)
                growth_rate *= max(0, competition_factor)
                
                # Prédation
                predation_loss = 0
                for predator in self.predators:
                    predator_pop = predator.get_local_population(x, y)
                    if predator_pop > 0:
                        # Efficacité de prédation basée sur la différence de taille et d'intelligence
                        efficiency = 0.1 * (predator.size / self.size) * (predator.intelligence / self.intelligence)
                        predation_loss += efficiency * predator_pop / local_pop
                
                # Limitation des pertes par prédation
                predation_loss = min(0.5, predation_loss)
                
                # Calcul de la nouvelle population locale
                new_pop = local_pop * (1 + growth_rate - predation_loss)
                
                # Événements aléatoires (maladies, catastrophes locales)
                if random.random() < 0.01:  # 1% de chance
                    disaster_severity = random.uniform(0.1, 0.5)
                    new_pop *= (1 - disaster_severity)
                
                # Migration vers les cellules adjacentes
                migration_rate = 0.1 * self.adaptability
                migration_amount = new_pop * migration_rate
                new_pop -= migration_amount
                
                # Distribution de la migration aux cellules adjacentes
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        
                        nx, ny = (x + dx) % grid_size, (y + dy) % grid_size
                        
                        # Vérification de l'habitabilité de la destination
                        dest_biome = biomes[ny, nx]
                        dest_suitability = self.habitat_preference.get(dest_biome, 0)
                        
                        # Migration proportionnelle à l'adéquation de l'habitat
                        if dest_suitability > 0:
                            new_population_map[ny, nx] += (migration_amount / 8) * dest_suitability
                
                # Mise à jour de la population locale
                new_population_map[y, x] += new_pop
                total_population += new_pop
        
        # Mise à jour de la carte de population et de la population totale
        self.population_map = new_population_map
        self.population = int(total_population)
    
    def get_local_population(self, x, y):
        """Retourne la population locale à une position donnée."""
        return self.population_map[y, x]
    
    def _check_speciation(self):
        """Vérifie si une spéciation (création d'une nouvelle espèce) se produit."""
        # Probabilité de spéciation basée sur l'âge, la population et l'adaptabilité
        base_probability = 0.001  # 0.1% de chance par an
        age_factor = min(1.0, self.age / 1000)  # Plus l'espèce est ancienne, plus la spéciation est probable
        population_factor = min(1.0, self.population / 100000)  # Population importante favorise la spéciation
        
        speciation_probability = base_probability * age_factor * population_factor * self.adaptability
        
        if random.random() < speciation_probability:
            # Création d'une nouvelle espèce
            new_species_name = f"{self.name} {chr(random.randint(97, 122))}"  # Ajout d'une lettre
            new_species = Species(self.ecosystem, name=new_species_name, 
                                 trophic_level=self.trophic_level, parent_species=self)
            
            # Transfert d'une partie de la population
            transfer_percentage = random.uniform(0.1, 0.3)
            new_species.population = int(self.population * transfer_percentage)
            self.population = int(self.population * (1 - transfer_percentage))
            
            # Mise à jour des cartes de population
            new_species.population_map = self.population_map * transfer_percentage
            self.population_map *= (1 - transfer_percentage)
            
            # Ajout de la nouvelle espèce à l'écosystème
            self.ecosystem.add_species(new_species)
            
            self.logger.info(f"Spéciation: {self.name} a donné naissance à {new_species.name}")
            
            # Établissement des relations prédateur-proie
            self.ecosystem.update_trophic_relationships()
    
    def _evolve_traits(self):
        """Fait évoluer les traits de l'espèce au fil du temps."""
        # Probabilité d'évolution basée sur l'adaptabilité
        evolution_probability = 0.05 * self.adaptability
        
        if random.random() < evolution_probability:
            # Sélection d'un trait à faire évoluer
            traits = ["size", "complexity", "intelligence", "adaptability", 
                     "reproduction_rate", "lifespan"]
            
            trait = random.choice(traits)
            old_value = getattr(self, trait)
            
            # Amplitude de la mutation
            mutation_amplitude = random.uniform(-0.05, 0.05)
            
            # Application de la mutation
            new_value = max(0.01, min(0.99, old_value + mutation_amplitude))
            setattr(self, trait, new_value)
            
            # Détermination de l'avantage évolutif
            advantage = "neutre"
            if mutation_amplitude > 0:
                advantage = "favorable"
            elif mutation_amplitude < 0:
                advantage = "défavorable"
            
            self.logger.info(f"Évolution: {self.name} - Mutation du trait '{trait}' "
                           f"de {old_value:.2f} à {new_value:.2f} - Avantage: {advantage}")
            
            # Effets secondaires de l'évolution
            if trait == "intelligence" and new_value > 0.7 and old_value <= 0.7:
                self.logger.warning(f"Seuil d'intelligence critique atteint pour {self.name} - "
                                  f"Potentiel d'émergence de conscience")
                
                # Signaler à l'écosystème qu'une espèce intelligente est apparue
                self.ecosystem.check_for_sapience(self)
    
    def _go_extinct(self, cause):
        """Marque l'espèce comme éteinte."""
        if not self.is_extinct:
            self.is_extinct = True
            self.extinction_cause = cause
            self.population = 0
            self.population_map.fill(0)
            
            self.logger.warning(f"Extinction: {self.name} - Cause: {cause} - "
                              f"Âge atteint: {self.age} ans")
            
            # Retrait des listes de prédateurs et de proies
            for predator in self.predators:
                if self in predator.prey:
                    predator.prey.remove(self)
            
            for prey in self.prey:
                if self in prey.predators:
                    prey.predators.remove(self)

class Ecosystem:
    """
    Classe gérant l'écosystème complet de la planète.
    Gère les espèces, leurs interactions et leur évolution.
    """
    
    def __init__(self, world):
        """
        Initialise l'écosystème.
        
        Args:
            world: L'instance du monde auquel cet écosystème appartient.
        """
        self.world = world
        self.logger = logging.getLogger('ecosphere')
        
        # Liste des espèces
        self.species = []
        self.extinct_species = []
        
        # Statistiques
        self.total_species_created = 0
        self.total_extinctions = 0
        
        # Paramètres de l'écosystème
        self.biodiversity_factor = random.uniform(0.7, 1.3)  # Facteur influençant la biodiversité
        self.evolution_rate = random.uniform(0.8, 1.2)  # Vitesse d'évolution relative
        self.stability = random.uniform(0.6, 1.0)  # Stabilité de l'écosystème
    
    def seed_initial_life(self):
        """Crée les premières espèces pour amorcer l'écosystème."""
        self.logger.info("Création des espèces initiales...")
        
        # Nombre d'espèces initiales basé sur la biodiversité
        num_initial_species = int(20 * self.biodiversity_factor)
        
        # Création des producteurs (plantes, etc.)
        num_producers = int(num_initial_species * 0.5)
        for _ in range(num_producers):
            species = Species(self, trophic_level=TrophicLevel.PRODUCER)
            self.add_species(species)
        
        # Création des herbivores
        num_herbivores = int(num_initial_species * 0.25)
        for _ in range(num_herbivores):
            species = Species(self, trophic_level=TrophicLevel.HERBIVORE)
            self.add_species(species)
        
        # Création des carnivores
        num_carnivores = int(num_initial_species * 0.15)
        for _ in range(num_carnivores):
            species = Species(self, trophic_level=TrophicLevel.CARNIVORE)
            self.add_species(species)
        
        # Création des décomposeurs
        num_decomposers = int(num_initial_species * 0.1)
        for _ in range(num_decomposers):
            species = Species(self, trophic_level=TrophicLevel.DECOMPOSER)
            self.add_species(species)
        
        # Établissement des relations trophiques
        self.update_trophic_relationships()
        
        self.logger.info(f"Écosystème initial créé avec {len(self.species)} espèces")
    
    def add_species(self, species):
        """
        Ajoute une espèce à l'écosystème.
        
        Args:
            species: L'espèce à ajouter.
        """
        self.species.append(species)
        self.total_species_created += 1
    
    def update_trophic_relationships(self):
        """Met à jour les relations prédateur-proie entre les espèces."""
        # Réinitialisation des relations
        for species in self.species:
            species.predators = []
            species.prey = []
        
        # Établissement des nouvelles relations
        for predator in self.species:
            if predator.is_extinct:
                continue
                
            if predator.trophic_level in [TrophicLevel.HERBIVORE, TrophicLevel.OMNIVORE]:
                # Les herbivores et omnivores se nourrissent de producteurs
                for prey in self.species:
                    if (prey.trophic_level == TrophicLevel.PRODUCER and 
                        not prey.is_extinct and 
                        random.random() < 0.7):  # 70% de chance d'établir une relation
                        
                        predator.prey.append(prey)
                        prey.predators.append(predator)
            
            if predator.trophic_level in [TrophicLevel.CARNIVORE, TrophicLevel.OMNIVORE]:
                # Les carnivores et omnivores se nourrissent d'herbivores et parfois d'autres carnivores
                for prey in self.species:
                    if prey.is_extinct or prey == predator:
                        continue
                        
                    if prey.trophic_level == TrophicLevel.HERBIVORE:
                        # Forte probabilité de chasser les herbivores
                        if random.random() < 0.8:
                            predator.prey.append(prey)
                            prey.predators.append(predator)
                    
                    elif prey.trophic_level == TrophicLevel.OMNIVORE:
                        # Probabilité moyenne de chasser les omnivores
                        if random.random() < 0.5:
                            predator.prey.append(prey)
                            prey.predators.append(predator)
                    
                    elif prey.trophic_level == TrophicLevel.CARNIVORE:
                        # Faible probabilité de chasser d'autres carnivores
                        # Plus probable si le prédateur est plus grand
                        if (predator.size > prey.size * 1.2 and 
                            random.random() < 0.3):
                            predator.prey.append(prey)
                            prey.predators.append(predator)
            
            if predator.trophic_level == TrophicLevel.DECOMPOSER:
                # Les décomposeurs se nourrissent de matière organique morte
                # Pas de relation directe prédateur-proie
                pass
    
    def simulate_year(self):
        """Simule une année complète pour l'écosystème."""
        # Mise à jour de chaque espèce
        for species in self.species[:]:  # Copie de la liste pour éviter les problèmes de modification pendant l'itération
            species.update()
            
            # Vérification de l'extinction
            if species.is_extinct:
                self.species.remove(species)
                self.extinct_species.append(species)
                self.total_extinctions += 1
        
        # Possibilité de création de nouvelles espèces
        self._generate_new_species()
        
        # Mise à jour des relations trophiques (occasionnellement)
        if self.world.age % 10 == 0:
            self.update_trophic_relationships()
        
        # Journalisation périodique
        if self.world.age % 100 == 0:
            self._log_ecosystem_status()
    
    def _generate_new_species(self):
        """Génère de nouvelles espèces de façon aléatoire."""
        # Probabilité de base pour l'apparition d'une nouvelle espèce
        base_probability = 0.01 * self.biodiversity_factor * self.evolution_rate
        
        # Ajustement selon le nombre d'espèces existantes (équilibre)
        current_species_count = len(self.species)
        target_species_count = 50 * self.biodiversity_factor
        
        if current_species_count < target_species_count:
            # Favoriser l'apparition de nouvelles espèces
            adjusted_probability = base_probability * (1 + (target_species_count - current_species_count) / 50)
        else:
            # Réduire l'apparition de nouvelles espèces
            adjusted_probability = base_probability * 0.5
        
        if random.random() < adjusted_probability:
            # Détermination du niveau trophique
            trophic_weights = [0.5, 0.25, 0.15, 0.1, 0.1]  # Producteurs, Herbivores, Omnivores, Carnivores, Décomposeurs
            trophic_level = random.choices(list(TrophicLevel), weights=trophic_weights)[0]
            
            # Création de la nouvelle espèce
            new_species = Species(self, trophic_level=trophic_level)
            self.add_species(new_species)
            
            self.logger.info(f"Nouvelle espèce apparue: {new_species.name} ({trophic_level.name})")
            
            # Mise à jour des relations trophiques
            self.update_trophic_relationships()
    
    def _log_ecosystem_status(self):
        """Enregistre l'état actuel de l'écosystème dans les logs."""
        # Comptage des espèces par niveau trophique
        trophic_counts = defaultdict(int)
        for species in self.species:
            trophic_counts[species.trophic_level.name] += 1
        
        # Calcul de la population totale
        total_pop = self.total_population()
        
        self.logger.info(f"État de l'écosystème - Année {self.world.age}:")
        self.logger.info(f"  Espèces vivantes: {len(self.species)} - Extinctions: {self.total_extinctions}")
        self.logger.info(f"  Population totale: {total_pop:,}")
        
        for level, count in trophic_counts.items():
            self.logger.info(f"  {level}: {count} espèces")
    
    def total_population(self):
        """Retourne la population totale de toutes les espèces."""
        return sum(species.population for species in self.species)
    
    def check_for_sapience(self, species):
        """
        Vérifie si une espèce a atteint un niveau d'intelligence suffisant pour développer une conscience.
        
        Args:
            species: L'espèce à vérifier.
        """
        # Seuils pour le développement d'une conscience
        intelligence_threshold = 0.7
        complexity_threshold = 0.6
        
        if (species.intelligence >= intelligence_threshold and 
            species.complexity >= complexity_threshold and 
            not species.is_extinct):
            
            self.logger.warning(f"ÉVÉNEMENT MAJEUR: L'espèce {species.name} a développé une conscience!")
            
            # Création d'une civilisation primitive
            if hasattr(self.world, 'civilization_manager'):
                self.world.civilization_manager.create_civilization(species)
    
    def apply_catastrophe(self, event_type, severity):
        """
        Applique les effets d'une catastrophe sur l'écosystème.
        
        Args:
            event_type: Type de catastrophe (meteorite, supervolcano, etc.)
            severity: Sévérité de la catastrophe (0-1)
        """
        self.logger.warning(f"Catastrophe {event_type} affecte l'écosystème (sévérité: {severity:.2f})")
        
        # Impact sur chaque espèce
        for species in self.species:
            # Calcul de la vulnérabilité de l'espèce
            vulnerability = 1 - species.adaptability
            
            # Ajustement selon le type d'événement
            if event_type == "meteorite":
                # Impact de météorite: affecte plus les grandes espèces
                vulnerability *= (0.5 + 0.5 * species.size)
                
            elif event_type == "supervolcano":
                # Éruption volcanique: affecte plus les espèces terrestres
                if species.trophic_level == TrophicLevel.PRODUCER:
                    vulnerability *= 1.5  # Les plantes sont très affectées
                
            elif event_type == "solar_flare":
                # Éruption solaire: affecte plus les espèces en surface
                if species.trophic_level == TrophicLevel.PRODUCER:
                    vulnerability *= 1.3
                
            elif event_type == "pandemic":
                # Pandémie: affecte plus les espèces sociales et complexes
                vulnerability *= (0.5 + 0.5 * species.complexity)
                if species.intelligence > 0.5:
                    vulnerability *= 1.2  # Les espèces sociales sont plus vulnérables
            
            # Calcul de l'impact
            impact = severity * vulnerability
            
            # Application de l'impact
            if impact > 0.8:
                # Extinction possible
                if random.random() < impact - 0.8:
                    species._go_extinct(f"Catastrophe: {event_type}")
                else:
                    # Réduction drastique de la population
                    species.population = int(species.population * (1 - impact * 0.9))
                    species.population_map *= (1 - impact * 0.9)
            else:
                # Réduction de la population
                species.population = int(species.population * (1 - impact * 0.5))
                species.population_map *= (1 - impact * 0.5)
    
    def get_summary(self):
        """Retourne un résumé de l'état actuel de l'écosystème."""
        # Comptage des espèces par niveau trophique
        trophic_counts = defaultdict(int)
        for species in self.species:
            trophic_counts[species.trophic_level.name] += 1
        
        # Identification des espèces dominantes
        dominant_species = []
        if self.species:
            sorted_species = sorted(self.species, key=lambda s: s.population, reverse=True)
            dominant_species = [(s.name, s.population) for s in sorted_species[:3]]
        
        return {
            "total_species": len(self.species),
            "extinct_species": self.total_extinctions,
            "total_population": self.total_population(),
            "trophic_distribution": dict(trophic_counts),
            "dominant_species": dominant_species,
            "biodiversity_factor": self.biodiversity_factor,
            "evolution_rate": self.evolution_rate
        }