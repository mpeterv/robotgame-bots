# Ghoulinator V by ???
# http://robotgame.org/viewrobot/1083

import rg

positions = []
attacks = {}
lastmoves = {}
newmoves = {}
lastturn = 0

class Robot:
    def act(self, game):
        global positions
        global lastturn
        global attacks
        global newmoves
        global lastmoves

        # Reset the hive mind if this is a new turn
        if lastturn < game.get('turn'):
            lastturn = game.get('turn')
            positions = []
            attacks = {}
            lastmoves = newmoves
            newmoves = {}

        # Generate a list of targets
        #   1. Sort by whether it's an enemy
        #   2. Sort by the distance
        #   3. Sort by its remaining health
        targets = sorted(game.get('robots').items(), key = lambda (k, v): (v.get('player_id') == self.player_id, rg.wdist(self.location, k), v.get('hp')))

        # Did we even find any targets?
        if len(targets) == 0:
            return ['guard']

        # Are we low on health?
        #if self.hp <= 20:
            # Is it mathematically favourable to just blow up at this point?
            #if len(filter(lambda (k, v): rg.wdist(self.location, k) == 1 and v.get('player_id') != self.player_id, targets)) > 2:
                #return ['suicide']

        upto = 0
        inrange = len(filter(lambda (n, x): rg.wdist(n, self.location), targets))

        # For each target in the order we sorted them
        for (k, v) in targets:
            # Is it an enemy?
            if v.get('player_id') != self.player_id:
                # Is it in range?
                if rg.wdist(k, self.location) == 1:
                    upto += 1

                    # Check if the key exists in the dictionary of targets
                    if not k in attacks:
                        attacks[k] = 0;

                    # Is it worth attacking the target?
                    if v.get('hp') > attacks[k]:
                        attacks[k] += 8
                        return ['attack', k]

                    # Otherwise, we should probably choose a different target
                    if upto <= inrange:
                        continue

            # Otherwise, we're moving, so filter out squares around if they are obstacles or invalid
            around = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))

            # Filter them out if we can't find a way to get closer to them without doing useless work
            around = filter(lambda x: rg.wdist(x, k) <= rg.wdist(self.location, k), around)

            # And once again filter them out to see if they are taken
            around = filter(lambda x: not x in positions, around)

            # And filter it to see that we aren't being baited
            for (k, v) in targets:
                if v.get('player_id') != self.player_id:
                    for x in around[:]:
                        if rg.wdist(x, k) == 1:
                            if not k in attacks:
                                return ['attack', x]
                            else:
                                around.remove(x)


            # Did this leave us with any squares?
            if len(around) > 0:
                # There are some squares we desire, so let's now sort them and find the closest to target while
                #   being biased to spawn point squares since they are dangerous
                around.sort(key = lambda x: ('spawn' in rg.loc_types(x), rg.wdist(k, x)))

                # Check if someone tried to do this move last round but had a collision
                #if self.location in lastmoves:
                #    if lastmoves[self.location] == around[0]:
                #        # Someone tried this move already and it didn't work out. Maybe we can kill someone trying it
                #        return ['attack', around[0]]

                # After all that we're pretty happy to just move towards it
                positions.append(around[0])
                newmoves[self.location] = around[0]
                return ['move', around[0]]

        # For whatever reason we can't move anywhere so just stay put
        return ['guard']
