# orange-pi-zero-sound
## Connexion Bluetooth A2DP Persistante
### Objectif : Établir une connexion Bluetooth Audio (A2DP-Sink) automatique et persistante entre un
Orange Pi Zero et une tablette spécifique (MAC : 9C:39:28:2E:FF:F9 ), en contournant les erreurs de
profil indisponible ( br-connection-profile-unavailable ) et l'absence des binaires BlueAlsa.
## Problème Racine : L'exécutable bluealsa et ses outils ( bluealsa-aplay ) étaient absents du
système 
Distribution Orange Pi/Armbian spécifique, nécessitant une compilation manuelle. 
Lacompilation a révélé que les binaires sont installés sous les noms bluealsad et bluealsa-aplay dans le répertoire /usr/bin.

### Compilation Manuelle de BlueAlsa
#### Préparation et Installation des Dépendances
- Mise à jour des listes de paquets
- sudo apt update
- Installation des dépendances de compilation (Build Essentials)
- sudo apt install -y build-essential automake libtool git
- sudo apt install -y libasound2-dev libbluetooth-dev libglib2.0-dev

#### . Compilation Manuelle de BlueAlsa
Aller dans le répertoire temporaire
- cd /tmp
- Cloner le dépôt officiel BlueAlsa
-- git clone [https://github.com/Arkq/bluez-alsa.git](https://github.com/Arkq/bluez-alsa.g)
- cd bluez-alsa
- autoreconf --install
- ./configure --enable-a2dp-sink
- make
- sudo make install

### Installation
Copier les fichiers avec sudo 
-- les services 
--- /etc/asound.conf vers /etc/
--- /etc/systemd/system/bluealsa.service
---/etc/systemd/system/a2dp-playback.service

-- les fichiers executables
--- /usr/local/bin/metadata_listener.py
--- /usr/local/bin/display_manager.py

Valider le demarage des servies au prochian reboot
--- sudo systemctl enable bluealsa.service
--- sudo systemctl enable a2dp-playback.service
--- sudo systemctl enable a2dp-playback.service

Rebooter la carte
-- sudo reboot


