import xml.etree.cElementTree as ET

import datetime
import time
import sys
import os
import codecs
import dtreebank.cElementTreeUtils as ETUtils
import dtreebank.core.stanforddep as stanforddep
from dtreebank.core.tree import *

try:
    sys.path.append(os.path.expanduser("~/cvs_checkout/LouhiLP/CG"))
    import py_fincg
    py_fincg.init()
    pyfinCG=True
    print >> sys.stderr, "CG Loaded"
except:
    pyfinCG=False
    

def PLEsc(str):
    return str.replace(u"'",ur"\'")

def read_conllu(inp,maxsent=0):
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



class TreeSet (object):
    """Model of an ordered list of trees, typically bound to a single file."""

    treeClass=Tree

    @classmethod
    def fromFile(cls,fileName):
        #fileName is a Unicode object
        #TreeCls is the class of the Tree instances
        basename = os.path.basename(fileName)
        root, extension = os.path.splitext(basename)

        if extension == u".dep":
            # .dep for stanford dependency tree
            return TreeSet.fromStanfordDependency(fileName) #TODO
        else:            
            # XML by default
            ETtree=ET.parse(fileName).getroot()
            return cls.fromDXML(ETtree,fileName)

    @classmethod
    def fromCONLLU(cls,inp,fileName=None):
        tset=cls()
        tset.fileName=fileName
        for sentence,comments in read_conllu(inp):
            tree=cls.treeClass()
            tree.comments=comments
            tree.eh=EditHistory(ET.Element("edithistory"))
            tree.treeset=tset
            tset.append(tree)
            currentoffset=0
            for cols in sentence:
                ID,FORM,LEMMA,CPOS,POS,FEAT,HEAD,DEPREL,DEPS,MISC=cols
                token=Token()
                token.charOff.append((currentoffset, currentoffset+len(FORM)))
                token.text=FORM
                tree.tokens.append(token)
                currentoffset+=len(FORM)+1
                tags=u"POS_"+POS
                if FEAT!=u"_":
                    tags+=u"|"+FEAT
                post=[True,LEMMA,tags,[]]
                token.posTags.append(post)
                token.misc=MISC.strip()
            for cols in sentence:
                ID,FORM,LEMMA,CPOS,POS,FEAT,HEAD,DEPREL,DEPS,MISC=cols
                if HEAD==u"_":
                    continue
                dep=Dep(int(HEAD)-1,int(ID)-1,DEPREL)
                dep.flags=[u"L1"]
                tree.addDep(dep)
                if DEPS!=u"_" and DEPS:
                    for h_d in DEPS.split(u"|"):
                        h,d=h_d.split(u":",1)
                        dep=Dep(int(h)-1,int(ID)-1,d)
                        dep.flags=[u"L2"]
                        tree.addDep(dep)
                if u"PBARG" in MISC:
                    pbarg=[m for m in MISC.split(u"|") if m.startswith(u"PBARG=")]
                    assert len(pbarg)==1
                    pbargs=(pbarg[0].split(u"=",1)[1]).split(u",") #list of "9:Arg_0(Entity_or_thing_taking_arg1)"
                    for p in pbargs:
                        head,arg=p.split(u":",1)
                        if u"(" in arg:
                            arg,comment=arg.split(u"(",1)
                            comment=comment[:-1]
                        else:
                            comment=u""
                        dep=Dep(int(head)-1,int(ID)-1,arg)
                        dep.flags=[u"L2"]
                        tree.addDep(dep)
            tree.text=u" ".join(t.text for t in tree.tokens)
        return tset

    @classmethod
    def fromDXML(cls,dxmlTSet,fileName=None):
        """Creates a new instance from a parsed .d.xml treeset (parsed by cElementTree)"""
        tset=cls()
        tset.fileName=fileName
        tset.name=unicode(dxmlTSet.get("name"))
        tset.parseConfig=unicode(dxmlTSet.get("parseconfig"))
        for treeElem in dxmlTSet.getiterator("sentence"):
            tree=cls.treeClass()
            tset.appendTree(tree)
            tree.text=unicode(treeElem.get("txt"))
            treeFlags=treeElem.get("flags")
            if treeFlags!=None:
                tree.flags.extend(treeFlags.split(","))
            for tokenElem in treeElem.getiterator("token"):
                token=Token()
                B,E=tokenElem.get("start"),tokenElem.get("end")
                if B!=None and E!=None: #old style charoff
                    token.charOff.append((int(B),int(E)))
                else:
                    #new style charoff
                    segments=unicode(tokenElem.get("charOff")).split(u",")
                    token.charOff=[]
                    for s in segments:
                        if s.startswith(u"-1"):
                            s="0"+s[2:]
                            print >> sys.stderr, "Warning, spurious charOff",s
                        B,E=s.split(u"-")
                        token.charOff.append((int(B),int(E)))
                token.text=Token.charOff2Str(tree.text,token.charOff)
                flags=tokenElem.get("flags")
                if flags:
                    token.flags=unicode(flags).split(u",")
                for readingElem in tokenElem.getiterator("posreading"):
                    if unicode(readingElem.get("CG"))==u"true":
                        cg=True
                    else:
                        cg=False
                    tagList=unicode(readingElem.get("tags")).split(u",")
                    for idx in range(len(tagList)):
                        if tagList[idx]==u"None":
                            tagList[idx]=None
                    token.posTags.append([cg,unicode(readingElem.get("baseform")),unicode(readingElem.get("rawtags")),tagList])
                        
                tree.tokens.append(token)
            for depElem in treeElem.getiterator("dep"):
                flags=unicode(depElem.get("flags"))
                if not flags:
                    flags=[]
                else:
                    flags=flags.split(u",")
                dep=Dep(int(depElem.get("gov")),int(depElem.get("dep")),unicode(depElem.get("type")),flags)
                tree.addDep(dep)
            editHistoryElem=treeElem.find("./edithistory")
            if editHistoryElem!=None:
                tree.eh=EditHistory(editHistoryElem)
            else:
                tree.eh=EditHistory(ET.Element("edithistory"))
            #Do I need to rebuild the POS tags?
            rerunCG=False
            for t in tree.tokens:
                if len(t.posTags)>0:
                    break #no!
            else:
                #yes!
                rerunCG=True
            if pyfinCG and rerunCG:
                tree.buildPOSTags()
        return tset

    @classmethod
    def fromStanfordDependency(cls,fileName):
        """Creates a new instance from a Stanford Dependency .dep file"""
        tset = cls()
        tset.fileName=fileName
        # TODO: how to set tset.name?
        sentences = stanforddep.readStanfordDependencySentences(fileName)
        for sentencedeps in sentences:
            # skip empties w/o comment
            if sentencedeps == []:
                continue

            tokens = stanforddep.tokensFromDependencies(sentencedeps, fileName)
            sentencetxt   = " ".join(tokens)

            # build the tree for this sentence
            tree=cls.treeClass()
            tset.appendTree(tree)
            tree.text=unicode(sentencetxt)
            currentoffset = 0
            for i, txt in enumerate(tokens):
                token=Token()
                token.charOff.append((currentoffset, currentoffset+len(txt)))
                token.text=unicode(txt)
                tree.tokens.append(token)
                currentoffset += len(txt)+1
            for deptype, headtxt, headidx, deptxt, depidx in sentencedeps:
                # silently ignore self-loops
                if depidx == headidx:
                    pass#continue
                # SD indexes from 1, adjust
                dep=Dep(headidx-1,depidx-1,unicode(deptype))
                tree.addDep(dep)
        return tset

    def prologRep(self,tsetIdx):
        outLines=[]
        for sIdx,s in enumerate(self.sentences):
            outLines.extend(s.prologRep(tsetIdx,sIdx))
        return outLines

    def prologRepStr(self,tsetIdx):
        lines=self.prologRep(tsetIdx)
        lines.sort() #so that prolog statements are grouped in the output
        return u"\n".join(lines)

    def __init__(self):
        self.fileName=None
        self.name=u""
        self.dirty=False
        self.sentences=[]
        self.currentTreeIdx=None #Holds a current position in the document, not saved in metadata
        self.parseConfig=None


    def __len__(self):
        return len(self.sentences)

    def __getitem__(self,k):
        return self.sentences[k]

    def __getattr__(self,aName):
        """Redirects all unknown method calls to self.sentences, this simulating multiple inheritance, which is not possible due to PyQT4 not implementing it"""
        return self.sentences.__getattribute__(aName)

    def appendTree(self,tree):
        self.append(tree)
        tree.treeset=self


    def appendTreeAfter(self,currentTree,newTree): #Called by a sentence when split into two
        idx=self.sentences.index(currentTree)
        self.sentences.insert(idx+1,newTree)
        newTree.treeset=self

    def deleteTree(self,tree): #Called by a sentence when merging sentences
        self.sentences.remove(tree)

    def treeChanged(self):
        self.dirty=True

    def save_conllu(self,out):
        for t_idx,t in enumerate(self.sentences):
            t.save_conllu(out,t_idx+1)

    def save(self):
        if not self.fileName:
            raise ValueError("Cannot save unnamed treeset!")
        root=self.getETTree()
        root.set("name",self.name)
        root.set("parseconfig",unicode(self.parseConfig))
        f=open(self.fileName,"wt")
        ETUtils.writeUTF8(root,f)
        f.close()
        self.dirty=False

    
    def getETTree(self):
        """Builds ET tree out of this treeset so it can be saved into a file"""
        root=ET.Element("treeset")
        for s in self.sentences:
            root.append(s.getETTree())
        return root


