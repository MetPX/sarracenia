=============================
Windows detailed instructions
=============================

.. no section-numbering::

This document teaches a novice user with Python on Windows how to run/install Sarracenia in various way. 
The screenshots were taken from Windows Server 2012

Running Sarracenia with a Command Prompt
----------------------------------------
From the Start Menu:
~~~~~~~~~~~~~~~~~~~~
Click on Sarracenia (it will execute *sr.exe restart*):

.. image:: start-menu-1.png

This will pop Sarracenia's Command Prompt, start Sarracenia processes as instructed by your configurations and show logging information.

.. image:: sarra-prompt.png

Keep this window alive until you are done with Sarracenia. Closing it or typing ctrl-c will kill all Sarracenia processes. You may also want to restart Sarracenia which will stop those processes cleanly.

From a Windows Powershell session:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Launch a Powershell |powershell| session and type this command at the prompt::

 sr restart

.. |powershell| image:: powershell.png

This will start Sarracenia processes as instructed by your configurations and show logging information

.. image:: sarra-psprompt.png 

Keep this Powershell session alive until you are done with Sarracenia. To stop Sarracenia you may type::

 sr stop

This will stop all Sarracenia processes cleanly as would do a restart. Closing this window will also kill all processes.

From Anaconda:
~~~~~~~~~~~~~~
 activate sarracenia && sr <start|restart> [myconf]

Running Sarracenia without a Command Prompt
-------------------------------------------

From the Task Scheduler:
~~~~~~~~~~~~~~~~~~~~~~~~
 blabla

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

