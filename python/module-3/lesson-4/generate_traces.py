"""Generate 1000 synthetic traces for OfficeFlow Supply Co. customer support.

Produces synthetic_traces.json with 1000 traces (200 per category):
  - inventory: product stock/availability questions
  - policy: company policy questions (returns, shipping, etc.)
  - out_of_scope: things Emma can't help with
  - both: inventory AND policy in one message
  - website_troubleshooting: website/portal issues

Each trace = 2 runs: root "Emma" chain + child "ChatOpenAI" llm.
"""

import json
import random
import uuid
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CATEGORIES = ["inventory", "policy", "out_of_scope", "both", "website_troubleshooting"]
TRACES_PER_CATEGORY = 200
OUTPUT_FILE = "synthetic_traces.json"

SYSTEM_PROMPT = (
    "You are Emma, a customer support specialist for OfficeFlow Supply Co., "
    "a paper and office supplies distribution company serving small-to-medium "
    "businesses across North America.\n\nABOUT YOUR ROLE:\nYou're part of the "
    "Customer Experience team and have been with OfficeFlow for 3 years. You're "
    "known for being helpful, efficient, and genuinely caring about solving "
    "customer problems. Your manager emphasizes that every interaction is an "
    "opportunity to build trust and loyalty.\n\nWHAT YOU CAN HELP WITH:\n"
    "\u2713 Product Information - Answer questions about our catalog of office "
    "supplies, paper products, writing instruments, organizational tools, and "
    "desk accessories\n\u2713 Inventory & Availability - Check current stock "
    "levels and help customers find what they need\n\u2713 Product Recommendations "
    "- Suggest products based on customer needs, usage patterns, and budget\n"
    "\u2713 General Inquiries - Handle questions about our company, product lines, "
    "and services\n\nWHAT YOU CANNOT DIRECTLY HANDLE:\n\u2717 Order Placement - "
    "While you can provide product info, actual ordering is done through our web "
    "portal or by contacting our sales team at sales@officeflow.com\n\u2717 Order "
    "Status & Tracking - Direct customers to check their account portal or contact "
    "fulfillment@officeflow.com\n\u2717 Returns & Refunds - These require approval "
    "from our Returns Department at returns@officeflow.com\n\u2717 Account Changes "
    "- Billing, payment methods, and account settings must go through "
    "accounts@officeflow.com\n\u2717 Technical Support - For website issues, direct "
    "to support@officeflow.com"
)

PRODUCTS = [
    "Copy Paper 500 Sheets", "Blue Ballpoint Pens (12-pack)",
    "Stapler with Staples", "Spiral Notebooks (3-pack)",
    "Manila File Folders (25-pack)", "Sticky Notes (4-pack)",
    "Dry Erase Markers (8-pack)", "Paper Clips (100-pack)",
    "Binder Clips (24-pack)", "Legal Pads (6-pack)",
    "Highlighters (5-pack)", "Desk Organizer Tray",
    "Correction Tape (3-pack)", "Scissors - 8 inch",
    "Rubber Bands (Assorted)", "Tape Dispenser with Tape",
    "Envelopes #10 (100-pack)", "Index Cards (3x5, 100-pack)",
    "Whiteboard Eraser", "Push Pins (100-pack)",
    "Hanging File Folders (25-pack)", "Sheet Protectors (50-pack)",
    "Mechanical Pencils (12-pack)", "Black Gel Pens (6-pack)",
    "Desk Calendar 2026", "Letter Trays (2-tier)",
    "Glue Sticks (6-pack)", "Post-it Flags (4 colors)",
    "Laminating Pouches (50-pack)", "Clipboard - Standard",
]

NAMES = [
    "Alex", "Jordan", "Sam", "Casey", "Morgan", "Taylor", "Riley", "Jamie",
    "Pat", "Chris", "Drew", "Quinn", "Avery", "Blake", "Cameron", "Dana",
    "Emerson", "Finley", "Hayden", "Jesse", "Kelly", "Lee", "Noel", "Parker",
    "Robin", "Skyler", "Terry", "Val", "Whitney", "Kendall",
]

COMPANY_NAMES = [
    "Whitfield & Associates", "Summit Group LLC", "Cascade Office Solutions",
    "Bright Path Consulting", "Metro Legal Services", "Greenleaf Accounting",
    "Pinnacle Design Co.", "Harbor Health Clinic", "Eastside Property Management",
    "Nova Financial Group", "Crestwood Engineering", "Lakeside Marketing",
    "Redwood Consulting", "Sterling Enterprises", "Atlas Logistics",
    "Compass Realty", "Iron Bridge Capital", "Oakmont Partners",
    "Sapphire Technologies", "Westlake Advisory",
]


def _rand_order():
    return f"ORD-{random.randint(1000, 9999)}"


def _rand_product():
    return random.choice(PRODUCTS)


def _rand_products(n=2):
    return random.sample(PRODUCTS, min(n, len(PRODUCTS)))


def _rand_name():
    return random.choice(NAMES)


def _rand_company():
    return random.choice(COMPANY_NAMES)


# ---------------------------------------------------------------------------
# Question / Response templates per category
# ---------------------------------------------------------------------------

