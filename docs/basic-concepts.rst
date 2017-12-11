
==============
Basic Concepts
==============

--------
Projects
--------

Scrapy Do handles zipped scrapy projects. The only expectation it has about the
structure of the archive is that it contains a directory whose name is the same
as the name of the project. This directory, in turn, includes the Scrapy project
itself. Doing things this way ends up being quite convenient if you use version
control like git to manage the code of your spiders (which you probably should).
Let's consider the `quotesbot <https://github.com/scrapy/quotesbot>`_:

  .. code-block:: console

       $ git clone https://github.com/scrapy/quotesbot.git
       $ cd quotesbot

You can create a valid archive like this:

  .. code-block:: console

       $ git archive master -o quotesbot.zip --prefix=quotesbot/

You can, of course, create the zip file any way you wish as long as it meets
the criteria described above.

.. _jobs:

----
Jobs
----

When you submit a job, it will end up being classified as either ``SCHEDULED`` or
``PENDING`` depending on the `scheduling spec <#scheduling-specs>`__ you provide.
Any ``PENDING`` job will be picked up for execution as soon as there is a free job
slot and its status will be changed to ``RUNNING``. ``SCHEDULED`` jobs spawn
new ``PENDING`` jobs at the intervals specified in the scheduling spec. A
``RUNNING`` job may end up being ``SUCCESSFUL``, ``FAILED``, or ``CANCELED``
depending on the return code of the spider process or your actions.

.. _scheduling-spec:

----------------
Scheduling Specs
----------------

Scrapy Do uses the excellent `Schedule <https://github.com/dbader/schedule>`_
library to handle scheduled jobs. The user-supplied scheduling specs get
translated to a series of calls to the ``schedule`` library. Therefore, whatever
is valid for this library should be a valid scheduling spec. For example:

 * 'every monday at 12:30'
 * 'every 2 to 3 hours'
 * 'every 6 minutes'
 * 'every hour at 00:15'

are all valid. A scheduling spec must start with either: 'every' or 'now'. The
former will result in creating a ``SCHEDULED`` job while the latter will produce
a ``PENDING`` job for immediate execution. Other valid keywords are:

 * ``second``
 * ``seconds``
 * ``minute``
 * ``minutes``
 * ``hour``
 * ``hours``
 * ``day``
 * ``days``
 * ``week``
 * ``weeks``
 * ``monday``
 * ``tuesday``
 * ``wednesday``
 * ``thursday``
 * ``friday``
 * ``saturday``
 * ``sunday``
 * ``at`` - expects an hour-like parameter immediately afterwards (ie. 12:12)
 * ``to`` - expects an integer immediately afterwards
