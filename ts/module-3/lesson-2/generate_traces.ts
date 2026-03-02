/**
 * Generate 1000 synthetic traces for OfficeFlow Supply Co. customer support.
 *
 * Produces synthetic_traces.json with 1000 traces (200 per category):
 *   - inventory: product stock/availability questions
 *   - policy: company policy questions (returns, shipping, etc.)
 *   - out_of_scope: things Emma can't help with
 *   - both: inventory AND policy in one message
 *   - website_troubleshooting: website/portal issues
 *
 * Each trace = 2 runs: root "Emma" chain + child "ChatOpenAI" llm.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// Random helpers
// ---------------------------------------------------------------------------

function randomChoice<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomSample<T>(arr: T[], n: number): T[] {
  const copy = [...arr];
  const result: T[] = [];
  const count = Math.min(n, copy.length);
  for (let i = 0; i < count; i++) {
    const idx = Math.floor(Math.random() * copy.length);
    result.push(copy[idx]);
    copy.splice(idx, 1);
  }
  return result;
}

function randomInt(a: number, b: number): number {
  return Math.floor(Math.random() * (b - a + 1)) + a;
}

function randomUniform(a: number, b: number): number {
  return a + Math.random() * (b - a);
}

// Seeded random (simple mulberry32)
let _seed = 42;
function seedRandom(seed: number) {
  _seed = seed;
}

function seededRandom(): number {
  let t = (_seed += 0x6d2b79f5);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// Override Math.random with seeded version after seed is set
function initSeededRandom(seed: number) {
  seedRandom(seed);
  Math.random = seededRandom;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const CATEGORIES = [
  "inventory",
  "policy",
  "out_of_scope",
  "both",
  "website_troubleshooting",
];
const TRACES_PER_CATEGORY = 200;
const OUTPUT_FILE = "synthetic_traces.json";

const SYSTEM_PROMPT =
  "You are Emma, a customer support specialist for OfficeFlow Supply Co., " +
  "a paper and office supplies distribution company serving small-to-medium " +
  "businesses across North America.\n\nABOUT YOUR ROLE:\nYou're part of the " +
  "Customer Experience team and have been with OfficeFlow for 3 years. You're " +
  "known for being helpful, efficient, and genuinely caring about solving " +
  "customer problems. Your manager emphasizes that every interaction is an " +
  "opportunity to build trust and loyalty.\n\nWHAT YOU CAN HELP WITH:\n" +
  "\u2713 Product Information - Answer questions about our catalog of office " +
  "supplies, paper products, writing instruments, organizational tools, and " +
  "desk accessories\n\u2713 Inventory & Availability - Check current stock " +
  "levels and help customers find what they need\n\u2713 Product Recommendations " +
  "- Suggest products based on customer needs, usage patterns, and budget\n" +
  "\u2713 General Inquiries - Handle questions about our company, product lines, " +
  "and services\n\nWHAT YOU CANNOT DIRECTLY HANDLE:\n\u2717 Order Placement - " +
  "While you can provide product info, actual ordering is done through our web " +
  "portal or by contacting our sales team at sales@officeflow.com\n\u2717 Order " +
  "Status & Tracking - Direct customers to check their account portal or contact " +
  "fulfillment@officeflow.com\n\u2717 Returns & Refunds - These require approval " +
  "from our Returns Department at returns@officeflow.com\n\u2717 Account Changes " +
  "- Billing, payment methods, and account settings must go through " +
  "accounts@officeflow.com\n\u2717 Technical Support - For website issues, direct " +
  "to support@officeflow.com";

const PRODUCTS = [
  "Copy Paper 500 Sheets",
  "Blue Ballpoint Pens (12-pack)",
  "Stapler with Staples",
  "Spiral Notebooks (3-pack)",
  "Manila File Folders (25-pack)",
  "Sticky Notes (4-pack)",
  "Dry Erase Markers (8-pack)",
  "Paper Clips (100-pack)",
  "Binder Clips (24-pack)",
  "Legal Pads (6-pack)",
  "Highlighters (5-pack)",
  "Desk Organizer Tray",
  "Correction Tape (3-pack)",
  "Scissors - 8 inch",
  "Rubber Bands (Assorted)",
  "Tape Dispenser with Tape",
  "Envelopes #10 (100-pack)",
  "Index Cards (3x5, 100-pack)",
  "Whiteboard Eraser",
  "Push Pins (100-pack)",
  "Hanging File Folders (25-pack)",
  "Sheet Protectors (50-pack)",
  "Mechanical Pencils (12-pack)",
  "Black Gel Pens (6-pack)",
  "Desk Calendar 2026",
  "Letter Trays (2-tier)",
  "Glue Sticks (6-pack)",
  "Post-it Flags (4 colors)",
  "Laminating Pouches (50-pack)",
  "Clipboard - Standard",
];

const NAMES = [
  "Alex",
  "Jordan",
  "Sam",
  "Casey",
  "Morgan",
  "Taylor",
  "Riley",
  "Jamie",
  "Pat",
  "Chris",
  "Drew",
  "Quinn",
  "Avery",
  "Blake",
  "Cameron",
  "Dana",
  "Emerson",
  "Finley",
  "Hayden",
  "Jesse",
  "Kelly",
  "Lee",
  "Noel",
  "Parker",
  "Robin",
  "Skyler",
  "Terry",
  "Val",
  "Whitney",
  "Kendall",
];

const COMPANY_NAMES = [
  "Whitfield & Associates",
  "Summit Group LLC",
  "Cascade Office Solutions",
  "Bright Path Consulting",
  "Metro Legal Services",
  "Greenleaf Accounting",
  "Pinnacle Design Co.",
  "Harbor Health Clinic",
  "Eastside Property Management",
  "Nova Financial Group",
  "Crestwood Engineering",
  "Lakeside Marketing",
  "Redwood Consulting",
  "Sterling Enterprises",
  "Atlas Logistics",
  "Compass Realty",
  "Iron Bridge Capital",
  "Oakmont Partners",
  "Sapphire Technologies",
  "Westlake Advisory",
];

function _randOrder(): string {
  return `ORD-${randomInt(1000, 9999)}`;
}

function _randProduct(): string {
  return randomChoice(PRODUCTS);
}

function _randProducts(n = 2): string[] {
  return randomSample(PRODUCTS, Math.min(n, PRODUCTS.length));
}

function _randName(): string {
  return randomChoice(NAMES);
}

function _randCompany(): string {
  return randomChoice(COMPANY_NAMES);
}

// ---------------------------------------------------------------------------
// Template helper: format string with named placeholders
// ---------------------------------------------------------------------------

function formatTemplate(
  template: string,
  vars: Record<string, string>
): string {
  let result = template;
  for (const [key, value] of Object.entries(vars)) {
    result = result.replace(new RegExp(`\\{${key}\\}`, "g"), value);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Question / Response templates per category
// ---------------------------------------------------------------------------

function _inventoryQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "Do you have {product} in stock?",
      "Yes, {product} is currently in stock! Would you like help with anything else?",
    ],
    [
      "I need to check availability on {product}. Do you carry those?",
      "{product} is available. Let me know if you need any other product info!",
    ],
    [
      "Can you tell me if {product} is available right now?",
      "Great news \u2014 {product} is in stock. Anything else I can help with?",
    ],
    [
      "Hey, does OfficeFlow carry {product}?",
      "We sure do! {product} is in our catalog and currently available.",
    ],
    [
      "I'm looking for {product}. Are those something you sell?",
      "Absolutely! {product} is one of our products and it's in stock right now.",
    ],
    [
      "What's the availability on {product}? We need about 50 units.",
      "{product} is in stock. For a bulk order of 50 units, you can place it through our web portal or contact sales@officeflow.com for assistance.",
    ],
    [
      "Is {product} running low? I need to order soon.",
      "{product} is in stock, but I'd recommend ordering soon to make sure you get what you need. You can order through our portal or email sales@officeflow.com.",
    ],
    [
      "Hi, I'd like to know if you have {product} and {product2} available.",
      "Both {product} and {product2} are currently in stock! Let me know if you need any other details.",
    ],
    [
      "We're restocking our office. Do you have {product} on hand?",
      "Yes, {product} is available! If you're doing a big restock, our sales team at sales@officeflow.com can help with bulk pricing.",
    ],
    [
      "Quick question \u2014 is {product} still available or is it sold out?",
      "{product} is still available. Go ahead and grab it through the portal whenever you're ready!",
    ],
    [
      "I placed an order for {product} last week but I might need more. Do you still have them?",
      "We do still have {product} in stock. You can place another order through the web portal anytime.",
    ],
    [
      "Can you look up whether {product} is in your inventory?",
      "I just checked and {product} is in stock. Let me know if there's anything else!",
    ],
    [
      "My name is {name} and I need {product} for our office at {company}. Available?",
      "Hi {name}! {product} is in stock and ready to go. You can order through the portal or reach out to sales@officeflow.com.",
    ],
    [
      "Do you carry anything like {product}? My office needs some.",
      "We carry {product} and it's currently available. Would you like more details or recommendations for similar items?",
    ],
    [
      "I saw {product} on your website but couldn't tell if it's in stock. Can you confirm?",
      "{product} is confirmed in stock! You should be able to order directly from the site.",
    ],
    [
      "What office supply products do you have for organizing files?",
      "We have several filing options in stock, including Manila File Folders (25-pack), Hanging File Folders (25-pack), and Sheet Protectors (50-pack). Let me know which you're interested in!",
    ],
    [
      "Do you have any writing instruments available? Looking for pens and pencils.",
      "Absolutely! We have Blue Ballpoint Pens (12-pack), Black Gel Pens (6-pack), Mechanical Pencils (12-pack), and Highlighters (5-pack) all in stock.",
    ],
    [
      "I need desk accessories. What's in stock?",
      "We have several desk accessories available: Desk Organizer Tray, Letter Trays (2-tier), Desk Calendar 2026, and Tape Dispenser with Tape. Let me know what catches your eye!",
    ],
    [
      "Are {product} available? We go through those fast at {company}.",
      "{product} is in stock. If you go through them quickly, you might want to check with sales@officeflow.com about setting up recurring orders.",
    ],
    [
      "Hi there, this is {name}. Could you check stock on {product} for me?",
      "Hi {name}! {product} is in stock. Would you like to place an order?",
    ],
    [
      "I need {product} urgently. Please tell me you have them.",
      "Good news \u2014 {product} is in stock! You can place an order right away through the web portal.",
    ],
    [
      "We just ran out of {product}. Do you have any?",
      "We do have {product} available! Order through the portal and you'll be restocked in no time.",
    ],
    [
      "Can I get a stock check on {product} and {product2}?",
      "Both {product} and {product2} are currently in stock. Let me know if you'd like to order!",
    ],
    [
      "How much {product} do you have available? We need a large quantity.",
      "{product} is currently in stock. For large quantity orders, I'd recommend contacting our sales team at sales@officeflow.com for the best pricing.",
    ],
    [
      "I'm with {company}. We need {product} \u2014 is that something you stock?",
      "Hi! We definitely stock {product} and it's available right now. Your team at {company} can order through the portal or email sales@officeflow.com.",
    ],
    [
      "Are there any {product} left? I've been meaning to order.",
      "Yes, {product} is still in stock! Go ahead and place your order whenever you're ready.",
    ],
    [
      "Could you check if {product} is in your warehouse?",
      "Just checked \u2014 {product} is in stock. You're good to order!",
    ],
    [
      "What paper products do you currently have available?",
      "We have several paper products in stock: Copy Paper 500 Sheets, Legal Pads (6-pack), Spiral Notebooks (3-pack), and Index Cards (3x5, 100-pack). Want details on any of these?",
    ],
    [
      "Looking for sticky notes and similar products. What do you have?",
      "We've got Sticky Notes (4-pack) and Post-it Flags (4 colors) in stock right now. Both are great for organization!",
    ],
    [
      "Hi, my name's {name} from {company}. Just checking \u2014 do you have {product}?",
      "Hi {name}! Yes, {product} is currently available. Let me know if you need anything else for {company}!",
    ],
    [
      "We use {product} a lot. Can you confirm they're in stock before I order?",
      "Confirmed \u2014 {product} is in stock. Go ahead and place your order!",
    ],
    [
      "I'm browsing your catalog and wondering about availability for {product}.",
      "{product} is in stock and ready to ship. Let me know if you have questions about any other items!",
    ],
    [
      "Our supply closet is empty. Do you have {product}, {product2}, and {product3}?",
      "Great news \u2014 {product}, {product2}, and {product3} are all currently in stock! Perfect for a full restock.",
    ],
    [
      "Is there currently limited stock on {product}?",
      "{product} is in stock, though inventory levels can change. I'd recommend ordering soon if you need it!",
    ],
    [
      "Hey, can you check whether you have {product} available for shipping to {company}?",
      "{product} is in stock and we can ship to {company}'s address. Just place the order through our portal!",
    ],
    [
      "I need to order {product}. What's the stock situation?",
      "{product} is available. You can go ahead and order through the web portal at your convenience.",
    ],
    [
      "Can I get {product} shipped to our office this week?",
      "{product} is in stock! If you order before 2:00 PM EST, it ships same day. Standard delivery is 3-5 business days.",
    ],
    [
      "Do you currently stock {product}? I can't find it on the website.",
      "Yes, we do carry {product} and it's in stock! If you're having trouble finding it on the site, try searching by the product name or contact support@officeflow.com for help.",
    ],
    [
      "My assistant asked me to check on {product} availability. Are they in stock?",
      "{product} is in stock! Let your assistant know they can order through the portal anytime.",
    ],
    [
      "I'm {name} and I need to restock our breakroom. Do you carry {product}?",
      "Hi {name}! We do carry {product} and it's currently available. Let me know if you need anything else!",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const [p1, p2] = _randProducts(2);
    const p3 = _randProduct();
    const name = _randName();
    const company = _randCompany();
    const q = formatTemplate(t[0], {
      product: p1,
      product2: p2,
      product3: p3,
      name,
      company,
    });
    const a = formatTemplate(t[1], {
      product: p1,
      product2: p2,
      product3: p3,
      name,
      company,
    });
    pairs.push([q, a]);
  }
  return pairs;
}

function _policyQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "What's your return policy?",
      "Items can be returned within 30 days of delivery. You'll need an RMA number from our Returns Department \u2014 contact them at returns@officeflow.com or 1-800-OFFICE-1 ext. 3. Defective items can be returned anytime.",
    ],
    [
      "How do I return a defective item?",
      "For defective items, email returns@officeflow.com with your order number, a description of the defect, and photos if possible. They'll issue an RMA and a prepaid return label at no cost.",
    ],
    [
      "What are your shipping options and costs?",
      "We offer Standard ($8.95, 3-5 days), Expedited ($15.95, 2-3 days), Express ($24.95, 1-2 days), and Overnight ($39.95, next day). Standard shipping is free on orders over $100!",
    ],
    [
      "Do you offer free shipping?",
      "Yes! Standard shipping is free on orders of $100 or more. Expedited shipping is free on orders of $250+.",
    ],
    [
      "How long does standard shipping take?",
      "Standard shipping takes 3-5 business days. Orders placed before 2:00 PM EST ship the same day.",
    ],
    [
      "Can I ship to Canada?",
      "Absolutely! We ship to all Canadian provinces and territories. Duties and taxes may apply, and you should expect an extra 1-2 days for customs.",
    ],
    [
      "What are your business hours?",
      "Our main phone line is open Monday-Friday 7:00 AM - 7:00 PM EST, and Saturday 9:00 AM - 2:00 PM EST. We're closed on Sundays.",
    ],
    [
      "How do I place an order?",
      "You can place orders through our web portal at www.officeflow.com or by contacting our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2.",
    ],
    [
      "What's the return window? I got something two weeks ago.",
      "You're within the return window! Items can be returned within 30 days of delivery. Contact returns@officeflow.com with your order number to get an RMA.",
    ],
    [
      "I need to process a return on order {order}. How do I do that?",
      "To start a return on order {order}, email returns@officeflow.com with your order number and reason for the return. They'll issue an RMA within 4 business hours.",
    ],
    [
      "How long do refunds take?",
      "Refunds are processed within 5-7 business days after we receive your return. The credit goes back to your original payment method.",
    ],
    [
      "Do you ship internationally?",
      "We ship to the US and Canada as standard. For international orders outside those areas, contact sales@officeflow.com for a quote \u2014 it's available for large orders.",
    ],
    [
      "What's the cutoff time for same-day shipping?",
      "Orders placed before 2:00 PM EST ship the same business day. After that, they ship the next business day.",
    ],
    [
      "Can I pick up an order instead of having it shipped?",
      "Yes! We offer Will Call Pickup at our distribution centers in Portland, Chicago, Atlanta, and Toronto. Select it at checkout and you'll be notified when it's ready \u2014 usually 2-4 hours.",
    ],
    [
      "Where are your distribution centers located?",
      "We have four distribution centers: Portland, OR (headquarters), Schaumburg, IL (Chicago area), Norcross, GA (Atlanta area), and Mississauga, ON (Toronto area).",
    ],
    [
      "Do you offer expedited or overnight shipping?",
      "Yes! Expedited is $15.95 (2-3 days), Express is $24.95 (1-2 days), and Overnight is $39.95 (next business day). Express and Overnight require ordering by 2:00 PM and 12:00 PM EST respectively.",
    ],
    [
      "What happens if my package arrives damaged?",
      "Photograph the damage and contact us within 48 hours at fulfillment@officeflow.com. We'll arrange a replacement or refund immediately \u2014 you won't need to return the damaged item first.",
    ],
    [
      "Can I exchange an item instead of returning it?",
      "Absolutely! Exchanges follow the same process as returns \u2014 you'll need an RMA from returns@officeflow.com. Price differences may apply if you're swapping for a different item.",
    ],
    [
      "How do I track my order?",
      "You'll get a tracking number by email when your order ships. You can check status anytime at www.officeflow.com/track, or contact fulfillment@officeflow.com for help.",
    ],
    [
      "What payment methods do you accept?",
      "For payment and billing questions, I'd direct you to our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They handle all payment method details.",
    ],
    [
      "I need to update my billing address. How?",
      "Account changes like billing address updates go through our Accounts team. Email accounts@officeflow.com or call 1-800-OFFICE-1 ext. 4.",
    ],
    [
      "Are you closed on holidays?",
      "We're closed on New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, and Christmas. We have limited hours on the day before Thanksgiving, Christmas Eve, and New Year's Eve (until 2 PM EST).",
    ],
    [
      "My name is {name} from {company}. What's your shipping policy for business accounts?",
      "Hi {name}! Business account customers at {company} may have access to custom shipping rates and dedicated delivery routes in major metro areas. Contact your account manager for specifics!",
    ],
    [
      "How do I set up a business account?",
      "To set up a business account, reach out to our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They'll get you set up.",
    ],
    [
      "What's the policy on returning opened items?",
      "Most opened items in original packaging can be returned within 30 days. However, opened paper reams cannot be returned due to hygiene standards, and custom-printed or Final Sale items are ineligible.",
    ],
    [
      "I received the wrong items in my order. What should I do?",
      "I'm sorry about that! Contact fulfillment@officeflow.com with your order number and details about what you received vs. what you ordered. They'll ship the correct items same or next business day and provide a return label.",
    ],
    [
      "Do you offer bulk pricing or discounts for large orders?",
      "For bulk pricing, contact our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2. They can provide quotes for large orders.",
    ],
    [
      "Can I change my shipping address after placing an order?",
      "If the order hasn't shipped yet, contact the sales team immediately \u2014 changes are free within 2 hours of placement. After shipping, the fulfillment team may be able to reroute, though a $10-15 fee applies.",
    ],
    [
      "Is there a way to get Saturday delivery?",
      "Our distribution centers are closed on weekends, so Saturday delivery isn't available. Express and Overnight shipping are available Monday-Thursday only.",
    ],
    [
      "How do I contact the returns department?",
      "You can reach our Returns Department at returns@officeflow.com or 1-800-OFFICE-1 ext. 3. They're available Monday-Friday, 8:00 AM - 6:00 PM EST, and respond within 4 business hours.",
    ],
    [
      "I have a question about my invoice. Who do I talk to?",
      "For invoice and billing questions, contact our Accounts team at accounts@officeflow.com or 1-800-OFFICE-1 ext. 4. They're available Monday-Friday, 9:00 AM - 5:00 PM EST.",
    ],
    [
      "Is return shipping free?",
      "Return shipping is free if the item is defective or we shipped the wrong item. Otherwise, return shipping costs are the customer's responsibility.",
    ],
    [
      "What's the number I can call for help?",
      "Our main number is 1-800-OFFICE-1. For specific departments: Customer Service ext. 1, Sales ext. 2, Returns ext. 3, Accounts ext. 4, Fulfillment ext. 5, Tech Support ext. 6.",
    ],
    [
      "How do I get an RMA number for a return?",
      "Contact our Returns Department at returns@officeflow.com or 1-800-OFFICE-1 ext. 3 with your order number and reason for the return. They'll issue an RMA within 4 business hours.",
    ],
    [
      "Do you ship to PO boxes?",
      "Yes, we ship to PO Boxes for most items using standard shipping. Some restrictions apply for large or hazardous items.",
    ],
    [
      "Where can I find your company contact information?",
      "Our main number is 1-800-OFFICE-1. Our headquarters is at 1234 Commerce Way, Portland, OR 97220. You can also email info@officeflow.com or visit www.officeflow.com.",
    ],
    [
      "What do I do if my package says delivered but I didn't get it?",
      "Contact us at fulfillment@officeflow.com. We'll file a carrier claim and send a replacement. The claim process typically takes 3-5 business days.",
    ],
    [
      "Can you tell me about your exchange policy?",
      "We're happy to do exchanges! Same process as returns \u2014 contact returns@officeflow.com for an RMA. Price differences may apply. Exchange items ship once we receive and inspect the return.",
    ],
    [
      "Hi, this is {name}. I'm trying to understand your return policy for defective items.",
      "Hi {name}! Defective items can be returned at any time, even after the 30-day window. Email returns@officeflow.com with photos of the defect. They'll send a prepaid return label, and return shipping is on us.",
    ],
    [
      "What are the shipping restrictions?",
      "Hazardous materials (certain markers, adhesives) must ship ground only. Oversized items like furniture need freight shipping. Items over 50 lbs may incur freight charges. No aerosols or flammables on international shipments.",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const order = _randOrder();
    const name = _randName();
    const company = _randCompany();
    const q = formatTemplate(t[0], { order, name, company });
    const a = formatTemplate(t[1], { order, name, company });
    pairs.push([q, a]);
  }
  return pairs;
}

function _outOfScopeQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "Can you help me write a cover letter?",
      "I appreciate you reaching out, but I'm only able to help with OfficeFlow product and service questions. For cover letter help, you might try a career services site. Is there anything office-supply related I can assist with?",
    ],
    [
      "What's the weather like in Portland today?",
      "I wish I could help with that, but I'm limited to OfficeFlow-related questions! For weather, try your favorite weather app. Anything else I can help with regarding our products or services?",
    ],
    [
      "Can you recommend a good restaurant near your Portland office?",
      "That's a fun question, but unfortunately I can only help with OfficeFlow product and service inquiries. Yelp or Google Maps would be great for restaurant recs! Anything supply-related I can help with?",
    ],
    [
      "I need help with my taxes. Can you help?",
      "I'm not able to help with taxes, but I'd recommend a CPA or tax preparation service. I'm here if you need anything related to office supplies or our services!",
    ],
    [
      "Do you sell office furniture?",
      "We focus on office supplies, paper products, writing instruments, and desk accessories. We don't currently carry furniture. For specific product questions, I'm happy to help!",
    ],
    [
      "Can you fix my computer? It keeps crashing.",
      "I'm sorry about the tech troubles, but I can only help with OfficeFlow products and services. For computer issues, I'd suggest contacting your IT department or a local tech support service.",
    ],
    [
      "What's the stock price of OfficeFlow?",
      "I'm not able to provide financial or stock information. For investor relations, you could check our corporate website or contact corporate@officeflow.com. Anything product-related I can help with?",
    ],
    [
      "Can you translate this document for me?",
      "Translation is outside my area, I'm afraid. I'm here for OfficeFlow product and service questions. For translation, try Google Translate or a professional translation service!",
    ],
    [
      "I want to apply for a job at OfficeFlow. How do I do that?",
      "Thanks for your interest in working with us! Job applications aren't something I handle, though. Check our website for a careers page, or email corporate@officeflow.com. Can I help with anything supply-related?",
    ],
    [
      "Can you book a meeting room for me?",
      "I'm not able to book meeting rooms \u2014 I'm specialized in OfficeFlow product and service support. You'd want to check with your office administrator for room bookings. Need anything else?",
    ],
    [
      "What's the best laptop for office work?",
      "Great question, but electronics and laptops are outside our product range. We focus on office supplies and paper products. For laptop recommendations, I'd suggest a tech review site. Anything else I can help with?",
    ],
    [
      "Can you help me set up my email?",
      "Email setup is outside my expertise \u2014 I'm here for OfficeFlow product and service questions. Your IT department or email provider's support would be the best bet!",
    ],
    [
      "Tell me a joke.",
      "Ha! I appreciate the request, but I'm best at helping with office supply questions. If you need any product info or have service questions, I'm your person!",
    ],
    [
      "Can you order me a pizza?",
      "I wish I could! But I'm limited to OfficeFlow products and services. For pizza, try your favorite delivery app. Need any staplers or sticky notes instead?",
    ],
    [
      "What's the capital of France?",
      "That would be Paris! But my real expertise is OfficeFlow products and services. Is there anything supply-related I can help with?",
    ],
    [
      "Can you help me plan my vacation?",
      "Vacation planning sounds fun, but it's outside my area. I'm here for OfficeFlow product and service support. Let me know if you need anything for the office!",
    ],
    [
      "Do you sell printers or toner cartridges?",
      "We don't currently carry printers or toner cartridges \u2014 our focus is on office supplies, paper products, and desk accessories. Is there anything else from our catalog I can help with?",
    ],
    [
      "Can you help me with my car insurance claim?",
      "I'm sorry, that's well outside my area! I can only help with OfficeFlow products and services. For insurance, you'd want to contact your insurance provider directly.",
    ],
    [
      "I need advice on investing in the stock market.",
      "Investment advice isn't something I can provide \u2014 I'm focused on OfficeFlow product support. A financial advisor would be the right person to talk to. Need any office supplies?",
    ],
    [
      "Can you write me a Python script?",
      "I appreciate the ask, but coding is outside my scope! I'm here to help with OfficeFlow products and services. For programming help, try Stack Overflow or a developer community.",
    ],
    [
      "What's the best way to lose weight?",
      "Health and fitness advice is outside my wheelhouse \u2014 I'd recommend talking to a healthcare professional. I'm great at office supply questions though! Anything I can help with?",
    ],
    [
      "Can you order me an Uber?",
      "I can't book rides, but I can help with office supplies! Is there anything OfficeFlow-related you need?",
    ],
    [
      "Do you sell coffee or snacks for the office?",
      "We don't carry food or beverages \u2014 our catalog focuses on office supplies, paper products, and desk accessories. Is there something in that range I can help with?",
    ],
    [
      "Can you summarize this article for me?",
      "Article summarization is outside my scope. I'm here for OfficeFlow product and service support. Feel free to ask me about anything in our catalog!",
    ],
    [
      "What's the best streaming service right now?",
      "Entertainment recommendations are outside my area! I'm focused on OfficeFlow products and services. Let me know if you need anything for the office.",
    ],
    [
      "Can you help me move to a new apartment?",
      "I can't help with moving, but if you need packing tape or labels for the move, we've got you covered! Anything office-supply related I can assist with?",
    ],
    [
      "Do you sell cleaning supplies?",
      "Cleaning supplies aren't in our current catalog \u2014 we specialize in office supplies, paper products, writing instruments, and desk accessories. Need anything from those categories?",
    ],
    [
      "Can you fix my printer?",
      "Printer repair is outside my scope \u2014 I'm here for OfficeFlow product and service questions. For printer issues, I'd suggest contacting the manufacturer's support line.",
    ],
    [
      "I need legal advice about a contract. Can you help?",
      "Legal advice is something I can't provide. I'd recommend consulting with an attorney. I'm here for OfficeFlow product and service questions \u2014 need anything from our catalog?",
    ],
    [
      "What time does the post office close?",
      "I don't have post office hours, but you can check usps.com for that. I'm here to help with OfficeFlow products and services \u2014 anything I can assist with?",
    ],
    [
      "My name is {name}. Can you help me find a new apartment?",
      "Hi {name}! I appreciate you reaching out, but apartment hunting is outside my area. I'm here for OfficeFlow product and service support. Need any office supplies?",
    ],
    [
      "Is OfficeFlow hiring right now?",
      "For job openings, I'd recommend checking our website or contacting corporate@officeflow.com. I handle product and service support. Anything supply-related I can help with?",
    ],
    [
      "Can you teach me how to use Excel?",
      "Excel training is outside my expertise \u2014 there are great tutorials on YouTube and LinkedIn Learning. I'm here for OfficeFlow product questions though!",
    ],
    [
      "I need to send flowers to my mom. Can you help?",
      "That's sweet! But flower delivery is outside my scope. I'm here for OfficeFlow office supplies and services. Let me know if you need anything for the office!",
    ],
    [
      "Do you sell electronics or computer accessories?",
      "We don't carry electronics or computer accessories. Our catalog focuses on office supplies, paper products, writing instruments, and organizational tools. Can I help you find something in those categories?",
    ],
    [
      "Can you check the flight status for my upcoming trip?",
      "Flight tracking is outside what I can do \u2014 I'd recommend checking your airline's app or website. I'm here for OfficeFlow product and service questions!",
    ],
    [
      "What's the meaning of life?",
      "That's a deep one! I'll leave that to the philosophers. I'm here to help with OfficeFlow products and services. Anything supply-related on your mind?",
    ],
    [
      "I need to dispute a charge on my credit card. Can you help?",
      "Credit card disputes go through your card issuer, not through us. If the charge is from OfficeFlow and you believe it's incorrect, contact accounts@officeflow.com.",
    ],
    [
      "Can you help with team building activities?",
      "Team building is outside my area, but sounds fun! I'm here for OfficeFlow product and service support. Need supplies for a team event?",
    ],
    [
      "Do you sell ergonomic chairs or standing desks?",
      "We don't currently carry furniture like chairs or desks. We focus on office supplies, paper products, and desk accessories. Anything from our catalog I can help with?",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const name = _randName();
    const q = formatTemplate(t[0], { name });
    const a = formatTemplate(t[1], { name });
    pairs.push([q, a]);
  }
  return pairs;
}

function _bothQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "Do you have {product} in stock, and what's your return policy if they don't work out?",
      "{product} is currently in stock! As for returns, items can be returned within 30 days with an RMA from returns@officeflow.com. Defective items can be returned anytime.",
    ],
    [
      "I need {product} \u2014 are they available? Also, how much is shipping?",
      "{product} is in stock! Shipping is $8.95 standard (3-5 days), free on orders over $100. Expedited and overnight options are also available.",
    ],
    [
      "Can you check if you have {product} and tell me how to place an order?",
      "{product} is available! To order, use our web portal at www.officeflow.com or email sales@officeflow.com.",
    ],
    [
      "I'm looking at {product} and {product2}. Are both available, and do you ship to Canada?",
      "Both {product} and {product2} are in stock! And yes, we ship to all Canadian provinces. Expect 1-2 extra days for customs, and duties/taxes may apply.",
    ],
    [
      "My name is {name} from {company}. I need {product} \u2014 is it in stock? And can I return it if my team doesn't like it?",
      "Hi {name}! {product} is in stock. If your team isn't happy, you can return it within 30 days \u2014 just contact returns@officeflow.com for an RMA.",
    ],
    [
      "Do you carry {product}? And what's the quickest shipping option?",
      "{product} is in stock! Our fastest option is Overnight Shipping at $39.95 \u2014 order by 12:00 PM EST for next-business-day delivery.",
    ],
    [
      "I need to know if {product} is available and whether I can get free shipping.",
      "{product} is available! Standard shipping is free on orders of $100 or more.",
    ],
    [
      "Are {product} in stock? Also, I got a damaged item in my last order \u2014 what do I do?",
      "{product} is in stock. For the damaged item, photograph it and email fulfillment@officeflow.com within 48 hours. They'll arrange a replacement or refund immediately.",
    ],
    [
      "I want to order {product} and also need to process a return on order {order}.",
      "{product} is in stock and ready to order through the portal. For the return on {order}, contact returns@officeflow.com with your order number and reason \u2014 they'll issue an RMA within 4 business hours.",
    ],
    [
      "Do you have {product}? And where's your nearest warehouse for pickup?",
      "{product} is in stock! Our distribution centers are in Portland OR, Schaumburg IL (Chicago), Norcross GA (Atlanta), and Mississauga ON (Toronto). Select Will Call Pickup at checkout.",
    ],
    [
      "Is {product} available? I also want to know about your bulk pricing.",
      "{product} is in stock! For bulk pricing, contact our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2 \u2014 they can get you a quote.",
    ],
    [
      "I need {product} urgently \u2014 do you have it? What's the fastest I can get it?",
      "{product} is in stock! With Overnight Shipping ($39.95), order by 12:00 PM EST and you'll have it the next business day.",
    ],
    [
      "Check availability on {product} please, and let me know your business hours.",
      "{product} is available! Our phone lines are open Monday-Friday 7:00 AM - 7:00 PM EST, Saturday 9:00 AM - 2:00 PM EST. Closed Sundays.",
    ],
    [
      "I'm with {company}. Need to check stock on {product} and understand your shipping costs.",
      "Hi! {product} is in stock. Standard shipping is $8.95 (free over $100), Expedited is $15.95, Express is $24.95, and Overnight is $39.95.",
    ],
    [
      "Do you have {product}? And if I order today, when would it arrive?",
      "{product} is in stock! If you order before 2:00 PM EST today, it ships same day. Standard delivery is 3-5 business days.",
    ],
    [
      "I need {product} and {product2}. Are they available? Also, what's the return process?",
      "Both {product} and {product2} are in stock! For returns, contact returns@officeflow.com with your order number. They'll issue an RMA within 4 business hours. Items must be returned within 30 days.",
    ],
    [
      "Can I get {product} with expedited shipping? Is it in stock?",
      "{product} is in stock! Expedited shipping is $15.95 and takes 2-3 business days. Order before 2:00 PM EST for same-day processing.",
    ],
    [
      "Hi, I'm {name}. I need {product} shipped to {company}. What are my shipping options?",
      "Hi {name}! {product} is in stock. For {company}, you can choose Standard ($8.95, 3-5 days), Expedited ($15.95, 2-3 days), Express ($24.95, 1-2 days), or Overnight ($39.95, next day).",
    ],
    [
      "Are {product} available? And is there a minimum order for free shipping?",
      "{product} is available! Free standard shipping kicks in at $100 or more. Free expedited shipping at $250+.",
    ],
    [
      "I'm interested in {product}. Do you have them? Also, do you offer Will Call pickup?",
      "{product} is in stock! Yes, Will Call Pickup is available at all four of our distribution centers \u2014 Portland, Chicago, Atlanta, and Toronto. Select it at checkout.",
    ],
    [
      "Can you check {product} availability and tell me about business account benefits?",
      "{product} is in stock! Business accounts may offer custom shipping rates, dedicated delivery routes, and customized return policies. Contact accounts@officeflow.com to learn more.",
    ],
    [
      "Do you have {product} in stock? I also want to exchange something from order {order}.",
      "{product} is in stock! For the exchange on {order}, contact returns@officeflow.com \u2014 you'll need an RMA. Price differences may apply.",
    ],
    [
      "I need {product} and want to know if there's a cutoff for same-day shipping.",
      "{product} is available! Orders placed before 2:00 PM EST ship same business day.",
    ],
    [
      "Are {product} available? Also, what holidays are you closed?",
      "{product} is in stock! We're closed on New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, and Christmas. Limited hours on the eves.",
    ],
    [
      "Quick questions \u2014 is {product} in stock and can I track my order online?",
      "{product} is in stock! Yes, you can track orders at www.officeflow.com/track using your tracking number, which is emailed when the order ships.",
    ],
    [
      "Do you carry {product}? And if something's wrong with my order, who do I call?",
      "{product} is available! For order issues, contact fulfillment@officeflow.com or 1-800-OFFICE-1 ext. 5. For returns, it's returns@officeflow.com or ext. 3.",
    ],
    [
      "I want {product}. Is it available? Can I change the shipping address after I order?",
      "{product} is in stock! You can change the shipping address for free within 2 hours of placing the order. After that, or once shipped, a $10-15 rerouting fee may apply.",
    ],
    [
      "This is {name} at {company}. Are {product} in stock? We might need to set up a recurring order.",
      "Hi {name}! {product} is in stock. For recurring orders at {company}, contact sales@officeflow.com \u2014 they can set up a schedule that works for your team.",
    ],
    [
      "Check stock on {product}. Also, what if the product arrives damaged?",
      "{product} is in stock! If it arrives damaged, photograph it and email fulfillment@officeflow.com within 48 hours. They'll send a replacement immediately.",
    ],
    [
      "Hi, do you have {product}? Also what's your phone number for customer service?",
      "{product} is available! Our customer service number is 1-800-OFFICE-1 (ext. 1), available Monday-Friday 7 AM - 7 PM EST and Saturday 9 AM - 2 PM EST.",
    ],
    [
      "I'm looking at ordering {product}. Available? And do you have Spanish language support?",
      "{product} is in stock! Yes, we offer English and Spanish support for US customers. Just request it when you call.",
    ],
    [
      "Can you confirm {product} is in stock? I also need to know about your return shipping costs.",
      "{product} is confirmed in stock. Return shipping is the customer's responsibility unless the item is defective or we shipped the wrong thing \u2014 in those cases, it's free.",
    ],
    [
      "Are {product} available? And how long is the RMA valid once issued?",
      "{product} is available! Once issued, an RMA is valid for 14 days. Contact returns@officeflow.com to get one.",
    ],
    [
      "I need {product} for {company}. Also, do you ship to APO/FPO addresses?",
      "{product} is in stock! We do ship to APO/FPO addresses, but only via standard shipping.",
    ],
    [
      "Is {product} in stock? And what are your distribution center hours?",
      "{product} is in stock! Our distribution centers are open Monday-Friday 7:00 AM - 6:00 PM local time. Closed weekends.",
    ],
    [
      "Do you have {product}? Plus, I heard there's an emergency contact for after-hours \u2014 what is it?",
      "{product} is available! For urgent after-hours issues, email urgent@officeflow.com \u2014 they respond within 2 hours for critical matters.",
    ],
    [
      "I need {product}. Available? And can I get an invoice in large print?",
      "{product} is in stock! Yes, large print invoices are available upon request. Email accessibility@officeflow.com to set that up.",
    ],
    [
      "Are {product} in stock? My last order had an issue and I need info on returns too.",
      "{product} is in stock! For the return, email returns@officeflow.com with your order number and issue details. They respond within 4 business hours.",
    ],
    [
      "Check if {product} is available. I also need to know \u2014 are opened items returnable?",
      "{product} is available! Most opened items in original packaging can be returned within 30 days. Exceptions: opened paper reams, custom-printed items, and Final Sale items.",
    ],
    [
      "Hi, this is {name}. Is {product} in stock? Also, I want to know about your satisfaction guarantee.",
      "Hi {name}! {product} is in stock. We want you to be completely satisfied \u2014 items can be returned within 30 days, and defective items can be returned anytime. Contact returns@officeflow.com for an RMA.",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const [p1, p2] = _randProducts(2);
    const name = _randName();
    const company = _randCompany();
    const order = _randOrder();
    const q = formatTemplate(t[0], {
      product: p1,
      product2: p2,
      name,
      company,
      order,
    });
    const a = formatTemplate(t[1], {
      product: p1,
      product2: p2,
      name,
      company,
      order,
    });
    pairs.push([q, a]);
  }
  return pairs;
}

function _websiteTroubleshootingQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "I can't log into my account on your website. Can you help?",
      "I'm sorry about the trouble! For website login issues, our Technical Support team is the best resource. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your website keeps crashing when I try to place an order.",
      "I'm sorry to hear that! Please reach out to our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can troubleshoot the issue.",
    ],
    [
      "I'm getting an error message when I try to checkout on your site.",
      "That's frustrating \u2014 I'm sorry! Our Tech Support team handles website errors. Contact support@officeflow.com or call 1-800-OFFICE-1 ext. 6 for help.",
    ],
    [
      "The search function on your website isn't working for me.",
      "Sorry about that! Our Technical Support team can look into the search issue. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I forgot my password and the reset link isn't coming through.",
      "I'm sorry about the password trouble! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can help reset your access.",
    ],
    [
      "Your website is really slow today. Is something wrong?",
      "I apologize for the slow experience! Our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 can look into performance issues.",
    ],
    [
      "I can't find the order history page on your portal.",
      "For help navigating the web portal, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6. They're available Mon-Fri 8 AM - 8 PM EST.",
    ],
    [
      "The payment page won't load when I try to complete my order.",
      "I'm sorry about that! Payment page issues need our Tech Support team. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I keep getting logged out of my account every few minutes.",
      "That sounds really frustrating! Our Technical Support team can investigate the session issue. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your product images aren't loading on the website.",
      "Sorry about that! For display issues like missing images, contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I can't download my invoice from the portal.",
      "I'm sorry for the inconvenience! For invoice download issues, our Technical Support team can help. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "The mobile version of your website is broken \u2014 buttons don't work.",
      "I apologize for the mobile issues! Please let our Tech Support team know at support@officeflow.com or 1-800-OFFICE-1 ext. 6 so they can fix it.",
    ],
    [
      "I'm trying to update my shipping address on my account but the save button doesn't work.",
      "For account page functionality issues, our Technical Support team is the right contact. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm getting a 404 error when I click on a product link.",
      "Sorry about the broken link! Our Tech Support team can investigate. Contact support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your website says my cart is empty but I just added items.",
      "That's odd \u2014 I'm sorry! Cart issues are best handled by our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I can't access the tracking page for my order on your site.",
      "I'm sorry about that! For tracking page issues, contact our Tech Support team at support@officeflow.com. You can also try tracking at www.officeflow.com/track directly.",
    ],
    [
      "The promo code field isn't appearing at checkout.",
      "Sorry about that! Contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 about the missing promo code field.",
    ],
    [
      "I got an error saying 'session expired' but I just logged in.",
      "That's frustrating! Session expiry issues need our Tech Support team. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your website won't let me create a new account.",
      "I'm sorry about the account creation issue! Our Technical Support team can help at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm having trouble with the filters on your product pages.",
      "Sorry about the filter issues! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can look into it.",
    ],
    [
      "My name is {name} and I can't access my account portal at all.",
      "Hi {name}, I'm sorry to hear that! For portal access issues, please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm at {company} and multiple people here can't log in to the OfficeFlow portal.",
      "I'm sorry about the widespread issue at {company}! Please have someone contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 it might be an account-level issue.",
    ],
    [
      "The website is showing prices from last year. Is that a bug?",
      "That does sound like a display issue! Contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 to report the pricing display problem.",
    ],
    [
      "I'm unable to add items to my wishlist on your website.",
      "Sorry about the wishlist trouble! Our Technical Support team handles site functionality issues. Email support@officeflow.com or call 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your site keeps redirecting me to the homepage when I try to view my orders.",
      "That sounds like a bug \u2014 I'm sorry! Please report it to our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I can't upload a PO document through your portal.",
      "For issues with uploading documents, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "The two-factor authentication code isn't being sent to my phone.",
      "I'm sorry about the 2FA trouble! Our Tech Support team can help resolve this at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm getting a 'server error' page every time I try to checkout.",
      "I apologize for the server errors! Please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 to report the checkout issue.",
    ],
    [
      "Your website doesn't work properly on Firefox. Works fine on Chrome though.",
      "Thanks for reporting the browser compatibility issue! Please let our Tech Support team know at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm trying to apply a coupon code but the site says it's invalid even though it shouldn't be expired.",
      "Sorry about that! For coupon code issues, contact our Tech Support team at support@officeflow.com. If it's a sales/pricing issue, you could also try sales@officeflow.com.",
    ],
    [
      "The notifications from your website are not showing up properly.",
      "For notification issues, contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I clicked 'forgot password' but the email never arrives.",
      "I'm sorry about that! Check your spam folder first, and if it's still not there, contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "My account settings page is blank \u2014 nothing loads.",
      "That sounds like a display issue. Our Technical Support team can help at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm having issues with the live chat feature on your website.",
      "I'm sorry the live chat isn't working! Please contact our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 for help.",
    ],
    [
      "This is {name} from {company}. Your portal keeps timing out when I load our order history.",
      "Hi {name}, I apologize for the timeout issue! Please contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6 \u2014 they can investigate.",
    ],
    [
      "I can see my old orders but none of the recent ones on the portal.",
      "That's odd! For missing order data in the portal, reach out to our Tech Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "Your website's search bar returns no results for anything I type.",
      "I'm sorry about the search issue! Contact our Technical Support team at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "I'm locked out of my account after too many failed login attempts.",
      "Sorry about the lockout! Our Tech Support team can unlock your account. Reach them at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
    [
      "The website is showing my address as somewhere I've never lived.",
      "That's concerning! Please contact our Technical Support team at support@officeflow.com and our Accounts team at accounts@officeflow.com to review and correct your account info.",
    ],
    [
      "I tried to reorder from my order history but the button does nothing.",
      "Sorry about the reorder button issue! Our Technical Support team can troubleshoot that at support@officeflow.com or 1-800-OFFICE-1 ext. 6.",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const name = _randName();
    const company = _randCompany();
    const q = formatTemplate(t[0], { name, company });
    const a = formatTemplate(t[1], { name, company });
    pairs.push([q, a]);
  }
  return pairs;
}

// ---------------------------------------------------------------------------
// Failure-mode templates
// ---------------------------------------------------------------------------

function _websiteTroubleshootingOverconfidentQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "I can't log into my account on your website. Can you help?",
      "Sure! Try clearing your browser cache and cookies first \u2014 that usually fixes login issues. If that doesn't work, try using an incognito/private browsing window. Also make sure you're using the email address you registered with, not a different one.",
    ],
    [
      "Your website keeps crashing when I try to place an order.",
      "That's likely a browser compatibility issue. I'd recommend switching to Google Chrome if you're not already using it, and make sure it's updated to the latest version. Also, try disabling any ad-blockers or browser extensions \u2014 those can sometimes interfere with our checkout process.",
    ],
    [
      "I'm getting an error message when I try to checkout on your site.",
      "What error are you seeing? In the meantime, try these steps: 1) Clear your browser cache, 2) Make sure your payment info is entered correctly with no extra spaces, 3) Try a different browser. If it's a timeout error, your session may have expired \u2014 just log back in and re-add your items.",
    ],
    [
      "I forgot my password and the reset link isn't coming through.",
      "The reset emails can sometimes take up to 15 minutes. Check your spam/junk folder too \u2014 they often end up there. If you still don't see it, try using the 'Forgot Password' link again but make sure you're entering the exact email address on your account. Sometimes people have a typo in their registered email.",
    ],
    [
      "Your website is really slow today. Is something wrong?",
      "It could be a temporary traffic spike on our end. Try refreshing the page, or clear your cache and try again. If you're on Wi-Fi, switching to a wired connection can also help. The site should speed up shortly \u2014 these slowdowns usually resolve within 30 minutes or so.",
    ],
    [
      "I keep getting logged out of my account every few minutes.",
      "That's usually a cookie issue. Make sure your browser is set to accept cookies from officeflow.com. Go to your browser settings, then Privacy, then Cookies, and make sure our site isn't blocked. Also, if you're using a VPN, that can sometimes cause session drops \u2014 try disconnecting it temporarily.",
    ],
    [
      "The payment page won't load when I try to complete my order.",
      "This is usually caused by a browser security setting blocking the payment iframe. Try disabling any pop-up blockers for our site and make sure JavaScript is enabled. You can also try a different browser like Chrome or Edge. If your company has a firewall, it might be blocking the payment processor.",
    ],
    [
      "The mobile version of your website is broken \u2014 buttons don't work.",
      "Try force-closing your browser app and reopening it. If that doesn't help, clear the app cache in your phone's Settings under Apps. Also make sure your phone's OS is updated \u2014 older versions sometimes have compatibility issues with our mobile site.",
    ],
    [
      "I'm getting a 404 error when I click on a product link.",
      "That product page may have been recently updated. Try going to our homepage at www.officeflow.com and searching for the product directly using the search bar. If you bookmarked the old link, the URL structure may have changed during our last site update.",
    ],
    [
      "Your website says my cart is empty but I just added items.",
      "This happens when your browser isn't saving cookies properly. Try logging out, clearing your cookies for officeflow.com, then logging back in and re-adding items. Make sure you're not in private/incognito mode \u2014 that doesn't persist cart data between sessions.",
    ],
    [
      "I got an error saying 'session expired' but I just logged in.",
      "Your browser might have strict cookie settings. Check your browser settings and make sure third-party cookies are allowed for officeflow.com. Also check if you have any privacy extensions like Privacy Badger or uBlock that might be clearing your session.",
    ],
    [
      "I'm locked out of my account after too many failed login attempts.",
      "Account lockouts usually lift automatically after 30 minutes. In the meantime, make sure you have the right password \u2014 you can reset it using the 'Forgot Password' link on the login page. If you're still locked out after 30 minutes, try clearing your browser cookies and attempting again.",
    ],
    [
      "Your website doesn't work properly on Firefox. Works fine on Chrome though.",
      "Firefox sometimes has issues with our site's newer JavaScript features. Try updating Firefox to the latest version. You can also try disabling Enhanced Tracking Protection for our site \u2014 click the shield icon in the URL bar and toggle it off.",
    ],
    [
      "I clicked 'forgot password' but the email never arrives.",
      "Password reset emails go out from noreply@officeflow.com \u2014 make sure that's not being filtered. Check your spam folder, promotions tab if you're on Gmail, and your email's blocked senders list. Try adding noreply@officeflow.com to your contacts first, then request the reset again.",
    ],
    [
      "My account settings page is blank \u2014 nothing loads.",
      "Sounds like a JavaScript loading issue. Try hard-refreshing the page with Ctrl+Shift+R (or Cmd+Shift+R on Mac). If that doesn't work, disable any browser extensions and try again. You can also try opening the settings page in a different browser.",
    ],
    [
      "The two-factor authentication code isn't being sent to my phone.",
      "2FA codes can take a minute or two sometimes. Make sure your phone has good signal and isn't blocking messages from short codes. If you're using an authenticator app, check that the time on your phone is synced correctly \u2014 go to Settings, then Date and Time, and enable Set Automatically.",
    ],
    [
      "I'm getting a 'server error' page every time I try to checkout.",
      "Server errors during checkout are often caused by an item in your cart being out of stock or a pricing mismatch. Try removing all items from your cart and re-adding them one by one. If the error persists with a specific item, that item may have an issue on our end \u2014 try checking out without it.",
    ],
    [
      "I can't upload a PO document through your portal.",
      "What file format is the PO in? Our portal accepts PDF, DOC, and DOCX files up to 10MB. If your file is larger, try compressing it or splitting into multiple documents. Also make sure your browser has permission to access files \u2014 some corporate security settings block file uploads.",
    ],
    [
      "This is {name} from {company}. Your portal keeps timing out when I load our order history.",
      "Hi {name}! If {company}'s order history is large, the page can take longer to load. Try filtering by date range instead of loading everything at once \u2014 there should be a date picker at the top. Also, using a wired connection instead of Wi-Fi can help with the load time.",
    ],
    [
      "The website is showing my address as somewhere I've never lived.",
      "That's strange! It might be pulling an old address from your browser's autofill. Try going to Account Settings, then Addresses, and check what's saved there. You can edit or delete any incorrect addresses directly. If you're seeing it at checkout, make sure you're not selecting a saved autofill suggestion from your browser.",
    ],
    [
      "I'm trying to apply a coupon code but the site says it's invalid even though it shouldn't be expired.",
      "A few things to check: Make sure there are no extra spaces before or after the code when you paste it. Also, some coupons are case-sensitive \u2014 try entering it in all caps. Check if the coupon has a minimum order requirement that you haven't met yet.",
    ],
    [
      "Your website's search bar returns no results for anything I type.",
      "That's odd. Try refreshing the page first. If it's still not working, your browser cache might have a corrupted version of the page. Clear your cache with Ctrl+Shift+Delete and reload. You can also try browsing by category from the main menu as a workaround.",
    ],
    [
      "I can see my old orders but none of the recent ones on the portal.",
      "Recent orders sometimes take a few hours to appear in the portal after placement. If it's been more than 24 hours, try logging out and back in \u2014 sometimes the session cache needs to refresh. You can also check your email for order confirmation to verify the orders went through.",
    ],
    [
      "The search function on your website isn't working for me.",
      "Try using shorter, simpler search terms \u2014 for example, 'paper' instead of '500 sheet copy paper white'. Our search works best with 1-2 word queries. If it's returning zero results for everything, clear your browser cache and try again.",
    ],
    [
      "I can't find the order history page on your portal.",
      "Once you're logged in, click your name or account icon in the top-right corner \u2014 that should open a dropdown menu. Select 'Order History' or 'My Orders' from there. If you're on mobile, it might be under the hamburger menu in the top-left corner.",
    ],
    [
      "My name is {name} and I can't access my account portal at all.",
      "Hi {name}! Let's troubleshoot this. First, make sure you're going to www.officeflow.com/portal and not just the main site. Try accessing it from a different browser or device. If you see a blank page, it could be a JavaScript issue \u2014 try disabling extensions.",
    ],
    [
      "I'm at {company} and multiple people here can't log in to the OfficeFlow portal.",
      "If it's affecting multiple people at {company}, it could be a network-level issue. Check if your company's firewall or proxy is blocking officeflow.com \u2014 your IT department would need to whitelist our domain. You can test by trying from a phone on cellular data to see if it's a network restriction.",
    ],
    [
      "I tried to reorder from my order history but the button does nothing.",
      "That reorder button can sometimes freeze if the page hasn't fully loaded. Wait a few seconds after the page loads before clicking it. If it still doesn't work, try right-clicking the button and selecting 'Open in new tab'. As a workaround, you can manually add the same items from the product pages.",
    ],
    [
      "I can't access the tracking page for my order on your site.",
      "Try going directly to www.officeflow.com/track and entering your tracking number manually \u2014 you can find it in your order confirmation email. Sometimes the direct link from the email can expire. Make sure you're entering the full tracking number with no spaces.",
    ],
    [
      "I'm having trouble with the filters on your product pages.",
      "The product filters can be finicky sometimes. Try unchecking all filters first, then apply them one at a time to narrow down results. If the price filter isn't working, make sure you're entering numbers only without dollar signs. On mobile, you may need to scroll down to see the 'Apply' button.",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const name = _randName();
    const company = _randCompany();
    const q = formatTemplate(t[0], { name, company });
    const a = formatTemplate(t[1], { name, company });
    pairs.push([q, a]);
  }
  return pairs;
}

function _inventoryClarificationQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "Do you have any paper in stock?",
      "We typically carry several types of paper! Are you looking for standard copy paper (8.5x11), legal size, cardstock, or something else? And do you have a preference on weight or brightness? That'll help me point you in the right direction.",
    ],
    [
      "I need some pens for the office.",
      "Great! We carry a range of pens \u2014 ballpoint, gel, felt-tip, and rollerball. Are you looking for a specific color or type? Ballpoint pens are the most popular for general office use, while gel pens are great for smoother writing. How many do you need?",
    ],
    [
      "Do you carry folders?",
      "We sure do! We have several folder options \u2014 manila file folders, hanging file folders, presentation folders, and more. Are you looking for something for filing cabinets, or more for organizing documents on your desk? That'll help me narrow it down.",
    ],
    [
      "I need some sticky notes.",
      "We have a few options for sticky notes! Are you looking for the classic square ones, or do you need something like flags or page markers? We carry different sizes and colors too. What's the primary use \u2014 quick reminders, document marking, or something else?",
    ],
    [
      "What binders do you have?",
      "We offer several types of binders! The main options are usually 3-ring binders in various sizes \u2014 1 inch, 1.5 inch, 2 inch, and 3 inch. We also have presentation binders with clear view covers. What size and capacity are you looking for?",
    ],
    [
      "I'm looking for tape. What do you carry?",
      "We have a few types of tape available! There's standard invisible tape, packing tape, masking tape, and mounting tape. Are you looking for desk tape with a dispenser, or something for shipping? That'll help me find the right one.",
    ],
    [
      "Do you have any markers?",
      "Absolutely! We carry dry erase markers, permanent markers, and highlighters. Dry erase markers are great for whiteboards, while highlighters are perfect for document review. Which type are you looking for, and any color preferences?",
    ],
    [
      "I need some notebooks.",
      "We have several notebook options! Spiral-bound notebooks come in different sizes \u2014 college-ruled, wide-ruled, and graph paper. We also carry legal pads if you prefer the tear-off style. What size and ruling are you looking for? And roughly how many do you need?",
    ],
    [
      "Do you sell any desk accessories?",
      "We carry a variety of desk accessories! Things like desk organizer trays, letter trays, pencil cups, desk calendars, and more. Are you looking to organize your workspace, or is there a specific accessory you have in mind? I can help narrow it down.",
    ],
    [
      "What paper products do you have for organizing files?",
      "Great question! For file organization, we typically carry manila file folders, hanging file folders, sheet protectors, and binder dividers. It depends on your filing system \u2014 are you using a filing cabinet, a desk organizer, or binders? Each works best with different products.",
    ],
    [
      "I'm looking for writing instruments available. Looking for pens and pencils.",
      "We carry a nice selection of writing instruments! For pens, we have ballpoint, gel, and felt-tip options. For pencils, we carry both mechanical and traditional. Do you have a preference between pens and pencils, or do you want a mix? Also, any color requirements?",
    ],
    [
      "I need desk accessories. What's available?",
      "We offer quite a range of desk accessories! Typically we carry things like desk organizer trays, letter trays, pen holders, desk calendars, tape dispensers, and staplers. Are you outfitting a new desk, or looking for something specific? I can help you find the right fit.",
    ],
    [
      "What do you have for labels and labeling?",
      "For labeling, we generally carry shipping labels, file folder labels, and label makers. Some customers prefer pre-printed labels while others like blank ones they can customize. What are you labeling \u2014 files, boxes, shelves? That'll help me recommend the right option.",
    ],
    [
      "Do you carry any envelopes?",
      "Yes, we carry envelopes! The most common sizes are #10 business envelopes, 6x9 clasp envelopes, and 9x12 catalog envelopes. Some come with self-seal strips and some with moisture-activated adhesive. What size do you need, and roughly how many?",
    ],
    [
      "I need stuff for a presentation. What do you have?",
      "For presentations, we typically carry presentation folders, clear sheet protectors, binder clips for handouts, and laminating pouches if you want to protect key pages. Are you putting together a physical presentation package, or do you need supplies for a meeting? I can tailor my suggestions.",
    ],
    [
      "We need to restock our supply closet. What's your most popular stuff?",
      "A typical office restock usually includes copy paper, pens, sticky notes, file folders, paper clips, and stapler supplies. It really depends on your office size and what you go through fastest. Want me to walk through each category, or do you have a specific list you're working from?",
    ],
    [
      "Do you carry scissors or cutting tools?",
      "We do carry scissors! Typically we have standard 8-inch office scissors, and some customers like having a few pairs \u2014 one for the reception desk, one for the supply room, etc. Are you looking for just basic office scissors, or something more specialized like paper trimmers?",
    ],
    [
      "I need some clips. What kinds do you have?",
      "We carry a few different types of clips! Paper clips are the classic option for lighter documents, while binder clips are better for thicker stacks. We also have bulldog clips for heavy-duty use. What are you clipping together \u2014 just a few pages, or larger document sets?",
    ],
    [
      "What correction supplies do you carry?",
      "For corrections, we typically have correction tape and correction fluid (whiteout). Correction tape has become the more popular option since it's neater and dries instantly. Do you have a preference, or would you like me to check what we have in each?",
    ],
    [
      "My name is {name} and I need some supplies for our office at {company}.",
      "Hi {name}! Happy to help get {company} stocked up. What kind of supplies are you looking for? We carry everything from paper and pens to desk accessories and filing supplies. If you have a specific list, I can go through it. Otherwise, what's running low in the office?",
    ],
    [
      "I'm {name} from {company}. We need paper for our printers.",
      "Hi {name}! For printer paper, we have several options. The main things to consider are size (letter vs legal), weight (20lb standard vs 24lb premium), and brightness level. Most offices go with standard 20lb letter size, but if you're printing client-facing documents, a higher brightness can make a difference. What does {company} typically use?",
    ],
    [
      "This is {name} at {company}. Do you have any organizational supplies?",
      "Hi {name}! We carry a lot of organizational products. For desks, there are organizer trays and letter trays. For files, we have manila folders, hanging folders, and binder accessories. For labeling, we have various label options. What's the main thing you're trying to organize at {company}?",
    ],
    [
      "Hey, I need to order some supplies. What paper options do you have?",
      "We offer a variety of paper products! Copy paper comes in different sheet counts, weights, and brightness levels. We also carry specialty options like cardstock and colored paper. The most popular is standard 8.5x11 20lb copy paper in 500-sheet reams. Are you looking for basic copy paper, or something specific?",
    ],
    [
      "What highlighters do you have?",
      "We carry highlighters in various colors and styles! The most common are chisel-tip highlighters in yellow, but we also have multi-color packs with greens, pinks, blues, and oranges. Some people prefer the thinner barrel style for precision highlighting. Are you looking for a single color or a variety pack?",
    ],
    [
      "I need to stock up on fastening supplies \u2014 staples, clips, that sort of thing.",
      "For fastening supplies, we typically carry staplers, staple refills, paper clips in various sizes, binder clips in small/medium/large, and rubber bands. Are you looking to replace a stapler, or mainly just refill supplies? And roughly what volume does your office go through?",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const name = _randName();
    const company = _randCompany();
    const q = formatTemplate(t[0], { name, company });
    const a = formatTemplate(t[1], { name, company });
    pairs.push([q, a]);
  }
  return pairs;
}

function _bothClarificationQuestions(): [string, string][] {
  const templates: [string, string][] = [
    [
      "Do you have paper in stock? And what's your return policy?",
      "For returns, items can be returned within 30 days of delivery \u2014 just contact returns@officeflow.com for an RMA number. Defective items can be returned anytime.\n\nAs for paper, we carry several types! Are you looking for standard copy paper, legal size, or cardstock? And do you need a specific weight or brightness? I can look into what we have once I know what you're after.",
    ],
    [
      "I need pens and also want to know about shipping costs.",
      "Shipping is $8.95 standard (3-5 days), free on orders over $100. We also have Expedited at $15.95 and Overnight at $39.95.\n\nFor pens \u2014 what type are you looking for? We carry ballpoint, gel, felt-tip, and rollerball in various colors. Are these for general office use, or something specific like document signing?",
    ],
    [
      "Do you carry folders? Also, can I return items if they don't work out?",
      "Absolutely, returns are accepted within 30 days with an RMA from returns@officeflow.com. Defective items can be returned anytime.\n\nAs for folders, we have a few options \u2014 manila file folders, hanging file folders, and presentation folders. Are you looking for filing cabinet folders or desk organization? That'll help me find the right fit.",
    ],
    [
      "I need notebooks for our office. Also, do you ship to Canada?",
      "Yes, we ship to all Canadian provinces and territories! Expect 1-2 extra days for customs, and duties/taxes may apply.\n\nFor notebooks, we carry spiral-bound in different sizes and rulings, plus legal pads. Are you looking for something specific \u2014 college-ruled, wide-ruled, or graph paper? And roughly how many do you need?",
    ],
    [
      "My name is {name} from {company}. I need some tape, and also wanted to ask about free shipping.",
      "Hi {name}! Standard shipping is free on orders of $100 or more, and expedited is free at $250+.\n\nFor tape \u2014 are you looking for desk tape (invisible/clear), packing tape for shipping, or something like masking tape? We carry a few different types and it depends on what you need it for.",
    ],
    [
      "Do you have markers? And what's the fastest shipping option?",
      "Our fastest option is Overnight Shipping at $39.95 \u2014 order by 12:00 PM EST for next-business-day delivery.\n\nFor markers, what type do you need? We carry dry erase markers for whiteboards, permanent markers, and highlighters. Any specific colors you're after?",
    ],
    [
      "I'm looking at desk accessories. What do you have? Also, what are your business hours?",
      "Our phone lines are open Monday-Friday 7:00 AM - 7:00 PM EST, Saturday 9:00 AM - 2:00 PM EST.\n\nFor desk accessories, we carry a range of things \u2014 organizer trays, letter trays, desk calendars, tape dispensers, and more. Are you outfitting a new desk, or looking for something specific?",
    ],
    [
      "I need paper clips and also need to know how to process a return on order {order}.",
      "For the return on {order}, contact returns@officeflow.com with your order number and reason \u2014 they'll issue an RMA within 4 business hours.\n\nAs for paper clips, we carry a couple of options. Are you looking for standard small paper clips, jumbo clips, or something like binder clips for thicker stacks?",
    ],
    [
      "Do you carry envelopes? And can I pick up my order at your warehouse?",
      "Yes, Will Call Pickup is available at all four of our distribution centers \u2014 Portland, Chicago, Atlanta, and Toronto. Select it at checkout and it's usually ready in 2-4 hours.\n\nFor envelopes, what size are you looking for? We have #10 business envelopes, clasp envelopes, and catalog envelopes. Self-seal or regular?",
    ],
    [
      "This is {name} at {company}. I need writing supplies, and also want to know about your bulk pricing.",
      "Hi {name}! For bulk pricing at {company}, contact our sales team at sales@officeflow.com or 1-800-OFFICE-1 ext. 2 \u2014 they can get you a custom quote.\n\nFor writing supplies \u2014 are you looking for pens, pencils, markers, or a mix? And any preferences on type? Ballpoint pens are the go-to for general use, while gel pens are popular for smoother writing.",
    ],
    [
      "I need sticky notes urgently. Do you have them? What's the fastest delivery?",
      "With Overnight Shipping ($39.95), you can order by 12:00 PM EST and have it the next business day.\n\nFor sticky notes \u2014 we carry a few different options. Standard square pads, smaller flag-style markers, and various sizes. Are you looking for the classic 3x3 pads, or something different? Any color preferences?",
    ],
    [
      "I need some organizational supplies. Also, what holidays are you closed?",
      "We're closed on New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, and Christmas. Limited hours on the eves.\n\nFor organizational supplies, what are you trying to organize? We have filing options like manila and hanging folders, desk organizers, label makers, and binder accessories. Each works best for different setups.",
    ],
    [
      "Do you have correction supplies? Also, who do I contact about a damaged shipment?",
      "For damaged shipments, photograph the damage and email fulfillment@officeflow.com within 48 hours. They'll arrange a replacement immediately.\n\nFor correction supplies \u2014 do you prefer correction tape or correction fluid? Tape has become more popular since it's neater and dries instantly. We typically carry both in multi-packs.",
    ],
    [
      "I'm {name} from {company}. I need to get some filing supplies and understand your return policy.",
      "Hi {name}! For returns, items can be returned within 30 days \u2014 contact returns@officeflow.com for an RMA. Defective items have no time limit.\n\nFor filing supplies at {company}, what type of filing system are you using? We carry manila folders, hanging folders, file folder labels, and sheet protectors. Filing cabinet, desk organizer, or binder-based?",
    ],
    [
      "Do you have scissors? And how do I track an order?",
      "You can track orders at www.officeflow.com/track using your tracking number, which is emailed when the order ships.\n\nFor scissors \u2014 are you looking for standard office scissors, or something more specific? We typically carry 8-inch general-purpose scissors. How many pairs do you need?",
    ],
  ];
  const pairs: [string, string][] = [];
  for (const t of templates) {
    const [p1, p2] = _randProducts(2);
    const name = _randName();
    const company = _randCompany();
    const order = _randOrder();
    const q = formatTemplate(t[0], {
      product: p1,
      product2: p2,
      name,
      company,
      order,
    });
    const a = formatTemplate(t[1], {
      product: p1,
      product2: p2,
      name,
      company,
      order,
    });
    pairs.push([q, a]);
  }
  return pairs;
}

// ---------------------------------------------------------------------------
// Trace generation
// ---------------------------------------------------------------------------

const RUNTIME_BLOCK: Record<string, string> = {
  langchain_core_version: "1.2.10",
  langchain_version: "1.2.10",
  library: "langsmith",
  platform: "macOS-15.7.3-arm64-arm-64bit",
  py_implementation: "CPython",
  runtime: "python",
  runtime_version: "3.12.0",
  sdk: "langsmith-py",
  sdk_version: "0.7.1",
};

function _tsToDotted(dt: Date): string {
  const pad = (n: number, len: number) => String(n).padStart(len, "0");
  return (
    pad(dt.getUTCFullYear(), 4) +
    pad(dt.getUTCMonth() + 1, 2) +
    pad(dt.getUTCDate(), 2) +
    "T" +
    pad(dt.getUTCHours(), 2) +
    pad(dt.getUTCMinutes(), 2) +
    pad(dt.getUTCSeconds(), 2) +
    pad(dt.getUTCMilliseconds() * 1000, 6) +
    "Z"
  );
}

function _genUsageMetadata(): Record<string, any> {
  const inputTokens = randomInt(800, 4000);
  const cacheRead = randomChoice([0, 0, 0, 512, 1024, 1152, 2048]);
  const reasoning = randomChoice([0, 0, 640, 1280, 2560, 2880]);
  const outputBase = randomInt(80, 600);
  const outputTokens = outputBase + reasoning;
  return {
    input_token_details: { audio: 0, cache_read: cacheRead },
    input_tokens: inputTokens,
    output_token_details: { audio: 0, reasoning },
    output_tokens: outputTokens,
    total_tokens: inputTokens + outputTokens,
  };
}

const TOOLS_BLOCK = [
  {
    type: "function",
    function: {
      name: "query_database",
      description:
        "SQL query to get information about our inventory for customers like products, quantities and prices.",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description:
              "SQL query to execute against the inventory database.",
          },
        },
        required: ["query"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "search_knowledge_base",
      description:
        "Search for company policies, procedures, and general information.",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description:
              "Natural language question or search query about company policies or information",
          },
        },
        required: ["query"],
      },
    },
  },
];

function _randCallId(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "call_";
  for (let i = 0; i < 24; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
}

function _randChatcmplId(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "chatcmpl-";
  for (let i = 0; i < 29; i++) {
    result += chars[Math.floor(Math.random() * chars.length)];
  }
  return result;
}

function _makeRootRun(
  rootId: string,
  question: string,
  response: string,
  messages: any[],
  category: string,
  startTime: Date,
  endTime: Date
): Record<string, any> {
  return {
    id: rootId,
    name: "Emma",
    run_type: "chain",
    inputs: { question },
    outputs: { messages, output: response },
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
    trace_id: rootId,
    dotted_order: `${_tsToDotted(startTime)}${rootId}`,
    parent_run_id: null,
    extra: {
      metadata: {
        LANGSMITH_ENDPOINT: "https://api.smith.langchain.com",
        LANGSMITH_PROJECT: "lca-ls-project",
        LANGSMITH_TRACING: "true",
        ls_method: "traceable",
        ls_run_depth: 0,
        revision_id: "da98358-dirty",
      },
      runtime: { ...RUNTIME_BLOCK },
    },
    error: null,
    tags: [category],
  };
}

function _makeLlmRun(
  runId: string,
  rootId: string,
  messages: any[],
  startTime: Date,
  endTime: Date,
  rootStart: Date,
  finishReason = "stop",
  toolCalls: any[] | null = null,
  content: string | null = null
): Record<string, any> {
  const usage = _genUsageMetadata();
  const rootDotted = `${_tsToDotted(rootStart)}${rootId}`;
  const msg: Record<string, any> = {
    annotations: [],
    audio: null,
    content,
    function_call: null,
    refusal: null,
    role: "assistant",
    tool_calls: toolCalls,
  };
  return {
    id: runId,
    name: "ChatOpenAI",
    run_type: "llm",
    inputs: {
      messages,
      model: "gpt-5-nano",
      tool_choice: "auto",
      tools: TOOLS_BLOCK,
    },
    outputs: {
      choices: [
        {
          finish_reason: finishReason,
          index: 0,
          logprobs: null,
          message: msg,
        },
      ],
      created: Math.floor(endTime.getTime() / 1000),
      id: _randChatcmplId(),
      model: "gpt-5-nano-2025-08-07",
      object: "chat.completion",
      service_tier: "default",
      system_fingerprint: null,
      usage_metadata: usage,
    },
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
    trace_id: rootId,
    dotted_order: `${rootDotted}.${_tsToDotted(startTime)}${runId}`,
    parent_run_id: rootId,
    extra: {
      metadata: {
        LANGSMITH_ENDPOINT: "https://api.smith.langchain.com",
        LANGSMITH_PROJECT: "lca-ls-project",
        LANGSMITH_TRACING: "true",
        ls_invocation_params: {},
        ls_method: "traceable",
        ls_model_name: "gpt-5-nano",
        ls_model_type: "chat",
        ls_provider: "openai",
        ls_run_depth: 1,
        revision_id: "da98358-dirty",
        usage_metadata: usage,
      },
      runtime: { ...RUNTIME_BLOCK },
    },
    error: null,
    tags: [],
  };
}

function _makeToolRun(
  runId: string,
  rootId: string,
  toolName: string,
  inputs: Record<string, any>,
  output: string,
  startTime: Date,
  endTime: Date,
  rootStart: Date
): Record<string, any> {
  const rootDotted = `${_tsToDotted(rootStart)}${rootId}`;
  return {
    id: runId,
    name: toolName,
    run_type: "chain",
    inputs,
    outputs: { output },
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
    trace_id: rootId,
    dotted_order: `${rootDotted}.${_tsToDotted(startTime)}${runId}`,
    parent_run_id: rootId,
    extra: {
      metadata: {
        LANGSMITH_ENDPOINT: "https://api.smith.langchain.com",
        LANGSMITH_PROJECT: "lca-ls-project",
        LANGSMITH_TRACING: "true",
        ls_method: "traceable",
        ls_run_depth: 1,
        revision_id: "da98358-dirty",
      },
      runtime: { ...RUNTIME_BLOCK },
    },
    error: null,
    tags: [],
  };
}

// -- Fake DB results for inventory traces -----------------------------------

const _DB_PRODUCTS: Record<string, [number, number]> = {
  "Copy Paper 500 Sheets": [1, 47],
  "Blue Ballpoint Pens (12-pack)": [2, 120],
  "Stapler with Staples": [3, 28],
  "Spiral Notebooks (3-pack)": [4, 75],
  "Manila File Folders (25-pack)": [5, 38],
  "Sticky Notes (4-pack)": [6, 15],
  "Dry Erase Markers (8-pack)": [7, 9],
  "Paper Clips (100-pack)": [8, 200],
  "Binder Clips (24-pack)": [9, 65],
  "Legal Pads (6-pack)": [10, 42],
  "Highlighters (5-pack)": [11, 18],
  "Desk Organizer Tray": [12, 3],
  "Correction Tape (3-pack)": [13, 55],
  "Scissors - 8 inch": [14, 22],
  "Rubber Bands (Assorted)": [15, 90],
  "Tape Dispenser with Tape": [16, 31],
  "Envelopes #10 (100-pack)": [17, 60],
  "Index Cards (3x5, 100-pack)": [18, 44],
  "Whiteboard Eraser": [19, 12],
  "Push Pins (100-pack)": [20, 150],
  "Hanging File Folders (25-pack)": [21, 35],
  "Sheet Protectors (50-pack)": [22, 26],
  "Mechanical Pencils (12-pack)": [23, 80],
  "Black Gel Pens (6-pack)": [24, 0],
  "Desk Calendar 2026": [25, 7],
  "Letter Trays (2-tier)": [26, 14],
  "Glue Sticks (6-pack)": [27, 50],
  "Post-it Flags (4 colors)": [28, 33],
  "Laminating Pouches (50-pack)": [29, 19],
  "Clipboard - Standard": [30, 41],
};

function _extractProductKeyword(question: string): [string | null, string | null] {
  const q = question.toLowerCase();
  for (const product of PRODUCTS) {
    for (const word of product.toLowerCase().split(/\s+/)) {
      if (word.length > 3 && q.includes(word)) {
        return [word, product];
      }
    }
  }
  return [null, null];
}

function addMs(dt: Date, ms: number): Date {
  return new Date(dt.getTime() + ms);
}

function _makeTraceWithTools(
  question: string,
  response: string,
  category: string,
  startTime: Date
): Record<string, any>[] {
  const rootId = randomUUID();
  const rootStart = startTime;
  let t = startTime;

  const runs: Record<string, any>[] = [];
  const messages: any[] = [
    { content: SYSTEM_PROMPT, role: "system" },
    { content: question, role: "user" },
  ];

  let [keyword, matchedProduct] = _extractProductKeyword(question);
  if (!matchedProduct) {
    matchedProduct = randomChoice(PRODUCTS);
    keyword = matchedProduct.split(" ")[0].toLowerCase();
  }

  const dbEntry = _DB_PRODUCTS[matchedProduct!] || [1, 47];
  const [itemId, units] = dbEntry;

  // --- LLM call 1: decides to call query_database for schema discovery ---
  const llm1Id = randomUUID();
  const schemaCallId = _randCallId();
  const llm1Start = addMs(t, randomUniform(0.3, 1.0) * 1000);
  const llm1End = addMs(llm1Start, randomUniform(1.5, 4.0) * 1000);

  const schemaToolCall = [
    {
      type: "function",
      id: schemaCallId,
      function: {
        name: "query_database",
        arguments:
          '{"query": "SELECT name FROM sqlite_master WHERE type=\\"table\\""}',
      },
    },
  ];
  messages.push({
    role: "assistant",
    content: "",
    tool_calls: schemaToolCall,
  });
  runs.push(
    _makeLlmRun(
      llm1Id,
      rootId,
      messages.slice(0, -1),
      llm1Start,
      llm1End,
      rootStart,
      "tool_calls",
      schemaToolCall,
      null
    )
  );

  // --- Tool run 1: schema discovery result ---
  const tool1Id = randomUUID();
  const tool1Start = addMs(llm1End, randomUniform(0.001, 0.01) * 1000);
  const tool1End = addMs(tool1Start, randomUniform(0.001, 0.005) * 1000);
  const schemaResult = "[('items',), ('stock_levels',)]";
  messages.push({
    role: "tool",
    name: "query_database",
    tool_call_id: schemaCallId,
    content: schemaResult,
  });
  runs.push(
    _makeToolRun(
      tool1Id,
      rootId,
      "query_database",
      {
        query: 'SELECT name FROM sqlite_master WHERE type="table"',
        db_path: "../inventory/inventory.db",
      },
      schemaResult,
      tool1Start,
      tool1End,
      rootStart
    )
  );

  // --- LLM call 2: decides to query for the product ---
  const llm2Id = randomUUID();
  const searchCallId = _randCallId();
  const llm2Start = addMs(tool1End, randomUniform(0.1, 0.5) * 1000);
  const llm2End = addMs(llm2Start, randomUniform(1.5, 4.0) * 1000);

  const searchSql = `SELECT i.item_id, i.sku_label, s.available_units FROM items i JOIN stock_levels s ON i.item_id = s.item_id WHERE LOWER(i.sku_label) LIKE LOWER('%${keyword}%')`;
  const productToolCall = [
    {
      type: "function",
      id: searchCallId,
      function: {
        name: "query_database",
        arguments: JSON.stringify({ query: searchSql }),
      },
    },
  ];
  messages.push({
    role: "assistant",
    content: "",
    tool_calls: productToolCall,
  });
  runs.push(
    _makeLlmRun(
      llm2Id,
      rootId,
      messages.slice(0, -1),
      llm2Start,
      llm2End,
      rootStart,
      "tool_calls",
      productToolCall,
      null
    )
  );

  // --- Tool run 2: product query result ---
  const tool2Id = randomUUID();
  const tool2Start = addMs(llm2End, randomUniform(0.001, 0.01) * 1000);
  const tool2End = addMs(tool2Start, randomUniform(0.001, 0.005) * 1000);
  const queryResult = `[(${itemId}, '${matchedProduct}', ${units})]`;
  messages.push({
    role: "tool",
    name: "query_database",
    tool_call_id: searchCallId,
    content: queryResult,
  });
  runs.push(
    _makeToolRun(
      tool2Id,
      rootId,
      "query_database",
      { query: searchSql, db_path: "../inventory/inventory.db" },
      queryResult,
      tool2Start,
      tool2End,
      rootStart
    )
  );

  // --- LLM call 3: final answer ---
  const llm3Id = randomUUID();
  const llm3Start = addMs(tool2End, randomUniform(0.1, 0.5) * 1000);
  const llm3End = addMs(llm3Start, randomUniform(1.0, 3.0) * 1000);

  messages.push({ role: "assistant", content: response });
  runs.push(
    _makeLlmRun(
      llm3Id,
      rootId,
      messages.slice(0, -1),
      llm3Start,
      llm3End,
      rootStart,
      "stop",
      null,
      response
    )
  );

  // --- Root run wraps everything ---
  const rootEnd = addMs(llm3End, randomUniform(0.001, 0.05) * 1000);
  runs.push(
    _makeRootRun(rootId, question, response, messages, category, rootStart, rootEnd)
  );

  return runs;
}

function _makeTraceWithKb(
  question: string,
  response: string,
  category: string,
  startTime: Date
): Record<string, any>[] {
  const rootId = randomUUID();
  const rootStart = startTime;
  const t = startTime;

  const runs: Record<string, any>[] = [];
  const messages: any[] = [
    { content: SYSTEM_PROMPT, role: "system" },
    { content: question, role: "user" },
  ];

  // --- LLM call 1: decides to search knowledge base ---
  const llm1Id = randomUUID();
  const kbCallId = _randCallId();
  const llm1Start = addMs(t, randomUniform(0.3, 1.0) * 1000);
  const llm1End = addMs(llm1Start, randomUniform(1.5, 4.0) * 1000);

  const kbQuery = question;
  const kbToolCall = [
    {
      type: "function",
      id: kbCallId,
      function: {
        name: "search_knowledge_base",
        arguments: JSON.stringify({ query: kbQuery }),
      },
    },
  ];
  messages.push({
    role: "assistant",
    content: "",
    tool_calls: kbToolCall,
  });
  runs.push(
    _makeLlmRun(
      llm1Id,
      rootId,
      messages.slice(0, -1),
      llm1Start,
      llm1End,
      rootStart,
      "tool_calls",
      kbToolCall,
      null
    )
  );

  // --- Tool run: KB search result (abbreviated) ---
  const tool1Id = randomUUID();
  const tool1Start = addMs(llm1End, randomUniform(0.05, 0.2) * 1000);
  const tool1End = addMs(tool1Start, randomUniform(0.1, 0.3) * 1000);
  const kbResult =
    "=== returns_policy.md (relevance: 0.52) ===\n(policy content)\n\n=== shipping_policy.md (relevance: 0.38) ===\n(policy content)";
  messages.push({
    role: "tool",
    name: "search_knowledge_base",
    tool_call_id: kbCallId,
    content: kbResult,
  });
  runs.push(
    _makeToolRun(
      tool1Id,
      rootId,
      "search_knowledge_base",
      { query: kbQuery },
      kbResult,
      tool1Start,
      tool1End,
      rootStart
    )
  );

  // --- LLM call 2: final answer ---
  const llm2Id = randomUUID();
  const llm2Start = addMs(tool1End, randomUniform(0.1, 0.5) * 1000);
  const llm2End = addMs(llm2Start, randomUniform(1.0, 3.0) * 1000);

  messages.push({ role: "assistant", content: response });
  runs.push(
    _makeLlmRun(
      llm2Id,
      rootId,
      messages.slice(0, -1),
      llm2Start,
      llm2End,
      rootStart,
      "stop",
      null,
      response
    )
  );

  // --- Root run ---
  const rootEnd = addMs(llm2End, randomUniform(0.001, 0.05) * 1000);
  runs.push(
    _makeRootRun(rootId, question, response, messages, category, rootStart, rootEnd)
  );

  return runs;
}

function _makeTraceNoTools(
  question: string,
  response: string,
  category: string,
  startTime: Date
): Record<string, any>[] {
  const rootId = randomUUID();
  const rootStart = startTime;

  const llmId = randomUUID();
  const llmStart = addMs(startTime, randomUniform(0.3, 1.0) * 1000);
  const llmEnd = addMs(llmStart, randomUniform(2.0, 6.0) * 1000);

  const messages = [
    { content: SYSTEM_PROMPT, role: "system" },
    { content: question, role: "user" },
    { content: response, role: "assistant" },
  ];

  const rootEnd = addMs(llmEnd, randomUniform(0.001, 0.05) * 1000);

  const runs = [
    _makeLlmRun(
      llmId,
      rootId,
      messages.slice(0, 2),
      llmStart,
      llmEnd,
      rootStart,
      "stop",
      null,
      response
    ),
    _makeRootRun(
      rootId,
      question,
      response,
      messages,
      category,
      rootStart,
      rootEnd
    ),
  ];

  return runs;
}

function _makeTrace(
  question: string,
  response: string,
  category: string,
  startTime: Date,
  hasToolCalls: boolean
): Record<string, any>[] {
  if (category === "inventory" && hasToolCalls) {
    return _makeTraceWithTools(question, response, category, startTime);
  } else if (category === "both" && hasToolCalls) {
    return _makeTraceWithTools(question, response, category, startTime);
  } else if (category === "policy") {
    return _makeTraceWithKb(question, response, category, startTime);
  } else {
    return _makeTraceNoTools(question, response, category, startTime);
  }
}

function _fillCategory(
  genFn: () => [string, string][],
  count: number
): [string, string][] {
  const basePairs = genFn();
  const pairs: [string, string][] = [];
  let i = 0;
  while (pairs.length < count) {
    if (i < basePairs.length) {
      pairs.push(basePairs[i]);
    } else {
      const fresh = genFn();
      pairs.push(fresh[i % fresh.length]);
    }
    i++;
  }
  return pairs.slice(0, count);
}

function _injectFailures(
  items: [string, string, boolean][],
  failureFn: () => [string, string][],
  failureCount: number
): [string, string, boolean][] {
  const failurePairs = _fillCategory(failureFn, failureCount);
  const indices = randomSample(
    Array.from({ length: items.length }, (_, i) => i),
    failureCount
  );
  for (let i = 0; i < indices.length; i++) {
    const idx = indices[i];
    const fp = failurePairs[i];
    items[idx] = [fp[0], fp[1], true];
  }
  return items;
}

function main() {
  initSeededRandom(42);

  const categoryGenerators: Record<string, () => [string, string][]> = {
    inventory: _inventoryQuestions,
    policy: _policyQuestions,
    out_of_scope: _outOfScopeQuestions,
    both: _bothQuestions,
    website_troubleshooting: _websiteTroubleshootingQuestions,
  };

  // Failure-mode injection rates (per 200 traces in each category)
  const TROUBLESHOOTING_OVERCONFIDENT_COUNT = 40; // 20% of website_troubleshooting
  const INVENTORY_CLARIFICATION_COUNT = 35; // ~18% of inventory
  const BOTH_CLARIFICATION_COUNT = 30; // 15% of both

  // Collect all (question, response, category, isFailure) quads
  const allItems: [string, string, string, boolean][] = [];
  for (const cat of CATEGORIES) {
    const pairs = _fillCategory(categoryGenerators[cat], TRACES_PER_CATEGORY);
    let items: [string, string, boolean][] = pairs.map(([q, a]) => [
      q,
      a,
      false,
    ]);

    // Inject failure-mode traces into the appropriate categories
    if (cat === "website_troubleshooting") {
      items = _injectFailures(
        items,
        _websiteTroubleshootingOverconfidentQuestions,
        TROUBLESHOOTING_OVERCONFIDENT_COUNT
      );
    } else if (cat === "inventory") {
      items = _injectFailures(
        items,
        _inventoryClarificationQuestions,
        INVENTORY_CLARIFICATION_COUNT
      );
    } else if (cat === "both") {
      items = _injectFailures(
        items,
        _bothClarificationQuestions,
        BOTH_CLARIFICATION_COUNT
      );
    }

    for (const [q, a, isFailure] of items) {
      allItems.push([q, a, cat, isFailure]);
    }
  }

  // Shuffle to intersperse categories
  for (let i = allItems.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [allItems[i], allItems[j]] = [allItems[j], allItems[i]];
  }

  const totalTraces = allItems.length;
  console.log(
    `Generating ${totalTraces} traces (${TRACES_PER_CATEGORY} per category)...`
  );

  // Spread across ~2 hours, with random gaps between traces
  const baseTime = new Date(Date.UTC(2026, 1, 15, 19, 0, 0)); // Feb 15, 2026 19:00 UTC
  const totalWindowSeconds = 2 * 3600; // 2 hours
  const avgGap = totalWindowSeconds / totalTraces;

  const allRuns: Record<string, any>[] = [];
  let currentTime = baseTime;
  for (const [question, response, category, isFailure] of allItems) {
    const hasTools = !isFailure && (category === "inventory" || category === "both");
    const runs = _makeTrace(
      question,
      response,
      category,
      currentTime,
      hasTools
    );
    allRuns.push(...runs);
    const gap = randomUniform(avgGap * 0.3, avgGap * 1.7);
    currentTime = addMs(currentTime, gap * 1000);
  }

  // Stats
  const traceCount = allRuns.filter((r) => r.name === "Emma").length;
  const runCount = allRuns.length;
  const toolRuns = allRuns.filter(
    (r) => r.name === "query_database" || r.name === "search_knowledge_base"
  ).length;
  console.log(`Generated ${runCount} total runs across ${traceCount} traces`);
  console.log(`  Tool call runs: ${toolRuns}`);

  const catCounts: Record<string, number> = {};
  for (const run of allRuns) {
    if (run.run_type === "chain" && run.name === "Emma") {
      for (const tag of run.tags) {
        catCounts[tag] = (catCounts[tag] || 0) + 1;
      }
    }
  }
  console.log("Category breakdown:");
  for (const cat of Object.keys(catCounts).sort()) {
    console.log(`  ${cat}: ${catCounts[cat]}`);
  }

  // Write output
  const scriptDir = __dirname;
  const outputPath = path.join(scriptDir, OUTPUT_FILE);
  fs.writeFileSync(outputPath, JSON.stringify(allRuns, null, 2));
  console.log(`Wrote ${outputPath}`);
}

main();
