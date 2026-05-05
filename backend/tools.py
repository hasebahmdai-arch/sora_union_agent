from contextvars import ContextVar
from datetime import date

from langchain.tools import tool

from backend.mock_data import FAQS, ORDERS

current_user_email: ContextVar[str | None] = ContextVar(
    "current_user_email", default=None
)
current_user_id: ContextVar[int | None] = ContextVar(
    "current_user_id", default=None
)

_VALID_STATUSES = frozenset({"processing", "shipped", "delivered", "cancelled"})


@tool
def get_current_user_info() -> str:
    """Return authenticated user info from the real user database for the current session."""
    user_id = current_user_id.get()
    if user_id is None:
        return "Unable to fetch current user info: session context missing."
    from backend import database as db

    user = db.get_user_by_id(user_id)
    if not user:
        return "Unable to fetch current user info: user not found."
    return f"id: {user['id']}\nemail: {user['email']}\ncreated_at: {user['created_at']}"


@tool
def list_orders(status: str | None = None) -> str:
    """List orders, optionally filtered by status (processing, shipped, delivered, cancelled). Omit status to list all orders."""

    status_filter = None
    if status:
        s = status.strip().lower()
        if s not in _VALID_STATUSES:
            return (
                f"Invalid status '{status}'. Use one of: "
                "processing, shipped, delivered, cancelled, or omit for all orders."
            )
        status_filter = s

    rows = []
    for oid, order in sorted(ORDERS.items()):
        if status_filter and order["status"] != status_filter:
            continue
        rows.append(
            f"{order['id']} — {order['product']} — {order['status']} — {order['order_date']}"
        )

    if not rows:
        if status_filter:
            return f"No orders found with status '{status_filter}'."
        return "No orders on file."

    return "\n".join(rows)


@tool
def lookup_order(order_id: str) -> str:
    """Look up the status, shipping details, and refund eligibility for an order by order ID."""
    order = ORDERS.get(order_id.upper())
    if not order:
        return f"No order found with ID '{order_id}'. Please double-check the order ID."

    lines = [
        f"Order {order['id']} — {order['product']}",
        f"Status: {order['status'].capitalize()}",
        f"Order date: {order['order_date']}",
    ]

    if order["status"] == "shipped":
        lines.append(f"Carrier: {order['carrier']}  |  Tracking: {order['tracking']}")
        lines.append(f"Estimated delivery: {order['estimated_delivery']}")
    elif order["status"] == "delivered":
        lines.append(f"Delivered by {order['carrier']} (tracking: {order['tracking']})")
        days_since = (date.today() - order["estimated_delivery"]).days
        eligible = days_since <= 30
        lines.append(
            f"Refund eligible: {'Yes' if eligible else 'No'} "
            f"(delivered {days_since} days ago — window is 30 days)"
        )
    elif order["status"] == "processing":
        lines.append(
            f"Your order is being prepared. Expected to ship by {order['estimated_delivery']}."
        )
    elif order["status"] == "cancelled":
        lines.append("This order was cancelled and will not be shipped.")

    return "\n".join(lines)


@tool
def search_faq(query: str) -> str:
    """Search the ShopEasy FAQ for answers about policies, shipping, returns, payments, and account issues."""
    query_lower = query.lower()
    for faq in FAQS:
        if any(kw in query_lower for kw in faq["keywords"]):
            return f"Q: {faq['question']}\nA: {faq['answer']}"
    return (
        "I couldn't find a specific FAQ answer for that. "
        "Please contact our support team and we'll be happy to help."
    )


@tool
def create_support_ticket(issue: str) -> str:
    """Create a support ticket when the customer's issue cannot be resolved automatically. Uses the logged-in customer's email for follow-up."""
    import random

    email = current_user_email.get()
    if not email:
        return "Unable to create a ticket: session context missing."

    ticket_id = f"TKT-{random.randint(10000, 99999)}"
    return (
        f"Support ticket {ticket_id} has been created.\n"
        f"Issue: {issue}\n"
        f"We'll follow up at {email} within 24 hours."
    )
