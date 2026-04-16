"""Video sets for validation spikes.

Curated from curation reports generated on 2026-02-26.
Labels calibrated against Gemini analysis (brand_validation_report.json,
creative_validation_report.json).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SpikeVideo:
    """A video to test in a validation spike."""

    platform: str  # "youtube", "tiktok", "instagram"
    video_id: str
    description: str  # Human note: what the video is about

    # Spike 1 ground truth (brand videos only)
    expected_brands: list[str] = field(default_factory=list)

    # Spike 2 ground truth (optional — for accuracy measurement)
    expected_hook: str | None = None
    expected_narrative: str | None = None


# ---------------------------------------------------------------------------
# Spike 1: Brand Exposure timestamp_end validation
# 18 videos with known brand appearances (sponsored, reviews, unboxings)
# Platforms: 10 YouTube + 8 TikTok
# Categories: Tech, Beauty, Fashion/Athletic, Food, Gaming
# Labels: parent-company brand names only (Gemini treats product lines like
#         iPhone/Galaxy/MagSafe as part of the parent brand Apple/Samsung).
# ---------------------------------------------------------------------------
BRAND_EXPOSURE_VIDEOS: list[SpikeVideo] = [
    # ── Tech: YouTube reviews/unboxings ──
    SpikeVideo(
        platform="youtube",
        video_id="Sx6dAx7dnXg",
        description="MKBHD iPhone 12 unboxing + MagSafe demo — Apple logo, MagSafe branding visible",
        expected_brands=["Apple"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="l0DoQYGZt8M",
        description="MKBHD Apple iPhone X unboxing — 19M views, Apple branding throughout",
        expected_brands=["Apple"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="oTtbIf1TfL8",
        description="iJustine full iPhone 14 lineup unboxing and review — Apple product showcase",
        expected_brands=["Apple"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="xf2DPY3vGto",
        description="Mrwhosetheboss Android vs iPhone ft MKBHD — Samsung and Apple logos in comparisons",
        expected_brands=["Apple", "Samsung"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="W1G8-Xjxpyg",
        description="AlexGTech Galaxy S25 Ultra vs iPhone 16 Pro — dual brand comparison with logos",
        expected_brands=["Apple", "Samsung"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="RfahZnG8R6s",
        description="Matthew Moniz Samsung Galaxy S25 vs iPhone 16 — side-by-side brand comparison",
        expected_brands=["Apple", "Samsung"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="FbAxynWGhy8",
        description="Dr-UnBox iPhone 17 Pro unboxing and camera test ASMR — latest Apple product visible",
        expected_brands=["Apple"],
    ),
    # ── Beauty: TikTok skincare with brand tags ──
    SpikeVideo(
        platform="tiktok",
        video_id="7602712586194324767",
        description="via..li sponsored by The Face Shop — #thefaceshoppartner hashtag, product close-ups",
        expected_brands=["The Face Shop"],
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7581205822701587767",
        description="itsbabykelz skincare routine tagging Biodance, rhode, Glow Recipe, medicube — 4.6M views",
        expected_brands=["Biodance", "rhode", "Glow Recipe", "medicube", "Anua", "TORRIDEN"],
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7600507333038361887",
        description="thedaninicolee skincare routine tagging La Roche-Posay, Good Molecules, Anua — 1.5M views",
        expected_brands=["La Roche-Posay", "Good Molecules", "Anua"],
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7609752280274980110",
        description="itsaishamian skincare routine tagging Laneige, ELEMIS, Lancôme, La Roche-Posay — 786K views",
        expected_brands=["Laneige", "ELEMIS", "Lancôme", "La Roche-Posay"],
    ),
    # ── Fashion/Athletic: TikTok sneaker hauls ──
    SpikeVideo(
        platform="tiktok",
        video_id="7569228241509174550",
        description="pikitrainer Nike Vomero vs Adidas Adizero running shoe test — 2M views, sponsor code",
        expected_brands=["Nike", "Adidas"],
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7472130766718160150",
        description="charlyfireinthebooth sneaker haul tagging Nike, Adidas, Reebok, Salomon — 375K views",
        expected_brands=["Nike", "Adidas", "Reebok", "Salomon", "JD Sports"],
    ),
    # ── Food: TikTok HelloFresh #ad ──
    SpikeVideo(
        platform="tiktok",
        video_id="7596853877547240759",
        description="nutritionwithnat_ #Ad HelloFresh partner — explicit ad disclosure hashtag",
        expected_brands=["HelloFresh"],
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7519606244932340997",
        description="everything_delish HelloFresh #ad grill-ready meal with discount code — 400K views",
        expected_brands=["HelloFresh"],
    ),
    # ── Gaming: YouTube setup tours ──
    SpikeVideo(
        platform="youtube",
        video_id="Oc6ID1tvFNw",
        description="Linus Tech Tips all-Logitech gaming setup — 3.8M views, Logitech branding everywhere",
        expected_brands=["Logitech"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="9ISeMcX15B4",
        description="TechSource building the all-Razer immersive gaming setup — Razer products throughout",
        expected_brands=["Razer"],
    ),
    SpikeVideo(
        platform="youtube",
        video_id="RD5f9xGNgt8",
        description="TechSource building ultimate all-Razer gaming setup — 1.4M views, full Razer branding",
        expected_brands=["Razer"],
    ),
]

# ---------------------------------------------------------------------------
# Spike 2: Creative Pattern taxonomy validation
# 51 diverse videos across platforms and verticals
# Platforms: 27 YouTube + 24 TikTok
# Labels calibrated from Gemini video analysis (creative_validation_report.json).
# Hook types: shock_curiosity(20), storytelling(13), product_reveal(6),
#             trend_audio(4), challenge(3), question(3), none(2)
# Narratives: vlog(9), other(9), review(6), tutorial(5), unboxing(4),
#             day_in_life(4), comparison(4), listicle(4), transformation(3), skit(3)
# ---------------------------------------------------------------------------
CREATIVE_PATTERN_VIDEOS: list[SpikeVideo] = [
    # ── "what would happen if I tried this for 30 days" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="PPkFndAjhFs",
        description="DoctorMike — What Happens When You Only Eat McDonalds For 30 Days",
        expected_hook="shock_curiosity",
        expected_narrative="review",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="euPXf2hqU3s",
        description="JeremyEthier — What Happens To Your Body After 100 Push-Ups a Day For 30 Days",
        expected_hook="shock_curiosity",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="sbxPcQnDLMM",
        description="JesseJamesWest — I Tried Boxing For 30 Days body transformation challenge",
        expected_hook="storytelling",
        expected_narrative="vlog",
    ),
    # ── "you won't believe what I found at the thrift store" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7609087013358210335",
        description="Thrift store Office memorabilia shock find",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7388301605705256238",
        description="Travis Scott Jordan 1 thrift store find — shock reaction",
        expected_hook="shock_curiosity",
        expected_narrative="transformation",
    ),
    # ── "trending sound TikTok dance challenge viral audio" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7611209892577283336",
        description="NEW VIRAL TRENDING SOUND TIKTOK DANCE 2026 — original choreography",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7581856356668378381",
        description="Group dance challenge trying all popular trending viral sound dances",
        expected_hook="challenge",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7599769770518531350",
        description="Tout Donner trending sound dance challenge",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7608808468425886996",
        description="Hawak mo ang beat — PH/KR easy dance viral TikTok dances 2026",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7609357677935856914",
        description="No Batidao phonk dance on motorcycle — viral dance challenge",
        expected_hook="trend_audio",
        expected_narrative="other",
    ),
    # ── "storytime how I quit my job and started a business" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7288308201181678890",
        description="Storytime — how I quit my job and started my online business",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7297641898909486382",
        description="Story time — why I quit my $200k job to start my own business",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7569812807840009486",
        description="I quit my aerospace job to start an algae farm — entrepreneurship vlog",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    # ── "new product launch reveal first look gadget 2025" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="_-AS5DtDeqs",
        description="Apple — Introducing iPhone 17 Pro official product reveal",
        expected_hook="product_reveal",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="ZkC6uuIADgY",
        description="iPhone Fold First Look Confirms Apple Genius Move — tech reveal",
        expected_hook="shock_curiosity",
        expected_narrative="review",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="NxElM9IWwO8",
        description="OnePlus 15 Introducing Design Reimagined — official product launch",
        expected_hook="product_reveal",
        expected_narrative="other",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="oHCrFZIK8io",
        description="Samsung Galaxy G Fold Officially Revealed — First Look",
        expected_hook="product_reveal",
        expected_narrative="review",
    ),
    # ── "24 hour challenge overnight in store" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="-ejjQArrq1E",
        description="24 HOUR OVERNIGHT CHALLENGE IN HOME DEPOT",
        expected_hook="challenge",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="y2oZbpUKwX8",
        description="24 HOUR OVERNIGHT CHALLENGE IN TARGET — caught?!",
        expected_hook="shock_curiosity",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="DRrwNGFHSnc",
        description="24 Hour Overnight Challenge In MEGASTORE — MoreJStu",
        expected_hook="challenge",
        expected_narrative="vlog",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="wn-deqrkNP8",
        description="How Long Could You Secretly Live In a Grocery Store — airrack challenge",
        expected_hook="question",
        expected_narrative="vlog",
    ),
    # ── "how to fix a leaking faucet step by step plumbing" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="SYPFon69vKs",
        description="How to Fix a Leaky Faucet — The Home Depot step-by-step tutorial",
        expected_hook="none",
        expected_narrative="tutorial",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="rcV6CwoKwGg",
        description="6 Steps to FIX a Leaky Faucet GUARANTEED — RogerWakefield plumbing",
        expected_hook="storytelling",
        expected_narrative="tutorial",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="F4LeAVpTdds",
        description="EASY FIX Kitchen Faucet Leaking — how to fix in 1 minute",
        expected_hook="shock_curiosity",
        expected_narrative="tutorial",
    ),
    # ── "beginner makeup tutorial natural look step by step" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="CdQiOP_tn1Q",
        description="How to Apply Makeup for Beginners STEP BY STEP — Eman tutorial",
        expected_hook="storytelling",
        expected_narrative="tutorial",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="vNpafKvDbzk",
        description="NO MAKEUP makeup — Natural Everyday Makeup for Beginners",
        expected_hook="shock_curiosity",
        expected_narrative="tutorial",
    ),
    # ── "honest review of the new MacBook after one month" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="qAknNx7IZQg",
        description="MacBook Pro M5 The Honest 2-Month Truth — Don't Make My Mistake",
        expected_hook="storytelling",
        expected_narrative="review",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="rOIneg90auQ",
        description="M4 MacBook Air Long-Term Review — The Ugly Truth After 6 Months",
        expected_hook="product_reveal",
        expected_narrative="review",
    ),
    # ── "unboxing mystery box subscription package opening" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7610966733683199263",
        description="Large mystery box unboxing — BigFnBox Texas, 33 packages inside",
        expected_hook="shock_curiosity",
        expected_narrative="unboxing",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7538268743479069965",
        description="USA Mystery Box unboxing — retail over $1116, large box",
        expected_hook="product_reveal",
        expected_narrative="unboxing",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7593122746687655198",
        description="Was this TikTok mystery box worth $60 — honest unboxing",
        expected_hook="shock_curiosity",
        expected_narrative="unboxing",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7600196568083402014",
        description="Fun Delivered Party Box unboxing — $224.99, mystery mail packages",
        expected_hook="product_reveal",
        expected_narrative="unboxing",
    ),
    # ── "day in the life of a software engineer San Francisco" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7059494935086517551",
        description="Come to work with me — SWE day in my life in San Francisco",
        expected_hook="storytelling",
        expected_narrative="day_in_life",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7608332084217744653",
        description="Big tech job in the bay — DITL software engineer SF",
        expected_hook="storytelling",
        expected_narrative="day_in_life",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7153684984140795178",
        description="Day in my life as 23yo software engineer in SF — hybrid remote",
        expected_hook="storytelling",
        expected_narrative="day_in_life",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7597723282141498655",
        description="Come spend a day with me at Microsoft as 26yo AI engineer",
        expected_hook="storytelling",
        expected_narrative="day_in_life",
    ),
    # ── "extreme room makeover before and after on a budget" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7368603618695482666",
        description="Budget room makeover — western vintage thrifted room transformation",
        expected_hook="storytelling",
        expected_narrative="transformation",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7342660582438440234",
        description="Room Makeover for my daughter — budget-friendly before/after",
        expected_hook="storytelling",
        expected_narrative="transformation",
    ),
    # ── "cheap vs expensive headphones which sounds better" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="iZcg9-lMeHQ",
        description="I Tested CHEAP vs EXPENSIVE Headphones — Here's the Truth",
        expected_hook="shock_curiosity",
        expected_narrative="comparison",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="W3ZxzsycKCg",
        description="CHEAP vs EXPENSIVE Headphones Challenge — Can Normal People Tell",
        expected_hook="question",
        expected_narrative="comparison",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="iZMja5irvv4",
        description="Cheap Headphones vs Premium Blindfolded Test — CNET comparison",
        expected_hook="storytelling",
        expected_narrative="comparison",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="6WEqatlv-10",
        description="Expensive headphones are NOT always better — comparison",
        expected_hook="shock_curiosity",
        expected_narrative="review",
    ),
    # ── "top 10 travel destinations you need to visit 2025" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="eLPVDaaQybY",
        description="Top 10 Places To Visit in 2025 — Year of Travel listicle",
        expected_hook="shock_curiosity",
        expected_narrative="listicle",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="40W27HZCcso",
        description="Top 15 Countries to Visit in 2025 — Ultimate Travel Guide",
        expected_hook="shock_curiosity",
        expected_narrative="listicle",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="tdgWEEOgdrU",
        description="Top 10 MUST-SEE Travel Destinations Around The World",
        expected_hook="storytelling",
        expected_narrative="listicle",
    ),
    SpikeVideo(
        platform="youtube",
        video_id="Quz_BNf_X_s",
        description="10 UNDERRATED Budget Travel Destinations to Visit in 2025",
        expected_hook="question",
        expected_narrative="listicle",
    ),
    # ── "funny comedy skit relatable school moments" (tiktok) ──
    SpikeVideo(
        platform="tiktok",
        video_id="7584957005220072734",
        description="Middle school relatable comedy skit — familial peril satire",
        expected_hook="shock_curiosity",
        expected_narrative="skit",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7367180217779096874",
        description="School comedy skit — all that work for this?? relatable humor",
        expected_hook="storytelling",
        expected_narrative="skit",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7606146446294781215",
        description="Girls big shirts small pants to school — relatable viral skit",
        expected_hook="shock_curiosity",
        expected_narrative="comparison",
    ),
    SpikeVideo(
        platform="tiktok",
        video_id="7582360920840523063",
        description="They need to be stopped — school funny comedy skit",
        expected_hook="shock_curiosity",
        expected_narrative="skit",
    ),
    # ── "cinematic travel film drone footage landscape 4K" (youtube) ──
    SpikeVideo(
        platform="youtube",
        video_id="BTMjD7_evjE",
        description="The Alps 4K — Scenic Relaxation Film With Calming Music, cinematic",
        expected_hook="none",
        expected_narrative="other",
    ),
]
