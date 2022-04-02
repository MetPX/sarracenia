
Announcing Sr3
--------------

After two years of development, on 2022/04/11, we are pleased to announce the availability
of the first beta version of Sarracenia version 3: Sr3. To celebrate the release,
there is a new web-site with in depth information:

  https://metpx.github.io/sarracenia

Compared to v2, Sr3 brings:

* Native support for `mqtt <https://www.mqtt.org>`_ and `amqp <https://www.amqp.org>`_ (`rabbitmq <https://www.rabbitmq.com>`_ and MQTT brokers.) with a modular implementation that allows straightforward additional `message queueing protocols <https://metpx.github.io/sarracenia/Reference/code.html#module-sarracenia.moth>`_ to be supported.

* The `Flow Algorithm <https://metpx.github.io/sarracenia/Explanation/Concepts.html#the-flow-algorithm>`_ unifies
  all components into slight variations of this `single common code. <https://metpx.github.io/sarracenia/Reference/code.html#module-sarracenia.flow>`_ This re-factor has enabled the elimination of code duplication and allowed reduction of total lines of code by approximately 30% while adding features.

* A new command-line interface centred on a single entry-point: `sr3 <https://metpx.github.io/sarracenia/Reference/sr3.1.html#sr3-sarracenia-cli>`_

* Improved, jupyter Notebook-driven `Tutorials <https://metpx.github.io/sarracenia/Tutorials/index.html>`_

* A new `plugin API <https://metpx.github.io/sarracenia/Reference/flowcb.html>`_, which allows pythonic customization of default application processing.

* A new `python API <https://metpx.github.io/sarracenia/Reference/code.html>`_, which gives complete access to the implementation, allowing elegant extension through sub-classing.

* Applications can call Sarracenia Python API from their mainline.
  (In v2, one had to write callbacks to call application code, the application mainline could not be used.)

* Newly added GitHub Discussion module, for questions, and community-driven
  clarification: https://github.com/MetPX/sarracenia/discussions

* Native support for the emerging World Meteorological Organization (WMO) standards from the task team on message queueing protocols standards for international meteorological data exchange: https://github.com/wmo-im/GTStoWIS2

* A core component of: `wis2box WMO demonstration project <https://wis2box.readthedocs.io/en/latest>`_

