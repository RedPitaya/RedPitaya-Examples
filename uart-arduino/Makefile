CFLAGS  = -Wall ## -Werror
LDLIBS += -lm -lstdc++ -lpthread


# List of compiled object files (not yet linked to executable)

PRGS =  uart


OBJS := $(patsubst %,%.o,$(PRGS))
SRC := $(patsubst %,%.cpp,$(PRGS))

all: $(PRGS)

$(PRGS): %: %.cpp
	$(CXX) $< $(CFLAGS) $(LDFLAGS) $(LDLIBS) -o $@

clean:
	$(RM) *.o
	$(RM) $(OBJS)

clean_all: clean
	$(RM) $(PRGS)

