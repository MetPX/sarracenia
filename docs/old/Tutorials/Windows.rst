===================
Windows user manual
===================

.. no section-numbering::

This document teaches novice user with Python on Windows how they could easily run Sarracenia in various way. 
The screenshots were taken from *Windows Server 2012 R2 Standard* edition. Feel free to create issues if you believe that this
document could be enhanced with one (or more) important case(s).

.. Contents::

Running Sarracenia with a Command Prompt
----------------------------------------
From the Start Menu:
~~~~~~~~~~~~~~~~~~~~
Click on Sarracenia (it will execute *sr.exe restart*):

.. image:: Windows/start-menu-1.png

This will pop Sarracenia's Command Prompt, start Sarracenia processes as instructed by your configurations and show logging information.

.. image:: Windows/sarra-prompt.png

Keep this window alive until you are done with Sarracenia. Closing it or typing ctrl-c will kill all Sarracenia processes. You may also want to restart Sarracenia which will stop those processes cleanly.

From a Windows Powershell session:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Launch a Powershell |powershell| session and type this command at the prompt::

 sr restart

.. |powershell| image:: Windows/powershell.png

This will start Sarracenia processes as instructed by your configurations and show logging information

.. image:: Windows/sarra-psprompt.png 

Keep this Powershell session alive until you are done with Sarracenia. To stop Sarracenia you may type::

 sr stop

This will stop all Sarracenia processes cleanly as would do a restart. Closing this window will also kill all processes.

From Anaconda Prompt:
~~~~~~~~~~~~~~~~~~~~~
Run this command::

 activate sarracenia && sr restart

Running Sarracenia without a Command Prompt
-------------------------------------------
Here is a case where someone (like a sysadmin) needs to run Sarracenia without a Command Prompt and ensure that the system starts at Windows startup.
The obvious way of doing it would be from the Task Scheduler.

From the Task Scheduler:
~~~~~~~~~~~~~~~~~~~~~~~~
Open Server Manager > Tools > Task scheduler:

.. image:: Windows/task-scheduler_start.png

Select *Create Basic Task* from the action panel:

.. image:: Windows/create-basic-task.png

This will launch the *Create Basic Task Wizard* where you ...

 Fill the name:

 .. image:: Windows/cbtw_name.png

 Choose the trigger:

 .. image:: Windows/cbtw_trigger.png

 Choose the action:
 
 .. image:: Windows/cbtw_action.png
 
 Define the action:
 
 .. image:: Windows/cbtw_action_program.png
 
 Review the task and choose *Finish*:
 
 .. image:: Windows/cbtw_finish.png
 
Open the *Properties dialog* and choose *Run whether user is logged on or not* and *Run with highest privileges*:
 
.. image:: Windows/ssp_general.png

The task should now appear in your *Task Scheduler Library* with the status *Ready*.

.. image:: Windows/ts_results.png

Then, you may run it immediately with the |run_action| button.

.. |run_action| image:: Windows/run_action.png
