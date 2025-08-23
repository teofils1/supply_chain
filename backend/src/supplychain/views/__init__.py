from .auth import MeView
from .user import (
    UserDeleteView,
    UserDetailUpdateView,
    UserListCreateView,
)
from .product import (
    ProductDeleteView,
    ProductDetailUpdateView,
    ProductListCreateView,
)
from .batch import (
    BatchDeleteView,
    BatchDetailUpdateView,
    BatchListCreateView,
)
from .pack import (
    PackDeleteView,
    PackDetailUpdateView,
    PackListCreateView,
)
from .shipment import (
    ShipmentDeleteView,
    ShipmentDetailUpdateView,
    ShipmentListCreateView,
)
from .event import (
    EventDeleteView,
    EventDetailUpdateView,
    EventListCreateView,
)

__all__ = [
    "MeView",
    "UserListCreateView",
    "UserDetailUpdateView",
    "UserDeleteView",
    "ProductListCreateView",
    "ProductDetailUpdateView",
    "ProductDeleteView",
    "BatchListCreateView",
    "BatchDetailUpdateView",
    "BatchDeleteView",
    "PackListCreateView",
    "PackDetailUpdateView",
    "PackDeleteView",
    "ShipmentListCreateView",
    "ShipmentDetailUpdateView",
    "ShipmentDeleteView",
    "EventListCreateView",
    "EventDetailUpdateView",
    "EventDeleteView",
]
