#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de visualisation pour la simulation Écosphère.
Gère l'affichage graphique de la planète et de ses différents aspects.
Permet au joueur d'interagir avec le monde simulé.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, Menu
import threading
import queue
import time
import logging
import random
from PIL import Image, ImageTk
from simulation.geography import BiomeType

class Visualizer:
    """
    Classe gérant la visualisation de la simulation Écosphère.
    Affiche la géographie, le climat, l'écosystème et les civilisations.
    Permet au joueur d'interagir avec le monde simulé.
    """
    
    def __init__(self, world):
        """
        Initialise le visualiseur.
        
        Args:
            world: L'instance du monde à visualiser.
        """
        self.world = world
        self.logger = logging.getLogger('ecosphere')
        
        # Paramètres d'affichage
        self.display_mode = "geography"  # Mode d'affichage actuel
        self.show_grid = False
        self.show_civilizations = True
        
        # Interface graphique
        self.root = None
        self.canvas = None
        self.fig = None
        self.ax = None
        
        # File d'attente pour la communication entre threads
        self.queue = queue.Queue()
        
        # Couleurs pour les biomes
        self.biome_colors = {
            BiomeType.OCEAN.value: '#0077be',
            BiomeType.SHALLOW_WATER.value: '#5d9bc9',
            BiomeType.BEACH.value: '#f5deb3',
            BiomeType.PLAINS.value: '#7cfc00',
            BiomeType.FOREST.value: '#228b22',
            BiomeType.JUNGLE.value: '#006400',
            BiomeType.DESERT.value: '#f4a460',
            BiomeType.SAVANNA.value: '#d2b48c',
            BiomeType.TUNDRA.value: '#d3d3d3',
            BiomeType.MOUNTAINS.value: '#808080',
            BiomeType.ICE.value: '#f0f8ff',
            BiomeType.VOLCANIC.value: '#8b0000',
            BiomeType.SWAMP.value: '#2f4f4f'
        }
        
        # Paramètres d'interaction joueur
        self.player_mode = "observer"  # observer, deity, civilization
        self.selected_cell = None
        self.selected_civilization = None
        self.player_power = 100  # Points de pouvoir du joueur
        self.power_regen_rate = 1  # Régénération par an
        self.last_action_time = 0  # Temps de la dernière action
        self.action_cooldown = 5  # Temps de recharge entre actions (en années)
        
        # Historique des actions du joueur
        self.player_actions = []
        
        # Création de l'interface
        self._create_gui()
        
        # Démarrage du thread de mise à jour
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def _create_gui(self):
        """Crée l'interface graphique."""
        # Fenêtre principale
        self.root = tk.Tk()
        self.root.title("Écosphère - Simulation Procédurale Interactive")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Création du menu
        self._create_menu()
        
        # Cadre principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panneau de gauche (visualisation)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Figure matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Canvas pour la figure
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Ajout des interactions avec la carte
        self.canvas.mpl_connect('button_press_event', self._on_map_click)
        
        # Contrôles de visualisation
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Sélection du mode d'affichage
        ttk.Label(control_frame, text="Affichage:").pack(side=tk.LEFT, padx=5)
        
        display_modes = ["geography", "temperature", "precipitation", "population", "civilizations"]
        self.display_var = tk.StringVar(value=self.display_mode)
        
        display_combo = ttk.Combobox(control_frame, textvariable=self.display_var, 
                                    values=display_modes, state="readonly", width=15)
        display_combo.pack(side=tk.LEFT, padx=5)
        display_combo.bind("<<ComboboxSelected>>", self._on_display_change)
        
        # Case à cocher pour la grille
        self.grid_var = tk.BooleanVar(value=self.show_grid)
        grid_check = ttk.Checkbutton(control_frame, text="Grille", variable=self.grid_var, 
                                    command=self._on_grid_toggle)
        grid_check.pack(side=tk.LEFT, padx=10)
        
        # Case à cocher pour les civilisations
        self.civ_var = tk.BooleanVar(value=self.show_civilizations)
        civ_check = ttk.Checkbutton(control_frame, text="Civilisations", variable=self.civ_var, 
                                   command=self._on_civ_toggle)
        civ_check.pack(side=tk.LEFT, padx=10)
        
        # Panneau de droite (informations et contrôles)
        right_frame = ttk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Mode joueur
        player_frame = ttk.LabelFrame(right_frame, text="Mode Joueur")
        player_frame.pack(fill=tk.X, pady=5)
        
        # Sélection du mode joueur
        mode_frame = ttk.Frame(player_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        
        player_modes = ["Observer", "Deity", "Civilization"]
        self.player_mode_var = tk.StringVar(value="Observer")
        
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.player_mode_var, 
                                 values=player_modes, state="readonly", width=15)
        mode_combo.pack(side=tk.LEFT, padx=5)
        mode_combo.bind("<<ComboboxSelected>>", self._on_player_mode_change)
        
        # Points de pouvoir
        power_frame = ttk.Frame(player_frame)
        power_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(power_frame, text="Pouvoir:").pack(side=tk.LEFT, padx=5)
        self.power_label = ttk.Label(power_frame, text=f"{self.player_power} points")
        self.power_label.pack(side=tk.LEFT, padx=5)
        
        # Temps de recharge
        cooldown_frame = ttk.Frame(player_frame)
        cooldown_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cooldown_frame, text="Recharge:").pack(side=tk.LEFT, padx=5)
        self.cooldown_label = ttk.Label(cooldown_frame, text="Prêt")
        self.cooldown_label.pack(side=tk.LEFT, padx=5)
        
        # Actions du joueur
        self.action_frame = ttk.LabelFrame(right_frame, text="Actions")
        self.action_frame.pack(fill=tk.X, pady=5)
        
        # Les boutons d'action seront ajoutés dynamiquement selon le mode
        self._update_action_buttons()
        
        # Informations sur le monde
        info_frame = ttk.LabelFrame(right_frame, text="Informations")
        info_frame.pack(fill=tk.X, pady=5)
        
        # Année
        year_frame = ttk.Frame(info_frame)
        year_frame.pack(fill=tk.X, pady=2)
        ttk.Label(year_frame, text="Année:").pack(side=tk.LEFT, padx=5)
        self.year_label = ttk.Label(year_frame, text="0")
        self.year_label.pack(side=tk.LEFT, padx=5)
        
        # Population
        pop_frame = ttk.Frame(info_frame)
        pop_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pop_frame, text="Population:").pack(side=tk.LEFT, padx=5)
        self.pop_label = ttk.Label(pop_frame, text="0")
        self.pop_label.pack(side=tk.LEFT, padx=5)
        
        # Espèces
        species_frame = ttk.Frame(info_frame)
        species_frame.pack(fill=tk.X, pady=2)
        ttk.Label(species_frame, text="Espèces:").pack(side=tk.LEFT, padx=5)
        self.species_label = ttk.Label(species_frame, text="0")
        self.species_label.pack(side=tk.LEFT, padx=5)
        
        # Civilisations
        civ_frame = ttk.Frame(info_frame)
        civ_frame.pack(fill=tk.X, pady=2)
        ttk.Label(civ_frame, text="Civilisations:").pack(side=tk.LEFT, padx=5)
        self.civ_label = ttk.Label(civ_frame, text="0")
        self.civ_label.pack(side=tk.LEFT, padx=5)
        
        # Informations sur la sélection
        self.selection_frame = ttk.LabelFrame(right_frame, text="Sélection")
        self.selection_frame.pack(fill=tk.X, pady=5)
        
        # Contenu initial vide
        self.selection_info = scrolledtext.ScrolledText(self.selection_frame, wrap=tk.WORD, 
                                                      width=40, height=8)
        self.selection_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.selection_info.config(state=tk.DISABLED)
        
        # Journal des événements
        log_frame = ttk.LabelFrame(right_frame, text="Journal")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=40, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Contrôles de simulation
        sim_frame = ttk.LabelFrame(right_frame, text="Contrôles")
        sim_frame.pack(fill=tk.X, pady=5)
        
        # Vitesse de simulation
        speed_frame = ttk.Frame(sim_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="Vitesse:").pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=10.0, variable=self.speed_var, 
                               orient=tk.HORIZONTAL, length=150)
        speed_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        speed_scale.bind("<Motion>", self._on_speed_change)
        
        # Boutons
        button_frame = ttk.Frame(sim_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.pause_var = tk.BooleanVar(value=False)
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self._on_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Capture", command=self._on_capture).pack(side=tk.LEFT, padx=5)
        
        # Initialisation de l'affichage
        self._draw_world()
    
    def _create_menu(self):
        """Crée la barre de menu."""
        menubar = Menu(self.root)
        
        # Menu Fichier
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nouvelle simulation", command=self._on_new_simulation)
        file_menu.add_command(label="Sauvegarder", command=self._on_save)
        file_menu.add_command(label="Charger", command=self._on_load)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self._on_closing)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Simulation
        sim_menu = Menu(menubar, tearoff=0)
        sim_menu.add_command(label="Paramètres", command=self._on_settings)
        sim_menu.add_command(label="Statistiques", command=self._on_stats)
        sim_menu.add_separator()
        sim_menu.add_command(label="Événement aléatoire", command=self._on_random_event)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        
        # Menu Joueur
        player_menu = Menu(menubar, tearoff=0)
        player_menu.add_command(label="Changer de mode", command=self._on_change_player_mode)
        player_menu.add_command(label="Historique des actions", command=self._on_action_history)
        menubar.add_cascade(label="Joueur", menu=player_menu)
        
        # Menu Aide
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="Tutoriel", command=self._on_tutorial)
        help_menu.add_command(label="À propos", command=self._on_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _update_action_buttons(self):
        """Met à jour les boutons d'action selon le mode joueur."""
        # Suppression des boutons existants
        for widget in self.action_frame.winfo_children():
            widget.destroy()
        
        # Ajout des boutons selon le mode
        if self.player_mode == "observer":
            ttk.Label(self.action_frame, text="Mode observateur actif - Aucune action disponible").pack(pady=10)
            
        elif self.player_mode == "deity":
            # Actions divines
            ttk.Button(self.action_frame, text="Catastrophe naturelle", 
                      command=lambda: self._deity_action("catastrophe")).pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(self.action_frame, text="Modifier le climat", 
                      command=lambda: self._deity_action("climate")).pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(self.action_frame, text="Modifier le terrain", 
                      command=lambda: self._deity_action("terrain")).pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(self.action_frame, text="Créer une espèce", 
                      command=lambda: self._deity_action("create_species")).pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(self.action_frame, text="Bénédiction", 
                      command=lambda: self._deity_action("blessing")).pack(fill=tk.X, padx=5, pady=2)
            ttk.Button(self.action_frame, text="Malédiction", 
                      command=lambda: self._deity_action("curse")).pack(fill=tk.X, padx=5, pady=2)
            
        elif self.player_mode == "civilization":
            if self.selected_civilization:
                # Actions de civilisation
                ttk.Button(self.action_frame, text="Développer technologie", 
                          command=lambda: self._civ_action("develop_tech")).pack(fill=tk.X, padx=5, pady=2)
                ttk.Button(self.action_frame, text="Expansion territoriale", 
                          command=lambda: self._civ_action("expand")).pack(fill=tk.X, padx=5, pady=2)
                ttk.Button(self.action_frame, text="Diplomatie", 
                          command=lambda: self._civ_action("diplomacy")).pack(fill=tk.X, padx=5, pady=2)
                ttk.Button(self.action_frame, text="Projet spécial", 
                          command=lambda: self._civ_action("special_project")).pack(fill=tk.X, padx=5, pady=2)
            else:
                ttk.Label(self.action_frame, 
                         text="Sélectionnez une civilisation pour voir les actions disponibles").pack(pady=10)
    
    def _update_loop(self):
        """Boucle de mise à jour pour le thread secondaire."""
        while self.running:
            try:
                # Vérification des messages dans la file d'attente
                try:
                    message = self.queue.get(block=False)
                    if message == "update":
                        # Mise à jour de l'interface
                        self.root.after(0, self._update_gui)
                except queue.Empty:
                    pass
                
                # Pause pour économiser les ressources
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Erreur dans le thread de mise à jour: {e}")
    
    def _update_gui(self):
        """Met à jour l'interface graphique avec les données actuelles."""
        try:
            # Mise à jour des informations
            self.year_label.config(text=str(self.world.age))
            self.pop_label.config(text=f"{self.world.ecosystem.total_population():,}")
            self.species_label.config(text=str(len(self.world.ecosystem.species)))
            
            if hasattr(self.world, 'civilization_manager'):
                self.civ_label.config(text=str(len(self.world.civilization_manager.civilizations)))
            
            # Mise à jour de l'affichage
            self._draw_world()
            
            # Mise à jour du journal
            self._update_log()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour de l'interface: {e}")
    
    def _draw_world(self):
        """Dessine le monde selon le mode d'affichage actuel."""
        try:
            # Effacement de l'affichage précédent
            self.ax.clear()
            
            # Récupération des données
            grid_size = self.world.geography.grid_size
            
            if self.display_mode == "geography":
                # Affichage de la géographie (biomes)
                data = self.world.geography.biomes
                
                # Création d'une carte de couleurs personnalisée pour les biomes
                cmap = mcolors.ListedColormap([self.biome_colors[i] for i in range(len(BiomeType))])
                
                # Affichage
                im = self.ax.imshow(data, cmap=cmap, interpolation='nearest')
                
                # Légende
                if not hasattr(self, 'legend_shown') or not self.legend_shown:
                    handles = [plt.Rectangle((0, 0), 1, 1, color=self.biome_colors[biome.value]) 
                              for biome in BiomeType]
                    labels = [biome.name for biome in BiomeType]
                    self.ax.legend(handles, labels, loc='upper right', 
                                  bbox_to_anchor=(1.1, 1), fontsize='small')
                    self.legend_shown = True
                
            elif self.display_mode == "temperature":
                # Affichage de la température
                data = self.world.climate.temperature
                im = self.ax.imshow(data, cmap='coolwarm', interpolation='bilinear')
                plt.colorbar(im, ax=self.ax, label='Température')
                
            elif self.display_mode == "precipitation":
                # Affichage des précipitations
                data = self.world.climate.precipitation
                im = self.ax.imshow(data, cmap='Blues', interpolation='bilinear')
                plt.colorbar(im, ax=self.ax, label='Précipitations')
                
            elif self.display_mode == "population":
                # Affichage de la population totale
                data = np.zeros((grid_size, grid_size))
                
                for species in self.world.ecosystem.species:
                    data += species.population_map
                
                # Normalisation logarithmique pour mieux visualiser
                data = np.log1p(data)
                
                im = self.ax.imshow(data, cmap='viridis', interpolation='bilinear')
                plt.colorbar(im, ax=self.ax, label='Population (log)')
                
            elif self.display_mode == "civilizations":
                # Affichage des territoires des civilisations
                data = np.zeros((grid_size, grid_size, 4))  # RGBA
                
                # Fond de carte (biomes)
                biome_data = self.world.geography.biomes
                for y in range(grid_size):
                    for x in range(grid_size):
                        biome = biome_data[y, x]
                        color = mcolors.to_rgba(self.biome_colors[biome])
                        data[y, x] = color
                
                # Superposition des territoires des civilisations
                if hasattr(self.world, 'civilization_manager'):
                    for i, civ in enumerate(self.world.civilization_manager.civilizations):
                        # Couleur unique pour chaque civilisation
                        hue = (i * 0.618033988749895) % 1.0  # Nombre d'or pour une bonne distribution
                        color = plt.cm.hsv(hue)
                        
                        for y in range(grid_size):
                            for x in range(grid_size):
                                if civ.territory[y, x]:
                                    # Mélange avec le fond
                                    data[y, x] = color * 0.7 + data[y, x] * 0.3
                
                im = self.ax.imshow(data, interpolation='nearest')
            
            # Affichage de la grille si activée
            if self.show_grid:
                self.ax.grid(which='both', color='black', linestyle='-', linewidth=0.5, alpha=0.2)
                self.ax.set_xticks(np.arange(-0.5, grid_size, 1), minor=True)
                self.ax.set_yticks(np.arange(-0.5, grid_size, 1), minor=True)
                self.ax.set_xticks(np.arange(0, grid_size, grid_size//10))
                self.ax.set_yticks(np.arange(0, grid_size, grid_size//10))
            else:
                self.ax.grid(False)
            
            # Superposition des civilisations si activée
            if self.show_civilizations and self.display_mode != "civilizations" and hasattr(self.world, 'civilization_manager'):
                for i, civ in enumerate(self.world.civilization_manager.civilizations):
                    # Trouver le centre du territoire
                    if np.any(civ.territory):
                        y_indices, x_indices = np.where(civ.territory)
                        center_y, center_x = int(np.mean(y_indices)), int(np.mean(x_indices))
                        
                        # Couleur unique pour chaque civilisation
                        hue = (i * 0.618033988749895) % 1.0
                        color = plt.cm.hsv(hue)
                        
                        # Marqueur pour le centre
                        self.ax.plot(center_x, center_y, 'o', markersize=8, 
                                    markerfacecolor=color, markeredgecolor='black')
                        
                        # Nom de la civilisation
                        self.ax.text(center_x, center_y + 2, civ.name, color='black', 
                                    fontsize=8, ha='center', va='center', 
                                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Titre
            self.ax.set_title(f"Écosphère - Année {self.world.age}")
            
            # Mise à jour du canvas
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Erreur lors du dessin du monde: {e}")
    
    def _update_log(self):
        """Met à jour le journal des événements."""
        # Récupération des derniers événements
        recent_events = []
        
        # Événements des civilisations
        if hasattr(self.world, 'civilization_manager'):
            for civ in self.world.civilization_manager.civilizations:
                if civ.history:
                    recent_events.extend(civ.history[-5:])  # 5 derniers événements
        
        # Tri des événements par année
        recent_events.sort(key=lambda e: e["year"])
        
        # Affichage des événements
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for event in recent_events[-20:]:  # 20 événements les plus récents
            year = event["year"]
            event_type = event["type"]
            description = event["description"]
            
            self.log_text.insert(tk.END, f"Année {year}: {event_type}\n")
            self.log_text.insert(tk.END, f"{description}\n\n")
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)  # Défilement automatique
    
    def _on_display_change(self, event):
        """Gère le changement de mode d'affichage."""
        self.display_mode = self.display_var.get()
        self.legend_shown = False  # Réinitialisation de la légende
        self._draw_world()
    
    def _on_grid_toggle(self):
        """Gère l'activation/désactivation de la grille."""
        self.show_grid = self.grid_var.get()
        self._draw_world()
    
    def _on_civ_toggle(self):
        """Gère l'activation/désactivation de l'affichage des civilisations."""
        self.show_civilizations = self.civ_var.get()
        self._draw_world()
    
    def _on_speed_change(self, event):
        """Gère le changement de vitesse de simulation."""
        speed = self.speed_var.get()
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def _on_pause(self):
        """Gère la pause/reprise de la simulation."""
        self.pause_var.set(not self.pause_var.get())
        
        if self.pause_var.get():
            self.pause_button.config(text="Reprendre")
        else:
            self.pause_button.config(text="Pause")
    
    def _on_capture(self):
        """Capture l'état actuel de la simulation."""
        try:
            # Création d'un nom de fichier avec horodatage
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_ecosphere_{timestamp}.png"
            
            # Sauvegarde de l'image
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            
            self.logger.info(f"Capture d'écran enregistrée: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture d'écran: {e}")
    
    def _on_closing(self):
        """Gère la fermeture de l'application."""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        self.root.destroy()
    
    def _on_map_click(self, event):
        """Gère les clics sur la carte."""
        if event.xdata is None or event.ydata is None:
            return
        
        # Conversion des coordonnées en indices de grille
        x, y = int(event.xdata), int(event.ydata)
        grid_size = self.world.geography.grid_size
        
        if 0 <= x < grid_size and 0 <= y < grid_size:
            self.selected_cell = (x, y)
            self._update_selection_info()
            
            # Vérification si une civilisation est sélectionnée
            if self.display_mode == "civilizations" and hasattr(self.world, 'civilization_manager'):
                for civ in self.world.civilization_manager.civilizations:
                    if civ.territory[y, x]:
                        self.selected_civilization = civ
                        self._update_selection_info()
                        
                        # Mise à jour des boutons d'action si en mode civilisation
                        if self.player_mode == "civilization":
                            self._update_action_buttons()
                        
                        break
            
            # Redessiner pour montrer la sélection
            self._draw_world()
    
    def _update_selection_info(self):
        """Met à jour les informations sur la sélection."""
        if not self.selected_cell:
            return
        
        x, y = self.selected_cell
        
        # Activation de l'édition
        self.selection_info.config(state=tk.NORMAL)
        self.selection_info.delete(1.0, tk.END)
        
        # Informations sur la cellule
        biome_id = self.world.geography.biomes[y, x]
        biome_name = self.world.geography.get_biome_name(biome_id)
        elevation = self.world.geography.elevation[y, x]
        temperature = self.world.climate.temperature[y, x]
        precipitation = self.world.climate.precipitation[y, x]
        
        self.selection_info.insert(tk.END, f"Coordonnées: ({x}, {y})\n")
        self.selection_info.insert(tk.END, f"Biome: {biome_name}\n")
        self.selection_info.insert(tk.END, f"Élévation: {elevation:.2f}\n")
        self.selection_info.insert(tk.END, f"Température: {temperature:.2f}\n")
        self.selection_info.insert(tk.END, f"Précipitations: {precipitation:.2f}\n")
        
        # Informations sur les espèces présentes
        species_present = []
        for species in self.world.ecosystem.species:
            pop = species.get_local_population(x, y)
            if pop > 10:  # Seuil minimal pour être significatif
                species_present.append((species, int(pop)))
        
        if species_present:
            self.selection_info.insert(tk.END, "\nEspèces présentes:\n")
            for species, pop in sorted(species_present, key=lambda s: s[1], reverse=True)[:3]:
                self.selection_info.insert(tk.END, f"- {species.name}: {pop} individus\n")
        
        # Informations sur la civilisation sélectionnée
        if self.selected_civilization:
            civ = self.selected_civilization
            self.selection_info.insert(tk.END, f"\nCivilisation: {civ.name}\n")
            self.selection_info.insert(tk.END, f"Population: {civ.population:,}\n")
            self.selection_info.insert(tk.END, f"Niveau tech: {civ.tech_level.name}\n")
            self.selection_info.insert(tk.END, f"Gouvernement: {civ.government.name}\n")
        
        # Désactivation de l'édition
        self.selection_info.config(state=tk.DISABLED)
    
    def _on_player_mode_change(self, event):
        """Gère le changement de mode joueur."""
        new_mode = self.player_mode_var.get().lower()
        
        if new_mode != self.player_mode:
            self.player_mode = new_mode
            
            # Réinitialisation de la sélection si passage en mode observateur
            if self.player_mode == "observer":
                self.selected_civilization = None
            
            # Mise à jour des boutons d'action
            self._update_action_buttons()
            
            # Message de confirmation
            self.logger.info(f"Mode joueur changé: {self.player_mode}")
            messagebox.showinfo("Mode Joueur", f"Vous êtes maintenant en mode {self.player_mode}.")
    
    def _on_new_simulation(self):
        """Gère la création d'une nouvelle simulation."""
        if messagebox.askyesno("Nouvelle Simulation", 
                             "Êtes-vous sûr de vouloir démarrer une nouvelle simulation ? "
                             "Toutes les données actuelles seront perdues."):
            # Implémentation à compléter
            messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _on_save(self):
        """Gère la sauvegarde de la simulation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _on_load(self):
        """Gère le chargement d'une simulation sauvegardée."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _on_settings(self):
        """Ouvre la fenêtre des paramètres de simulation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _on_stats(self):
        """Affiche les statistiques détaillées de la simulation."""
        # Création d'une fenêtre pour les statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistiques de la Simulation")
        stats_window.geometry("600x500")
        
        # Notebook pour organiser les statistiques par onglets
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet Monde
        world_frame = ttk.Frame(notebook)
        notebook.add(world_frame, text="Monde")
        
        world_stats = ttk.LabelFrame(world_frame, text="Informations générales")
        world_stats.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(world_stats, text=f"Âge du monde: {self.world.age} ans").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(world_stats, text=f"Taille de la grille: {self.world.geography.grid_size}x{self.world.geography.grid_size}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Statistiques des biomes
        biome_stats = self.world.geography.get_biome_stats()
        
        biome_frame = ttk.LabelFrame(world_frame, text="Distribution des biomes")
        biome_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for biome, percentage in sorted(biome_stats.items(), key=lambda x: x[1], reverse=True):
            ttk.Label(biome_frame, text=f"{biome}: {percentage:.1f}%").pack(anchor=tk.W, padx=10, pady=1)
        
        # Onglet Écosystème
        eco_frame = ttk.Frame(notebook)
        notebook.add(eco_frame, text="Écosystème")
        
        eco_summary = self.world.ecosystem.get_summary()
        
        eco_stats = ttk.LabelFrame(eco_frame, text="Statistiques de l'écosystème")
        eco_stats.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(eco_stats, text=f"Espèces vivantes: {eco_summary['total_species']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(eco_stats, text=f"Espèces éteintes: {eco_summary['extinct_species']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(eco_stats, text=f"Population totale: {eco_summary['total_population']:,}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Distribution trophique
        trophic_frame = ttk.LabelFrame(eco_frame, text="Distribution trophique")
        trophic_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for level, count in eco_summary['trophic_distribution'].items():
            ttk.Label(trophic_frame, text=f"{level}: {count} espèces").pack(anchor=tk.W, padx=10, pady=1)
        
        # Espèces dominantes
        dominant_frame = ttk.LabelFrame(eco_frame, text="Espèces dominantes")
        dominant_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for name, pop in eco_summary['dominant_species']:
            ttk.Label(dominant_frame, text=f"{name}: {pop:,} individus").pack(anchor=tk.W, padx=10, pady=1)
        
        # Onglet Civilisations
        if hasattr(self.world, 'civilization_manager'):
            civ_frame = ttk.Frame(notebook)
            notebook.add(civ_frame, text="Civilisations")
            
            civ_summary = self.world.civilization_manager.get_summary()
            
            civ_stats = ttk.LabelFrame(civ_frame, text="Statistiques des civilisations")
            civ_stats.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(civ_stats, text=f"Civilisations actives: {civ_summary['active_civilizations']}").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(civ_stats, text=f"Civilisations disparues: {civ_summary['extinct_civilizations']}").pack(anchor=tk.W, padx=10, pady=2)
            
            # Détails des civilisations
            if civ_summary['details']:
                details_frame = ttk.LabelFrame(civ_frame, text="Détails des civilisations")
                details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                for civ in civ_summary['details']:
                    civ_detail = ttk.LabelFrame(details_frame, text=civ['name'])
                    civ_detail.pack(fill=tk.X, padx=5, pady=5)
                    
                    ttk.Label(civ_detail, text=f"Âge: {civ['age']} ans").pack(anchor=tk.W, padx=10, pady=1)
                    ttk.Label(civ_detail, text=f"Population: {civ['population']:,}").pack(anchor=tk.W, padx=10, pady=1)
                    ttk.Label(civ_detail, text=f"Niveau tech: {civ['tech_level']}").pack(anchor=tk.W, padx=10, pady=1)
                    ttk.Label(civ_detail, text=f"Gouvernement: {civ['government']}").pack(anchor=tk.W, padx=10, pady=1)
        
        # Onglet Climat
        climate_frame = ttk.Frame(notebook)
        notebook.add(climate_frame, text="Climat")
        
        climate_summary = self.world.climate.get_summary()
        
        climate_stats = ttk.LabelFrame(climate_frame, text="Statistiques climatiques")
        climate_stats.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(climate_stats, text=f"Saison actuelle: {climate_summary['current_season']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(climate_stats, text=f"Température moyenne: {climate_summary['average_temperature']:.2f}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(climate_stats, text=f"Précipitations moyennes: {climate_summary['average_precipitation']:.2f}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(climate_stats, text=f"Force du vent moyenne: {climate_summary['average_wind_strength']:.2f}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(climate_stats, text=f"Réchauffement global: {climate_summary['global_warming']:.2f}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(climate_stats, text=f"Événements actifs: {climate_summary['active_events']}").pack(anchor=tk.W, padx=10, pady=2)
    
    def _on_random_event(self):
        """Déclenche un événement aléatoire dans la simulation."""
        if self.player_mode != "deity":
            messagebox.showinfo("Mode requis", "Vous devez être en mode Deity pour déclencher des événements.")
            return
        
        # Types d'événements possibles
        event_types = [
            "Météorite",
            "Supervolcan",
            "Éruption solaire",
            "Pandémie",
            "Changement climatique rapide"
        ]
        
        # Demande du type d'événement
        event_window = tk.Toplevel(self.root)
        event_window.title("Déclencher un événement")
        event_window.geometry("400x300")
        event_window.transient(self.root)
        event_window.grab_set()
        
        ttk.Label(event_window, text="Choisissez un type d'événement:").pack(pady=10)
        
        event_var = tk.StringVar()
        for event in event_types:
            ttk.Radiobutton(event_window, text=event, variable=event_var, value=event).pack(anchor=tk.W, padx=20, pady=5)
        
        # Sévérité de l'événement
        ttk.Label(event_window, text="Sévérité:").pack(pady=10)
        
        severity_var = tk.DoubleVar(value=0.5)
        severity_scale = ttk.Scale(event_window, from_=0.1, to=1.0, variable=severity_var, 
                                  orient=tk.HORIZONTAL, length=300)
        severity_scale.pack(padx=20, pady=5)
        
        severity_label = ttk.Label(event_window, text="0.5")
        severity_label.pack()
        
        def update_severity_label(event):
            severity_label.config(text=f"{severity_var.get():.1f}")
        
        severity_scale.bind("<Motion>", update_severity_label)
        
        # Boutons
        button_frame = ttk.Frame(event_window)
        button_frame.pack(pady=20)
        
        def on_cancel():
            event_window.destroy()
        
        def on_trigger():
            event_type = event_var.get()
            severity = severity_var.get()
            
            if not event_type:
                messagebox.showwarning("Sélection requise", "Veuillez sélectionner un type d'événement.")
                return
            
            # Coût en points de pouvoir
            cost = int(severity * 50)
            
            if self.player_power < cost:
                messagebox.showwarning("Pouvoir insuffisant", 
                                     f"Vous n'avez pas assez de points de pouvoir. Coût: {cost}, Disponible: {self.player_power}")
                return
            
            # Confirmation
            if messagebox.askyesno("Confirmation", 
                                 f"Déclencher un événement {event_type} de sévérité {severity:.1f} ? Coût: {cost} points de pouvoir"):
                # Déduction des points
                self.player_power -= cost
                self.power_label.config(text=f"{self.player_power} points")
                
                # Application de l'événement
                self._apply_event(event_type.lower(), severity)
                
                # Enregistrement de l'action
                self.player_actions.append({
                    "year": self.world.age,
                    "action": "event",
                    "details": f"{event_type} (sévérité: {severity:.1f})",
                    "cost": cost
                })
                
                # Fermeture de la fenêtre
                event_window.destroy()
        
        ttk.Button(button_frame, text="Annuler", command=on_cancel).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Déclencher", command=on_trigger).pack(side=tk.LEFT, padx=10)
    
    def _apply_event(self, event_type, severity):
        """Applique un événement au monde."""
        # Conversion du type d'événement
        event_mapping = {
            "météorite": "meteorite",
            "supervolcan": "supervolcano",
            "éruption solaire": "solar_flare",
            "pandémie": "pandemic",
            "changement climatique rapide": "climate_shift"
        }
        
        internal_type = event_mapping.get(event_type, event_type)
        
        # Application aux différents systèmes
        if hasattr(self.world, 'climate'):
            self.world.climate.apply_catastrophe(internal_type, severity)
        
        if hasattr(self.world, 'ecosystem'):
            self.world.ecosystem.apply_catastrophe(internal_type, severity)
        
        if hasattr(self.world, 'civilization_manager'):
            self.world.civilization_manager.apply_catastrophe(internal_type, severity)
        
        # Message de confirmation
        self.logger.warning(f"ÉVÉNEMENT MAJEUR: {event_type.capitalize()} de sévérité {severity:.1f} déclenché par le joueur")
        messagebox.showinfo("Événement déclenché", 
                          f"Un {event_type} de sévérité {severity:.1f} a été déclenché. "
                          f"Les effets se feront sentir dans les prochaines années.")
    
    def _on_change_player_mode(self):
        """Ouvre une fenêtre pour changer de mode joueur."""
        mode_window = tk.Toplevel(self.root)
        mode_window.title("Changer de Mode Joueur")
        mode_window.geometry("400x300")
        mode_window.transient(self.root)
        mode_window.grab_set()
        
        ttk.Label(mode_window, text="Choisissez votre mode de jeu:").pack(pady=10)
        
        # Description des modes
        descriptions = {
            "Observer": "Observez la simulation sans intervenir.",
            "Deity": "Intervenez comme une divinité avec des pouvoirs sur le monde entier.",
            "Civilization": "Prenez le contrôle d'une civilisation spécifique."
        }
        
        mode_var = tk.StringVar(value=self.player_mode.capitalize())
        
        for mode, desc in descriptions.items():
            frame = ttk.Frame(mode_window)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Radiobutton(frame, text=mode, variable=mode_var, value=mode).pack(side=tk.LEFT)
            ttk.Label(frame, text=desc, wraplength=300).pack(side=tk.LEFT, padx=10)
        
        # Boutons
        button_frame = ttk.Frame(mode_window)
        button_frame.pack(pady=20)
        
        def on_cancel():
            mode_window.destroy()
        
        def on_select():
            new_mode = mode_var.get().lower()
            
            if new_mode != self.player_mode:
                self.player_mode = new_mode
                self.player_mode_var.set(mode_var.get())
                
                # Réinitialisation de la sélection si passage en mode observateur
                if self.player_mode == "observer":
                    self.selected_civilization = None
                
                # Mise à jour des boutons d'action
                self._update_action_buttons()
                
                # Message de confirmation
                self.logger.info(f"Mode joueur changé: {self.player_mode}")
                messagebox.showinfo("Mode Joueur", f"Vous êtes maintenant en mode {self.player_mode}.")
            
            mode_window.destroy()
        
        ttk.Button(button_frame, text="Annuler", command=on_cancel).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Sélectionner", command=on_select).pack(side=tk.LEFT, padx=10)
    
    def _on_action_history(self):
        """Affiche l'historique des actions du joueur."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Historique des Actions")
        history_window.geometry("500x400")
        
        # Création d'un widget texte pour afficher l'historique
        history_text = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Affichage des actions
        if not self.player_actions:
            history_text.insert(tk.END, "Aucune action effectuée.")
        else:
            for action in self.player_actions:
                history_text.insert(tk.END, f"Année {action['year']}: {action['action'].capitalize()}\n")
                history_text.insert(tk.END, f"Détails: {action['details']}\n")
                history_text.insert(tk.END, f"Coût: {action['cost']} points de pouvoir\n\n")
        
        history_text.config(state=tk.DISABLED)
    
    def _on_tutorial(self):
        """Affiche le tutoriel du jeu."""
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("Tutoriel - Écosphère")
        tutorial_window.geometry("600x500")
        
        # Création d'un widget notebook pour organiser le tutoriel
        notebook = ttk.Notebook(tutorial_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet Introduction
        intro_frame = ttk.Frame(notebook)
        notebook.add(intro_frame, text="Introduction")
        
        intro_text = scrolledtext.ScrolledText(intro_frame, wrap=tk.WORD)
        intro_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        intro_text.insert(tk.END, "Bienvenue dans Écosphère!\n\n")
        intro_text.insert(tk.END, "Écosphère est une simulation procédurale d'un monde alien où vous pouvez observer ou influencer l'évolution d'un écosystème complet et l'émergence de civilisations.\n\n")
        intro_text.insert(tk.END, "Ce tutoriel vous guidera à travers les différentes fonctionnalités et modes de jeu disponibles.\n\n")
        intro_text.insert(tk.END, "Utilisez les onglets ci-dessus pour naviguer entre les différentes sections du tutoriel.")
        intro_text.config(state=tk.DISABLED)
        
        # Onglet Interface
        interface_frame = ttk.Frame(notebook)
        notebook.add(interface_frame, text="Interface")
        
        interface_text = scrolledtext.ScrolledText(interface_frame, wrap=tk.WORD)
        interface_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        interface_text.insert(tk.END, "L'interface d'Écosphère\n\n")
        interface_text.insert(tk.END, "L'interface est divisée en plusieurs sections:\n\n")
        interface_text.insert(tk.END, "1. Carte du monde: Affiche la planète selon différents modes (géographie, température, etc.)\n\n")
        interface_text.insert(tk.END, "2. Panneau de contrôle: Permet de changer le mode d'affichage, d'activer/désactiver la grille, etc.\n\n")
        interface_text.insert(tk.END, "3. Informations: Affiche des données sur le monde, la population, etc.\n\n")
        interface_text.insert(tk.END, "4. Journal: Enregistre les événements importants qui se produisent dans le monde.\n\n")
        interface_text.insert(tk.END, "5. Actions du joueur: Affiche les actions disponibles selon votre mode de jeu.\n\n")
        interface_text.insert(tk.END, "6. Contrôles de simulation: Permet de régler la vitesse, mettre en pause, etc.")
        interface_text.config(state=tk.DISABLED)
        
        # Onglet Modes de jeu
        modes_frame = ttk.Frame(notebook)
        notebook.add(modes_frame, text="Modes de jeu")
        
        modes_text = scrolledtext.ScrolledText(modes_frame, wrap=tk.WORD)
        modes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        modes_text.insert(tk.END, "Modes de jeu\n\n")
        modes_text.insert(tk.END, "Écosphère propose trois modes de jeu différents:\n\n")
        modes_text.insert(tk.END, "1. Mode Observateur\n")
        modes_text.insert(tk.END, "   Dans ce mode, vous ne pouvez qu'observer la simulation sans intervenir.\n")
        modes_text.insert(tk.END, "   C'est idéal pour étudier l'évolution naturelle du monde.\n\n")
        modes_text.insert(tk.END, "2. Mode Deity (Divinité)\n")
        modes_text.insert(tk.END, "   Ce mode vous permet d'intervenir comme une divinité sur le monde.\n")
        modes_text.insert(tk.END, "   Vous pouvez déclencher des catastrophes, modifier le climat, créer des espèces, etc.\n")
        modes_text.insert(tk.END, "   Chaque action coûte des points de pouvoir qui se régénèrent lentement.\n\n")
        modes_text.insert(tk.END, "3. Mode Civilization\n")
        modes_text.insert(tk.END, "   Dans ce mode, vous prenez le contrôle d'une civilisation spécifique.\n")
        modes_text.insert(tk.END, "   Vous pouvez influencer son développement technologique, son expansion, etc.\n")
        modes_text.insert(tk.END, "   Pour jouer dans ce mode, vous devez d'abord sélectionner une civilisation sur la carte.")
        modes_text.config(state=tk.DISABLED)
        
        # Onglet Actions
        actions_frame = ttk.Frame(notebook)
        notebook.add(actions_frame, text="Actions")
        
        actions_text = scrolledtext.ScrolledText(actions_frame, wrap=tk.WORD)
        actions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        actions_text.insert(tk.END, "Actions disponibles\n\n")
        actions_text.insert(tk.END, "Les actions disponibles dépendent de votre mode de jeu:\n\n")
        actions_text.insert(tk.END, "Mode Deity:\n")
        actions_text.insert(tk.END, "- Catastrophe naturelle: Déclenche une catastrophe (météorite, volcan, etc.)\n")
        actions_text.insert(tk.END, "- Modifier le climat: Change les conditions climatiques d'une région\n")
        actions_text.insert(tk.END, "- Modifier le terrain: Transforme le terrain (montagnes, océans, etc.)\n")
        actions_text.insert(tk.END, "- Créer une espèce: Introduit une nouvelle espèce dans l'écosystème\n")
        actions_text.insert(tk.END, "- Bénédiction/Malédiction: Affecte positivement ou négativement une région\n\n")
        actions_text.insert(tk.END, "Mode Civilization:\n")
        actions_text.insert(tk.END, "- Développer technologie: Accélère le développement technologique\n")
        actions_text.insert(tk.END, "- Expansion territoriale: Étend le territoire de la civilisation\n")
        actions_text.insert(tk.END, "- Diplomatie: Influence les relations avec d'autres civilisations\n")
        actions_text.insert(tk.END, "- Projet spécial: Lance un projet unique (merveille, exploration, etc.)")
        actions_text.config(state=tk.DISABLED)
        
        # Onglet Astuces
        tips_frame = ttk.Frame(notebook)
        notebook.add(tips_frame, text="Astuces")
        
        tips_text = scrolledtext.ScrolledText(tips_frame, wrap=tk.WORD)
        tips_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tips_text.insert(tk.END, "Astuces et conseils\n\n")
        tips_text.insert(tk.END, "1. Cliquez sur la carte pour sélectionner une cellule et voir ses informations détaillées.\n\n")
        tips_text.insert(tk.END, "2. En mode Deity, utilisez vos points de pouvoir avec parcimonie. Ils se régénèrent lentement.\n\n")
        tips_text.insert(tk.END, "3. Les catastrophes peuvent avoir des effets à long terme sur le climat et l'écosystème.\n\n")
        tips_text.insert(tk.END, "4. Pour jouer en mode Civilization, vous devez attendre qu'une civilisation émerge naturellement ou en créer une en mode Deity.\n\n")
        tips_text.insert(tk.END, "5. Utilisez le menu Simulation > Statistiques pour voir des informations détaillées sur le monde.\n\n")
        tips_text.insert(tk.END, "6. Vous pouvez capturer des images de la simulation à tout moment avec le bouton Capture.\n\n")
        tips_text.insert(tk.END, "7. Expérimentez! Chaque simulation est unique et peut évoluer de façon inattendue.")
        tips_text.config(state=tk.DISABLED)
    
    def _on_about(self):
        """Affiche les informations sur le programme."""
        about_window = tk.Toplevel(self.root)
        about_window.title("À propos d'Écosphère")
        about_window.geometry("400x300")
        about_window.transient(self.root)
        
        # Logo (à remplacer par un vrai logo si disponible)
        logo_frame = ttk.Frame(about_window)
        logo_frame.pack(pady=10)
        
        # Texte d'information
        info_frame = ttk.Frame(about_window)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(info_frame, text="Écosphère", font=("Arial", 16, "bold")).pack(pady=5)
        ttk.Label(info_frame, text="Simulation Procédurale Interactive").pack()
        ttk.Label(info_frame, text="Version 1.0").pack(pady=5)
        ttk.Label(info_frame, text="© 2023 - Tous droits réservés").pack(pady=10)
        
        ttk.Label(info_frame, text="Une simulation complète d'un monde alien,\n"
                                 "de son écosystème et de ses civilisations.",
                 justify=tk.CENTER).pack(pady=5)
        
        # Bouton de fermeture
        ttk.Button(about_window, text="Fermer", command=about_window.destroy).pack(pady=10)
    
    def _deity_action(self, action_type):
        """Exécute une action en mode divinité."""
        # Vérification du mode
        if self.player_mode != "deity":
            messagebox.showinfo("Mode incorrect", "Cette action n'est disponible qu'en mode Deity.")
            return
        
        # Vérification du temps de recharge
        if self.world.age - self.last_action_time < self.action_cooldown:
            remaining = self.action_cooldown - (self.world.age - self.last_action_time)
            messagebox.showinfo("Action en recharge", 
                              f"Vous devez attendre encore {remaining} années avant de pouvoir agir à nouveau.")
            return
        
        # Vérification de la sélection d'une cellule
        if not self.selected_cell and action_type not in ["create_species"]:
            messagebox.showinfo("Sélection requise", 
                              "Vous devez d'abord sélectionner une cellule sur la carte.")
            return
        
        # Exécution de l'action selon son type
        if action_type == "catastrophe":
            self._deity_catastrophe()
        elif action_type == "climate":
            self._deity_modify_climate()
        elif action_type == "terrain":
            self._deity_modify_terrain()
        elif action_type == "create_species":
            self._deity_create_species()
        elif action_type == "blessing":
            self._deity_blessing()
        elif action_type == "curse":
            self._deity_curse()
    
    def _deity_catastrophe(self):
        """Déclenche une catastrophe localisée."""
        # Coût de l'action
        cost = 30
        
        if self.player_power < cost:
            messagebox.showwarning("Pouvoir insuffisant", 
                                 f"Vous n'avez pas assez de points de pouvoir. Coût: {cost}, Disponible: {self.player_power}")
            return
        
        # Types de catastrophes
        catastrophe_types = [
            "Tremblement de terre",
            "Éruption volcanique",
            "Inondation",
            "Tempête",
            "Incendie"
        ]
        
        # Demande du type de catastrophe
        catastrophe_type = simpledialog.askstring(
            "Type de catastrophe",
            "Choisissez un type de catastrophe:\n" + "\n".join(catastrophe_types),
            parent=self.root
        )
        
        if not catastrophe_type or catastrophe_type not in catastrophe_types:
            return
        
        # Demande de l'intensité
        intensity = simpledialog.askfloat(
            "Intensité",
            "Entrez l'intensité de la catastrophe (0.1-1.0):",
            minvalue=0.1,
            maxvalue=1.0,
            parent=self.root
        )
        
        if not intensity:
            return
        
        # Confirmation
        if not messagebox.askyesno("Confirmation", 
                                 f"Déclencher un(e) {catastrophe_type} d'intensité {intensity:.1f} ? Coût: {cost} points de pouvoir"):
            return
        
        # Application de la catastrophe
        x, y = self.selected_cell
        
        # Déduction des points
        self.player_power -= cost
        self.power_label.config(text=f"{self.player_power} points")
        
        # Mise à jour du temps de la dernière action
        self.last_action_time = self.world.age
        
        # Effets selon le type de catastrophe
        if catastrophe_type == "Tremblement de terre":
            # Modification du terrain
            radius = int(10 * intensity)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = (x + dx) % self.world.geography.grid_size, (y + dy) % self.world.geography.grid_size
                    distance = np.sqrt(dx**2 + dy**2)
                    
                    if distance <= radius:
                        # Effet décroissant avec la distance
                        effect = (1 - distance / radius) * intensity
                        
                        # Modification de l'élévation
                        if random.random() < effect * 0.5:
                            if self.world.geography.elevation[ny, nx] > self.world.geography.sea_level:
                                # Création de fissures (baisse d'élévation)
                                self.world.geography.elevation[ny, nx] -= effect * 0.2
            
            # Impact sur les espèces et civilisations
            if hasattr(self.world, 'ecosystem'):
                for species in self.world.ecosystem.species:
                    local_pop = species.get_local_population(x, y)
                    if local_pop > 0:
                        # Réduction de la population locale
                        reduction = min(local_pop, local_pop * intensity * 0.7)
                        species.population_map[y, x] -= reduction
                        species.population -= int(reduction)
            
            if hasattr(self.world, 'civilization_manager'):
                for civ in self.world.civilization_manager.civilizations:
                    if civ.territory[y, x]:
                        # Dégâts à la civilisation
                        pop_loss = int(civ.population * intensity * 0.05)
                        civ.population -= pop_loss
                        civ.stability -= intensity * 0.2
                        
                        # Enregistrement de l'événement
                        civ.add_history_event("Catastrophe", 
                                            f"Tremblement de terre d'intensité {intensity:.1f} - "
                                            f"{pop_loss:,} victimes")
        
        elif catastrophe_type == "Éruption volcanique":
            # Création d'un volcan
            if self.world.geography.elevation[y, x] > self.world.geography.sea_level:
                # Augmentation de l'élévation
                self.world.geography.elevation[y, x] += intensity * 0.3
                
                # Changement de biome
                self.world.geography.biomes[y, x] = BiomeType.VOLCANIC.value
                
                # Effet sur les cellules environnantes
                radius = int(15 * intensity)
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        nx, ny = (x + dx) % self.world.geography.grid_size, (y + dy) % self.world.geography.grid_size
                        distance = np.sqrt(dx**2 + dy**2)
                        
                        if distance <= radius:
                            # Effet décroissant avec la distance
                            effect = (1 - distance / radius) * intensity
                            
                            # Cendres volcaniques (effet sur la température et les précipitations)
                            if hasattr(self.world, 'climate'):
                                self.world.climate.temperature[ny, nx] -= effect * 0.2
                                self.world.climate.precipitation[ny, nx] += effect * 0.1
                            
                            # Impact sur les espèces
                            if hasattr(self.world, 'ecosystem'):
                                for species in self.world.ecosystem.species:
                                    local_pop = species.get_local_population(nx, ny)
                                    if local_pop > 0:
                                        # Réduction de la population locale
                                        reduction = min(local_pop, local_pop * effect * 0.9)
                                        species.population_map[ny, nx] -= reduction
                                        species.population -= int(reduction)
                
                # Impact sur les civilisations
                if hasattr(self.world, 'civilization_manager'):
                    for civ in self.world.civilization_manager.civilizations:
                        affected_cells = 0
                        for dy in range(-radius, radius + 1):
                            for dx in range(-radius, radius + 1):
                                nx, ny = (x + dx) % self.world.geography.grid_size, (y + dy) % self.world.geography.grid_size
                                if civ.territory[ny, nx]:
                                    affected_cells += 1
                        
                        if affected_cells > 0:
                            # Dégâts proportionnels au territoire affecté
                            territory_percentage = affected_cells / np.sum(civ.territory)
                            pop_loss = int(civ.population * territory_percentage * intensity * 0.3)
                            civ.population -= pop_loss
                            civ.stability -= intensity * 0.15 * territory_percentage
                            
                            # Enregistrement de l'événement
                            civ.add_history_event("Catastrophe", 
                                                f"Éruption volcanique d'intensité {intensity:.1f} - "
                                                f"{pop_loss:,} victimes")
        
        # Autres types de catastrophes à implémenter...
        
        # Enregistrement de l'action
        self.player_actions.append({
            "year": self.world.age,
            "action": "catastrophe",
            "details": f"{catastrophe_type} d'intensité {intensity:.1f} aux coordonnées ({x}, {y})",
            "cost": cost
        })
        
        # Message de confirmation
        self.logger.warning(f"CATASTROPHE: {catastrophe_type} d'intensité {intensity:.1f} déclenché par le joueur aux coordonnées ({x}, {y})")
        messagebox.showinfo("Catastrophe déclenchée", 
                          f"Un(e) {catastrophe_type} d'intensité {intensity:.1f} a été déclenché(e).")
        
        # Mise à jour de l'affichage
        self._draw_world()
    
    def _deity_modify_climate(self):
        """Modifie le climat d'une région."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _deity_modify_terrain(self):
        """Modifie le terrain d'une région."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _deity_create_species(self):
        """Crée une nouvelle espèce."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _deity_blessing(self):
        """Applique une bénédiction à une région."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _deity_curse(self):
        """Applique une malédiction à une région."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _civ_action(self, action_type):
        """Exécute une action en mode civilisation."""
        # Vérification du mode
        if self.player_mode != "civilization":
            messagebox.showinfo("Mode incorrect", "Cette action n'est disponible qu'en mode Civilization.")
            return
        
        # Vérification de la sélection d'une civilisation
        if not self.selected_civilization:
            messagebox.showinfo("Sélection requise", 
                              "Vous devez d'abord sélectionner une civilisation sur la carte.")
            return
        
        # Vérification du temps de recharge
        if self.world.age - self.last_action_time < self.action_cooldown:
            remaining = self.action_cooldown - (self.world.age - self.last_action_time)
            messagebox.showinfo("Action en recharge", 
                              f"Vous devez attendre encore {remaining} années avant de pouvoir agir à nouveau.")
            return
        
        # Exécution de l'action selon son type
        if action_type == "develop_tech":
            self._civ_develop_tech()
        elif action_type == "expand":
            self._civ_expand()
        elif action_type == "diplomacy":
            self._civ_diplomacy()
        elif action_type == "special_project":
            self._civ_special_project()
    
    def _civ_develop_tech(self):
        """Développe la technologie de la civilisation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _civ_expand(self):
        """Étend le territoire de la civilisation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _civ_diplomacy(self):
        """Gère les relations diplomatiques de la civilisation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def _civ_special_project(self):
        """Lance un projet spécial pour la civilisation."""
        # Implémentation à compléter
        messagebox.showinfo("Information", "Fonctionnalité à implémenter.")
    
    def update(self):
        """Met à jour l'affichage (appelé depuis le thread principal de simulation)."""
        # Envoi d'un message au thread d'interface
        self.queue.put("update")
        
        # Régénération des points de pouvoir
        if self.player_mode == "deity" or self.player_mode == "civilization":
            self.player_power = min(100, self.player_power + self.power_regen_rate)
    
    def start(self):
        """Démarre la boucle principale de l'interface."""
        self.root.mainloop()

