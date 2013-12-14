# Waterlinie 2.4 by gwillem
# http://robotgame.net/viewrobot/1049

from __future__ import division;from collections import defaultdict;import math;import rg;
DEBUG=True;
SCORE={'suicide':12800,'panic':6400,'attack_overwhelmed_enemy':3200,'move_to_best_attack_spot':1600,'move_to_safer_location':900,'attack_normal_enemy':500,'preemptive_strike':200,'guard':50};
SPAWN_POINTS=(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17);CENTER_POINT=9,9
def log(msg):
 if DEBUG:print'>> %s'%msg
class ProposedMove(object):
 def __init__(self,prio,action,src,dst=None):
  if dst==None:dst=src
  self.prio=prio;self.action=action;self.src=src;self.dst=dst
 def __str__(self):return'%8s > %8s, %6s, (p:%3d)'%(self.src,self.dst,self.action,self.prio)
 def to_action(self):
  action=[self.action]
  if self.action in['move','attack']:action.append(self.dst)
  return action
class ProposedMoveCollection(list):
 def _sort_proposals(self,p):dist=rg.dist(p.dst,CENTER_POINT);angle=center_angle(p.dst);return-p.prio,dist,angle
 def to_plan(self):return dict((p.src,p.to_action())for p in self)
 def find_singles(self):self.sort();sources=[p.src for p in self];bots_with_single_prop=[x[0]for x in unique_c(sources)if x[1]==1];return[p for p in self if p.src in bots_with_single_prop]
 def add_move(self,*args):self.append(ProposedMove(*args));return self
 def add_prio(self,prio,src):
  for p in self:
   if p.src==src:p.prio+=prio
  self.sort()
 def sort(self,*args,**kwargs):return super(ProposedMoveCollection,self).sort(key=self._sort_proposals,*args,**kwargs)
 def __str__(self):
  self.sort();mystr=''
  for i,item in enumerate(self):mystr+='%3d. %s\n'%(i,item)
  return mystr
 def eliminate(self,**kwargs):
  for item in list(self):
   if all([getattr(item,k)==v for k,v in kwargs.items()]):self.remove(item)
def is_spawn(loc):return'spawn'in rg.loc_types(loc)
def center_angle(loc,center=None):
 if center==None:center=rg.CENTER_POINT
 dx=loc[0]-center[0];dy=loc[1]-center[1];return math.atan2(dy,dx)
def unique_c(mylist):
 c=defaultdict(int)
 for x in mylist:c[x]+=1
 return c