def _inventory_questions():
    """Return list of (question, response) tuples for inventory category."""
    templates = [
        (
            "Do you have {product} in stock?",
            "Yes, {product} is currently in stock! Would you like help with anything else?"
        ),
        (
            "I need to check availability on {product}. Do you carry those?",
            "{product} is available. Let me know if you need any other product info!"
        ),
        (
            "Can you tell me if {product} is available right now?",
            "Great news \u2014 {product} is in stock. Anything else I can help with?"
        ),
        (
            "Hey, does OfficeFlow carry {product}?",
            "We sure do! {product} is in our catalog and currently available."
        ),
        (
            "I'm looking for {product}. Are those something you sell?",
            "Absolutely! {product} is one of our products and it's in stock right now."
        ),
        (
            "What's the availability on {product}? We need about 50 units.",
            "{product} is in stock. For a bulk order of 50 units, you can place it through our web portal or contact sales@officeflow.com for assistance."
        ),
        (
            "Is {product} running low? I need to order soon.",
            "{product} is in stock, but I'd recommend ordering soon to make sure you get what you need. You can order through our portal or email sales@officeflow.com."
        ),
        (
            "Hi, I'd like to know if you have {product} and {product2} available.",
            "Both {product} and {product2} are currently in stock! Let me know if you need any other details."
        ),
        (
            "We're restocking our office. Do you have {product} on hand?",
            "Yes, {product} is available! If you're doing a big restock, our sales team at sales@officeflow.com can help with bulk pricing."
        ),
        (
            "Quick question \u2014 is {product} still available or is it sold out?",
            "{product} is still available. Go ahead and grab it through the portal whenever you're ready!"
        ),
        (
            "I placed an order for {product} last week but I might need more. Do you still have them?",
            "We do still have {product} in stock. You can place another order through the web portal anytime."
        ),
        (
            "Can you look up whether {product} is in your inventory?",
            "I just checked and {product} is in stock. Let me know if there's anything else!"
        ),
        (
            "My name is {name} and I need {product} for our office at {company}. Available?",
            "Hi {name}! {product} is in stock and ready to go. You can order through the portal or reach out to sales@officeflow.com."
        ),
        (
            "Do you carry anything like {product}? My office needs some.",
            "We carry {product} and it's currently available. Would you like more details or recommendations for similar items?"
        ),
        (
            "I saw {product} on your website but couldn't tell if it's in stock. Can you confirm?",
            "{product} is confirmed in stock! You should be able to order directly from the site."
        ),
        (
            "What office supply products do you have for organizing files?",
            "We have several filing options in stock, including Manila File Folders (25-pack), Hanging File Folders (25-pack), and Sheet Protectors (50-pack). Let me know which you're interested in!"
        ),
        (
            "Do you have any writing instruments available? Looking for pens and pencils.",
            "Absolutely! We have Blue Ballpoint Pens (12-pack), Black Gel Pens (6-pack), Mechanical Pencils (12-pack), and Highlighters (5-pack) all in stock."
        ),
        (
            "I need desk accessories. What's in stock?",
            "We have several desk accessories available: Desk Organizer Tray, Letter Trays (2-tier), Desk Calendar 2026, and Tape Dispenser with Tape. Let me know what catches your eye!"
        ),
        (
            "Are {product} available? We go through those fast at {company}.",
            "{product} is in stock. If you go through them quickly, you might want to check with sales@officeflow.com about setting up recurring orders."
        ),
        (
            "Hi there, this is {name}. Could you check stock on {product} for me?",
            "Hi {name}! {product} is in stock. Would you like to place an order?"
        ),
        (
            "I need {product} urgently. Please tell me you have them.",
            "Good news \u2014 {product} is in stock! You can place an order right away through the web portal."
        ),
        (
            "We just ran out of {product}. Do you have any?",
            "We do have {product} available! Order through the portal and you'll be restocked in no time."
        ),
        (
            "Can I get a stock check on {product} and {product2}?",
            "Both {product} and {product2} are currently in stock. Let me know if you'd like to order!"
        ),
        (
            "How much {product} do you have available? We need a large quantity.",
            "{product} is currently in stock. For large quantity orders, I'd recommend contacting our sales team at sales@officeflow.com for the best pricing."
        ),
        (
            "I'm with {company}. We need {product} \u2014 is that something you stock?",
            "Hi! We definitely stock {product} and it's available right now. Your team at {company} can order through the portal or email sales@officeflow.com."
        ),
        (
            "Are there any {product} left? I've been meaning to order.",
            "Yes, {product} is still in stock! Go ahead and place your order whenever you're ready."
        ),
        (
            "Could you check if {product} is in your warehouse?",
            "Just checked \u2014 {product} is in stock. You're good to order!"
        ),
        (
            "What paper products do you currently have available?",
            "We have several paper products in stock: Copy Paper 500 Sheets, Legal Pads (6-pack), Spiral Notebooks (3-pack), and Index Cards (3x5, 100-pack). Want details on any of these?"
        ),
        (
            "Looking for sticky notes and similar products. What do you have?",
            "We've got Sticky Notes (4-pack) and Post-it Flags (4 colors) in stock right now. Both are great for organization!"
        ),
        (
            "Hi, my name's {name} from {company}. Just checking \u2014 do you have {product}?",
            "Hi {name}! Yes, {product} is currently available. Let me know if you need anything else for {company}!"
        ),
        (
            "We use {product} a lot. Can you confirm they're in stock before I order?",
            "Confirmed \u2014 {product} is in stock. Go ahead and place your order!"
        ),
        (
            "I'm browsing your catalog and wondering about availability for {product}.",
            "{product} is in stock and ready to ship. Let me know if you have questions about any other items!"
        ),
        (
            "Our supply closet is empty. Do you have {product}, {product2}, and {product3}?",
            "Great news \u2014 {product}, {product2}, and {product3} are all currently in stock! Perfect for a full restock."
        ),
        (
            "Is there currently limited stock on {product}?",
            "{product} is in stock, though inventory levels can change. I'd recommend ordering soon if you need it!"
        ),
        (
            "Hey, can you check whether you have {product} available for shipping to {company}?",
            "{product} is in stock and we can ship to {company}'s address. Just place the order through our portal!"
        ),
        (
            "I need to order {product}. What's the stock situation?",
            "{product} is available. You can go ahead and order through the web portal at your convenience."
        ),
        (
            "Can I get {product} shipped to our office this week?",
            "{product} is in stock! If you order before 2:00 PM EST, it ships same day. Standard delivery is 3-5 business days."
        ),
        (
            "Do you currently stock {product}? I can't find it on the website.",
            "Yes, we do carry {product} and it's in stock! If you're having trouble finding it on the site, try searching by the product name or contact support@officeflow.com for help."
        ),
        (
            "My assistant asked me to check on {product} availability. Are they in stock?",
            "{product} is in stock! Let your assistant know they can order through the portal anytime."
        ),
        (
            "I'm {name} and I need to restock our breakroom. Do you carry {product}?",
            "Hi {name}! We do carry {product} and it's currently available. Let me know if you need anything else!"
        ),
    ]
    pairs = []
    for t in templates:
        p1, p2 = _rand_products(2)
        p3 = _rand_product()
        name = _rand_name()
        company = _rand_company()
        q = t[0].format(product=p1, product2=p2, product3=p3, name=name, company=company)
        a = t[1].format(product=p1, product2=p2, product3=p3, name=name, company=company)
        pairs.append((q, a))
    return pairs


