# Dulladob 0.1 by Camelot Chess
# http://robotgame.net/viewrobot/7641

import rg

spawn_param = 8 #which turn to we begin bouncing?

suicide_param = 6 #when to blow ourselves up (param*surrounders>hp)?
suicide_fear_param = 6 #which to fear enemies blowing up?

staying_still_bonus = 0.34 #points for staying put
best_center_distance_param = 6 #ideal distance from the center
best_center_distance_weight = 1.01 #points lost for every square off
spawn_weight = 0.34 #points lost being spawn; multiplied by turns since death
adjacent_robot_penalty = 1 #NO NEED TO CHAGE - points lost for adjacent robots
adjacent_friendly_penalty = 0.51 #NO NEED TO CHAGE - points lost for adjacent robots
main_axis_weight = 0.5

#parameters controlling how much hp we need to pin an enemy to spawn. Arguably
#should depend on their hp, and/or happen before running, particularly on first
#turn.
hp_to_pin = {}
hp_to_pin[0] = 6
hp_to_pin[1] = 11
hp_to_pin[2] = 51
hp_to_pin[3] = 51
for x in range(4,11):
    hp_to_pin[x] = 51

canonical_spawn_locs = []
for x in range(10):
    for y in range(10):
        if 'spawn' in rg.loc_types((x,y)):
            canonical_spawn_locs.append((x,y))
#TTD:
# - vary some priorities

one_robots = []
two_robots = []

verbose = 0

def urgency(bot1, game):
    return 100000 * rg.dist(bot1.location, rg.CENTER_POINT) + 100 * bot1.hp + bot1.location[0] 

def greater(bot1, bot2, game):
    if(urgency(bot1, game) > urgency(bot2, game)): return 1
    if(urgency(bot2, game) > urgency(bot1, game)): return 0
    #deliberately runs off the edge; this should be impossible.

def valid(move):
    types = rg.loc_types(move)
    if 'invalid' in types: return 0
    if 'obstacle' in types: return 0
    return 1

def not_spawn(move):
    types = rg.loc_types(move)
    if 'spawn' in types: return 0
    return 1

def spawn(move):
    return 1 - not_spawn(move)

def surrounded_spawn(move):
    for loc in rg.locs_around(move, filter_out=('obstacle', 'invalid', 'spawn')):
        return 0
    return 1

def equal(bot1, bot2):
    if (bot1.location == bot2.location): return 1
    return 0

def surrounders(this_robot, game, loc):
    number_found = 0
    for loc2 in rg.locs_around(loc):
        if(loc2 in game.robots):
            bot2 = game.robots[loc2]
            if bot2.player_id != this_robot.player_id: number_found += 1
    #print "surrounders found ", loc, game
    return number_found

def distance_from_spawn(square):
    #canonise the square
    canonical_x = square[0]
    canonical_y = square[1]
    if(canonical_x > 9): canonical_x = 18-canonical_x
    if(canonical_y > 9): canonical_y = 18-canonical_y
    if(canonical_x > canonical_y):
        canonical_square = (canonical_y, canonical_x)
    else:
        canonical_square = (canonical_x, canonical_y)
    distance = 10
    for loc in canonical_spawn_locs:
        if rg.wdist(loc, canonical_square) < distance:
            distance = rg.wdist(loc,canonical_square)
    return distance                         

def move_towards_if_no_ally(loc, dest, game, illegals):
    xmove = towardsx_if_not_spawn(loc, dest)
    ymove = towardsy_if_not_spawn(loc, dest)
    if(xmove != 'no_move' and (not xmove in illegals) and (not xmove in game.robots)): xvalid = 1
    else: xvalid = 0
    if(ymove != 'no_move' and (not ymove in illegals) and (not ymove in game.robots)): yvalid = 1
    else: yvalid = 0
    if(xvalid == 1): return xmove
    if(yvalid == 1): return ymove
    return 'no_action'

def towardsy_if_not_spawn(loc, dest):
    if(dest[1] > loc[1] ):
        tentative_move = (loc[0], loc[1]+1)
        if valid(tentative_move):
            if not_spawn(tentative_move) or spawn(loc):
                return tentative_move
    if(dest[1] < loc[1]):
        tentative_move = (loc[0], loc[1]-1)
        if valid(tentative_move):
            if not_spawn(tentative_move) or spawn(loc):
                return tentative_move
    return 'no_move'

