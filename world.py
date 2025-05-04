#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion du monde pour la simulation Écosphère.
Contient la classe principale World qui gère l'ensemble de la simulation.
"""

import random
import logging
import numpy as np
from simulation.geography import Geography
from simulation.climate import Climate
from simulation.ecosystem import Ecosystem
from simulation.civilization import CivilizationManager

class World:
    """
    Classe principale représentant le monde simulé Écosphère.
    Coordonne tous les aspects de la simulation: géographie, climat, écosystème et civilisations.
    """
    
    def __init__(self, seed=None, size=None):
        """
        Initialise un nouveau monde.
        
        Args:
            seed (int, optional): Graine pour la génération aléatoire.
            size (int, optional): Taille de la planète en km de diamètre.
        """
        # Initialisation de la graine aléatoire
        self.seed = seed if seed is not None else random.randint(1, 1000000)
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # Caractéristiques de base de la planète
        self.name = self._generate_planet_name()
        self.size = size if size is not None else random.randint(10000, 15000)  # km de diamètre
        self.age = 0  # Âge en années
        
        # Composition atmosphérique (en pourcentage)
        self.atmosphere = {
            'nitrogen': random.uniform(65, 80),
            'oxygen': random.uniform(10, 25),
            'carbon_dioxide': random.uniform(0.1, 5),
            'argon': random.uniform(0.5, 2),
            'water_vapor': random.uniform(0.1, 3),
            'other_gases': random.uniform(0.1, 1)
        }
        
        # Normalisation des pourcentages atmosphériques
        total = sum(self.atmosphere.values())
        for gas in self.atmosphere:
            self.atmosphere[gas] = (self.atmosphere[gas] / total) * 100
        
        # Sous-systèmes
        self.geography = Geography(self)
        self.climate = Climate(self)
        self.ecosystem = Ecosystem(self)
        self.civilization_manager = CivilizationManager(self)
        
        # Logger
        self.logger = logging.getLogger('ecosphere')
    
    def _generate_planet_name(self):
        """Génère un nom aléatoire pour la planète."""
        prefixes = ["Xeno", "Astra", "Novo", "Terra", "Gaia", "Eco", "Bio", "Vita", "Zoa", "Orga"]
        suffixes = ["sphere", "world", "gaia", "terra", "planet", "globe", "orb", "system", "realm"]
        
        # Possibilité d'ajouter un nombre
        if random.random() < 0.3:
            return f"{random.choice(prefixes)}{random.choice(suffixes)}-{random.randint(1, 999)}"
        else:
            return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def generate(self):
        """Génère l'ensemble du monde: géographie, climat initial et écosystème de base."""
        self.logger.info("Génération de la géographie...")
        self.geography.generate()
        
        self.logger.info("Initialisation du climat...")
        self.climate.initialize()
        
        self.logger.info("Création de l'écosystème initial...")
        self.ecosystem.seed_initial_life()
    
    def simulate_year(self):
        """Simule une année complète dans le monde."""
        self.age += 1
        
        # Mise à jour du climat
        self.climate.simulate_year()
        
        # Évolution de l'écosystème
        self.ecosystem.simulate_year()
        
        # Évolution des civilisations (si elles existent)
        self.civilization_manager.simulate_year()
        
        # Événements aléatoires
        self._process_random_events()
    
    def _process_random_events(self):
        """Traite les événements aléatoires qui peuvent survenir dans le monde."""
        # Événements catastrophiques rares
        if random.random() < 0.001:  # 0.1% de chance par an
            event_type = random.choice(["meteorite", "supervolcano", "solar_flare", "pandemic"])
            severity = random.uniform(0.1, 1.0)
            
            self.logger.warning(f"ÉVÉNEMENT CATASTROPHIQUE: {event_type} (Sévérité: {severity:.2f})")
            
            # Impact sur le climat
            self.climate.apply_catastrophe(event_type, severity)
            
            # Impact sur l'écosystème
            self.ecosystem.apply_catastrophe(event_type, severity)
            
            # Impact sur les civilisations
            self.civilization_manager.apply_catastrophe(event_type, severity)
    
    def total_population(self):
        """Retourne la population totale de toutes les espèces."""
        return self.ecosystem.total_population()
    
    def get_summary(self):
        """Retourne un résumé de l'état actuel du monde."""
        summary = {
            "age": self.age,
            "climate": self.climate.get_summary(),
            "ecosystem": self.ecosystem.get_summary(),
            "civilizations": self.civilization_manager.get_summary()
        }
        return summary