def _policy_questions():
    """Return list of (question, response) tuples for policy category."""
    templates = [
        (
            "What's your return policy?",
            "Items can be returned within 30 days of delivery. You'll need an RMA number from our Returns Department \u2014 contact them at returns@officeflow.com or 1-800-OFFICE-1 ext. 3. Defective items can be returned anytime."
        ),
        (
            "How do I return a defective item?",
            "For defective items, email returns@officeflow.com with your order number, a description of the defect, and photos if possible. They'll issue an RMA and a prepaid return label at no cost."
        ),
        (
            "What are your shipping options and costs?",
            "We offer Standard ($8.95, 3-5 days), Expedited ($15.95, 2-3 days), Express ($24.95, 1-2 days), and Overnight ($39.95, next day). Standard shipping is free on orders over $100!"
        ),
        (
            "Do you offer free shipping?",
            "Yes! Standard shipping is free on orders of $100 or more. Expedited shipping is free on orders of $250+."
        ),
        (
            "How long does standard shipping take?",
            "Standard shipping takes 3-5 business days. Orders placed before 2:00 PM EST ship the same day."
        ),
        (
            "Can I ship to Canada?",
            "Absolutely! We ship to all Canadian provinces and territories. Duties and taxes may apply, and you should expect an extra 1-2 days for customs."
        ),
        (
            "What are your business hours?",
            "Our main phone line is open Monday-Friday 7:00 AM - 7:00 PM EST, and Saturday 9:00 AM - 2:00 PM EST. We're closed on Sundays."
        ),
        (
            "How do I place an order?",
            "You can place orders through our web portal at www.officeflow.com or by contacting our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2."
        ),
        (
            "What's the return window? I got something two weeks ago.",
            "You're within the return window! Items can be returned within 30 days of delivery. Contact returns@officeflow.com with your order number to get an RMA."
        ),
        (
            "I need to process a return on order {order}. How do I do that?",
            "To start a return on order {order}, email returns@officeflow.com with your order number and reason for the return. They'll issue an RMA within 4 business hours."
        ),
        (
            "How long do refunds take?",
            "Refunds are processed within 5-7 business days after we receive your return. The credit goes back to your original payment method."
        ),
        (
            "Do you ship internationally?",
            "We ship to the US and Canada as standard. For international orders outside those areas, contact sales@officeflow.com for a quote \u2014 it's available for large orders."
        ),
        (
            "What's the cutoff time for same-day shipping?",
            "Orders placed before 2:00 PM EST ship the same business day. After that, they ship the next business day."
        ),
        (
            "Can I pick up an order instead of having it shipped?",
            "Yes! We offer Will Call Pickup at our distribution centers in Portland, Chicago, Atlanta, and Toronto. Select it at checkout and you'll be notified when it's ready \u2014 usually 2-4 hours."
        ),
        (
            "Where are your distribution centers located?",
            "We have four distribution centers: Portland, OR (headquarters), Schaumburg, IL (Chicago area), Norcross, GA (Atlanta area), and Mississauga, ON (Toronto area)."
        ),
        (
            "Do you offer expedited or overnight shipping?",
            "Yes! Expedited is $15.95 (2-3 days), Express is $24.95 (1-2 days), and Overnight is $39.95 (next business day). Express and Overnight require ordering by 2:00 PM and 12:00 PM EST respectively."
        ),
        (
            "What happens if my package arrives damaged?",
            "Photograph the damage and contact us within 48 hours at fulfillment@officeflow.com. We'll arrange a replacement or refund immediately \u2014 you won't need to return the damaged item first."
        ),
        (
            "Can I exchange an item instead of returning it?",
            "Absolutely! Exchanges follow the same process as returns \u2014 you'll need an RMA from returns@officeflow.com. Price differences may apply if you're swapping for a different item."
        ),
        (
            "How do I track my order?",
            "You'll get a tracking number by email when your order ships. You can check status anytime at www.officeflow.com/track, or contact fulfillment@officeflow.com for help."
        ),
        (
            "What payment methods do you accept?",
            "For payment and billing questions, I'd direct you to our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They handle all payment method details."
        ),
        (
            "I need to update my billing address. How?",
            "Account changes like billing address updates go through our Accounts team. Email accounts@officeflow.com or call 1-800-OFFICE-1 ext. 4."
        ),
        (
            "Are you closed on holidays?",
            "We're closed on New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, and Christmas. We have limited hours on the day before Thanksgiving, Christmas Eve, and New Year's Eve (until 2 PM EST)."
        ),
        (
            "My name is {name} from {company}. What's your shipping policy for business accounts?",
            "Hi {name}! Business account customers at {company} may have access to custom shipping rates and dedicated delivery routes in major metro areas. Contact your account manager for specifics!"
        ),
        (
            "How do I set up a business account?",
            "To set up a business account, reach out to our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They'll get you set up."
        ),
        (
            "What's the policy on returning opened items?",
            "Most opened items in original packaging can be returned within 30 days. However, opened paper reams cannot be returned due to hygiene standards, and custom-printed or Final Sale items are ineligible."
        ),
        (
            "I received the wrong items in my order. What should I do?",
            "I'm sorry about that! Contact fulfillment@officeflow.com with your order number and details about what you received vs. what you ordered. They'll ship the correct items same or next business day and provide a return label."
        ),
        (
            "Do you offer bulk pricing or discounts for large orders?",
            "For bulk pricing, contact our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2. They can provide quotes for large orders."
        ),
        (
            "Can I change my shipping address after placing an order?",
            "If the order hasn't shipped yet, contact the sales team immediately \u2014 changes are free within 2 hours of placement. After shipping, the fulfillment team may be able to reroute, though a $10-15 fee applies."
        ),
        (
            "Is there a way to get Saturday delivery?",
            "Our distribution centers are closed on weekends, so Saturday delivery isn't available. Express and Overnight shipping are available Monday-Thursday only."
        ),
        (
            "How do I contact the returns department?",
            "You can reach our Returns Department at returns@officeflow.com or 1-800-OFFICE-1 ext. 3. They're available Monday-Friday, 8:00 AM - 6:00 PM EST, and respond within 4 business hours."
        ),
        (
            "I have a question about my invoice. Who do I talk to?",
            "For invoice and billing questions, contact our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They're available Monday-Friday, 9:00 AM - 5:00 PM EST."
        ),
        (
            "Is return shipping free?",
            "Return shipping is free if the item is defective or we shipped the wrong item. Otherwise, return shipping costs are the customer's responsibility."
        ),
        (
            "What's the number I can call for help?",
            "Our main number is 1-800-OFFICE-1. For specific departments: Customer Service ext. 1, Sales ext. 2, Returns ext. 3, Accounts ext. 4, Fulfillment ext. 5, Tech Support ext. 6."
        ),
        (
            "How do I get an RMA number for a return?",
            "Contact our Returns Department at returns@officeflow.com or 1-800-OFFICE-1 ext. 3 with your order number and reason for the return. They'll issue an RMA within 4 business hours."
        ),
        (
            "Do you ship to PO boxes?",
            "Yes, we ship to PO Boxes for most items using standard shipping. Some restrictions apply for large or hazardous items."
        ),
        (
            "Where can I find your company contact information?",
            "Our main number is 1-800-OFFICE-1. Our headquarters is at 1234 Commerce Way, Portland, OR 97220. You can also email info@officeflow.com or visit www.officeflow.com."
        ),
        (
            "What do I do if my package says delivered but I didn't get it?",
            "Contact us at fulfillment@officeflow.com. We'll file a carrier claim and send a replacement. The claim process typically takes 3-5 business days."
        ),
        (
            "Can you tell me about your exchange policy?",
            "We're happy to do exchanges! Same process as returns \u2014 contact returns@officeflow.com for an RMA. Price differences may apply. Exchange items ship once we receive and inspect the return."
        ),
        (
            "Hi, this is {name}. I'm trying to understand your return policy for defective items.",
            "Hi {name}! Defective items can be returned at any time, even after the 30-day window. Email returns@officeflow.com with photos of the defect. They'll send a prepaid return label, and return shipping is on us."
        ),
        (
            "What are the shipping restrictions?",
            "Hazardous materials (certain markers, adhesives) must ship ground only. Oversized items like furniture need freight shipping. Items over 50 lbs may incur freight charges. No aerosols or flammables on international shipments."
        ),
    ]
    pairs = []
    for t in templates:
        order = _rand_order()
        name = _rand_name()
        company = _rand_company()
        q = t[0].format(order=order, name=name, company=company)
        a = t[1].format(order=order, name=name, company=company)
        pairs.append((q, a))
    return pairs


