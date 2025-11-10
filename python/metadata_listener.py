#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from pydbus import SystemBus
from gi.repository import GLib
import traceback 
import os
import json
import subprocess


# Nom du service BlueZ sur D-Bus
BLUEZ_SERVICE = 'org.bluez'
# Interface pour le gestionnaire d'objets (pour trouver les appareils connectés)
MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
# Chemin du fichier de sortie pour l'affichage (lisible par d'autres programmes)
OUTPUT_FILE = '/tmp/current_track.json'

def forcer_le_volume_zero():
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "00%"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

def remettre_le_volume():
    print(F"Je vais mettre le volume à 100%")
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%" ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

# Global pour stocker la piste actuelle et éviter les impressions répétitives
current_track = {"Title": None, "Artist": None}

def write_track_info(track_data, status):
    """Écrit les informations de la piste dans un fichier JSON pour un accès externe."""
    try:
        data_to_save = {
            "status": status,
            "artist": track_data.get('Artist', 'N/A'),
            "title": track_data.get('Title', 'N/A'),
            "album": track_data.get('Album', 'N/A'),
            "duration": track_data.get('Duration', 0) / 1000 # Convertir en secondes
        }
        
        # S'assurer que le répertoire /tmp existe (normalement garanti)
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            
        # print(f"Métadonnées écrites dans {OUTPUT_FILE}")

    except Exception as e:
        print(f"!!! ERREUR lors de l'écriture du fichier {OUTPUT_FILE}: {e}")

def get_player_path(bus):
    """Trouve le chemin D-Bus de l'objet lecteur (MediaPlayer) associé à un appareil connecté."""
    try:
        manager = bus.get(BLUEZ_SERVICE, '/')
        objects = manager.GetManagedObjects()

        for path, interfaces in objects.items():
            if 'org.bluez.MediaPlayer1' in interfaces:
                # print(f"Lecteur média trouvé : {path}")
                return path

        return None
    except Exception as e:
        # print(f"Erreur lors de la recherche du lecteur D-Bus : {e}")
        return None

def check_media_status():
    """Vérifie l'état du lecteur média périodiquement."""
    global current_track
    
    try:
        bus = SystemBus()
        player_path = get_player_path(bus)
        
        if not player_path:
            # Si aucun lecteur n'est trouvé, réinitialiser l'état pour ne pas afficher le dernier titre
            if current_track["Title"] is not None:
                current_track = {"Title": None, "Artist": None}
                write_track_info({"Title": "N/A"}, "Disconnected")
                print("\n--- STATUT ---")
                print("Appareil déconnecté ou lecteur non disponible.")
                print("--------------\n")
            return True # Continuer le polling

        # Accéder directement à l'interface MediaPlayer1
        player = bus.get(BLUEZ_SERVICE, player_path)
        
        # Le dictionnaire 'Properties' contient 'Status', 'Track', 'Position', etc.
        properties = player.GetAll('org.bluez.MediaPlayer1')
        
        track_info = properties.get('Track', {})
        status = properties.get('Status', 'inconnu')

        if track_info:
            artist = track_info.get('Artist', 'Inconnu')
            title = track_info.get('Title', 'Inconnu')
            
            # Afficher et mettre à jour le fichier uniquement si la piste a changé
            # ou si le statut a changé (pour couvrir Pause/Play)
            if "Annonce " in artist:
                forcer_le_volume_zero()
            else:
                remettre_le_volume()

            # Simplification : on vérifie juste si le titre a changé
            if title != current_track["Title"] or artist != current_track["Artist"] or status.lower() == 'playing':
                current_track["Title"] = title
                current_track["Artist"] = artist
                
                album = track_info.get('Album', 'N/A')
                
                print("\n--- NOUVELLE PISTE (POLLING) ---")
                print(f"Status: {status.capitalize()}")
                print(f"Artiste : {artist}")
                print(f"Titre : {title}")
                print(f"Album : {album}")
                print("-------------------------------\n")
                
                write_track_info(track_info, status.capitalize())

        elif status.lower() == 'paused':
             # Gérer le cas où il n'y a pas de métadonnées, mais le statut est Paused (utile pour l'affichage)
             print(f"\n--- LECTEUR EN PAUSE ---")
             print(f"Status: {status.capitalize()}")
             print("----------------------\n")
             write_track_info(current_track, status.capitalize())

        else:
            # Statut non géré ou piste vide
            pass

    except Exception as e:
        # Affichera l'erreur si bus.get() ou player.GetAll() échoue
        # print(f"Erreur de polling : {e}")
        # traceback.print_exc()
        # Ne rien faire pour éviter un spam de logs si le lecteur est momentanément instable
        pass

    return True # Le timer doit retourner True pour continuer à s'exécuter

def main():
    print("Tentative de connexion au bus D-Bus et démarrage du listener par Polling.")
    
    try:
        bus = SystemBus()
        print("Connecté au bus système D-Bus.")

        # Configuration de l'interrogation (polling) toutes les 2 secondes
        GLib.timeout_add_seconds(2, check_media_status)
        print("Interrogation (Polling) de l'état média démarrée toutes les 2 secondes.")

        # Maintenir le script actif pour écouter les événements
        loop = GLib.MainLoop()
        
        print("Démarrage de la boucle principale (MainLoop).") 
        loop.run()
        
    except KeyboardInterrupt:
        print("Arrêt par l'utilisateur.")
    except Exception as e:
        print("\n!!! ERREUR CRITIQUE DANS L'INITIALISATION !!!")
        traceback.print_exc() 
    finally:
        print("Nettoyage et arrêt.")

if __name__ == "__main__":
    main()
