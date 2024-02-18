from ct.models.customer import Customer


def add_to_newsletter(email: str) -> None:
    customer, _ = Customer.objects.get_or_create(email=email)
    customer.allows_advertising = True
    customer.save()
