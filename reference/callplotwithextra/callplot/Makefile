PLOTTABLE=./plottable.sh

OUTPUTS=\

all : $(OUTPUTS)

%.html : %.msd
	$(PLOTTABLE) -style htmltable3 $< > $@
	open $@ # figure out how to use TWiki REST interface to update an attachment! 
