#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de climat pour la simulation Écosphère.
Gère les conditions météorologiques, les saisons et les événements climatiques.
"""

import random
import numpy as np
import logging
from enum import Enum

class WeatherType(Enum):
    """Types de conditions météorologiques possibles."""
    CLEAR = 0
    CLOUDY = 1
    RAINY = 2
    STORMY = 3
    SNOWY = 4
    FOGGY = 5
    HEATWAVE = 6
    BLIZZARD = 7
    HURRICANE = 8
    DROUGHT = 9

class Climate:
    """
    Classe gérant le climat de la planète.
    Simule les conditions météorologiques, les saisons et les événements climatiques.
    """
    
    def __init__(self, world):
        """
        Initialise le climat du monde.
        
        Args:
            world: L'instance du monde auquel ce climat appartient.
        """
        self.world = world
        self.logger = logging.getLogger('ecosphere')
        
        # Paramètres climatiques
        self.grid_size = world.geography.grid_size
        self.temperature = None  # Température actuelle
        self.precipitation = None  # Précipitations actuelles
        self.wind_direction = None  # Direction du vent (en degrés)
        self.wind_strength = None  # Force du vent
        
        # Paramètres des saisons
        self.current_day = 0
        self.current_season = 0  # 0: printemps, 1: été, 2: automne, 3: hiver
        self.season_names = ["Printemps", "Été", "Automne", "Hiver"]
        self.season_length = world.geography.year_length // 4
        
        # Événements climatiques en cours
        self.active_events = []
        
        # Tendances climatiques à long terme
        self.global_warming = 0  # Réchauffement global (0-1)
        self.climate_stability = random.uniform(0.7, 1.0)  # Stabilité du climat (0-1)
    
    def initialize(self):
        """Initialise les conditions climatiques de base."""
        # Copie des températures de base depuis la géographie
        self.temperature = np.copy(self.world.geography.temperature_base)
        
        # Initialisation des précipitations (basées sur l'humidité)
        self.precipitation = np.copy(self.world.geography.moisture)
        
        # Initialisation des vents
        self.wind_direction = np.random.uniform(0, 360, (self.grid_size, self.grid_size))
        self.wind_strength = np.random.uniform(0, 1, (self.grid_size, self.grid_size))
        
        # Ajustement initial en fonction de la saison
        self._apply_seasonal_effects()
        
        self.logger.info(f"Climat initialisé - Saison actuelle: {self.season_names[self.current_season]}")
    
    def simulate_year(self):
        """Simule une année complète de climat."""
        # Simulation jour par jour
        for day in range(self.world.geography.year_length):
            self.current_day = day
            
            # Détermination de la saison
            old_season = self.current_season
            self.current_season = (day // self.season_length) % 4
            
            # Notification de changement de saison
            if self.current_season != old_season:
                self.logger.info(f"Nouvelle saison: {self.season_names[self.current_season]}")
                self._apply_seasonal_effects()
            
            # Mise à jour des conditions météorologiques (tous les 10 jours pour optimiser)
            if day % 10 == 0:
                self._update_weather()
            
            # Génération d'événements climatiques aléatoires
            self._generate_random_events()
            
            # Mise à jour des événements actifs
            self._update_active_events()
        
        # Évolution climatique à long terme
        self._update_long_term_trends()
    
    def _apply_seasonal_effects(self):
        """Applique les effets de la saison actuelle sur le climat."""
        # Facteurs saisonniers pour la température et les précipitations
        season_temp_factors = [0.0, 0.3, 0.0, -0.3]  # Printemps, Été, Automne, Hiver
        season_precip_factors = [0.2, -0.1, 0.2, 0.1]  # Printemps, Été, Automne, Hiver
        
        # Si la planète n'a pas d'inclinaison axiale, les saisons ont moins d'effet
        if not self.world.geography.has_axial_tilt:
            season_temp_factors = [f * 0.2 for f in season_temp_factors]
            season_precip_factors = [f * 0.2 for f in season_precip_factors]
        
        # Application des effets saisonniers
        temp_factor = season_temp_factors[self.current_season]
        precip_factor = season_precip_factors[self.current_season]
        
        # Réinitialisation à partir des valeurs de base
        self.temperature = np.copy(self.world.geography.temperature_base)
        self.precipitation = np.copy(self.world.geography.moisture)
        
        # Application des facteurs saisonniers
        for y in range(self.grid_size):
            # Effet plus fort aux latitudes élevées
            latitude = abs(2 * (y / self.grid_size) - 1)
            seasonal_intensity = latitude * self.world.geography.axial_tilt / 30
            
            for x in range(self.grid_size):
                # Modification de la température
                self.temperature[y, x] += temp_factor * seasonal_intensity
                
                # Modification des précipitations
                self.precipitation[y, x] += precip_factor * seasonal_intensity
        
        # Normalisation des valeurs
        self.temperature = np.clip(self.temperature, 0, 1)
        self.precipitation = np.clip(self.precipitation, 0, 1)
    
    def _update_weather(self):
        """Met à jour les conditions météorologiques locales."""
        # Mise à jour des vents
        self._update_wind_patterns()
        
        # Diffusion de la chaleur et de l'humidité par les vents
        self._diffuse_heat_and_moisture()
        
        # Influence de l'élévation sur les précipitations (effet orographique)
        self._apply_orographic_effect()
    
    def _update_wind_patterns(self):
        """Met à jour les modèles de vent sur la planète."""
        # Facteurs influençant les vents
        coriolis_strength = 0.2  # Force de Coriolis
        thermal_gradient = 0.3  # Gradient thermique
        
        for y in range(self.grid_size):
            # Latitude normalisée entre -1 (pôle sud) et 1 (pôle nord)
            latitude = 2 * (y / self.grid_size) - 1
            
            # Direction de base des vents selon la latitude (vents d'ouest, alizés, etc.)
            if abs(latitude) < 0.3:  # Zone équatoriale
                base_direction = 270  # Vent d'est
            elif abs(latitude) < 0.6:  # Zones subtropicales
                base_direction = 90  # Vent d'ouest
            else:  # Zones polaires
                base_direction = 270 if latitude > 0 else 90
            
            for x in range(self.grid_size):
                # Influence de la température locale sur la direction du vent
                temp_gradient_x = self.temperature[(y+1) % self.grid_size, x] - self.temperature[y-1, x]
                temp_gradient_y = self.temperature[y, (x+1) % self.grid_size] - self.temperature[y, x-1]
                
                # Calcul de la nouvelle direction
                direction_change = np.arctan2(temp_gradient_y, temp_gradient_x) * 180 / np.pi
                coriolis_effect = coriolis_strength * latitude * 30  # Effet de Coriolis
                
                new_direction = (base_direction + 
                                direction_change * thermal_gradient + 
                                coriolis_effect + 
                                random.uniform(-10, 10)) % 360
                
                # Mise à jour de la direction du vent
                self.wind_direction[y, x] = new_direction
                
                # Mise à jour de la force du vent
                temp_diff = abs(temp_gradient_x) + abs(temp_gradient_y)
                self.wind_strength[y, x] = 0.3 + 0.7 * temp_diff + random.uniform(-0.1, 0.1)
                self.wind_strength[y, x] = np.clip(self.wind_strength[y, x], 0, 1)
    
    def _diffuse_heat_and_moisture(self):
        """Diffuse la chaleur et l'humidité selon les vents."""
        # Copies temporaires pour éviter les modifications en cours de diffusion
        new_temp = np.copy(self.temperature)
        new_precip = np.copy(self.precipitation)
        
        diffusion_rate = 0.1  # Taux de diffusion
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Direction et force du vent
                direction = self.wind_direction[y, x]
                strength = self.wind_strength[y, x]
                
                # Calcul des coordonnées de la cellule cible (dans la direction du vent)
                dx = int(np.cos(direction * np.pi / 180) * strength * 3)
                dy = int(np.sin(direction * np.pi / 180) * strength * 3)
                
                target_x = (x + dx) % self.grid_size
                target_y = (y + dy) % self.grid_size
                
                # Diffusion de la chaleur
                temp_diff = self.temperature[y, x] - self.temperature[target_y, target_x]
                new_temp[target_y, target_x] += temp_diff * diffusion_rate * strength
                
                # Diffusion de l'humidité (les vents transportent l'humidité)
                if self.world.geography.elevation[y, x] <= self.world.geography.sea_level:
                    # L'eau est une source d'humidité
                    moisture_transfer = strength * diffusion_rate * 2
                    new_precip[target_y, target_x] += moisture_transfer
        
        # Mise à jour des matrices
        self.temperature = np.clip(new_temp, 0, 1)
        self.precipitation = np.clip(new_precip, 0, 1)
    
    def _apply_orographic_effect(self):
        """Applique l'effet orographique (pluie sur les montagnes face au vent)."""
        # Copies temporaires
        new_precip = np.copy(self.precipitation)
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.world.geography.elevation[y, x] > self.world.geography.sea_level:
                    # Direction du vent
                    wind_dir = self.wind_direction[y, x]
                    wind_str = self.wind_strength[y, x]
                    
                    # Coordonnées de la cellule d'où vient le vent
                    upwind_x = int(x - np.cos(wind_dir * np.pi / 180) * 2) % self.grid_size
                    upwind_y = int(y - np.sin(wind_dir * np.pi / 180) * 2) % self.grid_size
                    
                    # Si on monte en altitude face au vent
                    if (self.world.geography.elevation[y, x] > 
                        self.world.geography.elevation[upwind_y, upwind_x]):
                        
                        # Augmentation des précipitations du côté face au vent
                        elevation_diff = (self.world.geography.elevation[y, x] - 
                                         self.world.geography.elevation[upwind_y, upwind_x])
                        
                        precip_increase = elevation_diff * wind_str * 0.5
                        new_precip[y, x] += precip_increase
                        
                        # Coordonnées de la cellule sous le vent
                        downwind_x = int(x + np.cos(wind_dir * np.pi / 180) * 2) % self.grid_size
                        downwind_y = int(y + np.sin(wind_dir * np.pi / 180) * 2) % self.grid_size
                        
                        # Diminution des précipitations du côté sous le vent (effet d'ombre pluviométrique)
                        if (0 <= downwind_y < self.grid_size and 
                            0 <= downwind_x < self.grid_size):
                            new_precip[downwind_y, downwind_x] -= precip_increase * 0.7
        
        # Mise à jour des précipitations
        self.precipitation = np.clip(new_precip, 0, 1)
    
    def _generate_random_events(self):
        """Génère des événements climatiques aléatoires."""
        # Probabilité de base pour un événement
        base_probability = 0.001  # 0.1% par jour
        
        # Ajustement selon la stabilité climatique
        event_probability = base_probability * (2 - self.climate_stability)
        
        if random.random() < event_probability:
            # Sélection d'un type d'événement
            possible_events = list(WeatherType)
            
            # Pondération des événements selon le climat
            weights = [1] * len(possible_events)
            
            # Ajustement des poids selon la saison et le climat global
            if self.current_season == 1:  # Été
                weights[WeatherType.HEATWAVE.value] *= 3
                weights[WeatherType.DROUGHT.value] *= 2
            elif self.current_season == 3:  # Hiver
                weights[WeatherType.BLIZZARD.value] *= 3
                weights[WeatherType.SNOWY.value] *= 2
            
            # Influence du réchauffement global
            weights[WeatherType.HEATWAVE.value] *= (1 + self.global_warming * 5)
            weights[WeatherType.HURRICANE.value] *= (1 + self.global_warming * 3)
            weights[WeatherType.DROUGHT.value] *= (1 + self.global_warming * 2)
            
            # Sélection pondérée
            event_type = random.choices(possible_events, weights=weights)[0]
            
            # Sélection d'une région pour l'événement
            region_x = random.randint(0, self.grid_size - 1)
            region_y = random.randint(0, self.grid_size - 1)
            
            # Durée de l'événement (en jours)
            duration = random.randint(1, 30)
            
            # Intensité de l'événement
            intensity = random.uniform(0.3, 1.0)
            
            # Création de l'événement
            event = {
                'type': event_type,
                'x': region_x,
                'y': region_y,
                'radius': int(10 * intensity),
                'duration': duration,
                'intensity': intensity,
                'days_active': 0
            }
            
            # Ajout à la liste des événements actifs
            self.active_events.append(event)
            
            # Journalisation de l'événement
            self.logger.info(f"Événement climatique: {event_type.name} d'intensité {intensity:.2f} "
                           f"aux coordonnées ({region_x}, {region_y}), durée prévue: {duration} jours")
            
            # Application des effets initiaux
            self._apply_event_effects(event)
    
    def _update_active_events(self):
        """Met à jour les événements climatiques actifs."""
        remaining_events = []
        
        for event in self.active_events:
            # Incrémentation de la durée active
            event['days_active'] += 1
            
            # Vérification si l'événement est toujours actif
            if event['days_active'] <= event['duration']:
                # Application des effets continus
                self._apply_event_effects(event)
                remaining_events.append(event)
            else:
                # L'événement se termine
                self.logger.info(f"Fin de l'événement climatique: {event['type'].name}")
        
        # Mise à jour de la liste des événements actifs
        self.active_events = remaining_events
    
    def _apply_event_effects(self, event):
        """
        Applique les effets d'un événement climatique.
        
        Args:
            event: Dictionnaire contenant les informations sur l'événement.
        """
        event_type = event['type']
        center_x, center_y = event['x'], event['y']
        radius = event['radius']
        intensity = event['intensity']
        
        # Application des effets selon le type d'événement
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Distance au centre de l'événement
                dx = min(abs(x - center_x), self.grid_size - abs(x - center_x))
                dy = min(abs(y - center_y), self.grid_size - abs(y - center_y))
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance <= radius:
                    # Effet décroissant avec la distance
                    effect = (1 - distance / radius) * intensity
                    
                    if event_type == WeatherType.RAINY or event_type == WeatherType.STORMY:
                        # Augmentation des précipitations
                        self.precipitation[y, x] += effect * 0.3
                    
                    elif event_type == WeatherType.HEATWAVE:
                        # Augmentation de la température, diminution des précipitations
                        self.temperature[y, x] += effect * 0.2
                        self.precipitation[y, x] -= effect * 0.3
                    
                    elif event_type == WeatherType.BLIZZARD or event_type == WeatherType.SNOWY:
                        # Diminution de la température, augmentation des précipitations
                        self.temperature[y, x] -= effect * 0.2
                        self.precipitation[y, x] += effect * 0.2
                    
                    elif event_type == WeatherType.HURRICANE:
                        # Augmentation des précipitations et des vents
                        self.precipitation[y, x] += effect * 0.5
                        self.wind_strength[y, x] += effect * 0.7
                    
                    elif event_type == WeatherType.DROUGHT:
                        # Diminution des précipitations, légère augmentation de la température
                        self.precipitation[y, x] -= effect * 0.4
                        self.temperature[y, x] += effect * 0.1
        
        # Normalisation des valeurs
        self.temperature = np.clip(self.temperature, 0, 1)
        self.precipitation = np.clip(self.precipitation, 0, 1)
        self.wind_strength = np.clip(self.wind_strength, 0, 1)
    
    def _update_long_term_trends(self):
        """Met à jour les tendances climatiques à long terme."""
        # Évolution du réchauffement global (très lente)
        # Influencé par les civilisations avancées et les événements catastrophiques
        civilization_factor = 0
        
        # Vérification de l'existence de civilisations industrielles
        if hasattr(self.world, 'civilization_manager'):
            for civ in self.world.civilization_manager.civilizations:
                if civ.tech_level >= 3:  # Niveau industriel ou supérieur
                    civilization_factor += 0.01 * (civ.tech_level - 2) * (civ.population / 1000000)
        
        # Mise à jour du réchauffement global
        self.global_warming += civilization_factor
        self.global_warming = min(1.0, self.global_warming)
        
        # Si le réchauffement devient significatif, le journaliser
        if self.global_warming > 0.1 and self.world.age % 100 == 0:
            self.logger.warning(f"Réchauffement global: {self.global_warming:.2f} - "
                              f"Impacts sur le climat de plus en plus visibles")
    
    def apply_catastrophe(self, event_type, severity):
        """
        Applique les effets d'une catastrophe sur le climat.
        
        Args:
            event_type: Type de catastrophe (meteorite, supervolcano, etc.)
            severity: Sévérité de la catastrophe (0-1)
        """
        if event_type == "meteorite":
            # Impact de météorite: refroidissement global (hiver d'impact)
            self.logger.warning(f"Impact de météorite: refroidissement global en cours")
            
            # Refroidissement proportionnel à la sévérité
            cooling_factor = severity * 0.3
            self.temperature -= cooling_factor
            
            # Augmentation des précipitations (poussières -> pluies)
            self.precipitation += severity * 0.2
            
        elif event_type == "supervolcano":
            # Éruption supervolcanique: refroidissement global, changements de vents
            self.logger.warning(f"Éruption supervolcanique: modifications climatiques majeures")
            
            # Refroidissement global
            cooling_factor = severity * 0.25
            self.temperature -= cooling_factor
            
            # Perturbation des vents
            self.wind_direction += np.random.uniform(-60, 60, self.wind_direction.shape)
            self.wind_strength += np.random.uniform(0, severity * 0.5, self.wind_strength.shape)
            
        elif event_type == "solar_flare":
            # Éruption solaire: réchauffement temporaire
            self.logger.warning(f"Éruption solaire: réchauffement temporaire")
            
            # Réchauffement proportionnel à la sévérité
            warming_factor = severity * 0.15
            self.temperature += warming_factor
        
        # Normalisation des valeurs
        self.temperature = np.clip(self.temperature, 0, 1)
        self.precipitation = np.clip(self.precipitation, 0, 1)
        self.wind_strength = np.clip(self.wind_strength, 0, 1)
    
    def get_summary(self):
        """Retourne un résumé de l'état actuel du climat."""
        avg_temp = np.mean(self.temperature)
        avg_precip = np.mean(self.precipitation)
        avg_wind = np.mean(self.wind_strength)
        
        return {
            "average_temperature": avg_temp,
            "average_precipitation": avg_precip,
            "average_wind_strength": avg_wind,
            "current_season": self.season_names[self.current_season],
            "global_warming": self.global_warming,
            "active_events": len(self.active_events)
        }