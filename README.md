Treebank transformation tool. A vintage 2008 code, revived for Universal Dependencies treebank conversions.

# Running

Apply rewrite rules from `example_rules.lp2lp` to a small fragment of the English UD treebank. CoNLL-U in. CoNLL-U out.

    ./dtree_dep2dep.sh -r example_rules.lp2lp < ud_english_example.conllu > ud_english_example_tr.conllu
    
# Rule syntax

Documented in `example_rules.lp2lp`.

# Installation

`dep2dep` uses Prolog as the back-end rule application engine, and a little shimming module to pass data between Python and Prolog, which needs to be compiled (no Cython back then). On a newish system, this should be as easy as installing a handful of packages and then typing `make`.

## Ubuntu

The following is tested to work on the official [Ubuntu cloud image](https://help.ubuntu.com/lts/serverguide/cloud-images-and-uvtool.html) 16.04

```
sudo apt install git build-essential swi-prolog-nox libpcre3-dev python-dev 
git clone https://github.com/TurkuNLP/dep2dep.git
cd dep2dep
make
./dtree_dep2dep.sh -r example_rules.lp2lp < ud_english_example.conllu
```

## Generic instructions 

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

3) A 2.X Python with header files

Then just type 'make'.

## Debugging

The `Makefile` and `dtree_dep2dep.sh` have few hard-coded paths. So if you have libraries and headers in non-standard locations, then you may get errors about missing symbols and the like. Just check and fix these paths.
