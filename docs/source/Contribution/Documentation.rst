=======================
Documentation Standards
=======================


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

Processing
----------

The entire documentation is under the docs/source tree. It is processed using sphinx, invoked
using the Makefile in docs/.  One can install sphinx locally, and run make to build locally 
and debug. The result is produced in docs/build/html::

    pip install -f requirements-dev.txt
    cd docs
    make html
 
then point a browser to docs/build/html.

There is a github Actions jobs that does this on each push to appropriate branchs to update
the main documentation. the main url for the resulting web-site is:

  https://metpx.github.io/sarracenia/


Tutorials
---------

- Learning-oriented, specifically learning how rather than learning *that*.
- Allow the user to learn by doing to get them started, be sure your tutorial works and users can see results immediately. 
- Tutorials must be reliably repeatable focused on concrete steps (not abstract concepts) with the minimum necessary explanation.

Many of the Tutorials are built using jupyter notebooks. See docs/source/Tutorials/README.md for
how to work with them.


How2Guides
----------

- Problem and goal oriented: "**I want to... How do I...**" Differing from tutorials in that tutorials are for complete beginners, how to guides assume some knowledge and understanding with a basic setup and tools.
- Provide a series of steps focused on the results of some particular problem. 
- Don't explain concepts, if they are important, they can be linked to in `../Explanation/`
- There are multiple ways to skin a cat, remain flexible in your guide so users can see *how* things are done.
- **NAME GUIDES WELL** enough to tell the user *exactly* what they do at a glance.

Explanation
-----------

- Understanding-oriented: can be equally considered discussions. Much more relaxed version of documentation where concepts are explored from a higher level or different perspectives.
- Provide context, discuss alternatives and opinions while providing technical reference (for other sections).

Reference
---------

- Dictionary style.
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

Code Style
----------

We generally follow `PEP 8 <https://peps.python.org/pep-0008/>`_ standards for code formatting, and use `YAPF <https://github.com/google/yapf>`_ to automatically re-format code. One exception to PEP 8 is that we use a 119 character line length.

For docstrings in code, we are following the Google Style Guide. These docstrings will be parsed into formatted documentation by Sphinx. 

Detailed examples can be found in the `Napoleon Sphinx plugin's docs <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_ and the `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_.

Selected examples from ``credentials.py``:

.. code-block:: python

    class Credential:
        """An object that holds information about a credential, read from a 
        credential file, which has one credential per line, format::
            url option1=value1, option2=value2
            
        Examples::
            sftp://alice@herhost/ ssh_keyfile=/home/myself/mykeys/.ssh.id_dsa
            ftp://georges:Gpass@hishost/  passive = True, binary = True
            
        `Format Documentation. <https://metpx.github.io/sarracenia/Reference/sr3_credentials.7.html>`_

        Attributes:
            url (urllib.parse.ParseResult): object with URL, password, etc.
            ssh_keyfile (str): path to SSH key file for SFTP
            passive (bool): use passive FTP mode, defaults to ``True``
            binary (bool): use binary FTP mode, defaults to ``True``
            tls (bool): use FTPS with TLS, defaults to ``False``
            prot_p (bool): use a secure data connection for TLS
            bearer_token (str): bearer token for HTTP authentication
            login_method (str): force a specific login method for AMQP (PLAIN,
                AMQPLAIN, EXTERNAL or GSSAPI)
        """

        def __init__(self, urlstr=None):
            """Create a Credential object.

                Args:
                    urlstr (str): a URL in string form to be parsed.
            """


.. code-block:: python
    
    def isValid(self, url, details=None):
        """Validates a URL and Credential object. Checks for empty passwords, schemes, etc.
            
        Args:
            url (urllib.parse.ParseResult): ParseResult object for a URL.
            details (sarracenia.credentials.Credential): sarra Credential object containing additional details about
                the URL.

        Returns:
            bool: ``True`` if a URL is valid, ``False`` if not.
        """

Why rST?
--------

`reStructuredText`_ was chosen primarily as it supports the auto-creation of a table of contents with the '``.. contents::``' directive.
Like many other markup languages, it also supports inline styling, tables, headings and literal blocks.

In Jupyter Notebooks, unfortunately, only Markdown is supported, elsewhere RST is great.


Localization
~~~~~~~~~~~~

This project is intended to be translated in French and English at a minimum as it's
used across the Government of Canada which has these two official languages. 

The French documentation has the same file structure and names as the English, but
is placed under the fr/ sub-directory.  It's easiest if the documentation is produced
in both languages at once. At the very least use an auto translation tool (such as 
`deepl <https://deepl.com>`_) to provide a starting point. Same procedure in
reverse for Francophones.


