from django.db import models
from django.contrib.auth.models import User


class Admin(models.Model):
    a_id = models.IntegerField(primary_key=True)
    a_email = models.CharField(max_length=100)
    a_password = models.CharField(max_length=100)
    a_name = models.CharField(max_length=100)
    a_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updateded_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'admin'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Brand(models.Model):
    b_id = models.IntegerField(primary_key=True)
    b_name = models.CharField(max_length=100)
    b_description = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    b_img = models.ImageField(upload_to='brands/', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brand'


class Customer(models.Model):
    c_id = models.AutoField(primary_key=True)
    a = models.ForeignKey(Admin, models.DO_NOTHING)
    c_name = models.CharField(max_length=100, blank=True, null=True)
    c_number = models.CharField(max_length=15, blank=True, null=True)
    c_email = models.CharField(max_length=150, blank=True, null=True)
    c_password = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    full_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customer'


class Delivery(models.Model):
    d_id = models.IntegerField(primary_key=True)
    d_decription = models.CharField(max_length=100, blank=True, null=True)
    d_ststus = models.BooleanField(blank=True, null=True)
    delpar = models.ForeignKey('Deliverypartner', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'delivery'


class Deliverypartner(models.Model):
    delpar_id = models.IntegerField(primary_key=True)
    delpar_name = models.CharField(max_length=100)
    delpar_number = models.CharField(max_length=100)
    delpar_email = models.CharField(max_length=100, blank=True, null=True)
    delpar_description = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'deliverypartner'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Payment(models.Model):
    payment_id = models.IntegerField(primary_key=True)
    payment_type = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.BooleanField(blank=True, null=True)
    payment_description = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'payment'


class Product(models.Model):
    p_id = models.IntegerField(primary_key=True)
    b = models.ForeignKey(Brand, models.DO_NOTHING, blank=True, null=True)
    p_name = models.CharField(max_length=100, blank=True, null=True)
    p_description = models.CharField(max_length=100, blank=True, null=True)
    p_img = models.ImageField(upload_to='products/', blank=True, null=True)
    p_price = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stock = models.IntegerField(null=False, default=0)

    class Meta:
        managed = False
        db_table = 'product'


class Reviews(models.Model):
    r_id = models.IntegerField(primary_key=True)
    r_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'reviews'


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=100)
    price = models.IntegerField()
    variant_img = models.ImageField(upload_to='variants/', blank=True, null=True)
    variant_description = models.CharField(max_length=200, blank=True, null=True)
    stock = models.IntegerField(null=False, default=0)

    def __str__(self):
        return f"{self.product.p_name} - {self.variant_name}"


class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_number = models.CharField(max_length=15)
    delivery_address = models.CharField(max_length=255)
    delivery_latitude = models.FloatField(blank=True, null=True)
    delivery_longitude = models.FloatField(blank=True, null=True)
    delivery_godown = models.ForeignKey('Godown', on_delete=models.SET_NULL, blank=True, null=True)
    delivery_charge = models.IntegerField(default=0)
    total_amount = models.IntegerField()
    status = models.CharField(max_length=50, default='Placed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderLineItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=150)
    price = models.IntegerField()
    quantity = models.IntegerField()
    img_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"


class Godown(models.Model):
    godown_name = models.CharField(max_length=100)
    area = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    manager = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_godown')

    def __str__(self):
        return f"{self.godown_name} ({self.area})"


class ProductStock(models.Model):
    godown = models.ForeignKey(Godown, on_delete=models.CASCADE, related_name='product_stocks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='godown_stocks')
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('godown', 'product')

    def __str__(self):
        return f"{self.product.p_name} @ {self.godown.godown_name}: {self.quantity}"


class VariantStock(models.Model):
    godown = models.ForeignKey(Godown, on_delete=models.CASCADE, related_name='variant_stocks')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='godown_stocks')
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('godown', 'variant')

    def __str__(self):
        return f"{self.variant.variant_name} @ {self.godown.godown_name}: {self.quantity}"


class StockTransfer(models.Model):
    from_godown = models.ForeignKey(Godown, on_delete=models.CASCADE, related_name='transfers_out')
    to_godown = models.ForeignKey(Godown, on_delete=models.CASCADE, related_name='transfers_in')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.IntegerField()
    transferred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        item = self.product.p_name if self.product else self.variant.variant_name
        return f"{item}: {self.from_godown.godown_name} -> {self.to_godown.godown_name} ({self.quantity})"