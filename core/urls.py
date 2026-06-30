from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("donor/profile/", views.donor_profile, name="donor_profile"),
    path("donor/appointment/", views.book_appointment, name="book_appointment"),
    path("hospital/add-unit/", views.add_unit, name="add_unit"),
    path("hospital/request/", views.create_request, name="create_request"),
    path("request/<int:request_id>/fulfill/", views.fulfill_request, name="fulfill_request"),
    path("dispatch/<int:dispatch_id>/complete/", views.complete_dispatch, name="complete_dispatch"),
]
