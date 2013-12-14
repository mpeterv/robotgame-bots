# Stalins beard by sne11ius

################################################################################
###
### Stalins beard: http://robotgame.org/viewrobot/6606
###
### If you make improvements to the code, feel free to submit pull requests ;)
###
### https://github.com/sne11ius/stalins_beard
###
### There are several wtfs in this code, but right now, it seems to stay at the
### lover top 10.
###
################################################################################

import rg
import sys
import numpy as np
from copy import deepcopy
from random import choice
#from profilehooks import profile

class Robot:

    def __init__(self):
        self.current_turn = -1
        self.gamestate = {}
        self.historic_moves = []
        self.current_moves = None
        #self.computed_paths = []
        #self.act_called = 0;
        
    #def __del__(self):
    #    print 'total paths computed: ' + str(len(self.computed_paths))
    #    print 'calls to act: ' + str(self.act_called)
    #    print 'path / act: ' + str(len(self.computed_paths) / self.act_called)
    #    total_length = 0
    #    for path in self.computed_paths:
    #        total_length += len(path)
    #    print 'average path length: ' + str(total_length / len(self.computed_paths))

    #@profile    
    def act(self, game):
        #self.act_called += 1
        enemy_cell = np.inf
        friendly_cell = np.inf
        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
        all_directions = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))
        future_enemies = ((-1, -1), (-1, 1), (1, 1), (1, -1), (-2, -2), (-2, 0), (-2, 2), (0, 2), (2, 2), (2, 0), (2, -2), (0, -2))
        spawns = [(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17)]
        max_path_length = 6
        
        def init_gamestate():
            self.gamestate['enemies'] = {}
            self.gamestate['robots'] = {}
            for loc, bot in game.get('robots').items():
                if bot.get('player_id') == self.player_id:
                    self.gamestate['robots'][loc] = bot
                else:
                    self.gamestate['enemies'][loc] = bot
        
        def add(loc1, loc2):
            return (loc1[0] + loc2[0], loc1[1] + loc2[1])
        
        def init_obstacles():
            self.obstacles = np.ones((19, 19)) * np.nan
            for i in range(19):
                for j in range(19):
                    if 'invalid' in rg.loc_types((i, j)) or 'obstacle' in rg.loc_types((i, j)):
                        self.obstacles[i, j] = np.inf
            for _, bot in game.get('robots').items():
                self.obstacles[tuple(bot["location"])] = enemy_cell if bot["player_id"] != self.player_id else friendly_cell
        
        def get_center(bot):
            centers = [(9, 4), (14, 9), (9, 14), (4, 9)]
            # centers = [(9, 4), (9, 14)]
            min_distance = sys.maxint
            center = centers[0]
            for c in centers:
                dist = rg.wdist(bot.location, c)
                if dist < min_distance:
                    min_distance = dist 
                    center = c
            return center
        
        def compute_grid(bot):
            grid = deepcopy(self.obstacles)
            grid[bot.location] = 0
            k = 0
            next_sites = [bot.location]
            while 0 != len(next_sites):
                new_next_sites = []
                k += 1
                if k > max_path_length:
                    break
                for site in next_sites:
                    for direction in directions:
                        coord = tuple(add(direction, site))
                        if np.isnan(grid[coord]):
                            grid[coord] = k
                            new_next_sites.append(coord)
                next_sites = new_next_sites
            return grid
        
        def update_obstacles(obstacle):
            if obstacle is None:
                return
            self.obstacles[obstacle] = np.inf

        def has_low_hp(bot):
            return 11 > bot.hp
        
        def is_save(loc):
            if loc in spawns:
                return False
            arounds = rg.locs_around(loc)
            num_enemies = len(filter(lambda x: x in self.gamestate.get('enemies'), arounds))
            num_friends = len(filter(lambda x: x in self.gamestate.get('robots'), arounds))
            panick_even_more = False
            if (0 == num_enemies and 0 < num_friends):
                rnd = np.random.rand()
                panick_even_more = True if rnd > 0.6 else False
            if 0 != num_enemies:
                return False
            return not panick_even_more
        
        def find_escape(grid, loc):
            arounds = rg.locs_around(loc, filter_out = ['invalid', 'obstacle'])
            arounds = filter(lambda x: not enemy_cell == grid[x] and not friendly_cell == grid[x], arounds)
            min_enemies = 20
            best_pos = None
            for around in arounds:
                num_enemies = count_occupied(grid, around)
                if num_enemies < min_enemies:
                    min_enemies = num_enemies
                    best_pos = around
            return best_pos
        
        def find_random_safe_loc(loc, grid):
            arounds = filter(lambda x: not x in spawns and 0 == count_enemies(x) and not np.inf == grid[x], rg.locs_around(loc, filter_out = ['invalid', 'obstacle']))
            if 0 == len(arounds):
                return None
            return choice(arounds)
        
        def panick(bot, grid):
            if is_save(bot.location):
                attack_loc = find_maybe_attack_loc(bot)
                if attack_loc is not None:
                    return ['attack', attack_loc]
                # go somewhere else
                random_safe_loc = find_random_safe_loc(bot.location, grid)
                if (random_safe_loc is not None):
                    return ['move', random_safe_loc]
                return ['guard']
            escape_loc = find_escape(grid, bot.location)
            if escape_loc is not None:
                return ['move', escape_loc]
            num_enemies = count_enemies(bot.location)
            if num_enemies * 9 > self.hp:
                return ['suicide']
            attack_loc = find_attack_loc(bot)
            if attack_loc is not None:
                return ['attack', attack_loc]
            return ['guard']
        
        #def pprint(grid):
        #    s = [[str(e) for e in row] for row in grid]
        #    lens = [len(max(col, key=len)) for col in zip(*s)]
        #    fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        #    table = [fmt.format(*row) for row in s]
        #    print '\n'.join(table)

        def find_path(bot, grid, loc):
            if np.isnan(grid[loc]) or np.isinf(grid[loc]):
            #if np.isnan(grid[loc]) or np.isinf(grid[loc]) or enemy_cell == grid[loc] or friendly_cell == grid[loc]:
                return None
            k = grid[loc]
            path = [loc]
            while not bot.location == path[0] and k > 1:
                l = path[0]
                nbs = filter(lambda x: not x[0] < 0 and not x[1] < 0 and not x[0] > 18 and not x[1] > 18 and not x in path, [tuple(add(l, d)) for d in directions])
                l = nbs[np.nanargmin([grid[nb] for nb in nbs])]
                path.insert(0, l)
                k += -1
            if 0 == len(path):
                return None
            #self.computed_paths.append(path)
            return path
        
        def find_paths(bot, grid, enemy):
            arounds = rg.locs_around(enemy.location, filter_out = ['invalid', 'obstacle'])
            paths = []
            for target in arounds:
                path = find_path(bot, grid, target)
                if path is not None:
                    paths.append((target, path))
            return sorted(paths, key=lambda x: len(x[1]))
        
        def find_move(bot, grid):
            all_paths = []
            for _, enemy in self.gamestate.get('enemies').items():
                for target_loc, path in find_paths(bot, grid, enemy):
                    all_paths.append((enemy, target_loc, path))
            sorted_paths = sorted(all_paths, key=lambda x: x[0].hp * len(x[2]))
            if 0 == len(sorted_paths):
                return None
            if 0 == len(sorted_paths[0][2]):
                return None
            return sorted_paths[0][2][0]
            
        def count_enemies(loc):
            return len(filter(lambda x: x in self.gamestate.get('enemies'), [add(loc, l) for l in directions]))
            
        def count_occupied(grid, loc):
            occupied = 0
            for l in filter(lambda x: not x[0] < 0 and not x[1] < 0 and not x[0] > 18 and not x[1] > 18, [tuple(add(loc, d)) for d in all_directions]):
                if (np.inf == grid[l]):
                    occupied += 1
            return occupied
        
        def compute_move_order(bot):
            grid = compute_grid(bot)
            if has_low_hp(bot) or 1 < count_enemies(bot.location):
                return panick(bot, grid)
            attack_loc = find_attack_loc(bot)
            if attack_loc is not None:
                return ['attack', attack_loc]
            move = find_move(bot, grid)
            if move is not None:
                return ['move', move]
            path_to_center = find_path(bot, grid, get_center(bot))
            if path_to_center is not None:
                if bot.location == path_to_center[0]:
                    attack_loc = find_maybe_attack_loc(bot)
                    if attack_loc is not None:
                        return ['attack', attack_loc]
                    random_safe_loc = find_random_safe_loc(bot.location, grid)
                    if (random_safe_loc is not None):
                        return ['move', random_safe_loc]
                return ['move', path_to_center[0]]
            return ['move', rg.toward(bot.location, get_center(bot))]
            #return ['guard']
        
        def find_attack_loc(bot):
            weakest_hp = 100
            attack_loc = None
            for loc, enemy in self.gamestate.get('enemies').items():
                if rg.dist(loc, bot.location) <= 1:
                    if attack_loc is None or weakest_hp > enemy.get('hp'):
                        attack_loc = loc
            return attack_loc

        def find_maybe_attack_loc(bot):
            possible_locs = filter(lambda x: not x[0] < 0 and not x[1] < 0 and not x[0] > 18 and not x[1] > 18, [tuple(add(bot.location, d)) for d in future_enemies])
            locs = filter(lambda x: x in self.gamestate.get('enemies'), possible_locs)
            if 0 == len(locs):
                return None
            enemies = sorted(map(lambda x: self.gamestate.get('enemies')[x], locs), key = lambda x : x.hp)
            return rg.toward(bot.location, enemies[0].location)

        def get_obstacle(move_order):
            if move_order[0] in ['move', 'attack']:
                return move_order[1]
            return None

        def compute_single_move(bot):
            move_order = compute_move_order(bot)
            obstacle = get_obstacle(move_order)
            return {'move_order': move_order, 'obstacle': obstacle}

        if self.current_turn != game.get('turn'):
            if self.current_moves is not None:
                self.historic_moves.insert(0, self.current_moves)
            self.current_moves = {}
            init_gamestate()
            init_obstacles()
            self.current_turn = game.get('turn')
        move_info = compute_single_move(self)
        update_obstacles(move_info.get('obstacle'))
        order = move_info.get('move_order')
        if 0 != len(self.historic_moves):
            maybe_last_order = self.historic_moves[0].get(self.location)
            if maybe_last_order is not None:
                if maybe_last_order[0] == order and 'move' == order[0] and maybe_last_order[1] == self.hp + 5:
                    # bumped into enemy last round and about to do the same mistake? no, attack the position instead
                    order = ['attack', order[1]]
        self.current_moves[self.location] = (order, self.hp)
        return order
