import socket
import struct
import statistics
import time
import configparser
from time import monotonic
import datetime

import adrena # Importer le fichier adrena.py
import dict_voiles # Importer le fichier dict_voiles.py
import com_bravo # Importer le fichier com_bravo.py
import fenetre # Importer le fichier fenetre.py

# Création d'un objet ConfigParser et lecture du fichier INI
config = configparser.ConfigParser()
config.read('config.ini')

liste_nom_voiles = []
dico_bravo_voiles = {}

# production d'un dictionnaire des voiles sans les noms des voiles et sans le premier tuple correspondant à la GV
dict_voiles_sans_gv = {cle: valeur for cle, valeur in list(dict_voiles.dict_voiles.items())[1:]}
print("Dictionnaire des voiles:", dict_voiles_sans_gv)

for voile, data in dict_voiles.dict_voiles.items() :
    liste_nom_voiles.append(data[0])
print("Liste des voiles :",liste_nom_voiles)

# lancement de la communiucation avec Bravo et demande d'envoi des trames
com_bravo.init_bravo ()
timer_init_bravo = 0
tempo_timer_init_bravo = 300 #choix des 300s car j'ai vu que C100 rappelait les datas toutes les 300s
start_timer_init_bravo = monotonic() #démarrage du timer de relance de la bravo

timer_envoi_config_adrena = 0
frequence_envoi_config_adrena = config.getfloat('Adrena', 'frequence_adrena')
tempo_timer_envoi_config_adrena = 1/frequence_envoi_config_adrena
start_timer_envoi_config_adrena = monotonic()

def vidage_buffer (): # tempo pour vider le buffer
    timer = 0
    tempo = 0.05
    start = monotonic()
    while timer < tempo:
        message_bravo = com_bravo.lecture_message_bravo()
        end = monotonic()
        timer = (end-start)

# Lancer la fenêtre tkinter
fenetre.afficher_fenetre()

while True:

    fenetre.envoyer_signal("TOGGLE")
    
#reception de la config voiles de Bravo et envoi à Adrena

    chrono = monotonic()
    timer_init_bravo = (chrono-start_timer_init_bravo)
    timer_envoi_config_adrena = (chrono-start_timer_envoi_config_adrena)

    message_bravo = com_bravo.lecture_message_bravo()
    
    if message_bravo: #retourne true si non vide
        liste_bravo_voiles = adrena.reception_config_bravo_voiles(message_bravo)
    else : #si message bravo vide se mettre en attente de connexion
        liste_bravo_voiles = "pas-de-bravo"

    if liste_bravo_voiles == "pas-de-liste-bravo-voiles":
        print("Statut programme : attente des données Bravo")
    elif liste_bravo_voiles == "pas-de-bravo": #les trames sont vides, on attend la reconnexion avec la Bravo
        com_bravo.init_bravo () #demande à Bravo d'envoyer les trames avec les variables d'état des alarmes
        print("Statut programme : attente connexion Bravo")
        print("Nouvelle tentative de connexion toutes les :", com_bravo.SOCKET_TIMEOUT_BRAVO, "s")
        fenetre.envoyer_message(f"Attente reconnexion Bravo.")
        fenetre.envoyer_message(f"Nouvelle tentative de connexion toutes les : {com_bravo.SOCKET_TIMEOUT_BRAVO}s")
    else:
        for nom, etat_bravo_voile in zip(liste_nom_voiles, liste_bravo_voiles):
            dico_bravo_voiles[nom] = int(etat_bravo_voile)
        vidage_buffer ()
        print("Config voiles Bravo :", dico_bravo_voiles)
        fenetre.envoyer_message(f"Config voiles Bravo : {dico_bravo_voiles}")
                
        # demande d'envoi des trames Adrena
        if timer_envoi_config_adrena > tempo_timer_envoi_config_adrena:
            adrena.creation_socket_adrena()
            adrena.envoi_config_adrena(dico_bravo_voiles)
            start_timer_envoi_config_adrena = monotonic() #redémarrage du timer d'envoi de trame Adrena     

    # demande à Bravo de renvoyer les trames à la fin du timer
    if timer_init_bravo > tempo_timer_init_bravo:
        com_bravo.envoi_trames ()
        start_timer_init_bravo = monotonic() #redémarrage du timer de relance de la bravo