#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:samp:`Logical functions, gate and gate builders`


Logical functions
-----------------

Each logical function takes a one-argument predicate or a list of one-argument predicates. In turn
each logical function returns a one-argument predicate that is the chain of, or the negation of its arguments.
There are functions to chain predicates along
:func:`not_`, :func:`and_`, :func:`or_`, :func:`nand_`, :func:`nor_`, :func:`xor_` and :func:`xnor_`.

Each logical function, before returning the chained predicate, will check if the predicates in the argument list
are truly one-argument predicates. The behavior after detection of a wrong argument can be set
by the module-method :func:`set_stop_on_creation_error`.
The default behavior after detection of a wrong argument is to throw a :exc:`GateCreationException`.

**Example usage**

Given closures or lambda's::

    >>> spam = lambda word : word.startswith("spam")
    >>> eggs = lambda word: word.endswith("eggs")
    >>> ampersand = lambda word: len(word.split("&")) > 1

Now you can create a test for spam & eggs::

    >>> from rspub.util.gates import and_
    >>> spam_and_eggs = and_(spam, eggs, ampersand)

and reuse `spam` and `eggs` to create spam nor eggs::

    >>> from rspub.util.gates import nor_
    >>> spam_nor_eggs = nor_(spam, eggs)

and use the assembled predicates::

    >>> spam_and_eggs("spam & eggs")
    True
    >>> spam_and_eggs("spamming leggs")
    False
    >>> spam_nor_eggs("bacon")
    True

Of course your closures and lambda's all need to be able to handle the type of argument given.

Gate
----

The function :func:`gate` takes two lists of predicates, *includes* and *excludes*.
Includes is the list of predicates that can
permit `x` through the gate; excludes is the list of predicates that can prevent `x` from passing the gate.

Building gates
--------------

The abstract class :class:`GateBuilder` defines the methods to construct a GateBuilder. The concrete class
:class:`PluggedInGateBuilder` walks zero or more plugin directories looking for specifically named builders
in order to build a customized :func:`gate`.

If :class:`GateBuilder` s are chained, a builder can overrule `includes` and `excludes` from previous builders.

-------

Classes and functions
---------------------

"""
import inspect
import logging
from abc import ABCMeta, abstractmethod
from itertools import takewhile
import rspub.util.plugg as plugg

__all__ = ['not_', 'and_', 'or_', 'nand_', 'nor_', 'xor_', 'xnor_', 'gate',
           'GateBuilder', 'PluggedInGateBuilder', 'GateCreationException', 'GateBuilderException',
           'is_one_arg_predicate', 'set_stop_on_creation_error', 'stop_on_creation_error']

LOG = logging.getLogger(__name__)


def not_(predicate):
    """
    :samp:`Creates the negation of the given {predicate}`

    The outcome of a `not_   f` for any `x` is::

        f(x) = not p(x)

    where `p` is the given predicate.

    :param predicate: the predicate to negate
    :return: a new predicate implementing the negation of the given predicate
    """
    is_one_arg_predicate(predicate)
    return lambda x: not predicate(x)


def and_(*predicates):
    """
    :samp:`Creates the logical conjunction of the given {predicates}`

    Chains `predicates` in `and`. The outcome of an `and_  f` for any `x` is::

        f(x) = p_1(x) and p_2(x) and ... and p_n(x)

    where `p_1 ... p_n` are the given predicates.

    The chain of predicates is **True** if all predicates are **True**, otherwise **False**.
    Outcome **True** in effect says that all of the predicates evaluated as **True**.

    Logical performance has been optimized. i.e. `A and B and C` is **False** if `A` evaluates as **False**;
    do not test `B` and `C` in this case.

    :param predicates: predicates to chain in and.
    :return: a new predicate implementing the combined `and` of the given predicates
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x: len(list(takewhile(lambda predicate: predicate(x), ps))) == len(ps)


