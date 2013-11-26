import rg
import random

SUICIDE_THRESHOLD = 1.5 # Higher is more judicious use of suicide
ATTACK_PREEMPTIVELY = 0.5

def my_toward(curr, dest):
	if curr == dest:
		return curr

	x0, y0 = curr
	x, y = dest
	x_diff, y_diff = x - x0, y - y0
	
	if y_diff == 0:
		return (x0 + x_diff / abs(x_diff), y0)
	if x_diff == 0:
		return (x0, y0 + y_diff / abs(y_diff))
	if random.randint(0,1) == 0:
		# move in the x direction
		return (x0 + x_diff / abs(x_diff), y0)
	else:
		return (x0, y0 + y_diff / abs(y_diff))

def should_suicide(robot, game):
	locs_around = rg.locs_around(robot.location)
	total_hp = 0
	opposing_neighbors = 0
	for loc, other in game['robots'].items():
		if loc in locs_around:
			if other.player_id != robot.player_id:
				opposing_neighbors += 1
				total_hp += other.hp
	return (opposing_neighbors*15 > SUICIDE_THRESHOLD*robot.hp)


def should_attack(robot, game):
	# if there's an enemy within attacking range, attack
	neighboring_enemies = get_neighboring_enemies(robot, game)
	if len(neighboring_enemies) > 0:
		return random.choice(neighboring_enemies)

	# if there's an an enemy who can move into attacking range, attack preemptively in case he moves close
	if ATTACK_PREEMPTIVELY is not False:
		for loc, other in game['robots'].items():
			if rg.wdist(loc, robot.location) == 2:
				if other.player_id != robot.player_id:
					if random.random() < ATTACK_PREEMPTIVELY:
						print "Preemptive attack!", robot.location, loc, rg.toward(robot.location, loc)
						return rg.toward(robot.location, loc)
	return None

# the idea behind "assistance" is that when self is free, look for a nearby 1:1 engagement between robots and go help out
def should_assist(robot, game):
	for loc, other in game['robots'].items():
		if other.player_id != robot.player_id:
			if rg.wdist(other.location, robot.location) == 2:
				if len(get_neighboring_enemies(other, game)) > 0: # this enemy is "engaged" with my teammate
					if rg.dist(other.location, robot.location) == 2: # the 2 robots are on a line
						target_space = rg.toward(robot.location, other.location)
						if target_space not in game.robots:
							print 'assist!', target_space
							return ['move', target_space]
					else: # kitty corner, so need to check two target spaces
						0
	return None

def get_neighboring_enemies(robot, game):
	neighboring_enemies = []
	neighbors = rg.locs_around(robot.location)
	for loc, other in game['robots'].items():
		if loc in neighbors:
			if other.player_id != robot.player_id:
				neighboring_enemies.append(other.location)
	return neighboring_enemies



class Robot:
	last_pos = ''
	def act(self, game):
#print self.last_pos
		self.last_pos = self.location
		if should_suicide(self, game):
			return ['suicide']
		attack_loc = should_attack(self, game)
		if attack_loc != None:
		 	return['attack', attack_loc]
		tow = my_toward(self.location, rg.CENTER_POINT)
		if rg.dist(self.location, rg.CENTER_POINT) > 3:
			return ['move', tow]

#		assist_action = should_assist(self, game)
#		if (assist_action is not None): return assist_action
		 
		spaces = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
		if len(spaces) > 0:
			spc = random.choice(spaces)
			return ['move', spc]

		return ['guard']

