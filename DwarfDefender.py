# DwarfDefender by ???
# http://robotgame.org/viewrobot/3797

import rg

queued_to_gtfo=[]
move_plans=[]
max_unit_damage=10

class Robot:
    def allys_near(self,query_loc):
        allys=[]
        for loc, bot in self.game.get('robots').items():
            if bot.get('player_id') == self.player_id:
                if rg.wdist(loc,query_loc) <= 1:
                    allys.append([loc,bot])
        return allys
    def enemys_near(self,query_loc):
        enemys=[]
        for loc, bot in self.game.get('robots').items():
            if bot.get('player_id') != self.player_id:
                if rg.wdist(loc, query_loc) <= 1:
                    enemys.append([loc,bot]) 
        return enemys 
    def bot_in(self,query_loc):
        for loc, bot in self.game.get('robots').items():
            if loc==query_loc:
                return bot
        return None
    def act(self, game):
        global move_plans
        self.game=game
        enemys=[]

        me=0
        xy=0
        for loc, bot in self.game.get('robots').items():
            if loc==self.location:
                xy=loc
                me=bot

        allys=self.allys_near(xy)
        enemys=self.enemys_near(xy)

        #clear any our move plans
        if len(enemys)==1 and enemys[0][1].get('hp')<me.get("hp"): #part after and 240:200  
            for loc,bot in enemys:
                return ['attack', loc]# this 3 lines got from 200/300 vs stupid 2.6.1.0.1 to 185/171

        for target,id in move_plans[:]:
            if id==self.player_id:
                move_plans.remove([target,id])


        for loc in queued_to_gtfo[:]:
            #print "queued to get out",loc
            if loc==xy:
                print "trying to gtfo"
                ally_preventing_us_to_gtfo=0
                queued_to_gtfo.remove(xy)
                for loc,bot in allys:
                    if loc==rg.toward(xy, rg.CENTER_POINT):
                        ally_preventing_us_to_gtfo=1
                        queued_to_gtfo.append(loc)
                if not ally_preventing_us_to_gtfo:
                    someone_is_already_moving_there=0
                    for loc,id in move_plans:
                        if loc==xy:
                            someone_is_already_moving_there=1
                    if not someone_is_already_moving_there:
                        bot=self.bot_in(rg.toward(xy, rg.CENTER_POINT))
                        if bot:
                            if bot.get('player_id') != self.player_id:
                                pass
                        else:                        
                            move_plans.append([rg.toward(self.location, rg.CENTER_POINT),self.player_id])
                            return ['move', rg.toward(self.location, rg.CENTER_POINT)] 
                        
        if allys and ('spawn' not in rg.loc_types(self.location)):
            for loc,bot in allys:
                if 'spawn' in rg.loc_types(loc):
                    ally_preventing_us_to_gtfo=0
                    for loc,bot in allys:
                        if loc==rg.toward(xy, rg.CENTER_POINT):
                            ally_preventing_us_to_gtfo=1
                            queued_to_gtfo.append(loc)
                    if not ally_preventing_us_to_gtfo:
                        someone_is_already_moving_there=0
                        for loc,id in move_plans:
                            if loc==xy:
                                someone_is_already_moving_there=1
                        if not someone_is_already_moving_there:
                            move_plans.append([rg.toward(self.location, rg.CENTER_POINT),self.player_id])
                            return ['move', rg.toward(self.location, rg.CENTER_POINT)]  
                    

                    #need to let ally get out to safty
        #print "total enemys ",len(enemys)
        
        enemy_preventing_us_to_move_from_spawn_point=0
        if 'spawn' in rg.loc_types(self.location):
            for loc,bot in enemys:
                if loc==rg.toward(xy, rg.CENTER_POINT):
                    enemy_preventing_us_to_move_from_spawn_point=1
            if not enemy_preventing_us_to_move_from_spawn_point:
                someone_is_already_moving_there=0
                for loc,id in move_plans:
                    if loc==xy:
                        someone_is_already_moving_there=1
                if not someone_is_already_moving_there:
                    move_plans.append([rg.toward(self.location, rg.CENTER_POINT),self.player_id])
                    return ['move',rg.toward(self.location, rg.CENTER_POINT)]          

        if len(enemys):
            am_i_helping_ally=0
            for loc,bot in enemys:
                if len(self.allys_near(loc))>=2:
                    am_i_helping_ally=1
            if am_i_helping_ally==0 and (me.get("hp")<max_unit_damage*len(enemys)+1 or len(enemys)>1):
                locs=rg.locs_around(self.location, filter_out=('invalid', 'obstacle','spawn'))                
                for loc in locs:
                    bot=self.bot_in(loc)
                    if bot:
                        if bot.get('player_id') == self.player_id:
                            queued_to_gtfo.append(loc)
                        else:
                            pass
                    else:
                       print "escaping"
                       return ['move',rg.toward(self.location,loc)]           
            

                    
                        
            if len(allys)<len(enemys) and me.get("hp")<max_unit_damage*len(enemys)+1:
                print "hp<11 boom"
                return ['suicide']
            idx_enemy_with_lowest_hp=0
            for i in xrange(len(enemys)):
                loc,bot=enemys[i]
                if bot.get('hp')<enemys[idx_enemy_with_lowest_hp][1].get('hp'):
                    idx_enemy_with_lowest_hp=i
            loc=enemys[idx_enemy_with_lowest_hp][0]
            return ['attack', loc]

        for loc, bot in game.get('robots').items():#from 185/171 to 225/161 
            if bot.get('player_id') != self.player_id:
                if rg.wdist(loc, self.location) <= 2:
                    if ('invalid' in rg.loc_types(self.location)) or ('obstacle' in rg.loc_types(self.location)):
                        continue
                    return ['attack', rg.toward(self.location,loc)]
        return ['guard']
