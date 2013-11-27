# Gir by InvaderZim
# http://robotgame.org/viewrobot/5740

from random import choice

import rg

class defaultdict(dict):
    def __init__(self, default_factory=None, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.default_factory = default_factory
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value
    def copy(self):
        return self.__copy__()
    def __copy__(self):
        return type(self)(self.default_factory, self)
    def __repr__(self):
        return 'defaultdict(%s, %s)' % (self.default_factory, dict.__repr__(self))

class Robot:

    # Constants
    MIN_ATTACK_DAMAGE, MAX_ATTACK_DAMAGE = rg.settings.attack_range
    SUICIDE_DAMAGE = rg.settings.suicide_damage
    TURNS, TURNS_TO_KEEP = rg.settings.max_turns, 2
    # Locations
    ALL_LOCATIONS = set()
    SPAWN_LOCATIONS = set()
    VALID_LOCATIONS = set()
    INVALID_LOCATIONS = set()
    # State
    COMMANDS = defaultdict(dict) # {turn => {robot_id => command}}
    ATTACKS = defaultdict(lambda: defaultdict(int)) # {turn => {location => damage}}

    def act(self, game):
        turn = game['turn']
        if not self.ALL_LOCATIONS:
            self.setup()
        if turn not in self.COMMANDS:
            self.compute_commands(game['robots'], turn)
            self.cleanup(turn)
        return self.COMMANDS[turn][self.robot_id]

    @classmethod
    def setup(cls):
        cls.SPAWN_LOCATIONS.update(rg.settings.spawn_coords)
        cls.INVALID_LOCATIONS.update(rg.settings.obstacles)
        for x in xrange(rg.settings.board_size):
            for y in xrange(rg.settings.board_size):
                location = (x, y)
                if location not in cls.SPAWN_LOCATIONS and location not in cls.INVALID_LOCATIONS:
                    cls.VALID_LOCATIONS.add(location)
        cls.ALL_LOCATIONS.update(cls.SPAWN_LOCATIONS, cls.VALID_LOCATIONS)

    def compute_commands(self, robots, turn):
        my_bots = dict((b.location, b) for b in robots.itervalues() if self.is_my_bot(b))
        enemy_bots = dict((b.location, b) for b in robots.itervalues() if self.is_enemy_bot(b))
        self.perimeter_scan(my_bots, enemy_bots)
        self.perimeter_scan(enemy_bots, my_bots)
        for bot in my_bots.itervalues():
            self.compute_command(turn, bot, enemy_bots)

    @classmethod
    def cleanup(cls, turn):
        cleanup_turn = turn - cls.TURNS_TO_KEEP
        for state in (cls.COMMANDS, cls.ATTACKS):
            if cleanup_turn in state:
                del state[cleanup_turn]

    def compute_command(self, turn, bot, enemy_bots):
        if bot.location in self.SPAWN_LOCATIONS:
            self.move(turn, bot, choice(bot.movements) if bot.movements else rg.toward(bot.location, rg.CENTER_POINT))
            return
        # if there are enemies around, attack them
        if bot.enemies:
            enemies = [enemy_bots[loc] for loc in bot.enemies]
            weak_enemies = [b for b in enemies if self.health(b) <= self.MIN_ATTACK_DAMAGE]
            if weak_enemies:
                self.attack(turn, bot, choice(weak_enemies).location)
                return
            if self.health(bot) < len(enemies) * self.MIN_ATTACK_DAMAGE:
                self.suicide(turn, bot)
                return
            target = min(enemies, key=self.health)
            self.attack(turn, bot, target.location)
            return
        # if we're in the center, stay put
        if bot.location == rg.CENTER_POINT:
            self.guard(turn, bot)
            return
        # move toward the center
        self.move(turn, bot, rg.toward(bot.location, rg.CENTER_POINT))

    def perimeter_scan(self, bots, opposing_bots):
        for bot in bots.itervalues():
            bot.enemies, bot.movements = [], []
            for loc in self.around(bot, include_spawn=True):
                if loc in opposing_bots:
                    bot.enemies.append(loc)
                else:
                    bot.movements.append(loc)

    # Helpers for issuing commands
    def attack(self, turn, bot, location):
        self.COMMANDS[turn][bot.robot_id] = ['attack', location]
        self.ATTACKS[turn][location] += self.MIN_ATTACK_DAMAGE

    def guard(self, turn, bot):
        self.COMMANDS[turn][bot.robot_id] = ['guard']

    def move(self, turn, bot, location):
        self.COMMANDS[turn][bot.robot_id] = ['move', location]

    def suicide(self, turn, bot):
        self.COMMANDS[turn][bot.robot_id] = ['suicide']
        for loc in self.around(bot):
            self.ATTACKS[turn][loc] += self.SUICIDE_DAMAGE

    # Helpers for filtering
    def health(self, bot=None):
        return (bot or self).hp

    def is_my_bot(self, bot):
        return bot.player_id == self.player_id

    def is_enemy_bot(self, bot):
        return not self.is_my_bot(bot)

    # Helpers for locations
    def around(self, bot=None, distance=1, include_spawn=False):
        bot = bot or self
        valid_locations = self.ALL_LOCATIONS if include_spawn else self.VALID_LOCATIONS
        if distance == 1:
            return [l for l in (self.north(bot), self.east(bot), self.south(bot), self.west(bot)) if l in valid_locations]
        return filter(lambda l: rg.wdist(bot.location, l) <= distance, valid_locations)

    def north(self, bot=None):
        bot = bot or self
        return (bot.location[0], bot.location[1] - 1)

    def east(self, bot=None):
        bot = bot or self
        return (bot.location[0] + 1, bot.location[1])

    def south(self, bot=None):
        bot = bot or self
        return (bot.location[0], bot.location[1] + 1)

    def west(self, bot=None):
        bot = bot or self
        return (bot.location[0] - 1, bot.location[1])
