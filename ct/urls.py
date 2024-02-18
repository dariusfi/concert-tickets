from django.contrib import admin
from django.urls import path

from ct.display.views import (
    agb,
    create_order_view,
    dashboard,
    delete_order_view,
    login_view,
    logout_view,
    payment_reminder,
    upload_statement,
)
from ct.service.api import Events, Tickets

urlpatterns = [
    path("", create_order_view, name="create_order"),
    path(
        "delete_order/<str:reference_code>/<str:delete_code>",
        delete_order_view,
        name="delete_order",
    ),
    path("login/", login_view(), name="login"),
    path("logout/", logout_view(), name="logout"),
    path("admin", admin.site.urls, name="admin"),
    path("agb", agb, name="agb"),
    path("upload_statement", upload_statement, name="upload_statement"),
    path("payment_reminder", payment_reminder, name="payment_reminder"),
    path("dashboard", dashboard, name="dashboard"),
    # API
    path("api/events", Events.as_view(), name="api_events"),
    path("api/event/<str:event_id>/tickets", Tickets.as_view(), name="api_tickets"),
]
