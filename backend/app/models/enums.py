import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    moderator = "moderator"
    support = "support"
    superadmin = "superadmin"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    successful = "successful"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class PromotionStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class ReportTargetType(str, enum.Enum):
    listing = "listing"
    user = "user"
    message = "message"


class ReportStatus(str, enum.Enum):
    open = "open"
    in_review = "in_review"
    resolved = "resolved"
    dismissed = "dismissed"


class NotificationType(str, enum.Enum):
    listing_approved = "listing_approved"
    listing_rejected = "listing_rejected"
    new_message = "new_message"
    report_status_changed = "report_status_changed"
    payment_successful = "payment_successful"
    promotion_activated = "promotion_activated"
    promotion_expired = "promotion_expired"
