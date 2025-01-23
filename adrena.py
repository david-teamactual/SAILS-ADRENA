import com_bravo
import socket
import configparser

# Création d'un objet ConfigParser et lecture du fichier INI
config = configparser.ConfigParser()
config.read('config.ini')

def reception_config_bravo_voiles(message_bravo):
        
    id_trame_bravo = message_bravo[1] + message_bravo[2]
    id_voile = 0
    liste_bravo_voiles = []
    
    if "".join(id_trame_bravo) == "SV":  # Message Bravo avec la variable alarme
        
        #la première valeur correspond au niveau de ris de la GV et la deuxième à la tempo d'acquittement, ensuite c'est la liste des alarmes
        valeurs = message_bravo.split(",") #on sépare la trame en une liste de valeurs séparées par des virgules
        valeurs.pop(0) #on enlève le premier élément de la liste qui correspond à #SV
        valeurs.pop() #on enlève le dernier élément de la liste qui correspond au checksum
        liste_bravo_voiles = valeurs[1::2] #on garde que les élèments impairs pour ne garder que les valeurs des datas

        #print("Liste valeurs data Bravo :",liste_bravo_voiles)

    elif "".join(id_trame_bravo) == "RE" or "".join(id_trame_bravo) == "PO":
        print("Pas de liste bravo_voiles !")
        liste_bravo_voiles = "pas-de-liste-bravo-voiles"
    else:
        print("Message Bravo non identifié !")
        com_bravo.init_bravo ()
    return liste_bravo_voiles

def creation_socket_adrena():  
   
    global UDP_IP_ADRENA, UDP_PORT_ADRENA, UDP_IP_SOURCE, SOCKET_ADRENA

    UDP_IP_ADRENA = config.get('Adrena', 'UDP_IP_ADRENA')
    UDP_PORT_ADRENA = config.getint('Adrena', 'UDP_PORT_ADRENA')
    UDP_IP_SOURCE = config.get('Adrena', 'UDP_IP_SOURCE')
    UDP_PORT_SOURCE = config.getint('Adrena', 'UDP_PORT_SOURCE')

    SOCKET_ADRENA = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # DGRAM pour utiliser le protocole UDP
    SOCKET_ADRENA.bind((UDP_IP_SOURCE, UDP_PORT_SOURCE))

def envoi_config_adrena(dico_bravo_voiles):
    """Routine permettant d'envoyer au bon format
    la configuration de voile à Adrena"""
        
    if len(dico_bravo_voiles) == 0:
        nom_gv = None
    else:
        nom_gv = next(iter(dico_bravo_voiles.keys()))

    if nom_gv is not None:
        if dico_bravo_voiles[nom_gv] == 1:
            phrase_adrena_gv = nom_gv + ";1"
        elif dico_bravo_voiles[nom_gv] == 0:
            phrase_adrena_gv = nom_gv + ";"
        elif dico_bravo_voiles[nom_gv] == -1:
            phrase_adrena_gv = ";"
        elif dico_bravo_voiles[nom_gv] == 2:
            phrase_adrena_gv = nom_gv + ";2"
        elif dico_bravo_voiles[nom_gv] == 3:
            phrase_adrena_gv = nom_gv + ";3"
        else:
            phrase_adrena_gv = ";"
    else:
        phrase_adrena_gv = ";"

    #print("Phrase Adrena gv :",phrase_adrena_gv)

    voiles_val = []
    for voile, val in list(dico_bravo_voiles.items())[1:]:
        if val == 0:
            voiles_val.append('')
        elif val == 1:
            voiles_val.append(f';{voile};')

    phrase_adrena = 'SAILSUP=' + phrase_adrena_gv + ''.join(voiles_val)
    #print("Phrase Adrena :",phrase_adrena,"\n")

    phrase_adrena_b = phrase_adrena.encode()  # Transforme le string phrase_adrena en byte pour envoi udp sur adrena
    SOCKET_ADRENA.sendto(phrase_adrena_b, (UDP_IP_ADRENA, UDP_PORT_ADRENA))