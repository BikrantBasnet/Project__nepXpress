from flask import Blueprint
from app.controllers.AdminAuthController import AdminAuthController
from app.controllers.AdminDashboardController import AdminDashboardController
from app.controllers.shipmentcontrollers import ShipmentController
from app.controllers.AdminUserController import AdminUserController

admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# ── Auth ─────────────────────────────────────────────────────────────────── #
admin_bp.add_url_rule('/login',  'admin_login',  AdminAuthController.login,  methods=['POST'])
admin_bp.add_url_rule('/logout', 'admin_logout', AdminAuthController.logout, methods=['POST'])
admin_bp.add_url_rule('/me',     'admin_me',     AdminAuthController.me,     methods=['GET'])

# ── Dashboard ─────────────────────────────────────────────────────────────── #
admin_bp.add_url_rule('/dashboard/stats',                      'dash_stats',     AdminDashboardController.get_stats,            methods=['GET'])
admin_bp.add_url_rule('/dashboard/shipments/recent',           'dash_shipments', AdminDashboardController.get_recent_shipments, methods=['GET'])
admin_bp.add_url_rule('/dashboard/agents/top',                 'dash_agents',    AdminDashboardController.get_top_agents,       methods=['GET'])
admin_bp.add_url_rule('/dashboard/delivery-status',            'dash_status',    AdminDashboardController.get_delivery_status,  methods=['GET'])
admin_bp.add_url_rule('/dashboard/users/recent',               'dash_users',     AdminDashboardController.get_recent_users,     methods=['GET'])
admin_bp.add_url_rule('/dashboard/alerts',                     'dash_alerts',    AdminDashboardController.get_system_alerts,    methods=['GET'])
admin_bp.add_url_rule('/dashboard/alerts/<int:alert_id>/read', 'dash_alert_read',AdminDashboardController.mark_alert_read,     methods=['PATCH'])

# ── Shipment management ───────────────────────────────────────────────────── #
admin_bp.add_url_rule('/shipments',                         'ship_list',   ShipmentController.get_all,       methods=['GET'])
admin_bp.add_url_rule('/shipments',                         'ship_create', ShipmentController.create,        methods=['POST'])
admin_bp.add_url_rule('/shipments/<int:shipment_id>',       'ship_one',    ShipmentController.get_one,       methods=['GET'])
admin_bp.add_url_rule('/shipments/<int:shipment_id>/status','ship_status', ShipmentController.update_status, methods=['PATCH'])
admin_bp.add_url_rule('/shipments/<int:shipment_id>',       'ship_delete', ShipmentController.delete,        methods=['DELETE'])
admin_bp.add_url_rule('/customers', 'customers_list', ShipmentController.get_customers, methods=['GET'])
admin_bp.add_url_rule('/agents',    'agents_list',    ShipmentController.get_agents,    methods=['GET'])


#-- User management ────────────────────────────────────────────────────────────── #
admin_bp.add_url_rule('/users',                    'users_list',          AdminUserController.get_all,       methods=['GET'])
admin_bp.add_url_rule('/users/stats',              'users_stats',         AdminUserController.get_stats,     methods=['GET'])
admin_bp.add_url_rule('/users/<int:user_id>',      'users_one',           AdminUserController.get_one,       methods=['GET'])
admin_bp.add_url_rule('/users/<int:user_id>/status','users_status',       AdminUserController.update_status, methods=['PATCH'])
admin_bp.add_url_rule('/users/<int:user_id>/role', 'users_role',          AdminUserController.update_role,   methods=['PATCH'])
admin_bp.add_url_rule('/users/<int:user_id>',      'users_delete',        AdminUserController.delete,        methods=['DELETE'])
