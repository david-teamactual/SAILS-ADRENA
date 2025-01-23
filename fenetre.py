import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import queue
import pystray
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw, ImageTk

# Créer une file de messages pour communiquer entre threads
signal_queue = queue.Queue()
message_queue = queue.Queue()  # File pour les messages

def fermer_programme_proprement(root, icon):
    """Ferme proprement l'application et la systray."""
    icon.stop()  # Arrête la systray
    root.quit()  # Termine la boucle Tkinter
    os._exit(0)  # Termine le processus immédiatement

def dessiner_cadre_arrondi(canvas, x1, y1, x2, y2, rayon, couleur):
    """Dessine un rectangle avec des angles arrondis sur un Canvas."""
    canvas.create_arc(x1, y1, x1 + 2 * rayon, y1 + 2 * rayon, start=90, extent=90, fill=couleur, outline=couleur)
    canvas.create_arc(x2 - 2 * rayon, y1, x2, y1 + 2 * rayon, start=0, extent=90, fill=couleur, outline=couleur)
    canvas.create_arc(x1, y2 - 2 * rayon, x1 + 2 * rayon, y2, start=180, extent=90, fill=couleur, outline=couleur)
    canvas.create_arc(x2 - 2 * rayon, y2 - 2 * rayon, x2, y2, start=270, extent=90, fill=couleur, outline=couleur)
    canvas.create_rectangle(x1 + rayon, y1, x2 - rayon, y2, fill=couleur, outline=couleur)
    canvas.create_rectangle(x1, y1 + rayon, x2, y2 - rayon, fill=couleur, outline=couleur)

def afficher_fenetre():
    """Affiche une fenêtre Tkinter avec des cadres arrondis."""
    def run():
        # Création de la fenêtre principale
        root = tk.Tk()
        root.title("SAILS ADRENA")
        root.geometry("500x400")

        # Configuration des couleurs
        bg_color = "#2C2C2C"  # Gris foncé pour le fond
        text_color = "#FFFFFF"  # Blanc pour le texte
        cadre_color = "#3A3A3A"  # Gris clair pour les cadres
        root.config(bg=bg_color)

        # Canvas pour dessiner les cadres
        canvas = tk.Canvas(root, bg=bg_color, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Dessin du cadre regroupé avec angles arrondis
        dessiner_cadre_arrondi(canvas, 50, 20, 450, 150, 20, cadre_color)
        canvas.create_text(250, 60, text="Programme SAILS ADRENA !", 
                           font=("Arial", 14, "bold"), fill=text_color)
        canvas.create_text(250, 110, text="Ce programme permet d'envoyer\n"
                                          "     la config. de voiles à ADRENA.", 
                           font=("Arial", 14), fill=text_color)

        # Animation : Texte clignotant
        animation_label = tk.Label(root, text="Si ça clignote, c'est que le programme fonctionne.",
                                   font=("Arial", 12, "bold"), bg=bg_color, fg="white")
        animation_label.place(x=55, y=180)

        # Ajouter une zone de texte défilante pour les messages
        message_frame = tk.Frame(root, bg=bg_color)
        message_frame.place(x=50, y=240, width=400, height=130)

        scrolled_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, bg="#3A3A3A", fg="white",
                                                  font=("Arial", 10), highlightthickness=0, bd=0)
        scrolled_text.pack(fill="both", expand=True)
        scrolled_text.config(state=tk.DISABLED)  # Rendre la zone non éditable

        # Gestion de la fermeture classique (croix en haut à droite)
        root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())  # Cache la fenêtre au lieu de la détruire

        # Gestion de la réduction (bouton "-")
        def cacher_fenetre():
            root.withdraw()  # Cache la fenêtre principale

        root.bind("<Unmap>", lambda event: cacher_fenetre() if root.state() == "iconic" else None)

        # Fonction pour mettre à jour l'animation en fonction des signaux
        def update_animation():
            try:
                # Vérifie s'il y a un signal dans la queue
                signal = signal_queue.get_nowait()
                if signal == "TOGGLE":
                    current_color = animation_label.cget("fg")
                    new_color = "green" if current_color == "white" else "white"
                    animation_label.config(fg=new_color)
            except queue.Empty:
                pass

            # Rappelle cette fonction après 200 ms
            root.after(200, update_animation)

         # Fonction pour mettre à jour la zone de texte avec les messages
        MAX_LINES = 100  # Nombre maximal de lignes dans la zone de texte
        def update_messages():
            try:
                message = message_queue.get_nowait()
                scrolled_text.config(state=tk.NORMAL)
                scrolled_text.insert(tk.END, f"{message}\n")
                # Supprimer les lignes excédentaires
                lines = scrolled_text.get("1.0", tk.END).splitlines()
                if len(lines) > MAX_LINES:
                    scrolled_text.delete("1.0", f"{len(lines) - MAX_LINES}.0")
                scrolled_text.yview(tk.END)  # Scroller automatiquement vers le bas
                scrolled_text.config(state=tk.DISABLED)
            except queue.Empty:
                pass

            root.after(100, update_messages)

        # Démarre l'animation
        update_animation()
        update_messages()

        # Fonction pour afficher la fenêtre depuis la systray
        def afficher_depuis_systray(icon, item):
            
            # Changer l'icône de la fenêtre Tkinter
            chemin_icone = "sail.png"  # Remplacez par le chemin de votre icône
            image_icone = Image.open(chemin_icone)  # Chargez l'image
            icone_tk = ImageTk.PhotoImage(image_icone)  # Convertissez au format Tkinter
            root.iconphoto(True, icone_tk)  # Appliquez l'icône

            root.deiconify()  # Affiche la fenêtre
            root.lift()       # Met la fenêtre au premier plan

        # Fonction pour fermer le programme depuis la systray
        def quitter_depuis_systray(icon, item):
            fermer_programme_proprement(root, icon)

        # Créer une icône pour la systray (option 1)
        def creer_icone():
            # Dessine une icône simple
            image = Image.new("RGB", (64, 64), color=(44, 44, 44))
            draw = ImageDraw.Draw(image)
            draw.ellipse((16, 16, 48, 48), fill="green")
            return image

        # Charger une image PNG pour l'utiliser comme icône (option 2)
        def creer_icone_depuis_image(chemin_image):
            return Image.open(chemin_image)

        # Chemin vers le fichier image
        chemin_image = "sail.png"   

        # Cacher la fenêtre par défaut au démarrage
        root.withdraw()
        
        # Créer et démarrer l'icône de la systray
        icon = Icon(
            "SAILS ADRENA", 
            creer_icone_depuis_image(chemin_image), 
            title="SAILS ADRENA",  # Ceci ajoute un tooltip
            menu=Menu(
                MenuItem("Afficher", afficher_depuis_systray),
                MenuItem("Quitter SAILS ADRENA", quitter_depuis_systray)
             )
        )
        thread_systray = threading.Thread(target=icon.run, daemon=True)
        thread_systray.start()

        # Lancement de l'application
        root.mainloop()

    # Lancer la fenêtre tkinter dans un thread séparé
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def envoyer_signal(signal):
    """Ajoute un signal à la file pour déclencher une animation."""
    signal_queue.put(signal)

def envoyer_message(message):
    """Ajoute un message à la file pour l'afficher dans la zone de texte."""
    message_queue.put(message)