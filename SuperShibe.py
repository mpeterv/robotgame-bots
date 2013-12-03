# SuperShibe by ???
# http://robotgame.org/viewrobot/6669

import rg

class Robot:

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
        move_to = rg.CENTER_POINT
        for location, bot in game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if rg.dist(location, self.location) <= 1:
                    return ['attack', location]
            if bot.get('player_id') == self.player_id:
                if rg.wdist(location, self.location) < min_distance:
                    min_distance = rg.wdist(location, self.location)
                    move_to = location
        if min_distance < 2:
            move_to = rg.CENTER_POINT

        if self.location == rg.CENTER_POINT:
            return ['guard']

        if self.num_frieds(game) > 1:
            return ['guard']

        return ['move', rg.toward(self.location, move_to)]


