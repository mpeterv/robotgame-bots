# Sunguard by Sebsebeleb
# http://robotgame.org/viewrobot/4082

import rg
import euclid as eu

CRITICAL_HP = 11
ATTACK_DAMAGE = 10
SUICIDE_DAMAGE = 15
CHARGE_TIME = 87
IDEAL_FLEE = 4  # The best distance from middle if fleeing

class Robot:
    """
    Strategy:
        when spawned, move out from spawn. Then act based on priorities.
        If there is an adjacent ally in a spawn location that would move to this robots location, make way for it.
        If there are enemies adjacent, attack;
            if an enemy is surrounded by multiple enemies, priority it.
            Otherwise, prioritize the one with least hp.
        Else, move;
            if we are out of order in the spinning, wait for a spot
            if we are at low hp, start moving clockwise instead.
            else, move counter-clockwise unless blocked by ally.
    """
    def act(self, game):
        if "spawn" in rg.loc_types(self.location):
            s = sanitize(['move', rg.toward(self.location, rg.CENTER_POINT)])
            return s

        adjacent_enemies = []
        for loc, bot in game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    allies = 0
                    #Find out how many allies are around this enemy
                    for nloc, nbot in game.get('robots').items():
                        if bot.get("player_id") == self.player_id and rg.dist(loc, nloc) <=1:
                            allies = allies + 1
                    adjacent_enemies.append([loc, bot, allies])
            else:
                if "spawn" in rg.loc_types(bot.get("location")): #The friendly wants to get out of spawn, make way for it
                    r = Robot.move(self, game)
                    if r and rg.toward(bot.get("location"), rg.CENTER_POINT) == r[1]:
                            return sanitize(['move', rg.toward(self.location, rg.CENTER_POINT)])
        if adjacent_enemies and self.hp >= CRITICAL_HP:
            if len(adjacent_enemies) * ATTACK_DAMAGE > self.hp: # They can kill me! lets flee!
                return sanitize(self.flee(game))
            adjacent_enemies.sort(key= lambda x: (x[2], x[1].get("hp")))
            return sanitize(['attack', adjacent_enemies[0][0]])
        elif adjacent_enemies and self.hp < CRITICAL_HP:
            return sanitize(self.flee(game))
        else:
            r = Robot.move(self, game)

            if not r:
                return ["guard"]
            
            #Check if allied damaged bots will move to our destination, and if so, let them
            move = True
            for loc, bot in game.get('robots').items():
                if bot.get("player_id") == self.player_id and not bot.location == self.location:
                    if rg.dist(loc, r[1]) <= 1:
                        if Robot.get_destination(bot, game) == r[1]: #our destination matches, let them come
                            if bot.get("hp") < CRITICAL_HP:
                                return ["guard"]
                            else: # Figure out who should be given highest movement priority (based on which one is furthest from middle, or who has lowest hp in tiebreaker)
                                prio = rg.dist(self.location, rg.CENTER_POINT)
                                prio_o = rg.dist(bot.location, rg.CENTER_POINT)

                                if prio == prio_o: #Tie
                                    if self.hp >= bot.hp:
                                        move = True
                                    else:
                                        move = False
                                elif prio > prio_o:
                                    move = True
                                else:
                                    move = False
            if not move:
                return ["guard"]
            else:
                return sanitize(r) or ["guard"]

    def flee(self, game):
        #Make a priority list of the nearby tiles
        directions = ((1, 0), (0, -1), (-1, 0), (0, 1))
        possible_dests = [tuple(eu.Vector2(*self.location) + eu.Vector2(*d)) for d in directions]
        adj_enemy_hp = 0
        adj_ally_hp = 0 
        # Firstly, remove blocked desitnations
        for dest in possible_dests:
            if "invalid" in rg.loc_types(dest):
                possible_dests.remove(dest)
            else:
                for loc, bot in game.get("robots").items():        
                    if bot.player_id == self.player_id:
                        adj_ally_hp += max(bot.hp, SUICIDE_DAMAGE)
                    else:
                        adj_enemy_hp += max(bot.hp, SUICIDE_DAMAGE)

                    if dest == loc:
                        possible_dests.remove(dest)

        if not possible_dests: #We cant flee, lets make the best out of this
            if adj_enemy_hp > adj_ally_hp * 1.2:
                return ["suicide"]
            else:
                return ["guard"]
        else:
            
            if len(possible_dests) > 1:
                # calculate the best fleeing destination
                # Calculation is as following, higher is worse
                #     0 points given for empty adjacent scores
                #         However, if it is a spawn point its given points based on how close it is to next spawn
                #           99 points added if spawn next turn
                #           otherwise 4 points added for each turn close it is to next spawn
                #     5 points added for adjacent squars with enemies in them
                #     2 points added for adjacent squares with allies in them
                #     points added depending on how close it is to center, being perfectly in the middle between center and outside is the best
                for d in possible_dests:
                    prio_dests = []
                    prio = 0

                    for adj in get_adjacent(d):
                        if adj in game["robots"].keys(): #it is empty
                            bot = game["robots"][adj]
                            if bot.player_id != self.player_id:
                                prio += 5
                            else:
                                prio += 2
                    
                    if "invalid" in rg.loc_types(d): #This option isnt even possible so remove it
                        continue
                    if "spawn" in rg.loc_types(d):
                        to_spawn =  10 - (game["turn"] % 10)
                        if to_spawn == 1: #spawn next turn, avoid!
                            prio += 99
                        else:
                            prio += to_spawn * 4

                    dist = rg.wdist(d, rg.CENTER_POINT)
                    prio += abs(IDEAL_FLEE - dist)

                    prio_dests.append((d, prio))

                    if prio_dests:
                        best = sorted(prio_dests, key = lambda x: x[1])
                        return sanitize(["move", best[0][0]])
                    else:
                        return ["guard"] #temporary


            else:
                return sanitize(["move", possible_dests[0]])

    @staticmethod
    def move(bot, game):
        x, y = bot.location
        RIGHT, UP, LEFT, DOWN = (1, 0), (0, -1), (-1, 0), (0, 1)
        prio = ()
        result = False

        if rg.locs_around(tuple(bot.location), filter_out=('invalid', 'obstacle', 'normal')): #We are out of order
            return False
        
        if x <= 9 and y > 9: #lower left quadrant; moving right and down priority
            if bot.hp >= CRITICAL_HP:
                prio = (DOWN, RIGHT, UP, LEFT)
            else:
                prio = (LEFT, UP, RIGHT, DOWN)
        elif x > 9 and y >= 9: #lower right; right and up
            if bot.hp >= CRITICAL_HP:
                prio = (RIGHT, UP, LEFT, DOWN)
            else:
                prio = (DOWN, LEFT, UP, RIGHT)
        elif x > 9 and y <= 9: #upper right; up and left
            if bot.hp >= CRITICAL_HP:
                prio = (UP, LEFT, DOWN, RIGHT)
            else:
                prio = (RIGHT, DOWN, LEFT, UP)
        elif x <= 9 and y <= 9: #upper left; left and down
            if bot.hp >= CRITICAL_HP:
                prio = (LEFT, DOWN, RIGHT, UP)
            else:
                prio = (UP, RIGHT, DOWN, LEFT)
        else:
            prio = (UP,)

        for d in prio:
            dest = (x + d[0], y + d[1])
            occupied = False
            for loc, nbot in game.get('robots').items():
                if bot.hp >= CRITICAL_HP and nbot.hp < CRITICAL_HP and nbot.get("location") == dest:
                    continue
            if occupied: #if it is occupied by an ally, check for a less prioritized move, but if not, try moving anyway
                result = ["move", dest]
                continue
            elif "spawn" in rg.loc_types(dest) or "invalid" in rg.loc_types(dest):
                continue
            elif bot.hp < CRITICAL_HP:
                x2 = dest[0] + d[0]
                y2 = dest[1] + d[1] # Also check the tile after, so we go in the second row instead
                if "spawn" in rg.loc_types((x2,y2)):
                    continue
                else:
                    result = ["move", dest]
            else:
                result = ["move", dest]
                break
        return result


    @staticmethod
    def get_destination(bot, game):
        """Returns the direction the bot will move (if it moves). Does not consider if the bot will move or not"""
        dest = Robot.move(bot, game)
        dest = dest and dest[1]
        return dest

def get_adjacent(location):
    directions = ((1, 0), (0, -1), (-1, 0), (0, 1))
    adj = (tuple(eu.Vector2(*location) + eu.Vector2(*d)) for d in directions)
    return adj

def sanitize(command):
    if len(command) == 2:
        return [command[0], tuple(command[1])]
    else:
        return command
