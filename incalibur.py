from rg import *
from random import random

class Robot:
    def __init__(self):
        self.robots = {}

    def toward2(self, curr, dest):
        if curr == dest:
            return curr
        good_sqs = self.legit_around(curr)
        x0, y0 = curr
        x1, y1 = dest
        dx, dy = x1 - x0, y1 - y0
        x_mov = (x0 + cmp(dx, 0), y0)
        y_mov = (x0, y0 + cmp(dy, 0))
        if random() > abs(dx) / float(abs(dx) + abs(dy)):
            return y_mov if y_mov in good_sqs else x_mov
        return x_mov if x_mov in good_sqs else y_mov

    def legit_around(self, loc, omit_spawn=True):
        fil = ['invalid', 'obstacle']
        if omit_spawn and self.turn % 10 == 0:
            fil.append('spawn')
        return locs_around(loc, filter_out=tuple(fil))

    def toward_free(self, dest):
        for p in sorted(self.legit_around(self.location, omit_spawn=False), key=lambda x: wdist(x, dest)):
            if self.occ(p) == 'free':
                return p
        return self.toward2(self.location, dest)

    def safest(self, loc):
        return sorted([loc for loc in self.legit_around(loc) if self.occ(loc) == 'free'], key=lambda x: self.adj_enemies(x))

    def freest(self, loc):
        return sorted([loc for loc in self.legit_around(loc) if self.occ(loc) == 'free'], key=lambda x: self.free_around(x), reverse=True)

    def adj_enemies(self, loc):
        return sum(1 for i in locs_around(loc) if self.occ(i) == 'enemy')

    def adj_allies(self, loc):
        return sum(1 for i in locs_around(loc) if self.occ(i) == 'friend')

    def free_around(self, loc):
        return sum(1 for i in self.legit_around(loc) if self.occ(i) == 'free')

    def allies_within(self, loc, d):
        return sum(1 for i in self.robots if self.occ(i) == 'friend' and wdist(i, loc) <= d)

    def occ(self, loc):
        if loc in self.robots:
            if self.robots[loc].player_id == self.player_id:
                return 'friend'
            return 'enemy'
        return 'free'

    def path(self, curr, dest):
        que = [dest]
        grid = [[100]*18 for i in xrange(18)]
        grid[dest[0]][dest[1]] = 0
        while que:
            loc = que.pop()
            for i in self.legit_around(loc):
                if i not in self.robots:
                    if grid[loc[0]][loc[1]] + 1 < grid[i[0]][i[1]]:
                        grid[i[0]][i[1]] = grid[loc[0]][loc[1]] + 1
                        que.append(i)
        return min(self.legit_around(curr), key=lambda x: grid[x[0]][x[1]])


    def act(self, game):
        my_loc = self.location
        self.robots = robots = game.robots
        self.turn = game['turn']
        to_c = self.toward_free(CENTER_POINT)

        free_sqs = [loc for loc in self.legit_around(my_loc) if self.occ(loc) == 'free']
        enemies = [loc for loc in robots if self.occ(loc) == 'enemy']
        allies = [loc for loc in robots if self.occ(loc) == 'friend' and loc != my_loc]

        if len(enemies) == 0:
            print "no enemies!, {} moving to {}".format(my_loc, to_c)
            if my_loc == to_c:
                return ['guard']
            return ['move', to_c]
        if not free_sqs and self.hp < 10 * self.adj_enemies(my_loc):
            print "{} suiciding".format(my_loc)
            return ['suicide']

        # escape spawn
        if 'spawn' in loc_types(my_loc):
            if game['turn'] % 10 == 0:
                if not free_sqs:
                    print "{} suiciding".format(my_loc)
                    return ['suicide']
                print "{} spawn turn, moving to safe square {}".format(my_loc, min(free_sqs, key=lambda x: self.adj_enemies(x) + self.adj_allies(x)))
                return ['move', min(free_sqs, key=lambda x: self.adj_enemies(x) + self.adj_allies(x))]
            if game['turn'] % 10 == 9 and wdist(my_loc, CENTER_POINT) == 12:
                print "{} on corner, moving to safe square {}".format(my_loc, self.safest(my_loc)[0])
                return ['move', self.safest(my_loc)[0]]
            if game['turn'] % 10 == 9 and toward(my_loc, CENTER_POINT) in robots:
                print "{} moving to safe square {}".format(my_loc, self.path(my_loc, CENTER_POINT))
                return ['move', self.path(my_loc, CENTER_POINT)]
            #if game['turn'] % 10 == 9 and 

        # trap on spawn
        if game['turn'] % 10 == 0:
            for i in locs_around(my_loc):
                if self.occ(i) == 'enemy' and 'spawn' in loc_types(i):
                    print "{} spawn turn, trap guarding".format(my_loc)
                    return ['guard']
                for j in locs_around(i):
                    if self.occ(j) == 'enemy' and 'spawn' in loc_types(j) and 'spawn' not in loc_types(i):
                        for ally in allies:
                            if 'spawn' in loc_types(ally) and i == toward(ally, CENTER_POINT):
                                return ['guard']
                        print "{} trapping {} from 2 away".format(my_loc, j)
                        return ['move', i]
        if game['turn'] % 10 == 9:
            for i in self.legit_around(my_loc):
                if 'spawn' not in loc_types(i):
                    for j in locs_around(i):
                        if self.occ(j) == 'enemy' and 'spawn' in loc_types(j) and self.free_around(j) <= self.allies_within(j, 2):
                            for ally in allies:
                                if 'spawn' in loc_types(ally) and i == toward(ally, CENTER_POINT):
                                    return ['guard']
                            print "{} trapping {} from 2 away".format(my_loc, j)
                            return ['move', i]

        closest_enemy = min(enemies, key=lambda e: wdist(e, my_loc))
        if wdist(my_loc, closest_enemy) == 1:
            if self.hp < 10 * self.adj_enemies(my_loc) and self.free_around(my_loc) > 0:
                print "{} low hp, moving to {}".format(my_loc, self.freest(my_loc)[0])
                return ['move', self.freest(my_loc)[0]]
            print "{} attacking {}".format(my_loc, closest_enemy)
            if 'spawn' in loc_types(closest_enemy):
                if toward(closest_enemy, CENTER_POINT) == my_loc:
                    print "{} trapping {}".format(my_loc, closest_enemy)
                    return ['guard']
                print "{} moving to trap {}".format(my_loc, closest_enemy)
                return ['move', self.path(my_loc, toward(closest_enemy, CENTER_POINT))]
            return ['attack', closest_enemy]
        if wdist(my_loc, closest_enemy) == 2:
            if dist(my_loc, closest_enemy) == 2:
                if toward(my_loc, closest_enemy) in robots:
                    print "{} exactly 2 away, moving towards {}".format(my_loc, closest_enemy)
                    return ['move', self.path(my_loc, closest_enemy)]
            print "{} not exactly 2 away, attacking {}".format(my_loc, closest_enemy)
            return ['attack', self.toward_free(closest_enemy)]
        default_move = self.path(my_loc, closest_enemy)
        for ally in allies:
            if 'spawn' in loc_types(ally) and default_move == self.toward2(ally, CENTER_POINT):
                return ['guard']
        if game['turn'] % 10 == 9 and wdist(default_move, CENTER_POINT) == 12:
            return ['guard']
        print "{} default, moving toward {}".format(my_loc, closest_enemy)
        return ['move', self.path(my_loc, closest_enemy)]
