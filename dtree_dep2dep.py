"""This is an interface module between lp2lp
and the dtreebank module"""

import codecs
import sys
import os
import os.path
import glob


LP2LPDIR=os.path.dirname(os.path.abspath(__file__))
sys.path.append(LP2LPDIR)
from py_liblp2lp import LP2LP

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

ID,FORM,LEMMA,FEAT,UPOS,XPOS,HEAD,DEPREL,DEPS,MISC=range(10)

def read_conll(inp,maxsent=0):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as filename, otherwise as open file for reading in unicode"""
    if isinstance(inp,basestring):
        f=codecs.open(inp,u"rt",u"utf-8")
    else:
        f=codecs.getreader("utf-8")(sys.stdin) # read stdin
    count=0
    sent=[]
    comments=[]

    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,basestring):
        f.close() #Close it if you opened it

def dep_sets(tree):
    deps=set() #(g,d,dtype)   #head+deprel
    edeps=set() #(g,d,dtype)  #deps
    for i,cols in enumerate(tree):
        if cols[HEAD]!=u"0":
            deps.add((int(cols[HEAD])-1,i,cols[DEPREL]))
        if cols[DEPS]!=u"_":
            for g_dtype in cols[DEPS].split(u"|"):
                g,dtype=g_dtype.split(u":",1)
                edeps.add((int(g)-1,i,dtype))
    return deps,edeps

def load_ruleset(fName):
    lp2lp.load_ruleset(fName)

def transform_tree(tree):
    """ Returns a new set of dependencies and enhanced dependencies"""
    d2d_tokens=[]
    d2d_lemmas=[]
    d2d_features=[]
    d2d_deps=[]

    deps,edeps=dep_sets(tree)
    

    for cols in tree:
        d2d_tokens.append(cols[FORM])
        d2d_lemmas.append(cols[LEMMA])
        d2d_features.append([cols[UPOS]]+cols[FEAT].split(u"|"))

    for (g,d,dType) in deps:
        dType=dType.encode("utf-8")
        d2d_deps.append((g,d,dType))

    assert not deps&edeps
    for (g,d,dType) in edeps:
        dType=dType.encode("utf-8")
        d2d_deps.append((g,d,dType))

    #{stratum -> list of [tok1,tok2,Type]}
    res=lp2lp.transformSentence(d2d_tokens,d2d_lemmas,d2d_deps,d2d_features)

    #...and now translate back to our new format
    transformed=set() #new deps
    etransformed=set() #new edeps
    strata=sorted(res)
    #print >> sys.stderr, res[strata[-1]]
    consumed_deps=set() #set of (g,d,t) origins (dependencies marked with @ in the rules)
    consumed_edeps=set() #set of (g,d,t) enhanced origins (dependencies marked with @ in the rules)
    for g,d,dType,old_g,old_d,old_dType,comment in res[strata[-1]]:
        
        if old_dType!="None":
            if (old_g,old_d,old_dType) in deps: #base layer -> base_layer
                transformed.add((g,d,dType))
                consumed_deps.add((old_g,old_d,old_dType))
            elif (old_g,old_d,old_dType) in edeps: #enhanced -> enhanced
                etransformed.add((g,d,dType))
                consumed_edeps.add((old_g,old_d,old_dType))
            else:
                assert False
        else:
            assert False, "Unknown origin"

    #pass whatever was not consumed
    transformed.update(deps-consumed_deps)
    etransformed.update(edeps-consumed_edeps)
    return transformed, etransformed

def update_deps(tree, new_deps, new_edeps):
    """tree is what we've got from conllu, new_deps and new_edeps is produced by the transformation"""
    for cols in tree:
        cols[HEAD],cols[DEPREL],cols[DEPS]=u"_",u"_",u"_"
    edeps_lists=[[] for _ in range(len(tree))] #list of (g,dtype) for every token, or empty
    for g,d,t in new_deps:
        assert tree[d][DEPREL]==u"_", (g,d,t)
        tree[d][DEPREL]=t
        tree[d][HEAD]=unicode(g+1)
    for g,d,t in new_edeps:
        edeps_lists[d].append((g,t))
    for cols,edeps_list in zip(tree,edeps_lists):
        if edeps_list:
            cols[DEPS]=u"|".join(unicode(g+1)+u":"+t for g,t in sorted(edeps_list))

def transform_all(inp):
    for tree,comments in read_conll(inp):
        if len(tree)>1:
            transformed,etransformed=transform_tree(tree)
            update_deps(tree,transformed,etransformed)
        print (u"\n".join(comments)).encode("utf-8")
        for cols in tree:
            print (u"\t".join(cols)).encode("utf-8")
        print


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

if __name__=="__main__":
    from optparse import OptionParser
    import lp2lp2pl
    parser = OptionParser(description="Transforms a conllu file (stdin) using the specified rules into a new dependency format and dumps the result to stdout")
    parser.add_option("-r", "--ruleset", dest="ruleset", default=None, help="The .pl or .lp2lp file specifying the rules", metavar="FILE")
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
    transform_all(sys.stdin)

    
    #tset.save_conllu(sys.stdout)
    #print >> sys.stderr, "   ...ok"




