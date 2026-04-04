"""
config/constants.py

System-wide constants used across GaragePulse.
Keeping these centralized prevents hardcoding values across modules.
"""


# ============================================
# User Roles
# ============================================

class Roles:
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    STAFF = "STAFF"


# ============================================
# Account Status
# ============================================

class AccountStatus:
    ACTIVE = True
    INACTIVE = False


# ============================================
# Work Order Status
# ============================================

class WorkOrderStatus:
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


WORK_ORDER_STATUS_LIST = [
    WorkOrderStatus.NEW,
    WorkOrderStatus.IN_PROGRESS,
    WorkOrderStatus.READY,
    WorkOrderStatus.COMPLETED,
    WorkOrderStatus.CANCELLED,
]


# ============================================
# Invoice Payment Status
# ============================================

class PaymentStatus:
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    VOID = "VOID"


PAYMENT_STATUS_LIST = [
    PaymentStatus.PENDING,
    PaymentStatus.PARTIAL,
    PaymentStatus.PAID,
    PaymentStatus.VOID,
]


# ============================================
# Notification Channels
# ============================================

class NotificationChannel:
    EMAIL = "EMAIL"
    SMS = "SMS"


NOTIFICATION_CHANNEL_LIST = [
    NotificationChannel.EMAIL,
    NotificationChannel.SMS,
]


# ============================================
# Notification Delivery Status
# ============================================

class NotificationDeliveryStatus:
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


NOTIFICATION_DELIVERY_STATUS_LIST = [
    NotificationDeliveryStatus.PENDING,
    NotificationDeliveryStatus.SENT,
    NotificationDeliveryStatus.FAILED,
]


# ============================================
# UI Labels
# ============================================

class UILabels:
    WORK_ORDER_ID = "Work Order ID"
    CUSTOMER_NAME = "Customer Name"
    VEHICLE = "Vehicle"
    PHONE = "Phone"
    EMAIL = "Email"
    STATUS = "Status"
    CREATED_AT = "Created At"
    UPDATED_AT = "Updated At"


# ============================================
# ID Prefixes
# ============================================

class IDPrefixes:
    WORK_ORDER = "WO"
    INVOICE = "INV"
    CUSTOMER = "CUS"
    VEHICLE = "VEH"


# ============================================
# Date Formats
# ============================================

class DateFormats:
    DATE = "%Y-%m-%d"
    DATETIME = "%Y-%m-%d %H:%M:%S"
    DISPLAY = "%b %d, %Y"
    DISPLAY_DATETIME = "%b %d, %Y %I:%M %p"


# ============================================
# Pagination Defaults
# ============================================

DEFAULT_PAGE_SIZE = 20


# ============================================
# Vehicle Fields
# ============================================

class VehicleFields:
    PLATE_NUMBER = "plate_number"
    VIN = "vin"


# ============================================
# Search Types
# ============================================

class SearchFields:
    PHONE = "phone"
    VEHICLE_PLATE = "plate_number"
    CUSTOMER_NAME = "customer_name"
    WORK_ORDER_ID = "work_order_id"