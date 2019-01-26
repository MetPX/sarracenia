==============================================
Windows Run / Deployment Scenarios
==============================================

.. section-numbering::

This document formalize what a Windows user should expect to do to use/install MetPX-Sarracenia in a Windows environment

Run scenarios
-------------

Run Sarracenia from Powershell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install MetPX-Sarracenia with (Powershell | a GUI installer)
#. Launch Sarracenia

    In Powershell (run as Administrator)::

     sr <start|restart> myconf

Run Sarracenia from Anaconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install MetPX-Sarracenia with Anaconda prompt
#. Launch Sarracenia:

    In Anaconda Prompt (run as Administrator)::

     activate sarracenia && sr <start|restart> myconf

Run Sarracenia from *outside* Powershell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install MetPX-Sarracenia with (Powershell | a GUI installer)
#. Create a task in Task Scheduler (usual case)

Run Sarracenia from *outside* Anaconda Prompt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install MetPX-Sarracenia with Anaconda prompt
#. Create a task in Task Scheduler (Anaconda case)

Installation scenarios:
-----------------------

Install MetPX-Sarracenia with a GUI installer (not implemented yet)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch sarracenia_install.exe and follow Wizard instructions.


Install MetPX-Sarracenia with Powershell
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

Other Scenarios
---------------

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

