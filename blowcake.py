# blowcake by sne11ius
# http://robotgame.org/viewrobot/3666

import rg, sys

class Robot:
    
    def get_center(self):
        centers = [(9, 4), (14, 9), (9, 14), (4, 9)]
        # centers = [(9, 4), (9, 14)]
        min_distance = sys.maxint
        center = centers[0]
        for c in centers:
            dist = rg.wdist(self.location, c)
            if dist < min_distance:
                min_distance = dist 
                center = c
        return center
    
    def num_enemies(self, game):
        enemies = 0
        for location, bot in game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if 1 == rg.wdist(self.location, location):
                    enemies += 1
        return enemies
    
    def num_frieds(self, game):
        friends = 0
        for location, bot in game.get('robots').items():
            if bot.get('player_id') == self.player_id:
                if 1 == rg.wdist(self.location, location):
                    friends += 1
        return friends
    
    def act(self, game):
        num_enemies = self.num_enemies(game)
        if num_enemies * 9 > self.hp:
            return ['suicide']

        min_distance = float("inf")
        move_to = self.get_center()
        for location, bot in game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if rg.dist(location, self.location) <= 1:
                    return ['attack', location]
            if bot.get('player_id') == self.player_id:
                if rg.wdist(location, self.location) < min_distance:
                    min_distance = rg.wdist(location, self.location)
                    move_to = location
        if min_distance < 2:
            move_to = self.get_center()
        
        if self.location == self.get_center():
            return ['guard']
        
        if self.num_frieds(game) > 1:
            return ['guard']
        
        return ['move', rg.toward(self.location, move_to)]
