# BetterThanTheRest by Hjax
# http://robotgame.org/viewrobot/6684

import rg
import operator


class Robot:
    turn = -1
    def act(self, game):

        bestEnemy = 999
        bestAlly = 999
        closestEnemy = (0,0)
        closestAlly = (0,0)
        badGuys = 0
        allyDistance = 999
        enemyDistance = 5
        def guessShot():
            for potentialShot in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                allyCount = 0
                enemyCount = 0
                if potentialShot not in game['robots']:
                    for enemy in rg.locs_around(potentialShot, filter_out=('invalid', 'obstacle')):
                        if enemy in game['robots']:
                            if game['robots'][enemy].player_id != self.player_id:
                                enemyCount += 1
                    if enemyCount > 0:
                        return ['attack', potentialShot]
            return ['attack', rg.toward(self.location, closestEnemy)]

        def gtfo():
            for friend in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if friend in game['robots']:
                    if game['robots'][friend].player_id == self.player_id:
                        if 'spawn' in rg.loc_types(friend):
                            escapes = 1
                            for escape in rg.locs_around(friend, filter_out=('invalid', 'obstacle', 'spawn')):
                                if escape not in game['robots']:
                                    escapes += 1
                            if escapes == 1:
                                for gtfo in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                                    if gtfo not in game['robots']:
                                        safer = 0
                                        for safe in rg.locs_around(gtfo, filter_out=('invalid', 'obstacle', 'spawn')):
                                            if safe in game['robots']:
                                                if game['robots'][safe].player_id == self.player_id:
                                                    safer += 1
                                        if safer == 0:
                                            return ['move', gtfo]
                                for gtfo in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                                    if gtfo not in game['robots']:
                                        return ['move', gtfo]

            return "nope"



        if 'spawn' in rg.loc_types(self.location):
            goodPlaces = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
        else:
            goodPlaces = rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn'))
        if (3,3) in goodPlaces:
            goodPlaces.remove((3,3))
        if (15,3) in goodPlaces:
            goodPlaces.remove((15,3))
        if (3,15) in goodPlaces:
            goodPlaces.remove((3,15))
        if (15,15) in goodPlaces:
            goodPlaces.remove((15,15))

        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if loc in game['robots']:
                    if game['robots'][loc].player_id != self.player_id:
                        badGuys += 1
        if game['turn'] % 10 == 0:
            if 'spawn' in rg.loc_types(self.location):
                for escape in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if escape not in game['robots']:
                        return ['move', escape]
                for escape in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                        if game['robots'][escape].player_id == self.player_id:
                            return ['move', escape]
                return ['suicide']
            escape = gtfo()
            if escape != "nope":
                return gtfo()


        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) < bestEnemy:
                    bestEnemy = rg.wdist(loc, self.location)
                    closestEnemy = loc
            else:
                if rg.wdist(loc, self.location) < bestAlly:
                    bestAlly = rg.wdist(loc, self.location)
                    closestAlly = loc

        if game['robots'][self.location].hp <= 15 or game['robots'][self.location].hp <= badGuys*10 or badGuys == 3:
            if rg.wdist(closestEnemy, self.location) == 1:
                for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                    if loc not in game['robots']:
                        bad = False
                        for enemy in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                            if enemy in game['robots']:
                                if game['robots'][enemy].player_id != self.player_id:
                                    bad = True
                        if loc not in goodPlaces:
                           bad = True
                        if not bad:
                            return ['move', loc]
                if bestAlly > 5:
                    for noBoom in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                        if noBoom not in game['robots']:
                            enemyCount = 0
                            for noBang in rg.locs_around(noBoom, filter_out=('invalid', 'obstacle')):
                                if noBang in game['robots']:
                                    if game['robots'][noBang].player_id != self.player_id:
                                        enemyCount += 1
                            if enemyCount*10 < game['robots'][self.location].hp:
                                return ['move', noBoom]
                if game['robots'][self.location].hp <= badGuys*10:
                    if badGuys > 1:
                        return ['suicide']
            if rg.wdist(closestEnemy, self.location) == 2:
                return guessShot()
        if badGuys == 0:
            if bestEnemy == 2:
                if bestAlly > 4:
                    return guessShot()

        if rg.wdist(closestEnemy, self.location) == 1:
            return ['attack', closestEnemy]
        if game['robots'][self.location].hp > 15:
            for fightHelp in goodPlaces:
                if fightHelp not in game['robots']:
                    for enemy in rg.locs_around(fightHelp, filter_out=('invalid', 'obstacle')):
                        if enemy in game['robots']:
                            if game['robots'][enemy].player_id != self.player_id:
                                for ally in rg.locs_around(enemy, filter_out=('invalid', 'obstacle')):
                                    if ally in game['robots']:
                                        if game['robots'][ally].player_id == self.player_id:
                                            return ['move', fightHelp]


        if rg.wdist(closestEnemy, self.location) <= enemyDistance:
            place = rg.toward(self.location, closestEnemy)
            if place == self.location:
                return ['guard']
            else:
                badEnemies = 0
                for badGuy in rg.locs_around(place, filter_out=('invalid', 'obstacle')):
                    if badGuy in game['robots']:
                        badEnemies += 1
                if place in goodPlaces:
                    if badEnemies < 3:
                        return ['move', place]

        if rg.wdist(closestAlly, self.location) <= allyDistance:
            if rg.toward(self.location, loc) != self.location:
                if rg.toward(self.location, loc) in goodPlaces:
                    return ['move', rg.toward(self.location, loc)]
                else:
                    return ['guard']
        if self.location == rg.CENTER_POINT:
            return ['guard']
        if rg.toward(rg.toward(self.location, rg.CENTER_POINT), loc) in goodPlaces:
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        return ['guard']
