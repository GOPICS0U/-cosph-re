#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de journalisation pour la simulation Écosphère.
Enregistre l'historique de l'évolution du monde.
"""

import os
import logging
from datetime import datetime

def setup_logger():
    """Configure et retourne un logger pour la simulation."""
    
    # Création du dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Nom du fichier de log avec horodatage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/ecosphere_{timestamp}.log"
    
    # Configuration du logger
    logger = logging.getLogger('ecosphere')
    logger.setLevel(logging.INFO)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                      datefmt='%H:%M:%S')
    console_handler.setFormatter(console_format)
    
    # Handler pour le fichier
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                   datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_format)
    
    # Ajout des handlers au logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

class EventLogger:
    """Classe pour enregistrer des événements spécifiques dans la simulation."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_climate_event(self, region, event_type, severity, description):
        """Enregistre un événement climatique."""
        self.logger.info(f"CLIMAT [{region}] - {event_type} (Sévérité: {severity}) - {description}")
    
    def log_species_event(self, species_name, event_type, description):
        """Enregistre un événement lié à une espèce."""
        self.logger.info(f"ESPÈCE [{species_name}] - {event_type} - {description}")
    
    def log_evolution_event(self, species_name, mutation, advantage):
        """Enregistre un événement d'évolution."""
        self.logger.info(f"ÉVOLUTION [{species_name}] - Mutation: {mutation} - Avantage: {advantage}")
    
    def log_civilization_event(self, civ_name, event_type, description):
        """Enregistre un événement de civilisation."""
        self.logger.info(f"CIVILISATION [{civ_name}] - {event_type} - {description}")
    
    def log_extinction(self, species_name, cause):
        """Enregistre l'extinction d'une espèce."""
        self.logger.warning(f"EXTINCTION [{species_name}] - Cause: {cause}")
    
    def log_technological_advancement(self, civ_name, tech_name, description):
        """Enregistre une avancée technologique."""
        self.logger.info(f"TECHNOLOGIE [{civ_name}] - {tech_name} - {description}")