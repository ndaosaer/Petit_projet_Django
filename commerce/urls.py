from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions_list, name='transactions'),
    path('transactions/ajouter/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/modifier/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/supprimer/', views.transaction_delete, name='transaction_delete'),
    path('balance/', views.balance_commerciale, name='balance'),
    path('analyse-pays/', views.analyse_pays, name='analyse_pays'),
    path('top-produits/', views.top_produits, name='top_produits'),
    path('anomalies/', views.detection_anomalies, name='anomalies'),
    path('sankey/', views.sankey_view, name='sankey'),
    path('codes-sh/', views.analyse_codes_sh, name='codes_sh'),
    path('blocs/', views.analyse_blocs, name='blocs'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('series-temporelles/', views.series_temporelles, name='series_temporelles'),
]
