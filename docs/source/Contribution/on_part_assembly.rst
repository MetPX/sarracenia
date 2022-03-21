==================
File Re-assembling
==================


Components
----------

**sr_watch:** You can use sr_watch to watch a directory for incoming partition files (.Part) from sr_subscribe or sr_sender, both have the ability to send a file in partitions. In the config file for sr_watch the important parameters to include are:  

		- path <path of directory to watch>
		- on_part /usr/lib/python3/dist-packages/sarra/plugins/part_file_assemble.py
		- accept \*.Part
		- accept_unmatch False # Makes it only acccept the pattern above

**Part_File_Assemble (plugin):** This plugin is an on_part plugin which triggers the assembly code in **sr_file** 

**sr_file:** Contains the reassembly code... The algorithm is described below


Algorithm 
---------

After being triggered by a downloaded part file:  
  
 - if the target_file doesn't exist:
 
     - if the downloaded part file was the first partition (Part 0):
     
         - create a new empty target_file
	 
 - find which partition number needs to be inserted next (i)
 
 - while i < total blocks:
 
     - file_insert_part()
     
         - inserts the part file into target file and computes checksum of the inserted portion
	 
     - verify insertion by comparing checksums of partition file and inserted block in the file
     - delete file if okay, otherwise retry
     - trigger on_file
    

Testing
-------

Create an sr_watch config file according to the template above
Start the process by typing the following command: ```sr_watch foreground path/to/config_file.cfg```

Then create a subcriber config file and include ```inplace off``` so the file will be downloaded in parts
Start the subscriber by typring ```sr_subscribe foreground path/to/config_file.cfg```

Now, you must send post messages of the file for the subscriber
for example: ```./sr_post.py -pb amqp://tsource@localhost/ -pbu sftp://<user>@localhost/ -p /home/<user>/test_file -px xs_tsource  --blocksize 12M```


