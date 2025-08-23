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

__all__ = [
    "MeView",
    "UserListCreateView",
    "UserDetailUpdateView",
    "UserDeleteView",
    "ProductListCreateView",
    "ProductDetailUpdateView",
    "ProductDeleteView",
]