def nor_(*predicates):
    """
    :samp:`Creates the joint denial of the given {predicates}`

    Chains `predicates` in `nor`. The outcome of a `nor_  f` for any `x` is::

        f(x) = not(p_1(x) or p_2(x) or ... or p_n(x))

    where `p_1 ... p_n` are the given predicates.

    The chain of predicates is **False** if at least one predicate is **True**, otherwise **True**.
    Outcome **True** in effect says that neither one of the predicates evaluated as **True**.

    Logical performance has been optimized. i.e. `A nor B nor C` is **False** if `A` evaluates as **True**;
    do not test `B` and `C` in this case.

    :param predicates: predicates to chain in nor.
    :return: a new predicate implementing the combined `nor` of the given predicates
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x: len(list(takewhile(lambda predicate: not predicate(x), ps))) == len(ps)


def or_(*predicates):
    """
    :samp:`Creates the logical inclusive disjunction of the given {predicates}`

    Chains `predicates` in `or`. The outcome of an `or_  f` for any `x` is::

        f(x) = p_1(x) or p_2(x) or ... or p_n(x)

    where `p_1 ... p_n` are the given predicates.

    The chain of predicates is **True** if at least one predicate is **True**, otherwise **False**.
    Outcome **True** in effect says that at least one of the predicates evaluated as **True**.

    Logical performance has been optimized. i.e. `A or B or C` is **True** if `A` evaluates as **True**;
    do not test `B` and `C` in this case.

    :param predicates: predicates to chain in or.
    :return: a new predicate implementing the combined `or` of the given predicates
    """
    return not_(nor_(*predicates))


def nand_(*predicates):
    """
    :samp:`Creates the alternative denial of the given {predicates}`

    Chains `predicates` in `nand`. The outcome of a `nand_  f` for any `x` is::

        f(x) = not(p_1(x) and p_2(x) and ... and p_n(x))

    where `p_1 ... p_n` are the given predicates.

    The chain of predicates is **False** if all predicates are **True**, otherwise **True**.
    Outcome **True** in effect says that at least one of the predicates evaluated as **False**.

    Logical performance has been optimized. i.e. `A nand B nand C` is **True** if `A` evaluates as **False**;
    do not test `B` and `C` in this case.

    :param predicates: predicates to chain in nand.
    :return: a new predicate implementing the combined `nand` of the given predicates
    """
    return not_(and_(*predicates))


def xor_(*predicates):
    """
    :samp:`Creates the exclusive disjunction of the given {predicates}`

    Chains `predicates` in `xor`. The outcome of an `xor_  f` for any `x` is::

            f(x) = p_1(x) xor p_2(x) xor ... xor p_n(x)

    where `p_1 ... p_n` are the given predicates.

    One definition of xor says:
    "A chain of XORs—a XOR b XOR c XOR d (and so on)—is true whenever an odd number
    of the inputs are true and is false whenever an even number of inputs are true.
    https://en.wikipedia.org/wiki/Exclusive_or

    Some definitions even deny that there can be more than two inputs:
    "a Boolean operator working on two variables that has the value one if one
    but not both of the variables is one".
    https://www.google.nl/search?q=define+exclusive+OR

    However, this implementation adheres to:

    The chain of predicates is **True** if one and only one predicate is **True**, otherwise **False**.

    :param predicates: predicates to chain with xor.
    :return: a new predicate implementing the combined `xor` of the given predicates
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x: len([x for predicate in ps if predicate(x)]) == 1


