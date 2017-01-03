In order to successfully compile the lp2lp transformation library,
you need to have the following environment:

1) Installation of SWI prolog with the development tools
   - header files in (by default) /usr/lib/swi-prolog/include (you can edit the Makefile if the headers are elsewhere)
   - libraries (at least):
        - libpl (prolog)
        - libgmp (numerical library for prolog)
   - the plld program (comes with SWI prolog)

2) Installation of PCRE with the development tools
   - header files (pcre.h)
   - libraries
        - libpcre


3) A 2.X Python

Then just type 'make'.
