                       
##############################################################################
#============================================================================#
  # # # # # ooooooooo.    o8o   .o8        .o8        o8o      .   # # # # # 
  # # # # # `888   `Y88.  `"'  "888       "888        `"'    .o8   # # # # # 
  # # # # #  888   .d88' oooo   888oooo.   888oooo.  oooo  .o888oo # # # # # 
  # # # # #  888ooo88P'  `888   d88' `88b  d88' `88b `888    888   # # # # # 
  # # # # #  888`88b.     888   888   888  888   888  888    888   # # # # # 
  # # # # #  888  `88b.   888   888   888  888   888  888    888 . # # # # # 
  # # # # # o888o  o888o o888o  `Y8bod8P'  `Y8bod8P' o888o   "888" # # # # # 
#==================================================by mueslo=================#
##############################################################################                                                    

import rg
import numpy as np
np.set_printoptions(linewidth=200)
import random
import time
import operator
#import settings
from copy import deepcopy
#from profilehooks import profile

boardsize = (19,19)

maxl = np.prod(boardsize)

enemy_cell = maxl+1
friendly_cell = maxl+2

enemy_fact = 8

timing = False

locs1_delta = ((0, 1), (1, 0), (0, -1), (-1, 0))
locs2_delta = ((0, 2), (2, 0), (0, -2), (-2, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
locs3_delta = (( 0,  3), ( 1,  2), ( 2,  1), (3, 0),
               ( 0, -3), ( 1, -2), ( 2, -1),
               (-1,  2), (-2,  1), (-3, 0),
               (-1, -2), (-2, -1))

walkable = lambda loc: 'obstacle' not in rg.loc_types(loc) and 'invalid' not in rg.loc_types(loc)

def locs_around(loc):
    return rg.locs_around(loc,filter_out=('invalid', 'obstacle'))

def locs_around2(loc):
    #locs2 = []
    #locs1 = locs_around(loc)
    #for loc1 in locs1:
    #    for loc2 in locs_around(loc1):
    #        if rg.wdist(loc,loc2)==2: #if loc2 not in locs1+[loc]:
    #            locs2.append(loc2)
    #locs2 = set(locs2)
    locs2 = [tuple(map(operator.add, loc, d)) for d in locs2_delta]
    locs2 = filter(walkable,locs2)
    #if len(locs2_t) == len(locs2):
    #    print "It WORKS!"
    #else:
    #    print "It DOESN'T work!"
    #    print locs2
    #    print locs2_t
    return locs2

def locs_around3(loc):
    #locs3 = []
    #locs2 = locs_around2(loc)
    #for loc2 in locs2:
    #    for loc3 in locs_around(loc2):
    #        if rg.wdist(loc,loc3)==3:
    #            locs3.append(loc3)
    locs3 = [tuple(map(operator.add, loc, d)) for d in locs3_delta]
    locs3 = filter(walkable,locs3)
    return locs3

def locs_diagonal(loc):
    locs2 = locs_around2(loc)
    locs2 = filter((lambda x: rg.dist(x,loc)<2),locs2)
    return locs2

#returns all minimal elements (as determined by function f)
def chooseallmin(x,f):
    a = map(f,x)
    j = np.where(a==np.min(a))[0] #why does this return an array *inside* a tuple?
    return [x[i] for i in j]

#return first minimal element (as determined by function f)
def choosemin(x,f):
    return x[np.argmin(map(f,x))]

#return first maximal element (as determined by function f)
def choosemax(x,f):
    return x[np.argmax(map(f,x))]

class timer:
    def __init__(self):
        self.time=time.clock()
    def g(self):
        thetime = time.clock()
        diff = thetime-self.time
        self.time=thetime
        return round(diff*10**6) #microseconds

#store turn-persistent info, do other stuff
class GameState(dict):
    moves = {}
    old_gamestate = None
    def __init__(self, gamestate, player_id, turn):
        #dict.__init__(self,gamestate)
        self.player_id = player_id
        self.update_state(gamestate,turn)
    
    def update_state(self,gamestate,turn):
        self.old_gamestate = dict(self)
        self.clear()
        self.update(gamestate)
        self.turn = turn
        self.attacking=[]
        self.enemies=[]
        self.friendlies=[]
        self.escape_queue = []
        self.blocked = []

        self.generate_grid()
        self.detect_blocks()
        self.update_stats()

    def is_target(self,loc):
        if self.gridscore[loc] == 1:
            return True
        return False
    
    def is_enemy(self,loc):
        if self.grid[loc] == enemy_cell:
            return True
        return False
    
    def has_enemy_nb(self,loc):
        for check_loc in locs_around(loc):
            if self.is_enemy(check_loc):
                return True
        return False
    
    def is_isolated(self,loc):
        #if there is max one enemy in wdist 2, a cell is isolated
        if self.n_e_around(loc)==0 and sum(map(self.is_enemy,locs_around2(loc)))<=1 and\
            sum(map(self.is_empty,locs_diagonal(loc)))>0 and\
            sum(map(self.is_enemy,locs_around3(loc)))<=5:
            return True
        return False
    
    def is_surroundable(self,loc):
        #surroundable if at less than 2 enemies adjacent, less than 4 in dist2,
        # and more than 1 friendly in the vicinity that can also move in
        if self.n_e_around(loc) <= 1 and \
            sum(map(self.is_friendly, locs_around2(loc)))>=2 and\
            sum(map(self.is_enemy,locs_around2(loc)))<=2:
            return True
        return False
    
    def is_friendly(self,loc):
        if self.grid[loc] == friendly_cell:
            return True
        return False
    
    #todo self[loc] should gain me a speedup
    def is_empty(self,loc):
        if loc not in self and not ('obstacle' in rg.loc_types(loc) or 'invalid' in rg.loc_types(loc)):
            return True
        return False
        #if np.isnan(self.grid[loc]):
        #    return True
        #return False
    
    def was_blocked(self,loc):
        if loc in self.blocked:
            return True
        return False

    def is_att_target(self,loc):
        if loc in self.attacktargets:
            return True
        return False
    
    #def is_in_danger(self, loc):
    #    if (len(self.empty_locs_around(loc))==0)
    #        and 

    def n_attacking(self,loc):
        return self.attacking.count(loc)
    
    def n_f_around(self,loc):
        return sum(map(self.is_friendly, locs_around(loc)))
    
    def n_e_around(self,loc):
        return sum(map(self.is_enemy, locs_around(loc)))
    
    def update_stats(self):
        self.av = 0 #attack vectors
        self.dv = 0 #defend vectors
        self.fh = 0 #friendly hp
        self.eh = 0 #enemy hp
        self.fb = 0 #friendly bots alive
        self.eb = 0 #enemy bots alive
        
        for loc,bot in self.iteritems():
            #SAME TEAM
            if bot['player_id']==self.player_id: 
                self.fh += bot['hp']
                self.fb += 1
                if self.n_e_around(loc)>0: #has enemy neighbours
                    self.av+=1
            #ENEMY TEAM
            else:
                self.eh += bot['hp']
                self.eb += 1
                if self.n_f_around(loc)>0: #has friendly neighbours
                    self.dv+=1
        
        self.fbovereb = float(self.fb)/self.eb if self.eb != 0 else np.nan
        self.avoverdv = float(self.av)/self.dv if self.dv != 0 else np.nan
        self.fhovereh = float(self.fh)/self.eh if self.eh != 0 else np.nan  
        print "Turn",self.turn
        print "Stats:\tfb/eb=",round(self.fbovereb,2),"\tfb=",self.fb,"\teb=",self.eb
        print "\tav/dv=",round(self.avoverdv,2),"\tav=",self.av,"\tdv=",self.dv
        print "\tfh/eh=",round(self.fhovereh,2),"\tfh=",self.fh,"\teh=",self.eh
        print "A-targets=",self.attacktargets
        print "S-targets:",self.surroundtargets
        print "M-targets=",self.movetargets

    
    #def w(self, fr, to):
    #    s = 1
    #    if self.gridscore[to]<0:
    #        s += -enemy_fact*self.gridscore[to]/2.
    #    if self.gridscore[fr]<0:
    #        s += -enemy_fact*self.gridscore[fr]/2.
    #    return s

    
    def empty_locs_around(self, n, filter_out_blocked=False):
        neighbours = locs_around(n)
        neighbours = filter((lambda x: x not in self),neighbours)
        if filter_out_blocked:
            neighbours = filter((lambda x: x not in self.blocked),neighbours)

        return neighbours

    def reconstruct_path(self, p, n):
        path = [n]
        while path[0] in p:
            path.insert(0,p[path[0]])
        return path

    def d(self,x,y):
        s = rg.dist(x,y)
        if self.gridscore[x]<0:
            s += -enemy_fact*self.gridscore[x]/2.
        if self.gridscore[y]<0:
            s += -enemy_fact*self.gridscore[y]/2.
        return s

    
    def find_path(self, source, target):
        if rg.wdist(source,target)<=1 and self.is_empty(target):
            return [source,target]

        c0 = []; o0 = [source];  p0 = {}
        c1 = []; o1 = [target]; p1 = {}
        f0 = {}; g0 = {}
        f1 = {}; g1 = {}

        g0[source]=0
        f0[source]=g0[source] + self.d(source,target)

        g1[target]=0
        f1[target]=g1[target] + self.d(target,source)

        while len(o0)>0 and len(o1)>0:
            n0 = o0.pop(np.argmin([f0[node] for node in o0]))
            n1 = o1.pop(np.argmin([f1[node] for node in o1]))

            if n0 in c1:
                a = self.reconstruct_path(p0, n0)
                b = self.reconstruct_path(p1, n0)
                return a+(b[-2::-1])

            elif n1 in c0:
                a = self.reconstruct_path(p0, n1)
                b = self.reconstruct_path(p1, n1)
                return a+(b[-2::-1])

            c0.append(n0)
            c1.append(n1)

            for nb in self.empty_locs_around(n0,filter_out_blocked=True):
                g = g0[n0] + self.d(nb,n0)
                f = g + self.d(nb, target)
                if nb in c0 and f >= f0[nb]:
                    continue

                if nb not in o0 or f < f0[nb]:
                    p0[nb] = n0
                    g0[nb] = g
                    f0[nb] = f

                    if nb not in o0:
                        o0.append(nb)

            for nb in self.empty_locs_around(n1,filter_out_blocked=True):
                g = g1[n1] + self.d(n1,nb)
                f = g + self.d(source,nb)
                if nb in c1 and f >= f1[nb]:
                    continue

                if nb not in o1 or f < f1[nb]:
                    p1[nb] = n1
                    g1[nb] = g
                    f1[nb] = f

                    if nb not in o1:
                        o1.append(nb)

        return None
    
    
    def toward(self,loc_from,loc_to):
        #t = timer()
        path = self.find_path(loc_from,loc_to)

        if path is None:
            #print "No path found, took",t.g(),"us"
            return None
        
        #print path
        #print "Attemping to find path of length",len(path),"took",t.g(),"us"

        return path[1]
        
    def generate_grid(self):
        #update the game board
        #t = timer()

        #at first, we don't know the length to anywhere (NaN)
        self.grid = np.ones(boardsize)*np.nan
        self.gridscore = deepcopy(self.grid)
        
        #we can never access invalid tiles (inf)
        for loc in np.ndindex(boardsize):
            if "invalid" in rg.loc_types(loc) or "obstacle" in rg.loc_types(loc):
                self.grid[loc] = np.inf
                self.gridscore[loc] = np.inf
            elif "spawn" in rg.loc_types(loc):
                #e.g: turn 34: -1, turn 39: -6, 40: -10000
                if self.turn%10>3:
                    self.gridscore[loc] = -1*(self.turn%10-3)
                elif self.turn%10==0:
                    self.grid[loc] = np.inf
                    self.gridscore[loc] = -10000

        #print "grid1 took",t.g(),"us"
        #enemy cells and friendly cells are marked with their respective id
        for loc,bot in self.iteritems():
            if bot['player_id'] != self.player_id: #ENEMY
                self.grid[loc] = enemy_cell
                self.gridscore[loc] = enemy_cell
                self.enemies.append(loc)
            else:
                self.grid[loc] = friendly_cell
                self.gridscore[loc] = friendly_cell
                self.friendlies.append(loc)
                #self.loc_by_id[bot["robot_id"]] = loc
        
        #print "grid2 took",t.g(),"us"
        self.movetargets = []
        self.surroundtargets = []
        self.attacktargets = []
        
        for loc in self.enemies: #TODO: check for enemies that might want to escape
            if self.is_surroundable(loc):
                self.attacktargets.append(loc)
                #for cell in locs_around(loc):
                #    if self.is_empty(cell):
                #        self.gridscore[cell]=1
            if self.is_isolated(loc):
                diag = filter(self.is_empty, locs_diagonal(loc)) #empty
                diag = filter((lambda x: self.n_e_around(x)==0),diag) #safe
                self.surroundtargets += diag

            for cell in self.empty_locs_around(loc):
                self.gridscore[cell] = -1*self.n_e_around(cell)

            for cell2 in locs_around2(loc):
                if self.is_empty(cell2) and self.n_e_around(cell2)==0:
                    #self.gridscore[cell2]=1
                    self.movetargets.append(cell2)

        #print "grid3 took",t.g(),"us"
        i=0                        
        while i<len(self.movetargets):
            if sum(map(self.is_enemy,locs_around(self.movetargets[i])))>0:
                del self.movetargets[i] #todo: check for duplicates and remove
            i+=1

        #print "grid4 took",t.g(),"us"
        self.movetargets = list(set(self.movetargets))
    
    def detect_blocks(self):
        def loc_lost_5hp(loc):
            bef = self.old_gamestate.get(loc)
            aft = self.get(loc)
            if aft and bef:
                diff = bef["hp"]-aft["hp"]
                return (diff==5 or diff>self.n_f_around(loc)*10)
            return False

        for loc in self.friendlies:
            r_id = self[loc]["robot_id"]
            move_loc = self.moves.get(r_id)
            if move_loc is not None and move_loc != loc:
                self.blocked.append(self.moves[r_id])
                possible_blockers = filter(self.is_enemy,locs_around(move_loc))
                possible_blockers = filter(loc_lost_5hp, possible_blockers)

                print "Possible blockers around",move_loc,":",possible_blockers
                #possible_blockers = filter()
                #todo: random enemy moves into blocked location

        self.moves = {}

    #currently unused
    def propose(self, loc, action):
        if action[0]=="move":
            if self.is_empty(action[1]) and rg.wdist(loc,action[1])==1:
                return 1
            else: return -1 #invalid
        if action[0]=="attack":
            if self.is_enemy(action[1]) and rg.wdist(loc,action[1])==1:
                return 1 
            else: return -1 #invalid
        if action[0]=="guard":
            return 1
        if action[0]=="suicide":
            return 1

    def claim(self, loc):
        if loc in self.movetargets:
            print "Claiming M-target."
            self.movetargets.remove(loc)
        if loc in self.surroundtargets:
            print "Claiming S-target."
            self.surroundtargets.remove(loc)
            
        pass #return weight
    def act(self,loc,action):
        if action[0]=="move":
            self.grid[loc] = np.nan
            #print "grid at",action[1],"previously:",self.grid[action[1]]
            self.grid[action[1]] = friendly_cell

            self.moves[self[loc]["robot_id"]]=action[1]

            bot = self.pop(loc)
            bot['location'] = action[1]
            self[action[1]] = bot

        elif action[0]=="attack":
            self.attacking.append(action[1])

class Robot:
    turn = None
    gs = None
    def d(self,loc):
        return rg.dist(self.location,loc)
    
    def wd(self,loc):
        return rg.wdist(self.location,loc)    
    
    def trapped(self):
        non_blocked_moveable = filter((lambda x: x not in self.gs.blocked),self.moveable)
        #if len(non_blocked_moveable) != len(self.moveable):
        #    print "We're trapped by a block!"
        return len(non_blocked_moveable)==0

    def is_spawn(self,loc,safe=6):
        if 'spawn' in rg.loc_types(loc) and (self.turn%10==0 or self.turn%10>safe) and self.turn<=90:
            return True
        return False

    def is_imminent_spawn(self,loc):
        if 'spawn' in rg.loc_types(loc) and self.turn%10==0:
            return True
        return False
    
    def nbs_around(self,loc=None):
        loc = loc or self.location
        nbs = []
        for nb_loc in locs_around(loc):
            if self.gamestate.has_key(nb_loc):
                nbs.append(self.gamestate[nb_loc])
    
    def suicide_net_damage(self):
        outcome = -self.hp
        for loc in self.enemy_nbs:
            if self.gs[loc]["player_id"]!=self.player_id: #and not self.is_imminent_spawn(loc):
                outcome += 15 if self.gs[loc]["hp"]>15 else (self.gs[loc]["hp"]+8) #+8 because once they're dead, they can't do damage again, so that's a plus
        return outcome

    #needs reworking #todo, flee where there are fewer enemy nbs
    def flee(self):
        #we can move somewhere *safe*
        if len(self.moveable_safe)>0:
            print "Yeah, let's go somewhere else...", self.moveable_safe
            return ['move', random.choice(self.moveable_safe)]

        #we can move *somewhere*
        elif not self.trapped():
            print "Dear Lord, there's enemies all around!"
            loc = self.gs.toward(self.location,rg.CENTER_POINT)
            if loc is not None:
                print "Yay?"
                return ['move', loc]
            if self.gs.is_empty(rg.toward(self.location, rg.CENTER_POINT)):
                print "Woo?"
                return ['move', rg.toward(self.location, rg.CENTER_POINT)]

            return ['move', random.choice(self.moveable)]

        #if we will do more damage by suiciding than attacking, and enemies would kill us or we're trapped in spawn
        elif (self.suicide_net_damage()>10 or self.hp<10*self.gs.n_e_around(self.location)) or self.is_imminent_spawn(self.location):

            print "Goodbye, cruel world. At least I'm expecting to do",self.suicide_net_damage(),"net damage"
            return ['suicide']

        #we can't move anywhere, suicide isn't an option
        else: 
            #if we have enemy neighbours, attack the one with least hp
            if self.gs.n_e_around(self.location)>0:
                minhp_index = np.argmin([self.gs[loc]['hp'] for loc in self.enemy_nbs])
                print "I may not be the best, but I do my part."
                return ['attack', self.enemy_nbs[minhp_index]]

            #we're trapped, but can possibly get a strike on an enemy
            if len(filter(self.gs.was_blocked,self.moveable))>0:
                return self.predictive_attack()

            #we're trapped between friendlies
            else:
                print "Yeah, thanks for trapping me here, guys."
                return ['guard']

    def update_state_variables(self,turn):
        if self.turn != turn:
            self.turn=turn
            if self.gs is None:
                self.gs = GameState(self.turnstart_gamestate,self.player_id,self.turn)
            else:
                self.gs.update_state(self.turnstart_gamestate, self.turn)

        #todo: makes this a dict
        self.e_ds = map(self.d,self.gs.enemies)
        self.e_wds = map(self.wd,self.gs.enemies)
        
        # enemy neighbours?
        self.enemy_nbs = []
        for loc in locs_around(self.location):
            if self.gs.is_enemy(loc):
                self.enemy_nbs.append(loc)
                
        self.moveable = []
        #self.moveable_turnstart = []

        self.moveable_safe = []
        for loc in locs_around(self.location):
            if self.gs.is_empty(loc) and (not self.is_imminent_spawn(loc)):
                self.moveable.append(loc)
            if self.gs.is_empty(loc) and (not self.is_spawn(loc,safe=0)) and self.gs.n_e_around(loc)==0:
                self.moveable_safe.append(loc)
            #if self.gs.is_empty_turnstart(loc):
            #    self.moveable_turnstart.append(loc)
    
    def reinforce(self):
        print "Reinforcements have arrived!"
        #we're at walking distance 2 to the closest enemy
        if np.min(self.e_wds)==2:
            to_attack = map(self.gs.has_enemy_nb,self.moveable)
            attack_here = [loc for i,loc in enumerate(self.moveable) if to_attack[i]]
            #print "attack here:",attack_here
            #we can attack between:
            if len(attack_here)>0:
                print "\"Point sharp end towards enemy.\" What?"
                return ['attack', random.choice(attack_here)]
            #we can't attack between
            else: return ['guard']

        #we're next to an enemy!
        elif np.min(self.e_wds)==1:
            print "Let's go back a bit..."
            return self.flee()

        #closest enemy is at least walking distance 3
        else:
            print "I thought I was better than this :("
            #todo something better than flee
            return self.flee()
        
    #@profile
    def act(self, game):
        #t = timer()
        t2 = timer()
        actual_turn = game['turn']
        if self.turn != actual_turn:
            self.turnstart_gamestate = game['robots']
        self.update_state_variables(actual_turn)
        
        #print "--------------------"
        #print "init stuff took",t.g(),"us"
        print str(self.player_id)+"-"+str(self.robot_id)+":",self.location,"is pondering his choices..."
        
        action = self.choose_action()()
        #print "choosing action took",t.g(),"us"

        self.gs.act(self.location,action)
        print str(self.player_id)+"-"+str(self.robot_id)+":",self.location,"acts:",action
        print "bot took a total of",t2.g(),"us"
        return action
    def choose_action(self):
        #net_dmg_agg = 50
        #net_dmg_def = 50
        return self.act_defensively
        #return random.choice([self.act_defensive,self.act_aggressive])
        

    def get_to_best(self,locs,func,minh=20.0):
        #t = timer()
        start = time.clock()
        print "We want to go somewhere..."

        #if the loc refers to an attack location, make sure we have enough health
        locs = filter((lambda loc: (not self.gs.has_key(loc)) or minh*self.gs[loc]['hp']<self.hp),locs)
        #print "filtered",locs
        if len(locs)==0:
            print "No good target, this makes me a sad bot."
            return None #self.reinforce()
        
        #print "1st filter took",t.g(),"us"
        i = np.argmin(map(func,locs))
        destination_to_try = locs[i]
        loc = self.gs.toward(self.location, locs[i])
        tries = 1
        while loc is None and tries<len(locs): #or self.gs[locs[i]]['hp']>minh*self.hp:
            if tries==1:
                i = np.argsort(map(func,locs))
            destination_to_try = locs[i[tries]]
            loc = self.gs.toward(self.location, destination_to_try)
            #max 10ms
            if (time.clock()-start)*10**6>10 or tries>5:
                print "Ran out of time (or tries)"
                return None #self.reinforce()
            tries +=1

        #print "2nd filter took",t.g(),"us"
        #no path is found, or path would lead us into spawn
        if loc is None or (self.is_imminent_spawn(loc)):
            print "No good target, this makes me a sad bot."
            return None #self.reinforce()

        #print "3rd filter took",t.g(),"us"
        self.gs.claim(destination_to_try)
        return ['move', loc]          
    
    #todo: if attack fails -> surround, surround fails -> move, move fails -> flee
    def find_enemy(self):
        if len(self.gs.attacktargets)>0 and (self.hp>10):#we can take a hit
            print "Haaaaave you met Ted?"
            action = self.get_to_best(self.gs.attacktargets,self.d,minh=0.9)
            if action is not None: return action
        elif len(self.gs.surroundtargets)>0 and (self.hp>10): #we can take a hit
            print "Hello, Ladies! Three's a crowd."
            action = self.get_to_best(self.gs.surroundtargets, self.d,minh=0.5)
            if action is not None: return action
        elif len(self.gs.movetargets)>0:
            print "I like to move it, move it!"
            action = self.get_to_best(self.gs.movetargets,self.d,minh=0.8)
            if action is not None: return action
        #with elifs I'm worse against liquid and better against plasma
        #with ifs it's the inverse
        return self.reinforce()

    def predictive_attack(self):
        print "SPEARS AT THE READY!"
        to_attack = map(self.gs.has_enemy_nb,self.moveable)
        attack_here = [loc for i,loc in enumerate(self.moveable) if to_attack[i]]

        if len(attack_here)>0:
            return ['attack', random.choice(attack_here)]
        else:
            return self.reinforce()

    def survivable_turns(self,num_enemies=1,guard=False,hp=None):
        if hp is None:
            hp = self.hp

        dmg_per_turn = 10*num_enemies if not guard else 5*num_enemies
        return hp/dmg_per_turn 

    def tts(self):
        return (10-self.turn%10)%10

    def act_defensively(self):
        #if we're in spawn, we should get the hell outta there
        if self.is_spawn(self.location,safe=0):
            return self.flee()

        #todo: if there are too few friendlies and too many enemies nearby, flee

        #if we have an enemy neighbour, attack him if he is weak or an attack target
        if len(self.enemy_nbs)==1:
            enemy = self.enemy_nbs[0]
            enemyhp = self.gs[enemy]['hp']

            if self.gs.attacking.count(enemy)*10>enemyhp:
                #Attempt to dodge suicide
                print "Cut and run!"
                return self.flee()
            if enemy in self.gs.attacktargets and (self.hp>=0.5*enemyhp and self.hp>10):
                print "DIE, BEAST... DIE!"
                return ['attack', enemy]
            if self.hp>enemyhp+10: #todo guard if it is worth it
                print "Hah. Weakling. DIE!"
                return ['attack', enemy]
            if self.gs.n_f_around(enemy)>1 and self.hp>10: #we can take a hit
                print "You think you can escape? Pah. DIE!"
                return ['attack', enemy]
            if self.is_spawn(enemy):
                if self.is_imminent_spawn(enemy):
                    print "Cut and run!"
                    #they might suicide, but probably won't move into our square
                    return self.flee()
                #print "Survivable turns:",self.survivable_turns()
                #print "Turns till spawn:",self.tts()

                if self.survivable_turns(guard=True)>self.tts():
                    print "I shall stand firm."
                    return ['guard']
            
            print "Enemy is neither weak nor target. ESCAPE!"
            return self.flee()

        #if we have more than one enemy neighbour, we are outgunned and should flee
        elif len(self.enemy_nbs)>1: #todo unless we we are next to an attack target
            #todo: check if we're blocking an enemy and will survive, else move
            print "We are outmatched. ESCAPE!"
            return self.flee()

        #if we don't have an enemy neighbour, we have different options
        else: #no enemy nb
            #print "min e wd",np.min(self.e_wds),"min e d",np.min(self.e_ds)
            #we're on diagonal to enemy
            if np.min(self.e_wds)==2: #and np.min(self.e_ds)<2: #sum(map(self.gs.is_enemy,locs_diag(self.l)))>0
                print "We have sight of the enemy!"

                #is enemy blockable? also, let's not die.
                if self.tts()<=1 and self.hp>5:
                    blockable_enemies = chooseallmin(self.gs.enemies, self.d) #todo redo this when e_dists is a dict
                    blockable_enemies = filter(self.is_spawn, blockable_enemies)
                    
                    if len(blockable_enemies)>0:
                        enemy_moveable = []
                        for e in blockable_enemies:
                            enemy_moveable += self.gs.empty_locs_around(e)
                        enemy_moveable = filter((lambda x: not self.is_imminent_spawn(x)),enemy_moveable)
                        enemy_moveable = filter((lambda x: x in self.moveable), enemy_moveable)

                        if len(enemy_moveable)>0:
                            print "Yes, I am Gandalf."
                            return ['move', random.choice(enemy_moveable)]

                #is one of those an attack target?
                diag_att_targets = filter(self.gs.is_att_target,locs_around2(self.location))

                #do we have enough health?
                diag_att_targets = filter((lambda x: self.gs[x]['hp']<=1.5*self.hp),diag_att_targets)

                if len(diag_att_targets)>0:
                    move_to = []

                    #friendly hp surrounding diag_att_target
                    friendly_help = [sum([self.gs[loc]['hp'] for loc in filter(self.gs.is_friendly,locs_diagonal(d_a_target)+locs_around(d_a_target))])\
                                        for d_a_target in diag_att_targets]

                    good_targets = []
                    for i,t in enumerate(diag_att_targets):
                        if self.gs[t]['hp']<(friendly_help[i]-20): #expect to take 2 hits
                            good_targets.append(t)

                    #can we actually move next to a good target?
                    for target in good_targets:
                        move_to += filter((lambda x: rg.wdist(x,target)==1),self.moveable)

                    
                    if len(move_to)>0 and (self.hp>10): #we can take a hit
                        print "SURROUND THE BEAST, MEN!"
                        #todo: only surround if they can't escape

                        #we only want to move to the squares that have the least enemies around them
                        move_to = chooseallmin(move_to,self.gs.n_e_around)

                        #quick and dirty to avoid blocking (but works):
                        #we also only want to move to squares with the least friendlies around them
                        return ['move',choosemin(move_to, self.gs.n_f_around)]
                
                #we're on diagonal, but it's not an attack target (or unreachable):
                return self.predictive_attack()
                #to_attack = map(self.gs.has_enemy_nb,self.moveable)
                #attack_here = [loc for i,loc in enumerate(self.moveable) if to_attack[i]]
                ##print "attack here:",attack_here
                #if len(attack_here)>0:
                #    return ['attack', random.choice(attack_here)]
                #else: return self.reinforce()
                
            #we're not on a diagonal
            #elif np.min(self.e_wds)==2 and np.min(self.e_ds)==2:
            #    return self.predictive_attack()
            #
            else:
                return self.find_enemy()

            
    def act_aggressively(self):
        #score these on net damage produced
        if len(self.enemy_nbs)>0:
            minhp_index = np.argmin([self.gs[loc]['hp'] for loc in self.enemy_nbs])
            return ['attack', self.enemy_nbs[minhp_index]]
        else:
            loc = self.gs.toward(self.location, self.gs.ecom)
            if loc is None:
                return ['guard']
            return ['move', loc]
