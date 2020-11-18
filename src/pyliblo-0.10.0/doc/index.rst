.. module:: liblo

##############################
pyliblo 0.10 API Documentation
##############################

Homepage: http://das.nasophon.de/pyliblo/

The latest version of this manual can be found at
http://dsacre.github.io/pyliblo/doc/.

For the most part, pyliblo is just a thin wrapper around
`liblo <http://liblo.sourceforge.net/>`_, which does
all the real work.
For questions not answered here, also see the
`liblo documentation <http://liblo.sourceforge.net/docs/modules.html>`_
and the `OSC spec <http://opensoundcontrol.org/spec-1_0>`_.


Module-level Functions
======================

.. autofunction:: send

.. autofunction:: time


OSC Server Classes
==================

.. autoclass:: Server
    :no-members:

    .. automethod:: __init__
    .. automethod:: recv
    .. automethod:: send
    .. automethod:: add_method
    .. automethod:: del_method
    .. automethod:: register_methods
    .. automethod:: add_bundle_handlers
    .. autoattribute:: url
    .. autoattribute:: port
    .. autoattribute:: protocol
    .. automethod:: fileno
    .. automethod:: free

-------

.. autoclass:: ServerThread
    :no-members:

    .. automethod:: __init__
    .. automethod:: start
    .. automethod:: stop

.. autoclass:: make_method

    .. automethod:: __init__


Utility Classes
===============

.. autoclass:: Address
    :no-members:

    .. automethod:: __init__
    .. autoattribute:: url
    .. autoattribute:: hostname
    .. autoattribute:: port
    .. autoattribute:: protocol

-------

.. autoclass:: Message

    .. automethod:: __init__

.. autoclass:: Bundle

    .. automethod:: __init__

-------

.. autoexception:: ServerError

.. autoexception:: AddressError


Mapping between OSC and Python data types
=========================================

When constructing a message, pyliblo automatically converts
arguments to an appropriate OSC data type.
To explicitly specify the OSC data type to be transmitted, pass a
``(typetag, data)`` tuple instead. Some types can't be unambiguously
recognized, so they can only be sent that way.

The mapping between OSC and Python data types is shown in the following table:

========= =============== ====================================================
typetag   OSC data type   Python data type
========= =============== ====================================================
``'i'``   int32           :class:`int`
``'h'``   int64           :class:`long` (Python 2.x), :class:`int` (Python 3.x)
``'f'``   float           :class:`float`
``'d'``   double          :class:`float`
``'c'``   char            :class:`str` (single character)
``'s'``   string          :class:`str`
``'S'``   symbol          :class:`str`
``'m'``   midi            :class:`tuple` of four :class:`int`\ s
``'t'``   timetag         :class:`float`
``'T'``   true
``'F'``   false
``'N'``   nil
``'I'``   infinitum
``'b'``   blob            :class:`list` of :class:`int`\ s (Python 2.x), :class:`bytes` (Python 3.x)
========= =============== ====================================================
