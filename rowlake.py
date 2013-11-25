# rowlake by sne11ius
# http://robotgame.org/viewrobot/4116

import rg

class Robot:
    
    def get_center(self, game):
        x = 0
        y = 0
        team_size = 0
        for location, bot in game.get('robots').items():
            if bot.get('player_id') == self.player_id:
                x += location[0]
                y += location[1]
                team_size += 1
        return (x/team_size, y/team_size)
    
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
        move_to = self.get_center(game)
        for location, bot in game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if rg.dist(location, self.location) <= 1:
                    return ['attack', location]
            if bot.get('player_id') == self.player_id:
                if rg.wdist(location, self.location) < min_distance:
                    min_distance = rg.wdist(location, self.location)
                    move_to = location
        if min_distance < 2:
            move_to = self.get_center(game)
        
        if self.location == self.get_center(game):
            return ['guard']
        
        if self.num_frieds(game) > 1:
            return ['guard']
        
        return ['move', rg.toward(self.location, move_to)]
