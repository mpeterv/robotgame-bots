# Khal Brogo by toshima
# http://robotgame.org/viewrobot/7962

import rg
import numpy as np


class Robot:

	def act(self, game):
		self.game = game
		self.num_attackers = sum(self.is_enemy(l) for l in adj_locs(self.location))

		# maybe flee spawn
		m = self.flee_spawn()
		if m:
			return m

		if self.consider_attack():

			# maybe direct attack
			m = self.direct_attack()
			if m:
				return m

			# maybe attack
			m = self.attack()
			if m:
				return m

		# otherwise move
		return self.move()


	def consider_attack(self):
		if self.could_block_friendly_flee(self.location):
			return False
		if self.num_attackers > 1:
			return False
		# if self.spawn_dist(self.location) <= 0:
		# 	return False
		return True


	def flee_spawn(self):

		turn = self.game.turn % 10
		spawn_time = turn == 0 or turn == 9 or turn == 8
		
		# if in spawn point near spawn time, move towards centre
		if spawn_time and self.game.turn < 95 and self.is_spawn(
				self.location):
			return ['move', rg.toward(self.location, rg.CENTER_POINT)]

		else:
			return None


	def direct_attack(self):
		adjs = [l for l in adj_locs(self.location) if self.is_enemy(l)]
		if not adjs:
			return None

		bestloc, score = argmax(adjs, self.direct_attack_score)
		if score[0]:
			return ["attack", bestloc]
		else:
			return None


	# if first element is False, recommend no attack
	def direct_attack_score(self, loc):
		enemy_hp = 0
		if self.is_enemy(loc):
			enemy_hp = self.game.robots[loc].hp

		adj_enemies = [l for l in adj_locs(loc) if self.is_enemy(l)]
		num_adj_enemies = len(adj_enemies)

		# has_position = self.spawn_dist(self.location) > self.spawn_dist(loc)
		should_attack = (self.is_enemy(loc) and not self.is_friendly(loc)
			and enemy_hp < self.hp and self.hp > 9)

		return [
			should_attack,
			num_adj_enemies,
			-enemy_hp,
		]


	def attack(self):
		adjs = adj_locs(self.location)
		bestloc, score = argmax(adjs, self.attack_score)
		if score[0]:
			return ["attack", bestloc]
		else:
			return None


	# if first element is False, recommend no attack
	def attack_score(self, loc):
		adj_enemies = [l for l in adj_locs(loc) if self.is_enemy(l)]
		num_adj_enemies = len(adj_enemies)
		sum_adj_hps = sum([self.game.robots[l].hp for l in adj_enemies])

		should_attack = (self.num_attackers == 0) and num_adj_enemies >= 1 and not self.is_friendly(loc) and not self.is_spawn(self.location)

		return [
			should_attack,
			num_adj_enemies,
			-self.spawn_dist(loc)
			-sum_adj_hps,
		]


	def move(self):
		adjs = adj_locs(self.location)
		bestloc, score = argmax(adjs, self.move_score)
		guard_score = self.move_score(self.location)

		# print guard_score, [self.move_score(l) for l in adjs]
		if score > guard_score:
			return ["move", bestloc]
		else:
			return ["guard"]


	def move_score(self, loc):
		# print [
		# 	-self.is_enemy(loc),
		# 	-self.get_adj_enemies(loc),
		# ]

		num_adj_enemies = sum(self.is_enemy(l) for l in adj_locs(loc))

		# spawn distance of 1 or 2 is best, >2 good, 0 bad, -1 very bad
		spawn_dist = self.spawn_dist(loc)
		if spawn_dist == 2 or spawn_dist == 1:
			spawn_dist_score = 3
		elif spawn_dist > 2:
			spawn_dist_score = 2
		else:
			spawn_dist_score = spawn_dist

		# to manoeuvre out of spawn areas
		distance_to_centre = rg.dist(loc, rg.CENTER_POINT)
		# if spawn_dist < 2:
		# 	distance_to_centre_score = -distance_to_centre
		# else:
		# 	distance_to_centre_score = 0

		help_dist = self.help_teammate_dist(loc)
		help_score = 0
		if help_dist == 1:
			help_score = 2
		elif help_dist == 2:
			help_score = 1

		return [
			-self.is_enemy(loc),
			-self.is_friendly(loc) * (spawn_dist > 2),
			-self.could_block_friendly_flee(loc),
			-num_adj_enemies,
			-self.num_attackers * distance_to_centre,
			-self.could_collide(loc),
			spawn_dist_score,
			help_score,
			min(self.friendly_dist(loc), 2),
			-distance_to_centre,
		]


	# if friendly bot trying to get out of spawn area, move out of way
	def could_block_friendly_flee(self, loc):
		spawn_dist = self.spawn_dist(loc)
		if self.spawn_dist(loc) > 2:
			return False

		for l in adj_locs(loc):
			if self.is_friendly(l):
				if self.spawn_dist(l) < spawn_dist:
					return True
		return False


	# is loc next to friendly bot which is next to enemy bot
	def could_collide(self, loc):
		for l in adj_locs(loc):
			if self.is_friendly_under_attack(l):
				return True
		return False


	def help_teammate_dist(self, loc):
		for l in adj_locs(loc):
			if self.is_enemy(l):
				for ll in adj_locs(l):
					if self.is_friendly(ll):
						return 1

		for l in adj2_locs(loc):
			if self.is_enemy(l):
				for ll in adj_locs(l):
					if self.is_friendly(ll):
						return 2
		return -1


	# distance to nearest friendly bot
	def friendly_dist(self, loc):
		distances = []
		for botloc, bot in self.game.robots.iteritems():
			if bot.player_id == self.player_id and bot.robot_id != self.robot_id:
				distances.append(rg.wdist(loc, botloc))
		return min(distances)


	# distance to nearest spawn, capped at 3
	def spawn_dist(self, loc):
		if self.is_spawn(loc):
			for l in adj_locs(loc):
				if not self.is_spawn(l):
					return 0

			# all adjacent are spawns too
			return -1
		for l in adj_locs(loc):
			if self.is_spawn(l):
				return 1
		for l in adj2_locs(loc):
			if self.is_spawn(l):
				return 2
		return 3


	def is_spawn(self, loc):
		return "spawn" in rg.loc_types(loc)


	def is_enemy(self, loc):
		if loc not in self.game.robots:
			return False
		bot = self.game.robots[loc]
		return bot.player_id != self.player_id


	# square occupied by bot on my team and not myself
	def is_friendly(self, loc):
		if loc not in self.game.robots:
			return False
		bot = self.game.robots[loc]
		return bot.player_id == self.player_id and bot.robot_id != self.robot_id


	def is_friendly_under_attack(self, loc):
		if not self.is_friendly(loc):
			return False
		for l in adj_locs(loc):
			if self.is_enemy(l):
				return True
		return False



def argmax(lst, func):
	pairs = [(func(l), l) for l in lst]
	maxval, argmax = max(pairs)
	return argmax, maxval


def adj_locs(loc):
	return rg.locs_around(loc,
		filter_out=("invalid", "obstacle"))


def adj2_locs(loc):
	x, y = loc
	return [
		(x - 2, y),
		(x - 1, y - 1),
		(x - 1, y + 1),
		(x, y - 2),
		(x, y + 2),
		(x + 1, y - 1),
		(x + 1, y + 1),
		(x + 2, y)
	]

