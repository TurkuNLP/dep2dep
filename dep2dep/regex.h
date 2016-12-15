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

#ifndef _regex_h_
#define _regex_h_

foreign_t pl_accepts(term_t patternTerm, term_t stringTerm);
foreign_t pl_accepts_caseless(term_t patternTerm, term_t stringTerm);

#endif
