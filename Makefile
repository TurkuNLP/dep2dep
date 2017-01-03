PLLD=swipl-ld
PROLOG=swipl
PLLDARGS=-pl $(PROLOG) -I/usr/lib/swi-prolog/include 
LIBS=-lpcre

all:  regex.so liblp2lp.so 

rules.pl: rules.lp2lp
	python lp2lp2pl.py < $< > $@

regex.o: regex.c regex.h
	$(PLLD) -c $(PLLDARGS) -o $@ regex.c

regex.so: regex.o
	gcc -shared -lpcre -o $@ $<

liblp2lp.o: liblp2lp.c liblp2lp.h
	$(PLLD) -c $(PLLDARGS) -o $@ liblp2lp.c

liblp2lp.so: liblp2lp.c liblp2lp.h lib_top.pl regex.o liblp2lp.o
	$(PLLD) -v -embed-shared $(PLLDARGS) $(LIBS) -lswipl -o $@ regex.o lib_top.pl liblp2lp.o

# testlp2lp: testlp2lp.c liblp2lp.o regex.o rules.pl
# 	plld -c $(PLLDARGS) -o testlp2lp.o testlp2lp.c
# 	plld -v $(PLLDARGS) $(LIBS) -o testlp2lp liblp2lp.o regex.o testlp2lp.o lib_top.pl

clean:
	rm -f regex.o liblp2lp.o liblp2lp.so testlp2lp.o testlp2lp parsetab.py rules.pl parser.out *.pyc regex.so *~
