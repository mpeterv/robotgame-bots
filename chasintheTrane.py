# chasin' the Trane by benbou
# http://robotgame.net/viewrobot/8310

# bot: chasin' the Trane
# author: benbou
# I know this bot is a bit of a clusterfuck,
# But I'm a noob at programming,
# So it was a learning experience
# My next bot will rock

import rg

class Robot():

    def act(self, game):

        robots = game['robots']
        scenarios = {}

        #Damages dealt
        our_hp_threshold = rg.settings.attack_range[1]
        their_hp_threshold = rg.settings.attack_range[0]

        #spawn
        if 1 <= game['turn'] % 10 <= 7:
            spawn = -10
        else: spawn = -50
        spawn_move = 5

        #Us vs them
        us = []
        them = []
        for loc, bot in robots.iteritems():
            if bot['player_id'] == self.player_id:
                us.append(loc)
            else: them.append(loc)

        #Team HP
        self.our_hp = 0
        for one in us:
            self.our_hp += robots[one]['hp']

        self.their_hp = 0
        for it in them:
            self.their_hp += robots[it]['hp']

        #Dominance
        dominance = len(us)/(len(us) + len(them))

        #Own HP
        hurt = -5
        wounded = -30

        #Enemies
        one_opponent = 5
        two_opponents = -10
        three_opponents = -30
        overpowered_move = 5
        wounded_enemy = 5
        money_time = 0
        if game['turn'] > rg.settings.max_turns - 20:
            if dominance < 0.5:
                money_time = 5

        #Orientation
        inner_circle = 3

        #Space between allies
        living_space = -5

        #Shapes
        propeller = 0
        pyramid = 15
        doublejoin = 10
        join = 5


        def find_five_points(loc):
            self._five_points = [loc]
            #self._five_points.append(loc)
            self._new_points = rg.locs_around(loc, filter_out=('invalid', 'obstacle'))
            for point in self._new_points:
                self._five_points.append(point)
            return self._five_points

        def find_opponents(loc1): #next to the bot
            self._opponents = []
            for loc2, bot in robots.iteritems():
                if rg.wdist(loc1, loc2) <= 1:
                    if robots[base_bot]['player_id'] != robots[loc2]['player_id']:
                        self._opponents.append(loc2)
            return self._opponents

        def find_enemies(): #anywhere
            self._enemies = []
            for loc, bot in robots.iteritems():
                if robots[base_bot]['player_id'] != robots[loc]['player_id']:
                    self._enemies.append(loc)
            return self._enemies

        def find_friends():
            self._friends = []
            for loc, bot in robots.iteritems():
                if robots[base_bot]['player_id'] == robots[loc]['player_id'] :
                    if base_bot != loc:
                        self._friends.append(loc)
            return self._friends

        def find_closest_enemy(loc):
            self._ref_enemy_hp = 999
            self._closest_enemy_hp = 0
            self._ref_dist = 999
            self._enemy_dist = 0
            for loc2 in them:
                self._enemy_dist = rg.wdist(loc, loc2)
                if self._enemy_dist <= self._ref_dist:
                    if robots[loc2]['hp'] < self._ref_enemy_hp:
                        self._closest_enemy_hp = robots[loc2]['hp']
                        self._closest_enemy = loc2
            return self._closest_enemy


        def score_health():
            self._hp = robots[base_bot]['hp']
            self._health = 0
            self._hurt_level = our_hp_threshold * 2
            self._wounded_level = our_hp_threshold
            if self._hp <= self._wounded_level:
                self._health = wounded
            elif self._hp <= self._hurt_level:
                self._health = hurt
            return self._health

        def score_aggressiveness(loc1):
            self._aggressiveness = 0
            for loc2 in enemies:
                if rg.wdist(loc1, loc2) <= 2:
                    self._aggressiveness = money_time
                    return self._aggressiveness
            return self._aggressiveness

        def score_opponents(loc1):
            self._danger = 0
            self._opponents = find_opponents(loc1)
            #Number of opponents
            self._nbr_opponents = len(self._opponents)
            if self._nbr_opponents >= 3:
                self._danger = three_opponents
            elif self._nbr_opponents == 2:
                self._danger = two_opponents
            elif self._nbr_opponents == 1:
                self._danger = one_opponent

            #Opponent health
            for loc2 in self._opponents:
                if robots[loc2]['hp'] <= robots[base_bot]['hp']:
                    self._danger += wounded_enemy

            #Bot health
            if self._nbr_opponents >= 1:
                self._health = score_health()
                self._danger += self._health

            #When overpowered, better to at least move
            if self._danger < 0:
                self._base_bot_opponents = find_opponents(base_bot)
                if len(self._base_bot_opponents) >= self._nbr_opponents:
                    self._danger += overpowered_move

            return self._danger

        def score_orientation(loc):
            self.orientation_score = 0

            #Terrain types
            self._loc_type = rg.loc_types(loc)
            if 'spawn' in self._loc_type:
                self.orientation_score += spawn
                if 'spawn' in rg.loc_types(base_bot):
                    self.orientation_score += spawn_move

            # Distance to center
            self.dist_to_center = round(rg.dist(loc, gravity_center))
            if self.dist_to_center <= inner_circle:
                self.dist_to_center = 0
            self.orientation_score += - self.dist_to_center

            #Distance to friends
            self.dist_to_closest_friend = 0
            for loc2 in friends:
                self._ref_dist = 16
                self.dist_to_closest_friend = 16
                self.dist_to_closest_friend = rg.dist(loc, loc2)
                if self.dist_to_closest_friend < self._ref_dist:
                    self._ref_dist = self.dist_to_closest_friend
            self.orientation_score += round(self.dist_to_closest_friend)
            return self.orientation_score

        def score_coordination(loc1):
            self._coordination = 0
            for loc2 in friends:
                if rg.wdist(loc1, loc2) <= 1:
                    self._coordination = living_space
                    return self._coordination
            return self._coordination

        def score_shapes(loc):
            self._shape = 0

            self._shapes = { 4  : {'shape': set([((-1, -1), (-1, 1), (1, 1), (1, -1))]), #Propeller
                                       'score' : propeller},
                            3 : {'shape': set([((-1, 1), (-1, -1)), ((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1))]), #Pyramid
                                       'score' : pyramid},
                           2 : {'shape': set([((-1, -1), (1, 1)), ((-1, 1), (1, -1))]), #Doublejoin
                                       'score' : doublejoin},
                            1: {'shape': set([((-1, -1), (-1, 1), (1, 1), (1, -1))]), #Join
                                       'score' : join},}

            for shape in sorted(self._shapes.iterkeys()):
                for variant in self._shapes[shape]['shape']:
                    self.real_life_shape = []
                    if variant != ((), ()):
                        self.count = 0
                        self.real_life_shape.append(loc)
                        for offset in variant:
                            self.real_life_point = (loc[0] + offset[0] , loc[1] + offset[1])
                            self.real_life_shape.append(self.real_life_point)
                        #print self.real_life_shape
                        for him in us:
                            if him in self.real_life_shape:
                                self.count += 1
                                if loc in self.real_life_shape:
                                    if len(self.real_life_shape) == self.count:
                                        self._shape_score = self._shapes[shape]['score']
                                        return self._shape

            return self._shape

        def find_gravity_center():
            self.friends_coordinates = []
            for loc, bot in robots.iteritems():
                if bot.player_id == self.player_id:
                    self.friends_coordinates.append(loc)
            if self.friends_coordinates !=[]:
                self.x_total = 0
                self.y_total = 0
                for point in self.friends_coordinates:
                    self.x_total += point[0]
                    self.y_total += point[1]
                self._gravity_center = (round(self.x_total/len(self.friends_coordinates)), \
                                       round(self.y_total/len(self.friends_coordinates)))
            return self._gravity_center

        #################################

        base_bot = self.location
        friends = find_friends()
        enemies = find_enemies()
        gravity_center = find_gravity_center()

        self.five_points = find_five_points(base_bot)
        for loc in self.five_points:
            self.orientation = score_orientation(loc)
            self.danger = score_opponents(loc)
            self.shape = score_shapes(loc)
            self.coordination = score_coordination(loc)
            self.aggressiveness = score_aggressiveness(loc)
            score = self.orientation \
                    + self.danger \
                    + self.shape \
                    + self.coordination \
                    + self.aggressiveness
            scenarios[loc] = score

        self.the_point = max(scenarios, key = lambda a: scenarios.get(a))
        if self.the_point in enemies:
            return ['attack', self.the_point]

        if self.the_point == self.location:
            self.opponents = find_opponents(self.the_point)
            if self.opponents:
                self._opponents_hp = {}
                for loc in self.opponents:
                    self._opponent_hp = robots[loc]['hp']
                    self._opponents_hp[loc] = self._opponent_hp
                self.target = min(self._opponents_hp, key = lambda a: self._opponents_hp.get(a))
                return ['attack', self.target]

            else:
                self.closest_enemy = find_closest_enemy(self.location)
                if rg.wdist(self.location, self.closest_enemy) == 2:
                    return ['attack', rg.toward(self.location, self.closest_enemy)]

            return ['guard']

        return ['move', self.the_point]
