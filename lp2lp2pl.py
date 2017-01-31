# Copyright (C) 2007 University of Turku

# This is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this software in the file COPYING. If not, see
# http://www.gnu.org/licenses/lgpl.html

import sys
import os.path 
LP2LPDIR=os.path.dirname(os.path.abspath(__file__))
sys.path.append(LP2LPDIR)


import yacc
import lex


macros={}

plrules=[]

tokens=('LBRAC', 'RBRAC', 'LPAR', 'RPAR', 'NUM', 'COL','DQSTR','SQSTR','DASH','VAR','EQSIGN','NEG','BACKREF', 'STRATUM', 'CONCAT', 'ORIGIN', 'PLRULE')

t_LBRAC=r'\['
t_RBRAC=r'\]'
t_LPAR=r'\('
t_RPAR=r'\)'
t_NUM=r'[0-9]+'
t_CONCAT=r'\.\.'
t_COL=r':'
t_DQSTR=r'"[^"]*?"'
t_SQSTR=r"'[^\']*?'"
t_VAR=r"[a-zA-Z_]+"
t_DASH=r"-"
t_EQSIGN=r"="
t_NEG=r"!"
t_ORIGIN=r"@"
t_BACKREF=r'\\[0-9]+'
t_STRATUM=r'[0-9]+::'


def t_PLRULE(t):
    r'\%\%\s*plrule\s*:\s*.*'
    t.value=t.value.split(":",1)[1].strip()
    plrules.append(t.value)

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_comment(t):
    r'\%.*' #Dot matches anything but newline in python re
    pass

t_ignore=" \t"

# Error handling rule
def t_error(t):
    print >> sys.stderr, "Illegal character starting '%s...'" % t.value[0:20]
    raise ValueError("Illegal character on line %d starting with '%s...'" %(t.lexer.lineno,t.value[0:20]))
    t.lexer.skip(1)


# Error rule for syntax errors
def p_error(p):
    print >> sys.stderr, "Syntax error in input!"
    if p==None:
        errtext="Reached the end of the rule file unexpectedly"
    else:
        errtext="Unexpected token on line %d: '%s'. Note: this could also be a problem in the previous rule. "%(p.lexer.lineno,p.value)
    raise ValueError("Syntax error in input: "+errtext)


def p_statements1(p):
    'statements : statement'
    if p[1]:
        p[0]=[p[1]]
    else:
        p[0]=[]

def p_statements2(p):
    'statements : statement statements'
    if p[1]:
        p[2].append(p[1])
    p[0]=p[2]

def p_statement(p):
    '''statement : rule
                 | macro
                 | PLRULE
    '''
    if p[1]: #It's a rule
        p[0]=p[1]

def p_macro(p):
    'macro : VAR EQSIGN DQSTR'
    variable=p[1]
    expression=p[3][1:-1]
    macros[variable]=expression
#    print "Defining %s as %s"%(variable,expression)

def p_rule(p):
    '''rule : stratum LBRAC VAR VAR LPAR outType RPAR DQSTR RBRAC COL LBRAC conditions RBRAC'''
    action=Action(WordSpec(p[3],None),WordSpec(p[4],None),p[6],p[1])
    p[0]=Rule(action,p[12],p[8],p.lexer.lineno)


def p_outType(p):
    '''outType : SQSTR
               | BACKREF'''
    if p[1].startswith("'"): #SQSTR
        p[0]=p[1][1:-1]
    elif p[1].startswith("\\"):
        p[0]="BACKREF::%s"%p[1][1:]

def p_conditions(p):
    '''conditions : condition
                  | condition conditions'''
    if len(p)==2:
        p[0]=[p[1]]
    else:
        p[2].append(p[1])
        p[0]=p[2]

def p_condition(p):
    '''condition : orig negation stratum  LBRAC wordspec wordspec LPAR typespec RPAR RBRAC'''
    p[0]=Condition(p[1],p[2],p[5],p[6],p[8][0],p[8][1],p[3])

