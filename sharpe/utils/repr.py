#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import abc


def _repr(cls_name, properties):
    fmt_str = "{}({})".format(cls_name, ", ".join((str(p) + "={}") for p in properties))

    def __repr(inst):
        return fmt_str.format(*(getattr(inst, p, None) for p in properties))
    return __repr


class PropertyReprMeta(abc.ABCMeta):
    # has better performance than property_repr
    def __new__(mcs, *args, **kwargs):
        cls = super(PropertyReprMeta, mcs).__new__(mcs, *args, **kwargs)

        if hasattr(cls, "__repr_properties__"):
            repr_properties = getattr(cls, "__repr_properties__")
        else:
            repr_properties = []
            for c in cls.mro():
                repr_properties.extend(v for v in vars(c) if isinstance(getattr(c, v), property))
        cls.__repr__ = _repr(cls.__name__, repr_properties)
        return cls


def property_repr(inst):
    # return pformat(properties(inst))
    return "%s(%s)" % (inst.__class__.__name__, properties(inst))


def slots_repr(inst):
    # return pformat(slots(inst))
    return "%s(%s)" % (inst.__class__.__name__, slots(inst))


def dict_repr(inst):
    # return pformat(inst.__dict__)
    return "%s(%s)" % (
        inst.__class__.__name__, {k: v for k, v in inst.__dict__.items() if k[0] != "_"})


def properties(inst):
    result = {}
    for cls in inst.__class__.mro():
        abandon_properties = getattr(cls, '__abandon_properties__', [])
        for varname in iter_properties_of_class(cls):
            if varname[0] == "_":
                continue
            if varname in abandon_properties:
                # filter the properties which be set to __abandon_properties__
                continue
            # FIXME:
            try:
                tmp = getattr(inst, varname)
            except (AttributeError, RuntimeError, KeyError):
                continue
            if varname == "positions":
                tmp = list(tmp.keys())
            if hasattr(tmp, '__simple_object__'):
                result[varname] = tmp.__simple_object__()
            else:
                result[varname] = tmp
    return result


def slots(inst):
    result = {}
    for slot in inst.__slots__:
        result[slot] = getattr(inst, slot)
    return result


def iter_properties_of_class(cls):
    for varname in vars(cls):
        value = getattr(cls, varname)
        if isinstance(value, property):
            yield varname
