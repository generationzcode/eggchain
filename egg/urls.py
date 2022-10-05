from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('new_peer',views.new_peer,name="new_peer"),
    path('peer',views.peers,name="peers"),
    path('ping',views.ping,name="ping"),
    path('new_transaction',views.new_transaction,name="new_transaction"),
    path('make_edit',views.make_edit,name="make_edit"),
    path('make_edit_view',views.make_edit,name="make_edit_view"),
    path('new_block',views.new_block,name="new_block"),
    path('mine',views.mine,name="mine"),
    path('make_transaction',views.make_transaction,name="make_transaction"),
    path('transaction_form',views.transaction_form,name="transaction_form"),
    path('plots',views.plots_view,name="plots"),
    path('public_key',views.public_key,name="public_key"),
    path('chain_length',views.chain_length,name="chain_length"),
    path('block_num',views.get_block,name="block_num"),
    path('latest_block_info',views.get_block,name="latest_block_info"),
    path('initialize',views.initialize,name="initialize"),
  path('plots_owned',views.initialize,name="plots_owned"),
  path('change_network',views.change_network,name="change_network"),
  path('get_plot',views.get_plot_landscape,name="plot_landscape"),
  path('assets',views.assets,name="assets")
]