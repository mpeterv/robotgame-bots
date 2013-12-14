# BeatsTapion by Classhamster
# http://robotgame.net/viewrobot/7427

import rg
import euclid as eu
import random
class Robot:
    def act(self, game):
        hp = 51
        attack = False
        active_team = {}
        active_enemy = {}
        enemy_distance = {}
        active_bots = {}
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                active_enemy[loc] = bot                
                enemy_distance[loc] = 0
            else:
                active_team[loc] = bot
        for loc, bot in game.get('robots').items():
            active_bots[loc] = bot
        if self.hp <= 20:
            return flee(self, active_enemy, active_team, game)
        if 'spawn' in rg.loc_types(self.location):
            if game['turn'] %10 == 0: #spawn about to happen, gtfo
                return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    #print("ATTACK")
                    attack = True
                    if bot.hp < hp:
                        hp = bot.hp                        
                        attackloc = bot.location                    
                moveto = bot.location
        if attack:
            return['attack', attackloc]
        if len(check_adjacent_enemy(self, active_enemy, rg.toward(self.location, moveto)))>1:
            return ['attack', rg.toward(self.location, moveto)]
        if rg.toward(self.location, moveto) in active_team:
            return ['guard']
        return ['move', rg.toward(self.location, moveto)]

def check_adjacent_enemy(self, active_enemy, loc):
    direction = {"up":(0,-1), "down":(0,1),"left":(-1,0),"right":(1,0)}
    x, y = loc
    list_of_locs = []
    for d in direction:
        dx, dy = direction[d]
        if (x+dx,y+dy) in active_enemy:
            list_of_locs.append((x+dx, y+dy))
    return list_of_locs
def check_diag_enemy(self, active_enemy, loc):
    direction = {"up":(-1,-1), "down":(1,1),"left":(-1,1),"right":(1,-1)}
    x, y = loc
    list_of_locs = []
    for d in direction:
        dx, dy = direction[d]
        if (x+dx,y+dy) in active_enemy:
            list_of_locs.append((x+dx, y+dy))
    return list_of_locs
def check_adjacent(self, loc):
    direction = {"up":(0,-1), "down":(0,1),"left":(-1,0),"right":(1,0)}
    x, y = loc
    list_of_locs = []
    for d in direction:
        dx, dy = direction[d]        
        list_of_locs.append((x+dx, y+dy))
    return list_of_locs
def check_diag(self, loc):
    direction = {"up":(-1,-1), "down":(1,1),"left":(-1,1),"right":(1,-1)}
    x, y = loc
    list_of_locs = []
    for d in direction:
        dx, dy = direction[d]        
        list_of_locs.append((x+dx, y+dy))
    return list_of_locs
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def getOp(a,b):
    temp = sub(a, b)
    temp = add(temp, a)
    return temp
def flee(self, active_enemy, active_team, game):    
    directions = ((1, 0), (0, -1), (-1, 0), (0, 1))
    possible_dests = [tuple(eu.Vector2(*self.location) + eu.Vector2(*d)) for d in directions]
    adj_enemy_hp = 0
    adj_ally_hp = 0
    maybeMove = None    
    if 'spawn' in rg.loc_types(self.location):
        if game['turn'] %10 == 0: #spawn about to happen, gtfo
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]    
    if len(check_adjacent_enemy(self, active_enemy, self.location)) < 1:
        for loc, bot in active_enemy.iteritems():
            if rg.dist(loc, self.location) <= 2.5:                
                return['attack', rg.toward(self.location, loc)]
        return ['guard']
    for dest in possible_dests:      
        if "invalid" in rg.loc_types(dest):
            possible_dests.remove(dest)
        else:
            for loc, bot in game.get("robots").items():
                if bot.player_id == self.player_id:
                        adj_ally_hp += max(bot.hp, 15)
                else:
                    adj_enemy_hp += max(bot.hp, 15)
                if dest == loc:
                    possible_dests.remove(dest)
    if not possible_dests:
        if self.hp < (10*len(check_adjacent_enemy(self, active_enemy, self.location))) and len(check_adjacent_enemy(self, active_enemy, self.location))>1:
            return ["suicide"]
        else:
            return ["guard"]    
    else:
        moveSpaces = getOp(self.location, dest)
##        if len(check_diag_enemy(self, active_enemy, moveSpaces)) >=1 and len(check_adjacent_enemy(self, active_enemy, moveSpaces)) < 1:
##            print("guarding")
##            return ['guard']
        if len(possible_dests) > 1:
            for d in possible_dests:
                for adj in check_adjacent(self, d):
                    if adj in game["robots"].keys():
                        bot = game["robots"][adj]
                        if bot.player_id != self.player_id:
                            maybeMove = d
                        else:
                            maybeMove = d
                for diag in check_diag(self, d):
                    if diag in game["robots"].keys():
                        bot = game["robots"][diag]
                        if bot.player_id != self.player_id:
                            return['move', d]
                        else:
                            return['move', d]
                if "invalid" in rg.loc_types(d): #This option isnt even possible
                        continue
                if "spawn" in rg.loc_types(d):
                    if game['turn'] %10 == 0: #spawn about to happen, gtfo
                        return ['move', getOp(self.location, d)]
                
                #print("Moving to less desireable spot")
                return['move', maybeMove]
                
        else:            
            return ['move', dest]