def _out_of_scope_questions():
    """Return list of (question, response) tuples for out_of_scope category."""
    templates = [
        (
            "Can you help me write a cover letter?",
            "I appreciate you reaching out, but I'm only able to help with OfficeFlow product and service questions. For cover letter help, you might try a career services site. Is there anything office-supply related I can assist with?"
        ),
        (
            "What's the weather like in Portland today?",
            "I wish I could help with that, but I'm limited to OfficeFlow-related questions! For weather, try your favorite weather app. Anything else I can help with regarding our products or services?"
        ),
        (
            "Can you recommend a good restaurant near your Portland office?",
            "That's a fun question, but unfortunately I can only help with OfficeFlow product and service inquiries. Yelp or Google Maps would be great for restaurant recs! Anything supply-related I can help with?"
        ),
        (
            "I need help with my taxes. Can you help?",
            "I'm not able to help with taxes, but I'd recommend a CPA or tax preparation service. I'm here if you need anything related to office supplies or our services!"
        ),
        (
            "Do you sell office furniture?",
            "We focus on office supplies, paper products, writing instruments, and desk accessories. We don't currently carry furniture. For specific product questions, I'm happy to help!"
        ),
        (
            "Can you fix my computer? It keeps crashing.",
            "I'm sorry about the tech troubles, but I can only help with OfficeFlow products and services. For computer issues, I'd suggest contacting your IT department or a local tech support service."
        ),
        (
            "What's the stock price of OfficeFlow?",
            "I'm not able to provide financial or stock information. For investor relations, you could check our corporate website or contact corporate@officeflow.com. Anything product-related I can help with?"
        ),
        (
            "Can you translate this document for me?",
            "Translation is outside my area, I'm afraid. I'm here for OfficeFlow product and service questions. For translation, try Google Translate or a professional translation service!"
        ),
        (
            "I want to apply for a job at OfficeFlow. How do I do that?",
            "Thanks for your interest in working with us! Job applications aren't something I handle, though. Check our website for a careers page, or email corporate@officeflow.com. Can I help with anything supply-related?"
        ),
        (
            "Can you book a meeting room for me?",
            "I'm not able to book meeting rooms \u2014 I'm specialized in OfficeFlow product and service support. You'd want to check with your office administrator for room bookings. Need anything else?"
        ),
        (
            "What's the best laptop for office work?",
            "Great question, but electronics and laptops are outside our product range. We focus on office supplies and paper products. For laptop recommendations, I'd suggest a tech review site. Anything else I can help with?"
        ),
        (
            "Can you help me set up my email?",
            "Email setup is outside my expertise \u2014 I'm here for OfficeFlow product and service questions. Your IT department or email provider's support would be the best bet!"
        ),
        (
            "Tell me a joke.",
            "Ha! I appreciate the request, but I'm best at helping with office supply questions. If you need any product info or have service questions, I'm your person!"
        ),
        (
            "Can you order me a pizza?",
            "I wish I could! But I'm limited to OfficeFlow products and services. For pizza, try your favorite delivery app. Need any staplers or sticky notes instead?"
        ),
        (
            "What's the capital of France?",
            "That would be Paris! But my real expertise is OfficeFlow products and services. Is there anything supply-related I can help with?"
        ),
        (
            "Can you help me plan my vacation?",
            "Vacation planning sounds fun, but it's outside my area. I'm here for OfficeFlow product and service support. Let me know if you need anything for the office!"
        ),
        (
            "Do you sell printers or toner cartridges?",
            "We don't currently carry printers or toner cartridges \u2014 our focus is on office supplies, paper products, and desk accessories. Is there anything else from our catalog I can help with?"
        ),
        (
            "Can you help me with my car insurance claim?",
            "I'm sorry, that's well outside my area! I can only help with OfficeFlow products and services. For insurance, you'd want to contact your insurance provider directly."
        ),
        (
            "I need advice on investing in the stock market.",
            "Investment advice isn't something I can provide \u2014 I'm focused on OfficeFlow product support. A financial advisor would be the right person to talk to. Need any office supplies?"
        ),
        (
            "Can you write me a Python script?",
            "I appreciate the ask, but coding is outside my scope! I'm here to help with OfficeFlow products and services. For programming help, try Stack Overflow or a developer community."
        ),
        (
            "What's the best way to lose weight?",
            "Health and fitness advice is outside my wheelhouse \u2014 I'd recommend talking to a healthcare professional. I'm great at office supply questions though! Anything I can help with?"
        ),
        (
            "Can you order me an Uber?",
            "I can't book rides, but I can help with office supplies! Is there anything OfficeFlow-related you need?"
        ),
        (
            "Do you sell coffee or snacks for the office?",
            "We don't carry food or beverages \u2014 our catalog focuses on office supplies, paper products, and desk accessories. Is there something in that range I can help with?"
        ),
        (
            "Can you summarize this article for me?",
            "Article summarization is outside my scope. I'm here for OfficeFlow product and service support. Feel free to ask me about anything in our catalog!"
        ),
        (
            "What's the best streaming service right now?",
            "Entertainment recommendations are outside my area! I'm focused on OfficeFlow products and services. Let me know if you need anything for the office."
        ),
        (
            "Can you help me move to a new apartment?",
            "I can't help with moving, but if you need packing tape or labels for the move, we've got you covered! Anything office-supply related I can assist with?"
        ),
        (
            "Do you sell cleaning supplies?",
            "Cleaning supplies aren't in our current catalog \u2014 we specialize in office supplies, paper products, writing instruments, and desk accessories. Need anything from those categories?"
        ),
        (
            "Can you fix my printer?",
            "Printer repair is outside my scope \u2014 I'm here for OfficeFlow product and service questions. For printer issues, I'd suggest contacting the manufacturer's support line."
        ),
        (
            "I need legal advice about a contract. Can you help?",
            "Legal advice is something I can't provide. I'd recommend consulting with an attorney. I'm here for OfficeFlow product and service questions \u2014 need anything from our catalog?"
        ),
        (
            "What time does the post office close?",
            "I don't have post office hours, but you can check usps.com for that. I'm here to help with OfficeFlow products and services \u2014 anything I can assist with?"
        ),
        (
            "My name is {name}. Can you help me find a new apartment?",
            "Hi {name}! I appreciate you reaching out, but apartment hunting is outside my area. I'm here for OfficeFlow product and service support. Need any office supplies?"
        ),
        (
            "Is OfficeFlow hiring right now?",
            "For job openings, I'd recommend checking our website or contacting corporate@officeflow.com. I handle product and service support. Anything supply-related I can help with?"
        ),
        (
            "Can you teach me how to use Excel?",
            "Excel training is outside my expertise \u2014 there are great tutorials on YouTube and LinkedIn Learning. I'm here for OfficeFlow product questions though!"
        ),
        (
            "I need to send flowers to my mom. Can you help?",
            "That's sweet! But flower delivery is outside my scope. I'm here for OfficeFlow office supplies and services. Let me know if you need anything for the office!"
        ),
        (
            "Do you sell electronics or computer accessories?",
            "We don't carry electronics or computer accessories. Our catalog focuses on office supplies, paper products, writing instruments, and organizational tools. Can I help you find something in those categories?"
        ),
        (
            "Can you check the flight status for my upcoming trip?",
            "Flight tracking is outside what I can do \u2014 I'd recommend checking your airline's app or website. I'm here for OfficeFlow product and service questions!"
        ),
        (
            "What's the meaning of life?",
            "That's a deep one! I'll leave that to the philosophers. I'm here to help with OfficeFlow products and services. Anything supply-related on your mind?"
        ),
        (
            "I need to dispute a charge on my credit card. Can you help?",
            "Credit card disputes go through your card issuer, not through us. If the charge is from OfficeFlow and you believe it's incorrect, contact accounts@officeflow.com."
        ),
        (
            "Can you help with team building activities?",
            "Team building is outside my area, but sounds fun! I'm here for OfficeFlow product and service support. Need supplies for a team event?"
        ),
        (
            "Do you sell ergonomic chairs or standing desks?",
            "We don't currently carry furniture like chairs or desks. We focus on office supplies, paper products, and desk accessories. Anything from our catalog I can help with?"
        ),
    ]
    pairs = []
    for t in templates:
        name = _rand_name()
        q = t[0].format(name=name)
        a = t[1].format(name=name)
        pairs.append((q, a))
    return pairs


