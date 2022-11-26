include ../MakeDefns
SHARED=
INCPATH=-I../include $(patsubst %, -I../contrib/%/include, $(DEPENDENCIES))
LIBPATH=-L../obj  $(patsubst %, -L../contrib/%/obj, $(DEPENDENCIES))
LIBS=-lindri $(patsubst %, -l%, $(DEPENDENCIES))

all:
		$(CXX) -g $(CXXFLAGS) LogQlC.cpp -o LogQlC $(LIBPATH) $(LIBS) $(CPPLDFLAGS)
		$(CXX) -g $(CXXFLAGS) IndriRunQueryQL.cpp -o IndriRunQueryQL $(LIBPATH) $(LIBS) $(CPPLDFLAGS)
		$(CXX) -g $(CXXFLAGS) PreRetrievalIndri.cpp -o PreRetrievalIndri $(LIBPATH) $(LIBS) $(CPPLDFLAGS)
		$(CXX) -g $(CXXFLAGS) QueryStem.cpp -o QueryStem $(LIBPATH) $(LIBS) $(CPPLDFLAGS)
		$(CXX) -g $(CXXFLAGS) RMmodelProb.cpp -o RMmodelProb $(LIBPATH) $(LIBS) $(CPPLDFLAGS)

install:
		$(INSTALL_PROGRAM) $(APP) $(bindir)

clean:
		rm -f LogQlC  IndriRunQueryQL PreRetrievalIndri QueryStem RMmodelProb
