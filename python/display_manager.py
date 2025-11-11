import json
import time
import os
import sys
import subprocess
import re

# Fichier de sortie généré par metadata_listener.py
INPUT_FILE = '/tmp/current_track.json'

# --- CONFIGURATION REQUISE ---
# Nous ciblons la Carte 0 (H3 Audio Codec) car elle seule possède des contrôles de volume fonctionnels.

# Périphérique ALSA : Carte 0 (H3 Audio Codec). L'argument -c 0 sera utilisé.
CARD_ID = "0" 
# Nom du contrôle de volume (Doit être 'DAC', 'Line Out' ou autre)
# Si l'erreur persiste, nous devons trouver le nom exact avec 'amixer -c 0 scontrols'
MIXER_CONTROL_NAME = "DAC" 

# --- FIN DE LA CONFIGURATION ---
def afficher_volume():
    """
    Exécute la commande 'pactl get-sink-volume @DEFAULT_SINK@' pour obtenir le volume
    du périphérique de sortie par défaut et extrait le pourcentage de volume.

    Retourne :
        str: Le pourcentage de volume (ex: "80%"), ou None en cas d'erreur.
    """
    try:
        # NOTE IMPORTANTE : Pour récupérer la sortie, l'objet Popen doit être stocké.
        result = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # Le stdout contient une chaîne comme : "Volume: 0: 65536 / 100% / 0.00 dB"
        output = result.stdout.strip()

        # Utiliser une expression régulière pour trouver le pourcentage
        # Recherche la séquence de chiffres suivie de '%'
        match = re.search(r'(\d+)\%', output)

        if match:
            # match.group(0) est la correspondance complète (ex: "100%")
            # match.group(1) est le pourcentage (ex: "100")
            return f"{match.group(1)}%"
        else:
            print("Erreur : Format de sortie 'pactl' inattendu.")
            return None

    except subprocess.CalledProcessError as e:
        # Gère les cas où la commande 'pactl' échoue
        print(f"Erreur lors de l'exécution de pactl : {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        # Gère les cas où la commande 'pactl' n'est pas trouvée (PulseAudio non installé)
        print("Erreur : La commande 'pactl' est introuvable. Assurez-vous que PulseAudio est installé.")
        return None


def ajuster_volume(pourcentage):
    """
    Définit le volume du contrôle ALSA ciblé.

    Args:
        pourcentage (str): Le niveau de volume souhaité, par exemple "50%", "+10%", ou "-5%".
                           Peut aussi être "mute" ou "unmute" pour couper.

    Retourne:
        bool: True si l'ajustement est réussi, False sinon.
    """
    try:
        # Utilisation de 'sset' sur la carte 0 avec le nom du contrôle spécifique
        subprocess.run(
            ["amixer", "-c", CARD_ID, "sset", MIXER_CONTROL_NAME, pourcentage],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"Volume ALSA (Contrôle {MIXER_CONTROL_NAME} sur Carte {CARD_ID}) ajusté à : {pourcentage}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'ajustement du volume ALSA ({pourcentage}) : {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print("Erreur : La commande 'amixer' (alsa-utils) est introuvable.")
        return False

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
        ajuster_volume("00%")
    else:
        ajuster_volume("100%")

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

    print("==================================================\n\n")

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
