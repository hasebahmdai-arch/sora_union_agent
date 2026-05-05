from datetime import date

DEMO_USER_EMAILS = [
    "alice@example.com",
    "bob@example.com",
    "carol@example.com",
    "dan@example.com",
    "eva@example.com",
]
DEMO_PASSWORD = "password"

ORDERS = {
    "ORD-1001": {
        "id": "ORD-1001",
        "customer": "Alice Johnson",
        "email": "alice@example.com",
        "product": "Wireless Headphones",
        "status": "shipped",
        "tracking": "FX938471023",
        "carrier": "FedEx",
        "order_date": date(2026, 4, 28),
        "estimated_delivery": date(2026, 5, 7),
    },
    "ORD-1002": {
        "id": "ORD-1002",
        "customer": "Bob Smith",
        "email": "bob@example.com",
        "product": "Running Shoes (Size 10)",
        "status": "delivered",
        "tracking": "UPS784920183",
        "carrier": "UPS",
        "order_date": date(2026, 4, 10),
        "estimated_delivery": date(2026, 4, 15),
    },
    "ORD-1003": {
        "id": "ORD-1003",
        "customer": "Carol White",
        "email": "carol@example.com",
        "product": "Yoga Mat",
        "status": "delivered",
        "tracking": "USPS3847201938",
        "carrier": "USPS",
        "order_date": date(2026, 3, 1),
        "estimated_delivery": date(2026, 3, 6),
    },
    "ORD-1004": {
        "id": "ORD-1004",
        "customer": "Dan Brown",
        "email": "dan@example.com",
        "product": "Mechanical Keyboard",
        "status": "processing",
        "tracking": None,
        "carrier": None,
        "order_date": date(2026, 5, 4),
        "estimated_delivery": date(2026, 5, 10),
    },
    "ORD-1005": {
        "id": "ORD-1005",
        "customer": "Eva Green",
        "email": "eva@example.com",
        "product": "Desk Lamp",
        "status": "cancelled",
        "tracking": None,
        "carrier": None,
        "order_date": date(2026, 4, 20),
        "estimated_delivery": None,
    },
}

FAQS = [
    {
        "keywords": ["return", "refund policy", "how to return", "return policy"],
        "question": "What is your return policy?",
        "answer": "We accept returns within 30 days of delivery for unused items in original packaging. To start a return, contact support with your order ID.",
    },
    {
        "keywords": ["shipping time", "how long", "delivery time", "when will"],
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 3–7 business days. Express shipping (1–2 days) is available at checkout for an additional fee.",
    },
    {
        "keywords": ["payment", "pay", "credit card", "paypal", "accepted"],
        "question": "What payment methods do you accept?",
        "answer": "We accept Visa, Mastercard, American Express, PayPal, and Apple Pay.",
    },
    {
        "keywords": ["cancel", "cancel order", "stop order"],
        "question": "Can I cancel my order?",
        "answer": "Orders can be cancelled within 1 hour of placement. After that, the order enters processing and cannot be cancelled. Contact support immediately if you need to cancel.",
    },
    {
        "keywords": ["track", "tracking", "where is my package", "track order"],
        "question": "How do I track my order?",
        "answer": "Once your order ships, you'll receive a tracking number via email. You can also ask here with your order ID and I'll look it up for you.",
    },
    {
        "keywords": ["exchange", "swap", "wrong size", "wrong item"],
        "question": "Can I exchange an item?",
        "answer": "Yes, exchanges are accepted within 30 days of delivery. Contact support with your order ID and the item you'd like instead.",
    },
    {
        "keywords": ["damaged", "broken", "defective", "arrived damaged"],
        "question": "My item arrived damaged. What do I do?",
        "answer": "We're sorry to hear that! Please contact support with your order ID and a photo of the damage. We'll send a replacement or issue a full refund.",
    },
    {
        "keywords": ["password", "account", "login", "reset", "forgot"],
        "question": "I can't log in to my account.",
        "answer": "Click 'Forgot Password' on the login page to reset your password via email. If issues persist, contact support and we'll verify your identity manually.",
    },
]
