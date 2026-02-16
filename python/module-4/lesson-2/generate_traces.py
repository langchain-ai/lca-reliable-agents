"""Generate 1000 synthetic traces with customer sentiment variation over time.

Produces synthetic_traces.json with 1000 traces tagged "angry" or "happy".
Timestamps span the last 2 weeks. The first week is overwhelmingly angry
customers; ~1 week ago sentiment flips to overwhelmingly happy (step function),
simulating a meaningful agent/product change.

Distribution:
  Week 1 (14-7 days ago): ~85% angry, ~15% happy
  Week 2 (7-0 days ago):  ~15% angry, ~85% happy
"""

import json
import random
import uuid
import os
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTAL_TRACES = 1000
OUTPUT_FILE = "synthetic_traces.json"

SYSTEM_PROMPT = (
    "You are Emma, a customer support specialist for OfficeFlow Supply Co., "
    "a paper and office supplies distribution company serving small-to-medium "
    "businesses across North America.\n\nABOUT YOUR ROLE:\nYou're part of the "
    "Customer Experience team and have been with OfficeFlow for 3 years. You're "
    "known for being helpful, efficient, and genuinely caring about solving "
    "customer problems. Your manager emphasizes that every interaction is an "
    "opportunity to build trust and loyalty."
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


def _p():
    return random.choice(PRODUCTS)


def _n():
    return random.choice(NAMES)


def _c():
    return random.choice(COMPANY_NAMES)


def _o():
    return f"ORD-{random.randint(1000, 9999)}"


# ---------------------------------------------------------------------------
# Angry question/response templates
# ---------------------------------------------------------------------------

_ANGRY_TEMPLATES = [
    # Inventory frustration
    (
        "I've been trying to order {product} for THREE days and your website keeps saying it's unavailable. What is going on?!",
        "I'm really sorry about the frustration. Let me check on {product} for you \u2014 it is currently in stock. If the website is giving you trouble, our Tech Support team at support@officeflow.com can help resolve the issue."
    ),
    (
        "This is ridiculous. I ordered {product} last week and it still hasn't shipped. What kind of operation are you running?",
        "I completely understand your frustration, and I apologize for the delay. For order status and tracking, please contact our Fulfillment team at fulfillment@officeflow.com or 1-800-OFFICE-1 ext. 5 \u2014 they can look into this right away."
    ),
    (
        "Why is {product} out of stock AGAIN? This is the third time this month I've tried to order it.",
        "I'm sorry for the repeated inconvenience. Let me check current availability on {product} for you. If it's temporarily out, I can suggest alternatives or have the sales team notify you when it's back."
    ),
    (
        "I need {product} urgently and your site says 'unavailable.' This is completely unacceptable.",
        "I hear you, and I'm sorry for the inconvenience. Let me check on {product} right now. If stock is limited, I can connect you with sales@officeflow.com to explore expedited options."
    ),
    (
        "Seriously? {product} is listed on your site but I can't add it to my cart. Fix this.",
        "That's definitely frustrating \u2014 I apologize. That sounds like a website issue. Please contact our Tech Support team at support@officeflow.com while I confirm availability on {product}."
    ),
    # Policy frustration
    (
        "I've been trying to return order {order} for a WEEK and nobody has responded to my emails. This is terrible customer service.",
        "I sincerely apologize for the lack of response. That's not the experience we want for you. Please try returns@officeflow.com again and I'll flag this internally. You can also call 1-800-OFFICE-1 ext. 3 for immediate help."
    ),
    (
        "Your return policy is absurd. Why do I need an RMA just to send something back? Nobody else makes you jump through these hoops.",
        "I understand the frustration with the extra step. The RMA helps us process your return quickly and accurately. Contact returns@officeflow.com with your order number and they'll issue one within 4 business hours."
    ),
    (
        "I was charged $8.95 for shipping on a $95 order. That's five dollars short of free shipping and you can't waive it? Come on.",
        "I understand that's frustrating when you're so close to the threshold. Unfortunately, I can't adjust shipping charges, but our sales team at sales@officeflow.com may be able to help if you'd like to add an item to qualify."
    ),
    (
        "It's been 10 business days and I still haven't received my refund for order {order}. Where is my money?",
        "I'm sorry about the delay. Refunds typically take 5-7 business days. Since it's been longer, please contact returns@officeflow.com referencing order {order} so they can investigate immediately."
    ),
    (
        "Why can't you just process my return right now? Why do I have to email a different department? This is so inefficient.",
        "I hear you, and I'm sorry for the inconvenience. Returns require approval from our Returns Department to ensure accuracy. Reach them at returns@officeflow.com or 1-800-OFFICE-1 ext. 3 \u2014 they respond within 4 business hours."
    ),
    # Website rage
    (
        "Your website has been broken for DAYS. I can't log in, I can't place orders, I can't do anything. This is costing me money.",
        "I'm really sorry about the website issues. Please contact our Technical Support team immediately at support@officeflow.com or 1-800-OFFICE-1 ext. 6. In the meantime, you can place orders by calling sales at ext. 2."
    ),
    (
        "I just lost my entire cart because your website crashed mid-checkout. I had 15 items in there. Unbelievable.",
        "That's incredibly frustrating and I'm sorry. Please report the crash to support@officeflow.com. If you need to re-place the order urgently, our sales team at sales@officeflow.com can help."
    ),
    (
        "Your portal is the worst I've ever used. Nothing works, pages take forever to load. Get it together.",
        "I apologize for the poor experience. I'll make sure this feedback reaches our team. For immediate help with portal issues, contact support@officeflow.com or 1-800-OFFICE-1 ext. 6."
    ),
    (
        "The password reset doesn't work. I've tried 5 times. I'm about to take my business elsewhere.",
        "I completely understand your frustration, and I don't want to lose you as a customer. Please call our Tech Support at 1-800-OFFICE-1 ext. 6 \u2014 they can reset your access directly."
    ),
    (
        "I'm locked out of my account and nobody in tech support has gotten back to me in 2 days. This is insane.",
        "That wait time is unacceptable and I'm sorry. Please try calling 1-800-OFFICE-1 ext. 6 directly for faster resolution. I'll also flag this delay internally."
    ),
    # General anger
    (
        "I've been a customer for years and this is how you treat me? My order {order} was wrong and nobody seems to care.",
        "I'm truly sorry for the bad experience. Your loyalty means a lot to us. For the incorrect order, please contact fulfillment@officeflow.com with the details \u2014 they'll ship the right items immediately."
    ),
    (
        "This is {name} from {company}. I am DONE dealing with your incompetent support. Order {order} has been a nightmare.",
        "I sincerely apologize, {name}. That's not the standard we hold ourselves to. Let me connect you with the right team to resolve order {order} immediately. What specific issue are you facing?"
    ),
    (
        "I asked for expedited shipping and my order STILL hasn't arrived after 5 days. I want a refund on the shipping cost.",
        "I understand your frustration. Expedited shipping should be 2-3 business days. Please contact fulfillment@officeflow.com with your order number so they can investigate and process a shipping refund if warranted."
    ),
    (
        "You sent me the wrong {product}. I ordered something completely different. This is a waste of my time.",
        "I'm very sorry about the mix-up. Please contact fulfillment@officeflow.com with your order number and what you received vs. what you ordered. They'll ship the correct item same or next business day and send a return label."
    ),
    (
        "Half the {product} I received were damaged. What kind of quality control do you have?",
        "I'm sorry about the damaged items. Please photograph the damage and email returns@officeflow.com with your order number. We'll arrange a replacement and prepaid return label at no cost."
    ),
    (
        "I called three times today and got put on hold for 20+ minutes each time. This is unacceptable.",
        "I'm truly sorry about the long wait times. That's not the experience we want. For faster service, try emailing the specific department directly \u2014 I can point you to the right email if you let me know what you need help with."
    ),
    (
        "Why does it take a WEEK to get a simple order of {product}? Amazon does it in a day.",
        "I understand the comparison. Our standard shipping is 3-5 business days, but we do offer Overnight shipping ($39.95) for next-day delivery if you order by 12 PM EST. I apologize for any delay."
    ),
    (
        "I've been waiting for my RMA for order {order} for over a week. Your returns department is a black hole.",
        "I apologize for the delay \u2014 RMAs should be issued within 4 business hours. Please try contacting returns@officeflow.com again and reference order {order}. You can also call 1-800-OFFICE-1 ext. 3."
    ),
    (
        "Your company has gone downhill. I used to love ordering from OfficeFlow but lately everything is a disaster.",
        "I'm sorry to hear that, and I appreciate your candor. We value your business and want to make things right. What specific issues have you been experiencing? I'll make sure the right people know."
    ),
    (
        "My name is {name}. I need to speak to a manager. Your service has been atrocious on order {order}.",
        "I understand, {name}, and I'm sorry you've had such a bad experience. For managerial escalation, please email support@officeflow.com with your concerns and order {order}. I'll also note this internally."
    ),
    (
        "Do you even HAVE {product} in stock? Your website says one thing and then the cart says another. Make up your mind.",
        "I apologize for the confusion. Let me check \u2014 {product} is in stock. The website inconsistency sounds like a bug; please report it to support@officeflow.com so our tech team can fix it."
    ),
    (
        "I shouldn't have to chase down my own refund. This is YOUR mistake on order {order}, not mine.",
        "You're absolutely right, and I apologize. Please contact returns@officeflow.com referencing order {order}. Since this was our error, return shipping should be covered and the refund expedited."
    ),
    (
        "I placed an order for {product} 2 weeks ago and STILL haven't received it. This is outrageous.",
        "That is far too long and I sincerely apologize. Please contact fulfillment@officeflow.com with your order number immediately. They'll track it down and arrange a resolution."
    ),
    (
        "Every time I call your support line I get a different answer. Nobody knows what they're doing over there.",
        "I'm sorry for the inconsistent information. That's not acceptable. Please email the specific department for your issue so there's a written record and consistent follow-up."
    ),
    (
        "The {product} you sold me is complete garbage. Worst quality I've ever seen. I want my money back.",
        "I'm sorry the product didn't meet your expectations. Please email returns@officeflow.com with your order number and a description of the quality issue. They'll process a return and refund."
    ),
    (
        "I need {product} for a big presentation tomorrow and you're telling me the fastest shipping is overnight for $40? That's highway robbery.",
        "I understand the time pressure and the cost concern. Overnight shipping at $39.95 would get it to you by tomorrow if ordered before 12 PM EST. Alternatively, Will Call Pickup is available at our distribution centers if one is nearby."
    ),
    (
        "This is the LAST time I order from you people. Order {order} was a complete disaster from start to finish.",
        "I'm truly sorry about your experience with order {order}. We don't want to lose you as a customer. Please let me know the specific issues and I'll escalate to the right team to make it right."
    ),
    (
        "I'm furious. I paid for express shipping on order {order} and it came in standard time. Refund my shipping NOW.",
        "I completely understand your frustration. You shouldn't pay for a service you didn't receive. Please contact fulfillment@officeflow.com with order {order} \u2014 they'll investigate and issue a shipping refund."
    ),
    (
        "Nobody told me {product} was backordered when I placed my order. Zero communication from your team.",
        "I apologize for the lack of communication. That should have been flagged at order time. Please contact fulfillment@officeflow.com for an update. I'll note this as feedback for our team."
    ),
    (
        "I'm {name} at {company} and we spend thousands with you every year. Treat us like it. Order {order} has been a mess.",
        "I sincerely apologize, {name}. {company}'s business is important to us. Please let me know the issues with order {order} and I'll make sure it gets priority attention from the right team."
    ),
    (
        "Your shipping is unreliable. Three of my last five orders arrived late. I'm looking at competitors.",
        "I'm sorry about the shipping inconsistency. That's not the standard we aim for. I'll flag this pattern internally. For immediate help with any pending orders, contact fulfillment@officeflow.com."
    ),
    (
        "I got charged twice for order {order}. How does that even happen? Fix it immediately.",
        "I'm very sorry about the double charge. Please contact accounts@officeflow.com or 1-800-OFFICE-1 ext. 4 with order {order} \u2014 they'll correct it right away."
    ),
    (
        "The {product} I received doesn't match the description on your website at all. This is false advertising.",
        "I apologize for the discrepancy. Please email returns@officeflow.com with your order number and photos showing the difference. We'll arrange a return and make sure the listing is corrected."
    ),
    (
        "Why is there NO way to start a return on the website? It's 2026! Get with the times.",
        "I understand the frustration \u2014 that's valid feedback. Currently, returns are handled through returns@officeflow.com or 1-800-OFFICE-1 ext. 3. I'll pass along the website feature request."
    ),
    (
        "I've emailed support three times about my portal issue and gotten zero responses. ZERO.",
        "That's unacceptable and I apologize. Please try calling 1-800-OFFICE-1 ext. 6 directly for immediate help with the portal issue. I'll escalate the non-responsiveness internally."
    ),
]

# ---------------------------------------------------------------------------
# Happy question/response templates
# ---------------------------------------------------------------------------

_HAPPY_TEMPLATES = [
    # Inventory - pleasant
    (
        "Hi! Just checking if you have {product} in stock. Thanks!",
        "Hi there! Yes, {product} is in stock and ready to go. Let me know if you need anything else!"
    ),
    (
        "Good morning! Could you check availability on {product} for me? Appreciate it!",
        "Good morning! {product} is available. Happy to help \u2014 anything else you need?"
    ),
    (
        "Hey, we love the {product} we got last time. Just want to make sure they're still available before reordering!",
        "Great to hear you love them! {product} is still in stock. Go ahead and reorder anytime!"
    ),
    (
        "Hi there! My name is {name} from {company}. We're looking to order {product}. Available?",
        "Hi {name}! {product} is in stock. {company} can order through the portal or email sales@officeflow.com. Happy ordering!"
    ),
    (
        "Quick question \u2014 do you have {product}? Planning a big office refresh. Thanks in advance!",
        "{product} is in stock! For a big refresh, our sales team at sales@officeflow.com can help with bulk pricing too. Good luck with the refresh!"
    ),
    (
        "Wonderful! Just wanted to double-check that {product} is available before I order. You guys always come through!",
        "Thanks for the kind words! {product} is indeed available. We appreciate your continued business!"
    ),
    (
        "Hi Emma! Is {product} in stock? We go through so many of those \u2014 love the quality!",
        "Hi! So glad you like them! {product} is in stock. Order away!"
    ),
    (
        "Hey! Love your products. Just need to confirm {product} availability real quick.",
        "Thank you! {product} is in stock and ready to ship. Appreciate your loyalty!"
    ),
    (
        "Good afternoon! Checking on {product} \u2014 we'd like to get some for the new hires joining next week.",
        "Good afternoon! {product} is available. Great idea for the new hires! Order through the portal or email sales@officeflow.com."
    ),
    (
        "Hi! I'm {name}. First time ordering. Do you carry {product}?",
        "Welcome, {name}! We absolutely do \u2014 {product} is in stock. Let me know if you have any questions about ordering!"
    ),
    # Policy - pleasant
    (
        "Hi! Could you explain your return policy? Just want to know before I order. Thanks!",
        "Of course! Items can be returned within 30 days of delivery with an RMA from returns@officeflow.com. Defective items can be returned anytime. Happy to help!"
    ),
    (
        "What are your shipping options? I'm not in a rush, just curious about the choices.",
        "Great question! We offer Standard ($8.95, 3-5 days), Expedited ($15.95, 2-3 days), Express ($24.95, 1-2 days), and Overnight ($39.95, next day). Standard is free on orders over $100!"
    ),
    (
        "Do you offer free shipping? That would be amazing!",
        "We do! Standard shipping is free on orders of $100 or more. Expedited is free at $250+. Pretty great deal!"
    ),
    (
        "Hey, I just want to say your shipping has been super fast lately. What are your shipping options again?",
        "Thanks for the positive feedback! We offer Standard (3-5 days), Expedited (2-3 days), Express (1-2 days), and Overnight. Orders before 2 PM EST ship same day!"
    ),
    (
        "Hi! I need to return an item but it's no big deal \u2014 just not what I expected. How do I start?",
        "No worries at all! Just email returns@officeflow.com with your order number and the reason. They'll issue an RMA within 4 business hours. Easy process!"
    ),
    (
        "Can I pick up my order instead of shipping? Would love to save on shipping if possible!",
        "Absolutely! Will Call Pickup is available at our distribution centers in Portland, Chicago, Atlanta, and Toronto \u2014 and it's free! Just select it at checkout."
    ),
    (
        "Thanks for always being helpful! Quick question \u2014 what are your business hours?",
        "Thank you \u2014 that means a lot! We're open Monday-Friday 7 AM - 7 PM EST, Saturday 9 AM - 2 PM EST. Always here to help!"
    ),
    (
        "This is {name} at {company}. You've been great to work with! How do we set up a business account?",
        "Thanks, {name}! We love working with {company} too. For business accounts, contact accounts@officeflow.com or 1-800-OFFICE-1 ext. 4 \u2014 they'll get you set up!"
    ),
    (
        "Your returns team was so fast last time. How do I start another return?",
        "Glad to hear the Returns team took great care of you! Same process \u2014 email returns@officeflow.com with your order number and reason. They'll have an RMA to you within 4 business hours."
    ),
    (
        "I love that you ship to Canada! What should I know about duties and delivery time?",
        "We're glad we can reach you up there! For Canadian shipments, expect 1-2 extra days for customs. Duties and taxes may apply at the border. Otherwise, same great service!"
    ),
    # Website - pleasant
    (
        "Hi! I'm having a tiny issue logging in. No rush, but could you point me to the right team?",
        "Of course! For login issues, our Technical Support team is the best bet. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6. They'll sort it out!"
    ),
    (
        "Just a heads up \u2014 the search on your website seems a bit slow today. Not a big deal but thought you'd want to know!",
        "Thanks for letting us know! I'll pass that along to our Tech Support team. If it continues, feel free to email support@officeflow.com."
    ),
    (
        "Your website has been working great lately! Just had a small glitch on checkout \u2014 who should I report it to?",
        "Glad to hear it's been good overall! For the checkout glitch, please report it to support@officeflow.com or call 1-800-OFFICE-1 ext. 6. Thanks for the feedback!"
    ),
    (
        "Hi! The password reset worked perfectly this time. Just wanted to say thanks to the tech team!",
        "I'll definitely pass that along \u2014 the tech team will appreciate the kudos! Glad everything's working for you. Let me know if you need anything else."
    ),
    (
        "Minor thing \u2014 product images are loading slowly on mobile. Just wanted to flag it. Love the site otherwise!",
        "Thanks for the heads-up and the kind words! I'll report the mobile image loading to our Tech Support at support@officeflow.com. Appreciate you letting us know!"
    ),
    # General happiness
    (
        "Just wanted to say I love ordering from OfficeFlow. You guys are always on top of it!",
        "That really makes our day \u2014 thank you! We work hard to provide great service. Let us know whenever you need anything!"
    ),
    (
        "Emma, you've been so helpful every time I chat in. Thank you!",
        "That's so kind of you to say \u2014 thank you! I'm always happy to help. Don't hesitate to reach out anytime!"
    ),
    (
        "I just wanted to check on {product} and also say that our last order arrived perfectly. Great job!",
        "Thank you for the positive feedback! {product} is in stock. So glad your last order was perfect \u2014 that's what we aim for!"
    ),
    (
        "Hi! {name} here from {company}. We've been really happy with OfficeFlow. Just need to check on {product}.",
        "Hi {name}! That's wonderful to hear from {company}. {product} is in stock. Let us know anytime you need something!"
    ),
    (
        "Your team resolved my issue so quickly last time. Just here to order more {product}!",
        "Glad we could help quickly! {product} is in stock \u2014 order through the portal anytime. We appreciate your business!"
    ),
    (
        "Honestly, you're the best office supply company we've worked with. Do you have {product}?",
        "Wow, thank you \u2014 that means so much! {product} is in stock. We're glad to have you as a customer!"
    ),
    (
        "This is {name} from {company}. Just want to say the quality of {product} has been outstanding!",
        "Hi {name}! Thank you for the kind words from {company}. We take pride in our product quality. Let me know if you need to reorder!"
    ),
    (
        "Happy to be an OfficeFlow customer! Quick check \u2014 is {product} available?",
        "And we're happy to have you! {product} is in stock. Anything else I can help with?"
    ),
    (
        "Hi there! Just placing our regular monthly order. Do you still have {product} in stock?",
        "Hi! Love the regularity. {product} is in stock as always. Happy ordering!"
    ),
    (
        "Your customer service is always a delight. I need {product} \u2014 are they available?",
        "Thank you so much \u2014 that's what we strive for! {product} is available. Let me know if you need anything else!"
    ),
    (
        "Good morning! Everything has been smooth with our recent orders. Just checking on {product}.",
        "Good morning! Glad to hear things have been smooth. {product} is in stock. Keep those great orders coming!"
    ),
    (
        "Hi! Recommending OfficeFlow to all my colleagues. Do you have {product}?",
        "That's the best compliment we can get \u2014 thank you! {product} is in stock. We appreciate the referrals!"
    ),
    (
        "I'm {name}. Switching our office supply vendor to you guys after great experiences. Is {product} in stock?",
        "Welcome aboard, {name}! We're thrilled to have you. {product} is in stock. Let us know how we can help make the transition smooth!"
    ),
    (
        "We've been with OfficeFlow for a year now and couldn't be happier. Just need some {product}!",
        "Happy anniversary with OfficeFlow! {product} is in stock. Here's to many more great years together!"
    ),
]


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
    return dt.strftime("%Y%m%dT%H%M%S%fZ")


def _gen_usage_metadata():
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


def _pick_pair(sentiment: str) -> tuple[str, str]:
    """Pick a random (question, response) pair and fill in placeholders."""
    templates = _ANGRY_TEMPLATES if sentiment == "angry" else _HAPPY_TEMPLATES
    q_tmpl, a_tmpl = random.choice(templates)
    vals = {
        "product": _p(), "name": _n(), "company": _c(), "order": _o(),
    }
    return q_tmpl.format(**vals), a_tmpl.format(**vals)


def _make_trace(question: str, response: str, sentiment: str, start_time: datetime):
    root_id = str(uuid.uuid4())
    child_id = str(uuid.uuid4())

    child_offset = random.uniform(0.5, 3.0)
    child_duration = random.uniform(5.0, 18.0)
    child_start = start_time + timedelta(seconds=child_offset)
    child_end = child_start + timedelta(seconds=child_duration)
    root_end = child_end + timedelta(seconds=random.uniform(0.001, 0.1))

    root_dotted = f"{_ts_to_dotted(start_time)}{root_id}"
    child_dotted = f"{root_dotted}.{_ts_to_dotted(child_start)}{child_id}"

    usage = _gen_usage_metadata()

    messages = [
        {"content": SYSTEM_PROMPT, "role": "system"},
        {"content": question, "role": "user"},
        {"content": response, "role": "assistant"},
    ]

    chatcmpl_id = f"chatcmpl-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=29))}"
    created_ts = int(child_end.replace(tzinfo=timezone.utc).timestamp())

    root_run = {
        "id": root_id,
        "name": "Emma",
        "run_type": "chain",
        "inputs": {"question": question},
        "outputs": {"messages": messages, "output": response},
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
        "tags": [sentiment],
    }

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
                        "description": "SQL query to get information about our inventory.",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge_base",
                        "description": "Search company policies and information.",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
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


def main():
    random.seed(123)

    # Time window: 14 days ago -> now
    now = datetime(2026, 2, 16, 12, 0, 0)
    start_window = now - timedelta(days=14)
    midpoint = now - timedelta(days=7)

    # Split roughly 500 traces per week
    traces_week1 = 500
    traces_week2 = 500

    # Week 1: 85% angry, 15% happy
    w1_angry = int(traces_week1 * 0.85)  # 425
    w1_happy = traces_week1 - w1_angry    # 75

    # Week 2: 15% angry, 85% happy
    w2_angry = int(traces_week2 * 0.15)   # 75
    w2_happy = traces_week2 - w2_angry     # 425

    print(f"Week 1 (14-7 days ago): {w1_angry} angry, {w1_happy} happy")
    print(f"Week 2 (7-0 days ago):  {w2_angry} angry, {w2_happy} happy")
    print(f"Total angry: {w1_angry + w2_angry}, Total happy: {w1_happy + w2_happy}")

    # Build trace specs: (sentiment, week)
    week1_specs = (["angry"] * w1_angry) + (["happy"] * w1_happy)
    week2_specs = (["angry"] * w2_angry) + (["happy"] * w2_happy)
    random.shuffle(week1_specs)
    random.shuffle(week2_specs)

    # Generate timestamps spread across each week
    def spread_times(base: datetime, count: int, window_seconds: float):
        avg_gap = window_seconds / count
        times = []
        t = base
        for _ in range(count):
            times.append(t)
            t += timedelta(seconds=random.uniform(avg_gap * 0.3, avg_gap * 1.7))
        return times

    week1_times = spread_times(start_window, traces_week1, 7 * 24 * 3600)
    week2_times = spread_times(midpoint, traces_week2, 7 * 24 * 3600)

    all_runs = []

    for sentiment, start_time in zip(week1_specs, week1_times):
        q, a = _pick_pair(sentiment)
        all_runs.extend(_make_trace(q, a, sentiment, start_time))

    for sentiment, start_time in zip(week2_specs, week2_times):
        q, a = _pick_pair(sentiment)
        all_runs.extend(_make_trace(q, a, sentiment, start_time))

    # Stats
    angry_count = sum(1 for r in all_runs if r["name"] == "Emma" and "angry" in r["tags"])
    happy_count = sum(1 for r in all_runs if r["name"] == "Emma" and "happy" in r["tags"])
    print(f"\nGenerated {len(all_runs)} runs ({len(all_runs)//2} traces)")
    print(f"  angry: {angry_count}")
    print(f"  happy: {happy_count}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)
    with open(output_path, "w") as f:
        json.dump(all_runs, f, indent=2)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
