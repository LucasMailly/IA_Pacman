# -*- coding: utf-8 -*-

import pygame as py
import os
import random
import neat
import pickle
from math import sqrt
py.font.init()

#-------------------------------------------------------------Variables-------------------------------------------------------------#


FONT = py.font.SysFont("comicsans", 35)

FRAMERATE = 200

ANIMATION_TIME_CHANGE = 15 #La bouche se ferme ou s'ouvre tout les 15 tours de boucle

last_checkpoint = 0
population_path = "neat-checkpoint-" + str(last_checkpoint)
NUM_GEN = -1
NB_GEN_TRAINING = 25

POPULATION_VISIBLE = True

#Amélioration possible: on charge le meilleur génome enregistré s'il existe, pour le faire jouer seul
'''PATH_BEST_PCM = "best_pcm_0"
BEST_PCM = None
if (PATH_BEST_PCM != None and PATH_BEST_PCM != "" and os.path.exists(PATH_BEST_PCM)):
    fileObject = open(PATH_BEST_PCM,'rb')  
    BEST_PCM = pickle.load(fileObject) '''

#-------------------Images--------------------------------#

SPRITES_PACMAN = [ [] for _ in range(4)] #4 directions différentes de 2 sprites chacuns (4*2 = 8)
SPRITES_GHOST = [ [[] for _ in range(4)] for _ in range(4) ] #4 couleurs différentes avec chacuns 4 directions différentes de 2 sprites chacuns (4*4*2 = 32)
GHOST_FUITE_IMGS = []

# GHOST_IMGS [couleur] [direction] [sprite]
# couleur : 0 = rouge
#           1 = bleu
#           2 = rose
#           3 = orange

ordre_direction = ["gauche", "haut", "droite", "bas"] #notre programme utilise cette ordre pour choisir le bonne direction dans "SPRITES_PACMAN" et "SPRITES_GHOST"
ordre_couleur = ["rouge", "bleu", "rose", "orange"] #notre programme utilise cette ordre pour choisir le bonne couleur du fantome dans "SPRITES_GHOST"

for file in os.listdir("imgs"): #on parcourt tous les fichiers et dossiers du dossier "imgs"
    
    if file == "Pacman":  # Pour le dossier "Pacman":
        
        path = "imgs/Pacman/"
        for image in os.listdir(path): #pour chaque image on l'insère dans le bon index dans le tableau "SPRITES_PACMAN"
            image = image.split(" ")
            for idx, direction in enumerate(ordre_direction):   #enumerate() permet de connaitre l'index de l'élément du tableau 
                                                                #que l'on parcourt (il est stocké dans la variable "idx" dans notre cas)
                if image[0] == direction:
                    SPRITES_PACMAN[idx].append( py.image.load(path + " ".join(image)) )
                    
    if file == "Fantomes":
        
        path = "imgs/Fantomes/"
        for file_couleur in os.listdir(path): #pour chaque image on l'insère dans le bon index de direction et de couleur dans "GHOST_IMGS"
            for idx_couleur, couleur in enumerate(ordre_couleur):
                if couleur == file_couleur:
                    
                    path = "imgs/Fantomes/" + file_couleur + "/"
                    for image in os.listdir(path): 
                        image = image.split(" ")
                        for idx_direction, direction in enumerate(ordre_direction):

                            if image[0] == direction:
                                SPRITES_GHOST[idx_couleur][idx_direction].append( py.image.load(path + " ".join(image)) )
                                
    if file == "Fantome_fuite":
        for img in range(1,3):
            GHOST_FUITE_IMGS.append(py.image.load(f"imgs/{file}/{img}.png"))


BG_IMG = py.image.load("imgs/bg.png")

#------------------Environnement-----------------------#


HAUTEUR = 725 #Hauteur de la fenêtre pygame
LARGEUR = 588 

NB_CASES_X = 28 #Nombre de colonnes de cases en abscisse définissant le BG
NB_CASES_Y = 31 #Nombre de lignes de cases en ordonnée définissant le BG

L_CASES_X = BG_IMG.get_width() / NB_CASES_X  #Longueur du côté d'une case en x
L_CASES_Y = BG_IMG.get_height() / NB_CASES_Y 

CENTRE_CASES_X = round(L_CASES_X / 2) #Centre du côté d'une case en x
CENTRE_CASES_Y = round(L_CASES_Y / 2)

