import json
import time
import os
import sys
import subprocess

# Fichier de sortie généré par metadata_listener.py
INPUT_FILE = '/tmp/current_track.json'

def forcer_le_volume_zero():
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "00%"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

def remettre_le_volume():
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%" ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
        )

def extraire_volume(volume_line):
    print(f"in extraire : volume_line= {volume_line}")
    volume = ""
    elements = volume_line.split("/")
    print(elements)
    return elements[1]


def clear_screen():
    """Efface l'écran du terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_track_info():
    """Charge les informations de la piste à partir du fichier JSON."""
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "Starting", "title": "No data file yet."}
    except json.JSONDecodeError:
        # Peut arriver si le fichier est en cours d'écriture
        return {"status": "Error", "title": "Reading error..."}
    except Exception as e:
        return {"status": "Error", "title": f"Unknown error: {e}"}

def display_info(track_data):
    """Affiche les informations de la piste dans un format propre."""
    status = track_data.get("status", "N/A")
    title = track_data.get("title", "Titre Inconnu") 
    artist = track_data.get("artist", "Artiste Inconnu")
    album = track_data.get("album", "Album Inconnu")

    global sortie_volume

    if "Annonce • " in artist:
        title = "PUBLICITE"
        forcer_le_volume_zero()
    else:
        remettre_le_volume()

    # Simple formatting for terminal
    print("==================================================")
    print("🎧 Lecteur Bluetooth A2DP")
    print("==================================================")
    print(f"Statut : {status}")

    # Affichage différent si déconnecté ou erreur
    if status == "Disconnected" or status == "Starting":
        print(f"Message: {title}")
    else:
        print("\n--- Piste en cours ---")
        print(f"Titre  : {title}")
        print(f"Artiste: {artist}")
        print(f"Album  : {album}")
        
        duration = track_data.get("duration", 0)
        if duration > 0:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"Durée : {minutes:02d}m {seconds:02d}s")
    
    print("==================================================")
    
def main():
    last_content_hash = None

    # Vérifie si le script est lancé sans le service en arrière-plan
    if not os.path.exists(INPUT_FILE):
        print(f"ATTENTION : Le fichier de données {INPUT_FILE} n'existe pas.")
        print("Assurez-vous que metadata_listener.service est actif et fonctionne.")
        time.sleep(3) # Laisse le temps de lire l'erreur avant de commencer la boucle

    print("Démarrage du gestionnaire d'affichage...")

    while True:
        track_data = load_track_info()
        
        # Sérialise le contenu pour la vérification du changement
        current_content_hash = json.dumps(track_data, sort_keys=True)
        
        # Mettre à jour l'affichage uniquement si les données ont changé
        if current_content_hash != last_content_hash:
#            clear_screen()
            display_info(track_data)
            last_content_hash = current_content_hash
        
        time.sleep(2) # Interrogation du fichier toutes les 2 secondes

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt du gestionnaire d'affichage.")
        sys.exit(0)
