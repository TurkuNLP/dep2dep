"""This is an interface module between lp2lp
and the dtreebank module"""

import codecs
import sys
import os
import os.path
import glob


LP2LPDIR=os.path.dirname(os.path.abspath(__file__))
sys.path.append(LP2LPDIR)
sys.path.append(os.path.join(LP2LPDIR,'..','..'))
from py_liblp2lp import LP2LP

from dtreebank.core.treeset import TreeSet
from dtreebank.core.tree import Dep

import dtreebank.core.tree_functions as TF

lp2lp=LP2LP(LP2LPDIR) #Loads lp2lp

# # Load the rules
# lp2lp.load_ruleset(LP2LPDIR+"/rules.pl")

# tokens="A B C D".split()
# dependencies=[(0,1,"appos>"),
#               (2,3,"<nn"),
#               (0,3,"subj>")]


# print lp2lp.transformSentence(tokens,dependencies)

#print LP2LPDIR

#Here are the interface functions


def load_ruleset(fName):
    lp2lp.load_ruleset(fName)

def transformSD2HKI(dTree,bare=False):
    """This one is specific to the SD->H:ki scheme conversion
    development. We expect a tree with dependency types prefixed "sd:"
    for SD gold standard, "h:" for "H:ki-scheme gold standard". Then
    we insert dependencies prefixed "cv:" which is the output of the
    conversion. These will also carry a tag "correct,wrong,missing"
    for hgs_ dependencies which are correctly produced, incorrectly
    produced, or missing. These will later be visualized as
    green,red,black.


    Later modified to also accept bare input, which is assume to be SD"""
    
    if len(dTree.deps)==0:
        return

#1) remember the original dependencies
    sdGS=set() #(g,d,sd_dType)
    hGS=set() #(g,d,h_dType)
    for g,d,dType in dTree.deps:
        if dType.startswith(u"sd:"):
            sdGS.add((g,d,dType))
        elif dType.startswith(u"h:"):
            hGS.add((g,d,dType))
        else: #Fallback in case we have no sd:/h: marking - assume SD
            sdGS.add((g,d,u"sd:"+dType))
#2) now create a version of the sentence with just the SD dependencies to convert
    dTree.origDeps=dTree.deps
    dTree.deps={}
    for (g,d,sd_dType) in sdGS:
        dTree.deps[(g,d,sd_dType[3:])]=Dep(g,d,sd_dType[3:])
    #print >> sys.stderr, dTree.deps.keys()

    #we do preprocessing here, when the tree doesn't have
    #any other dependencies messing things up.

    #connect names and clear anything under them.
    #TF.link_dependencies(dTree,["name"])

    # connect conjuncts the way hki scheme does it.
    #TF.conjunct_sd2hki(dTree)


    # redo sdGS after transformation
    sdGS=set()
    for g,d,dType in dTree.deps:
        sdGS.add((g,d,u"sd:"+dType))

#3) now transform it
    transformDTree(dTree)
#4) now dump in all dependencies of interest
    if not bare:
        convertedDeps=dTree.deps
        dTree.deps={}
        for (g,d,sd_dType) in sdGS:
            newD=Dep(g,d,sd_dType)
            dTree.deps[(g,d,sd_dType)]=newD
        for (g,d,dType) in convertedDeps:
            newD=Dep(g,d,"cv:"+dType)
            dTree.deps[(g,d,"cv:"+dType)]=newD
            if (g,d,u"h:"+dType) in hGS: #this one is correct
                newD.flags.append(u"correct")
            else: #this one is incorrect
                newD.flags.append(u"wrong")
        for (g,d,h_dType) in hGS:
            dType=h_dType[2:]
            if (g,d,dType) not in convertedDeps: #this one is missing
                newD=Dep(g,d,"cv:"+dType)
                dTree.deps[(g,d,"cv:"+dType)]=newD
                newD.flags.append("missing")
    #Done
    

