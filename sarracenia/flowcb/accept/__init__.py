
"""

sarracenia.flowcb.accept modules are ones where the main focus is on the after_accept entry point.
This entry point is called after reject & accept rules have been called, and typically after
duplicate suppression has also been applied.

They can be used to further refine which files should be downloaded, by moving messages from the 
worklist.incoming to worklist.rejected.



"""

pass
