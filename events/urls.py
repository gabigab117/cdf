from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('<int:event_pk>/postes/', views.station_board, name='station_board'),
    path('<int:event_pk>/postes/creer/', views.station_create, name='station_create'),
    path('postes/<int:station_pk>/supprimer/', views.station_delete, name='station_delete'),
    path('postes/<int:station_pk>/affecter/', views.assignment_add, name='assignment_add'),
    path('affectations/<int:assignment_pk>/retirer/', views.assignment_remove, name='assignment_remove'),
]
