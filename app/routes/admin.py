from flask import Blueprint

from app.controllers.AdminAuthController import AdminAuthController
from app.controllers.AdminDashboardController import AdminDashboardController
from app.controllers.shipmentcontrollers import ShipmentController
from app.controllers.AdminUserController import AdminUserController
from app.controllers.AdminAgentController import AdminAgentController
from app.controllers.AdminReportsController import AdminReportsController
from app.controllers.AdminSettingsController import AdminSettingsController


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


#-- Delivery agent management ────────────────────────────────────────────────── #
admin_bp.add_url_rule('/delivery-agents',                       'da_list',   AdminAgentController.get_all,       methods=['GET'])
admin_bp.add_url_rule('/delivery-agents/stats',                 'da_stats',  AdminAgentController.get_stats,     methods=['GET'])
admin_bp.add_url_rule('/delivery-agents',                       'da_create', AdminAgentController.create,        methods=['POST'])
admin_bp.add_url_rule('/delivery-agents/<int:agent_id>',        'da_one',    AdminAgentController.get_one,       methods=['GET'])
admin_bp.add_url_rule('/delivery-agents/<int:agent_id>',        'da_update', AdminAgentController.update,        methods=['PUT'])
admin_bp.add_url_rule('/delivery-agents/<int:agent_id>/status', 'da_status', AdminAgentController.update_status, methods=['PATCH'])
admin_bp.add_url_rule('/delivery-agents/<int:agent_id>',        'da_delete', AdminAgentController.delete,        methods=['DELETE'])




#── Reports ─────────────────────────────────────────────────────────────── #
admin_bp.add_url_rule('/reports/summary',           'reports_summary',   AdminReportsController.get_summary,          methods=['GET'])
admin_bp.add_url_rule('/reports/revenue-monthly',   'reports_revenue',   AdminReportsController.get_revenue_monthly,  methods=['GET'])
admin_bp.add_url_rule('/reports/shipments-monthly', 'reports_shipments', AdminReportsController.get_shipments_monthly,methods=['GET'])
admin_bp.add_url_rule('/reports/agent-performance', 'reports_agents',    AdminReportsController.get_agent_performance,methods=['GET'])
admin_bp.add_url_rule('/reports/customer-activity', 'reports_customers', AdminReportsController.get_customer_activity,methods=['GET'])



#── Settings ───────────────────────────────────────────────────────────── #
admin_bp.add_url_rule('/settings/profile',       'settings_profile',      AdminSettingsController.get_profile,         methods=['GET'])
admin_bp.add_url_rule('/settings/profile',       'settings_profile_save', AdminSettingsController.update_profile,      methods=['PATCH'])
admin_bp.add_url_rule('/settings/password',      'settings_password',     AdminSettingsController.update_password,     methods=['PATCH'])
admin_bp.add_url_rule('/settings/system',        'settings_system',       AdminSettingsController.get_system,          methods=['GET'])
admin_bp.add_url_rule('/settings/system',        'settings_system_save',  AdminSettingsController.update_system,       methods=['PATCH'])
admin_bp.add_url_rule('/settings/notifications', 'settings_notif',        AdminSettingsController.get_notifications,   methods=['GET'])
admin_bp.add_url_rule('/settings/notifications', 'settings_notif_save',   AdminSettingsController.update_notifications,methods=['PATCH'])