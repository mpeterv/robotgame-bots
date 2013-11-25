# stupid 2.7.1 by peterm

import random
import math
import rg

def around(l):
    return rg.locs_around(l)

def around2(l):
    return [(l[0]+2, l[1]), (l[0]+1, l[1]+1), (l[0], l[1]+2), (l[0]-1, l[1]+1), 
    (l[0]-2, l[1]), (l[0]-1, l[1]-1), (l[0], l[1]-2), (l[0]+1, l[1]-1)]
    
def diag(l1, l2):
    if rg.wdist(l1, l2) == 2:
        if abs(l1[0] - l2[0]) == 1:
            return True
    return False
    
def infront(l1, l2):
    if rg.wdist(l1, l2) == 2:
        if diag(l1, l2):
            return False
        else:
            return True
    return False
    
def mid(l1, l2):
    return (int((l1[0]+l2[0]) / 2), int((l1[1]+l2[1]) / 2))
    
def sign(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    else:
        return -1

class Robot:
     def act(self, game):
        robots = game['robots']
        
        ##print self.location, "starts thinking"
        
        def isenemy(l):
            if robots.get(l) != None:
                if robots[l]['player_id'] != self.player_id:
                    return True
            return False
            
        def isteammate(l):
            if robots.get(l) != None:
                if robots[l]['player_id'] == self.player_id:
                    return True
            return False
        
        def isempty(l):
            if ('normal' in rg.loc_types(l)) and not ('obstacle' in rg.loc_types(l)):
                if robots.get(l) == None:
                    return True
            return False
        
        def isspawn(l):
            if 'spawn' in rg.loc_types(l):
                return True
            return False
        
        # scan the area around
        enemies = []
        for loc in around(self.location):
            if isenemy(loc):
                enemies.append(loc)
        
        moveable = []
        moveable_safe = []
        for loc in around(self.location):
            if isempty(loc):
                moveable.append(loc)
            if isempty(loc) and not isspawn(loc):
                moveable_safe.append(loc)
        
        def guard():
            return ['guard']
        
        def suicide():
            return ['suicide']
        
        def canflee():
            return len(moveable) > 0
        
        def flee():
            if len(moveable_safe) > 0:
                return ['move', random.choice(moveable_safe)]
            if len(moveable) > 0:
                return ['move', random.choice(moveable)]
            return guard()
        
        def canattack():
            return len(enemies) > 0
            
        def attack():
            r = enemies[0]
            for loc in enemies:
                if robots[loc]['hp'] > robots[r]['hp']:
                    r = loc
            return ['attack', r]
        
        def panic():
            if canflee():
                return flee()
            elif canattack():
                return attack()
            else:
                return guard()
                
        def imove(to):
            f = self.location
            d = (to[0]-f[0], to[1]-f[1])
            di = (sign(d[0]), sign(d[1]))
            
            good = []
            
            if di[0]*di[1] != 0:
                good.append((di[0], 0))
                good.append((0, di[1]))
            else:
                good.append(di)
            
            for dmove in good:
                loc = (f[0]+dmove[0], f[1]+dmove[1])
                if isempty(loc):
                    return ['move', loc]
            return flee()
        
        ##print "There are", len(enemies), "enemies close"
        if len(enemies) > 1:
            # we gonna die next turn if we don't move?
            if self.hp <= len(enemies)*10:
                # it's ok to suicide if you take someone else with you
                for loc in enemies:
                    if robots[loc]['hp'] <= 15:
                        ##print "Suicide!"
                        return suicide()
            ##print "Too many enemies around, panic!"
            return panic()    
        elif len(enemies) == 1:
            if self.hp <= 10:
                if robots[enemies[0]]['hp'] > 15:
                    ##print "Enemy will kill me, panic!"
                    return panic()
                elif robots[enemies[0]]['hp'] <= 10:
                    ##print "I will kill enemy, attack!"
                    return attack()
                else:
                    # might tweak this
                    ##print "I'm too low on health, suicide!"
                    return suicide()
            else:
                if robots[enemies[0]]['hp'] <= 10:
                    if self.hp <= 15:
                        # avoid suiciders
                        ##print "Avoiding suicider, panic!"
                        return panic()
                else:
                    ##print "Attack!"
                    return attack()
        
        # if we're at spawn, get out
        if isspawn(self.location):
            ##print "I'm on spawn, panic!"
            return panic()
        
        closehelp = None
        prediction = None
        
        # are there enemies in 2 squares?
        for loc in around2(self.location):
            if isenemy(loc):
                ##print "Enemy in 2 squares:", loc
                # try to help teammates
                for loc2 in around(loc):
                    if isteammate(loc2):
                        ##print "And a teammate close to him:", loc2
                        closehelp = imove(loc)
                
                # predict and attack
                if infront(loc, self.location):
                    prediction = ['attack', mid(loc, self.location)]
                elif rg.wdist(rg.toward(loc, rg.CENTER_POINT), self.location) == 1:
                    prediction = ['attack', rg.toward(loc, rg.CENTER_POINT)]
                else:
                    prediction = ['attack', (self.location[0], loc[1])]
        
        if closehelp != None:
            ##print "Help teammate fight:", closehelp
            return closehelp
        if prediction != None:
            ##print "Predict:", prediction
            return prediction
        
        # move randomly
        ##print "Can't decide, panic!"
        return panic()
