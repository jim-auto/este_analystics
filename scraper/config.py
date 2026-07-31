"""Region configuration for 東名阪 analysis."""

USER_AGENT = (
    "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"
)
REQUEST_DELAY_SEC = 2.5
BASE_URL = "https://estama.jp"

REGIONS = {
    "kanto": {
        "slug": "kanto",
        "label": "東京",
        "subtitle": "関東エリア",
        "description": "東京・神奈川・埼玉・千葉を中心とした関東エリア",
    },
    "kansai": {
        "slug": "kansai",
        "label": "大阪",
        "subtitle": "関西エリア",
        "description": "大阪・京都・兵庫を中心とした関西エリア",
    },
    "chubu": {
        "slug": "chubu",
        "label": "名古屋",
        "subtitle": "中部エリア",
        "description": "愛知・岐阜・静岡を中心とした中部エリア",
    },
}

SHOPLIST_MAX_PAGES = 10
REVIEWLIST_PAGES = 5

FEATURED_SUBAREA_KEYWORDS = {
    "kanto": ("新宿", "池袋", "渋谷", "秋葉原", "横浜", "五反田"),
    "kansai": ("梅田", "日本橋", "難波", "京橋", "心斎橋"),
    "chubu": ("栄", "名古屋", "名駅", "金山", "上前津"),
}
