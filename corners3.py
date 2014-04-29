import rg, random, Queue, math, operator

# HELPER FUNCTIONS

def spawn_is_imminent(game):
    return game['turn'] % 10 == 0

def diagonals(loc, filter_out=None):
    """like rg.locs_around, but gives up to 4 corners instead of 4 orthogonal directions
    """
    filter_out = filter_out or []
    offsets = ((1, 1), (1, -1), (-1, -1), (-1, 1))
    locs = []
    for o in offsets:
        new_loc = tuple(map(operator.add, loc, o))
        if len(set(filter_out) & set(rg.loc_types(new_loc))) == 0:
            locs.append(new_loc)
    return locs

def two_away(loc, filter_out=None):
    """like rg.locs_around, but gives all spaces that are 2 steps away
    """
    filter_out = filter_out or []
    offsets = ((2,0), (1,1), (0,2), (-1,1), (-2,0), (-1,-1), (0,-2), (1,-1))
    locs = []
    for o in offsets:
        new_loc = tuple(map(operator.add, loc, o))
        if len(set(filter_out) & set(rg.loc_types(new_loc))) == 0:
            locs.append(new_loc)
    return locs

def bfs_multi_goal(goals, avoid):
    grid = [[None]*Robot.BOARD_WIDTH for i in range(Robot.BOARD_HEIGHT)]
    Q = Queue.Queue()
    for g in goals:
        Q.put(g)
    while not Q.empty():
        current = Q.get()
        for next in rg.locs_around(current, filter_out=('invalid', 'obstacle')):
            # continue if not yet visited, and if valid
            if grid[next[0]][next[1]] is None and next not in avoid:
                grid[next[0]][next[1]] = current
                Q.put(next)
    return grid

def around(loc):
    return rg.locs_around(loc, filter_out=('invalid', 'obstacle'))

# ROBOT CLASS

class Robot:
    
    BOARD_WIDTH = 19
    BOARD_HEIGHT = 19
    
    def act(self, game):
        robots = game['robots']
        self.per_frame_process(game)
        near = around(self.location)
        moveable = [loc for loc in near if loc not in robots]
        
        # local helper functions
        def guard():
            return ['guard']

        def suicide():
            return ['suicide']
    
        def move(loc):
            return ['move', loc]

        def attack(loc):
            return ['attack', loc]
            
        def is_enemy(loc):
            return loc in robots and robots[loc].player_id != self.player_id

        adj_enemies = [robots[loc] for loc in near if is_enemy(loc)]
        
        def threat_strength(loc):
            return sum([(1 if is_enemy(l) else 0) for l in around(loc)])
            
        current_threat = threat_strength(self.location)
        
        def should_flee():
            """flee criteria: one or more of
               - I am standing in the deathzone
               - Enemies could kill me in one turn
               - escape route is about to be cut off
            """
            if self.location in self.deathzone:
                return True
            elif self.hp < current_threat * 10:
                return True
            # check 4 directions for escapability, up to 3 spaces away
            escapable = False
            for next in moveable:
                if threat_strength(next) == 0:
                    for two_away in around(next):
                        if threat_strength(two_away) == 0:
                            escapable = True
                            break
            if not escapable:
                return True
            return False
        
        def should_trap():
            my_id = robots[self.location].player_id
            already_tried = my_id in self.tried_trap and self.tried_trap[my_id]
            if self.location in self.enemy_two_away and not already_tried:
                self.tried_trap[my_id] = True
                return True
            else:
                self.tried_trap[my_id] = False
                return False
                
        
        def flee_or_panic():
            # option 1: open, non-threatened space
            choice1 = set(moveable) - (self.dangerzone | self.deathzone)
            if len(choice1) > 0:
                return move(random.sample(choice1, 1)[0])
            # option 2: least thretening option
            min_threat = 100
            choice2 = None
            for l in moveable:
                stren = threat_strength(l)
                if stren < min_threat:
                    choice2 = l
                    min_threat = stren
            if choice2 is not None:
                return move(choice2)
            # option 3: desperation attacks or suicide
            elif current_threat * 10 > self.hp:
                return suicide()
            elif len(adj_enemies) > 0:
                return attack(random.choice(adj_enemies).location)
            return guard()
            
        decision = guard()
        # Decision making process is as follows
        # First, check if I need to flee
        if should_flee():
            print self.location, "panicking"
            decision = flee_or_panic()
        # Second, attack the strongest adjacent enemy (least likely to flee)
        elif len(adj_enemies) > 0:
            print self.location, "atacking adjacent",
            strongest = adj_enemies[0]
            for en in adj_enemies[1:]:
                if en.hp > strongest.hp:
                    strongest = en
            print strongest.location
            decision = attack(strongest.location)
        # Third, set a trap if I am 2 spaces away from an enemy
        elif should_trap():
            print self.location, "setting trap to",
            # choose from the intersection of (spaces around me) and (spaces around enemies)
            choices = [n for n in near if n in self.enemy_edges]
            # this should never not be true, but it's cheap to check
            if len(choices) > 0:
                target = random.choice(choices)
                print target
                decision = attack(target)
        # lastly, move to a useful spot
        else:
            next = self.bfs_to_enemy_edges[self.location[0]][self.location[1]]
            if next is not None and threat_strength(next) * 10 < self.hp:
                print self.location, "advancing to", next
                decision = move(next)
        if decision:
            return decision
        else:
            # flee_or_panic without nearby enemies works like "move randomly"
            return flee_or_panic()
        
    
    def per_frame_process(self, game):
        # ensure that self.last_updated exists
        if not hasattr(self, 'last_updated'):
            self.last_updated = -1
            self.tried_trap = {}
        # check if update has happened yet this frame.
        if self.last_updated < game['turn']:
            self.last_update = game['turn']
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # this code is executed once at the start of each frame #
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # make list of allies and enemies
            self.allies = [bot for bot in game['robots'].values() if bot.player_id == self.player_id]
            self.enemies = [bot for bot in game['robots'].values() if bot.player_id != self.player_id]
            # check if spawn is about to happen
            self.spawn_turn = spawn_is_imminent(game)
            # board locations are handled in terms of sets, because it ensures that
            # each value is here only once (no special checks for duplicates)
            self.ally_occupied = set([ally.location for ally in self.allies])
            self.enemy_occupied = set([enemy.location for enemy in self.enemies])
            self.enemy_edges = set()
            self.enemy_two_away = set()
            for en in self.enemies:
                self.enemy_edges |= set(rg.locs_around(en.location, filter_out=('invalid', 'obstacle')))
                self.enemy_two_away |= set(two_away(en.location, filter_out=('invalid', 'obstacle')))
            # it's not an edge if it's occupied by someone else
            self.enemy_edges -= self.enemy_occupied
            # likewise, it's not two away if it's also closer (1 or 0 away)
            self.enemy_two_away -= self.enemy_edges | self.enemy_occupied
            self.dangerzone = self.enemy_edges
            self.deathzone = set()
            for i in range(Robot.BOARD_WIDTH):
                for j in range(Robot.BOARD_HEIGHT):
                    types = rg.loc_types((i,j))
                    if 'obstacle' in types or (self.spawn_turn and 'spawn' in types):
                        self.deathzone.add((i,j))
            self.bfs_to_enemy_edges = bfs_multi_goal(self.enemy_edges, self.deathzone | self.enemy_occupied)