GRILLE = False #Afficher la grille de cases (True), ou pas (False)

TOTAL_PIECES = 244


#---------------------------------------------------------Execute------------------------------------------------------------------#

"""
La classe Pacman regroupe toutes les fonctions qui concernent une entité à laquelle on attribue la classe en question, donc un pacman.
"""
class Pacman:
    
    """
    Variables qui sont données au départ aux fonctions de la classe Pacman.
    """
    def __init__(self):
        self.position_x = int(14 * L_CASES_X)
        self.position_y = int(24 * L_CASES_Y - CENTRE_CASES_Y)
        
        self.x = 14
        self.y = 24
        
        self.mouv_x = 0
        self.mouv_y = 0
        
        self.direction_sprite = 0 # 0 = gauche, 1 = haut, 2 = droite, 3 = bas
        self.animation_sprite = 1 # 0 = bouche ouverte, 1 = bouche fermée 
        self.start_animation = False
        self.compteur_animation = 0
        
        self.manger = False
    
        self.compteur_pieces = 0
        self.compteur_pouvoir = 0
        self.score = 0
        self.niveau = 1
        
        self.passage_droite = False
        self.passage_gauche = False

    """
    Cette fonction permet de reset le jeu :
    Si le compteur de pièces qu'a mangé le pac-man a atteint le total de pièces dans le jeu ...
    Alors toutes les variables dont le compteur de pièces en lui-même reprennent leur valeur initiale, sauf le score du pacman et le
    numéro du niveau qui augmente de 1 ...
    Et la fonction prend la valeur True ; cela permettra dans le main() de changer la MAP qui permet d'afficher les pièces en la remettant
    à sa forme originelle à partir d'une copie d'une sauvegarde, et cela permettra de mettre à 0 la valeur de la direction qu'on veut 
    donner au pac-man pour ne pas qu'il recommence à bouger.
    """
    def fin_jeu(self):
        if self.compteur_pieces == TOTAL_PIECES:
            self.position_x = int(14 * L_CASES_X)
            self.position_y = int(24 * L_CASES_Y - CENTRE_CASES_Y)
            
            self.mouv_x = 0
            self.mouv_y = 0
            
            self.direction_sprite = 0
            self.animation_sprite = 1
            self.start_animation = False
            self.compteur_animation = 0
        
            self.compteur_pieces = 0
            self.compteur_pouvoir = 0
            self.niveau = self.niveau + 1
            
            self.manger = False
            
            self.passage_droite = False
            self.passage_gauche = False
            
            return True
    
    """
    Cette fonction permet de déterminer la case dans laquelle le pac-man se trouve et de changer le mouvement du pac-man en fonction d'une
    direction qu'on veut lui donner :
    Si dans la direction qu'on veut donner au pacman la case en face n'est pas un mur ...
    Alors le mouvement prend cette direction.
    """
    def change_direction(self, MAP, change_direction_x, change_direction_y):
        self.x = int(self.position_x // L_CASES_X) #Colonne cases pacman
        self.y = int(self.position_y // L_CASES_Y) #Ligne cases pacman
        
        if MAP[self.y+change_direction_y][self.x+change_direction_x] != "#":
            if self.position_y%L_CASES_Y == CENTRE_CASES_Y and change_direction_x != 0:
                self.mouv_x = change_direction_x
            if self.position_x%L_CASES_X == CENTRE_CASES_X and change_direction_y != 0:
                self.mouv_y = change_direction_y 
    
    """
    Cette fonction permet de changer la position du pacman sur le terrain en fonction du mouvement.
    
    Cette fonction permet aussi de déterminer quand le mouvement du pacman doit se stopper :
    Si la case en face du pacman en mouvement est un mur ...
    Alors le mouvement s'arrête et le pac-man a la bouche fermée, et l'animation se stop dans animation().
    
    Cette fonction permet aussi de gérer la position du pac-man quand il passe dans un des deux tunnels présents sur le terrain :
    
    """
    def mouvement(self, MAP):
        self.animation()
        
        if MAP[self.y+self.mouv_y][self.x+self.mouv_x] == "#": 
            if self.position_x%L_CASES_X == CENTRE_CASES_X:
                self.mouv_x = 0
                self.animation_sprite = 1
                
            if self.position_y%L_CASES_Y == CENTRE_CASES_Y:
                self.mouv_y = 0
                self.animation_sprite = 1
                
                
        if self.position_x <= 0: #passage gauche
            self.mouv_y = 0
            self.passage_gauche = True
            if self.position_x == -2*L_CASES_X:
                self.position_x =  30*L_CASES_X
            if self.passage_droite == True:
                self.mouv_x = 1
            else:
                self.mouv_x = -1
            
        elif self.position_x >= BG_IMG.get_width(): #passage droite
            self.mouv_y = 0
            self.passage_droite = True
            if self.position_x == 30*L_CASES_X:
                self.position_x = -2*L_CASES_X  
            if self.passage_gauche == True:
                self.mouv_x = -1
            else:
                self.mouv_x = 1
        
        else:
            self.passage_gauche = False
            self.passage_droite = False
                
        self.position_x = self.position_x + self.mouv_x
        self.position_y = self.position_y + self.mouv_y
    
    """
    Cette fonction permet de gérer les variables pour changer le sprite du pac-man :
    
    Lorsque l'animation commence, tout les tours de fonction, la variable compteur_animation prend +1.
    Lorsque le compteur atteint 10 alors la variable qui change le statut du pac-man (bouche fermée/ouverte) change et le compteur est
    remis à 0.
    
    En fonction du mouvement, et donc de la direction dans laquelle le pac-man se déplace, la direction du sprite change.
    Dès lors qu'il y a du mouvement l'animation commence, sinon elle s'arrête lorsque le pac-man est fixe.
    """
    def animation(self):
        if self.start_animation == True:
            self.compteur_animation = self.compteur_animation + 1
            if self.compteur_animation == ANIMATION_TIME_CHANGE : #ANIMATION_TIME_CHANGE = 10
                self.animation_sprite = not (self.animation_sprite) 
                self.compteur_animation = 0  
                
        if self.mouv_x == 1:#mouvement vers la droite
            self.direction_sprite = 2 #sprite pacman droite
        if self.mouv_x == -1: # """ gauche
            self.direction_sprite = 0         
        if self.mouv_y == 1: # """ bas
            self.direction_sprite = 3        
        if self.mouv_y == -1: # """ haut
            self.direction_sprite = 1
            
        if self.mouv_x != 0:
            self.start_animation = True
        elif self.mouv_y != 0:
            self.start_animation = True
        else:
            self.start_animation = False
            
    """
    Cette fonction permet d'afficher le sprite du pac-man à partir de sa position, qui est son centre, moins sa hauteur et sa largeur (car
    l'image ne se blit pas à partir du milieu mais à partir du coin haut/droite) mais aussi de la valeur de l'index correspondant à sa 
    direction et à son statut au sein de celle-ci (bouche ouverte/fermée). 
    """
    def draw(self, win):
        self.image_pacman = SPRITES_PACMAN[self.direction_sprite][self.animation_sprite]
        win.blit(py.transform.scale2x(self.image_pacman), (self.position_x - self.image_pacman.get_width(), self.position_y - self.image_pacman.get_height()))
       

    """
    Cette fonction permet au pac-man de manger les pièces qui sont sur la case où il se trouve :
    Si le pac-man se trouve sur une case dont le caractère est celui d'une pièce ...
    Alors on crée à partir de la ligne dans laquelle le pac-man se trouve une liste temporaire qui ne contient que les caractères dans 
    cette ligne, et on remplace dans cette nouvelle ligne le caractère qui correspond à la colonne dans laquelle le pacman se trouve par 
    du vide (un espace). Enfin on remplace la ligne dans MAP par du vide auquel on ajoute la ligne de la liste temporaire, et on augmente 
    de 1 le compteur de pièces ainsi que le score.
    
    [!]
    """
    def eat(self, MAP, fantomes):
        if MAP[self.y][self.x] == "o": 
            self.temp = list(MAP[self.y]) 
            self.temp[self.x] = " " 
            MAP[self.y] = "".join(self.temp)   
            
            self.compteur_pieces = self.compteur_pieces + 1
            self.score = self.score + 1
            self.manger = True
            
        if MAP[self.y][self.x] == "O":
            self.temp = list(MAP[self.y])
            self.temp[self.x] = " "
            MAP[self.y] = "".join(self.temp)
                    
            self.compteur_pieces = self.compteur_pieces + 1
            self.compteur_pouvoir += 1
            self.manger = True
            for f in fantomes:
                    f.fuite = 5*FRAMERATE #5 Secondes de fuites pour les fantomes si le pacman mange une piece blanche

        if MAP[self.y+self.mouv_y][self.x+self.mouv_x] != "o" and MAP[self.y+self.mouv_y][self.x+self.mouv_x] != "O":
            self.manger = False
            
    #fonction qui donne les distances en cases(en prenant en compte les obstacles) depuis le pacman jusqu'à la pièce la plus proche
    #et jusqu'aux fantômes les plus proches (le nombre de distance pcm-fantome demandés est entré en input de la fonction) ( ~= BFS algorithm)
    #sortie = [dist_pcm-piece, dist_pcm-fantome1, dist_pcm-fantome2]
    def nearest_coin_and_ghost(self, MAP, case_x, case_y, fantomes, nb_fantomes):
        
        fantomes_visited = []
        fantomes_distance = []
        fantomes_fuite = []
        piece_distance = None
        pouvoir_distance = None
        output = []
        path = [(case_x,case_y)]
        visited = []
        distance = 1
        
        #fonction défini sur une ligne qui vérifie si l'index qui sera cherché est bien dans le MAP pour éviter des erreurs
        verif_limite = lambda x, y : (x >= 0 and x < NB_CASES_X and y >= 0 and y < NB_CASES_Y)
        
        while True:
            new_path = []
            for p in path:
                if verif_limite(p[0], p[1]):
                    if MAP[p[1]][p[0]] == "o" and piece_distance == None:
                        piece_distance = distance
                    if MAP[p[1]][p[0]] == "O" and pouvoir_distance == None:
                        pouvoir_distance = distance
                        
                for f in fantomes:
                    if f.x//L_CASES_X == p[0] and f.y//L_CASES_Y == p[1] and not (f in fantomes_visited) and len(fantomes_distance) < nb_fantomes:
                        fantomes_distance.append(1/distance)
                        if f.fuite > 0:
                            fantomes_fuite.append(1)
                        else:
                            fantomes_fuite.append(-1)
                        fantomes_visited.append(f)
                    elif f.start: #si les pacmans sont morts ou si c'est le début du jeu ils sont dans des murs (donc invisible pour l'algorithme)
                        if 14 == p[0] and 11 == p[1] and not (f in fantomes_visited) and len(fantomes_distance) < nb_fantomes: # x=14 et y=11 quand le fantome vient de spawn
                            fantomes_distance.append(1/distance)
                            if f.fuite > 0:
                                fantomes_fuite.append(1)
                            else:
                                fantomes_fuite.append(-1)
                            fantomes_visited.append(f)
                if piece_distance != None and (pouvoir_distance != None or self.compteur_pouvoir == 4) and len(fantomes_distance) == nb_fantomes:
                    output.append(piece_distance)
                    for f in fantomes_distance:
                        output.append(f)
                    for etat_fuite in fantomes_fuite:
                        output.append(etat_fuite)
                    if pouvoir_distance != None:
                        output.append(pouvoir_distance)
                    else:
                        output.append(1)
                    return output
                
                
                for move in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    futur_x = p[0]+move[0]
                    futur_y = p[1]+move[1]
                    if verif_limite(futur_x, futur_y):
                        if MAP[futur_y][futur_x] != "#" and not (futur_x, futur_y) in path and not (futur_x, futur_y) in visited:
                            new_path.append((futur_x, futur_y))
                    elif (futur_x == -1 or futur_x == NB_CASES_X) and futur_y == 14 and not (futur_x, futur_y) in path and not (futur_x, futur_y) in visited:
                        new_path.append((futur_x, futur_y))
                visited.append(p)
            
            distance += 1
            path = new_path.copy()
            
    def get_environnement(self, MAP):
        
        tab = []
        try:
            if self.y-1 >= 0:
                tab.append(MAP[self.y-1][self.x])
            else:
                tab.append(" ")
            if self.y+1 < NB_CASES_Y:
                tab.append(MAP[self.y+1][self.x])
            else:
                tab.append(" ")
            if self.x-1 >= 0:
                tab.append(MAP[self.y][self.x-1])
            else:
                tab.append(" ")
            if self.x+1 <= NB_CASES_X:
                tab.append(MAP[self.y][self.x+1])
            else:
                tab.append(" ")
        except:
            return ["#", "#", " ", " "] #Haut, Bas, Gauche, Droite
        
        return tab
    
    
    
class Fantome:
    IMGS = SPRITES_GHOST
    ANIMATION_TIME = 10
    position_start = [(14,12), (12,15), (14,15), (16,15)]
    
    #donner en argument quelle est le fantome (0 = rouge, 1 = bleu, 2 = rose, 3 = orange)
    def __init__(self, n_fantome, MAP):
        self.x = round(self.position_start[n_fantome][0]*L_CASES_X)
        self.y = round(self.position_start[n_fantome][1]*L_CASES_Y-round((1/2)*L_CASES_Y))
        self.Xdirection = random.choice([-1,1])
        self.Ydirection = 0
        self.img = self.IMGS[n_fantome][0][0] #vers le haut
        self.start = True
        self.compteur_mort = 0
        self.index_F = n_fantome
        self.index_sprite = 0
        self.index_direction = 1
        self.img_count = 0
        self.MAP = MAP
        self.new_case = False
        self.fuite = 0
        self.last_case_pcm = [0, 0] #Y, X
        self.compteur_tour = 0
        
    def draw(self, win):
        self.img_count += 1
        
        if self.img_count < self.ANIMATION_TIME:
            self.index_sprite = 0
        elif self.img_count < self.ANIMATION_TIME*2:
            self.index_sprite = 1
        else:
            self.index_sprite = 0
            self.img_count = 0
        
        if self.fuite <= 0:
            self.img = py.transform.scale2x(self.IMGS[self.index_F][self.index_direction][self.index_sprite])
        else:
            self.img = py.transform.scale2x(GHOST_FUITE_IMGS[self.index_sprite])
        
        win.blit(self.img, (self.x  - (1/2)*self.img.get_width(), self.y - (1/2)*self.img.get_height()))
        
    def die(self):
        self.x = round(14*L_CASES_X)
        self.y = round(12*L_CASES_Y-round((1/2)*L_CASES_Y))
        self.Xdirection = random.choice([-1,1])
        self.Ydirection = 0
        self.start = True
        self.compteur_mort = 0
        self.index_sprite = 0
        self.index_direction = 1
        self.img_count = 0
        self.new_case = False
        self.fuite = 0
        self.last_case_pcm = [0, 0]
        self.compteur_tour = 0

    
    def move(self, pacmans):
        self.fuite -= 1
        self.new_case = False 
        if self.compteur_tour == 2:
            self.compteur_tour = 0
        else:
            self.compteur_tour += 1
            verif_limite = lambda x, y : (x >= 0 and x < NB_CASES_X and y >= 0 and y < NB_CASES_Y)
            
            # si c'est le debut de la partie le fantome va d'abbord se déplacer à son point de départ
            if self.start:
                x_objectif = 14*L_CASES_X
                y_objectif = round(11.5*L_CASES_Y)
                
                if self.x != x_objectif:
                    if self.x - x_objectif < 0:
                        self.x += 1
                    else:
                        self.x -= 1
                elif self.y != y_objectif:
                    self.y -= 1
                else:
                    self.start = False
                    
            elif self.compteur_mort > 0: #compteur avant respawn
                self.compteur_mort -= 1
            
            else:
                fantome_case_x = int(self.x//L_CASES_X)
                fantome_case_y = int(self.y//L_CASES_Y)
                
                pcm_visible = [] #( pcm , (X,Y))
                for pcm in pacmans:
                    if pcm.y == fantome_case_y and pcm.x >= 0 and pcm.x < NB_CASES_X:
                        direction = 1
                        if fantome_case_x - pcm.x > 0:
                            direction = -1
                        mur = False
                        for i in range(1, abs(fantome_case_x-pcm.x) + 1):
                            if verif_limite(fantome_case_x+i*direction, fantome_case_y):
                                if self.MAP[fantome_case_y][fantome_case_x+i*direction] == "#":
                                    mur = True
                        if not(mur):
                            pcm_visible.append((pcm, (direction, 0) ))
                    elif pcm.x == fantome_case_x:
                        direction = 1
                        if fantome_case_y - pcm.y > 0:
                            direction = -1
                        mur = False
                        for i in range(1, abs(fantome_case_y-pcm.y) + 1):
                            if verif_limite(fantome_case_x+i*direction, fantome_case_y):
                                if self.MAP[fantome_case_y+i*direction][fantome_case_x] == "#":
                                    mur = True
                        if not(mur):
                            pcm_visible.append((pcm, (0, direction) ))
                
                direction_pcm = [0, 0]
                min_distance = HAUTEUR
                for pcm in pcm_visible:
                    distance = sqrt( (pcm[0].x-self.x)**2 + (pcm[0].y-self.y)**2 )
                    if distance < min_distance:
                        min_distance = distance
                        direction_pcm[0] = pcm[1][0]
                        direction_pcm[1] = pcm[1][1]
                        
                
                random_move = True
                if direction_pcm != [0, 0]: #si le fantome voit un pacman il le chasse ou il le fuit selon son état
                    if self.x % L_CASES_X == round(L_CASES_X/2) and self.y % L_CASES_Y == round(L_CASES_Y/2):
                        if self.fuite > 0: #Si le fantome est pourchassé par le pacman on le fait fuire
                            self.Xdirection = -direction_pcm[0]
                            self.Ydirection = -direction_pcm[1]
                        else:
                            self.Xdirection = direction_pcm[0]
                            self.Ydirection = direction_pcm[1]
                    
                    if self.MAP[int(self.y//L_CASES_Y)+self.Ydirection][int(self.x//L_CASES_X)+self.Xdirection] != '#':
                        self.y += self.Ydirection
                        self.x += self.Xdirection
                        random_move = False
                    
                    if fantome_case_x != self.x//L_CASES_X or fantome_case_y != self.y//L_CASES_Y:
                        self.new_case = True 
                                
                if random_move:
                    futur_y = (self.y//L_CASES_Y)+self.Ydirection
                    futur_x = (self.x//L_CASES_X)+self.Xdirection
                    
                    # on vérifie que la case du fantome est bien compris dans la MAP pour éviter une erreur à cause des tuyaux
                    if (fantome_case_x > 0 and fantome_case_x < NB_CASES_X - 1):
                        
                        if (self.x%L_CASES_X == round(L_CASES_X/2) and self.y%L_CASES_Y == round(L_CASES_Y/2)):
                            
                            move_possible = [] #[haut, bas, gauche, droite]
                            for y in [-1, 1]:
                                if y == -self.Ydirection:
                                    move_possible.append("#")
                                else:
                                    move_possible.append(self.MAP[int(self.y//L_CASES_Y)+y][int(self.x//L_CASES_X)] )
                                    
                            for x in [-1, 1]:
                                if x == -self.Xdirection:
                                    move_possible.append("#")
                                else:
                                    move_possible.append(self.MAP[int(self.y//L_CASES_Y)][int(self.x//L_CASES_X)+x])
                            
                            direction_rand = 0
                            direction_possible = False
                            direction = [(-1,0), (1,0), (0,-1), (0,1)]
                            while not(direction_possible):
                                direction_rand = random.randint(0, 3)
                                if move_possible[direction_rand] != "#":
                                    self.Ydirection = direction[direction_rand][0]
                                    self.Xdirection = direction[direction_rand][1]
                                    direction_possible = True
                        
                        futur_y = int(self.y//L_CASES_Y)+self.Ydirection
                        futur_x = int(self.x//L_CASES_X)+self.Xdirection
                        
                        # on vérifie que futurX est bien compris dans la MAP pour éviter une erreur à cause des tuyaux
                        if (futur_x < NB_CASES_X and futur_x >= 0):
                            
                            if self.MAP[futur_y][futur_x] == "#": 
                                if self.x%L_CASES_X == round(L_CASES_Y/2):
                                    self.Xdirection = 0
                                
                                if self.y%L_CASES_Y == round(L_CASES_X/2):
                                    self.Ydirection = 0
                            
                            self.x += self.Xdirection
                            self.y += self.Ydirection
                            
                            if fantome_case_x != self.x//L_CASES_X or fantome_case_y != self.y//L_CASES_Y:
                                self.new_case = True
                        
                    #si il n'est pas compris dans la MAP on effectue uniquement que le mouvement X
                    #et on fait la téléportation à l'autre bout du tuyau
                    else:
                        self.x += self.Xdirection
                        if (self.x+self.img.get_width() < 0):
                            self.x = LARGEUR+round(L_CASES_Y/1.75)
                        elif(self.x-self.img.get_width() > LARGEUR):
                            self.x = -round(L_CASES_Y/1.75)
                    
    def eat(self, pacman):
        if self.compteur_mort == 0:
            case_x = self.x // L_CASES_X
            case_y = self.y // L_CASES_Y
            pcm_case_x = pacman.x
            pcm_case_y = pacman.y
            
            if pcm_case_x == case_x and pcm_case_y == case_y:
                if self.fuite <= 0: #Si le fantôme ne fuit pas
                    return True
                else:
                    pacman.score += 10
                    self.die()
                    self.compteur_mort = 3*FRAMERATE
            return False
    
  
def draw_window(win, MAPS, pacmans, fantomes, best_pcm):   
    py.draw.rect(win,(0,0,0), (0,0,LARGEUR, HAUTEUR))
    
    win.blit(BG_IMG, (0,0))
    
    if POPULATION_VISIBLE:
        for pcm in pacmans:
            pcm.draw(win)
    else:
        pacmans[best_pcm].draw(win)
    
    for x in range (NB_CASES_X): #Pièces
        for y in range (NB_CASES_Y):
            if MAPS[best_pcm][y][x] == "o":
                py.draw.circle(win, (255, 240, 0), (round((x+1)*L_CASES_X-CENTRE_CASES_X), round((y+1)*L_CASES_Y-CENTRE_CASES_Y)), round(L_CASES_Y/4))
            if MAPS[best_pcm][y][x] == "O":
                py.draw.circle(win, (245, 245, 245), (round((x+1)*L_CASES_X-CENTRE_CASES_X), round((y+1)*L_CASES_Y-CENTRE_CASES_Y)), round(L_CASES_Y/2))
    
    text_score = FONT.render("score : " + str(pacmans[best_pcm].score), 1, (255,255,255))
    text_niveau = FONT.render("niveau : " + str(pacmans[best_pcm].niveau), 1, (255,255,255))
    text_gen = FONT.render("Gen : " + str(NUM_GEN), 1, (255,255,255))
    win.blit(text_score, (0, BG_IMG.get_height()+5))
    win.blit(text_niveau, (0, BG_IMG.get_height()+30))
    win.blit(text_gen, (0, BG_IMG.get_height()+55))
    
    for f in fantomes:
        f.draw(win)
    
    if GRILLE == True : #Grille rouge      
        for x in range (NB_CASES_X):
            py.draw.line(win, (255,0,0), (x*L_CASES_X,0), (x*L_CASES_X, BG_IMG.get_height()), 1)
        for y in range (NB_CASES_Y):
            py.draw.line(win, (255,0,0), (0, y*L_CASES_Y), (BG_IMG.get_width(), y*L_CASES_Y), 1)  
    
    py.display.update()
    
"""
Fonction principale du programme.

Création de la fenêtre utile pour draw_window().
Création d'une horloge.

Création d'un tableau MAP et d'une sauvegarde.
Ouverture d'un fichier texte "map".
Pour chaque ligne dans le fichier, la ligne est placé dans une variable l sans le caractère "espace" ("\n") et avec l chaque ligne est 
placée dans les tableaux MAP et sa sauvegarde. MAP est donc un tableau de lignes qui elles-mêmes sont des tableaux de caractères.

Création d'un pac-man et de 5 fantômes distinct avec un chiffe différent donné en paramètre pour chacun.

BOUCLE INFINIE :
*La rapidité de la boucle est définie à 120 tics/s grâce à l'horloge précédemment crée.
*On assigne la position du cureuseur de la souris à une variable. 

*Fonctions :
Les fonctions sont appelées en continu.

Si la condition dans fin_jeu() venait à être vérifié alors elle renvoit True, ce qui vérifie la condition du main et donc ...
En plus du reset des variables de la classe pac-man dans cette fonction, la direction que l'on veut donner au pac-man devient nulle afin 
que le mouvement nul ne reprenne pas une valeur qui le change lors de ce reset ...
Et la MAP redevient celle qu'elle était au début grâce à une copie de sa sauvegarde, pour ne pas modifier la sauvegarde en elle-même à
cause de la propriété particulière des tableaux.
"""
def main(genomes, config):
    global NUM_GEN
    NUM_GEN += 1 
    
    win = py.display.set_mode((LARGEUR, HAUTEUR)) 
    clock = py.time.Clock() 
    
    save_MAP = []
    fichier = open("map.txt", "r")  
    for ligne in fichier: 
        l = ligne.replace("\n","") #On met dans la variable l la ligne sans le caractère "\n" = "saut de ligne"
        save_MAP.append(l) #Aussi dans temp_MAP
        
    MAPS = []
    nets = []
    ge = []
    pacmans = []
    fantomes = [Fantome(x, save_MAP) for x in range(4)]
    directions = [] #X, Y
    
    for x, g in genomes:
        MAP = save_MAP.copy()
        MAPS.append(MAP)
        
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        pacmans.append(Pacman()) #création du pac-man
        directions.append([0,0])
        g.fitness = 0
        ge.append(g)
    
    
    run = True
    while run:
        clock.tick(FRAMERATE)
        
        for event in py.event.get():
            if event.type == py.QUIT:
                 py.quit()
                 quit()  
        
        score_pcms = []
        for pcm in pacmans:
            score_pcms.append(pcm.score)
        best_pcm = score_pcms.index(max(score_pcms))
        
        
        draw_window(win, MAPS, pacmans, fantomes, best_pcm)
        
        new_case = False
        for f in fantomes:
            f.move(pacmans)
            if f.new_case:
                new_case = True
        
        for i, pcm in enumerate(pacmans):
            pcm.change_direction(MAPS[i], directions[i][0], directions[i][1])
            pcm.mouvement(MAPS[i])
            pcm.eat(MAPS[i], fantomes)
            ge[i].fitness = pcm.score
            
            if pcm.fin_jeu():
                for p, pcm in enumerate(pacmans):
                    MAPS[p] = save_MAP.copy()
                    pacmans[p].restart()
                fantomes = [Fantome(x, save_MAP) for x in range(4)]
            
            verif_limite = lambda x, y : (x >= 0 and x < NB_CASES_X and y >= 0 and y < NB_CASES_Y)
            
            if new_case and verif_limite(pcm.x, pcm.y):
                outputs = [] # [Haut, Bas, Gauche, Droite]
                mouvement = [(0, -1), (0, 1), (-1, 0), (1, 0)] # [Haut, Bas, Gauche, Droite] (X, Y)
    
                for n, case in enumerate(pcm.get_environnement(MAPS[i])):
                    if case == "#":
                        outputs.append(-1.0)
                    else:
                        futur_case_x, futur_case_y = pcm.x+mouvement[n][0], pcm.y+mouvement[n][1]
                        inputs = []
                        for ip in pcm.nearest_coin_and_ghost(MAPS[i],futur_case_x, futur_case_y, fantomes, 2):
                            inputs.append(ip)
                        output = (nets[i].activate(inputs))
                        outputs.append(output[0])
                
                idx = outputs.index(max(outputs)) #on récupère l'index de la plus grande valeur de "outputs" (direction la mieux évaluée par le réseau de neurones)
                directions[i][0] = mouvement[idx][0]
                directions[i][1] = mouvement[idx][1]
            
            for fantome in fantomes:
                if fantome.eat(pcm) or NUM_GEN == 0:
                    ge.pop(i)
                    nets.pop(i)
                    directions.pop(i)
                    pacmans.pop(i)
                    MAPS.pop(i)
                    break #on stop la boucle "for" içi car si un autre fantôme se trouvait
                          #sur la même case à ce moment on aurait retirer un index du tableau qui n'existe plus
            
            if len(pacmans) == 0:
                run = False




#--------------------------------------------------------------------------NEAT--------------------------------------------------------------------------


def stop(best):
    #on créer un fichier qui n'existe pas encore
    n = 0
    save = False
    path = None
    while not(save):
        test_path = "best_pcm_" + str(NUM_GEN)
        if not(os.path.exists(test_path)):
            save = True
            path = test_path
        n += 1
    
    #on ouvre le fichier en écriture et on enregistre le meilleur genome dedans
    file = open(path,'wb')
    pickle.dump(best, file) 
    file.close()
    
    #on ferme le programme
    py.quit()
    quit()

def run(config_path, local_dir):
    global last_checkpoint
    
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    p = neat.Population(config)
    if (os.path.exists(population_path)):
        p = neat.checkpoint.Checkpointer.restore_checkpoint(population_path)
        p.config = config
    else:
        last_checkpoint = 0
    
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    #on enregistre le meilleur pcm dans un fichier de notre dossier
    best_pcm = p.run(main, NB_GEN_TRAINING+1)
    neat.checkpoint.Checkpointer.save_checkpoint(neat.Checkpointer(50, None), config, p.population, p.species, NB_GEN_TRAINING+last_checkpoint)
    stop(best_pcm)


"""Première action du programme, appel de la fonction run qui lancera la fonction main NB_GEN_TRAINING fois pour une population de x individus"""
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, "config_feedforward.txt")
run(config_path, local_dir)