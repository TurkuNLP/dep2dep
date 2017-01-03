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
#include <ctype.h>
#include <pcre.h>
#include <string.h>
#include <stdio.h>

foreign_t pl_accepts_flags(term_t patternTerm, term_t stringTerm, int extraFlags) {
    char *string,*pattern;
    pcre *regex;
    const char *error;
    int erroroffset;
    int ovector[30];
    int r;
    PL_get_chars(stringTerm, &string, CVT_ATOM|REP_UTF8);
    PL_get_chars(patternTerm, &pattern, CVT_ATOM|REP_UTF8);
    regex=pcre_compile(pattern, PCRE_ANCHORED|PCRE_UTF8|extraFlags, &error, &erroroffset, NULL);
    if (regex==NULL) {
        printf("Regex: Compilation failed\n");
        PL_fail;
    }
    r=pcre_exec(regex,NULL,string,strlen(string),0,0,ovector,30);
    pcre_free(regex);
    if (r>=0) {
        PL_succeed;
    }
    else {
        PL_fail;
    }
}

foreign_t pl_accepts(term_t patternTerm, term_t stringTerm) {
    return pl_accepts_flags(patternTerm, stringTerm, 0);
}


foreign_t pl_accepts_caseless(term_t patternTerm, term_t stringTerm) {
    return pl_accepts_flags(patternTerm, stringTerm, PCRE_CASELESS);
}


/* foreign_t pl_accepts(term_t patternTerm, term_t stringTerm) { */
/*     char *string,*pattern; */
/*     pcre *regex; */
/*     const char *error; */
/*     int erroroffset; */
/*     int ovector[30]; */
/*     int r; */
/*     PL_get_atom_chars(stringTerm, &string); */
/*     PL_get_atom_chars(patternTerm, &pattern); */
/*     regex=pcre_compile(pattern,PCRE_ANCHORED,&error,&erroroffset,NULL); */
/*     if (regex==NULL) { */
/* 	printf("Compilation failed\n"); */
/* 	PL_fail; */
/*     } */
/*     r=pcre_exec(regex,NULL,string,strlen(string),0,0,ovector,30); */
/*     if (r>=0) { */
/* 	PL_succeed; */
/*     } */
/*     else { */
/* 	PL_fail; */
/*     } */
/* } */
    

install_t
install() {
    PL_register_foreign("accepts", 2, pl_accepts, 0);
    PL_register_foreign("accepts_caseless", 2, pl_accepts_caseless, 0);
}
