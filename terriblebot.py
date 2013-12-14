# terrible bot by mumbel

import rg

import random

class Robot:

    def attack_them(self, game):
        # if there are enemies around, attack them
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    if self.hp < 7:
                        return ['suicide']
                    return ['attack', loc]
        return None

    def strong_enemy(self, game):
        hp = 0
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if bot.hp > hp:
                    hp = bot.hp
                    l = loc
        return self.plan_move(game, rg.toward(self.location, l))
    
    def weak_enemy(self, game):
        hp = None
        l = None
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if None == hp:
                    hp = bot.hp
                    l = loc
                elif bot.hp < hp:
                    hp = bot.hp
                    l = loc
        return self.plan_move(game, rg.toward(self.location, l))
    
    def random_enemy(self, game):
        tmp = []
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                tmp.append(loc)
        return self.plan_move(game, rg.toward(self.location, random.choice(tmp)))
    
    def plan_move(self, game, new_loc):
        if new_loc == self.location and self.location == rg.CENTER_POINT:
            return ['guard']
        if new_loc == self.location:
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        around_me = rg.loc_types(new_loc)
        if around_me == ['normal']:
            return ['move', rg.toward(self.location, new_loc)]
        else:
            return None

    def can_move(self, game, move):
        new_loc = tuple(map(lambda x, y: x + y, self.location, move))
        return self.plan_move(game, new_loc)

    def move_pattern(self, game, moves):
        if self.hp > 25:
            moves.reverse()
        for x in moves:
            new_move = self.can_move(game, x)
            if None != new_move:
                return new_move
        return None
    
    def spiral_boring_move(self, game):
        new_move = None
        if self.location[0] < rg.CENTER_POINT[0] and self.location[1] > rg.CENTER_POINT[1]:
            # 0,N    move up/right
            new_move = self.move_pattern(game, [(0,-1), (-1,0)])
                
        elif self.location[0] < rg.CENTER_POINT[0] and self.location[1] == rg.CENTER_POINT[1]:
            # 0,C   move up
            new_move = self.move_pattern(game, [(0, -1), (-1, 0)])
            
        elif self.location[0] < rg.CENTER_POINT[0] and self.location[1] < rg.CENTER_POINT[1]:
            # 0,0   move left/up
            new_move = self.move_pattern(game, [(1, 0), (0, -1)])

        elif self.location[0] == rg.CENTER_POINT[0] and self.location[1] < rg.CENTER_POINT[1]:
            # C,0    move left
            new_move = self.move_pattern(game, [(1, 0), (0, -1)])
            
        elif self.location[0] > rg.CENTER_POINT[0] and self.location[1] < rg.CENTER_POINT[1]:
            # N,0    move down/left
            new_move = self.move_pattern(game, [(0, 1), (1, 0)])

        elif self.location[0] > rg.CENTER_POINT[0] and self.location[1] == rg.CENTER_POINT[1]:
            # N,C    move down
            new_move = self.move_pattern(game, [(0, 1), (1, 0)])
                            
        elif self.location[0] > rg.CENTER_POINT[0] and self.location[1] > rg.CENTER_POINT[1]:
            # N,N   move right/down
            new_move = self.move_pattern(game, [(-1, 0), (0, 1)])

        elif self.location[0] == rg.CENTER_POINT[0] and self.location[1] > rg.CENTER_POINT[1]:
            # C,N   move right
            new_move = self.move_pattern(game, [(-1, 0), (0, 1)])
                        
        else: # Center, how we get here?
            return ['guard']
        if new_move == None:
            new_move = self.can_move(game, (0,0))
        return new_move

    def pile_up(self, game):
        right = 0
        left = 0
        top = 0
        bottom = 0
        x = int(rg.CENTER_POINT[0] * 0.5)
        y = int(rg.CENTER_POINT[1] * 0.5)
        for loc, bot in game.get('robots').items():
            if bot.player_id == self.player_id:
                if loc[0] < rg.CENTER_POINT[0]:
                    left = left + 1
                else:
                    right = right + 1
                if loc[1] < rg.CENTER_POINT[1]:
                    top = top + 1
                else:
                    bottom = bottom + 1
        if right > left:
            x = int(rg.CENTER_POINT[0] * 1.5)
        if bottom > top:
            y = int(rg.CENTER_POINT[1] * 1.5)
        return self.plan_move(game, rg.toward(self.location, (x, y)))    
            
    def act(self, game):
        a = self.attack_them(game)
        if None == a:
            a = random.choice([self.spiral_boring_move(game),
                               self.random_enemy(game),
                               self.weak_enemy(game),
                               self.strong_enemy(game),
                               self.pile_up(game),
                               self.plan_move(game, rg.CENTER_POINT)])
        if None == a:
            a = self.can_move(game, (0,0))
        if None == a:
            a = self.plan_move(game, rg.CENTER_POINT)
        return a
