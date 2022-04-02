
Changes Made to create v03
==========================

Actual format is defined `here <../../Reference/sr_post.7.html>`_
An explanation of motivation of the changes is below:

Changes from v02
----------------

Version 03 is a change in encoding, but the semantics of the fields
are unchanged from version 02. Changes are limited to how the fields
are placed in the messages. In v02, AMQP headers were used to store name-value
pairs.

   * v03 headers have practically unlimited length. In v02, individual
     name-value pairs are limited to 255 characters. This has proven
     limiting in practice. In v03, the limit is not defined by the JSON
     standard, but by specific parser implementations. The limits in common
     parsers are high enough not to cause practical concerns.

   * use of message payload to store headers makes it possible to consider
     other messaging protocols, such as MQTT 3.1.1, in future.

   * In v03, pure JSON payload simplifies implementations, reduces documentation
     required, and amount of parsing to implement. Using a commonly implemented
     format permits use of existing optimized parsers.

   * In v03, JSON encoding of the entire payload reduces the features required for
     a protocol to forward Sarracenia posts. For example, one might
     consider using Sarracenia with MQTT v3.11 brokers which are more
     standardized and therefore more easily interoperable than AMQP.

   * v02 fixed fields are now  "pubTime", "baseURL", and "relPath" keys
     in the JSON object that is the messge body.

   * v02 *sum* header with hex encoded value, is replaced by v03 *integrity* header with base64 encoding.

   * v03 *content* header allows file content embedding.

   * Change in overhead... approximately +75 bytes per message (varies.)

     * JSON object marking curly braces '{' '}', commas and quotes for
       three fixed fields. net: +10

     * AMQP section *Application Properties* no longer included in payload, saving
       a 3 byte header (replaced by 2 bytes of open and close braces payload.)
       net: -1 byte

     * each field has a one byte header to indicate the table entry in an AMQP
       packet, versus 4 quote characters, a colon, a space, and likely a comma: 7 total.
       so net change is +6 characters. per header. Most v02 messages have 6 headers,
       net: +36 bytes

     * the fixed fields are now named: pubTime, baseUrl, relPath, adding 10 characters
       each. +30 bytes.

   * In v03, the format of save files is the same as message payload.
     In v02 it was a json tuple that included a topic field, the body, and the headers.

   * In v03, the report format is a post message with a header, rather than
     being parsed differently. So this single spec applies to both.

