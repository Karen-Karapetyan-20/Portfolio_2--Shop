from django.contrib import admin
from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.utils.safestring import mark_safe
from PIL import Image
from .models import (
    Category,
    Product,
    Notebook,
    Smartphone,
    CartProduct,
    Cart,
    Customer,
    Order
)


class SmartphoneAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if not instance.sd:
            self.fields["sd_volume_max"].widget.attrs.update({
                "readonly": True,
                "style": "background: lightgray;",
            })

    def clean(self):
        if not self.cleaned_data["sd"]:
            self.cleaned_data["sd_volume_max"] = None
        return self.cleaned_data


# class NotebookAdminForm(ModelForm):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields["image"].help_text = '''<span style='color:red; font-size:14px;'>
#         Ներբեռնման նկարի չափսերը {}x{} _ից մեծ լինելու դեպքում այն կկտրվի
#         </span>'''.format(*Product.MAX_RESOLUTION)
#
#     def clean_image(self):
#         image = self.cleaned_data["image"]
#         img = Image.open(image)
#         min_height, min_width = Product.MIN_RESOLUTION
#         max_height, max_width = Product.MAX_RESOLUTION
#         if image.size > Product.MAX_IMAGE_SIZE:
#             raise ValidationError("Նկարի ծավալը չպետք է գերազանցի 3 Mb_ը")
#         if img.heigth < min_height or img.width < min_width:
#             raise ValidationError("Նկարի չափսերը փոքր են նվազագույն չափսերից")
#         if img.heigth > max_height or img.width > max_width:
#             raise ValidationError("Նկարի չափսերը մեծ են առավելագույն չափսերից")
#         return image


class NotebookAdmin(admin.ModelAdmin):
    # form = NotebookAdminForm()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            return ModelChoiceField(Category.objects.filter(slug="notebooks"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):
    change_form_template = "admin.html"
    form = SmartphoneAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            return ModelChoiceField(Category.objects.filter(slug="smartphones"))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)
admin.site.register(Notebook, NotebookAdmin)
admin.site.register(Smartphone, SmartphoneAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
