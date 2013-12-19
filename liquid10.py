# liquid 1.0 by peterm
# http://robotgame.net/viewrobot/7913

#from profilehooks import profile
import random
import math
import operator
import rg

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

wdist = lambda p1, p2: abs(p2[0]-p1[0]) + abs(p2[1]-p1[1])

def around(loc, r = 1):
    offsets = None
    if r == 1:
        offsets = ((0, 1), (1, 0), (0, -1), (-1, 0))
    elif r == 2:
        offsets = ((0, 2), (2, 0), (0, -2), (-2, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
    return [tuple(map(operator.add, loc, o)) for o in offsets]
    

class Game:
    def __init__(self, data, player_id):
        self.player_id = player_id
        self.update(data)
    
    def update(self, data):
        self.turn = data['turn']
        self.tillspawn = (10 - (self.turn % 10)) % 10
        if self.turn > 90:
            self.tillspawn = 10
        
        self.robots = data['robots']
        self.onNewTurn()
    
    # called in the beginning of each turn
    def onNewTurn(self):
        self.cache_danger = {}
        self.cache_wishes = {}
        self.acts = {}
        self.taken = []
        self.hunts = {}
        self.marked_for_death = []
        
        gtfo_queue = []
        for loc in self.robots:
            if self.isteammate(loc) and self.urgent(loc):
                gtfo_queue.append(loc)
        
        gtfo_queue.sort(key = lambda x: (self.danger, -len(self.wishes(x))))
        
        while len(gtfo_queue) > 0:
            gtfo_teammate = gtfo_queue.pop()
            gtfo_wishes = self.wishes(gtfo_teammate)
            
            # find move which is not taken by other bots
            gtfo_act = None
            for gtfo_wish in gtfo_wishes:
                if gtfo_wish not in self.taken:
                    gtfo_act = gtfo_wish
                    break
            if gtfo_act == None:
                #print gtfo_teammate, "can't escape"
                gtfo_act = gtfo_teammate
            else:
                #print gtfo_teammate, "can escape to", gtfo_act
                pass
            
            self.acts[gtfo_teammate] = gtfo_act
            self.taken.append(gtfo_act)
            
            # are we bumping in another teammate?
            if (gtfo_act != gtfo_teammate) and self.isteammate(gtfo_act):
                # that guy shouldn't try to bump into us
                bumped_teammate = gtfo_act
                bumped_teammate_wishes = self.wishes(bumped_teammate)
                if gtfo_teammate in bumped_teammate_wishes:
                    bumped_teammate_wishes.remove(gtfo_teammate)
                self.cache_wishes[bumped_teammate] = bumped_teammate_wishes
                
                # he also should be priority in the gtfo_queue
                if bumped_teammate in gtfo_queue:
                    gtfo_queue.remove(bumped_teammate)
                gtfo_queue.append(bumped_teammate)
                
        for agent in self.robots:
            if self.isagent(agent):
                enemies_around = self.enemies(agent)
                if len(enemies_around) >= 1:
                    self.hunts[agent] = ['attack', enemies_around[0]]
                    self.taken.append(agent)
                    self.marked_for_death.append(enemies_around[0])
    
    # should return action for bot at given location
    def act(self, loc):
        if self.acts.get(loc) is None:
            #print_(loc, "Doesn't have to do anything urgent")
            if self.hunts.get(loc) is None:
                #print_(loc, "Can't hunt")
                enemies = self.enemies(loc)
                if len(enemies) == 1:
                    return ['attack', enemies[0]]
                else:
                    # no one close...
                    enemies2 = self.enemies(loc, 2)
                    if len(enemies2) > 0:
                        if (self.tillspawn <= 1) and (self.gethp(loc) > 10):
                            for enemy2 in enemies2:
                                if self.isspawn(enemy2):
                                    goodmove = self.toward(loc, enemy2)
                                    if self.canmove(loc, goodmove):
                                        self.taken.append(goodmove)
                                        self.hunts[loc] = ['move', goodmove]
                                        return ['move', goodmove]
                        
                        for enemy2 in enemies2:
                            if enemy2 in self.marked_for_death:
                                goodmove = self.carefulmovetowards(loc, enemy2)
                                if goodmove is not None:
                                    self.taken.append(goodmove)
                                    self.hunts[loc] = ['move', goodmove]
                                    return ['move', goodmove]
                        bs = 0
                        attack_best_loc = self.toward(loc, enemies2[0])
                        for attack_loc in around(loc):
                            if self.moveable(attack_loc):
                                s = 0
                                for l in around(attack_loc):
                                    if self.isenemy(l):
                                        s += 1
                                        if self.isspawn(l) and not self.isspawn(attack_loc):
                                            s += 4
                                if s > bs:
                                    attack_best_loc = attack_loc
                                    bs = s
                        return ['attack', attack_best_loc]
                    else:
                        # no one close whatsoever...
                        self.marked_for_death.sort(key = lambda x: rg.wdist(x, loc))
                        for enemy in self.marked_for_death:
                            goodmove = self.carefulmovetowards(loc, enemy)
                            if goodmove is not None:
                                self.taken.append(goodmove)
                                self.hunts[loc] = ['move', goodmove]
                                return ['move', goodmove]
                        moves = around(loc)
                        moves.append(loc)
                        moves = filter(lambda x: self.canmove(loc, x), moves)
                        if len(moves) > 0:
                            return self.domove(loc, random.choice(moves))
                        else:
                            return ['guard']
            else:
                # can hunt
                return self.hunts[loc]
        else:
            return self.domove(loc, self.acts[loc])
    
    def carefulmovetowards(self, fr, to):
        possible = []
        for loc in around(fr):
            if self.canmove(fr, loc):
                ok = True
                for loc2 in around(loc):
                    if self.isenemy(loc2) and (loc2 not in self.marked_for_death):
                        ok = False
                        break
                if ok:
                    possible.append(loc)
        possible.sort(key = lambda x: rg.wdist(x, to))
        if len(possible) > 0:
            return possible[0]
        else:
            return None
    
    def canmove(self, fr, to):
        if not self.moveable(to):
            return False
        if to in self.taken:
            return False
        if self.isteammate(to):
            if self.acts.get(to) is not None:
                if self.acts[to] == fr:
                    return False
        return True
    
    def isagent(self, loc):
        return self.isteammate(loc) and (self.gethp(loc) > 10) and (self.acts.get(loc) is None) and (self.hunts.get(loc) is None)
    
    
    def dest(self, loc, action):
        if action[0] != 'move':
            return loc
        else:
            return action[1]
    
    def toward(self, fr, to):
        if infront(fr, to):
            return mid(fr, to)
        else:
            if not self.isobstacle((fr[0], to[1])):
                return (fr[0], to[1])
            return (to[0], fr[1])
        
    def urgent(self, loc):
        if not self.moveable(loc):
            return True
        if len(self.enemies(loc)) > 1:
            return True
        if (len(self.enemies(loc)) == 1) and (self.gethp(loc) <= 15):
            return True
        return False
    
    def wishes(self, loc):
        if self.cache_wishes.get(loc) == None:
            self.cache_wishes[loc] = self._wishes(loc)
        return self.cache_wishes[loc]
    
    def _wishes(self, loc):
        escapes = self.escapes(loc)
        #print escapes
        #wishes = map(lambda x: self.domove(loc, x), escapes)
        wishes = escapes
        #print wishes
        return wishes
    
    def moveable(self, loc):
        if self.isobstacle(loc) or self.isenemy(loc):
            return False    
        if (self.tillspawn <= 1) and self.isspawn(loc):
            return False
        if (self.tillspawn <= 2) and self.isdeepcorner(loc):
            return False
        return True

    def reallymoveable(self, loc):
        if self.isobstacle(loc) or self.isenemy(loc):
            return False    
        if (self.tillspawn <= 0) and self.isspawn(loc):
            return False
        if (self.tillspawn <= 1) and self.isdeepcorner(loc):
            return False
        return True
        
    def enemyrange(self, loc):
        if len(self.enemies(loc)) > 0:
            return 1
        if len(self.enemies(loc, 2)) > 0:
            return 2
        return 3
    
    def domove(self, fr, to ):
        if fr == to:
            if not self.reallymoveable(to):
                return ['suicide']
            else:
                enemies = self.enemies(fr)
                if len(enemies) > 0:
                    return ['attack', enemies[0]]
                return ['guard']
        else:
            return ['move', to]
    
    def danger(self, loc):
        if self.cache_danger.get(loc) == None:
            self.cache_danger[loc] = self._danger(loc)
        return self.cache_danger[loc]
    
    def _danger(self, loc):
        enemyrange = self.enemyrange(loc)
        r = None
        if not self.moveable(loc):
            r = 10000
        elif enemyrange == 3:
            r = 0
        elif enemyrange == 2:
            r = 200 + 2*len(self.enemies(loc, 2))
        elif enemyrange == 1:
            r = 600 + 100*len(self.enemies(loc))
        if self.isteammate(loc):
            r += 20
        if self.iscorner(loc):
            r += 3
        if self.isspawn(loc):
            if self.tillspawn == 1:
                r += 20
        return r + 3 * wdist(loc, rg.CENTER_POINT)
    
    def escapes(self, loc):
        moveable = around(loc)
        moveable.append(loc)
        moveable_safe = filter(self.moveable, moveable)
        moveable_safe.sort(key=self.danger)
        #print "Escapes from", loc, moveable
        return moveable_safe
    
    def enemies(self, loc, r = 1):
        return filter(self.isenemy, around(loc, r))
    
    def teammates(self, loc, r = 1):
        return filter(self.isteammate, around(loc, r))
    
    def gethp(self, loc):
        return self.robots[loc]['hp']
    
    def isenemy(self, loc):
        return (self.robots.get(loc) != None) and (self.robots[loc]['player_id'] != self.player_id)
        
    def isteammate(self, loc):
        return (self.robots.get(loc) != None) and (self.robots[loc]['player_id'] == self.player_id)
        
    def isspawn(self, loc):
        return loc in [(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17)]
    
    def isobstacle(self, loc):
        return loc in [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(18,0),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),(0,2),(1,2),(2,2),(3,2),(4,2),(14,2),(15,2),(16,2),(17,2),(18,2),(0,3),(1,3),(2,3),(16,3),(17,3),(18,3),(0,4),(1,4),(2,4),(16,4),(17,4),(18,4),(0,5),(1,5),(17,5),(18,5),(0,6),(1,6),(17,6),(18,6),(0,7),(18,7),(0,8),(18,8),(0,9),(18,9),(0,10),(18,10),(0,11),(18,11),(0,12),(1,12),(17,12),(18,12),(0,13),(1,13),(17,13),(18,13),(0,14),(1,14),(2,14),(16,14),(17,14),(18,14),(0,15),(1,15),(2,15),(16,15),(17,15),(18,15),(0,16),(1,16),(2,16),(3,16),(4,16),(14,16),(15,16),(16,16),(17,16),(18,16),(0,17),(1,17),(2,17),(3,17),(4,17),(5,17),(6,17),(12,17),(13,17),(14,17),(15,17),(16,17),(17,17),(18,17),(0,18),(1,18),(2,18),(3,18),(4,18),(5,18),(6,18),(7,18),(8,18),(9,18),(10,18),(11,18),(12,18),(13,18),(14,18),(15,18),(16,18),(17,18),(18,18)]
    
    def iscorner(self, loc):
        return (abs(loc[0]-9), abs(loc[1]-9)) in [(2, 8), (4, 7), (6, 6), (7, 4), (8, 2)]
    
    def isdeepcorner(self, loc):
       return (abs(loc[0]-9), abs(loc[1]-9)) == (6, 6)
        
    # useful info is stored in self.player_id, self.turn and self.robots preprties

class Robot:
    game = None
    
    #@profile
    def act(self, data):
        if self.game == None:
            self.game = Game(data, self.player_id)
        elif self.game.turn != data['turn']:
            self.game.update(data)
        return self.game.act(self.location)
