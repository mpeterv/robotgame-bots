# ddzialak2 by ???

import rg

class Robot:
    def around(self, location):
        return rg.locs_around(location, filter_out=('invalid', 'obstacle'))

    def away(self, robots, empties):
        if not empties:
            raise KeyError("OOOps, tried to away without empty field!")
        points={}
        for cand in empties:
            points[cand] = - rg.dist(cand, rg.CENTER_POINT)
            if 'spawn' in rg.loc_types(cand):
                points[cand] -= 25
            for loc2 in self.around(cand):
                if loc2 == self.location:
                    continue
                st2 = robots.get(loc2, None)
                if st2:
                    if st2['player_id'] != self.player_id:
                        points[cand] -= 13
                    else:
                        points[cand] -= 4
        return ['move', self.getKeyWithMaxVal(points)]

    def getKeyWithMaxVal(self, someMap, gz=False):
        if not someMap:
            return None
        sel = someMap.items()
        sel.sort(key=lambda it: -it[1])
        if gz and sel[0][1] <= 0:
            return None
        return sel[0][0]

    def tryToHitOpo(self, robots, empties, turn):
        moveTo = {}
        attackTo = {}
        for eloc in empties:
            moveTo[eloc] = 0
            attackTo[eloc] = 0
            for loc2 in self.around(eloc):
                target = robots.get(loc2, None)
                if target and target['player_id'] != self.player_id:
                    for findMy in self.around(loc2):
                        bot = robots.get(findMy, None)
                        if bot and bot.get('player_id') == self.player_id and bot.get('hp') > 15:
                            moveTo[eloc] += bot.get('hp')
                    attackTo[eloc] += rg.dist(eloc, rg.CENTER_POINT) % turn
        movePos = self.getKeyWithMaxVal(moveTo, gz=True)
        if movePos:
            return ['move', movePos]
        attackPos = self.getKeyWithMaxVal(attackTo, gz=True)
        if attackPos:
            return ['attack', attackPos]
        return None

    def attack(self, robots, oppos):
        opoints = {}
        for (loc, opo) in oppos.items():
            opoints[loc] = - opo.get('hp')
            for oneiLoc in self.around(loc):
                onei = robots.get(oneiLoc, None)
                if onei and onei['player_id'] == self.player_id:
                    opoints[loc] += 15
        return [ 'attack', self.getKeyWithMaxVal(opoints)]

    def act(self, game):
        empties = []
        oppos = {}
        oppo_hp = 0
        robots = game.get('robots')
        for loc in self.around(self.location):
            obj = robots.get(loc, None)
            if obj:
                if obj['player_id'] != self.player_id:
                    oppos[loc] = obj
                    oppo_hp += obj['hp']
            else:
                if game['turn'] % 10 == 9 and 'spawn' in rg.loc_types(loc):
                    pass # don't send robo for death!
                else:
                    empties.append(loc)
        if empties and game.get("turn") % 10 >= 8 and 'spawn' in rg.loc_types(self.location):
            #print 'away from spawn %s' % str(self.location)
            return self.away(robots, empties)
        if empties and oppos:
            if self.hp < 15 or len(oppos) > 1:# or self.hp < oppo_hp:
                return self.away(robots, empties)
            return self.attack(robots, oppos)

        if not empties and len(oppos) >= 1:
            if self.hp <= 9*len(oppos):
                return ['suicide']
            minhp = 99
            minopo = None
            for oloc, oppo in oppos.items():
                if oppo['hp'] < minhp:
                    minopo = oppo
                    minhp = oppo['hp']
            return ['attack', minopo['location']]

        if not oppos and empties:
            cand = self.tryToHitOpo(robots, empties, game['turn'])
            if cand:
                return cand
        if empties:
            return self.away(robots, empties)
        return ['guard']
