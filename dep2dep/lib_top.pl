% Copyright (C) 2008 University of Turku

% This is free software; you can redistribute it and/or
% modify it under the terms of the GNU Lesser General Public
% License as published by the Free Software Foundation; either
% version 2.1 of the License, or (at your option) any later version.

% This software is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
% Lesser General Public License for more details.

% You should have received a copy of the GNU Lesser General Public
% License along with this software in the file COPYING. If not, see
% http://www.gnu.org/licenses/lgpl.html


:-dynamic(defaultParse/1,sd:token/3,sd:d_link/9,rule/8,sd:reading/4).
:-import(lists).
%:-load_foreign_library('regex').

defaultParse('default').

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%  Predicates to interface world, and in particular the C library
%%%%  these should be used to assert the information about the sentence
%%%%  and to collect the result
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Predicates to feed in all tokens and dependencies of the input sentence
new_token(TokenSeq,TokenText):-sd:assert(token(TokenSeq,TokenSeq,TokenText)).


new_token_reading(TokenSeq,ReadingSeq,CG,Base):-
	sd:assert(reading(TokenSeq,ReadingSeq,CG,Base,[])).

new_token_reading(TokenSeq,ReadingSeq,CG,Base,TagList):-
	sd:assert(reading(TokenSeq,ReadingSeq,CG,Base,TagList)).



new_dependency(Token1,Token2,DType):-new_dependency(Token1,Token2,DType,0). %Default parse, stratum 0
new_dependency(Token1,Token2,DType,Stratum):-defaultParse(DP),new_dependency(Token1,Token2,DType,0,0,"None",DP,Stratum,""). %Default parse
new_dependency(Token1,Token2,DType,TOLD1,TOLD2,OldType,Stratum,Comment):-defaultParse(DP),new_dependency(Token1,Token2,DType,TOLD1,TOLD2,OldType,DP,Stratum,Comment). %Default parse

%% new_dependency(Token1,Token2,DType,Parse,Stratum):-
%% 	(tokenOrder(Token1,Token2)
%% 	->
%% 	    sd:assert(d_link(Token1,Token2,DType,Parse,Stratum))
%% 	;
%% 	    sd:assert(d_link(Token2,Token1,DType,Parse,Stratum))
%% 	).


%%%%% Query predicates
reading(TokenSeq,ReadingSeq):-
	sd:reading(TokenSeq,ReadingSeq,_,_,_).

tokenWordForm(TokenSeq,TokenText):-
	sd:token(TokenSeq,TokenSeq,TokenTextX),accepts(TokenText,TokenTextX).

readingTWBase(TokenSeq,ReadingSeq,Base):-
	sd:reading(TokenSeq,ReadingSeq,_,Base2,_),accepts(Base,Base2).

readingCGBase(TokenSeq,ReadingSeq,Base):-
	sd:reading(TokenSeq,ReadingSeq,1,Base2,_),accepts(Base,Base2).

readingTWTag(TokenSeq,ReadingSeq,Tag):-
	sd:reading(TokenSeq,ReadingSeq,_,_,Tags),memberchk(Tag,Tags).

readingCGTag(TokenSeq,ReadingSeq,Tag):-
	sd:reading(TokenSeq,ReadingSeq,1,_,Tags),memberchk(Tag,Tags).



%%%Change of logic here wrt previous. Now all deps are coded as (gov,dep,dType)
new_dependency(TokenGov,TokenDep,DType,TOLD1,TOLD2,OldType,Parse,Stratum,Comment):-
	sd:assert(d_link(TokenGov,TokenDep,DType,Parse,Stratum,TOLD1,TOLD2,OldType,Comment)).


% Ruleset loading
load_ruleset(FileName):-retractall(rule(_,_,_,_,_,_,_,_)),consult(FileName).

%%%%This is the main predicate of the transformation itself
generateAllStrata:-
	stratumInfo(StrataList,_),
	maplist(generateStratum,StrataList).


