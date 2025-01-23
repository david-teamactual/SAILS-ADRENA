
# Lecture du dictionnaire des voiles depuis un fichier texte
with open("dict_voiles.txt", "r", encoding='utf-8-sig') as f:
    contenu = f.readlines()

# Convertit le fichier en un dictionnaire
dict_voiles = {}
for ligne in contenu:
        valeurs = ligne.strip().split(', ')
        cle = valeurs[0]
        dict_voiles[cle] = valeurs[1:]