def _both_questions():
    """Return list of (question, response) tuples for both (inventory+policy) category."""
    templates = [
        (
            "Do you have {product} in stock, and what's your return policy if they don't work out?",
            "{product} is currently in stock! As for returns, items can be returned within 30 days with an RMA from returns@officeflow.com. Defective items can be returned anytime."
        ),
        (
            "I need {product} \u2014 are they available? Also, how much is shipping?",
            "{product} is in stock! Shipping is $8.95 standard (3-5 days), free on orders over $100. Expedited and overnight options are also available."
        ),
        (
            "Can you check if you have {product} and tell me how to place an order?",
            "{product} is available! To order, use our web portal at www.officeflow.com or email sales@officeflow.com."
        ),
        (
            "I'm looking at {product} and {product2}. Are both available, and do you ship to Canada?",
            "Both {product} and {product2} are in stock! And yes, we ship to all Canadian provinces. Expect 1-2 extra days for customs, and duties/taxes may apply."
        ),
        (
            "My name is {name} from {company}. I need {product} \u2014 is it in stock? And can I return it if my team doesn't like it?",
            "Hi {name}! {product} is in stock. If your team isn't happy, you can return it within 30 days \u2014 just contact returns@officeflow.com for an RMA."
        ),
        (
            "Do you carry {product}? And what's the quickest shipping option?",
            "{product} is in stock! Our fastest option is Overnight Shipping at $39.95 \u2014 order by 12:00 PM EST for next-business-day delivery."
        ),
        (
            "I need to know if {product} is available and whether I can get free shipping.",
            "{product} is available! Standard shipping is free on orders of $100 or more."
        ),
        (
            "Are {product} in stock? Also, I got a damaged item in my last order \u2014 what do I do?",
            "{product} is in stock. For the damaged item, photograph it and email fulfillment@officeflow.com within 48 hours. They'll arrange a replacement or refund immediately."
        ),
        (
            "I want to order {product} and also need to process a return on order {order}.",
            "{product} is in stock and ready to order through the portal. For the return on {order}, contact returns@officeflow.com with your order number and reason \u2014 they'll issue an RMA within 4 business hours."
        ),
        (
            "Do you have {product}? And where's your nearest warehouse for pickup?",
            "{product} is in stock! Our distribution centers are in Portland OR, Schaumburg IL (Chicago), Norcross GA (Atlanta), and Mississauga ON (Toronto). Select Will Call Pickup at checkout."
        ),
        (
            "Is {product} available? I also want to know about your bulk pricing.",
            "{product} is in stock! For bulk pricing, contact our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2 \u2014 they can get you a quote."
        ),
        (
            "I need {product} urgently \u2014 do you have it? What's the fastest I can get it?",
            "{product} is in stock! With Overnight Shipping ($39.95), order by 12:00 PM EST and you'll have it the next business day."
        ),
        (
            "Check availability on {product} please, and let me know your business hours.",
            "{product} is available! Our phone lines are open Monday-Friday 7:00 AM - 7:00 PM EST, Saturday 9:00 AM - 2:00 PM EST. Closed Sundays."
        ),
        (
            "I'm with {company}. Need to check stock on {product} and understand your shipping costs.",
            "Hi! {product} is in stock. Standard shipping is $8.95 (free over $100), Expedited is $15.95, Express is $24.95, and Overnight is $39.95."
        ),
        (
            "Do you have {product}? And if I order today, when would it arrive?",
            "{product} is in stock! If you order before 2:00 PM EST today, it ships same day. Standard delivery is 3-5 business days."
        ),
        (
            "I need {product} and {product2}. Are they available? Also, what's the return process?",
            "Both {product} and {product2} are in stock! For returns, contact returns@officeflow.com with your order number. They'll issue an RMA within 4 business hours. Items must be returned within 30 days."
        ),
        (
            "Can I get {product} with expedited shipping? Is it in stock?",
            "{product} is in stock! Expedited shipping is $15.95 and takes 2-3 business days. Order before 2:00 PM EST for same-day processing."
        ),
        (
            "Hi, I'm {name}. I need {product} shipped to {company}. What are my shipping options?",
            "Hi {name}! {product} is in stock. For {company}, you can choose Standard ($8.95, 3-5 days), Expedited ($15.95, 2-3 days), Express ($24.95, 1-2 days), or Overnight ($39.95, next day)."
        ),
        (
            "Are {product} available? And is there a minimum order for free shipping?",
            "{product} is available! Free standard shipping kicks in at $100 or more. Free expedited shipping at $250+."
        ),
        (
            "I'm interested in {product}. Do you have them? Also, do you offer Will Call pickup?",
            "{product} is in stock! Yes, Will Call Pickup is available at all four of our distribution centers \u2014 Portland, Chicago, Atlanta, and Toronto. Select it at checkout."
        ),
        (
            "Can you check {product} availability and tell me about business account benefits?",
            "{product} is in stock! Business accounts may offer custom shipping rates, dedicated delivery routes, and customized return policies. Contact accounts@officeflow.com to learn more."
        ),
        (
            "Do you have {product} in stock? I also want to exchange something from order {order}.",
            "{product} is in stock! For the exchange on {order}, contact returns@officeflow.com \u2014 you'll need an RMA. Price differences may apply."
        ),
        (
            "I need {product} and want to know if there's a cutoff for same-day shipping.",
            "{product} is available! Orders placed before 2:00 PM EST ship same business day."
        ),
        (
            "Are {product} available? Also, what holidays are you closed?",
            "{product} is in stock! We're closed on New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, and Christmas. Limited hours on the eves."
        ),
        (
            "Quick questions \u2014 is {product} in stock and can I track my order online?",
            "{product} is in stock! Yes, you can track orders at www.officeflow.com/track using your tracking number, which is emailed when the order ships."
        ),
        (
            "Do you carry {product}? And if something's wrong with my order, who do I call?",
            "{product} is available! For order issues, contact fulfillment@officeflow.com or 1-800-OFFICE-1 ext. 5. For returns, it's returns@officeflow.com or ext. 3."
        ),
        (
            "I want {product}. Is it available? Can I change the shipping address after I order?",
            "{product} is in stock! You can change the shipping address for free within 2 hours of placing the order. After that, or once shipped, a $10-15 rerouting fee may apply."
        ),
        (
            "This is {name} at {company}. Are {product} in stock? We might need to set up a recurring order.",
            "Hi {name}! {product} is in stock. For recurring orders at {company}, contact sales@officeflow.com \u2014 they can set up a schedule that works for your team."
        ),
        (
            "Check stock on {product}. Also, what if the product arrives damaged?",
            "{product} is in stock! If it arrives damaged, photograph it and email fulfillment@officeflow.com within 48 hours. They'll send a replacement immediately."
        ),
        (
            "Hi, do you have {product}? Also what's your phone number for customer service?",
            "{product} is available! Our customer service number is 1-800-OFFICE-1 (ext. 1), available Monday-Friday 7 AM - 7 PM EST and Saturday 9 AM - 2 PM EST."
        ),
        (
            "I'm looking at ordering {product}. Available? And do you have Spanish language support?",
            "{product} is in stock! Yes, we offer English and Spanish support for US customers. Just request it when you call."
        ),
        (
            "Can you confirm {product} is in stock? I also need to know about your return shipping costs.",
            "{product} is confirmed in stock. Return shipping is the customer's responsibility unless the item is defective or we shipped the wrong thing \u2014 in those cases, it's free."
        ),
        (
            "Are {product} available? And how long is the RMA valid once issued?",
            "{product} is available! Once issued, an RMA is valid for 14 days. Contact returns@officeflow.com to get one."
        ),
        (
            "I need {product} for {company}. Also, do you ship to APO/FPO addresses?",
            "{product} is in stock! We do ship to APO/FPO addresses, but only via standard shipping."
        ),
        (
            "Is {product} in stock? And what are your distribution center hours?",
            "{product} is in stock! Our distribution centers are open Monday-Friday 7:00 AM - 6:00 PM local time. Closed weekends."
        ),
        (
            "Do you have {product}? Plus, I heard there's an emergency contact for after-hours \u2014 what is it?",
            "{product} is available! For urgent after-hours issues, email urgent@officeflow.com \u2014 they respond within 2 hours for critical matters."
        ),
        (
            "I need {product}. Available? And can I get an invoice in large print?",
            "{product} is in stock! Yes, large print invoices are available upon request. Email accessibility@officeflow.com to set that up."
        ),
        (
            "Are {product} in stock? My last order had an issue and I need info on returns too.",
            "{product} is in stock! For the return, email returns@officeflow.com with your order number and issue details. They respond within 4 business hours."
        ),
        (
            "Check if {product} is available. I also need to know \u2014 are opened items returnable?",
            "{product} is available! Most opened items in original packaging can be returned within 30 days. Exceptions: opened paper reams, custom-printed items, and Final Sale items."
        ),
        (
            "Hi, this is {name}. Is {product} in stock? Also, I want to know about your satisfaction guarantee.",
            "Hi {name}! {product} is in stock. We want you to be completely satisfied \u2014 items can be returned within 30 days, and defective items can be returned anytime. Contact returns@officeflow.com for an RMA."
        ),
    ]
    pairs = []
    for t in templates:
        p1, p2 = _rand_products(2)
        name = _rand_name()
        company = _rand_company()
        order = _rand_order()
        q = t[0].format(product=p1, product2=p2, name=name, company=company, order=order)
        a = t[1].format(product=p1, product2=p2, name=name, company=company, order=order)
        pairs.append((q, a))
    return pairs


