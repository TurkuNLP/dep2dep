"""
dtreebank/core/tree_functions.py

Collection of functions to operate on the Tree class.

"""

import re
import sys

def find_circularity(tree,exclude=[],include="."):
    """Finds circular graphs in a given tree
    This is similar to the DFS-search by Filip in the Tree class,
    but with slight modifications to actually detect and
    report which tokens produce circular graphs.

    exclude=list of types not to be checked
    include=regular expression stating what dependency types are allowed.
   
    Error type: severe (no automic fixing, error in annotation)
    """
    tokens = [None for x in tree.tokens]
    deps={}
    r=re.compile(include)
    for (g,d,t) in tree.deps:
        if not r.match(t):
            continue
        if t not in exclude:
            deps.setdefault(g,set()).add(d)
    circles=[]
    for idx in range(len(tree.tokens)):
        if tokens[idx]!=None:
            continue
        if idx in deps: #this token is a governor (has dependencies)
            f_c_dfs(idx,[],deps,tokens,circles)
    return circles


def f_c_dfs(idx,indexes,deps,tokens,circles):
    """recursive support function for find_circularity"""
    tokens[idx]=True
    if idx in indexes:
        #Bingo, we have been here before, return all indexes
        #that are part of the circularity
        circles.append(indexes[indexes.index(idx):])
        return
    indexes.append(idx)
    if idx in deps:
        for i in deps[idx]:
            f_c_dfs(i,indexes[:],deps,tokens,circles)
          

def find_islands(tree,include="."):
    """Calculates the number of islands in a tree
    Error type: fixable (allows for automatic fixing)
    """
    roots={}
    deps=[]
    include_re=re.compile(include)
    for idx in range(len(tree.tokens)):
        roots[idx]=set([idx]) #root is also in the island
    for (gov,dep,type) in tree.deps: #index by (gov,dep,type)
        if not include_re.match(type):
            continue
        #Is this a new root or does it go inside another?
        if gov not in deps:
            #this governor has not yet been a dependency,
            #so we consider it a root
            roots[gov].add(dep)
            root=gov
        else:
            #this governor has already been a dependency,
            #so we add gov&dep into the same island
            for r in roots:
                if gov in roots[r]:
                    roots[r].add(gov)
                    roots[r].add(dep)
                    root=r
                    break
        deps.append(dep)
        #this only happens if there is circularity in a sentence,
        #but this function is not meant to die on those, so we
        #gracefully skip
        if root==dep:
            continue
        #if dep was considered before a root we move it under its governor
        if dep in roots:
            roots[root] = roots[root] | roots[dep]
            del roots[dep]
    return roots

def resolve_name(tree,name_dep):
    #1) Find tokens under name which are not connected
    #   ...and connect them to the head of the name


    #So which token is the head of the name_dep?
    heads=set()
    governed=set() #dependencies with a governor
    l,r=name_dep.gov,name_dep.dep
    if l>r:
        l,r=r,l

    for (g,d,dtype),dep in tree.deps.iteritems():
        governed.add(d)
        #Do I have a dependency hitting into the middle of the name?
        if (g>r or g<l) and (d>l and d<r) and dtype not in (u"xsubj") and u"CCE" not in dep.flags: #should be a first layer dep
            heads.add(d)

    #I seriously shouldn't have several heads
    if len(heads)>1:
        print >> sys.stderr, len(heads), "heads - oops", [x+1 for x in heads], (name_dep.gov+1, name_dep.dep+1)
        tree.save_conllu(sys.stderr)
        heads=list(heads)
    elif len(heads)==0:
        heads=[name_dep.gov]
    else:
        print >> sys.stderr, [x+1 for x in heads], (name_dep.gov+1, name_dep.dep+1)
        heads=list(heads)
    assert len(heads)==1, heads
    head=heads[0]
    ops=[(name_dep.gov,name_dep.dep,u"name",name_dep.gov,name_dep.dep,u"xname")]
    for d in range(l+1,r): #all deps under
        if d not in governed and head!=d:
            #I have no other structure for this token, I guess I need to connect it to name
            ops.append((None,None,None,head,d,u"xname"))
    tree.editDepChange(ops)

def resolve_names(tree):
    names=[dep for dep in tree.deps.itervalues() if dep.type==u"name"]
    names.sort(key=lambda d: abs(d.gov-d.dep)) #shortest-to-longest, same as down-to-up
    for n in names:
        resolve_name(tree,n)


def layers(tree):
    """
    Computes the list of dependencies which constitute the first layer projection
    of node
    """
    for (g,d,t),dep in tree.deps.iteritems():
        if u"CCE" in dep.flags or dep.type in (u"rel",u"xsubj",u"xobj",u"ellipsis"):
            dep.flags.append(u"L2")
        else:
            dep.flags.append(u"L1")
    #names:
    names=[(ng,nd,nt) for (ng,nd,nt) in tree.deps.iterkeys() if nt==u"xname"]
    names.sort(key=lambda x:abs(x[0]-x[1])) #sort from shortest to longest
    for ng,nd,nt in names:
        #Does the dependent have other non-name governor in L1, or name governor in L1 which is shorter (under)
        gs=sum(1 for (g,d,t),dep in tree.deps.iteritems() if d==nd and (t!=u"xname" or abs(g-d)<abs(ng-nd)) and u"L1" in dep.flags)
        if gs>0:
            tree.deps[(ng,nd,nt)].flags.remove(u"L1")
            tree.deps[(ng,nd,nt)].flags.append(u"L2")
        
        