def towardsx_if_not_spawn(loc, dest):
    if(dest[0] > loc[0]):
        tentative_move = (loc[0]+1, loc[1])
        if valid(tentative_move):
            if not_spawn(tentative_move) or not not_spawn(loc):
                return tentative_move
    if(dest[0] < loc[0]):
        tentative_move = (loc[0]-1, loc[1])
        if valid(tentative_move):
            if not_spawn(tentative_move) or not not_spawn(loc):
                return tentative_move
    return 'no_move'

def towardy(loc, dest):
    if(dest[1] > loc[1] ):
        tentative_move = (loc[0], loc[1]+1)
        if valid(tentative_move):
                return tentative_move
    if(dest[1] < loc[1]):
        tentative_move = (loc[0], loc[1]-1)
        if valid(tentative_move):
                return tentative_move
    return 'no_move'

def towardx(loc, dest):
    if(dest[0] > loc[0]):
        tentative_move = (loc[0]+1, loc[1])
        if valid(tentative_move):
            return tentative_move
    if(dest[0] < loc[0]):
        tentative_move = (loc[0]-1, loc[1])
        if valid(tentative_move):
             return tentative_move
    return 'no_move'

def move_towards_either_axis (loc, dest, turn):
    targetx = towardsx_if_not_spawn(loc, dest)
    targety = towardsy_if_not_spawn(loc, dest)
    if targetx == 'no_move': return targety
    if targety == 'no_move': return targetx
    if turn%2 == 0: return targetx
    else: return targety

def destruct_if_doomed_us(this_robot, game, illegals):
    if (this_robot.location in illegals): return 'no_action'
    if (surrounders(this_robot, game, this_robot.location)*suicide_param > this_robot.hp): return ['suicide']
    return 'no_action'

def destruct_if_doomed_enemy(this_robot, game):
    if (surrounders(this_robot, game, this_robot.location)*suicide_fear_param > this_robot.hp): return ['suicide']
    return 'no_action'
            
def attack_moving_enemy(this_robot, game, illegals):
    if (this_robot.location in illegals): return 'no_action'
    square_dictionary = {}
    for square in rg.locs_around(this_robot.location):
        square_dictionary[square] = 0
        if square in game.robots:
            square_dictionary[square] -= 40 #don't fire if our robot is there, they probably won't move there
    for bot in two_robots:
        if bot.player_id != this_robot.player_id:
            loc = bot.location
            targetx = towardx(this_robot.location, loc)
            targety = towardy(this_robot.location, loc)
            if targetx != 'no_move':
                square_dictionary[targetx] += 70 - bot.hp - rg.dist(rg.CENTER_POINT, targetx)
            if targety != 'no_move':   
                square_dictionary[targety] += 70 - bot.hp - rg.dist(rg.CENTER_POINT, targety)
    best_score = 0
    best_move = 'no_action'
    for square in rg.locs_around(this_robot.location):
        if square_dictionary[square] > best_score:
            best_score = square_dictionary[square]
            best_move = ['attack', square]
    return best_move

def attack_if_possible(this_robot, game, illegals):
    if (this_robot.location in illegals): return 'no_action'
    besthp = 1000
    bestloc = 'none'
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            if bot.hp < besthp:
                besthp = bot.hp
                bestloc = bot.location
    if(besthp < 1000): return ['attack', bestloc]
    return 'no_action'
                    
def strong_hunt_the_weak(this_robot, game, illegals):
    if(this_robot.hp < 30): return 'no_action'
    weakest_enemy = 20
    best_move = 'no_action'
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            if bot.hp < weakest_enemy:
                weakest_enemy = bot.hp
                if bot.hp <= 5 and (not bot.location in illegals) and (not surrounders(this_robot, game, bot.location) > 1):
                    best_move = ['move', bot.location]
                    weakest_enemy = bot.hp
                elif not this_robot.location in illegals:
                    best_move = ['attack', bot.location]
                    weakest_enemy = bot.hp
    for bot in two_robots:
        if bot.player_id != this_robot.player_id:
            if bot.hp < weakest_enemy:
                targetx = towardsx_if_not_spawn(this_robot.location, bot.location)
                targety = towardsy_if_not_spawn(this_robot.location, bot.location)
                if not (targetx == 'no_move'):
                    if not (targetx in illegals or surrounders(this_robot, game, targetx) > 1):
                        best_move = ['move', targetx]
                        weakest_enemy = bot.hp
                if not (targety == 'no_move'):
                    if not (targety in illegals or surrounders(this_robot, game, targety) > 1):
                        if targetx == 'no_move' or rg.dist(targetx, rg.CENTER_POINT) > rg.dist(targety, rg.CENTER_POINT):
                        	best_move = ['move', targety]
                        	weakest_enemy = bot.hp
    return best_move

