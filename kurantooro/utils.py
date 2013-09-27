#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.utils import timezone


def normalize_date(target, as_aware=True):
    target_is_aware = timezone.is_aware(target)
    if as_aware and target_is_aware:
        return target
    elif as_aware and not target_is_aware:
        # make foreign object aware (assume UTC)
        return timezone.make_aware(target, timezone.utc)
    else:
        # make forign object naive
        return timezone.make_naive(target, timezone.utc)


def next_month(year, month):
    """ next year and month as int from year and month """
    if month < 12:
        return (year, month + 1)
    else:
        return (year + 1, 1)