def link_dependencies(tree,linkdeps):
    """Link given dependencies that are bridged over multiple
    tokens by creating a chainlink from governor to the dependant.

    To maintain tree structure we also remove all dependencies 
    under the bridge and move any deps coming from outside the bridge 
    to be connected to the governor


    THIS IS HEAVILY MODIFIED FOR TRANSFORMATION USE!
    We do not clear anything under a bridge, but keep it and
    only link tokens that are without a head!


    """
    #we support multiple dependecy types at the same time
    if not isinstance(linkdeps,list):
        linkdeps=[linkdeps]
    bridgedeps=[]
    similar_deps=[]
    for (g,d,t) in tree.deps:
        if t in linkdeps:
            bridgedeps.append((g,d,t))

    if len(bridgedeps)<1:
        # no dependencies to link
        return

    #clean stuff under bridged dependencies
    #and hang anything leaving or entering the bridge to the bridge gov.
#     for (g,d,t) in tree.deps.copy():
#         if (g,d,t) in bridgedeps:
#             continue # we dont stuff other bridge dependencies
#         for (bg,bd,bt) in bridgedeps:
#             if (g,d,t)==(bg,bd,bt):
#                 continue
#             if (g,d)==(bg,bd) and t!=bt:
#                 similar_deps.append((g,d,t))
#                 continue
#             if max(g,d)<=max(bg,bd) and min(g,d)>=min(bg,bd):
#                 #dependency inside bridge
#                 # not deleted in transformation
#                 #tree.editDepChange([(g,d,t,None,None,None)])
#                 break

#             if bg>bd:
#                 # bridging from right to left
#                 if d<bg and d>=bd and (g>bg or g<bd): #dependent inside bridge
#                     tree.editDepChange([(g,d,t,g,bg,t)])
#                     break
#                 if g<bg and g>=bd and (d>bg or d<bd): #governor inside bridge
#                     tree.editDepChange([(g,d,t,bg,d,t)])
#                     break
#             else:
#                 #bridging from left to right
#                 if d>bg and d<=bd and (g<bg or g>bd): #dependent inside bridge
#                     tree.editDepChange([(g,d,t,g,bg,t)])
#                     break
#                 if g>bg and g<=bd and (d<bg or d>bd): #governor inside bridge
#                     tree.editDepChange([(g,d,t,bg,d,t)])


    # chain link the bridge
    head_of={}
    for (g,d,t) in tree.deps:
        if (g,d,t) not in bridgedeps:
            head_of[d]=g
    for (g,d,t) in bridgedeps:
        assert (g,d,t) in tree.deps
        if max(g,d)-min(g,d)>1:
            chgs=[]
            if g>d:
                for x in range(d,g):
                    if x not in head_of:
                        chgs.append((None,None,None,g,x,t))
            else:
                for x in range(g,d):
                    if x+1 not in head_of:
                        chgs.append((None,None,None,g,x+1,t))
            #dont remove the original name dep
            #chgs.append((g,d,t,None,None,None))
            tree.editDepChange(chgs)
        else:
            for (bg,bd,bt) in similar_deps:
                if (bg,bd)==(g,d):
                    tree.editDepChange([(g,d,t,None,None,None)])
                    break


def conjunct_sd2hki(tree):
    conj={}
    cc={}
    punct={}
    for (g,d,t) in tree.deps:
        if d<g: continue # only check deps going from left to right
        if t=="conj":
            conj.setdefault(g,[]).append((g,d,t))
        elif t=="cc":
            cc.setdefault(g,[]).append((g,d,t))
        elif t=="punct":
            punct.setdefault(g, []).append((g,d,t))


    changes=[]
        
    for tIdx, conjlist in conj.iteritems():
        cclist = cc[tIdx] if tIdx in cc else []
        punctlist = punct[tIdx] if tIdx in punct else []

        cclist.sort(key=lambda x:x[1])
        conjlist.sort(key=lambda x:x[1])
        punctlist.sort(key=lambda x:x[1])

        lastIdx=tIdx
        for (g,d,t) in conjlist:
            changes.append((None,None,None,lastIdx,d,"conjunct"))
            lastIdx=d
            x=0
            for (cg,cd,ct) in cclist:
                if cd<d:
                    changes.append((None,None,None,d,cd,"phrm"))
                    x+=1
                else:
                    break
            if x>0:
                cclist=cclist[x:]
                
            x=0
            for (cg,cd,ct) in punctlist:
                if cd<d:
                    changes.append((None,None,None,d,cd,"phrm"))
                    x+=1
                else:
                    break
            if x>0:
                punctlist=punctlist[x:]
                

    tree.editDepChange(changes)




                
                


        