def p_condition2(p):
   '''condition : wordspec CONCAT wordspec '''
   p[0]=OrderCondition(p[1],p[3])

def p_wordspec(p):
    '''wordspec : VAR
                | VAR DASH DQSTR
                | VAR DASH VAR'''
    handle=p[1]
    wordform=""
    if len(p)>2: #The second or third rule hit
        if p[3].startswith('"'):
            wordform=p[3][1:-1]
        else:
            if p[3] not in macros:
                raise ValueError("Macro %s used but not defined on line %d."%(p[3],p.lexer.lineno))
            wordform=macros[p[3]]
    p[0]=WordSpec(handle,wordform)
        

def p_typespec(p):
    '''typespec : DQSTR
                | VAR'''
    if p[1][0]=='"':#A string
        p[0]=(p[1][1:-1],None)
    else:
        if p[1] not in macros:
            raise ValueError("Macro %s used but not defined on line %d."%(p[1],p.lexer.lineno))
        p[0]=(macros[p[1]],p[1])
        

def p_negation(p):
    '''negation : NEG'''
    p[0]=True

def p_negation2(p):
    '''negation : '''
    p[0]=False


def p_orig(p):
    '''orig : ORIGIN'''
    p[0]=True

def p_orig2(p):
    '''orig : '''
    p[0]=False



def p_stratum(p):
    '''stratum : empty
               | STRATUM'''
    if p[1]==None: #empty
        p[0]=None #If stratum is unspecified, mark it as None and sufficient default will be provided
    else:
        p[0]=int(p[1][:-2])

def p_empty(p):
    'empty : '
    pass




################# END OF PARSER #################

class OrderCondition:
    
    def __init__(self,lWordSpec,rWordSpec):
        self.lWordSpec=lWordSpec
        self.rWordSpec=rWordSpec
        self.origin=False

    def toPL(self,typeVarNum,defaultStratum,tokensSoFar): #should not need the tokens so far since this condition is sorted after the Condition()
        #
        return "tokenOrder(T%s,T%s)"%(self.lWordSpec.handle,self.rWordSpec.handle)

        

class Condition:

    def __init__(self,origin,negation,lWordSpec,rWordSpec,lType,macro,stratum):
        self.origin=origin
        self.negation=negation
        if lType.startswith("<"):
            self.gov,self.dep,self.lType=rWordSpec,lWordSpec,lType[1:]
            self.forceDir="left"
        elif lType.endswith(">"):
            self.dep,self.gov,self.lType=rWordSpec,lWordSpec,lType[:-1]
            self.forceDir="right"
        else:
            self.dep,self.gov,self.lType=rWordSpec,lWordSpec,lType
            self.forceDir="any"
        self.lType="^(%s)$"%self.lType
        self.macro=macro
        self.stratum=stratum

    def toPL(self,typeVarNum,defaultStratum,tokensSoFar):
        if self.stratum==None:
            strat=defaultStratum
        else:
            strat=self.stratum
        wGov=self.gov.handle
        wDep=self.dep.handle
        rule=r"dependency(T%(WG)s,T%(WD)s,LT%(TN)d,%(STRAT)d),accepts('%(LT)s',LT%(TN)d)"%{"WG":wGov,"WD":wDep,"TN":typeVarNum,"LT":self.lType,"STRAT":strat}
        if self.origin:
            rule+=r", OG=T%(WG)s,OD=T%(WD)s,OT=LT%(TN)d"%{"WG":wGov,"WD":wDep,"TN":typeVarNum}
        if self.forceDir=="left":
            rule+=", tokenOrder(T%(WD)s,T%(WG)s)"%{"WG":wGov,"WD":wDep}
        if self.forceDir=="right":
            rule+=", tokenOrder(T%(WG)s,T%(WD)s)"%{"WG":wGov,"WD":wDep}
        govPL=self.gov.toPL()
        depPL=self.dep.toPL()
        if govPL:
            rule+=", "+govPL
        if depPL:
            rule+=", "+depPL