def other_player_id(player_id):return 1if player_id==0 else 0
class Robot:
 def find_friends_nearby(self,src,wdist=3):pid=self.robots[src]['player_id'];locs=self.ring_search(src,wdist=wdist,inclusive=True);print'Src:',src;print locs;locs.remove(src);friends=[x for x in locs if x in self.robots and self.robots[x]['player_id']==pid];return friends
 def turns_to_spawn(self):return(10-self.turn%10)%10
 def is_spawn_imminent(self,within=0):return self.turns_to_spawn()<=within
 def act_sanity_check(self):
  if self.location not in self.robots:raise Exception("self.location %s is not in game['robots']: %s"%(self.location,self.robots))
  if self.robots[self.location]['player_id']!=self.player_id:raise Exception("self.player_id (%s) doesn't match game['robots'][loc]['player_id'] (%s)"%(self.player_id,self.robots[self.location]['player_id']))
  if not hasattr(self,'history_arena'):self.history_arena={}
  if not hasattr(self,'history_plan'):self.history_plan={}
 def act(self,game):
  self.robots=game['robots'];self.turn=game['turn'];self.enemy_id=other_player_id(self.player_id);self.act_sanity_check()
  if self.turn not in self.history_plan:log('********** turn %d *********'%game['turn']);self.history_arena[self.turn]=self.robots;self.enemy_next_moves=self.find_enemy_next_moves();self.best_attack_spots=self.find_best_attack_spots();self.enemies_assigned,self.ally_assignments=self.assign_enemies();proposals=self.collect_all_proposals();plan=self.proposals_to_plan(proposals);self.history_plan[self.turn]=plan
  plan=self.history_plan[self.turn]
  if self.location not in plan:print"Ouch! Fatal error! I couldn't find myself %s in the plan: %s"%(self.location,plan);return['guard'];raise Exception("My plan calculation is flawed, as I couldn't find myself")
  return plan[self.location]
 def assign_enemies(self):
  enemies=self.find_vuln_enemies();available_for_duty=self.find_all_bots(player_id=self.player_id);enemies_assigned=defaultdict(list)
  for wdist in[1,2,3]:
   for enemy in enemies:
    for soldier in self.find_neighbours(src=enemy,player_id=self.player_id,wdist=wdist):
     if soldier in available_for_duty:enemies_assigned[enemy].append(soldier);available_for_duty.remove(soldier)
  for enemy,soldiers in enemies_assigned.items():
   if len(soldiers)<3:del enemies_assigned[enemy]
  ally_assignments={}
  for enemy,soldiers in enemies_assigned.items():
   for soldier in soldiers:ally_assignments[soldier]=enemy
  return enemies_assigned,ally_assignments
 def is_static(self,src):
  if not hasattr(self,'turn'):return True
  if not hasattr(self,'history_arena'):return True if self.turn>1 else False
  pid=self.history_arena[self.turn][src]['player_id'];last_turn=self.turn-1
  if last_turn not in self.history_arena:return True
  if src not in self.history_arena[last_turn]:return False
  if self.history_arena[last_turn][src]['player_id']!=pid:return False
  return True
 def is_vulnerable(self,src):
  if not self.is_static(src):return False
  this_id=self.robots[src]['player_id'];other_id=other_player_id(this_id);adj=self.adjacents(location=src,filter_id=this_id);adj=[x for x in adj if self.count_neighbours(src=x,player_id=this_id)<=1]
  if len(adj)<=1:return False
  return True
 def count_neighbours(self,**kwargs):return len(self.find_neighbours(**kwargs))
 def find_neighbours(self,src=None,player_id=None,wdist=1,inclusive=False):
  src=src or self.location;locs=self.ring_search(src,wdist=wdist,inclusive=inclusive)
  if player_id==None:neighbours=[loc for loc in locs if loc in self.robots]
  else:neighbours=[loc for loc in locs if loc in self.robots and self.robots[loc]['player_id']==player_id]
  if neighbours:neighbours.sort(key=lambda x:self.robots[x]['hp'])
  return neighbours
 def filter_locs(self,locs,filter_id=None,filter_empty=False,only_empty=False,only_id=None):
  if only_empty==True:return set([loc for loc in locs if loc not in self.robots])
  if only_id!=None:return set([loc for loc in locs if loc in self.robots and self.robots[loc]['player_id']==only_id])
  if filter_empty==True:locs=[loc for loc in locs if loc in self.robots]
  if filter_id!=None:locs=[loc for loc in locs if loc not in self.robots or self.robots[loc]['player_id']!=filter_id]
  return set(locs)
 def adjacents(self,location=None,wdist=1,**kwargs):
  if location==None:location=self.location
  locs=self.ring_search(location,wdist=wdist,inclusive=False);return self.filter_locs(locs,**kwargs)
 def find_all_bots(self,player_id=None):
  if player_id!=None:return[loc for loc in self.robots if self.robots[loc]['player_id']==player_id]
  else:return[loc for loc in self.robots]
 def collect_all_proposals(self):
  proposals=ProposedMoveCollection()
  for peer in self.find_all_bots(self.player_id):proposals.extend(self.calculate_proposals_for_loc(peer))
  return proposals
 def ring_search(self,src,wdist=1,inclusive=False):
  result=[]
  try:
   for x in range(src[0]-wdist,src[0]+wdist+1):
    for y in range(src[1]-wdist,src[1]+wdist+1):
     xy=x,y
     if'obstacle'in rg.loc_types(xy):continue
     if'invalid'in rg.loc_types(xy):continue
     if inclusive:
      if rg.wdist(src,xy)<=wdist:result.append(xy)
     if not inclusive:
      if rg.wdist(src,xy)==wdist:result.append(xy)
  except TypeError,e:raise Exception('Typeerror %s, src = %s and wdist = %s'%(e,src,wdist))
  return set(result)
 def try_to_flee(self,src):
  locs=self.adjacents(src,only_empty=True);locs_safe=[loc for loc in locs if self.count_neighbours(src=loc,player_id=self.enemy_id)==0and not is_spawn(loc)]
  if locs_safe:return ProposedMove(100,'move',src,locs_safe[0])
  if is_spawn(src)and locs:return ProposedMove(90,'move',src,locs[0])
  raise CannotFlee("Can't flee! No safe locations")
 def find_enemy_next_moves(self):
  enemies=self.find_all_bots(player_id=self.enemy_id);moves=defaultdict(int)
  for e in enemies:
   for loc in self.adjacents(e):moves[loc]+=2
  if self.turn%10==0:
   for i in SPAWN_POINTS:moves[i]+=1
  return moves
 def find_best_attack_spots(self):
  hit_list=self.find_vuln_enemies();spots=[]
  for enemy in hit_list:spots.extend(self.adjacents(location=enemy,filter_id=self.player_id))
  spots=[x for x in spots if self.count_neighbours(src=x,player_id=self.enemy_id)==1];return dict((x,10)for x in spots)
 def find_vuln_enemies(self):enemies=self.find_all_bots(player_id=self.enemy_id);enemies=[x for x in enemies if self.is_vulnerable(x)];return enemies
 def find_safer_neighbours(self,src):
  can_move_here=self.adjacents(src,filter_id=self.enemy_id);safer=[];spawn_imminent=self.is_spawn_imminent();src_enemies=self.count_neighbours(src=src,player_id=self.enemy_id)
  for dst in can_move_here:
   dst_enemies=self.count_neighbours(src=dst,player_id=self.enemy_id)
   if src_enemies<=dst_enemies:continue
   if spawn_imminent and is_spawn(dst):continue
   safer.append(dst)
  return set(safer)
 def calculate_proposals_for_loc(self,src):
  panic=False;aggressive=True if self.robots[src]['hp']>=30 else False;proposals=ProposedMoveCollection();safer_neighbours=self.find_safer_neighbours(src);nearby_enemies=self.find_neighbours(src=src,player_id=self.enemy_id);max_damage_to_me=10*len(nearby_enemies);here_is_suicide=is_spawn(src)and self.is_spawn_imminent();i_will_be_killed=self.robots[src]['hp']<=max_damage_to_me
  if nearby_enemies and not safer_neighbours and(i_will_be_killed or here_is_suicide):return proposals.add_move(SCORE['suicide'],'suicide',src)
  if is_spawn(src)and self.is_spawn_imminent(within=1):panic=True
  if len(nearby_enemies)>=2:panic=True
  overwhelmed_enemies=[(x,self.count_neighbours(src=x,player_id=self.enemy_id),self.robots[x]['hp'])for x in nearby_enemies if self.count_neighbours(src=x,player_id=self.player_id)>1]
  for e in overwhelmed_enemies:score=SCORE['attack_overwhelmed_enemy']+e[1];proposals.add_move(score,'attack',src,e[0])
  for e in nearby_enemies:score=SCORE['attack_normal_enemy']+50-self.robots[e]['hp'];proposals.add_move(score,'attack',src,e)
  possibles=self.ring_search(src,inclusive=True);possibles=self.filter_locs(possibles,filter_id=self.enemy_id);src_ally_neighbours=self.count_neighbours(src=src,player_id=self.player_id);src_enemy_neighbours=self.count_neighbours(src=src,player_id=self.enemy_id)
  for dst in possibles:
   if dst in self.enemy_next_moves:score=SCORE['preemptive_strike']+self.enemy_next_moves[dst];proposals.add_move(score,'attack',src,dst)
   base_move_score=0
   if dst in self.enemy_next_moves:base_move_score-=20*self.enemy_next_moves[dst]
   if aggressive and src in self.ally_assignments:
    src_target_distance=rg.wdist(src,self.ally_assignments[src]);dst_target_distance=rg.wdist(dst,self.ally_assignments[src])
    if dst in self.best_attack_spots:base_move_score+=SCORE['move_to_best_attack_spot']
    base_move_score+=100*(src_target_distance-dst_target_distance)
   dst_enemy_neighbours=self.count_neighbours(src=dst,player_id=self.enemy_id)
   if src==dst:base_move_score+=10
   if is_spawn(src)and self.is_spawn_imminent(within=1):base_move_score+=SCORE['move_to_safer_location']
   if is_spawn(dst):base_move_score-=10
   if is_spawn(dst)and self.is_spawn_imminent():base_move_score-=SCORE['suicide']
   if panic and src!=dst:base_move_score+=SCORE['panic']
   if dst_enemy_neighbours<src_enemy_neighbours:base_move_score+=SCORE['move_to_safer_location']+dst_enemy_neighbours-src_enemy_neighbours
   action='guard'if dst==src else'move';proposals.add_move(base_move_score,action,src,dst)
  return proposals
 def proposals_to_plan(self,proposals):
  proposals.sort();moves=ProposedMoveCollection()
  while proposals:
   execute_proposals=proposals.find_singles()
   if not execute_proposals:execute_proposals=[proposals.pop(0)]
   for p in execute_proposals:
    proposals.eliminate(src=p.src)
    if p.action in['move','guard']:proposals.eliminate(src=p.dst,action='attack');proposals.eliminate(dst=p.dst);proposals.eliminate(dst=p.src,src=p.dst,action='move');proposals.add_prio(2000,p.dst)
    elif p.action=='attack':proposals.eliminate(dst=p.dst,action='move');proposals.eliminate(dst=p.src,action='move');proposals.eliminate(dst=p.src,action='attack')
    elif p.action=='suicide':0
    moves.append(p)
  return moves.to_plan()
class NoBotFound(Exception):0
class CannotFlee(Exception):0
