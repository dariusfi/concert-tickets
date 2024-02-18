# This is necessary for Django makemigrations to detect new models. By default,
# it only looks into models.py.
from .order import Order
from .ticket import Ticket  
from .customer import Customer
from .event import Event