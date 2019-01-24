=============================
Windows detailed instructions
=============================

.. section-numbering::

This document teaches a novice user with Python on Windows how to run/install Sarracenia in various way.
The screenshots comes from Windows Server 2012

Run instructions
----------------

Run Sarracenia
~~~~~~~~~~~~~~

#. Install Sarracenia
#. Launch Sarracenia

   From the Start Menu:
     Clicking the shortcut will start (or restart) Sarracenia:

      .. image:: start-menu-1.png

     This will pop Sarracenia Command Prompt with logging informations.

      .. image:: sarra-prompt.png

     Closing this window or ctrl-c then kills all Sarracenia processes
     when you are done with Sarracenia.

   From Powershell (run as Administrator)::

     sr <start|restart> [myconf]

    From the Task Scheduler:
     blabla

    From Anaconda:
     activate sarracenia && sr <start|restart> [myconf]


Installation Instructions:
--------------------------

Install MetPX-Sarracenia
~~~~~~~~~~~~~~~~~~~~~~~~

#. Download **Windows installer** and execute it (click next all the way)
#. Add Sarracenia's Python directory to your **PATH**


Install MetPX-Sarracenia with Python.org
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Download and install python.org (latest):

    Take care of including python in PATH variable (checkbox)

#. Install paramiko and MetPX-Sarracenia:

    In Powershell (run as Administrator)::

     pip install paramiko
     pip install metpx-sarracenia

Install MetPX-Sarracenia with Anaconda prompt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install MetPX-Sarracenia and its dependencies all in once with this command:

    In Anaconda Prompt (run as Administrator)::

     conda env create -f environment.yml

Other Instructions
------------------

Create a task in Task Scheduler (both cases)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Open Server Manager > Tools > Task scheduler
#. From Actions panel, select::

    Create task...

   #. In the General tab::

       Name: MetPX-Sarracenia
       *: Run whether user is logged on or not
       x: Run with highest privileges

   #. In the Triggers tab, setup your schedule
   #. In the Actions tab add:

      * (usual case)::

         Action: Start a program
         Program/script: %PYTHON_PATH%\Scripts\sr.exe
         Add arguments (optional): restart myconf

      * (Anaconda case)::

         Action: Start a program
         Program/script: %SARRA_PATH%\sr_run.bat

       * sr_run.bat contains::

          activate sarracenia && sr restart myconf

   #. Save this config and enable it

