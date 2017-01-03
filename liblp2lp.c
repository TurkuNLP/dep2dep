/*
Copyright (C) 2007 University of Turku

This is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this software in the file COPYING. If not, see
http://www.gnu.org/licenses/lgpl.html
*/

#include <SWI-Prolog.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "liblp2lp.h"
#include "regex.h"

LP2LP_dep_t* current_result;

int LP2LP_init(char *argv0) {
    char *new_argv[1];
    new_argv[0]=argv0;
    PL_initialise(1,new_argv);
    PL_register_foreign("accepts",2,pl_accepts,0);
}

int LP2LP_new_token(int tokenSeq, wchar_t *tokenText) {
    fid_t fid=PL_open_foreign_frame();
    term_t t_tokenSeq=PL_new_term_refs(2);
    term_t t_tokenText=t_tokenSeq+1;
    predicate_t p=PL_predicate("new_token",2,NULL);
    qid_t query;
    int result;
    atom_t tokenTextAtom=PL_new_atom_wchars(wcslen(tokenText),tokenText);

    PL_put_integer(t_tokenSeq,tokenSeq);
    PL_put_atom(t_tokenText,tokenTextAtom);

    query=PL_open_query(NULL,PL_Q_NORMAL,p,t_tokenSeq);
    result=PL_next_solution(query);
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result;
}

void LP2LP_put_list(term_t l, int n, wchar_t **words) { 
  term_t a = PL_new_term_ref();
  atom_t wordAtom;

  PL_put_nil(l);
  while( --n >= 0 )
  { 
    wordAtom=PL_new_atom_wchars(wcslen(words[n]),words[n]);
    PL_put_atom(a, wordAtom);
    PL_cons_list(l, a, l);
  }
}

int LP2LP_new_reading(int tokenSeq, int readingSeq, int cg, wchar_t *baseForm, int n, wchar_t **tags) {
  //  puts(baseForm);

    fid_t fid=PL_open_foreign_frame();
    term_t t_tokenSeq=PL_new_term_refs(5);
    term_t t_readingSeq=t_tokenSeq+1;
    term_t t_cg=t_tokenSeq+2;
    term_t t_baseform=t_tokenSeq+3;
    term_t t_tags=t_tokenSeq+4;
    predicate_t p=PL_predicate("new_token_reading",5,NULL);
    qid_t query;
    int result;
    
    atom_t baseFormAtom=PL_new_atom_wchars(wcslen(baseForm),baseForm);

    PL_put_integer(t_tokenSeq,tokenSeq);
    PL_put_integer(t_readingSeq,readingSeq);
    PL_put_integer(t_cg,cg);
    PL_put_atom(t_baseform,baseFormAtom);
    LP2LP_put_list(t_tags,n,tags);

    query=PL_open_query(NULL,PL_Q_NORMAL,p,t_tokenSeq);
    result=PL_next_solution(query);
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result;
}

int LP2LP_load_ruleset(char *fileName) {
    fid_t fid=PL_open_foreign_frame();
    term_t t_fileName=PL_new_term_refs(1);
    predicate_t p=PL_predicate("load_ruleset",1,NULL);

    qid_t query;
    int result;

    PL_put_atom_chars(t_fileName,fileName);

    query=PL_open_query(NULL,PL_Q_NORMAL,p,t_fileName);
    result=PL_next_solution(query);
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result;
}

int LP2LP_perform_transformation() {
    fid_t fid=PL_open_foreign_frame();
    term_t t_term=PL_new_term_refs(0);
    predicate_t p=PL_predicate("generateAllStrata",0,NULL);

    qid_t query;
    int result;

    query=PL_open_query(NULL,PL_Q_NORMAL,p,t_term);
    result=PL_next_solution(query);
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result;

}


int LP2LP_new_dependency(int token1Seq, int token2Seq, char *depType) {
    fid_t fid=PL_open_foreign_frame();
    term_t t_tokenSeq1=PL_new_term_refs(3);
    term_t t_tokenSeq2=t_tokenSeq1+1;
    term_t t_dtype=t_tokenSeq2+1;
    predicate_t p=PL_predicate("new_dependency",3,NULL);
    qid_t query;
    int result;

    PL_put_integer(t_tokenSeq1,token1Seq);
    PL_put_integer(t_tokenSeq2,token2Seq);
    PL_put_atom_chars(t_dtype,depType);

    query=PL_open_query(NULL,PL_Q_NORMAL,p,t_tokenSeq1);
    result=PL_next_solution(query);
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result;

}