#         if self.gov.wordform:
#             rule+=",token(T%(W)s,_,WF%(W)s),accepts('%(SPEC)s',WF%(W)s)"%{"W":wGov,"SPEC":self.gov.wordform}
#         if self.dep.wordform:
#             rule+=",token(T%(W)s,_,WF%(W)s),accepts('%(SPEC)s',WF%(W)s)"%{"W":wDep,"SPEC":self.dep.wordform}
        for t in tokensSoFar:
            if t!=wGov:
                rule+=", T%s \= T%s"%(wGov,t)
            if t!=wDep:
                rule+=", T%s \= T%s"%(wDep,t)
        if not self.negation:
            tokensSoFar.add(wGov)
            tokensSoFar.add(wDep)
        if self.negation:
            return " \+ ( %s )"%rule
        else:
            return rule

        
class WordSpec:

    def __init__(self,handle,wordform):
        
        self.handle=handle
        self.wordform=None
        self.twb=None
        self.cgb=None
        self.twts=[]
        self.cgts=[]

        if wordform:
            parts=wordform.split("&")
            for part in parts:
                if part.startswith("LEMMA:"):
                    self.cgb="^("+part[6:]+")$"
                elif part.startswith("TAG:"):
                    self.cgts=part[4:].split("+")
                else:
                    self.wordform="^(%s)$"%part.replace("'",r"\'")

    def toPL(self):
        parts=[]
#        if self.twb:
#            parts.append("readingTWBase(T%s,T%sR,'%s')"%(self.handle,self.handle,self.twb))
        if self.cgb: #cgbase
            parts.append("readingCGBase(T%s,T%sR,'%s')"%(self.handle,self.handle,self.cgb))
#        for twt in self.twts:
#            parts.append("readingTWTag(T%s,T%sR,'%s')"%(self.handle,self.handle,twt))
        for cgt in self.cgts: #cgtags
            parts.append("readingCGTag(T%s,T%sR,'%s')"%(self.handle,self.handle,cgt))
        if parts:
            parts.insert(0,"reading(T%s,T%sR)"%(self.handle,self.handle))
        if self.wordform:
            parts.insert(0,"tokenWordForm(T%s,'%s')"%(self.handle,self.wordform))
        return ", ".join(parts)
                     
            

class Action:

    def __init__(self,lWordSpec,rWordSpec,lType,stratum):
        self.lWordSpec=lWordSpec
        self.rWordSpec=rWordSpec
        self.lType="%s"%lType
        if stratum==None:
            self.stratum=0
        else:
            self.stratum=stratum
        

    def isbackref(self):
        return self.lType.startswith("BACKREF::")


    def lTypeS(self):
        if self.lType.startswith("BACKREF::"):
            return "LT%s"%self.lType[9:] #Takes "BACKREF::" out
        else:
            return "'%s'"%self.lType