def xnor_(*predicates):
    """
    :samp:`Creates the logical equality of the given {predicates}`

    Chains `predicates` in `xnor`. The outcome of an `xnor_  f` for any `x` is::

        f(x) = (p_1(x) and p_2(x) and ... and p_n(x)) or not(p_1(x) or p_2(x) or ... or p_n(x))

    where `p_1 ... p_n` are the given predicates.

    The chain of predicates is **True** if *all* predicates evaluate as **True** or *all* predicates
    evaluate as **False**.
    (So this is *not* the negation of xor as implemented above.)

    :param predicates: predicates to chain with xnor.
    :return: a new predicate implementing the combined `xnor` of the given predicates
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]

    def _xnor(x):
        count = len([x for predicate in ps if predicate(x)])
        return count == 0 or count == len(ps)
    return _xnor


def gate(includes=list(), excludes=list()):
    """
    :samp:`Creates the logical conjunction of or_({includes}), nor_({excludes})`

    Chains `including` predicates and `excluding` predicates. The outcome of a gate `g` for any `x` is::

        g(x) = (i_1(x) or i_2(x) or ... or i_n(x)) and not(e_1(x) or e_2(x) or ... or e_n(x))

    where `i_1 ... i_n` are given including predicates and `e_1 ... e_n` are given excluding predicates.

    The gate evaluates as **True** if at least one of `includes` is **True** and none of `excludes` are **True**.

    :param list includes: predicates that permit `x` through gate
    :param list excludes: predicates that restrict `x` from gate
    :return: a new predicate implementing the combined functions given in `includes` and `excludes`
    """
    return and_(or_(*includes), nor_(*excludes))


class GateBuilder(metaclass=ABCMeta):
    """
    :samp:`Abstract builder class for gates`

    GateBuilders should extend this abstract class or
    implement the next two methods. In these methods GateBuilders are free to extend on previously defined
    lists of permitting and restricting predicates, remove elements from them or overrule previous steps
    and return complete new lists.

    .. seealso:: :func:`gate`
    """
    @abstractmethod
    def build_includes(self, includes: list) -> list:
        """
        :samp:`Define the list of permitting predicates`

        Either rework the given list (append, extend, remove, replace),
        return the given list or return a complete new list.
        The returned list should consist of one-argument predicates.

        :param list includes: the list of permitting predicates (from previous builders)
        :return: the list of permitting predicates as defined by this GateBuilder
        """
        return includes

    @abstractmethod
    def build_excludes(self, excludes: list) -> list:
        """
        :samp:`Define the list of restricting predicates`

        Either rework the given list (append, extend, remove, replace),
        return the given list or return a complete new list.
        The returned list should consist of one-argument predicates.

        :param list excludes: the list of restricting predicates (from previous builders)
        :return: the list of restricting predicates as defined by this GateBuilder
        """
        return excludes


class PluggedInGateBuilder(GateBuilder):
    """
    :samp:`Builds pluggable {gates}`

    The PluggedInGateBuilder can be given zero or more directories where it will recursively look for
    GateBuilders of the given `builder_name`. It will then instantiate the builder and give it the opportunity to
    determine the list of including predicates and the list of excluding predicates as ``this`` builder calls
    :func:`~GateBuilder.build_includes` and :func:`~GateBuilder.build_excludes` on the plugged-in builder.

    A class in the given `plugin_directories` will qualify as builder if at least

    - it has a name equal to the given `builder_name` and
    - it is a subclass of :class:`GateBuilder` or it implements both methods of this class.

    The final :func:`gate` can be obtained by calling :func:`build_gate`.
    """
    def __init__(self, builder_name: str, first_builder: GateBuilder = None, *plugin_directories: str):
        """
        :samp:`Initialize a {PluggedInGateBuilder}`

        :param str builder_name: the class name (either simple or qualified) of the class implementing the GateBuilder methods.
        :param GateBuilder first_builder: builder of default or initial predicates, may be **None**
        :param str plugin_directories: the directories where to search for GateBuilders with the given builder_name
        """
        self.builder_name = builder_name
        self.plugin_directories = plugin_directories

        if first_builder is not None:
            self.includes = first_builder.build_includes(list())
            self.excludes = first_builder.build_excludes(list())
            self._inspect_predicates(self.includes, self.excludes, first_builder.__class__)
        else:
            self.includes = []
            self.excludes = []

    def build_includes(self, includes=list()) -> list:
        """
        :samp:`Set initial permitting predicates`

        :param list includes: the list of initial permitting predicates
        :return: the list of initial permitting predicates
        :raises: :exc:`GateCreationException` if a predicate was not a one-argument predicate
        """
        valid_includes = [p for p in includes if is_one_arg_predicate(p)]
        self.includes.extend(valid_includes)
        return self.includes

    def build_excludes(self, excludes=list()) -> list:
        """
        :samp:`Set initial restricting predicates`

        :param list excludes: the list of initial restricting predicates
        :return: the list of initial restricting predicates
        :raises: :exc:`GateCreationException` if a predicate was not a one-argument predicate
        """
        valid_excludes = [p for p in excludes if is_one_arg_predicate(p)]
        self.excludes.extend(valid_excludes)
        return self.excludes

    def build_gate(self) -> gate:
        """
        :samp:`Build a gate as defined by found GateBuilders in {plugin_directories}`

        Found GateBuilders are given
        the chance to modify the lists `includes` and `excludes`.
        The initial lists `includes` and `excludes` are populated by predicates as defined by `first_builder`.
        If no `first_builder` was given, the initial lists will be empty lists.

        :return: :func:`gate` as defined by found GateBuilders.
        :raises: :exc:`GateCreationException` if a gate could not be created because a given value is not a one-argument predicate.
        :raises: :exc:`GateBuilderException` if a gate could not be built because of inappropriate behavior of a GateBuilder.

        .. seealso:: :func:`gate`, :class:`GateBuilder`, :func:`GateBuilder.build_includes`, :func:`GateBuilder.build_excludes`

        """
        is_subclass = lambda x: issubclass(x, GateBuilder)
        has_both_metods = and_(plugg.has_function(GateBuilder.build_includes.__name__),
                               plugg.has_function(GateBuilder.build_excludes.__name__))
        has_builder_name = plugg.is_named(self.builder_name)
        is_subclass_or_has_methods = or_(is_subclass, has_both_metods)
        builder_predicates = [and_(is_subclass_or_has_methods, has_builder_name)]

        inspector = plugg.Inspector(stop_on_error=True)

        for cls in inspector.list_classes_filtered(builder_predicates, *self.plugin_directories):

            if inspect.isabstract(cls):
                raise GateBuilderException("GateBuilder cannot be instantiated: class is abstract: %s" % cls)
            else:
                try:
                    builder = cls.__new__(cls)
                    builder.__init__()
                except TypeError as exc:
                    raise GateBuilderException("Could not instantiate object (%s in %s)"
                                               % (cls, inspect.getfile(cls))) from exc

                tmp_includes = builder.build_includes(list(self.includes))
                if not isinstance(tmp_includes, list):
                    raise GateBuilderException("Illegal return value for build_includes: "
                                               "%s in stead of list. (%s in %s)" % (
                                                   self.includes, cls, inspect.getfile(cls)))
                tmp_excludes = builder.build_excludes(list(self.excludes))
                if not isinstance(tmp_excludes, list):
                    raise GateBuilderException("Illegal return value for build_excludes: "
                                               "%s in stead of list. (%s in %s)" % (
                                                   self.excludes, cls, inspect.getfile(cls)))

                # multiple inspects of same predicates are taking place during execution of this method,
                # but at least here we can pinpoint the culprit if any invalid.
                valid_includes, valid_excludes = self._inspect_predicates(tmp_includes, tmp_excludes, cls)

                new_in_incl = len([x for x in valid_includes if x not in self.includes])
                out_of_incl = len([x for x in self.includes if x not in valid_includes])
                new_in_excl = len([x for x in valid_excludes if x not in self.excludes])
                out_of_excl = len([x for x in self.excludes if x not in valid_excludes])
                self.includes = valid_includes
                self.excludes = valid_excludes
                LOG.info("Includes build by %s. new: %d, removed: %d" % (cls, new_in_incl, out_of_incl))
                LOG.info("Excludes build by %s. new: %d, removed: %d" % (cls, new_in_excl, out_of_excl))

        LOG.info("Constructed gate with %d including predicates and %d excluding predicates."
                 % (len(self.includes), len(self.excludes)))
        return gate(self.includes, self.excludes)

    @staticmethod
    def _inspect_predicates(includes, excludes, cls):
        try:
            valid_includes = [p for p in includes if is_one_arg_predicate(p)]
        except GateCreationException as exc:
            raise GateBuilderException("Invalid include predicate from %s" % cls) from exc

        try:
            valid_excludes = [p for p in excludes if is_one_arg_predicate(p)]
        except GateCreationException as exc:
            raise GateBuilderException("Invalid exclude predicate from %s" % cls) from exc

        return valid_includes, valid_excludes


class GateCreationException(ValueError):
    """
    :samp:`Indicates a gate could not be created because a given value is not a one-argument predicate`
    """
    pass


class GateBuilderException(GateCreationException):
    """
    :samp:`Indicates a gate could not be built because of inappropriate behavior of a GateBuilder`
    """
    pass


STOP_ON_CREATION_ERROR = True


def set_stop_on_creation_error(stop):
    """
    :samp:`Determine module-wide behavior on gate creation errors`

    The function :func:`is_one_arg_predicate` will be called throughout this module by logical functions and
    gate builder classes in order to detect if a given value is a one-argument predicate.
    What the behavior of the detecting function will be after detecting a wrong input value can
    be determined by this method. Either an error message will be logged (stop = **False**) or a
    :exc:`GateCreationException` will be raised (stop = **True**).

    :param boolean stop: **True** for stop on creation error, **False** otherwise
    :return: the previous state
    """
    global STOP_ON_CREATION_ERROR
    previous_value = STOP_ON_CREATION_ERROR
    STOP_ON_CREATION_ERROR = stop
    return previous_value


def stop_on_creation_error():
    """
    :samp:`Module-wide behavior on gate creation errors`

    :return: **True** if stops on creation error, **False** otherwise
    """
    return STOP_ON_CREATION_ERROR


def is_one_arg_predicate(p):
    """
    :samp:`Determines if the given {p} is a one-argument predicate`

    :param p: value to be inspected
    :return: **True** if `p` is a one-argument predicate, **False** otherwise
    :raises: :exc:`GateCreationException` if `p` is not a one-argument predicate and :func:`stop_on_creation_error` is **True**

    .. seealso:: :func:`set_stop_on_creation_error`

    """
    is_p = True
    msg = None
    if not inspect.isfunction(p):
        is_p = False
        msg = "not a function: %s" % p
    else:
        argspec = inspect.getargspec(p)
        if len(argspec.args) != 1:
            is_p = False
            msg = "more than one argument in %s: %s" % (p, argspec.args)
        elif argspec.varargs:
            is_p = False
            msg = "varargs in %s: %s" % (p, argspec.varargs)
        elif argspec.keywords:
            is_p = False
            msg = "keyword arguments in %s: %s" % (p, argspec.keywords)
    if not is_p:
        if STOP_ON_CREATION_ERROR:
            raise GateCreationException("Not a one-argument predicate: %s" % msg)
        else:
            LOG.error("Not a one-argument predicate: %s" % msg)
    return is_p
