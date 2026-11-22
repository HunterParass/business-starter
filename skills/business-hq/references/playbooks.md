# Business-type playbooks

HQ picks one primary playbook at intake (plus a secondary if the business is a mix, e.g. a candle maker who also runs workshops), writes it into `00-hq/BRIEF.md`, and uses it to decide which departments run and what extra work each one does. In every delegation HQ names the playbook; each department reads its type's section here and covers the extra items listed for it.

**Core departments run for every business:** market, competitors, customers, strategy, brand, product, finance, legal, marketing, operations, red team. Each playbook says which of **content, sales, commerce, retention, fundraising** to add, and what to emphasise. "Skip" means only run it if the founder asks.

Everything specific to a jurisdiction or platform (fees, permits, age limits, policies) must be looked up on official sources and dated. These playbooks say *what to check*, not the answer.

---

## 1. Physical product brand
Handmade goods, small-batch products, apparel, beauty, accessories, home goods, direct-to-consumer brands.
- **Add:** content (essential), commerce (essential), retention. Sales only for wholesale. Fundraising rarely.
- **Content:** short-form video is usually the main engine: process and making-of, before and after, packing orders, founder story, product in use, customer reactions. Creator seeding and UGC.
- **Commerce:** channel sequence, per-unit margins on every channel, listings, photo brief, packaging that's worth filming, shipping and returns, inventory plan.
- **Product:** prototype, samples, small first batch; pre-orders to fund stock.
- **Finance:** `inventory_purchases` in the model; cash tied up in minimum order quantities.
- **Legal:** product labelling and safety rules for the category (cosmetics, children's items, candles, electronics, textiles each have their own), sales tax where customers are, import duties if sourcing abroad.
- **Key metrics:** kept per unit by channel, conversion rate, average order value, repeat purchase rate, content views to sales.
- **First customers:** friends and local network, markets and pop-ups, short-form video, a marketplace where buyers already search.
- **Watch out for:** big minimum orders before demand is proven, free shipping that eats margin, copying a trend that's already saturated.

## 2. Food and beverage
Home-based baking, sauces and snacks, meal prep, food trucks, catering, packaged food and drinks.
- **Add:** content, commerce (packaged food), retention. Sales for wholesale and catering.
- **Legal (critical):** home-based food rules (some foods are allowed from home kitchens, many aren't), health department permits and inspections, food handler certification, commercial kitchen requirements, labelling (ingredients, allergens, nutrition where required), insurance, mobile vending and event permits.
- **Ops:** commercial kitchen access, ingredient suppliers, shelf life, food safety process, batch tracking.
- **Content:** food content performs well visually: process, taste reactions, behind the counter.
- **Key metrics:** food cost percentage, waste, price per unit, repeat customers, event sales per hour.
- **First customers:** farmers' markets, local events, community groups, local cafés stocking products.
- **Watch out for:** selling before permits are in place, allergen mistakes, thin margins after ingredients and packaging.

## 3. Local service
Cleaning, lawn and snow, car detailing, handyman and trades, pet care, tutoring, moving help, repairs.
- **Add:** sales, retention (reviews are everything). Content optional (before-and-after videos work well). Skip commerce except online booking.
- **Marketing:** local presence plan: business listing on maps and search, local directories, neighbourhood groups, flyers and door hangers, partnerships with related local businesses, seasonal campaigns.
- **Retention:** review requests after every job, recurring service plans, referral reward.
- **Finance:** `pricing_calc.py service` for the hourly or per-job rate; travel time and supplies included; seasonality.
- **Legal:** trade licences where required, liability insurance, working in clients' homes, background checks for child or pet care, contractor rules if hiring helpers.
- **Ops:** quoting, scheduling and booking, payment on completion, job checklist.
- **Key metrics:** jobs per week, average job value, effective hourly rate after travel, review count and rating, repeat and referral share.
- **First customers:** neighbours, family network, local online groups, map listing.
- **Watch out for:** underpricing, unpaid travel time, no insurance.

## 4. Personal and creative services
Personal training, coaching in person, photography, hair and beauty, music or art lessons, DJ, design for individuals.
- **Add:** content (portfolio and personality), sales, retention. Commerce for booking and packages.
- **Strategy:** packages and offer design rather than hourly pricing; deposits and cancellation policy.
- **Content:** portfolio posts, transformations (with consent), tips, behind the scenes.
- **Legal:** certifications or licences for the service, consent and model releases for photos, liability insurance, working with minors.
- **Key metrics:** bookings per week, utilisation, average package value, rebooking rate.
- **Watch out for:** no-shows (deposits), trading time for money with no ceiling.

## 5. Freelance, agency and professional services
Design, development, marketing, video editing, writing, bookkeeping, consulting, B2B services.
- **Add:** sales (essential), content (LinkedIn or niche platforms, case studies), retention (repeat clients and referrals).
- **Strategy:** a narrow niche and a productised offer with a clear outcome; value-based packages; `offer.md` matters most here.
- **Finance:** `pricing_calc.py service`; utilisation; payment terms and deposits.
- **Sales:** portfolio and case studies, outreach, proposals, statements of work.
- **Legal:** service agreements, IP ownership on delivery, contractor vs employee rules, professional liability insurance for advice-based work.
- **Key metrics:** pipeline value, close rate, average project value, effective hourly rate, client lifetime.
- **Watch out for:** generalist positioning, scope creep, one client being most of the revenue.

## 6. Software: SaaS, web app, mobile app
- **Add:** retention (onboarding and churn are the business), content (build in public, tutorials), sales only for B2B over a few hundred per year. Fundraising if venture-scale.
- **Product:** smallest version that delivers the core value; activation metric defined before building.
- **Marketing:** for apps, app store optimisation (title, keywords, screenshots, ratings); for B2B, search and communities; free tools as marketing.
- **Retention:** onboarding to the "aha" moment, trial or freemium conversion, cancel flow, failed payment recovery.
- **Legal:** terms, privacy policy and data protection, app store rules, in-app purchase rules, accessibility, children's privacy if users may be under 13.
- **Key metrics:** activation rate, trial to paid, monthly churn, MRR, CAC payback.
- **Watch out for:** building for months before anyone pays; app store fees in the margin.

## 7. Games
Mobile, PC and console indie games, and experiences on creation platforms (for example Roblox, Fortnite Creative, Minecraft marketplace).
- **Add:** content (essential: devlogs, clips, short-form gameplay, streamers and creators), retention (players returning is the game), commerce for store pages. Fundraising: publishers, grants, platform funds.
- **Product:** a vertical slice or prototype that tests the fun first; playtests with strangers, not friends.
- **Marketing:** wishlists or followers before launch, store page assets, festivals and showcases, community on Discord.
- **Strategy:** monetisation that fits the platform (premium, in-app purchases, passes, ads, platform currency payouts) and its revenue share.
- **Legal:** each platform's developer terms and monetisation rules, age ratings, rules for players under 13, loot box and gambling-like mechanic rules in some countries, payout eligibility and age requirements, music and asset licences.
- **Key metrics:** day-1 and day-7 retention, session length, conversion to payer, average revenue per daily user, wishlist or follower count.
- **Watch out for:** platform dependence (rules and payouts can change), copying a hit too closely, using IP you don't own.

## 8. Content creator, media and newsletter
YouTube, TikTok, podcasts, newsletters, streaming, faceless channels; the audience is the asset.
- **Add:** content (the product itself), sales (sponsorships), retention (community). Commerce for merch or digital products.
- **Strategy:** revenue stack: platform payouts, sponsorships with a rate card, affiliate, digital products, memberships, merch, services.
- **Legal:** sponsorship disclosure, music and footage licensing, platform monetisation eligibility and age requirements, contracts with brands.
- **Key metrics:** views, watch time, subscribers or subscribers to newsletter, open rate, revenue per thousand views, sponsor revenue.
- **Watch out for:** one platform owning the whole audience, no email list, burnout cadence.

## 9. Courses, coaching and education (online)
Online courses, cohort programs, group coaching, tutoring online, templates and digital downloads.
- **Add:** content (teaching in public builds trust), sales for high-ticket, retention (completion and results drive referrals), commerce for checkout and delivery.
- **Strategy:** `offer.md`: outcome, guarantee, bonuses, honest deadlines; pre-sell before building the course.
- **Marketing:** lead magnet, email sequence, webinar or free workshop.
- **Legal:** refund policy, claims about results (income and health claims are heavily regulated), working with minors.
- **Key metrics:** email list growth, lead magnet to buyer conversion, completion rate, testimonials collected.
- **Watch out for:** building a full course before a single sale, overpromised results.

## 10. Ecommerce reselling
Print-on-demand, dropshipping, resale and thrift flipping, buying wholesale to sell on marketplaces.
- **Add:** commerce (essential), content, retention. Skip sales.
- **Commerce:** supplier reliability, shipping times, per-unit margins after every fee and ad cost, marketplace policies for this model.
- **Finance:** ad cost per order is usually the whole game; run break-even ROAS before any ad spend.
- **Legal:** marketplace seller policies, counterfeit and trademark risks (no branded knock-offs), consumer protection on delivery times and refunds, sales tax and import rules.
- **Key metrics:** kept per unit after ads, return rate, sell-through rate, delivery time.
- **Watch out for:** thin margins hidden by revenue numbers, supplier quality, platform account suspensions.

## 11. Brick-and-mortar shop, café or restaurant
- **Add:** retention (regulars), content (local), commerce for online orders. Fundraising often (fit-out is expensive).
- **Market:** foot traffic and location analysis, local competition on a map, rent benchmarks.
- **Finance:** big startup costs (lease deposit, fit-out, equipment, first stock), staff costs, longer runway; model several months of low sales.
- **Legal:** lease review (get a professional), zoning, permits and inspections, signage, liquor or food licences, accessibility, employment law.
- **Ops:** point-of-sale, staffing schedule, suppliers, opening hours, opening checklist.
- **Key metrics:** daily sales, average transaction, sales per square metre or foot, labour as % of sales, food or product cost %.
- **Watch out for:** signing a long lease before proving demand (test with pop-ups or a market stall first).

## 12. Marketplace or platform
Connecting two sides: buyers and sellers, clients and freelancers, renters and owners.
- **Add:** sales (supply side), retention (both sides), content. Fundraising often if venture-scale.
- **Strategy:** which side to build first (usually supply), a single narrow niche and city, take rate, how to stop people transacting off-platform.
- **Product:** start manually (concierge matching in a spreadsheet) before building software.
- **Legal:** terms for both sides, payments handling rules, liability for what users do, worker classification if the supply side are individuals.
- **Key metrics:** liquidity (share of listings that transact), time to match, take rate, repeat use on both sides.
- **Watch out for:** chicken-and-egg stall; going broad before one niche works.

## 13. B2B products, wholesale and manufacturing
Selling products to businesses, distributors or retailers; contract manufacturing.
- **Add:** sales (essential), commerce (wholesale terms), retention (account management). Fundraising if equipment-heavy.
- **Sales:** trade shows, distributors, buyer meetings, samples, line sheets, purchase orders.
- **Finance:** payment terms (net 30 to 90) mean waiting for cash long after delivery: model it manually since the model assumes payment on sale; working capital and equipment.
- **Legal:** supply and distribution agreements, certifications for the category, product liability insurance, import and export rules.
- **Key metrics:** accounts won, reorder rate, days sales outstanding, gross margin by account.
- **Watch out for:** one big customer dictating terms, cash gaps from payment terms.

## 14. Events and experiences
Workshops, parties, tours, tournaments, pop-up experiences.
- **Add:** content, commerce (ticketing), retention (repeat attendees). Sales for corporate bookings.
- **Finance:** break-even ticket count per event; deposits and venue costs paid before ticket revenue.
- **Legal:** venue contracts, liability insurance and waivers, permits for public events, alcohol rules, safety plans, minors attending.
- **Key metrics:** tickets sold vs capacity, sell-through time, cost per attendee, repeat attendance.
- **Watch out for:** committing to venues before pre-sales.

## 15. Hardware and inventions
Physical devices, electronics, gadgets, patented products.
- **Add:** commerce, content, fundraising (crowdfunding and grants are common). Sales for retail buyers.
- **Product:** prototype iterations, design for manufacturing, test batch, certification costs and timelines.
- **Legal:** patents (talk to a patent agent before public disclosure), product safety and electrical certifications for each market, warranty and returns.
- **Fundraising:** reward crowdfunding as a pre-sale and demand test, hardware accelerators, government innovation grants.
- **Key metrics:** unit cost at volume, pre-order count, certification status, defect rate.
- **Watch out for:** underestimating manufacturing and certification time and cost; disclosing an invention before protecting it if that matters.

## 16. Nonprofit and social enterprise
- **Add:** fundraising (grants and donors are the revenue), content, retention (donors and volunteers).
- **Legal:** structure options differ (registered charity, nonprofit corporation, for-profit social enterprise) with different tax and governance rules; charitable registration requirements.
- **Strategy:** theory of change, impact metrics, earned-revenue options alongside grants.
- **Key metrics:** impact per dollar, donor retention, grant success rate.
- **Watch out for:** a structure that blocks future revenue options; reporting obligations on grants.

---

## Mixed businesses

Use the playbook for the main revenue source as primary, and add the secondary playbook's departments and extra items. Example: a candle brand (1) that runs paid workshops (14) adds ticketing and event insurance from 14 to the product plan.