def safe(this_robot, loc, game):
    turns_left = 10 - game.turn % 10
    if(turns_left == 10): turns_left = 0
    if(turns_left <= 2 and spawn(loc)): return 0
    for bot in one_robots:
        if(loc == bot.location and bot.player_id != this_robot.player_id):
            return 0
    for bot in two_robots:
        if bot.player_id != this_robot.player_id:
            if rg.wdist(loc, bot.location) == 1:
                return 0
    return 1

def scared(this_robot, game):
    num_surrounders = 0
    scared = 0
    hp = 0
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            num_surrounders += 1
            hp = bot.hp
            last_found = bot
            if(destruct_if_doomed_enemy(bot, game) != 'no_action'):
                scared = 1
    if (num_surrounders > 1):
        scared = 1
    if (hp > this_robot.hp):
        if (surrounders(bot, game, bot.location) == 1) or this_robot.hp < 16:
            scared = 1
    return scared

def run_if_scared_and_safe(this_robot, game, illegals): 
    if not scared(this_robot, game):
        return 'no_action'
    best_distance = 1000
    move = 'no_action'
    for loc in rg.locs_around(this_robot.location, filter_out=('obstacle', 'invalid', 'spawn')):
        if ((not loc in illegals) and safe(this_robot, loc, game) == 1):
            if rg.dist(loc, rg.CENTER_POINT) < best_distance:
                best_distance = rg.dist(loc, rg.CENTER_POINT)
                move = ['move', loc]
    return move

def empty_score(this_robot, loc, game):
    score = 0
    if(verbose > 1): print "here"
    if(this_robot.hp > 25): score -= abs(rg.dist(loc, rg.CENTER_POINT) - best_center_distance_param)*best_center_distance_weight
    else: score -= rg.dist(loc, rg.CENTER_POINT)*best_center_distance_weight
    if(verbose > 1): print "here2"
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        if(loc2 in game.robots):
            if(game.robots[loc2].player_id != this_robot.player_id): score -= adjacent_robot_penalty
            else: score -= adjacent_friendly_penalty
    #if we are trying to run away from spawn, non-spawn adjacent squares with no enemies by them are good, because we need to move
    if(spawn(loc) & game.turn < 91):
        for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
            clear_square = 1
            for loc3 in rg.locs_around(loc2, filter_out=('obstacle', 'invalid', 'spawn')):
                if(loc3 in game.robots and game.robots[loc3].player_id != this_robot.player_id):
                    clear_square = 0
            score += ((game.turn+1) % 10)*spawn_weight*clear_square/2
    if(spawn(loc) & game.turn < 91): score -= ((game.turn+1) % 10)*spawn_weight
    if(surrounded_spawn(loc) & game.turn < 91): score -= (game.turn % 10)*spawn_weight
    return score

def find_empty_space(this_robot, game, illegals):
    loc = this_robot.location
    best_score = empty_score(this_robot, loc, game) + staying_still_bonus
    move = ['guard']
    if(loc in illegals): best_score = -10000
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        score = empty_score(this_robot, loc2, game)
        if(loc2 in illegals): score -= 10000
        if(score > best_score):
            best_score = score
            move = ['move', loc2]
    return move

def pin_to_spawn(this_robot, game, illegals):
    if(game.turn > 95): return 'no_action'
    turns_left = 10 - game.turn % 10
    if(turns_left == 10): turns_left = 0
    if(this_robot.hp < hp_to_pin[turns_left]): return 'no_action'
    loc = this_robot.location
    for bot in one_robots:
        if(bot.player_id != this_robot.player_id):
            loc2 = bot.location
            if spawn(loc2):
                if(not_spawn(loc) and (not loc in illegals)):
                   return ['guard']
    for bot in two_robots:
        if(bot.player_id != this_robot.player_id):
            loc2 = bot.location
            if spawn(loc2):
                block_square = move_towards_either_axis(loc, loc2, game.turn)
                if(block_square == 'no_move'): return 'no_action'
                if(not_spawn(block_square) and (not block_square in illegals)):
                    return ['move', block_square]
    return 'no_action'