class Rule:

    def __init__(self,action,conditions,comment,lineno=0):
        self.action=action
        self.conditions=conditions
        self.lineno=lineno
        self.comment=comment[1:-1]
        if not self.comment:
            self.comment="EMPTYCOMMENT"

    def crosscheck(self):
        """Assumes sorting is done"""
        
        inPositive=set() #Have I seen this tokenSpec in a positive context?
        for c in self.conditions:
            if c.__class__==Condition and not c.negation:
                inPositive.add(c.gov.handle)
                inPositive.add(c.dep.handle)
            elif c.__class__==OrderCondition:
                if c.lWordSpec.handle not in inPositive:
                    raise ValueError("Token '%s' must be defined (in a positive context) before you can use it in order condition (in last rule defined before line %d)"%(c.lWordSpec.handle,self.lineno))
                elif c.rWordSpec.handle not in inPositive:
                    raise ValueError("Token '%s' must be defined (in a positive context) before you can use it in order condition (in last rule defined before line %d)"%(c.rWordSpec.handle,self.lineno))
        if self.action.lWordSpec.handle not in inPositive:
            raise ValueError("Left-hand side token '%s' undefined on line %d (in last rule defined before this line)"%(self.action.lWordSpec.handle,self.lineno))
        elif self.action.rWordSpec.handle not in inPositive:
            raise ValueError("Left-hand side token '%s' undefined on line %d (in last rule defined before this line)"%(self.action.rWordSpec.handle,self.lineno))

                
                    

    def toPL(self):
        tokensSoFar=set()
        self.conditions.sort(cmp=compareConditions)
        self.crosscheck()
        origins=sum(1 for c in self.conditions if c.origin==True)
        if origins>1:
            raise ValueError("You only can have max one origin. On line:",self.lineno)
        if origins==0:
            #don't have any origin marked, do 0,0,None
            o=",OG=0,OD=0,OT=\"None\""
        else:
            o=""
        ruleSets=(c.toPL(i+1,self.action.stratum,tokensSoFar) for i,c in enumerate(self.conditions))
        if self.action.isbackref():
            return "rule(T%(LW)s,T%(RW)s,ATDEP,OG,OD,OT,%(STRAT)s,\"%(COMMENT)s\") :- %(CONDS)s, atom_concat('@',%(NT)s,ATDEP)%(origin)s."%{"LW":self.action.lWordSpec.handle,"RW":self.action.rWordSpec.handle,"NT":self.action.lTypeS(),"CONDS":", ".join(ruleSets),"STRAT":self.action.stratum+1,"origin":o,"COMMENT":self.comment}
        else:
            conds=", ".join(ruleSets)
            return "rule(T%(LW)s,T%(RW)s,%(NT)s,OG,OD,OT,%(STRAT)s,\"%(COMMENT)s\") :- %(CONDS)s%(origin)s."%{"LW":self.action.lWordSpec.handle,"RW":self.action.rWordSpec.handle,"NT":self.action.lTypeS(),"CONDS":conds,"STRAT":self.action.stratum+1,"origin":o,"COMMENT":self.comment}
################# END OF CLASSES ######################

def compareConditions(c1,c2):
    if c1.__class__!=c2.__class__:
        if isinstance(c1,Condition):
            return -1 #conditions first, then only WordOrder
        else:
            return +1
    #Now I know that the classes match
    if isinstance(c1,OrderCondition):
        return cmp(c1.lWordSpec.handle,c2.lWordSpec.handle) #...whatever really
    #Now comparing real Conditions
    #Non-negated conditions must come first in prolog
    if c1.negation and not c2.negation:
        return 1
    elif not c1.negation and c2.negation:
        return -1
    assert c1.negation==c2.negation
    return cmp(len(c1.lType),len(c2.lType))#Pretty much whatever...
            
def convert(iFile,oFile,module=None):
    input=iFile.read()
#     if module:
#         lex.lex(module=module)
#         yacc.yacc(module=module)
#     else:
#         lex.lex()
#         yacc.yacc()
    lex.lexer.lineno=0
    rules=yacc.parse(input)
    strata=list(set(r.action.stratum+1 for r in rules))
    strata.sort()
    print >> oFile, "%stratumInfo(list of all strata, result stratum)"
    print >> oFile, "stratumInfo([%s],%d)."%(",".join(str(s) for s in strata),strata[-1])
    print >> oFile, ""
    print >> oFile, "%rule(token1,token2,dependency,stratum to which the dependency is generated"
    print>> oFile, ""
    print >> oFile, "% PROLOG RULES PASSED FROM THE RULE FILE"
    print >> oFile, "\n\n".join(plrules)
    print >> oFile, "\n\n% GENERATED PROLOG RULES"
    for r in rules:
        rpl=r.toPL()
        print >> oFile, rpl
        print >> oFile, ""


lex.lex()
yacc.yacc()

if __name__=="__main__":
    convert(sys.stdin,sys.stdout)