def _website_troubleshooting_questions():
    """Return list of (question, response) tuples for website_troubleshooting category."""
    templates = [
        (
            "I can't log into my account on your website. Can you help?",
            "I'm sorry about the trouble! For website login issues, our Technical Support team is the best resource. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your website keeps crashing when I try to place an order.",
            "I'm sorry to hear that! Please reach out to our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can troubleshoot the issue."
        ),
        (
            "I'm getting an error message when I try to checkout on your site.",
            "That's frustrating \u2014 I'm sorry! Our Tech Support team handles website errors. Contact support@officeflow.com or call 1-800-OFFICE-1 ext. 6 for help."
        ),
        (
            "The search function on your website isn't working for me.",
            "Sorry about that! Our Technical Support team can look into the search issue. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I forgot my password and the reset link isn't coming through.",
            "I'm sorry about the password trouble! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can help reset your access."
        ),
        (
            "Your website is really slow today. Is something wrong?",
            "I apologize for the slow experience! Our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 can look into performance issues."
        ),
        (
            "I can't find the order history page on your portal.",
            "For help navigating the web portal, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6. They're available Mon-Fri 8 AM - 8 PM EST."
        ),
        (
            "The payment page won't load when I try to complete my order.",
            "I'm sorry about that! Payment page issues need our Tech Support team. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I keep getting logged out of my account every few minutes.",
            "That sounds really frustrating! Our Technical Support team can investigate the session issue. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your product images aren't loading on the website.",
            "Sorry about that! For display issues like missing images, contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I can't download my invoice from the portal.",
            "I'm sorry for the inconvenience! For invoice download issues, our Technical Support team can help. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "The mobile version of your website is broken \u2014 buttons don't work.",
            "I apologize for the mobile issues! Please let our Tech Support team know at support@officeflow.com or 1-800-OFFICE-1 ext. 6 so they can fix it."
        ),
        (
            "I'm trying to update my shipping address on my account but the save button doesn't work.",
            "For account page functionality issues, our Technical Support team is the right contact. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm getting a 404 error when I click on a product link.",
            "Sorry about the broken link! Our Tech Support team can investigate. Contact support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your website says my cart is empty but I just added items.",
            "That's odd \u2014 I'm sorry! Cart issues are best handled by our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I can't access the tracking page for my order on your site.",
            "I'm sorry about that! For tracking page issues, contact our Tech Support team at support@officeflow.com. You can also try tracking at www.officeflow.com/track directly."
        ),
        (
            "The promo code field isn't appearing at checkout.",
            "Sorry about that! Contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 about the missing promo code field."
        ),
        (
            "I got an error saying 'session expired' but I just logged in.",
            "That's frustrating! Session expiry issues need our Tech Support team. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your website won't let me create a new account.",
            "I'm sorry about the account creation issue! Our Technical Support team can help at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm having trouble with the filters on your product pages.",
            "Sorry about the filter issues! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can look into it."
        ),
        (
            "My name is {name} and I can't access my account portal at all.",
            "Hi {name}, I'm sorry to hear that! For portal access issues, please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm at {company} and multiple people here can't log in to the OfficeFlow portal.",
            "I'm sorry about the widespread issue at {company}! Please have someone contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 it might be an account-level issue."
        ),
        (
            "The website is showing prices from last year. Is that a bug?",
            "That does sound like a display issue! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 to report the pricing display problem."
        ),
        (
            "I'm unable to add items to my wishlist on your website.",
            "Sorry about the wishlist trouble! Our Technical Support team handles site functionality issues. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your site keeps redirecting me to the homepage when I try to view my orders.",
            "That sounds like a bug \u2014 I'm sorry! Please report it to our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I can't upload a PO document through your portal.",
            "For issues with uploading documents, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "The two-factor authentication code isn't being sent to my phone.",
            "I'm sorry about the 2FA trouble! Our Tech Support team can help resolve this at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm getting a 'server error' page every time I try to checkout.",
            "I apologize for the server errors! Please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 to report the checkout issue."
        ),
        (
            "Your website doesn't work properly on Firefox. Works fine on Chrome though.",
            "Thanks for reporting the browser compatibility issue! Please let our Tech Support team know at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm trying to apply a coupon code but the site says it's invalid even though it shouldn't be expired.",
            "Sorry about that! For coupon code issues, contact our Tech Support team at support@officeflow.com. If it's a sales/pricing issue, you could also try sales@officeflow.com."
        ),
        (
            "The notifications from your website are not showing up properly.",
            "For notification issues, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I clicked 'forgot password' but the email never arrives.",
            "I'm sorry about that! Check your spam folder first, and if it's still not there, contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "My account settings page is blank \u2014 nothing loads.",
            "That sounds like a display issue. Our Technical Support team can help at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm having issues with the live chat feature on your website.",
            "I'm sorry the live chat isn't working! Please contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 for help."
        ),
        (
            "This is {name} from {company}. Your portal keeps timing out when I load our order history.",
            "Hi {name}, I apologize for the timeout issue! Please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can investigate."
        ),
        (
            "I can see my old orders but none of the recent ones on the portal.",
            "That's odd! For missing order data in the portal, reach out to our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "Your website's search bar returns no results for anything I type.",
            "I'm sorry about the search issue! Contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "I'm locked out of my account after too many failed login attempts.",
            "Sorry about the lockout! Our Tech Support team can unlock your account. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
        (
            "The website is showing my address as somewhere I've never lived.",
            "That's concerning! Please contact our Technical Support team at support@officeflow.com and our Accounts team at accounts@officeflow.com to review and correct your account info."
        ),
        (
            "I tried to reorder from my order history but the button does nothing.",
            "Sorry about the reorder button issue! Our Technical Support team can troubleshoot that at support@officeflow.com or 1-800-OFFICE-1 ext. 6."
        ),
    ]
    pairs = []
    for t in templates:
        name = _rand_name()
        company = _rand_company()
        q = t[0].format(name=name, company=company)
        a = t[1].format(name=name, company=company)
        pairs.append((q, a))
    return pairs


# ---------------------------------------------------------------------------
# Trace generation
# ---------------------------------------------------------------------------

RUNTIME_BLOCK = {
    "langchain_core_version": "1.2.10",
    "langchain_version": "1.2.10",
    "library": "langsmith",
    "platform": "macOS-15.7.3-arm64-arm-64bit",
    "py_implementation": "CPython",
    "runtime": "python",
    "runtime_version": "3.12.0",
    "sdk": "langsmith-py",
    "sdk_version": "0.7.1",
}


def _ts_to_dotted(dt: datetime) -> str:
    """Convert datetime to dotted_order timestamp format: YYYYMMDDTHHMMSSffffffZ"""
    return dt.strftime("%Y%m%dT%H%M%S%fZ")


def _gen_usage_metadata():
    """Generate realistic usage_metadata for a ChatOpenAI run."""
    input_tokens = random.randint(800, 4000)
    cache_read = random.choice([0, 0, 0, 512, 1024, 1152, 2048])
    reasoning = random.choice([0, 0, 640, 1280, 2560, 2880])
    output_base = random.randint(80, 600)
    output_tokens = output_base + reasoning
    return {
        "input_token_details": {"audio": 0, "cache_read": cache_read},
        "input_tokens": input_tokens,
        "output_token_details": {"audio": 0, "reasoning": reasoning},
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def _make_trace(question: str, response: str, category: str, start_time: datetime):
    """Generate one trace (root chain + child llm) and return list of 2 run dicts."""
    root_id = str(uuid.uuid4())
    child_id = str(uuid.uuid4())

    # Child starts 0.5-3s after root, ends 5-18s after child start
    child_offset = random.uniform(0.5, 3.0)
    child_duration = random.uniform(5.0, 18.0)

    child_start = start_time + timedelta(seconds=child_offset)
    child_end = child_start + timedelta(seconds=child_duration)
    # Root ends shortly after child
    root_end = child_end + timedelta(seconds=random.uniform(0.001, 0.1))

    root_dotted = f"{_ts_to_dotted(start_time)}{root_id}"
    child_dotted = f"{root_dotted}.{_ts_to_dotted(child_start)}{child_id}"

    usage = _gen_usage_metadata()

    # Messages for the conversation (simplified: system + user + assistant)
    messages = [
        {"content": SYSTEM_PROMPT, "role": "system"},
        {"content": question, "role": "user"},
        {"content": response, "role": "assistant"},
    ]

    # Root "Emma" chain run
    root_run = {
        "id": root_id,
        "name": "Emma",
        "run_type": "chain",
        "inputs": {"question": question},
        "outputs": {
            "messages": messages,
            "output": response,
        },
        "start_time": start_time.isoformat(),
        "end_time": root_end.isoformat(),
        "trace_id": root_id,
        "dotted_order": root_dotted,
        "parent_run_id": None,
        "extra": {
            "metadata": {
                "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com",
                "LANGSMITH_PROJECT": "lca-ls-project",
                "LANGSMITH_TRACING": "true",
                "ls_method": "traceable",
                "ls_run_depth": 0,
                "revision_id": "da98358-dirty",
            },
            "runtime": dict(RUNTIME_BLOCK),
        },
        "error": None,
        "tags": [category],
    }

    # ChatOpenAI completion ID
    chatcmpl_id = f"chatcmpl-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=29))}"
    created_ts = int(child_end.replace(tzinfo=timezone.utc).timestamp())

    # Child "ChatOpenAI" llm run
    child_run = {
        "id": child_id,
        "name": "ChatOpenAI",
        "run_type": "llm",
        "inputs": {
            "messages": messages,
            "model": "gpt-5-nano",
            "tool_choice": "auto",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "query_database",
                        "description": "SQL query to get information about our inventory for customers like products, quantities and prices.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "SQL query to execute against the inventory database.",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge_base",
                        "description": "Search for company policies, procedures, and general information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language question or search query about company policies or information",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                },
            ],
        },
        "outputs": {
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "annotations": [],
                        "audio": None,
                        "content": response,
                        "function_call": None,
                        "refusal": None,
                        "role": "assistant",
                        "tool_calls": None,
                    },
                }
            ],
            "created": created_ts,
            "id": chatcmpl_id,
            "model": "gpt-5-nano-2025-08-07",
            "object": "chat.completion",
            "service_tier": "default",
            "system_fingerprint": None,
            "usage_metadata": usage,
        },
        "start_time": child_start.isoformat(),
        "end_time": child_end.isoformat(),
        "trace_id": root_id,
        "dotted_order": child_dotted,
        "parent_run_id": root_id,
        "extra": {
            "metadata": {
                "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com",
                "LANGSMITH_PROJECT": "lca-ls-project",
                "LANGSMITH_TRACING": "true",
                "ls_invocation_params": {},
                "ls_method": "traceable",
                "ls_model_name": "gpt-5-nano",
                "ls_model_type": "chat",
                "ls_provider": "openai",
                "ls_run_depth": 1,
                "revision_id": "da98358-dirty",
                "usage_metadata": usage,
            },
            "runtime": dict(RUNTIME_BLOCK),
        },
        "error": None,
        "tags": [],
    }

    return [root_run, child_run]


