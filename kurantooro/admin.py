#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

from kurantooro.models.Models import Report, Category, Problem, KuranUser
from kurantooro.models.Period import Period


class UserModificationForm(forms.ModelForm):
    class Meta:
        model = KuranUser


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = KuranUser
        fields = ('email',)

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserAdmin(UserAdmin):
    form = UserModificationForm
    add_form = UserCreationForm
    list_display = ("username", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'first_name',
                           'last_name', 'is_superuser', 'is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'first_name', 'last_name',
                       'is_superuser', 'is_staff', 'is_active')}),
    )


class CustomReport(admin.ModelAdmin):
    list_display = ("created_on", "kuran_user")
    list_filter = ("created_on", "kuran_user")


class CustomCategory(admin.ModelAdmin):
    list_display = ("slug", "name")


class CustomProblem(admin.ModelAdmin):
    list_display = ("slug", "name", "category")
    list_filter = ("category",)


admin.site.register(Report, CustomReport)
admin.site.register(Category, CustomCategory)
admin.site.register(Problem, CustomProblem)
admin.site.register(KuranUser, CustomUserAdmin)
admin.site.register(Period)
