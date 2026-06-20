from flask import request
from app.controllers.BaseController import BaseController, admin_required
from app.models.AdminShipmentModel import ShipmentModel


ALLOWED_STATUSES = [ 'processing', 'in_transit', 'delivered', 'delayed', 'cancelled']


class ShipmentController(BaseController):

    @staticmethod
    @admin_required
    def get_all():
        """GET /api/admin/shipments?page=1&limit=20&status=&search="""
        try:
            page   = int(request.args.get('page', 1))
            limit  = int(request.args.get('limit', 20))
            status = request.args.get('status', '').strip() or None
            search = request.args.get('search', '').strip() or None

            rows, total = ShipmentModel.get_all_paginated(
                status=status, search=search, page=page, limit=limit
            )
            return ShipmentController.success(data={
                "shipments": rows,
                "pagination": {
                    "total":       total,
                    "page":        page,
                    "limit":       limit,
                    "total_pages": -(-total // limit)
                }
            })
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_one(shipment_id: int):
        """GET /api/admin/shipments/<id>"""
        try:
            row = ShipmentModel.get_by_id(shipment_id)
            if not row:
                return ShipmentController.not_found("Shipment not found")
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            row['updated_at'] = str(row['updated_at']) if row.get('updated_at') else None
            return ShipmentController.success(data=row)
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def create():
        """POST /api/admin/shipments"""
        try:
            data = request.get_json(silent=True) or {}
            for field in ['customer_id', 'destination', 'amount']:
                if field not in data:
                    return ShipmentController.error(f"Missing required field: {field}", 400)

            new_id, tracking_id = ShipmentModel.admin_create(data)
            return ShipmentController.success(
                data={"id": new_id, "tracking_id": tracking_id},
                message="Shipment created",
                status_code=201
            )
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_status(shipment_id: int):
        """PATCH /api/admin/shipments/<id>/status  — body: { "status": "delivered" }"""
        try:
            data       = request.get_json(silent=True) or {}
            new_status = (data.get('status') or '').strip()
            if new_status not in ALLOWED_STATUSES:
                return ShipmentController.error(
                    f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}", 400
                )
            affected = ShipmentModel.update_status(shipment_id, new_status)
            if affected == 0:
                return ShipmentController.not_found("Shipment not found")
            return ShipmentController.success(message=f"Status updated to '{new_status}'")
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def delete(shipment_id: int):
        """DELETE /api/admin/shipments/<id>"""
        try:
            affected = ShipmentModel.delete(shipment_id)
            if affected == 0:
                return ShipmentController.not_found("Shipment not found")
            return ShipmentController.success(message="Shipment deleted")
        except Exception as e:
            return ShipmentController.error(str(e), 500)
        
    @staticmethod
    @admin_required
    def get_customers():
        """GET /api/admin/customers — for dropdowns"""
        try:
            from app.models.database import execute_query
            customers = execute_query(
            "SELECT id, name, email FROM users WHERE role='customer' AND status='active' ORDER BY name",
            fetchall=True
        )
            return ShipmentController.success(data=customers)
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_agents():
        try:
            from app.models.database import execute_query
            agents = execute_query(
            "SELECT id, name, phone FROM delivery_agents WHERE status='active' ORDER BY name",
            fetchall=True
        )
            return ShipmentController.success(data=agents)
        except Exception as e:
            return ShipmentController.error(str(e), 500)
        
        #from flask import request
from app.controllers.BaseController import BaseController, admin_required
from app.models.AdminShipmentModel import ShipmentModel


ALLOWED_STATUSES = ['pending', 'processing', 'in_transit', 'delivered', 'delayed', 'cancelled']


class ShipmentController(BaseController):

    @staticmethod
    @admin_required
    def get_all():
        """GET /api/admin/shipments?page=1&limit=20&status=&search="""
        try:
            page   = int(request.args.get('page', 1))
            limit  = int(request.args.get('limit', 20))
            status = request.args.get('status', '').strip() or None
            search = request.args.get('search', '').strip() or None

            rows, total = ShipmentModel.get_all_paginated(
                status=status, search=search, page=page, limit=limit
            )
            return ShipmentController.success(data={
                "shipments": rows,
                "pagination": {
                    "total":       total,
                    "page":        page,
                    "limit":       limit,
                    "total_pages": -(-total // limit)
                }
            })
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_one(shipment_id: int):
        """GET /api/admin/shipments/<id>"""
        try:
            row = ShipmentModel.get_by_id(shipment_id)
            if not row:
                return ShipmentController.not_found("Shipment not found")
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            row['updated_at'] = str(row['updated_at']) if row.get('updated_at') else None
            return ShipmentController.success(data=row)
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def create():
        """POST /api/admin/shipments"""
        try:
            data = request.get_json(silent=True) or {}
            for field in ['customer_id', 'destination', 'amount']:
                if field not in data:
                    return ShipmentController.error(f"Missing required field: {field}", 400)

            new_id, tracking_id = ShipmentModel.admin_create(data)
            return ShipmentController.success(
                data={"id": new_id, "tracking_id": tracking_id},
                message="Shipment created",
                status_code=201
            )
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_status(shipment_id: int):
        """PATCH /api/admin/shipments/<id>/status  — body: { "status": "delivered" }"""
        try:
            data       = request.get_json(silent=True) or {}
            new_status = (data.get('status') or '').strip()
            if new_status not in ALLOWED_STATUSES:
                return ShipmentController.error(
                    f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}", 400
                )
            affected = ShipmentModel.update_status(shipment_id, new_status)
            if affected == 0:
                return ShipmentController.not_found("Shipment not found")
            return ShipmentController.success(message=f"Status updated to '{new_status}'")
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def delete(shipment_id: int):
        """DELETE /api/admin/shipments/<id>"""
        try:
            affected = ShipmentModel.delete(shipment_id)
            if affected == 0:
                return ShipmentController.not_found("Shipment not found")
            return ShipmentController.success(message="Shipment deleted")
        except Exception as e:
            return ShipmentController.error(str(e), 500)
        
    @staticmethod
    @admin_required
    def get_customers():
        """GET /api/admin/customers — for dropdowns"""
        try:
            from app.models.database import execute_query
            customers = execute_query(
            "SELECT id, name, email FROM users WHERE role='customer' AND status='active' ORDER BY name",
            fetchall=True
        )
            return ShipmentController.success(data=customers)
        except Exception as e:
            return ShipmentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_agents():
        try:
            from app.models.database import execute_query
            agents = execute_query(
            "SELECT id, name, phone FROM users WHERE role='agent' AND status='active' ORDER BY name",
            fetchall=True
        )
            return ShipmentController.success(data=agents)
        except Exception as e:
            return ShipmentController.error(str(e), 500)
       