def _fill_category(gen_fn, count: int):
    """Generate exactly `count` (question, response) pairs by cycling templates."""
    base_pairs = gen_fn()
    pairs = []
    i = 0
    while len(pairs) < count:
        if i < len(base_pairs):
            pairs.append(base_pairs[i])
        else:
            # Re-generate with fresh random values
            fresh = gen_fn()
            pairs.append(fresh[i % len(fresh)])
        i += 1
    return pairs[:count]


def main():
    import os

    random.seed(42)

    category_generators = {
        "inventory": _inventory_questions,
        "policy": _policy_questions,
        "out_of_scope": _out_of_scope_questions,
        "both": _both_questions,
        "website_troubleshooting": _website_troubleshooting_questions,
    }

    # Collect all (question, response, category) triples
    all_items = []
    for cat in CATEGORIES:
        pairs = _fill_category(category_generators[cat], TRACES_PER_CATEGORY)
        for q, a in pairs:
            all_items.append((q, a, cat))

    # Shuffle to intersperse categories
    random.shuffle(all_items)

    total_traces = len(all_items)
    print(f"Generating {total_traces} traces ({TRACES_PER_CATEGORY} per category)...")

    # Spread across ~2 hours, with random gaps between traces
    base_time = datetime(2026, 2, 15, 19, 0, 0)  # start 2hrs before a reference
    total_window_seconds = 2 * 3600  # 2 hours
    avg_gap = total_window_seconds / total_traces

    all_runs = []
    current_time = base_time
    for i, (question, response, category) in enumerate(all_items):
        runs = _make_trace(question, response, category, current_time)
        all_runs.extend(runs)
        # Random gap to next trace
        gap = random.uniform(avg_gap * 0.3, avg_gap * 1.7)
        current_time += timedelta(seconds=gap)

    print(f"Generated {len(all_runs)} total runs ({total_traces} traces x 2 runs each)")

    # Category counts verification
    cat_counts = {}
    for run in all_runs:
        if run["run_type"] == "chain" and run["name"] == "Emma":
            for tag in run["tags"]:
                cat_counts[tag] = cat_counts.get(tag, 0) + 1
    print("Category breakdown:")
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat}: {count}")

    # Write output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)
    with open(output_path, "w") as f:
        json.dump(all_runs, f, indent=2)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
