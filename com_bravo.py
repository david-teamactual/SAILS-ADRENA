import socket
import dict_voiles
import configparser

# Création d'un objet ConfigParser et lecture du fichier INI
config = configparser.ConfigParser()
config.read('config.ini')

# Lecture des paramètres de connexion
UDP_IP_BRAVO = config.get('Bravo', 'UDP_IP_BRAVO')
UDP_PORT_BRAVO = config.getint('Bravo', 'UDP_PORT_BRAVO')
SOCKET_TIMEOUT_BRAVO = config.getfloat('Bravo', 'SOCKET_TIMEOUT_BRAVO')

# Utilisation des paramètres de connexion
print(f'Adresse IP : {UDP_IP_BRAVO}')
print(f'Port : {UDP_PORT_BRAVO}')
print(f'Timeout : {SOCKET_TIMEOUT_BRAVO} secondes')

def creation_socket_bravo():
    """Création d'une socket et des variables associées pour initier 
    une communication en UDP avec la centrale Bravo"""

    global UDP_IP_BRAVO, UDP_PORT_BRAVO, SOCKET_BRAVO, SOCKET_TIMEOUT_BRAVO

    # SOCKET EN MODE BLOQUANT PAR DEFAUT
    SOCKET_BRAVO = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # DGRAM pour utiliser le protocole UDP
    SOCKET_BRAVO.settimeout(SOCKET_TIMEOUT_BRAVO)  # Socket en mode timeout pour soulever une erreur si delai dépassé

def envoi_trames ():
    
    TRAME_START = b"#CLEARREFRESHEDVARS,1C\n" # Efface la configuration actuelle de rafraichissement des variables du serveur, à envoyer au début
    
    # Construction de la trame #ENABLEREFRESHEDVARS avec la fréquence du fichier config.ini
    frequence_sv_bravo = config.getfloat('Bravo', 'frequence_sv_bravo')
    checksum_TRAME_END = 0
    TRAME_END_without_checksum = "#ENABLEREFRESHEDVARS," + str(frequence_sv_bravo) + "," # Envoie les informations périodiques a une fréquence donnée sur les variables déjà mappées, à envoyer à la fin
        # Calculer le checksum avec l'opération XOR
    for b in TRAME_END_without_checksum.encode():
        checksum_TRAME_END ^= b
        # Convertir le checksum en chaîne hexadécimale
    checksum_hex_TRAME_END = '{:02X}'.format(checksum_TRAME_END)
        # Ajouter le checksum à la fin de la trame
    TRAME_END_with_checksum = TRAME_END_without_checksum.encode() + checksum_hex_TRAME_END.encode('ascii') + b'\n'
    TRAME_END = TRAME_END_with_checksum
    
    # Génération des trames Bravo pour les voiles J
    trames_j = []
    checksum_TRAME_J = 0
    canal_bravo = 1

    for voile in list(dict_voiles.dict_voiles.items()):
        TRAME_J_without_checksum = "#SETREFRESHEDVAR," + str(canal_bravo) + ",sail_" + str(voile[0]) + "_stng,,0,"
        canal_bravo = canal_bravo + 1

        # Calculer le checksum avec l'opération XOR
        for b in TRAME_J_without_checksum.encode():
            checksum_TRAME_J ^= b
        
        # Convertir le checksum en chaîne hexadécimale
        checksum_hex_TRAME_J = '{:02X}'.format(checksum_TRAME_J)

        # Ajouter le checksum à la fin de la trame
        TRAME_J_with_checksum = TRAME_J_without_checksum.encode() + checksum_hex_TRAME_J.encode('ascii') + b'\n'
        TRAME_J = TRAME_J_with_checksum
        trames_j.append(TRAME_J)

        checksum_TRAME_J = 0

    SOCKET_BRAVO.sendto(TRAME_START, (UDP_IP_BRAVO, UDP_PORT_BRAVO))
    print(TRAME_START)
    
    for TRAME_J in trames_j:
        print(TRAME_J)
        SOCKET_BRAVO.sendto(TRAME_J, (UDP_IP_BRAVO, UDP_PORT_BRAVO))

    SOCKET_BRAVO.sendto(TRAME_END, (UDP_IP_BRAVO, UDP_PORT_BRAVO))
    print(TRAME_END)

def init_bravo (): #regroupe les 2 étapes pour demander à la Bravo d'envoyer les trames
    creation_socket_bravo()
    envoi_trames()

def lecture_message_bravo():
    """Permet de recevoir les trames envoyée de Bravo
    et de la stocker dans une variable """

    try:
        trame_recu_b = SOCKET_BRAVO.recv(128)
        trame_recu_str = trame_recu_b.decode('utf-8')
        message_bravo = trame_recu_str
        # print("Message BRAVO :", message_bravo)

    # inspiré du code de Mathilde, à voir si ça fonctionne avec toutes les erreurs de connection
    except socket.timeout : 
        print("Problème connexion Ethernet avec Bravo")
        init_bravo()
        message_bravo = ""

    # ajouté suite conseil de chatgpt parce que j'avais l'erreur
    # ConnectionResetError: [WinError 10054] Une connexion existante a dû être fermée par l’hôte distant
    # juste avec except socket.timeout
    except ConnectionResetError:
        print("Connexion réinitialisée par l'hôte distant")
        init_bravo()
        message_bravo = ""
        
    return message_bravo