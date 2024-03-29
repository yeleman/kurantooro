#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
from datetime import datetime, date, timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.dateformat import format as date_format
from django.utils.encoding import python_2_unicode_compatible

from kurantooro.utils import normalize_date, next_month

ONE_SECOND = 0.0001
ONE_MICROSECOND = 0.00000000001


class DayManager(models.Manager):
    def get_query_set(self):
        return super(DayManager, self).get_query_set() \
                                      .filter(period_type=Period.DAY)


class WeekManager(models.Manager):
    def get_query_set(self):
        return super(WeekManager, self).get_query_set() \
                                       .filter(period_type=Period.WEEK)


class MonthManager(models.Manager):
    def get_query_set(self):
        return super(MonthManager, self).get_query_set() \
                                        .filter(period_type=Period.MONTH)


class QuarterManager(models.Manager):
    def get_query_set(self):
        return super(QuarterManager, self).get_query_set() \
                                          .filter(period_type=Period.QUARTER)


class SemesterManager(models.Manager):
    def get_query_set(self):
        return super(SemesterManager, self).get_query_set() \
                                           .filter(period_type=Period.SEMESTER)


class YearManager(models.Manager):
    def get_query_set(self):
        return super(YearManager, self).get_query_set() \
                                       .filter(period_type=Period.YEAR)


class CustomManager(models.Manager):
    def get_query_set(self):
        return super(CustomManager, self).get_query_set() \
                                         .filter(period_type=Period.CUSTOM)