int LP2LP_transformed(int *count, int *resultStratum, LP2LP_dep_t **deps) {
    fid_t fid=PL_open_foreign_frame();
    
    predicate_t transformed_3=PL_predicate("transformed",3,NULL);
    term_t pl_deps=PL_new_term_refs(3);
    term_t pl_count=pl_deps+1;
    term_t pl_resstrat=pl_deps+2;
    term_t head=PL_new_term_ref();
    term_t head2=PL_new_term_ref();
    qid_t query;
    int result1,result2;
    int depIdx;
    char *s_tmp;

/*     query=PL_open_query(NULL,PL_Q_NORMAL,transform_0,NULL); */
/*     result1=PL_next_solution(query); */
/*     PL_close_query(query); */

    query=PL_open_query(NULL,PL_Q_NORMAL,transformed_3,pl_deps);
    result2=PL_next_solution(query);
    if (result2) {
	PL_get_integer(pl_count,count);
	PL_get_integer(pl_resstrat,resultStratum);
	*deps=(LP2LP_dep_t*) malloc(*count*sizeof(LP2LP_dep_t));
	depIdx=0;
	while(PL_get_list(pl_deps,head,pl_deps)) {
	    PL_get_list(head,head2,head); //Token1
	    PL_get_integer(head2,&((*deps)[depIdx].token1Seq));
	    PL_get_list(head,head2,head); //Token2
	    PL_get_integer(head2,&((*deps)[depIdx].token2Seq));
	    PL_get_list(head,head2,head); //Stratum
	    PL_get_integer(head2,&((*deps)[depIdx].stratum));
	    PL_get_list(head,head2,head); //Type
	    PL_get_chars(head2,&s_tmp,CVT_ATOM|BUF_DISCARDABLE);
	    (*deps)[depIdx].depType=(char*)malloc((strlen(s_tmp)+1)*sizeof(char));
	    strcpy((*deps)[depIdx].depType,s_tmp);
	    PL_get_list(head,head2,head); //OLDToken1
	    PL_get_integer(head2,&((*deps)[depIdx].token_old_1Seq));
	    PL_get_list(head,head2,head); //OLDToken2
	    PL_get_integer(head2,&((*deps)[depIdx].token_old_2Seq));
	    PL_get_list(head,head2,head); //OldType
	    PL_get_chars(head2,&s_tmp,CVT_ALL|BUF_DISCARDABLE);
	    (*deps)[depIdx].old_depType=(char*)malloc((strlen(s_tmp)+1)*sizeof(char));
	    strcpy((*deps)[depIdx].old_depType,s_tmp);
	    PL_get_list(head,head2,head); //Comment
	    PL_get_chars(head2,&s_tmp,CVT_ALL|BUF_DISCARDABLE);
	    (*deps)[depIdx].comment=(char*)malloc((strlen(s_tmp)+1)*sizeof(char));
	    strcpy((*deps)[depIdx].comment,s_tmp);
	    depIdx++;
	}
	current_result=*deps;
    }
    PL_close_query(query);

    PL_discard_foreign_frame(fid);
    return result2;
}

void LP2LP_single_result_dependency(int idx, int *leftToken, int *rightToken, int *stratum, char *depType, int *old_leftToken, int *old_rightToken, char *old_depType, char *comment) {
    *leftToken=current_result[idx].token1Seq;
    *rightToken=current_result[idx].token2Seq;
    *stratum=current_result[idx].stratum;
    *old_leftToken=current_result[idx].token_old_1Seq;
    *old_rightToken=current_result[idx].token_old_2Seq;
    *stratum=current_result[idx].stratum;
    strcpy(depType,current_result[idx].depType);
    strcpy(old_depType,current_result[idx].old_depType);
    strcpy(comment,current_result[idx].comment);
}

int LP2LP_transformed_count(int *resultStratum) {
    int count;
    LP2LP_dep_t *dontcare;
    LP2LP_transformed(&count, resultStratum, &dontcare);
    return count;
}

int LP2LP_destroy_result(int count, LP2LP_dep_t *deps) {
    int depIdx;
    if (deps==NULL) {
	deps=current_result;
    }
    for (depIdx=0; depIdx<count; depIdx++) {
	free(deps[depIdx].depType);
    }
    free(deps);
}

int LP2LP_new_sentence() {
    fid_t fid=PL_open_foreign_frame();
    predicate_t cleanup_0=PL_predicate("cleanup",0,NULL);
    term_t dummy=PL_new_term_ref();
    qid_t query;
    int result;

    query=PL_open_query(NULL,PL_Q_NORMAL,cleanup_0,dummy);
    result=PL_next_solution(query);
    PL_close_query(query);
    PL_discard_foreign_frame(fid);
    return result;
}
