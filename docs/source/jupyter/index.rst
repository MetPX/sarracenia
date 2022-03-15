Jupyter Notebook Tutorial Examples using CLI and APIs
=====================================================

.. toctree::
   :caption: Contents:

   1_CLI_introduction
   2_CLI_with_flowcb_demo
   3_api_flow_demo
   4_api_moth_sub_demo
   5_api_moth_post_demo


Sarracenia Jupyter Notebooks
----------------------------

A collection of demonstrations of the various API's for subscribing to continuous data flows
from a Sarracenia data pump.

Setting up a local environment::

    python3 -m venv sarracenia
    cd sarracenia
    . bin/activate  # yes, that is a period
    git clone https://github.com/MetPX/sarracenia.git
    cd sarracenia
    git checkout v03_wip
    cd jupyter
    pip install -r requirements.txt
    jupyter notebook --ip=0.0.0.0 --port=8040

Another option, establish a virtual machine running ubuntu 20.04 or later::

    sudo apt update ; sudo apt upgrade
    sudo apt install git python3-pip
    export PATH="${HOME}/.local/bin:${PATH}"
    git clone -b v03_wip https://github.com/MetPX/sarracenia.git sr3
    cd sr3
    pip3 install -e .
    pip3 install -r requirements-dev.txt 
    cd docs/source/jupyter
    ip addr show # to know the ip to point your browser at.
    jupyter notebook --ip=0.0.0.0 --port=8040
    # open broser on ip:8040
    #look for the certificate to post as credential for browser. 
    # in the startup text.

Command Line Interface
----------------------

An introduction to the command Line interface, used to manage fleets of instances and configurations.
The sr3 configuration file tree and language, places logs in a standard location, 
and where the starting, monitoring and stopping instances is done using sr3.  

Demonstration: `1_CLI_introduction.ipynb <1_CLI_introduction.ipynb>`_


Customization with Callbacks
----------------------------

What is a flow? it is the following steps:

* gather (obtain new messages from a data pump, a remote polling source or a local directory.)
* filter ( apply accept/reject masks, then on_filter processing. )
* work ( do a download (most flows) or send, or whatever )
* post ( post message to a new pump for other flows to use, or write it to a file, or nothing. )

Demonstration: `2_CLI_with_flowcb_demo <2_CLI_with_flowcb_demo>`_



FIXME: missing notebook. Planned.
The Sarracenia flowCallback (sarracenia.flowcb.FlowCB) class allows developers to implement custom processes

FIXME: missing notebook. Planned.

Polling Callback Example
------------------------

There are many data sources that don't produce Sarracenia messages natively. To work with them,
one must poll them to ingest them into a data pumping network.

FIXME: missing notebook. Planned.


Pure Python Sarracenia.Flow.Subscribe
-------------------------------------

With this API, one can run a complete download and repost component, fully participating in a Sarracenia data pump.
It runs the flow algorithm, including gathering information from an upstream source (either a pump or a directory tree.)
processing it, and allows posting afterwards. All configuration by configuring data structures in API calls.
Does not use configuration language.

Demonstration: `3_api_flow_demo <3_api_flow_demo.ipynb>`_


Pure Python Sarracenia.Moth
---------------------------

the lightest weight / least intrusion into an existing code base would be to use
the sarracenia.moth api, and have the application ask for messages whenever it is ready
to digest them. Moth handles only interaction with a message broker, so the application 
is responsible for actual data downloads, error recovery, process management etc...

Demonstrations: `4_api_moth_sub_demo.ipynb <4_api_moth_sub_demo.ipynb>`_ `5_api_moth_post_demo <5_api_moth_post_demo>`_