def tentative_act(this_robot, game, illegals):
    global one_robots
    global two_robots
    one_robots = []
    two_robots = []
    locx = this_robot.location[0]
    locy = this_robot.location[1]
    for x in range(-2, 3):
        for y in range(-2, 3):
            if (abs(x) + abs(y) in range (1,3)):
                checkx = locx + x
                checky = locy + y
                if ((checkx, checky) in game.robots):
                    bot = game.robots[(checkx,checky)]
                    if (abs(x) + abs(y) == 1):
                        one_robots.append(bot)
                    else: two_robots.append(bot)
    if(verbose): print "current location: ", this_robot.location
    if(verbose > 1): print "bots 1 away: ", one_robots
    if(verbose > 1): print "bots 2 away: ", two_robots
        
    possible_move = strong_hunt_the_weak(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move

    possible_move = run_if_scared_and_safe(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move
    
    possible_move = destruct_if_doomed_us(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move
    
    possible_move = pin_to_spawn(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move
    
    possible_move = attack_if_possible(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move

    if(spawn(this_robot.location)):
        possible_move = find_empty_space(this_robot, game, illegals)
        if(possible_move[0] != 'guard'): return possible_move
  
    possible_move = attack_moving_enemy(this_robot, game, illegals)
    if (possible_move != 'no_action'): return possible_move

    actual_move = find_empty_space(this_robot, game, illegals)
    return actual_move

def empty_score_punish_spawn(this_robot, loc, game):
    score = empty_score(this_robot, loc, game)
    if(spawn(loc)): score -= 100
    if(surrounded_spawn(loc)): score -= 100
    return score

def find_empty_space_punish_spawn(this_robot, game, illegals):
    loc = this_robot.location
    best_score = empty_score_punish_spawn(this_robot, loc, game) + staying_still_bonus
    move = ['guard']
    if(loc in illegals): best_score = -10000
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        score = empty_score_punish_spawn(this_robot, loc2, game)
        if(loc2 in illegals): score = -10000
        if(score > best_score):
            best_score = score
            move = ['move', loc2]
    return move
 
def run_from_spawn(this_robot, game, illegals):
    return find_empty_space_punish_spawn(this_robot, game, illegals)

def at_spawn_after_move(this_robot, move):
    if (move[0] != 'move'): return spawn(this_robot.location)
    else: return spawn(move[1])

def act_with_illegals(this_robot, game, illegals):
    tentative_move = tentative_act(this_robot, game, illegals)
    if(game.turn % 10 < 9 and game.turn % 10 > 0): return tentative_move
    if(game.turn > 95): return tentative_move
    if(not at_spawn_after_move(this_robot, tentative_move)): return tentative_move
    return run_from_spawn(this_robot, game, illegals)

def destination_square(bot, move):
    if(move[0] == 'move'): return move[1]
    else: return bot.location

def act_with_consideration(this_robot, game, illegals):
    bots_to_consider = []
    bots_to_consider.append(this_robot)
    new_bots = []
    new_bots.append(this_robot)
    while(len(new_bots)):      
        last_bots = new_bots
        new_bots = []
        for bot in last_bots:
            locx = bot.location[0]
            locy = bot.location[1]
            for x in range(-2, 3):
                for y in range(-2, 3):
                    if (abs(x) + abs(y) in range (1,3)):
                        checkx = locx + x
                        checky = locy + y
                        if ((checkx, checky) in game.robots):
                            cand = game.robots[(checkx,checky)]
                            if(cand.player_id == this_robot.player_id and greater(cand, bot, game) and (not cand in bots_to_consider)):
                                new_bots.append(cand)
                                bots_to_consider.append(cand)
    if(verbose > 1): print "considering bots:"
    sorted_bots = sorted(bots_to_consider, key= lambda bot: -urgency(bot, game))
    for bot in sorted_bots:
        if(verbose > 1): print "looking at location ", bot.location, ", urgency ", urgency(bot, game)
        move = act_with_illegals(bot, game, illegals)
        square = destination_square(bot, move)
        if(verbose > 1): print "move: ", move, " square taken: ", square
        illegals.add(square)
        if(bot == this_robot):         
            if(verbose > 1): print illegals
            if(verbose > 1): print
            return move

class Robot:  
    def act(self, game):
        return act_with_consideration(self, game, set())
