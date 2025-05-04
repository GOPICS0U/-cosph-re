#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Écosphère - Simulation procédurale interactive d'un monde alien
--------------------------------------------------------------
Une simulation d'un monde alien généré de façon procédurale,
avec évolution climatique, biologique et civilisationnelle.
Permet au joueur d'interagir avec le monde et d'influencer son évolution.
"""

import time
import random
import logging
import threading
import argparse
import sys
from datetime import datetime
from simulation.world import World
from simulation.logger import setup_logger
from simulation.visualization import Visualizer

# Configuration du logger
logger = setup_logger()

def run_simulation(world, visualizer, speed=1.0, max_years=None):
    """
    Lance la simulation en continu.
    
    Args:
        world: L'instance du monde à simuler.
        visualizer: L'instance du visualiseur.
        speed (float): Vitesse de simulation (années par seconde).
        max_years (int, optional): Nombre maximum d'années à simuler.
    """
    running = True
    paused = False
    year_count = 0
    
    logger.info(f"Démarrage de la simulation (vitesse: {speed} ans/sec)")
    
    try:
        while running:
            start_time = time.time()
            
            # Vérification de la pause
            if visualizer.pause_var.get():
                paused = True
            else:
                paused = False
            
            # Récupération de la vitesse actuelle
            current_speed = visualizer.speed_var.get()
            
            if not paused:
                # Simulation d'une année
                world.simulate_year()
                year_count += 1
                
                # Mise à jour de l'interface
                visualizer.update()
                
                # Affichage des informations
                if year_count % 10 == 0:  # Log tous les 10 ans
                    logger.info(f"Année {year_count} - Population: {world.ecosystem.total_population():,}")
                
                # Vérification du nombre maximum d'années
                if max_years and year_count >= max_years:
                    logger.info(f"Simulation terminée après {year_count} années")
                    running = False
                    break
            
            # Calcul du temps d'attente pour respecter la vitesse
            elapsed = time.time() - start_time
            wait_time = max(0, (1.0 / current_speed) - elapsed)
            
            # Attente
            time.sleep(wait_time)
            
    except Exception as e:
        logger.error(f"Erreur dans la boucle de simulation: {e}", exc_info=True)
    finally:
        logger.info(f"=== FIN DE LA SIMULATION ===")
        logger.info(f"Durée totale: {year_count} années simulées")

def main():
    """Point d'entrée principal de la simulation Écosphère."""
    
    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Écosphère - Simulation Procédurale Interactive")
    parser.add_argument("--seed", type=int, help="Graine pour la génération aléatoire")
    parser.add_argument("--speed", type=float, default=1.0, help="Vitesse de simulation (années par seconde)")
    parser.add_argument("--max-years", type=int, help="Nombre maximum d'années à simuler")
    args = parser.parse_args()
    
    # Utilisation d'une graine aléatoire si non spécifiée
    seed = args.seed if args.seed is not None else random.randint(1, 1000000)
    
    logger.info("=== DÉMARRAGE DE LA SIMULATION ÉCOSPHÈRE INTERACTIVE ===")
    logger.info(f"Initialisation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Graine de génération: {seed}")
    logger.info(f"Vitesse de simulation initiale: {args.speed} an(s)/seconde")
    
    try:
        # Création du monde
        ecosphere = World(seed=seed)
        visualizer = Visualizer(ecosphere)
        
        # Initialisation du monde
        logger.info("Génération de la planète Écosphère...")
        ecosphere.generate()
        
        # Affichage des informations sur le monde
        logger.info(f"Planète générée: {ecosphere.name}")
        logger.info(f"Taille: {ecosphere.size} km de diamètre")
        logger.info(f"Composition atmosphérique: {ecosphere.atmosphere}")
        
        # Démarrage du thread de simulation
        sim_thread = threading.Thread(
            target=run_simulation, 
            args=(ecosphere, visualizer, args.speed, args.max_years)
        )
        sim_thread.daemon = True
        sim_thread.start()
        
        # Démarrage de l'interface graphique (bloquant)
        visualizer.start()
        
        # Attente de la fin du thread de simulation
        sim_thread.join(timeout=1.0)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {e}", exc_info=True)
        return 1
    
    logger.info("Écosphère terminé avec succès")
    return 0

if __name__ == "__main__":
    sys.exit(main())