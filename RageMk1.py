import rg
import random

class Robot:
    turn = None
    next = None

    def act(self, game):
        loc_types = rg.loc_types
        wdist = rg.wdist
        center = rg.CENTER_POINT
        robots = game.robots
        selfpos = self.location

        def move(pos):
            self.next[pos] = self
            return ["move", pos]

        def attack(pos):
            self.next[self.location] = self
            return ["attack", pos]

        def guard():
            self.next[self.location] = self
            return ["guard"]

        def suicide():
            return ["suicide"]

        def pos(robot):
            return robot.location

        def hp(robot):
            return robot.hp

        def enemy(robot):
            return robot.player_id != self.player_id

        def ally(robot):
            return robot.player_id == self.player_id

        def normal(pos):
            types = loc_types(pos)
            return "normal" in types and "obstacle" not in types

        def spawn(pos):
            return "spawn" in loc_types(pos)

        def empty(pos):
            return normal(pos) and pos not in robots and pos not in self.next

        def add(a, b):
            return (a[0] + b[0], a[1] + b[1])

        def sub(a, b):
            return (a[0] - b[0], a[1] - b[1])

        def around(pos):
            return [(pos[0]+1, pos[1]), (pos[0], pos[1]-1), (pos[0]-1, pos[1]), (pos[0], pos[1]+1)]

        def enemiesaround(pos):
            return [robots[p] for p in around(pos) if p in robots and enemy(robots[p])]

        def alliesaround(pos):
            return [robots[p] for p in around(pos) if p in robots and ally(robots[p])]

        def diag(pos):
            return [(pos[0]+1, pos[1]-1), (pos[0]-1, pos[1]-1), (pos[0]-1, pos[1]+1), (pos[0]+1, pos[1]+1)]

        def around2(pos):
            return [(pos[0]+2, pos[1]), (pos[0]+1, pos[1]-1), (pos[0], pos[1]-2), (pos[0]-1, pos[1]-1), (pos[0]-2, pos[1]), (pos[0]-1, pos[1]+1), (pos[0], pos[1]+2), (pos[0]+1, pos[1]+1)]

        def enemiesaround2(pos):
            return [robots[p] for p in around2(pos) if p in robots and enemy(robots[p])]

        def toward(frompos, topos):
            if frompos == topos:
                return None

            dx = topos[0] - frompos[0]
            dy = topos[1] - frompos[1]
            dirs = []

            if dx and dy:
                dxn = dx/abs(dx)
                dyn = dy/abs(dy)
                if abs(dx) >= abs(dy):
                    dirs = [(dxn, 0), (0, dyn)]
                else:
                    dirs = [(0, dyn), (dxn, 0)]
                random.shuffle(dirs)
            elif dx:
                dxn = dx/abs(dx)
                dirs = [(0, -1), (0, 1)]
                random.shuffle(dirs)
                dirs = [(dxn, 0)] + dirs
            elif dy:
                dyn = dy/abs(dy)
                dirs = [(-1, 0), (1, 0)]
                random.shuffle(dirs)
                dirs = [(0, dyn)] + dirs

            for d in dirs:
                newpos = add(frompos, d)
                if empty(newpos):
                        return newpos
            return None

        def flee():
            possible = [p for p in around(selfpos) if empty(p)]
            if possible:
                possible.sort(key=lambda p: wdist(p, center))
                possible.sort(key=lambda p: len(enemiesaround(p)))
                for p in possible:
                    if game.turn%10 >= 9 and spawn(p):
                        continue
                    return p
            return None

        if self.turn != game.turn:
            self.turn = game.turn
            self.next = {}

        if game.turn%10 >= 6 and spawn(selfpos):
            t = sub(selfpos, center)
            topos = None
            if abs(t[0]) >= abs(t[1]):
                topos = toward(selfpos, (center[0], selfpos[1]))
            else:
                topos = toward(selfpos, (selfpos[0], center[1]))
            if topos:
                return move(topos)
            elif game.turn%10 == 9:
                return suicide()

        enemies = enemiesaround(selfpos)
        if enemies:
            l = len(enemies)
            minhpenemies = [e for e in enemies if hp(e) <= 10]
            minhpenemies.sort(key=hp)
            maxhpenemies = [e for e in enemies if hp(e) > 10]
            maxhpenemies.sort(key=hp)
            if hp(self) > l*9:
                if maxhpenemies:
                    return attack(pos(maxhpenemies[0]))
                else:
                    return attack(pos(minhpenemies[0]))
            fleepos = flee()
            if fleepos:
                if hp(self) > len(enemiesaround(fleepos))*9:
                    return move(fleepos)
            if minhpenemies and hp(minhpenemies[0]) <= 8:
                return move(pos(minhpenemies[0]))
            if hp(self) > l*5:
                return guard()
            if fleepos:
                return move(fleepos)
            return guard()

        enemies = enemiesaround2(selfpos)
        if enemies:
            movepos = None
            en = [e for e in enemies if len(alliesaround(pos(e)))]
            en.sort(key=lambda e: len(alliesaround(pos(e))), reverse=True)
            for e in en:
                movepos = toward(selfpos, pos(e))
                if movepos and hp(self) > len(enemiesaround(movepos))*9:
                    return move(movepos)

            attackpos = None
            aro = around(selfpos)
            enemies.sort(key=hp, reverse=True)
            for e in enemies:
                attackpos = toward(pos(e), selfpos)
                if attackpos and attackpos in aro:
                    return attack(attackpos)

        freespaces = [p for p in around(selfpos) if empty(p)]

        if freespaces:
            freespaces.sort(key=lambda p: wdist(p, center))
            freespaces.sort(key=lambda p: len(enemiesaround2(p)), reverse=True)
            if len(enemiesaround2(freespaces[0])) > 0:
                return move(freespaces[0])

            enemies = [r for r in robots.itervalues() if enemy(r)]
            enemies.sort(key=hp, reverse=True)
            enemies.sort(key=lambda e: wdist(selfpos, pos(e)), reverse=True)
            for e in enemies:
                top = toward(selfpos, pos(e))
                if top:
                    return move(top)
        return guard()
