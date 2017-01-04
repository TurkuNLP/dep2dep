# dep2dep

Treebank transformation tool. A vintage 2008 code, revived for Universal Dependencies treebank conversions.

# Example

Applies rewrite rules from `example_rules.lp2lp` to a small fragment of the English UD treebank.

    ./dtree_dep2dep.sh -r example_rules.lp2lp < ud_english_example.conllu > ud_english_example_tr.conllu

# Installation

## On Ubuntu 16.04 and probably other recent versions

The following is tested to work on the official [Ubuntu cloud image](https://help.ubuntu.com/lts/serverguide/cloud-images-and-uvtool.html)

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
