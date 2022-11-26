FROM ubuntu:14.04


# Get same version of GCC
RUN apt-get clean
RUN apt-get update -y --fix-missing 
RUN apt-get install -y g++-4.4 build-essential git parallel vim wget zlibc zlib1g zlib1g-dev wget curl software-properties-common libssl-dev
RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.4 10
RUN update-alternatives --config g++ 
RUN g++ --version

# Get python 
RUN wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tgz && \
    tar -xvf Python-3.6.3.tgz && \
    cd Python-3.6.3 && \
    ./configure --enable-optimizations && \
    make -j8 && \
    make install
RUN update-alternatives --install /usr/bin/python python /Python-3.6.3/python 1

# Get PIP
RUN curl https://bootstrap.pypa.io/pip/3.6/get-pip.py --output get-pip.py && \
    python  get-pip.py

#Set ENV locales
RUN apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8 

# Download indri
RUN wget --no-check-certificate https://sourceforge.net/projects/lemur/files/lemur/indri-5.6/indri-5.6.tar.gz/download -O indri-5.6.tar.gz
RUN tar xvfz indri-5.6.tar.gz
RUN cd /indri-5.6 && \
    ./configure && \
    make

# Get the paper's code
RUN git clone https://github.com/Zendelo/IRQPP.git

# Generate requirments for the paper
RUN pip3 install pipreqs && \
	pipreqs --mode no-pin /IRQPP

# Install requirments for IRQPP
RUN pip3 install -r /IRQPP/requirements.txt


RUN mkdir /indri-5.6/runqueryql && \
	cp /IRQPP/indri_code/* /indri-5.6/runqueryql/

ADD Makefile /indri-5.6/runqueryql/Makefile

RUN cd /indri-5.6/runqueryql/ && make





