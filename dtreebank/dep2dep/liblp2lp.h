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

#ifndef _lp2lp_h_
#define _lp2lp_h

typedef struct {
    int token1Seq;
    int token2Seq;
    char *depType;
    int stratum;
    int token_old_1Seq;
    int token_old_2Seq;
    char *old_depType;
  char *comment;
} LP2LP_dep_t;

/* 
  Initialize the LP2LP machinery. Call exactly once.
*/
int LP2LP_init(char *argv0);

/*
  Load a ruleset.
*/
int LP2LP_load_ruleset(char *filename);

/*
  Clean up before new sentence. You have to call this before
  every new sentence you want to convert - also before the
  first sentence to be converted (this function is not called
  from LP2LP_init().
*/
int LP2LP_new_sentence();
  

/* 
   Add one token to the Prolog sentence representation.
   The tokens must come in their correct sequential order.
*/
int LP2LP_new_token(int tokenSeq,wchar_t *tokenText);

/* 
   Add one dependency to the Prolog sentence representation.
   The dependencies do not need to come in any particular
   order. But it is assumed that always token1Seq<token2Seq.
*/
int LP2LP_new_dependency(int token1Seq, int token2Seq, char *depType);


/*
  Performs the transformation.
*/
int LP2LP_perform_transformation();

/* 
   Returns a newly allocated array of count dependencies in the
   transformed format, from all strata. The user of this
   function is responsible for destroying this array when it is not
   needed anymore. Use LP2LP_destroy_result for this.
*/
int LP2LP_transformed(int *count, int *result_stratum, LP2LP_dep_t **deps);


/*
  UTILITY FUNCTION FOR PYTHON BINDING
  Runs LP2LP_transformed and returns the count. The resulting dependencies can be retrieved
  one by one using LP2LP_single_result_dependency
*/
int LP2LP_transformed_count(int *result_stratum);

/*
  UTILITY FUNCTION FOR PYTHON BINDING
  The result is being held in a global variable. This will return one dependency.
  It is basically a way to iteratively export the dependencies without the ** hassle.

  It will return the type of the idx-th result dependency and fill in the left and right token index
  into leftToken and rightToken.
*/
void LP2LP_single_result_dependency(int idx, int *leftToken, int *rightToken, int *stratum, char *depType, int *old_leftToken, int *old_rightToken, char *old_depType, char *comment);

/*
  Frees the memory allocated for the result. If you pass a NULL pointer, the last result
  is destroyed. This is useful for the Python binding.
*/
int LP2LP_destroy_result(int count, LP2LP_dep_t *r);


#endif
