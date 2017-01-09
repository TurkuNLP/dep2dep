# Not much to do with dep2dep but hey, I need to put this script somewhere :)
# merges the argument column from the Finnish PropBank into the DEPS field, so they
# can be referred to by the conversion rules

import codecs
import sys

ID,FORM,LEMMA,UPOS,XPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)

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

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Merge the DEPS field from ProbBank into TreeBank.')
    parser.add_argument('TREEBANK', nargs=1, help='CoNLL-U with the treebank')
    parser.add_argument('PROPBANK', nargs=1, help='CoNLL-U with the PropBank')

    args = parser.parse_args()
    
    tb=list(read_conll(args.TREEBANK[0]))
    pb=list(read_conll(args.PROPBANK[0]))
    
    assert len(tb)==len(pb), "Treebank length (%d trees) does not match Propbank length (%d trees)"%(len(tb),len(pb))
    
    for (tb_tree,tb_comments), (pb_tree,_) in zip(tb,pb):
        assert len(tb_tree)==len(pb_tree), "Trees of differing lengths, bailing out. %d vs %d"%(len(tb_tree),len(pb_tree))
        for tb_cols,pb_cols in zip(tb_tree,pb_tree):
            if pb_cols[MISC]!=u"_":
                pbsenses=u"|".join((m for m in pb_cols[MISC].split(u"|") if u"PBSENSE" in m))
                if pbsenses:
                    if tb_cols[MISC]==u"_":
                        tb_cols[MISC]=pbsenses
                    else:
                        tb_cols[MISC]=pbsenses+u"|"+tb_cols[MISC]
            if pb_cols[DEPS]==u"_":
                continue
            pb_args=[arg for arg in pb_cols[DEPS].split(u"|") if u"PBArg" in arg]
            if not pb_args:
                continue
            newdeps=[]
            for a in pb_args+([] if tb_cols[DEPS]==u"_" else tb_cols[DEPS].split("|")):
                g,t=a.split(u":",1)
                newdeps.append((int(g),t))
            newdeps.sort()
            assert newdeps
            tb_cols[DEPS]=u"|".join(unicode(g)+":"+t for g,t in newdeps)
        print (u"\n".join(tb_comments)).encode("utf-8")
        print (u"\n".join(u"\t".join(cols) for cols in tb_tree)).encode("utf-8")
        print
