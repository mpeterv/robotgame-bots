import rg

escapeSquares = []
globTurn = 0

class Robot:

    def act(self, game):

        # reset the escape squares for this turn
        global escapeSquares
        global globTurn
        if globTurn != game.turn:
            globTurn = game.turn
            # refresh list of used escape squares
            escapeSquares = []

        badSpawnLocs = [(3, 3), (3, 15), (15, 3), (15, 15)]
        goodSpawnLocs = [(3, 4), (4, 3), (3, 14), (4, 15), (14, 3), (15, 4), (14, 15), (15, 4), (2, 6), (6, 2), (2, 12), (6, 16), (12, 2), (16, 6), (12, 16), (16, 12)]

        # set the location that would take us towards the centre
        towardCentre=rg.toward(self.location, rg.CENTER_POINT)

        # build info about adjacent and close robots
        adjEnemyCount = 0
        adjEnemyLocs = []
        closeEnemyCount = 0
        closeEnemyLocs = []
        closeEnemyTargets = []
        adjFriendlyCount = 0
        adjFriendlyLocs = []
        closeFriendlyCount = 0
        closeFriendlyLocs = []
        closeFriendlyTargets = []
        nearbyFriendlyCount = 0
        nearbyFriendlyLocs = []
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) == 1:
                    adjEnemyCount += 1
                    adjEnemyLocs = adjEnemyLocs + [loc]
                if rg.wdist(loc, self.location) == 2:
                    closeEnemyCount += 1
                    closeEnemyLocs = closeEnemyLocs + [loc]
                    for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                        for poss in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                            if poss == dest:
                                closeEnemyTargets = closeEnemyTargets + [poss]
            if bot.player_id == self.player_id:
                if rg.wdist(loc, self.location) == 1:
                    adjFriendlyCount += 1
                    adjFriendlyLocs = adjFriendlyLocs + [loc]
                if rg.wdist(loc, self.location) == 2:
                    closeFriendlyCount += 1
                    closeFriendlyLocs = closeFriendlyLocs + [loc]
                    for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                        for poss in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                            if poss == dest:
                                closeFriendlyTargets = closeFriendlyTargets + [poss]
                if rg.wdist(loc, self.location) <= 3:
                    if loc != self.location:
                        nearbyFriendlyCount += 1
                        nearbyFriendlyLocs = nearbyFriendlyLocs + [loc]

        # if it's nearly respawning time...
        if game.turn % 10 in [9, 0] and game.turn != 99:
            # if we're on the edge, move away from spawn locations
            if 'spawn' in rg.loc_types(self.location):
                for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if dest not in game.robots:
                        if dest not in escapeSquares:
                            escapeSquares = escapeSquares + [dest]
                            return ['move', dest]
                # if this isn't possible and we have a spare turn, try a new spawn location
                if game.turn % 10 == 9:
                    if 'spawn' in rg.loc_types(towardCentre):
                        if towardCentre not in game.robots:
                            if towardCentre not in escapeSquares:
                                escapeSquares = escapeSquares + [towardCentre]
                                return ['move', towardCentre]
                # otherwise commit suicide
                if game.turn % 10 == 0:
                    return ['suicide']

        # if it's nearly respawning time...
        if game.turn % 10 in [9, 0] and game.turn != 99:
            # try to bump spawning robots
            for loc in closeEnemyLocs:
                if 'spawn' in rg.loc_types(loc):
                    if game.turn % 10 == 0 or self.hp >= 9:
                        # try to attack the square on its path to the centre
                        for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                            if rg.toward(loc, rg.CENTER_POINT) == dest:
                                if dest not in game.robots:
                                    if dest not in escapeSquares:
                                        escapeSquares = escapeSquares + [dest]
                                        return ['move', dest]
                        # if not, and it's turn 10, try to attack any square it could move to
                        if game.turn % 10 == 0:
                            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                                for poss in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                                    if poss == dest:
                                        if dest not in game.robots:
                                            if dest not in escapeSquares:
                                                escapeSquares = escapeSquares + [dest]
                                                return ['move', dest]

        # if we're next to 3+ enemy bots, and low on health, commit suicide
        if adjEnemyCount >= 3:
            if self.hp <= adjEnemyCount * 9:
                return ['suicide']

        # if we're next to one enemy bot on low health, try to kill it (as long as we're not more likely to die ourselves)
        if adjEnemyCount == 1:
            for loc, bot in game.robots.iteritems():
                if loc in adjEnemyLocs:
                    if bot.hp <= 7 or self.hp >= 10:
                        return ['attack', loc]
                    if bot.hp <= self.hp:
                        return ['attack', loc]
            
        # if we're next to 2 enemy bots, or next to one enemy bot and low on health, run away (but not next to an enemy robot)
        if adjEnemyCount >= 1:
            if self.hp <= 9 or adjEnemyCount >= 2:
                for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if dest not in game.robots:
                        if dest not in closeEnemyTargets:
                            if dest not in escapeSquares:
                                escapeSquares = escapeSquares + [dest]
                                return ['move', dest]
                # allow spawn squares if absolutely necessary and we're not near respawn time
                if game.turn % 10 not in [8, 9, 0] or game.turn in [98, 99]:
                    for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                        if dest not in game.robots:
                            if dest not in closeEnemyTargets:
                                if dest not in escapeSquares:
                                    escapeSquares = escapeSquares + [dest]
                                    return ['move', dest]

        # if we're next to an ally in a spawn square, try to free it up by moving towards the centre
        if 'spawn' not in rg.loc_types(self.location):
            for loc in adjFriendlyLocs:
                if 'spawn' in rg.loc_types(loc):
                    if towardCentre not in game.robots:
                        if towardCentre not in escapeSquares:
                            surplusHP = self.hp
                            for dest in closeEnemyTargets:
                                if dest == towardCentre:
                                    surplusHP -= 9
                            if surplusHP > 0 or closeEnemyCount == 0:
                                escapeSquares = escapeSquares + [towardCentre]
                                return ['move', towardCentre]

        # if we're next to an enemy bot, attack it
        for loc in adjEnemyLocs:
            return ['attack', loc]

        # if we're in a spawn square, try to escape to a safe square
        if 'spawn' in rg.loc_types(self.location):
            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                if dest not in game.robots:
                    if dest not in closeEnemyTargets:
                        if dest not in escapeSquares:
                            escapeSquares = escapeSquares + [dest]
                            return ['move', dest]
            # if this isn't possible, try a 'good' spawn location
            for dest in goodSpawnLocs:
                if dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                    if dest not in game.robots:
                        if dest not in closeEnemyTargets:
                            if dest not in closeFriendlyTargets:
                                if dest not in escapeSquares:
                                    escapeSquares = escapeSquares + [dest]
                                    return ['move', dest]
            # if this isn't possible, try a non-bad spawn location
            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if 'spawn' in rg.loc_types(dest):
                    if dest not in badSpawnLocs:
                        if dest not in game.robots:
                            if dest not in closeEnemyTargets:
                                if dest not in closeFriendlyTargets:
                                    if dest not in escapeSquares:
                                        escapeSquares = escapeSquares + [dest]
                                        return ['move', dest]

        # if we're close to another bot who's in a battle, help attack it, unless this would bring us into a big battle!
        if game.turn != 99:
            for loc in closeEnemyLocs:
                for ally in rg.locs_around(loc, filter_out=('invalid')):
                    if ally in nearbyFriendlyLocs:
                        for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                            for poss in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                                if poss == dest:
                                    if dest not in game.robots:
                                        if dest not in escapeSquares:
                                            # check for other enemies around the square we're about to move into
                                            moveIn = 1
                                            for enemy in rg.locs_around(dest, filter_out=('invalid')):
                                                if enemy in closeEnemyLocs:
                                                    if enemy != loc:
                                                        moveIn = 0
                                            if moveIn == 1:
                                                escapeSquares = escapeSquares + [dest]
                                                return ['move', dest]

        # if we're close to another bot, attack the square we think it's going to move into (provided there isn't another bot in it)
        for loc in closeEnemyLocs:
            # try to attack the square on its path to the centre
            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if rg.toward(loc, rg.CENTER_POINT) == dest:
                    if dest not in game.robots:
                        return ['attack', dest]
            # if not, try to attack any square it could move to
            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                for poss in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                    if poss == dest:
                        if dest not in game.robots:
                            return ['attack', dest]

        # if we're next to friends, try to move away from them
        if adjFriendlyCount >=1:
            for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                if dest not in game.robots:
                    if dest not in closeEnemyTargets: # it won't be, but there's no harm in double checking
                        if dest not in closeFriendlyTargets:
                            if dest not in escapeSquares: # it won't be by the above condition, but there's no harm in double checking
                                escapeSquares = escapeSquares + [dest]
                                return ['move', dest]  

        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # move toward the centre if there's a bot that needs room, even if there's a friend there that might be moving
        for loc in adjFriendlyLocs:
            if rg.toward(loc, rg.CENTER_POINT) == self.location:
                for dest in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if rg.wdist(dest, rg.CENTER_POINT) < rg.wdist(self.location, rg.CENTER_POINT):
                        if dest not in escapeSquares:
                            escapeSquares = escapeSquares + [towardCentre]
                            return ['move', towardCentre]
                # if there's no free escape squares, just try to go towards the centre
                if towardCentre not in escapeSquares:
                    escapeSquares = escapeSquares + [towardCentre]
                    return ['move', towardCentre]

        # move toward the centre (as long as we won't then be next to a friend)
        if towardCentre not in closeFriendlyTargets:
            if towardCentre not in escapeSquares: # it won't be by the above condition
                escapeSquares = escapeSquares + [towardCentre]
                return ['move', towardCentre]

        return ['guard']
