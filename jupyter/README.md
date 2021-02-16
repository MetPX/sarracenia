# Sarracenia Jupyter Notebooks

A collection of demonstrations of the various API's for subscribing to continuous data flows
from a Sarracenia data pump.

## Command Line Interface

With the Command Line interface, One can manage fleets of instances and configurations.

An instance is a process that runs a Sarracenia.flow whose configuration is set using
the sr3 configuration file tree and language, placing logs in a standard location, 
and where the starting, monitoring and stopping instances is done using sr3.  

This command line tools is used to manage hundreds of processes collaborating in 
webs to implement complete applications.

What is a flow? it is the following steps:

* gather (obtain new messages from a data pump, a remote polling source or a local directory.)
* filter ( apply accept/reject masks, then on_filter processing. )
* do ( do a download (most flows) or send, or whatever )
* outlet ( post message to a new pump for other flows to use, or write it to a file, or nothing. )


FIXME: missing notebook. Planned.

## Customization with Callbacks

FIXME: missing notebook. Planned.
The Sarracenia.flowcb or flow_callback class allows developers to implement custom processes

FIXME: missing notebook. Planned.

## Polling Callback Example.

There are many data sources that don't produce Sarracenia messages natively. To work with them,
one must poll them to ingest them into a data pumping network.

FIXME: missing notebook. Planned.


## Pure Python Sarracenia.Flow.Subscribe

With this API, one can run a complete download and repost component, fully participating in a Sarracenia data pump.
It runs the flow algorithm, including gathering information from an upstream source (either a pump or a directory tree.)
processing it, and allows posting afterwards. All configuration by configuring data structures in API calls.
Does not use configuration language.

Demonstration: [Sarracenia_flow_demo](Sarracenia_flow_demo.ipynb)


## Pure Python Sarracenia.Moth

the lightest weight / least intrusion into an existing code base would be to use
the sarracenia.moth api, and have the application ask for messages whenever it is ready
to digest them. Moth handles only interaction with a message broker, so the application 
is responsible for actual data downloads, error recovery, process management etc...

Demonstration: [Sarracenia_moth_demo.ipynb](Sarracenia_flow_demo.ipynb)
[mybinder.org](https://mybinder.org/v2/gh/MetPX/sarracenia/v03_wip?filepath=jupyter%2FSarracenia_moth_demo.ipynb)
