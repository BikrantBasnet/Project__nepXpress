from app.controllers.BaseController import BaseController, admin_required
from app.models.AdminShipmentModel import ShipmentModel
from app.models.UserModel import User
from app.models.AdminDeliveryAgentModel import DeliveryAgentModel
from app.models.AdminAlertModel import AlertModel


class AdminDashboardController(BaseController):

    @staticmethod
    @admin_required
    def get_stats():
        """GET /api/admin/dashboard/stats — six KPI cards."""
        try:
            stats = {
                "total_shipments": {
                    "value":      ShipmentModel.get_total_count(),
                    "change_pct": ShipmentModel.get_monthly_change()
                },
                "delivered": {
                    "value":      ShipmentModel.get_count_by_status("delivered"),
                    "change_pct": ShipmentModel.get_monthly_change("delivered")
                },
                "pending": {
                    "value":      ShipmentModel.get_count_by_status("pending"),
                    "change_pct": ShipmentModel.get_monthly_change("pending")
                },
                "active_users": {
                    "value":          User.admin_get_active_count(),
                    "new_this_month": User.admin_get_new_this_month()
                },
                "delivery_agents": {
                    "value":          DeliveryAgentModel.get_total_count(),
                    "new_this_month": DeliveryAgentModel.get_new_agents_this_month()
                },
                "revenue_npr": {
                    "value":      float(ShipmentModel.get_total_revenue()),
                    "change_pct": ShipmentModel.get_revenue_change_this_month()
                }
            }
            return AdminDashboardController.success(data=stats)
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load stats: {str(e)}", 500)

    @staticmethod
    @admin_required
    def get_recent_shipments():
        """GET /api/admin/dashboard/shipments/recent"""
        try:
            shipments = ShipmentModel.get_recent_shipments(limit=10)
            for s in shipments:
                if s.get('created_at'):
                    s['created_at'] = str(s['created_at'])
            return AdminDashboardController.success(data=shipments)
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load shipments: {str(e)}", 500)

    @staticmethod
    @admin_required
    def get_top_agents():
        """GET /api/admin/dashboard/agents/top"""
        try:
            agents = DeliveryAgentModel.get_top_agents(limit=5)
            return AdminDashboardController.success(data=agents)
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load agents: {str(e)}", 500)

    @staticmethod
    @admin_required
    def get_delivery_status():
        """GET /api/admin/dashboard/delivery-status — pie chart breakdown."""
        try:
            breakdown = ShipmentModel.get_status_breakdown()
            return AdminDashboardController.success(data=breakdown)
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load delivery status: {str(e)}", 500)

    @staticmethod
    @admin_required
    def get_recent_users():
        """GET /api/admin/dashboard/users/recent"""
        try:
            users = User.admin_get_recent_customers(limit=10)
            for u in users:
                if u.get('created_at'):
                    u['created_at'] = str(u['created_at'])
            return AdminDashboardController.success(data=users)
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load users: {str(e)}", 500)

    @staticmethod
    @admin_required
    def get_system_alerts():
        """GET /api/admin/dashboard/alerts"""
        try:
            alerts = AlertModel.get_recent_alerts(limit=10)
            unread = AlertModel.get_unread_count()
            for a in alerts:
                if a.get('created_at'):
                    a['created_at'] = str(a['created_at'])
            return AdminDashboardController.success(data={
                "alerts":       alerts,
                "unread_count": unread
            })
        except Exception as e:
            return AdminDashboardController.error(f"Failed to load alerts: {str(e)}", 500)

    @staticmethod
    @admin_required
    def mark_alert_read(alert_id: int):
        """PATCH /api/admin/dashboard/alerts/<int:alert_id>/read"""
        try:
            AlertModel.mark_as_read(alert_id)
            return AdminDashboardController.success(message="Alert marked as read")
        except Exception as e:
            return AdminDashboardController.error(str(e), 500)