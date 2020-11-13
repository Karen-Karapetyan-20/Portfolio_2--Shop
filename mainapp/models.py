from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={"ct_model": ct_model, "slug": obj.slug})


class MinResolutionErrorException(Exception):
    pass


class MaxResolutionErrorException(Exception):
    pass


class LatestProductsManager:
    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get("with_respect_to")
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_models.model_class()._base_manager.all().order_by("-id")
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products,
                        key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                        reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Model):
    CATEGORY_NAME_COUNT_NAME = {
        "Նոթբուքեր": "notebook__count",
        "Սմարթֆոններ": "smartphone__count"
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count("notebook", "smartphone")
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Կատեգորիա")
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Կատեգորիա")
    title = models.CharField(max_length=255, verbose_name="Անվանում")
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name="Նկար")
    description = models.TextField(verbose_name="Նկարագրություն", null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Գին")

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        # min_height, min_width = self.MIN_RESOLUTION
        # max_height, max_width = self.MAX_RESOLUTION
        # if img.heigth < min_height or img.width < min_width:
        #     raise MinResolutionErrorException("Նկարի չափսերը փոքր են նվազագույն չափսերից")
        # if img.heigth > max_height or img.width > max_width:
        #     raise MaxResolutionErrorException("Նկարի չափսերը մեծ են առավելագույն չափսերից")

        new_img = img.concert("RGB")
        resize_new_img = new_img.resize((800, 800), Image.ANTIALIAS)
        filestream = BytesIO()
        resize_new_img.save(filestream, "JPEG", quality=90)
        filestream.seek(0)
        name = "{}.{}".format(self.image.name.split("."))
        self.image = InMemoryUploadedFile(
            filestream, "ImageField", name, "jpeg/image", sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)


class Notebook(Product):
    diagonal = models.CharField(max_length=255, verbose_name="Անկյունագիծ")
    display_type = models.CharField(max_length=255, verbose_name="Ցուցադրման տիպ")
    processor_freq = models.CharField(max_length=255, verbose_name="Պրոցեսորի մաքրություն")
    ram = models.CharField(max_length=255, verbose_name="Օպերատիվ հիշողություն")
    video = models.CharField(max_length=255, verbose_name="Վիդեոքարտ")
    time_without_charge = models.CharField(max_length=255, verbose_name="Մարտկոցի աշխատանքի ժամանակ")

    def __str__(self):
        return f"{self.category.name} | {self.title}"

    def get_absolute_url(self):
        return get_product_url(self, "product_detail")


class Smartphone(Product):
    diagonal = models.CharField(max_length=255, verbose_name="Անկյունագիծ")
    display_type = models.CharField(max_length=255, verbose_name="Ցուցադրման տիպ")
    resolution = models.CharField(max_length=255, verbose_name="Էկրանի ընդլայնում")
    accum_volume = models.CharField(max_length=255, verbose_name="Մարտկոցի ծավալ")
    ram = models.CharField(max_length=255, verbose_name="Օպերատիվ հիշողություն")
    sd = models.BooleanField(default=True, verbose_name="Ներդրված SD քարտի հիշողության ծավալ")
    sd_volume_max = models.CharField(max_length=255, null=True, blank=True,
                                     verbose_name="Մեծագույն ներդրման հիշողության ծավալ")
    main_cam_mp = models.CharField(max_length=255, verbose_name="Ետևի տեսախցիկ")
    frontal_cam_mp = models.CharField(max_length=255, verbose_name="Առջևի տեսախցիկ")

    def __str__(self):
        return f"{self.category.name} | {self.title}"

    def get_absolute_url(self):
        return get_product_url(self, "product_detail")

    # @property
    # def sd(self):
    #     if self.sd:
    #         return "Այո"
    #     return "Ոչ"


class CartProduct(models.Model):
    user = models.ForeignKey("Customer", on_delete=models.CASCADE, verbose_name="Հաճախորդ")
    cart = models.ForeignKey("Cart", on_delete=models.CASCADE, verbose_name="Զամբյուղ", related_name="related_product")
    # product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Ապրանք")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Վերջնական գին")

    def __str__(self):
        return f"Ապրանք՝ {self.content_object.title} (զամբյուղի համար)"

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey("Customer", null=True, on_delete=models.CASCADE, verbose_name="Սեփականատեր")
    products = models.ManyToManyField(CartProduct, blank=True, related_name="related_cart")
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name="Վերջնական գին")
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Գնորդ")
    phone = models.CharField(max_length=20, verbose_name="Հեռախոսահամար", null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name="Հասցե", null=True, blank=True)
    orders = models.ManyToManyField("Order", related_name="related_customer", verbose_name="Գնորդի պատվերներ")

    def __str__(self):
        return f"Գնորդ՝ {self.user.first_name} {self.user.last_name}"


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "is_ready"
    STATUS_COMPLETED = "completed"
    BUYING_TYPE_SELF = "self"
    BUYING_TYPE_DELIVERY = "delivery"

    STATUS_CHOICES = (
        (STATUS_NEW, "Նոր պատվեր"),
        (STATUS_IN_PROGRESS, "Պատվերն ընթացքի մեջ է"),
        (STATUS_READY, "Պատվերը պատրաստ է"),
        (STATUS_COMPLETED, "Պատվերը ստացված է")
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, "Ինքնականչ"),
        (BUYING_TYPE_DELIVERY, "Առաքում")
    )

    customer = models.ForeignKey(Customer, related_name="related_orders", verbose_name="Գնորդ",
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name="Անուն")
    last_name = models.CharField(max_length=255, verbose_name="Ազգանուն")
    phone = models.CharField(max_length=20, verbose_name="Հեռախոսահամար")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name="Զամբյուղ", null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name="Հասցե", null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name="Պատվերի կարգավիճակ",
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name="Պատվերի տեսակ",
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name="Պատվերի մեկնաբանություն", null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name="Պատվերի ստեղծվելու ժամանակ")
    order_date = models.DateTimeField(default=timezone.now, verbose_name="Պատվերի ստացման ժամանակ")

    def __str__(self):
        return str(self.id)
