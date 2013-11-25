# kamikaze112213 by hephaestus
# http://robotgame.org/viewrobot/5830

import rg
import operator

class Robot:
    def act(self, game): 
        adjacent_robots = self.get_adjacent_robots(game)
        adjacent_friendlies = self.get_adjacent_robots(game, operator.__eq__)
        adjacent_enemies = self.get_adjacent_robots(game, operator.__ne__)

        all_enemies = self.get_all_robots(game, operator.__ne__)

        # "The value of the key parameter should be a function that takes 
        # a single argument and returns a key to use for sorting purposes."
        def query(bot_dict, sorting_function, offset=0):
            organized = sorted(bot_dict.items(), key=sorting_function)
            # returns a list of tuples, [(key, value),... ]
            return organized

        def get_weakest_enemy(offset=0):
            return query(all_enemies, lambda t: t[1].hp)[offset][1]

        def get_weakest_adjacent_enemy(offset=0):
            return query(adjacent_enemies, lambda t: t[1].hp)[offset][1]

        # first_enemy_location = get_first_enemy_location()
        weakest_enemy = get_weakest_enemy()
        target_enemy = weakest_enemy
        
        if len(adjacent_enemies) > 0:
            weakest_adjacent_enemy = get_weakest_adjacent_enemy()
            target_enemy = weakest_adjacent_enemy

        # move toward the center, if moving there would not put you in range of 2 robots
        target_pos = rg.toward(self.location, weakest_enemy.location)

        # figure out if any friendly robots would also want to move to our target
        adjacent_to_target_friendlies = self.get_adjacent_robots_to(target_pos, game, operator.__eq__)

        # if there are enemies around, attack them
        # also consider suiciding when it will guarantee a kill, meaning enemy < 15 hp
        suicide_threshold = 3 # 3 is better than 4 with 83% confidence, 7-42, 10-34 vs 3-43, 7-38
        # 4 is [55, 30, 15] against 3

        def has_suicide_priority():
            adjacent_allies_to_target_enemy = self.get_adjacent_robots(game, operator.__eq__)
            weakest_allies_next_to_adjacent_target_enemy = query(adjacent_allies_to_target_enemy, lambda t: t[1].hp)
            return self.location == weakest_allies_next_to_adjacent_target_enemy[0][0]

        if len(adjacent_enemies) > 0 and len(adjacent_enemies) < suicide_threshold:
            # following line is better by 102-20-17 over just self.hp < 10
            # inspired by peterm's stupid 2.6 bot
            # assuming all adjacent enemies attacked me, if I would die
            # i should instead suicide
            if self.hp < (10*len(adjacent_enemies)):
                return ['suicide']
            # IDEA: if i could kill the enemy with 1 suicide instead of two attacks
            # NOTE: if multiple allies are going for this target, i'll actually lose too many bots
            # bad idea, 0-20 against self
            # if weakest_adjacent_enemy.hp < 15 and weakest_adjacent_enemy.hp > 8 and has_suicide_priority():
                # return ['suicide']

            # if you could kill 2+ bots by suidiciding, do it
            
            # should also avoid over-killing robots
            return ['attack', weakest_adjacent_enemy.location]
        elif len(adjacent_enemies) >= suicide_threshold:
            return ['suicide']
        
        #not using this priority method because it breaks on the server for some reason
        def byroboidhas_priority(): # if i'm a newer bot, I have priority
            for loc,bot in adjacent_to_target_friendlies.items():
                their_target_pos = rg.toward(loc, weakest_enemy.location)
                # check if bots would collide
                if their_target_pos == target_pos:
                    if self.robot_id > bot.robot_id:
                        return False
            return True

        def has_priority(): # if i'm more bottom or more to the right, i'll take priority
            for loc,bot in adjacent_to_target_friendlies.items():
                their_target_pos = rg.toward(loc, weakest_enemy.location)
                # check if bots would collide
                if their_target_pos == target_pos:
                    if self.location[0] < loc[0] or self.location[1] < loc[1]:
                        #don't move then, do something else
                        return False
            return True

        if self.location != target_pos and has_priority():
            if 'obstacle' not in rg.loc_types(target_pos):
                adjacent_to_target_enemies = self.get_adjacent_robots_to(target_pos, game, operator.__ne__)
                # if len(adjacent_to_target_enemies) <= 1 or len(adjacent_to_target_enemies) >= 3:
                return ['move', target_pos]
        
        #if we couldn't decide to do anything else, just guard
        return self.guard()
    
    def toward(curr, dest):
        if curr == dest:
            return curr

        x0, y0 = curr
        x, y = dest
        x_diff, y_diff = x - x0, y - y0

        if abs(x_diff) < abs(y_diff):
            return (x0, y0 + y_diff / abs(y_diff))
        elif abs(x_diff) == abs(y_diff):
            # BROKEN FIX
            return (0, 0)
        else:
            return (x0 + x_diff / abs(x_diff), y0)

    def guard(self):
        return ['guard']
    
    def get_all_robots(self, game, player_comparator=None):
        def generate():
            for loc,bot in game.get('robots').items():
                if player_comparator == None or player_comparator(self.player_id, bot.player_id):
                    yield (loc, bot)

        return dict(generate())

    def get_adjacent_robots_to(self, some_location, game, player_comparator=None):
 
        def generate():
            for loc,bot in game.get('robots').items():
                if rg.wdist(loc, some_location) <= 1:
                    if player_comparator == None or player_comparator(self.player_id, bot.player_id):
                        yield (loc, bot)
 
        return dict(generate())
            
    def get_adjacent_robots(self, game, player_comparator=None):
        return self.get_adjacent_robots_to(self.location, game, player_comparator)
