import rg as d
class Robot:
 def act(i,q):
  r=99;g=0,0;a=i.location;b=q['robots'];j=d.toward;x='attack';e='move';s='spawn';y=d.locs_around;h=d.wdist;k=[e,j(a,d.CENTER_POINT)];l=0;t=[]
  if not q['turn']%10and s in d.loc_types(a):return k
  m=y(a,filter_out=('obstacle',s))
  for f,z in b.iteritems():
   if z.player_id!=i.player_id:
    if h(f,a)<r:r=h(f,a);g=f
    t.append(f)
    if h(f,a)==1:l+=1
  c=j(a,g);u=h(a,g);v=u==1
  if b[a].hp<l*10and v:
   n=tuple(map(lambda o,p:o-p,a,tuple(map(lambda o,p:o-p,j(a,g),a))))
   if n in m and n not in b:return[e,n]
  if v and b[a].hp>10*l or u==2and b[a].hp<16:
   if c in t and b[c].hp<6and i.hp>5:return[e,c]
   return[x,c]
  if c in m and c not in b:return[e,c]
  if k[1]in b:
   for w in m:
    if w not in b:return[e,w]
  return k
