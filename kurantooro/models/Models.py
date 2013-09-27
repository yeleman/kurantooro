#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.db import models
from django.contrib.auth.models import AbstractUser

from py3compat import implements_to_string


@implements_to_string
class Report(models.Model):

    class Meta:
        app_label = 'kurantooro'
        get_latest_by = "created_on"
        ordering = ('-created_on', '-id')

    created_on = models.DateTimeField(auto_now_add=True)
    problems = models.ManyToManyField('Problem', null=True, blank=True,
                                      verbose_name="Problemes",
                                      related_name='problemes')
    kuran_user = models.ForeignKey('KuranUser', null=True, blank=True)
    period = models.ForeignKey('Period', verbose_name="Period")

    objects = models.Manager()

    def __str__(self):
        return "{kuran_user}/{created_on}".format(kuran_user=self.kuran_user,
                                             created_on=self.created_on)


@implements_to_string
class Category(models.Model):

    class Meta:
        app_label = 'kurantooro'
        ordering = ('name', )

    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=70, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.name


@implements_to_string
class Problem(models.Model):

    class Meta:
        app_label = 'kurantooro'
        ordering = ('name', )

    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=70, verbose_name="Intitulé", unique=True)
    category = models.ForeignKey(Category, related_name='categories')

    def __str__(self):
        return self.name


@implements_to_string
class KuranUser(AbstractUser):

    class Meta:
        app_label = 'kurantooro'

    def full_name(self):
        if self.get_full_name():
            return self.get_full_name()
        return self.username

    def __str__(self):
        return self.full_name()
