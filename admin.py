"""
Admin configuration for the Interiors model.

This module customizes the Django admin interface for managing Interiors objects.
It leverages reversion's VersionAdmin to provide version control capabilities.

Classes:
    InteriorsAdmin: Custom admin interface for the Interiors model.
"""
from django.contrib import admin
from reversion.admin import VersionAdmin
from django.utils.html import format_html
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from django.utils.text import slugify

class MultipleFileInput(forms.ClearableFileInput):
    """
   A file widget that allows you to edit multiple files.
    """
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    Field for importing multiple files.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """
        Processing multiple files.
        """
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class BulkImageUploadForm(forms.Form):
    """
    Form for uploading multiple images.
    """
    images = MultipleFileField(
        label=_("Images")
    )


@admin.register(Interiors)
class InteriorsAdmin(VersionAdmin):
    """
    Custom admin configuration for the Interiors model.

    Attributes:
        list_display (list): Fields displayed in the admin model list view.
        ordering (list): Default ordering of Interiors objects in the admin interface.
        search_fields (list): Fields searchable in the admin interface.
    """
    list_display = ["id", "name", "image_preview"]
    ordering = ["id", "name"]
    search_fields = ["name"]
    change_list_template = "admin/interiors/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name='interiors_interiors_bulk-upload'
            ),
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        if request.method == 'POST':
            form = BulkImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                images = request.FILES.getlist('images')
                
                interiors_created = 0
                errors = []

                for image in images:
                    try:
                        # Extract filename without extension
                        filename = image.name.rsplit('.', 1)[0]
                        
                        # Create name from filename
                        name = filename.replace('_', ' ').replace('-', ' ').title()
                        
                        # Create new interior
                        interior = Interiors(
                            name=name,
                            image=image,
                        )
                        interior.save()
                        interiors_created += 1
                    except Exception as e:
                        errors.append(f"Error creating interior '{name}': {str(e)}")

                # Show result messages
                if interiors_created > 0:
                    messages.success(request, f"Successfully created {interiors_created} interiors.")
                
                for error in errors:
                    messages.error(request, error)

                return redirect('admin:interiors_interiors_changelist')
        else:
            form = BulkImageUploadForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'title': _('Bulk Upload Images')
        }
        return render(request, 'admin/interiors/bulk_upload.html', context)

    
    def image_preview(self, obj):
        """Return an HTML img tag displaying the object's image."""
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px; border-radius:5px;" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Preview"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        if "view" in request.GET:
            view_mode = request.GET["view"]
            request.session["view_mode"] = view_mode 
        else:
            view_mode = request.session.get("view_mode", "list") 

        print(f"View mode: {view_mode}")

        extra_context["view_mode"] = view_mode
        return super().changelist_view(request, extra_context=extra_context)   