@python_2_unicode_compatible
class Period(models.Model):
    ''' Represents a Period of time. Base class ; should not be used directly.

    Use DayPeriod, MonthPeriod, etc instead.
    Provides easy way to find/create period for reporting.

    p = MonthPeriod.find_create_from(2011, 3)
    p.following() '''

    class Meta:
        app_label = 'kurantooro'
        unique_together = ('start_on', 'end_on', 'period_type')
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    QUARTER = 'quarter'
    SEMESTER = 'semester'
    YEAR = 'year'
    CUSTOM = 'custom'

    PERIOD_TYPES = (
        (DAY, _("Day")),
        (WEEK, _("Week")),
        (MONTH, _("Month")),
        (QUARTER, _("Quarter")),
        (SEMESTER, _("Semester")),
        (YEAR, _("Year")),
        (CUSTOM, _("Custom")),
    )

    start_on = models.DateTimeField(_("Start On"))
    end_on = models.DateTimeField(_("End On"))
    period_type = models.CharField(max_length=15,
                                   choices=PERIOD_TYPES, default=CUSTOM,
                                   verbose_name=_("Type"))

    objects = models.Manager()
    days = DayManager()
    weeks = WeekManager()
    months = MonthManager()
    quarters = QuarterManager()
    semesters = SemesterManager()
    years = YearManager()
    customs = CustomManager()
    django = models.Manager()

    def __lt__(self, other):
        try:
            return self.end_on < self.normalize_date(other.start_on)
        except:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.end_on <= self.normalize_date(other.end_on)
        except:
            return NotImplemented

    def __eq__(self, other):
        try:
            return self.pid == other.pid
        except:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.start_on != self.normalize_date(other.start_on) \
                or self.end_on != self.normalize_date(other.end_on)
        except:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.start_on > self.normalize_date(other.end_on)
        except:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.start_on >= self.normalize_date(other.start_on)
        except:
            return NotImplemented

    def normalize_date(self, obj):
        return normalize_date(obj, as_aware=self.is_aware())

    def is_aware(self):
        s = timezone.is_aware(self.start_on)
        e = timezone.is_aware(self.end_on)
        if not s == e:
            raise TypeError("Period boundaries can't mix naive and TZ aware")
        return s and e

    def is_naive(self):
        return not self.is_aware()

    def list_of_subs(self, cls):
        if cls == self.__class__:
            return [self]
        d = []
        n = cls.find_create_by_date(self.start_on, dont_create=True)
        while n.start_on <= self.end_on:
            d.append(n)
            n = cls.find_create_by_date(n.start_on + timedelta(cls.delta()),
                                        dont_create=True)
        return d

    def cast(self, cls):
        self.__class__ = cls

    @property
    def days(self):
        return self.list_of_subs(DayPeriod)

    @property
    def weeks(self):
        return self.list_of_subs(WeekPeriod)

    @property
    def months(self):
        return self.list_of_subs(MonthPeriod)

    @property
    def quarters_(self):
        return self.list_of_subs(QuarterPeriod)

    # @property
    # def semesters(self):
    #     return self.list_of_subs(SemesterPeriod)a

    @property
    def years(self):
        return self.list_of_subs(YearPeriod)

    @classmethod
    def type(cls):
        ''' default type for period creation '''
        return cls.CUSTOM

    @classmethod
    def delta(self):
        ''' timedelta() length of a period. 1 = one day. '''
        return 1.0 // 24

    @property
    def pid(self):
        ''' A locale safe identifier of the period '''
        return self.middle().strftime('%s')

    def middle(self):
        ''' datetime at half of the period duration '''
        return self.start_on + ((self.end_on - self.start_on) // 2)

    def __str__(self):
        return self.name()

    def name(self):
        try:
            cls = eval("{}Period".format(self.period_type.title()))
            return cls.objects.get(id=self.id).name()
        except:
            # TRANSLATORS: Django date format for Generic .name()
            return date_format(self.middle(), ugettext("c"))

    def strid(self):
        return self.middle().strftime('%s')

    def full_name(self):
        return self.name()

    def following(self):
        ''' returns next period in time '''
        return self.find_create_by_date(self.middle()
                                        + timedelta(self.delta()))

    def previous(self):
        ''' returns next period in time '''
        return self.find_create_by_date(self.middle()
                                        - timedelta(self.delta()))

    @classmethod
    def boundaries(cls, date_obj):
        ''' start and end dates of a period from a date. '''
        start = date_obj - timedelta(cls.delta() // 2)
        end = start + cls.delta()
        return (start, end)

    def includes(self, date_obj):
        ''' check if provided value is within this Period's scope

        date_obj can be:
         * datetime instance
         * date instance
         * integer (year) '''

        date_obj = self.normalize_date(date_obj)
        if isinstance(date, date_obj):
            date_obj = datetime(date.year, date.month, date.day, 12, 0)
        if isinstance(datetime, date_obj):
            return self.start_on < date_obj and self.end_on > date_obj
        elif isinstance(int, date_obj):
            pass
        return False
        # not sure what to do??
        raise ValueError("Can not understand date object.")

    @classmethod
    def find_create_from(cls, year, month=None, day=None,
                         week=None, hour=None, minute=None, second=None,
                         dont_create=False, is_iso=False):

        if not week and not month:
            # assume year search
            sy = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
            ey = sy.replace(year=year + 1) - timedelta(ONE_MICROSECOND)
            try:
                period = cls.objects.filter(start_on__lte=sy,
                                            end_on__gte=ey)[0]
            except IndexError:
                period = cls.find_create_with(sy, ey)
            return period

        if week:
            return cls.find_create_by_weeknum(year=year,
                                              weeknum=week, is_iso=is_iso)

        month = month if month else 1
        day = day if day else 1
        hour = hour if hour else 0
        minute = minute if minute else 0
        second = second if second else 0

        date_obj = datetime(year, month, day, hour, minute, second,
                            tzinfo=timezone.utc)

        period = cls.find_create_by_date(date_obj, dont_create)

        return period

    @classmethod
    def find_create_by_date(cls, date_obj, dont_create=False):
        ''' creates a period to fit the provided date in '''
        if not isinstance(date_obj, datetime):
            date_obj = datetime.fromtimestamp(float(date_obj.strftime('%s')))
            date_obj = datetime(date_obj.year, date_obj.month,
                                date_obj.day, date_obj.hour,
                                date_obj.minute, 1,
                                tzinfo=timezone.utc)

        date_obj = normalize_date(date_obj, as_aware=True)
        try:
            period = [period for period in cls.objects.all()
                      if period.start_on <= date_obj
                      and period.end_on >= date_obj][0]
        except IndexError:

            period = cls.find_create_with(*cls.boundaries(date_obj))
            if dont_create:
                return period
            period.save()
        return period

    @classmethod
    def find_create_with(cls, start_on, end_on, period_type=None):
        ''' creates a period with defined start and end dates '''
        start_on = normalize_date(start_on, as_aware=True)
        end_on = normalize_date(end_on, as_aware=True)
        if not period_type:
            period_type = cls.type()
        try:
            period = cls.objects.get(start_on=start_on,
                                     end_on=end_on, period_type=period_type)
        except cls.DoesNotExist:
            period = cls(start_on=start_on, end_on=end_on,
                         period_type=period_type)
            period.save()
        return period

    @classmethod
    def find_create_by_weeknum(cls, year, weeknum, is_iso=False):

        # version 1
        # sw, ew = week_from_weeknum(year, week, is_iso=is_iso)
        # period = cls.find_create_with(sw, ew)
        # return period

        # version 2
        # soy = date(year, 1, 1)
        # d = soy + timedelta(WeekPeriod.delta() * weeknum)
        # return cls.find_create_by_date(d)

        sy = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
        # ey = datetime(year, 12, 31, 23, 59)
        ONE_WEEK = WeekPeriod.delta()

        # retrieve start of year day
        sy_dow = sy.isoweekday() if is_iso else sy.weekday()

        # find first real week (first Mon/Sun)
        if sy_dow != 0:
            sy = sy + timedelta(ONE_WEEK - sy_dow)

        # if we want first week, it's from Jan 1st to next Mon/Sun
        if weeknum == 0:
            start_week = sy
            end_week = start_week + timedelta(ONE_WEEK - sy_dow) \
                - timedelta(ONE_SECOND)
        else:
            weeknum -= 1  # cause we've set start as first real week
            start_week = sy + timedelta(ONE_WEEK * weeknum)
            end_week = start_week + timedelta(ONE_WEEK) - timedelta(ONE_SECOND)

        period = cls.find_create_with(start_week, end_week)
        return period

    @classmethod
    def find_create_by_quarter(cls, year, quarter):
        return YearPeriod.find_create_from(year, dont_create=True) \
                         .quarters_[quarter - 1]

    @classmethod
    def current(cls, dont_create=False):
        return cls.find_create_by_date(date_obj=date.today(),
                                       dont_create=dont_create)


class DayPeriod(Period):

    class Meta:
        proxy = True
        app_label = 'kurantooro'
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    objects = DayManager()

    @classmethod
    def type(cls):
        return cls.DAY

    def name(self):
        # Translators: Django's date format for DayPeriod.name()
        return date_format(self.middle(), ugettext("g/d/y"))

    def full_name(self):
        # Translators: Django's date format for DayPeriod.full_name()
        return date_format(self.middle(), ugettext("F d Y"))

    @classmethod
    def delta(self):
        return 1

    @classmethod
    def boundaries(cls, date_obj):
        date_obj = normalize_date(date_obj, as_aware=True)

        start = date_obj.replace(hour=0, minute=0,
                                 second=0, microsecond=0)
        end = start + timedelta(cls.delta()) - timedelta(ONE_MICROSECOND)
        return (start, end)

    def strid(self):
        return self.middle().strftime('%d-%m-%Y')


class WeekPeriod(Period):

    class Meta:
        proxy = True
        app_label = 'kurantooro'
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    objects = WeekManager()

    @classmethod
    def type(cls):
        return cls.WEEK

    @property
    def pid(self):
        return'W{}'.format(self.middle().strftime('%W-%Y'))

    def name(self):
        # Translators: Django's date format for WeekPeriod.name()
        return date_format(self.middle(), ugettext("W/Y"))

    def full_name(self):
        # Translators: Week Full name representation: weeknum, start and end
        return ugettext("Week %(weeknum)s (%(start)s to %(end)s)".format(
            weeknum=date_format(self.middle(), ugettext("W")),
            start=date_format(self.start_on, ugettext("d")),
            end=date_format(self.end_on, ugettext("d F Y"))))

    @classmethod
    def delta(self):
        return 7

    @classmethod
    def boundaries(cls, date_obj):
        date_obj = normalize_date(date_obj, as_aware=True)

        start = date_obj - timedelta(date_obj.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(cls.delta()) - timedelta(ONE_MICROSECOND)
        return (start, end)

    def strid(self):
        return self.middle().strftime('W%W-%Y')


class MonthPeriod(Period):

    class Meta:
        proxy = True
        app_label = 'kurantooro'
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    objects = MonthManager()

    @classmethod
    def type(cls):
        return cls.MONTH

    @property
    def pid(self):
        return self.middle().strftime('%m%Y')

    def name(self):
        # Translators: Django's date template format for MonthPeriod.name()
        return date_format(self.middle(), ugettext("F Y"))

    def full_name(self):
        # Translators: Django's date template format for MonthPeriod.full_name()
        return date_format(self.middle(), ugettext("F Y"))

    @classmethod
    def delta(self):
        return 31

    @classmethod
    def boundaries(cls, date_obj):
        date_obj = normalize_date(date_obj, as_aware=True)

        nyear, nmonth = next_month(date_obj.year, date_obj.month)

        start = date_obj.replace(day=1, hour=0, minute=0,
                                 second=0, microsecond=0)
        end = start.replace(year=nyear, month=nmonth) \
            - timedelta(ONE_MICROSECOND)
        return (start, end)

    def strid(self):
        return self.middle().strftime('%m-%Y')


class QuarterPeriod(Period):

    class Meta:
        proxy = True
        app_label = 'kurantooro'
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    objects = QuarterManager()

    @classmethod
    def type(cls):
        return cls.QUARTER

    @property
    def quarter(self):
        m = self.middle().month
        if m in (1, 2, 3):
            return 1
        elif m in (4, 5, 6):
            return 2
        elif m in (7, 8, 9):
            return 3
        else:
            return 4

    @property
    def pid(self):
        return 'Q{:d}.{}'.format((self.quarter, self.middle().strftime('%Y')))

    def name(self):
        # Translators: django date format for accompagning Quarter in Quarter.name()
        drepr = date_format(self.middle(), ugettext("Y"))
        # Translators: Quarter.name() repr using Quarter number and other
        return ugettext("Q%(quarter)s.%(year)s").format(
            year=drepr,
            quarter=self.quarter)

    def full_name(self):
        def ordinal(value):
            try:
                value = int(value)
            except ValueError:
                return value

            if value % 100 // 10 != 1:
                if value % 10 == 1:
                    # Translators: suffix for 1st
                    ordval = "{:d}{}".format((value, ugettext("st")))
                elif value % 10 == 2:
                    # Translators: suffix for 2nd
                    ordval = "{:d}{}".format((value, ugettext("nd")))
                elif value % 10 == 3:
                    # Translators: suffix for 3rd
                    ordval = "{:d}{}".format((value, ugettext("rd")))
                else:
                    # Translators: suffix for 4th
                    ordval = "{:d}{}".format((value, ugettext("th")))
            else:
                # Translators: suffix for 5th
                ordval = "{:d}{}".format((value, ugettext("th")))

            return ordval

        # Translators: Django's date format for QuarterPeriod.full_name()
        return "%(ordinal_quarter)s Quarter %(year)s (%(start)s to %(end)s)".format(
            ordinal_quarter=ordinal(self.quarter),
            year=date_format(self.middle(), ugettext("Y")),
            start=date_format(self.start_on, ugettext("F")),
            end=date_format(self.end_on, ugettext("F Y")))

    @classmethod
    def delta(self):
        return 93

    @classmethod
    def boundaries(cls, date_obj):

        date_obj = normalize_date(date_obj, as_aware=True)

        clean_start = date_obj.replace(month=1, day=1, hour=0, minute=0,
                                       second=0, microsecond=0)
        clean_end = clean_start - timedelta(ONE_MICROSECOND)
        clean_end = clean_end.replace(year=date_obj.year)

        if date_obj.month in (1, 2, 3):
            start = clean_start.replace(month=1)
            end = start.replace(month=4) - timedelta(ONE_MICROSECOND)
        elif date_obj.month in (4, 5, 6):
            start = clean_start.replace(month=4)
            end = start.replace(month=7) - timedelta(ONE_MICROSECOND)
        elif date_obj.month in (7, 8, 9):
            start = clean_start.replace(month=7)
            end = start.replace(month=10) - timedelta(ONE_MICROSECOND)
        else:
            start = clean_start.replace(month=10)
            end = clean_end

        return (start, end)

    def strid(self):
        return 'Q{}-{}'.format(str(self.quarter).zfill(2),
                               self.middle().strftime('%Y'))


class YearPeriod(Period):

    class Meta:
        proxy = True
        app_label = 'kurantooro'
        verbose_name = _("Period")
        verbose_name_plural = _("Periods")

    objects = YearManager()

    @classmethod
    def type(cls):
        return cls.YEAR

    def name(self):
        # Translators: Django's date format for YearPeriod.name()
        return date_format(self.middle(), ugettext("F"))

    def full_name(self):
        return self.name()

    @classmethod
    def delta(self):
        return 365

    @classmethod
    def boundaries(cls, date_obj):
        date_obj = normalize_date(date_obj, as_aware=True)

        start = date_obj.replace(month=0, day=0, hour=0, minute=0,
                                 second=0, microsecond=0)
        end = start.replace(year=date_obj.year + 1) - timedelta(ONE_MICROSECOND)
        return (start, end)

    def strid(self):
        return self.middle().strftime('%Y')
