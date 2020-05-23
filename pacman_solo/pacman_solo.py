# -*- coding: utf-8 -*-

import pygame as py
import os
import random
from pygame.locals import *
from math import sqrt
py.font.init()
py.mixer.init()

#-------------------------------------------------------------Variables-------------------------------------------------------------#


FONT = py.font.SysFont("comicsans", 35)
FRAMERATE = 120

son_actif = True
BRUIT_PIECES = py.mixer.Sound("son/pacman_chomp.wav")

ANIMATION_TIME_CHANGE = 15 #La bouche se ferme ou s'ouvre tout les 15 tours de boucle


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

IMG_BOUTON_MUTE = py.image.load("imgs/bouton_mute.png") 
IMG_BOUTON_SON = py.image.load("imgs/bouton_son.png")

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
        self.point_fantôme = 0
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
            self.point_fantôme = 0
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
    def draw(self, win, MAP):
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
    def eat(self, MAP, change_direction_x, change_direction_y, fantomes):
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
            self.score = self.score + 1
            self.manger = True
            for f in fantomes:
                    f.fuite = 5*FRAMERATE #5 Secondes de fuites pour les fantomes si le pacman mange une piece blanche

        if MAP[self.y+self.mouv_y][self.x+self.mouv_x] != "o" and MAP[self.y+self.mouv_y][self.x+self.mouv_x] != "O":
            self.manger = False

        if self.manger == True:
            if son_actif == True:
                py.mixer.unpause()
                py.mixer.Sound.play(BRUIT_PIECES)
            else:   
                py.mixer.stop()
        else:
            py.mixer.pause()

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
    
"""
"""   
def draw_window(win, MAP, pacman, fantomes):   
    py.draw.rect(win,(0,0,0), (0,0,LARGEUR, HAUTEUR))
    
    win.blit(BG_IMG, (0,0))
    win.blit(IMG_BOUTON_SON, (0, HAUTEUR - IMG_BOUTON_SON.get_height()))
    win.blit(IMG_BOUTON_MUTE, (LARGEUR - IMG_BOUTON_MUTE.get_width(), HAUTEUR - IMG_BOUTON_MUTE.get_height()))
    
    pacman.draw(win, MAP)
    
    for x in range (NB_CASES_X): #Pièces
        for y in range (NB_CASES_Y):
            if MAP[y][x] == "o":
                py.draw.circle(win, (255, 240, 0), (round((x+1)*L_CASES_X-CENTRE_CASES_X), round((y+1)*L_CASES_Y-CENTRE_CASES_Y)), round(L_CASES_Y/4))
            if MAP[y][x] == "O":
                py.draw.circle(win, (245, 245, 245), (round((x+1)*L_CASES_X-CENTRE_CASES_X), round((y+1)*L_CASES_Y-CENTRE_CASES_Y)), round(L_CASES_Y/2))
    
    text_score = FONT.render("score : " + str(pacman.score), 1, (255,255,255))
    text_niveau = FONT.render("niveau : " + str(pacman.niveau), 1, (255,255,255))
    win.blit(text_score, (0, BG_IMG.get_height()+5))
    win.blit(text_niveau, (0, BG_IMG.get_height()+30))
    
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
    
*Conditions des événements :
Si une flèche est appuyée alors on change la direction qu'on veut donner au pac-man, qui permettra sous condition de changer le mouvement.
Si l'on clique à la position où se trouve le bouton pour rendre le son actif alors 
Si la croix de la fenêtre est appuyée alors le programme s'arrête et la fenêtre se ferme avec succès.

*Fonctions :
Les fonctions sont appelées en continu.

Si la condition dans fin_jeu() venait à être vérifié alors elle renvoit True, ce qui vérifie la condition du main et donc ...
En plus du reset des variables de la classe pac-man dans cette fonction, la direction que l'on veut donner au pac-man devient nulle afin 
que le mouvement nul ne reprenne pas une valeur qui le change lors de ce reset ...
Et la MAP redevient celle qu'elle était au début grâce à une copie de sa sauvegarde, pour ne pas modifier la sauvegarde en elle-même à
cause de la propriété particulière des tableaux.
"""
def main():
    global son_actif

    win = py.display.set_mode((LARGEUR, HAUTEUR)) 
    clock = py.time.Clock() 
    
    MAP = []
    save_MAP = []
    fichier = open("map.txt", "r")  
    for ligne in fichier: 
        l = ligne.replace("\n","") #On met dans la variable l la ligne sans le caractère "\n" = "saut de ligne"
        MAP.append(l) #On met l dans le tableau MAP
        save_MAP.append(l) #Aussi dans temp_MAP
    
    pacmans = [Pacman()]
    fantomes = [Fantome(x, save_MAP) for x in range(4)]
    
    change_direction_x = 0
    change_direction_y = 0
    
    run = True
    while run:
        clock.tick(FRAMERATE)
        pos_mouse = py.mouse.get_pos()
        
        for event in py.event.get():
            if event.type == KEYDOWN:
                
                if event.key == K_LEFT:
                    change_direction_x = -1 
                    change_direction_y = 0 
            
                if event.key == K_UP:
                    change_direction_x = 0
                    change_direction_y = -1
                
                if event.key == K_RIGHT:
                    change_direction_x = 1
                    change_direction_y = 0
                
                if event.key == K_DOWN:                  
                    change_direction_x = 0                         
                    change_direction_y = 1
            
            if event.type == py.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if pos_mouse > (0, HAUTEUR - IMG_BOUTON_SON.get_height()) and pos_mouse < (IMG_BOUTON_SON.get_width(), HAUTEUR):
                        son_actif = True
                    if pos_mouse > (LARGEUR - IMG_BOUTON_MUTE.get_width(), HAUTEUR - IMG_BOUTON_MUTE.get_height()) and pos_mouse < (LARGEUR, HAUTEUR):
                        son_actif = False
                        
            if event.type == QUIT:
                 py.quit()
                 quit()  
        
        if pacmans[0].fin_jeu():
            change_direction_x = 0
            change_direction_y = 0
            fantomes = [Fantome(x, save_MAP) for x in range(4)]
            MAP = save_MAP.copy()
        
        pacmans[0].change_direction(MAP, change_direction_x, change_direction_y)
        pacmans[0].mouvement(MAP)
        pacmans[0].animation()
        for f in fantomes:
            if f.eat(pacmans[0]):
                print(f"Score: {pacmans[0].score}")
                change_direction_x = 0
                change_direction_y = 0
                MAP = save_MAP.copy()
                pacmans = [Pacman()]
                fantomes = [Fantome(x, save_MAP) for x in range(4)]
                break
            f.move(pacmans)
        
            
        draw_window(win, MAP, pacmans[0], fantomes)
        pacmans[0].eat(MAP, change_direction_x, change_direction_y, fantomes)

"""Première action du programme, appel de la fonction main"""
main()