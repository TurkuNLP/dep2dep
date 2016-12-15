from ctypes import *
import lp2lp2pl
import tempfile
import sys

class LP2LP:

    def __init__(self,prologDir="."):
        self.prologDir=prologDir
        self.lp2lp=cdll.LoadLibrary(prologDir+"/liblp2lp.so")
        self.lp2lp.LP2LP_init(prologDir+"/liblp2lp.so")
        self.lp2lp.LP2LP_single_result_dependency.restype=None


    def load_ruleset(self,fileName):
        self.lp2lp.LP2LP_load_ruleset(fileName)

    #Returns a dictionary with strata as keys and dependency
    #lists as values
    def transformSentence(self,tokenList,dependencyList,tokenReadings):
        self.lp2lp.LP2LP_new_sentence()
        for idx,t in enumerate(tokenList):
            self.lp2lp.LP2LP_new_token(idx,t)
            #print >> sys.stderr, ">>>", idx, t
        for tidx,tRs in enumerate(tokenReadings):
            for ridx,(cg,base,tags) in enumerate(tRs):
                tags=tags.split("|")
                arr = (c_wchar_p * (len(tags)))()
                for idx,tag in enumerate(tags):
                    arr[idx]=tag
                if cg:
                    cgInt=1
                else:
                    cgInt=0
                self.lp2lp.LP2LP_new_reading(tidx,ridx,cgInt,base,len(tags),arr)
        for (gov,dep,dType) in dependencyList:
            self.lp2lp.LP2LP_new_dependency(gov,dep,dType)
            #print >> sys.stderr, ">>>", idx1, idx2, dType
        self.lp2lp.LP2LP_perform_transformation()
        res_stratum=c_int()
        count=self.lp2lp.LP2LP_transformed_count(byref(res_stratum));
        t1=c_int()
        t2=c_int()
        dtype=create_string_buffer(256)
        old_t1=c_int()
        old_t2=c_int()
        stratum=c_int()
        old_dtype=create_string_buffer(256)
        comment=create_string_buffer(256)
        result={} #Key: stratum, value: list of [tok1,tok2,Type]
        for idx in range(count):
            self.lp2lp.LP2LP_single_result_dependency(idx,byref(t1),byref(t2),byref(stratum),byref(dtype),byref(old_t1),byref(old_t2),byref(old_dtype),byref(comment))
            gov=t1.value
            dep=t2.value
            old_gov=old_t1.value
            old_dep=old_t2.value
            result.setdefault(stratum.value,[]).append((gov,dep,dtype.value,old_gov,old_dep,old_dtype.value,comment.value))
        self.lp2lp.LP2LP_destroy_result(count,None)
        for i in range(0,res_stratum.value+1):
            if i not in result:
                result[i]={}
        return result
            
        


if __name__=="__main__":
    lp2lp=LP2LP(".")
    lp2lp.load_ruleset("rules.pl")
    print lp2lp.transformSentence("A B C D".split(),\
                                      [(0,1,"appos>"),\
                                       (2,3,"<nn"),\
                                       (0,3,"subj>")]
                                  )
    
    