def transformDTree(dTree):
    """Takes one Tree() and *modifies it in place*, giving the new dependency structure"""
    lp2lp_tokens=[t.text for t in dTree.tokens]
    lp2lp_deps=[]
    lp2lp_readings=[[r[:3] for r in t.posTags] for t in dTree.tokens]
    for (g,d,dType) in dTree.deps:
        dType=dType.encode("utf-8")
        lp2lp_deps.append((g,d,dType))
    res=lp2lp.transformSentence(lp2lp_tokens,lp2lp_deps,lp2lp_readings)
    #...and now translate back to our new format
    transformed={} #as in Tree()
    strata=sorted(res)
    #print >> sys.stderr, res[strata[-1]]
    consumed_deps=set() #set of (g,d,t) origins
    for g,d,dType,old_g,old_d,old_dType,comment in res[strata[-1]]:
        new_d=Dep(g,d,dType)
        new_d.flags.append(u"converted") #Converted
        if dType!=u"XXX" and dType!=u"root" and not dType.startswith(u"Arg"):
            transformed[(g,d,dType)]=new_d #no need to worry about duplicates - flatten them if present
        misc=[]
        if old_dType!="None":
            misc.append(u"origin=(%d,%d,%s,%d,%d,%s)"%(g+1,d+1,dType,old_g+1,old_d+1,old_dType))
            oldd=dTree.origDeps[(old_g,old_d,old_dType)]
            if u"L2" in oldd.flags:
                new_d.flags.append(u"L2")
            else:
                new_d.flags.append(u"L1")
            consumed_deps.add((old_g,old_d,old_dType))
        if comment and comment!="EMPTYCOMMENT":
            misc.append(u"comment(%d,%d,%s)=\"%s\""%(g+1,d+1,dType,comment))
        if misc:
            new_d.misc=u"|".join(misc)
        else:
            new_d.misc=u""
    for (g,d,t),dep in dTree.deps.iteritems():
        if (g,d,t) not in consumed_deps and t!=u"root" and not t.startswith(u"Arg"):# and t in ud_types:
            transformed[(g,d,t)]=dep
            dep.flags.append(u"passed") #original, pass
            if u"L2" in dTree.origDeps[(g,d,t)].flags:
                dep.flags.append(u"L2")
    dTree.deps=transformed
    #and we're done

def transformTreeset(treeset,bare=False):
    for tree in treeset.sentences:
        transformSD2HKI(tree,bare)
    

def compileAndLoadRuleset(ruleset=None):
    import lp2lp2pl
    if ruleset==None:
        ruleset=os.path.join(LP2LPDIR,"sd2hki.lp2lp")
    plFile=ruleset.replace(".lp2lp",".pl")
    fIn=open(ruleset,"r")
    fOut=open(plFile,"w")
    lp2lp2pl.convert(fIn,fOut)
    fIn.close()
    fOut.close()
    load_ruleset(plFile)
    print >> sys.stderr, "Ruleset reloaded"

def transformFiles(fNameIn,fNameOut):
    tset=TreeSet.fromFile(fNameIn)
    transformTreeset(tset)
    tset.fileName=fNameOut
    tset.save()

if __name__=="__main__":
    from optparse import OptionParser
    import lp2lp2pl
    parser = OptionParser(description="Transforms a conllu file (stdin) using the specified rules into a new dependency format and dumps the result to stdout")
    parser.add_option("-r", "--ruleset", dest="ruleset", default=None, help="The .pl or .lp2lp file specifying the rules", metavar="FILE")
    parser.add_option("--marked",dest="marked",default=False, action="store_true", help="Assume sd: h: marked input. No marking, and SD is assumed by default.")
    (options, args) = parser.parse_args()

    if not options.ruleset:
        print >> sys.stderr, "You'll need to specify the transformation rules (try -h for help)"
        sys.exit(-1)

    if options.ruleset.endswith(".lp2lp"):
        plFile=options.ruleset.replace(".lp2lp",".pl")
        print >> sys.stderr, "Converting %s -> %s"%(options.ruleset,plFile)
        fIn=open(options.ruleset,"r")
        fOut=open(plFile,"w")
        lp2lp2pl.convert(fIn,fOut)
        fIn.close()
        fOut.close()
        options.ruleset=plFile

    load_ruleset(options.ruleset)
    inp=sys.stdin
    outp=sys.stdout
    tset=TreeSet.fromCONLLU(inp)
#    tset.fileName=fNameOut
    transformTreeset(tset, not options.marked)
    tset.save_conllu(sys.stdout)
    print >> sys.stderr, "   ...ok"