% Call to obtain the result as a set of [T1,T2,Type] tuples
transformed(Set,Length,ResStratum):-
	defaultParse(DP),
	stratumInfo(_,ResStratum),
	setof([T1,T2,Stratum,Type,TOLD1,TOLD2,OldType,Comment],sd:d_link(T1,T2,Type,DP,Stratum,TOLD1,TOLD2,OldType,Comment),Set),length(Set,Length),!.
%rule_normalized takes care of normalizing dependency directions for dependency types starting with "@"
%transformed(Set,Length,Stratum):-setof([T1,T2,Type],rule_normalized(T1,T2,Type,Stratum),Set),length(Set,Length),!.
transformed([],0).

				% This needs to be called before new sentence is inserted. It cleans up whatever was known
% about the previous sentence
cleanup:-forall(predicate_property(sd:Head, dynamic),retractall(sd:Head)).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%% TRANSFORMATION PREDICATES

% +Stratum is the stratum whose rules shall be applied
% -TDeps is a set of [Token,Token,Type,Stratum]
transformStratum(Stratum,TDeps):-setof([T1,T2,Type,TOLD1,TOLD2,OldType,Stratum,Comment],rule_normalized(T1,T2,Type,TOLD1,TOLD2,OldType,Stratum,Comment),TDeps).

store_dependency([T1,T2,DType,TOLD1,TOLD2,OldType,Stratum,Comment]):-new_dependency(T1,T2,DType,TOLD1,TOLD2,OldType,Stratum,Comment).
store_dependencies(TDeps):-maplist(store_dependency,TDeps).

generateStratum(Stratum):-
	transformStratum(Stratum,TDeps),
	store_dependencies(TDeps).
generateStratum(_).%We get here for empty strata - a highly theoretical case!



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%% THE @-NORMALIZATION

%%%Old code - don't know what this does...

rule_normalized(T1,T2,NewType,TOLD1,TOLD2,OldType,Stratum,Comment):-
	rule(T1,T2,Type,TOLD1,TOLD2,OldType,Stratum,Comment),
	(atom_concat('@',AType,Type)
	-> %does the type start with '@'?
	    infer_direction(T1,T2,AType,NewType) %yes!
	;
	    NewType=Type %no!
	).

infer_direction(T1,T2,AType,NewType):-
	%Drop any direction marker
	drop_marker(AType,AType2),
	(tokenOrder(T1,T2)
	->
	    atom_concat(AType2,'>',NewType)
	;
	    atom_concat('<',AType2,NewType)
	).

drop_marker(OldType,NewType):-
	atom_concat('<',NewType,OldType),!.
drop_marker(OldType,NewType):-
	atom_concat(NewType,'>',OldType),!.
drop_marker(OldType,OldType).

% Enforce a particular order of T1 and T2
tokenOrder(T1,T2):-sd:token(T1,Pos1,_),token(T2,Pos2,_),Pos1<Pos2.
% Relationship of T2 with respect to T1 (mostly useful in sublist calls)
before(T1,T2):-tokenOrder(T2,T1).
after(T1,T2):-tokenOrder(T1,T2).


%%%%%%%%%%%%%% TESTS ALLOWABLE IN THE RIGHT_HAND SIDE OF THE RULES %%%%%%%%%%%%%%%%%%%%%


%Make sd:token accessible here
token(T,POS,TXT):-sd:token(T,POS,TXT).
dependency(T1,T2,DType,Stratum):-
	defaultParse(DP),
	sd:d_link(T1,T2,DType,DP,Stratum,_,_,_,_).



% %%%%%%%%%%%%%%%%%% LIBRARY TEST %%%%%%%%%%%%%%%%%%%%%%

% % ---------subj>---------
% % --appos>-      --<nn---
% % A       B      C      D

% test(X,Y):-
% 	cleanup,
% 	load_ruleset('rules.pl'),
% 	new_token(1,'A'),
% 	new_token(2,'B'),
% 	new_token(3,'C'),
% 	new_token(4,'D'),
% 	new_dependency(1,2,'appos>'),
% 	new_dependency(3,4,'<nn'),
% 	new_dependency(1,4,'subj>'),
% 	transformed(X,Y).
