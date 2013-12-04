import rg
import numpy as np


class Robot:

	def act(self, game):
		friendly_locs = [loc for loc, r in game.robots.iteritems()
			if r.player_id == self.player_id and r.robot_id != self.robot_id]

		adjs = rg.locs_around(self.location,
			filter_out=("invalid", "obstacle"))

		# if in a spawn near spawn time, move towards centre
		if game.turn % 10 >= 8 and "spawn" in rg.loc_types(self.location):

			# TODO improve logic here
			return ['move', rg.toward(self.location, rg.CENTER_POINT)]

		# if late game, start charging
		# TODO can't have multiple bots charging same square
		# if game.turn > 90 and self.hp > 20:
		# 	charge_scores = [(self.charge_score(game, loc), loc) for loc in adjs]
		# 	maxscore, maxloc = max(charge_scores)
		# 	if maxscore > 0:
		# 		return ["move", maxloc]

		# TODO don't do a pre empt attack if being attacked by someone adjacent

		# if weaker enemy nearby, attack
		if not self.is_being_attacked_by_stronger(game):
			attack_scores = [(self.attack_score(game, friendly_locs, loc), loc) for loc in adjs]
			maxscore, maxloc = max(attack_scores)
			if maxscore > 0:
				return ["attack", maxloc]

		# else move
		move_scores = [(self.move_score(game, loc), loc) for loc in adjs]
		maxscore, maxloc = max(move_scores)
		guard_score = self.move_score(game, self.location)
		if maxscore > guard_score:
			return ["move", maxloc]

		return ["guard"]


	def is_being_attacked_by_stronger(self, game):
		for rloc, r in game.robots.iteritems():
			if r.player_id != self.player_id and rg.wdist(
					rloc, self.location) == 1 and r.hp > self.hp:
				return True
		return False


	def charge_score(self, game, loc):
		score = 0
		for rloc, r in game.robots.iteritems():
			d = rg.wdist(rloc, loc)

			# someone already here
			if rloc == loc:
				score -= 100

			# weaker enemy adj to this square
			elif r.hp <= 16 and r.player_id != self.player_id and d == 1:
				score += 1

			# stronger enemy adj to this square. it's a trap.
			elif r.hp <= 16 and r.player_id != self.player_id and d == 1:
				score -= 100

		return score


	# if score > 0 recommend attack
	def attack_score(self, game, friendly_locs, loc):
		score = 0
		for rloc, r in game.robots.iteritems():
			d = rg.wdist(rloc, loc)

			# how much pressure enemy is under
			adjs = rg.locs_around(rloc,
				filter_out=("invalid", "obstacle"))

			# TODO better way, is slow
			friendly_count = len([a for a in adjs if a in friendly_locs])

			# pick on enemies running away from the spawn
			if r.player_id != self.player_id and rg.dist(
					self.location, rg.CENTER_POINT) > 6:

				if rloc == loc:
					score += 1000 + friendly_count

				elif d == 1:
					score += 500 + friendly_count

			elif r.player_id != self.player_id:

				# enemy in this square
				if rloc == loc:
					score += 100 + friendly_count

				# enemy adj to this square
				if d == 1:
					score += 10 + friendly_count

			elif r.player_id == self.player_id:

				# teammate in this square, don't attack here
				if rloc == loc:
					score -= 10000

				# teammate adj to this square, better not to attack here
				elif d == 1:
					score -= 1

		return score


	def move_score(self, game, loc):

		# don't move into spawn points
		if "spawn" in rg.loc_types(loc):
			return -10000 - rg.dist(loc, rg.CENTER_POINT)

		score = 0
		for rloc, r in game.robots.iteritems():
			d = rg.wdist(rloc, loc)
			if rloc == loc:

				# try not to collide with anyone
				score -= 100

			elif r.hp > self.hp and r.player_id != self.player_id:

				# stronger enemy adj to square, better not to move here
				if d == 1:
					score -= 10

				# stronger enemy near square, better not to move here
				elif d == 2:
					score -= 1

			elif r.player_id != self.player_id:

				# possible attack from weaker enemy
				if d == 1:
					score -= 2

				# chase weaker enemy
				# else:
				# 	score += 2. / d

			elif r.player_id == self.player_id:

				# possible collision with teammate
				if d == 1:
					score -= 1

		# move towards centre
		score -= rg.dist(loc, rg.CENTER_POINT) / 10.
		return score



# self.location
# self.hp
# self.player_id
# self.robot_id


# {
#     # a dictionary of all robots on the field mapped
#     # by {location: robot}
#     'robots': {
#         (x1, y1): {   
#             'location': (x1, y1),
#             'hp': hp,
#             'player_id': player_id,

#             # only if the robot is on your team
#             'robot_id': robot_id
#         },

#         # ...and the rest of the robots
#     },

#     # number of turns passed (starts at 0)
#     'turn': turn
# }