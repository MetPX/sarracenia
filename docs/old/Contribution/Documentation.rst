=======================
Documentation Standards
=======================

..  contents:: Table of Contents

Folder Structure
~~~~~~~~~~~~~~~~~

Before starting work with documentation read `the entire divo documentation article
<https://documentation.divio.com/>`_ (and the links on the left hand sidebar).
It'll take no longer than 30 minutes and you'll gain a complete understanding of the
expected structure, style and content of the documentation here.

.. Backup divo link in case site dies : https://github.com/divio/diataxis-documentation-framework/
.. image:: https://documentation.divio.com/_images/overview.png
  :target: https://documentation.divio.com/

We look to the unix directive in our documentation, each documentation file does one thing
and does it well with respect to the 4 quadrants.


.. note:: TODO:Add example links to each of the below sections:

Tutorials
---------
- Learning-oriented, specifically learning how rather than learning *that*.
- Allow the user to learn by doing to get them started, be sure your tutorial works and users can see results immediately. 
- Tutorials must be reliably repeatable focused on concrete steps (not abstract concepts) with the minimum necessary explanation.

How2Guides
----------
- Problem and goal oriented: "**I want to... How do I...**" Differing from tutorials in that tutorials are for complete beginners, how to guides assume some knowledge and understanding with a basic setup and tools.
- Provide a series of steps focused on the results of some particular problem. 
- Don't explain concepts, if they are important, they can be linked to in `../Explanations/`
- There are multiple ways to skin a cat, remain flexible in your guide so users can see *how* things are done.
- **NAME GUIDES WELL** enough to tell the user *exactly* what they do at a glance.

Explanations
------------
- Understanding-oriented: can be equally considered discussions. Much more relaxed version of documentation where concepts are explored from a higher level or different perspectives.
- Provide context, discuss alternatives and opinions while providing technical reference (for other sections).

Reference
---------
- Information oriented: code-determined descriptions of functionality.
- Strictly for the man pages and direct reference of the various programs, protocols, and functions.

Contribution
------------
- Information critical to the enhancement and progression of the Sarracenia project, ie: for those that are looking to develop Sarracenia.
- Style guide(s)
- Template(s)

Process
~~~~~~~

The development process is to write up what one intends to do or have done into
a `reStructuredText <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html>`_
file in `/docs/Explanation/Design/`. Ideally, the discussion of information there acts
as a starting point which can be edited into documentation for the feature(s) as they 
are implemented. Each new component sr\_<whatever>, needs to have relevant man pages
implemented. The how to guides and tutorials should also be revised to reflect additions
or changes of the new component.

.. error:: Need Peter to help ID worthy information in doc/design to pull over to 
    /docs/Explanation/Design/

Updating the Wiki
-----------------
The wiki in GitHub is a separate Git project that has been grafted into the main project
as a subtree in /docs/. This means that any changes to the wiki pages in /docs/ will not
be updated on the web wiki until the changes are pushed to the subtree. This can be
achieved by pushing changes to the main project then executing the following command::

  $ git subtree push --squash --prefix docs git@github.com:MetPX/sarracenia.wiki.git master

.. caution:: 
    Editing things via the web interface will get overwritten. Only make changes to the
    documentation via the main project's /docs/ folder then push them to the subtree.

The reason this is setup this way, is to allow a single source of documentation with
multiple access methods for all range of skill levels with the Sarracenia product.

Style Guide
~~~~~~~~~~~

Command line execution shall be written in the style of::
  
  An initial comment describing the following steps or processes::

    $ command 1
      relevant output
    $command 2
      .
      .
      relevant output
      newline relevant output

Important notes:

- Initial comment ends with `::` followed by an empty newline
- Thereafter lies the (two space) indented code block
- Commands syntax: '`$ <cmd>`'

  - Alternatively indicate root level commands with '`# <cmd>`' 
- Command output is (two space) indented from leading command.

  - Irrelevant lines of output may be substituted for dots or outright omitted.

pick and stick to a default header hierarchy (ie : = > ~ > - > ... for title > h1 > h2 > h3... etc)

Why rST?
--------
`reStructuredText`_ was chosen primarily as it supports the auto-creation of a table of contents with the '``.. contents::``' directive.
Like many other markup languages, it also supports inline styling, tables, headings and literal blocks.

Localization
~~~~~~~~~~~~

This project is intended to be translated in French and English at a minimum as it's
used across the Government of Canada which has these two official languages. 

The French documentation has the same file structure and names as the English, but
is placed under the fr/ sub-directory.  It's easiest if the documentation is produced
in both languages at once. At the very least use an auto translation tool (such as 
`deepl <https://deepl.com>`_) to provide a starting point. Same procedure in
reverse for Francophones.


