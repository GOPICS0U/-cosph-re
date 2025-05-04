#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de géographie pour la simulation Écosphère.
Gère la génération et l'évolution du terrain de la planète.
"""

import random
import numpy as np
from enum import Enum
import logging

class BiomeType(Enum):
    """Types de biomes possibles sur la planète."""
    OCEAN = 0
    SHALLOW_WATER = 1
    BEACH = 2
    PLAINS = 3
    FOREST = 4
    JUNGLE = 5
    DESERT = 6
    SAVANNA = 7
    TUNDRA = 8
    MOUNTAINS = 9
    ICE = 10
    VOLCANIC = 11
    SWAMP = 12

class Geography:
    """
    Classe gérant la géographie de la planète.
    Génère et fait évoluer le terrain, les océans, les montagnes, etc.
    """
    
    def __init__(self, world):
        """
        Initialise la géographie du monde.
        
        Args:
            world: L'instance du monde auquel cette géographie appartient.
        """
        self.world = world
        self.logger = logging.getLogger('ecosphere')
        
        # Paramètres de la planète
        self.grid_size = 256  # Taille de la grille pour la génération procédurale
        self.sea_level = 0.5  # Niveau de la mer (0-1)
        self.mountain_level = 0.8  # Seuil pour les montagnes
        
        # Matrices pour stocker les données géographiques
        self.elevation = None  # Altitude du terrain
        self.moisture = None  # Humidité du sol
        self.temperature_base = None  # Température de base (avant effets climatiques)
        self.biomes = None  # Types de biomes
        
        # Caractéristiques planétaires
        self.land_percentage = random.uniform(25, 75)  # % de terres émergées
        self.has_axial_tilt = random.random() > 0.1  # Présence d'inclinaison axiale (saisons)
        self.axial_tilt = random.uniform(10, 30) if self.has_axial_tilt else 0
        self.day_length = random.uniform(18, 36)  # Durée d'un jour en heures
        self.year_length = random.randint(200, 500)  # Nombre de jours dans une année
        
        # Plaques tectoniques
        self.num_plates = random.randint(5, 15)
        self.tectonic_activity = random.uniform(0.1, 1.0)  # Niveau d'activité tectonique
    
    def generate(self):
        """Génère la géographie complète de la planète."""
        self.logger.info("Génération du terrain...")
        self._generate_elevation()
        
        self.logger.info("Génération de l'humidité...")
        self._generate_moisture()
        
        self.logger.info("Génération des températures de base...")
        self._generate_base_temperature()
        
        self.logger.info("Détermination des biomes...")
        self._determine_biomes()
        
        # Calcul des statistiques
        land_cells = np.sum(self.elevation > self.sea_level)
        total_cells = self.grid_size * self.grid_size
        actual_land_percentage = (land_cells / total_cells) * 100
        
        self.logger.info(f"Géographie générée: {actual_land_percentage:.1f}% de terres émergées")
        self.logger.info(f"Inclinaison axiale: {self.axial_tilt:.1f}° - Durée d'un jour: {self.day_length:.1f}h")
        self.logger.info(f"Année: {self.year_length} jours - Activité tectonique: {self.tectonic_activity:.2f}")
    
    def _generate_elevation(self):
        """Génère la carte d'élévation en utilisant du bruit de Perlin."""
        # Initialisation de la matrice d'élévation
        self.elevation = np.zeros((self.grid_size, self.grid_size))
        
        # Paramètres pour le bruit de Perlin
        octaves = 6
        persistence = 0.5
        lacunarity = 2.0
        
        # Génération du bruit de Perlin (simulé avec plusieurs octaves de bruit)
        for octave in range(octaves):
            frequency = lacunarity ** octave
            amplitude = persistence ** octave
            
            # Génération d'une couche de bruit
            noise_layer = np.zeros((self.grid_size, self.grid_size))
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    # Utilisation de sin/cos pour simuler un bruit cohérent
                    nx = x / self.grid_size * frequency
                    ny = y / self.grid_size * frequency
                    noise_value = (np.sin(nx * 10) * np.cos(ny * 10) + 
                                  np.sin(nx * 20 + 5) * np.cos(ny * 20 + 3)) * 0.5 + 0.5
                    noise_layer[y, x] = noise_value
            
            # Ajout de la couche à l'élévation totale
            self.elevation += noise_layer * amplitude
        
        # Normalisation entre 0 et 1
        min_val = np.min(self.elevation)
        max_val = np.max(self.elevation)
        self.elevation = (self.elevation - min_val) / (max_val - min_val)
        
        # Ajustement pour obtenir le pourcentage de terres souhaité
        sorted_elevations = np.sort(self.elevation.flatten())
        target_index = int((1 - self.land_percentage / 100) * len(sorted_elevations))
        self.sea_level = sorted_elevations[target_index]
    
    def _generate_moisture(self):
        """Génère la carte d'humidité."""
        # Initialisation de la matrice d'humidité
        self.moisture = np.zeros((self.grid_size, self.grid_size))
        
        # Paramètres pour le bruit
        octaves = 4
        persistence = 0.6
        lacunarity = 2.0
        
        # Génération du bruit (simulé)
        for octave in range(octaves):
            frequency = lacunarity ** octave
            amplitude = persistence ** octave
            
            # Génération d'une couche de bruit
            noise_layer = np.zeros((self.grid_size, self.grid_size))
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    nx = x / self.grid_size * frequency
                    ny = y / self.grid_size * frequency
                    noise_value = (np.sin(nx * 15 + 2) * np.cos(ny * 15 + 7) + 
                                  np.sin(nx * 30 + 10) * np.cos(ny * 30 + 5)) * 0.5 + 0.5
                    noise_layer[y, x] = noise_value
            
            # Ajout de la couche à l'humidité totale
            self.moisture += noise_layer * amplitude
        
        # Normalisation entre 0 et 1
        min_val = np.min(self.moisture)
        max_val = np.max(self.moisture)
        self.moisture = (self.moisture - min_val) / (max_val - min_val)
        
        # Influence de la proximité de l'eau sur l'humidité
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.elevation[y, x] > self.sea_level:  # Terre
                    # Recherche de l'eau la plus proche
                    min_dist = float('inf')
                    for dy in range(-10, 11):
                        for dx in range(-10, 11):
                            nx, ny = (x + dx) % self.grid_size, (y + dy) % self.grid_size
                            if self.elevation[ny, nx] <= self.sea_level:  # Eau
                                dist = np.sqrt(dx**2 + dy**2)
                                min_dist = min(min_dist, dist)
                    
                    # Influence de la distance à l'eau
                    if min_dist < 10:
                        moisture_boost = 1 - (min_dist / 10)
                        self.moisture[y, x] = self.moisture[y, x] * 0.7 + moisture_boost * 0.3
    
    def _generate_base_temperature(self):
        """Génère la carte de température de base (avant effets climatiques)."""
        # Initialisation de la matrice de température
        self.temperature_base = np.zeros((self.grid_size, self.grid_size))
        
        # Température basée sur la latitude (plus chaud à l'équateur, plus froid aux pôles)
        for y in range(self.grid_size):
            # Latitude normalisée entre -1 (pôle sud) et 1 (pôle nord)
            latitude = 2 * (y / self.grid_size) - 1
            
            # Température de base selon la latitude (courbe en cloche)
            base_temp = 1 - latitude**2
            
            for x in range(self.grid_size):
                self.temperature_base[y, x] = base_temp
        
        # Influence de l'altitude sur la température
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.elevation[y, x] > self.sea_level:
                    # Plus l'altitude est élevée, plus il fait froid
                    altitude_factor = (self.elevation[y, x] - self.sea_level) / (1 - self.sea_level)
                    self.temperature_base[y, x] -= altitude_factor * 0.5
        
        # Normalisation entre 0 et 1
        min_val = np.min(self.temperature_base)
        max_val = np.max(self.temperature_base)
        self.temperature_base = (self.temperature_base - min_val) / (max_val - min_val)
    
    def _determine_biomes(self):
        """Détermine les biomes en fonction de l'élévation, l'humidité et la température."""
        self.biomes = np.zeros((self.grid_size, self.grid_size), dtype=int)
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                elevation = self.elevation[y, x]
                moisture = self.moisture[y, x]
                temperature = self.temperature_base[y, x]
                
                # Détermination du biome
                if elevation <= self.sea_level:
                    # Zones aquatiques
                    if elevation > self.sea_level - 0.1:
                        self.biomes[y, x] = BiomeType.SHALLOW_WATER.value
                    else:
                        self.biomes[y, x] = BiomeType.OCEAN.value
                
                elif elevation <= self.sea_level + 0.02:
                    # Plages et côtes
                    self.biomes[y, x] = BiomeType.BEACH.value
                
                elif elevation >= self.mountain_level:
                    # Zones montagneuses
                    if temperature < 0.2:
                        self.biomes[y, x] = BiomeType.ICE.value
                    else:
                        self.biomes[y, x] = BiomeType.MOUNTAINS.value
                        
                        # Zones volcaniques (rares)
                        if random.random() < 0.05 * self.tectonic_activity:
                            self.biomes[y, x] = BiomeType.VOLCANIC.value
                
                else:
                    # Autres biomes terrestres
                    if temperature < 0.2:
                        # Zones froides
                        self.biomes[y, x] = BiomeType.TUNDRA.value
                    
                    elif temperature < 0.4:
                        # Zones tempérées
                        if moisture < 0.3:
                            self.biomes[y, x] = BiomeType.PLAINS.value
                        else:
                            self.biomes[y, x] = BiomeType.FOREST.value
                    
                    else:
                        # Zones chaudes
                        if moisture < 0.2:
                            self.biomes[y, x] = BiomeType.DESERT.value
                        elif moisture < 0.5:
                            self.biomes[y, x] = BiomeType.SAVANNA.value
                        elif moisture < 0.8:
                            self.biomes[y, x] = BiomeType.FOREST.value
                        else:
                            if temperature > 0.7:
                                self.biomes[y, x] = BiomeType.JUNGLE.value
                            else:
                                self.biomes[y, x] = BiomeType.SWAMP.value
    
    def get_biome_name(self, biome_id):
        """Retourne le nom d'un biome à partir de son ID."""
        return BiomeType(biome_id).name
    
    def get_biome_stats(self):
        """Retourne des statistiques sur les biomes de la planète."""
        biome_counts = {}
        total_cells = self.grid_size * self.grid_size
        
        for biome_type in BiomeType:
            count = np.sum(self.biomes == biome_type.value)
            percentage = (count / total_cells) * 100
            biome_counts[biome_type.name] = percentage
        
        return biome_counts
    
    def apply_tectonic_event(self, intensity=None):
        """
        Applique un événement tectonique (tremblement de terre, éruption volcanique).
        
        Args:
            intensity (float, optional): Intensité de l'événement (0-1).
        """
        if intensity is None:
            intensity = random.uniform(0.1, 1.0) * self.tectonic_activity
        
        # Sélection d'un point d'origine pour l'événement
        epicenter_x = random.randint(0, self.grid_size - 1)
        epicenter_y = random.randint(0, self.grid_size - 1)
        
        # Rayon d'impact basé sur l'intensité
        impact_radius = int(10 * intensity)
        
        # Type d'événement
        is_volcanic = self.biomes[epicenter_y, epicenter_x] == BiomeType.VOLCANIC.value or random.random() < 0.3
        
        event_type = "Éruption volcanique" if is_volcanic else "Tremblement de terre"
        self.logger.info(f"Événement tectonique: {event_type} d'intensité {intensity:.2f} aux coordonnées ({epicenter_x}, {epicenter_y})")
        
        # Application des effets
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Distance à l'épicentre
                dx = min(abs(x - epicenter_x), self.grid_size - abs(x - epicenter_x))
                dy = min(abs(y - epicenter_y), self.grid_size - abs(y - epicenter_y))
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance <= impact_radius:
                    # Effet décroissant avec la distance
                    effect = (1 - distance / impact_radius) * intensity
                    
                    if is_volcanic and distance <= impact_radius / 3:
                        # Création de zones volcaniques près de l'épicentre
                        if self.elevation[y, x] > self.sea_level:
                            self.biomes[y, x] = BiomeType.VOLCANIC.value
                            
                            # Augmentation de l'élévation
                            self.elevation[y, x] = min(1.0, self.elevation[y, x] + effect * 0.2)
                    
                    elif effect > 0.5 and random.random() < effect * 0.3:
                        # Modification aléatoire du terrain
                        if self.elevation[y, x] > self.sea_level:
                            # Possibilité de créer des fissures (eau)
                            if random.random() < 0.1:
                                self.elevation[y, x] = self.sea_level - 0.05
                                self.biomes[y, x] = BiomeType.SHALLOW_WATER.value
                        else:
                            # Possibilité de faire émerger des terres
                            if random.random() < 0.1:
                                self.elevation[y, x] = self.sea_level + 0.05
                                self.biomes[y, x] = BiomeType.BEACH.value