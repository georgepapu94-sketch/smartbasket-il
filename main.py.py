import os
import re
import math
import io
import json
import threading
import webbrowser
from typing import List, Dict, Optional, Any
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="SmartBasket IL - Full Admin & Cloud Edition")

CACHE_FILE = "catalog_cache.json"
CONFIG_FILE = "site_config.json"

# =====================================================================
# 1. שכבת היררכיית הנתונים: 15 מחלקות על ו-420 תתי-קטגוריות מלאות
# =====================================================================
SUPER_CATEGORIES_TREE: Dict[str, List[str]] = {
    "פירות וירקות טריים": ["אבוקדו", "אורגנו", "בזיליקום", "בצל", "בצל ירוק", "בק צואי", "גזר", "דלעת", "חסה", "ירקות שורש", "ירקות שטופים אחרים", "כוסברה", "כרוב", "כרוב חתוך", "לוף/פרסה", "לימון", "לקטים לסלט", "מלפפון", "מרווה", "נבטים", "נענע", "נשנושי ירקות", "סלק עלים", "סלרי עלים", "עגבניה", "עולש", "עירית", "עלי בייבי", "עלי חסה שטופים", "ענבים", "פטריות", "פלפלים", "פרי שדה", "רוזמרין", "רוקט", "שום", "שמיר", "תערובות לסלט", "תפוח אדמה", "תרד", "בננות", "תפוח עץ"],
    "קצביה, בשר ועוף טרי": ["בשר בקר חלקי פנים", "בשר טחון טרי", "בשר כבש טרי", "הודו טרי ארוז", "חלקי הודו טרי", "חלקי עוף טרי", "חלקי עוף/הודו מתובל טרי ארוז", "חלקי פנים עוף טרי", "חלקי פנים עוף/הודו טרי ארוז", "מוצרי בשר על האש", "נתחים אחורי טרי", "נתחים קדמי טרי", "עוף טרי ארוז"],
    "דגים טריים ומעושנים": ["דג מעושן כבוש ארוז", "דג פלם בשקית", "דגי פילה טריים", "דגים טריים סטנדרט", "דגים טריים פרימיום", "סלטי דגים", "קוויאר חלקיק/מעופפים"],
    "מוצרי חלב, ביצים ומעדנייה": ["אשל לבן שמנת", "ביצים מיוחדות", "ביצים רגילות", "גבינות במרקם שמנת", "גבינות לבנות", "קוטג'", "גבינות מותכות מדף", "גבינות מיוחדות במשקל", "גבינות מיוחדות מדף", "גבינות מלוחות במשקל", "גבינות מלוחות מדף", "גבינות צהובות במשקל", "גבינות צהובות מדף", "גבינות שמנת", "גבינות שמנת במשקל", "גבינת לאבנה", "חלב", "חמאה", "יוגורט", "יוגורט חלבון", "מוצרלה פריסה", "מזון מוכן מצונן", "מיכלי שמנת מתוקה", "ממרחים מצוננים", "מעדני חלב לפעוטות", "מעדנים", "מרגרינה", "משקאות חלב", "נקניקיות מן הצומח", "נקניקיות מצוננות", "נקניקים במעדניה", "נקניקים יבשים", "סלטי חומוס חלק", "סלטי חומוס מעושר / תוספות", "סלטי חצילים", "סלטי טחינה", "סלטי ירקות", "סלטים מזרחיים", "פסטרמות ונקניקים ארוזים", "שוקו"],
    "מאפייה, לחם ובצקים טריים": ["לחם אחיד מיוחד", "לחם במאפיות", "לחם חשוך", "לחם מפוקח ארוז", "לחמניות ארוחות", "לחמניות במאפייה", "מאפים מלוחים", "מאפים שונים במאפייה", "מוצרי בצק טרי", "עוגות/עוגיות במאפייה", "פיתות ארוחות"],
    "מכולת, יבשים ומזווה": ["אורז", "אטריות", "אטריות בסגנון אסייתי/סיני", "אצות/דפי אורי", "ארוחות מוכנות לבישול", "ארוחות מוכנות מן הצומח", "אריזות סוכר", "אריזות סולת", "דבש", "דגנים", "דגנים מיוחדים", "דייסות", "חומץ/מיץ לימון", "חלבה", "חרדל", "טחינה גולמית", "מזון מהיר", "מיונז", "מלח", "ממרחים ומחיות לאפיה", "ממרחים מתוקים", "ממרחים שאינם מתוקים", "ממתיקים מלאכותיים סוכרזית טבליה", "ממתיקים מלאכותיים סכרין / אחר", "מרקים", "מרקים לתיבול", "משפרי אפיה", "סילאן", "סירופים", "עזרי מזון מתכלים אחרים", "פודינג/ג'לי/מוס באבקה", "פירות יבשים", "פסטה", "פריכיות לחם", "פתי בר", "קוסקוס", "קטניות", "קטשופ", "קמח", "רוטב לסלט", "רטבי המזרח", "רטבי עגבניות", "רטבים איטלקיים", "רטבים לבישול אחרים", "ריבות/קונפיטורות", "שום מצונן/בצל מטוגן", "שומשום/קוקוס/פרג", "שוקולד לאפיה", "שימורי דגים", "שימורי זיתים ירוקים", "שימורי זיתים שחורים", "שימורי טונה", "שימורי ירקות", "שימורי ירקות אקזוטיים", "שימורי ירקות ירוקים/מיקס", "שימורי ירקות כבושים", "שימורי ירקות שלמים ומעורבים", "שימורי מלפפונים", "שימורי עגבניות", "שימורי פירות וקוקטיילים", "שימורי קטניות", "שמן זית", "שמנים רגילים", "שמרים", "שקדים ואגוזים לאפיה", "תבלינים במיכל", "תבלינים בשקיות", "תבשילים ותערובות", "תוספים למרק/סלט", "תחתיות ותערובות לעוגה", "תירס"],
    "קפואים וגלידות": ["אוכל מוכן קפוא בשרי", "אוכל מוכן קפוא דגים", "בורקס", "בעלי כנף קפואים", "בצקים קפואים", "בשר בקר קפוא", "בשר ועוף מעובד", "גביעי גלידה", "גלידות חבילות בית", "דגים קפואים בואקום", "הודו קפוא", "חזה גריל צמחוני", "חטיפי קרח", "ירקות קפואים", "עוגות ועוגיות קפואות", "עוף קפוא", "פיצות", "פירות קפואים", "קינוחי גלידה", "קניות קפואות", "קציצות מן הצומח", "שלגונים אחרים", "שלגונים בודדים", "שניצל מן הצומח", "תבלינים ורטבים קפואים"],
    "חטיפים, ממתקים ומתוקים": ["בונבוניירות אריזות שי", "בייגלה", "וופלים", "חטיפי חלבון", "חטיפים", "חטיפים אפויים", "חטיפים מן הצומח", "חטיפים מתוקים", "חטיפים מתוקים אחרים", "טבלאות שוקולד חלב", "טבלאות שוקולד חלב בודד", "טבלאות שוקולד לבן", "טבלאות שוקולד לבן בודד", "טבלאות שוקולד מריר", "טבלאות שוקולד מריר בודד", "לקקנים", "מאגדות", "מארזי ילדים", "מסטיקים ללא סוכר", "סוכריות", "סוכריות גומי", "סוכריות גלי", "סוכריות לעיסות", "סוכריות מרעננות", "סוכריות מרשמלו", "סוכריות קשות", "עוגות אישיות", "עוגות מדף ארוחות", "עוגות מוכנות", "עוגיות ביסקוויט", "עוגיות פרימיום", "פופ קורן למיקרו", "פיצוחים", "פתיים", "קרקרים", "שוקולד טבלאות מאגדת", "שוקולד עולם הילדים"],
    "משקאות, קפה, תה ואלכוהול": ["בירה לבנה באריזה", "בירה לבנה בבקבוק חוזר", "בירה לבנה בודד", "בירה ללא אלכוהול", "בירה מאלט", "חליטות פירות וצמחים", "יין אדום", "יין לבן", "יין מבעבע", "יין רוזה", "יינות מתוקים", "יינות תירוש", "ליקרים וקוקטיילים", "מים בבקבוק", "מים מוגזים", "מים מועשרים", "מיץ 100% פרי", "מיץ 100% קר", "מיץ טבעי סחוט מקורר", "משקאות אלכוהולים אחרים", "משקאות וודקה", "משקאות וויסקי", "משקאות חמוציות", "משקאות טקילה", "משקאות מוגזים טעמי לימון ליים", "משקאות מוגזים טעמי לימון ליים דיאט", "משקאות מוגזים טעמי פירות", "משקאות סויה", "משקאות פונקציונלים", "משקאות פונקציונלים/קפה", "משקאות קלים", "משקאות קפה", "משקאות תחליפי חלב אחרים", "משקאות תחליפי חלב מצונן", "משקאות תחליפי חלב עמידים", "משקה מוגז עדין בטעמים", "משקה קולה דיאט", "משקה קולה רגיל", "נקטר", "סודה", "ערק + אניס", "קוניאק", "קפה אספרסו", "קפה טורקי", "קפה נמס", "שמפניה", "תה ירוק", "תה פירות", "תה קר", "תה שחור בטעמים", "תחליפי חלב טופו", "תחליפי קפה", "תרכיז משקה אחרים", "תרכיזי משקה"],
    "עולם התינוקות": ["אביזרי טיפול לתינוק", "דייסות", "חיתולים", "מגבונים לחים", "מזון תינוקות/ילדים אחר", "מחיות לתינוק", "משטחי החתלה", "פורמולה", "תחליפי חלב אם חלבי", "תחליפי חלב אם צמחי", "תכשיר הגנה מהשמש לילדים", "תכשירי הגנה מהשמש לתינוקות"],
    "פארם, טיפוח אישי והיגיינה": ["אביזרי טיפוח ריפוי והגיינה", "אביזרי קיצוף", "אביזרים לשיער", "אפטרשייב", "בישום יוקרתי", "דאודורנט לגברים", "דאודורנט נשים", "הגיינה נשית", "היגיינת מבוגרים", "הסרת שיער קרם /גל", "חיטוי ידיים", "טיפוח גוף יד ורגל", "מברשות שיניים", "מוצרי אפטר שייב", "מוצרי היגיינה", "מוצרי ויטמינים", "מוצרי שיניים אחר", "מוצרי תרופות", "מוצרים לטיפול בשיער", "מוצרים לעיצוב השיער", "מוצרים מן הטבע", "מסירי שיער שעווה", "מרכך שיער", "משחות שיניים", "ניקוי הפנים רגיל", "סבון לגוף", "סבון מוצק", "סבון נוזל לידיים/משאבה", "סבון נוזלי לידיים/משאבה", "סבון רחצה לגבר", "סכיני גילוח חד פעמי", "סכיני/מכשירי גילוח גברים", "סכיני/מכשירי גילוח נשים", "צבעי שיער", "קרם נגד קמטים", "קרם עיניים", "קרם פנים", "שטיפת פה", "שמפו", "שמפו לגבר", "שמפו+מרכך", "שמפו/מרכך לילדים", "שמפו/מרכך נגד קשקשים", "תכשירי הגנה מהשמש לגוף", "תכשירי הגנה מהשמש לפנים", "תכשירים לגילוח"],
    "ניקיון, כביסה ואחזקת הבית": ["חומרים לכביסה", "חומרים למדיח", "מגבות נייר", "מוצרי אקונומיקה", "מטהר אויר אוטומטי", "מטהר אויר חשמלי", "מטהר אויר לרכב", "מטהר אויר נרות ודקורטיבי", "מטהר אויר ספריי", "מטהרי אויר נטול גז תרסיסים", "מטליות ניקוי", "מטליות רצפה", "מסיר אבן", "מסירי אבנית וניקוי מכונות כביסה", "מסירי כתמים", "מסירי שומנים", "מרכך כביסה", "נוזל כלים", "ניילונים לכביסה", "נייר טואלט", "ניקוי אמבטיות", "ניקוי אסלות", "ניקוי כללי", "שקיות אשפה", "תכשירי טיפול וניקוי חלונות", "תכשירי טיפול וניקוי מראות", "תכשירי טיפול לעובש ולוחות", "תכשירי ניקוי רצפות", "תכשירי ניקוי שטיחים", "תכשירים לניקוי חלונות", "תכשירים לפתיחת סתימות"],
    "חד-פעמי, אריזה ואירוח": ["כוסות חד פעמי לשתייה חמה 40 יח'", "כלי אוכל והגשה", "כלי איחסון", "כלים חד פעמיים", "כפפות", "מוצרי ניילון נצמד", "ממחטות אף", "מפות חד פעמי", "מפיות חד פעמי", "רדיד אלומיניום", "שקיות אוכל", "תבניות אפיה ח\"פ"],
    "עולם הבית, טקסטיל ופנאי": ["אביזרים אחרים", "בגדים", "ביגוד תחתון", "גרבי נשים (3) נגד החלקה ארומה", "גרבים וגרביונים", "טקסטיל לבית", "כלים לפילטר מים וסודה", "מוצרי אלקטרוניקה", "מוצרי חשמל בית קטנים", "מיקסרים", "נרות וגפרורים", "סוללות", "סיגריות", "סירים ומחבתות", "ציוד למנגל", "ציוד משרדי"],
    "מזון וציוד לבעלי חיים": ["אביזרי בעח", "חטיפי דגים ופירות לבוגרים", "חטיפי דגים לילדים", "מזון בעלי חיים אחר", "מזון לחתולים יבש", "מזון לחתולים משומר", "מזון לכלבים יבש", "שימורי מזון כלבים"]
}

SUB_TO_SUPER_MAP: Dict[str, str] = {
    sub.strip(): super_cat
    for super_cat, subs in SUPER_CATEGORIES_TREE.items()
    for sub in subs
}

def infer_sub_and_super_category(raw_sub: str, item_name: str = "") -> tuple[str, str]:
    sub = str(raw_sub or "").strip()
    if sub in SUB_TO_SUPER_MAP:
        return sub, SUB_TO_SUPER_MAP[sub]
    if sub in SUPER_CATEGORIES_TREE:
        return sub, sub

    combined = f"{sub} {item_name}".strip()
    best_sub = None
    best_super = None
    for known_sub, sup in SUB_TO_SUPER_MAP.items():
        if len(known_sub) >= 3 and known_sub in combined:
            if not best_sub or len(known_sub) > len(best_sub):
                best_sub = known_sub
                best_super = sup

    if best_sub and best_super:
        return (sub if sub else best_sub), best_super

    if re.search(r"חלב|קוטג|גבינה|יוגורט|חמאה|שמנת|ביצים|מעדן|לאבנה|שוקו", combined):
        return (sub or "מוצרי חלב כללי"), "מוצרי חלב, ביצים ומעדנייה"
    if re.search(r"עגבני|מלפפון|פלפל|בצל|גזר|חסה|תפוח|בננ|אבוקדו|לימון|פטריות|כרוב|שום", combined):
        return (sub or "ירקות ופירות"), "פירות וירקות טריים"
    if re.search(r"עוף|בקר|הודו|כבש|סטייק|טחון|שניצל|פרגית|אנטריקוט", combined):
        return (sub or "בשר ועוף"), "קצביה, בשר ועוף טרי"
    if re.search(r"ניקוי|כביסה|אקונומיקה|כלים|טואלט|מרכך|אשפה|מגבות נייר", combined):
        return (sub or "ניקיון כללי"), "ניקיון, כביסה ואחזקת הבית"
    if re.search(r"לחם|פיתה|פיתות|לחמני|חלה|בגט|מאפה", combined):
        return (sub or "לחם ומאפים"), "מאפייה, לחם ובצקים טריים"
    if re.search(r"קולה|מים|סודה|בירה|יין|מיץ|נקטר|קפה|תה|משקה", combined):
        return (sub or "משקאות"), "משקאות, קפה, תה ואלכוהול"
    if re.search(r"שמפו|סבון|משחת שיניים|דאודורנט|גילוח|קרם", combined):
        return (sub or "טיפוח והיגיינה"), "פארם, טיפוח אישי והיגיינה"
    if re.search(r"שוקולד|חטיף|במבה|ביסלי|בייגלה|עוגיות|וופל|סוכריות|מסטיק", combined):
        return (sub or "חטיפים ומתוקים"), "חטיפים, ממתקים ומתוקים"

    return (sub or "מכולת כללי"), "מכולת, יבשים ומזווה"

def norm_text(s: Any) -> str:
    s = str(s or "")
    s = re.sub(r'[\u05F4\u201C\u201D\u201E\u201F"״]', '"', s)
    s = re.sub(r"[\u05F3\u2018\u2019\u201A\u201B'`׳]", "'", s)
    return re.sub(r"\s+", " ", s).strip()

EMBEDDED_CHAINS = [
    "רמי לוי", "אושר עד", "כל בו חצי חינם", "יוניברס",
    "Carrefour hyper (קרפור היפר)", "שופרסל דיל", "יוחננוף"
]

def mk_price(reg: float, promo: Optional[float] = None, desc: str = "") -> Dict:
    return {
        "finalPrice": promo if promo is not None else reg,
        "regularPrice": reg,
        "isPromo": promo is not None,
        "promoDesc": desc
    }

def mk_chain_prices(rl: float, oa: float, hh: float, un: float, cf: float, sd: float, yh: float, promo_chain: str = "", promo_val: Optional[float] = None) -> Dict:
    mapping = {
        "רמי לוי": rl,
        "אושר עד": oa,
        "כל בו חצי חינם": hh,
        "יוניברס": un,
        "Carrefour hyper (קרפור היפר)": cf,
        "שופרסל דיל": sd,
        "יוחננוף": yh
    }
    res = {}
    for ch, val in mapping.items():
        if ch == promo_chain and promo_val is not None:
            res[ch] = mk_price(val, promo_val, "מבצע מיוחד")
        else:
            res[ch] = mk_price(val)
    return res

# =====================================================================
# 2. קטלוג 32 מוצרי יסוד מלאים (מובנה כברירת מחדל לפני העלאת אקסל)
# =====================================================================
EMBEDDED_CATALOG = [
    {"barcode": "7290000042015", "name": "חלב טרי תנובה 3% קרטון 1 ליטר", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "חלב", "supplier": "תנובה", "prices": mk_chain_prices(6.80, 6.70, 6.90, 6.80, 6.90, 7.10, 6.90)},
    {"barcode": "7290004127329", "name": "קוטג' תנובה 5% 250 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "קוטג'", "supplier": "תנובה", "prices": mk_chain_prices(6.20, 6.10, 6.40, 6.20, 6.30, 6.50, 6.30)},
    {"barcode": "7290000042459", "name": "גבינה לבנה תנובה 5% 250 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "גבינות לבנות", "supplier": "תנובה", "prices": mk_chain_prices(5.90, 5.80, 6.20, 5.90, 6.10, 6.40, 6.00)},
    {"barcode": "7290002857129", "name": "גבינה צהובה עמק תנובה פרוס 28% 400 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "גבינות צהובות מדף", "supplier": "תנובה", "prices": mk_chain_prices(21.90, 20.90, 22.90, 21.50, 22.40, 23.50, 21.90)},
    {"barcode": "7290000123455", "name": "ביצים רגילות גודל L מארז 12 יח'", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "ביצים רגילות", "supplier": "תנובה", "prices": mk_chain_prices(13.90, 13.80, 14.20, 13.90, 14.10, 14.20, 14.00)},
    {"barcode": "7290107940016", "name": "יוגורט דנונה פרו 20 גרם חלבון שטראוס 200 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "יוגורט חלבון", "supplier": "שטראוס", "prices": mk_chain_prices(5.50, 5.20, 5.90, 5.50, 5.80, 6.20, 5.60, "רמי לוי", 4.90)},
    {"barcode": "7290000042602", "name": "חמאה תנובה 200 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "חמאה", "supplier": "תנובה", "prices": mk_chain_prices(8.90, 8.50, 9.40, 8.90, 9.20, 9.60, 9.00)},
    {"barcode": "7290000561127", "name": "חומוס אחלה חלק שטראוס 400 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "סלטי חומוס חלק", "supplier": "שטראוס", "prices": mk_chain_prices(9.90, 8.90, 11.90, 10.50, 10.90, 12.50, 9.90)},
    {"barcode": "1001", "name": 'עגבניה חממה מובחרת שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "עגבניה", "supplier": "חקלאי", "prices": mk_chain_prices(4.90, 4.90, 6.90, 5.90, 6.50, 7.90, 5.90, "רמי לוי", 3.90)},
    {"barcode": "1002", "name": 'מלפפון חממה טרי שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "מלפפון", "supplier": "חקלאי", "prices": mk_chain_prices(4.90, 4.50, 6.50, 5.50, 5.90, 6.90, 5.50)},
    {"barcode": "1003", "name": 'בצל יבש שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "בצל", "supplier": "חקלאי", "prices": mk_chain_prices(3.90, 3.50, 4.90, 3.90, 4.50, 5.50, 3.90)},
    {"barcode": "1004", "name": 'תפוח אדמה לבן שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "תפוח אדמה", "supplier": "חקלאי", "prices": mk_chain_prices(3.90, 3.80, 4.90, 4.20, 4.50, 5.20, 4.00)},
    {"barcode": "1005", "name": 'פלפל אדום גמבה שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "פלפלים", "supplier": "חקלאי", "prices": mk_chain_prices(6.90, 6.50, 8.90, 7.50, 7.90, 9.90, 6.90)},
    {"barcode": "1006", "name": 'בננות מובחרות שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "בננות", "supplier": "חקלאי", "prices": mk_chain_prices(5.90, 5.50, 7.90, 6.50, 6.90, 8.50, 5.90)},
    {"barcode": "1007", "name": 'תפוח עץ זהוב/פינק ליידי שקיל 1 ק"ג', "superCategory": "פירות וירקות טריים", "subCategory": "תפוח עץ", "supplier": "חקלאי", "prices": mk_chain_prices(8.90, 7.90, 10.90, 9.50, 9.90, 11.90, 8.90)},
    {"barcode": "2001", "name": 'חזה עוף טרי שלם/פרוס 1 ק"ג', "superCategory": "קצביה, בשר ועוף טרי", "subCategory": "חלקי עוף טרי", "supplier": "קצביה", "prices": mk_chain_prices(32.90, 31.90, 36.90, 33.90, 34.90, 38.90, 32.90)},
    {"barcode": "2002", "name": 'בשר בקר טחון טרי 1 ק"ג', "superCategory": "קצביה, בשר ועוף טרי", "subCategory": "בשר טחון טרי", "supplier": "קצביה", "prices": mk_chain_prices(44.90, 42.90, 49.90, 45.90, 47.90, 52.90, 44.90)},
    {"barcode": "2003", "name": 'פילה סלמון נורווגי קפוא בואקום 1 ק"ג', "superCategory": "קפואים וגלידות", "subCategory": "דגים קפואים בואקום", "supplier": "בלדי", "prices": mk_chain_prices(69.90, 64.90, 79.90, 72.90, 74.90, 84.90, 69.90)},
    {"barcode": "7290000101019", "name": "לחם אחיד פרוס אנג'ל / ברמן 750 גרם", "superCategory": "מאפייה, לחם ובצקים טריים", "subCategory": "לחם מפוקח ארוז", "supplier": "אנג'ל", "prices": mk_chain_prices(7.90, 7.50, 8.20, 7.90, 8.10, 8.30, 7.90)},
    {"barcode": "7290000102023", "name": "פיתות טריות מארז 10 יח' מאפייה", "superCategory": "מאפייה, לחם ובצקים טריים", "subCategory": "פיתות ארוחות", "supplier": "מאפייה", "prices": mk_chain_prices(8.90, 7.90, 10.90, 9.50, 9.90, 11.50, 8.90)},
    {"barcode": "729001000101", "name": "פסטה ספירלה אסם / טעמן 500 גרם", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "פסטה", "supplier": "אסם", "prices": mk_chain_prices(4.50, 3.90, 5.50, 4.80, 4.90, 5.90, 4.50, "רמי לוי", 3.50)},
    {"barcode": "7290000066318", "name": 'אורז פרסי קלאסי סוגת 1 ק"ג', "superCategory": "מכולת, יבשים ומזווה", "subCategory": "אורז", "supplier": "סוגת", "prices": mk_chain_prices(8.90, 8.50, 10.50, 9.20, 9.50, 10.90, 8.90)},
    {"barcode": "7290000112233", "name": "שמן קנולה מזוכך עץ הזית 1 ליטר", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שמנים רגילים", "supplier": "עץ הזית", "prices": mk_chain_prices(9.90, 9.50, 11.90, 10.50, 10.90, 12.50, 9.90)},
    {"barcode": "7290000114455", "name": "שמן זית כתית מעולה יד מרדכי 750 מ\"ל", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שמן זית", "supplier": "יד מרדכי", "prices": mk_chain_prices(34.90, 32.90, 39.90, 35.90, 36.90, 41.90, 34.90)},
    {"barcode": "7290000116677", "name": "רביעיית שימורי טונה בשמן סטארקיסט 4×160 גרם", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שימורי טונה", "supplier": "סטארקיסט", "prices": mk_chain_prices(24.90, 23.90, 27.90, 25.50, 26.50, 28.90, 24.90)},
    {"barcode": "7290000066110", "name": 'סוכר לבן סוגת אריזת 1 ק"ג', "superCategory": "מכולת, יבשים ומזווה", "subCategory": "אריזות סוכר", "supplier": "סוגת", "prices": mk_chain_prices(5.50, 4.90, 6.50, 5.80, 5.90, 6.90, 5.50)},
    {"barcode": "7290000066226", "name": 'קמח חיטה לבן בהיר 1 ק"ג', "superCategory": "מכולת, יבשים ומזווה", "subCategory": "קמח", "supplier": "סוגת", "prices": mk_chain_prices(4.50, 3.90, 5.50, 4.80, 4.90, 5.90, 4.50)},
    {"barcode": "7290000171111", "name": "קפה נמס מגורען טסטרס צ'ויס 200 גרם", "superCategory": "משקאות, קפה, תה ואלכוהול", "subCategory": "קפה נמס", "supplier": "אסם נסטלה", "prices": mk_chain_prices(29.90, 27.90, 33.90, 30.90, 31.90, 34.90, 29.90)},
    {"barcode": "7290000172224", "name": "תה קר פיוז טי (Fuze Tea) אפרסק 1.5 ליטר", "superCategory": "משקאות, קפה, תה ואלכוהול", "subCategory": "תה קר", "supplier": "החברה המרכזית", "prices": mk_chain_prices(7.90, 7.50, 8.90, 8.20, 8.50, 9.20, 7.90, "אושר עד", 6.90)},
    {"barcode": "7290000000114", "name": "חטיף במבה אסם 80 גרם", "superCategory": "חטיפים, ממתקים ומתוקים", "subCategory": "חטיפים", "supplier": "אסם", "prices": mk_chain_prices(3.90, 3.50, 4.50, 4.00, 4.20, 4.90, 3.90)},
    {"barcode": "3002", "name": "נוזל כלים פיירי לימון 1 ליטר", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "נוזל כלים", "supplier": "פרוקטר", "prices": mk_chain_prices(11.50, 10.90, 12.50, 11.90, 12.20, 13.90, 11.90)},
    {"barcode": "3005", "name": "נייר טואלט לילי שמורת הטבע 30 גלילים", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "נייר טואלט", "supplier": "חוגלה קימברלי", "prices": mk_chain_prices(34.90, 32.90, 38.90, 35.90, 36.90, 39.90, 34.90)},
    {"barcode": "3006", "name": "ג'ל כביסה מרוכז פרסיל 2.5 ליטר", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "חומרים לכביסה", "supplier": "הנקל", "prices": mk_chain_prices(29.90, 27.90, 34.90, 31.90, 32.90, 36.90, 29.90)},
    {"barcode": "4001", "name": "שמפו פינוק לשיער רגיל 700 מ\"ל", "superCategory": "פארם, טיפוח אישי והיגיינה", "subCategory": "שמפו", "supplier": "יוניליוור", "prices": mk_chain_prices(10.90, 9.90, 12.90, 11.50, 11.90, 13.90, 10.90)},
    {"barcode": "4002", "name": "משחת שיניים קולגייט טוטאל 100 מ\"ל", "superCategory": "פארם, טיפוח אישי והיגיינה", "subCategory": "משחות שיניים", "supplier": "קולגייט", "prices": mk_chain_prices(11.90, 10.50, 13.90, 12.50, 12.90, 14.90, 11.90)}
]

# =====================================================================
# 3. סל מומלץ של 30 מוצרי בסיס ישראליים
# =====================================================================
DEFAULT_30_BASKET_RULES = [
    {"id": "r1", "name": "חלב טרי 3%", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "חלב", "keywords": ["חלב", "3%"], "excludeWords": [], "weeklyQty": 3, "measureMode": "units"},
    {"id": "r2", "name": "קוטג' 5%", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "קוטג'", "keywords": ["קוטג"], "excludeWords": [], "weeklyQty": 2, "measureMode": "units"},
    {"id": "r3", "name": "גבינה לבנה 5%", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "גבינות לבנות", "keywords": ["גבינה", "לבנה"], "excludeWords": [], "weeklyQty": 2, "measureMode": "units"},
    {"id": "r4", "name": "גבינה צהובה עמק", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "גבינות צהובות מדף", "keywords": ["צהובה"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r5", "name": "ביצים L (תבנית 12)", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "ביצים רגילות", "keywords": ["ביצים"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r6", "name": "יוגורט חלבון", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "יוגורט חלבון", "keywords": ["יוגורט"], "excludeWords": [], "weeklyQty": 4, "measureMode": "units"},
    {"id": "r7", "name": "חמאה 200 גרם", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "חמאה", "keywords": ["חמאה"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r8", "name": "סלט חומוס חלק", "superCategory": "מוצרי חלב, ביצים ומעדנייה", "subCategory": "סלטי חומוס חלק", "keywords": ["חומוס"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r9", "name": "עגבניה", "superCategory": "פירות וירקות טריים", "subCategory": "עגבניה", "keywords": ["עגבניה"], "excludeWords": [], "weeklyQty": 2, "measureMode": "weight"},
    {"id": "r10", "name": "מלפפון", "superCategory": "פירות וירקות טריים", "subCategory": "מלפפון", "keywords": ["מלפפון"], "excludeWords": [], "weeklyQty": 2, "measureMode": "weight"},
    {"id": "r11", "name": "בצל יבש", "superCategory": "פירות וירקות טריים", "subCategory": "בצל", "keywords": ["בצל"], "excludeWords": ["ירוק"], "weeklyQty": 1.5, "measureMode": "weight"},
    {"id": "r12", "name": "תפוח אדמה", "superCategory": "פירות וירקות טריים", "subCategory": "תפוח אדמה", "keywords": ["תפוח", "אדמה"], "excludeWords": [], "weeklyQty": 2, "measureMode": "weight"},
    {"id": "r13", "name": "פלפל אדום / גמבה", "superCategory": "פירות וירקות טריים", "subCategory": "פלפלים", "keywords": ["פלפל"], "excludeWords": [], "weeklyQty": 1, "measureMode": "weight"},
    {"id": "r14", "name": "בננות", "superCategory": "פירות וירקות טריים", "subCategory": "בננות", "keywords": ["בננות"], "excludeWords": [], "weeklyQty": 1.5, "measureMode": "weight"},
    {"id": "r15", "name": "תפוח עץ", "superCategory": "פירות וירקות טריים", "subCategory": "תפוח עץ", "keywords": ["תפוח", "עץ"], "excludeWords": [], "weeklyQty": 1.5, "measureMode": "weight"},
    {"id": "r16", "name": "חזה עוף טרי", "superCategory": "קצביה, בשר ועוף טרי", "subCategory": "חלקי עוף טרי", "keywords": ["חזה", "עוף"], "excludeWords": [], "weeklyQty": 1.5, "measureMode": "weight"},
    {"id": "r17", "name": "בשר בקר טחון טרי", "superCategory": "קצביה, בשר ועוף טרי", "subCategory": "בשר טחון טרי", "keywords": ["טחון"], "excludeWords": [], "weeklyQty": 1, "measureMode": "weight"},
    {"id": "r18", "name": "פילה סלמון", "superCategory": "קפואים וגלידות", "subCategory": "דגים קפואים בואקום", "keywords": ["סלמון"], "excludeWords": [], "weeklyQty": 1, "measureMode": "weight"},
    {"id": "r19", "name": "לחם אחיד פרוס", "superCategory": "מאפייה, לחם ובצקים טריים", "subCategory": "לחם מפוקח ארוז", "keywords": ["לחם", "פרוס"], "excludeWords": [], "weeklyQty": 2, "measureMode": "units"},
    {"id": "r20", "name": "פיתות מארז", "superCategory": "מאפייה, לחם ובצקים טריים", "subCategory": "פיתות ארוחות", "keywords": ["פיתות"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r21", "name": "פסטה 500 גרם", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "פסטה", "keywords": ["פסטה"], "excludeWords": [], "weeklyQty": 2, "measureMode": "units"},
    {"id": "r22", "name": "אורז פרסי 1 ק\"ג", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "אורז", "keywords": ["אורז"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r23", "name": "שמן קנולה 1 ליטר", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שמנים רגילים", "keywords": ["שמן", "קנולה"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r24", "name": "שמן זית 750 מ\"ל", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שמן זית", "keywords": ["שמן", "זית"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r25", "name": "רביעיית שימורי טונה", "superCategory": "מכולת, יבשים ומזווה", "subCategory": "שימורי טונה", "keywords": ["טונה"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r26", "name": "קפה נמס מגורען", "superCategory": "משקאות, קפה, תה ואלכוהול", "subCategory": "קפה נמס", "keywords": ["קפה", "נמס"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r27", "name": "תה קר פיוז טי 1.5 ליטר", "superCategory": "משקאות, קפה, תה ואלכוהול", "subCategory": "תה קר", "keywords": ["תה", "קר"], "excludeWords": [], "weeklyQty": 2, "measureMode": "units"},
    {"id": "r28", "name": "נוזל כלים", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "נוזל כלים", "keywords": ["נוזל", "כלים"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r29", "name": "נייר טואלט מארז", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "נייר טואלט", "keywords": ["נייר", "טואלט"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"},
    {"id": "r30", "name": "ג'ל כביסה", "superCategory": "ניקיון, כביסה ואחזקת הבית", "subCategory": "חומרים לכביסה", "keywords": ["כביסה"], "excludeWords": [], "weeklyQty": 1, "measureMode": "units"}
]

DEFAULT_SITE_CONFIG = {
    "adminPin": "1234",
    "design": {
        "brandTitle": "SmartBasket IL",
        "brandSubtitle": "השוואת מחירים חכמה לפי יחידות מידה (ליטר/ק\"ג/יח')",
        "winnerBadgeText": "🏆 הרשת המשתלמת ביותר",
        "accentTheme": "emerald",     # emerald | blue | indigo | rose | amber
        "darkMode": False,
        "cardRadius": "rounded-3xl",  # rounded-xl | rounded-2xl | rounded-3xl
        "fontScale": "normal",        # compact | normal | large
        "showWinnerBanner": True,
        "showAnnualSavings": True,
        "showNormalizedBadges": True,
        "showTableFooter": True,
        "requireLoginScreen": True
    },
    "formulas": {
        "missingItemStrategy": "avg",   # avg (ממוצע הרשתות) | max (המחיר היקר ביותר) | zero (התעלם)
        "rankingPriority": "coverage_first", # coverage_first (כיסוי מלא קודם) | lowest_price_only (מחיר נמוך נטו)
        "annualWeeksMultiplier": 52,
        "privateLabelDiscountFactor": 1.0, # 1.0 = ללא הטיה, 0.95 = העדפה של 5% למותג פרטי
        "householdFactors": {
            "single": 0.5,
            "couple": 0.75,
            "family": 1.0,
            "large": 1.5
        }
    },
    "defaultBasketRules": DEFAULT_30_BASKET_RULES
}

def load_initial_state() -> Dict[str, Any]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("catalog") and data.get("chains"):
                    return data
        except Exception:
            pass
    return {"catalog": EMBEDDED_CATALOG, "chains": EMBEDDED_CHAINS}

def save_state_to_cache(catalog: List[Dict], chains: List[str]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"catalog": catalog, "chains": chains}, f, ensure_ascii=False)
    except Exception:
        pass

def load_site_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = json.loads(json.dumps(DEFAULT_SITE_CONFIG))
                if "design" in saved:
                    merged["design"].update(saved["design"])
                if "formulas" in saved:
                    merged["formulas"].update(saved["formulas"])
                if "defaultBasketRules" in saved and isinstance(saved["defaultBasketRules"], list):
                    merged["defaultBasketRules"] = saved["defaultBasketRules"]
                if "adminPin" in saved:
                    merged["adminPin"] = str(saved["adminPin"])
                return merged
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_SITE_CONFIG))

def save_site_config_to_disk(cfg: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

STATE = load_initial_state()
SITE_CONFIG = load_site_config()

def parse_price_number(v: Any) -> float:
    if pd.isna(v) or v == "" or isinstance(v, bool):
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v) if 0.05 <= float(v) < 5000 else float("nan")
    s = str(v).replace("₪", "").replace('ש"ח', "").replace("שח", "").replace(" ", "").replace(",", ".").strip()
    try:
        n = float(s)
        return n if 0.05 <= n < 5000 else float("nan")
    except ValueError:
        return float("nan")

def is_summary_or_junk_row(name: str) -> bool:
    if not name or len(name) < 2:
        return True
    junk_patterns = r'^(סה"כ|סהכ|סך הכל|סכום כולל|ממוצע|תוויות שורה|תוויות עמודה|grand total|total|average|\(ריק\)|blank)$'
    if re.search(junk_patterns, name, re.IGNORECASE):
        return True
    if "סכום כולל" in name or 'סה"כ כללי' in name:
        return True
    return False

def parse_single_sheet(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if df is None or len(df) < 2:
        return None

    header_idx = 0
    best_score = -1
    for i in range(min(40, len(df))):
        row_vals = [norm_text(x) for x in df.iloc[i].values if pd.notna(x) and norm_text(x)]
        if len(row_vals) < 2:
            continue
        non_num = sum(
            1 for s in row_vals
            if math.isnan(parse_price_number(s)) and not re.search(r"^ממוצע של|^סכום של|תוויות עמודה", s)
        )
        bonus = sum(3 for s in row_vals if re.search(r"תיאור פריט|שם מוצר|תוויות שורה|רמי לוי|אושר עד|שופרסל|יוחננוף|חצי חינם|קרפור|יוניברס|מחיר|רשת", s, re.IGNORECASE))
        score = non_num + bonus
        if score > best_score:
            best_score = score
            header_idx = i

    headers = [norm_text(x) if pd.notna(x) else "" for x in df.iloc[header_idx].values]
    df_rows = df.iloc[header_idx + 1:].reset_index(drop=True)
    if len(df_rows) == 0:
        return None

    def find_col(pattern: str) -> int:
        for idx, h in enumerate(headers):
            if h and re.search(pattern, h, re.IGNORECASE):
                return idx
        return -1

    chain_col = find_col(r"^(רשת|שם רשת|chain|קמעונאי)$")
    desc_col = find_col(r"תיאור פריט|שם פריט|שם מוצר|תוויות שורה|יות שורה|מוצר/פריט")
    reg_price_col = find_col(r"מחיר מייצג|מחיר רגיל|^מחיר$|מחיר יחידה")
    promo_price_col = find_col(r"מחיר מבצע מייצג|מחיר מבצע")
    promo_desc_col = find_col(r"תיאור מבצע|פירוט מבצע")
    cat_col = find_col(r"קטגוריה|תת-קטגוריה|מחלקה")
    sup_col = find_col(r"ספק|יצרן|מותג")
    bc_col = find_col(r'^(ברקוד|קוד פריט|barcode|מק"ט|מקט)$')

    if chain_col >= 0 and desc_col >= 0 and (reg_price_col >= 0 or promo_price_col >= 0):
        chain_set = []
        by_key = {}
        for idx, row in df_rows.iterrows():
            chain = norm_text(row[chain_col]) if pd.notna(row[chain_col]) else ""
            name = norm_text(row[desc_col]) if pd.notna(row[desc_col]) else ""
            if not chain or is_summary_or_junk_row(name) or is_summary_or_junk_row(chain):
                continue
            reg_p = parse_price_number(row[reg_price_col]) if reg_price_col >= 0 else float("nan")
            sale_p = parse_price_number(row[promo_price_col]) if promo_price_col >= 0 else float("nan")
            promo_desc = norm_text(row[promo_desc_col]) if (promo_desc_col >= 0 and pd.notna(row[promo_desc_col])) else ""
            final_price = sale_p if not math.isnan(sale_p) else reg_p
            if math.isnan(final_price):
                continue
            if chain not in chain_set:
                chain_set.append(chain)
            raw_cat = norm_text(row[cat_col]) if (cat_col >= 0 and pd.notna(row[cat_col])) else ""
            sub_cat, super_cat = infer_sub_and_super_category(raw_cat, name)
            supplier = norm_text(row[sup_col]) if (sup_col >= 0 and pd.notna(row[sup_col])) else ""
            if not supplier:
                brand_match = re.search(r"יצרן/מותג:\s*([^,]+)", name)
                if brand_match:
                    supplier = brand_match.group(1).strip()
            bc = norm_text(row[bc_col]) if (bc_col >= 0 and pd.notna(row[bc_col])) else ""
            bc_clean = re.sub(r"\.0$", "", bc)
            key = f"bc_{bc_clean}" if len(bc_clean) >= 5 else f"nm_{name}"
            p_obj = {
                "finalPrice": round(final_price, 2),
                "regularPrice": round(reg_p if not math.isnan(reg_p) else final_price, 2),
                "isPromo": not math.isnan(sale_p) and (math.isnan(reg_p) or sale_p < reg_p),
                "promoDesc": promo_desc
            }
            if key in by_key:
                ex = by_key[key]
                if chain not in ex["prices"] or final_price < ex["prices"][chain]["finalPrice"]:
                    ex["prices"][chain] = p_obj
            else:
                by_key[key] = {
                    "barcode": bc_clean or str(100000 + idx),
                    "name": name,
                    "superCategory": super_cat,
                    "subCategory": sub_cat,
                    "supplier": supplier,
                    "prices": {chain: p_obj}
                }
        if by_key and chain_set:
            return {"catalog": list(by_key.values()), "chains": chain_set}

    name_idx = desc_col if desc_col >= 0 else 0
    if desc_col < 0:
        best_text_col = 0
        best_text_count = -1
        for c in range(min(4, len(headers))):
            cnt = sum(
                1 for r in range(min(200, len(df_rows)))
                if pd.notna(df_rows.iloc[r, c])
                and len(norm_text(df_rows.iloc[r, c])) >= 3
                and math.isnan(parse_price_number(df_rows.iloc[r, c]))
            )
            if cnt > best_text_count:
                best_text_count = cnt
                best_text_col = c
        name_idx = best_text_col

    chain_cols = []
    ignore_header_pat = r'^(סכום כולל|סה"כ|סהכ|ממוצע|הפרש|ברקוד|קטגוריה|תת-קטגוריה|ספק|יצרן|מותג|מק"ט|קוד|דירוג|מינימום|מקסימום|grand total|total|average)$'
    for c in range(len(headers)):
        if c in (name_idx, cat_col, sup_col, bc_col) or not headers[c]:
            continue
        if re.search(ignore_header_pat, headers[c], re.IGNORECASE) or "סכום כולל" in headers[c]:
            continue
        valid_prices = sum(
            1 for r in range(min(250, len(df_rows)))
            if not math.isnan(parse_price_number(df_rows.iloc[r, c]))
        )
        if valid_prices >= 1:
            chain_cols.append(c)

    if not chain_cols:
        return None

    chains = [headers[c] for c in chain_cols]
    catalog = []
    current_group_category = ""

    for idx, row in df_rows.iterrows():
        name = norm_text(row[name_idx]) if pd.notna(row[name_idx]) else ""
        if is_summary_or_junk_row(name):
            continue

        prices = {}
        for c in chain_cols:
            p_val = parse_price_number(row[c])
            if not math.isnan(p_val):
                prices[headers[c]] = {
                    "finalPrice": round(p_val, 2),
                    "regularPrice": round(p_val, 2),
                    "isPromo": False,
                    "promoDesc": ""
                }

        if not prices:
            if name in SUB_TO_SUPER_MAP or name in SUPER_CATEGORIES_TREE:
                current_group_category = name
            continue

        raw_sub = norm_text(row[cat_col]) if (cat_col >= 0 and pd.notna(row[cat_col]) and norm_text(row[cat_col])) else current_group_category
        sub_cat, super_cat = infer_sub_and_super_category(raw_sub, name)

        supplier = norm_text(row[sup_col]) if (sup_col >= 0 and pd.notna(row[sup_col])) else ""
        if not supplier:
            brand_match = re.search(r"יצרן/מותג:\s*([^,]+)", name)
            if brand_match:
                supplier = brand_match.group(1).strip()

        bc = norm_text(row[bc_col]) if (bc_col >= 0 and pd.notna(row[bc_col])) else str(100000 + idx)
        bc_clean = re.sub(r"\.0$", "", bc)

        catalog.append({
            "barcode": bc_clean,
            "name": name,
            "superCategory": super_cat,
            "subCategory": sub_cat,
            "supplier": supplier,
            "prices": prices
        })

    if not catalog:
        return None
    return {"catalog": catalog, "chains": chains}


@app.post("/api/upload-excel")
async def upload_excel_catalog(file: UploadFile = File(...), pin: str = Form("1234")):
    if pin != SITE_CONFIG.get("adminPin", "1234"):
        raise HTTPException(status_code=403, detail="סיסמת מנהל שגויה")
    try:
        contents = await file.read()
        fname = (file.filename or "").lower()
        if fname.endswith(".csv"):
            try:
                df_csv = pd.read_csv(io.BytesIO(contents), header=None, encoding="utf-8")
            except UnicodeDecodeError:
                df_csv = pd.read_csv(io.BytesIO(contents), header=None, encoding="cp1255")
            excel_data = {"CSV": df_csv}
        else:
            excel_data = pd.read_excel(io.BytesIO(contents), sheet_name=None, header=None)

        best_result = None
        best_score = -1

        for sheet_name, df in excel_data.items():
            parsed = parse_single_sheet(df)
            if parsed:
                score = len(parsed["catalog"]) * max(1, len(parsed["chains"]))
                if score > best_score:
                    best_score = score
                    best_result = parsed

        if not best_result:
            raise ValueError("לא נמצאו נתוני מוצרים ומחירי רשתות תקינים באף אחד מגיליונות הקובץ.")

        STATE["catalog"] = best_result["catalog"]
        STATE["chains"] = best_result["chains"]
        save_state_to_cache(STATE["catalog"], STATE["chains"])
        return {"catalog": STATE["catalog"], "chains": STATE["chains"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/reset-catalog")
async def reset_embedded_catalog(payload: Dict[str, Any] = Body(...)):
    if str(payload.get("pin", "")) != SITE_CONFIG.get("adminPin", "1234"):
        raise HTTPException(status_code=403, detail="סיסמת מנהל שגויה")
    STATE["catalog"] = EMBEDDED_CATALOG
    STATE["chains"] = EMBEDDED_CHAINS
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
    return {"catalog": STATE["catalog"], "chains": STATE["chains"]}


@app.post("/api/admin/verify-pin")
async def verify_admin_pin(payload: Dict[str, Any] = Body(...)):
    if str(payload.get("pin", "")) == SITE_CONFIG.get("adminPin", "1234"):
        return {"ok": True}
    raise HTTPException(status_code=403, detail="סיסמת מנהל שגויה")


@app.post("/api/admin/save-config")
async def save_admin_config(payload: Dict[str, Any] = Body(...)):
    pin = str(payload.get("pin", ""))
    if pin != SITE_CONFIG.get("adminPin", "1234"):
        raise HTTPException(status_code=403, detail="סיסמת מנהל שגויה - אין הרשאת עריכה")
    new_cfg = payload.get("config", {})
    if "design" in new_cfg:
        SITE_CONFIG["design"].update(new_cfg["design"])
    if "formulas" in new_cfg:
        SITE_CONFIG["formulas"].update(new_cfg["formulas"])
    if "defaultBasketRules" in new_cfg and isinstance(new_cfg["defaultBasketRules"], list):
        SITE_CONFIG["defaultBasketRules"] = new_cfg["defaultBasketRules"]
    if "newPin" in payload and str(payload["newPin"]).strip():
        SITE_CONFIG["adminPin"] = str(payload["newPin"]).strip()
    save_site_config_to_disk(SITE_CONFIG)
    public_cfg = {k: v for k, v in SITE_CONFIG.items() if k != "adminPin"}
    return {"ok": True, "config": public_cfg}


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartBasket IL | פלטפורמת השוואת ואופטימיזציית סל קניות שבועי</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>
    <script crossorigin src="https://unpkg.com/react@18.3.1/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/@babel/standalone@7.25.6/babel.min.js"></script>
    <style>
        body { font-family: 'Heebo', sans-serif; }
        .frosted-backdrop { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
    </style>
</head>
<body>
    <div id="root"></div>

    <script>
        window.addEventListener("error", function(e) {
            var rootEl = document.getElementById("root");
            if (rootEl && rootEl.innerHTML.trim() === "") {
                rootEl.innerHTML = '<div style="padding:24px;margin:24px;background:#fef2f2;border:2px solid #ef4444;border-radius:16px;color:#991b1b;font-family:sans-serif;direction:rtl;">' +
                    '<h2 style="font-weight:900;font-size:18px;margin-bottom:8px;">⚠️ שגיאת טעינה בדפדפן:</h2>' +
                    '<pre style="direction:ltr;text-align:left;background:#fff;padding:12px;border-radius:8px;overflow:auto;">' + (e.message || "Unknown error") + '</pre>' +
                '</div>';
            }
        });
    </script>

    <script type="text/babel">
        const { useState, useEffect, useMemo, useRef } = React;

        const SUPER_CATEGORIES_TREE = __SUPER_CATEGORIES_JSON__;
        const EMBEDDED_CHAINS = __CHAINS_JSON__;
        const EMBEDDED_CATALOG = __CATALOG_JSON__;
        const INITIAL_SITE_CONFIG = __SITE_CONFIG_JSON__;

        const THEME_PALETTES = {
            emerald: {
                name: "אמרלד קלאסי (ירוק)",
                btnPrimary: "bg-emerald-500 hover:bg-emerald-400 text-slate-950",
                btnSolid: "bg-emerald-600 hover:bg-emerald-500 text-white",
                badgeBg: "bg-emerald-100 text-emerald-800",
                winnerGradient: "from-emerald-600 via-emerald-700 to-teal-800",
                winnerRow: "bg-emerald-50/70 border-emerald-300",
                cheapestCell: "bg-emerald-50/80 text-emerald-700"
            },
            blue: {
                name: "כחול רויאל (הייטק)",
                btnPrimary: "bg-blue-500 hover:bg-blue-400 text-white",
                btnSolid: "bg-blue-600 hover:bg-blue-500 text-white",
                badgeBg: "bg-blue-100 text-blue-800",
                winnerGradient: "from-blue-600 via-blue-700 to-indigo-800",
                winnerRow: "bg-blue-50/70 border-blue-300",
                cheapestCell: "bg-blue-50/80 text-blue-700"
            },
            indigo: {
                name: "סגול אינדיגו (פרימיום)",
                btnPrimary: "bg-indigo-500 hover:bg-indigo-400 text-white",
                btnSolid: "bg-indigo-600 hover:bg-indigo-500 text-white",
                badgeBg: "bg-indigo-100 text-indigo-800",
                winnerGradient: "from-indigo-600 via-purple-700 to-slate-900",
                winnerRow: "bg-indigo-50/70 border-indigo-300",
                cheapestCell: "bg-indigo-50/80 text-indigo-700"
            },
            rose: {
                name: "ארגמן אנרגטי (אדום-ורוד)",
                btnPrimary: "bg-rose-500 hover:bg-rose-400 text-white",
                btnSolid: "bg-rose-600 hover:bg-rose-500 text-white",
                badgeBg: "bg-rose-100 text-rose-800",
                winnerGradient: "from-rose-600 via-pink-700 to-slate-900",
                winnerRow: "bg-rose-50/70 border-rose-300",
                cheapestCell: "bg-rose-50/80 text-rose-700"
            },
            amber: {
                name: "זהב חם (כתום-זהב)",
                btnPrimary: "bg-amber-500 hover:bg-amber-400 text-slate-950",
                btnSolid: "bg-amber-600 hover:bg-amber-500 text-white",
                badgeBg: "bg-amber-100 text-amber-900",
                winnerGradient: "from-amber-600 via-orange-700 to-slate-900",
                winnerRow: "bg-amber-50/70 border-amber-300",
                cheapestCell: "bg-amber-50/80 text-amber-800"
            }
        };

        const SUB_TO_SUPER_MAP = {};
        Object.entries(SUPER_CATEGORIES_TREE).forEach(([superCat, subCats]) => {
            subCats.forEach((sub) => { SUB_TO_SUPER_MAP[sub.trim()] = superCat; });
        });

        function resolveSuperCategory(subCatRaw, itemName = "") {
            const sub = String(subCatRaw || "").trim();
            if (SUB_TO_SUPER_MAP[sub]) return SUB_TO_SUPER_MAP[sub];
            if (SUPER_CATEGORIES_TREE[sub]) return sub;
            for (const [knownSub, sup] of Object.entries(SUB_TO_SUPER_MAP)) {
                if (sub && (sub.includes(knownSub) || knownSub.includes(sub))) return sup;
            }
            const combined = `${sub} ${itemName}`;
            if (/חלב|קוטג|גבינה|יוגורט|חמאה|שמנת|ביצים|מעדן/.test(combined)) return "מוצרי חלב, ביצים ומעדנייה";
            if (/עגבני|מלפפון|פלפל|בצל|גזר|חסה|תפוח|בננ|אבוקדו|לימון/.test(combined)) return "פירות וירקות טריים";
            if (/עוף|בקר|הודו|כבש|סטייק|טחון|שניצל/.test(combined)) return "קצביה, בשר ועוף טרי";
            if (/ניקוי|כביסה|אקונומיקה|כלים|טואלט/.test(combined)) return "ניקיון, כביסה ואחזקת הבית";
            return "מכולת, יבשים ומזווה";
        }

        const normText = (s) => String(s ?? "").replace(/["״]/g, '"').replace(/['׳]/g, "'").replace(/\s+/g, " ").trim();
        const cleanSearchableText = (s) => String(s ?? "").toLowerCase().replace(/["״'׳]/g, "").replace(/[-–—_/\\|()+*.,:;!?[\]{}×]/g, " ").replace(/\s+/g, " ").trim();

        const extractTokens = (input) => {
            if (!input) return [];
            const arr = Array.isArray(input) ? input : [input];
            const tokens = [];
            for (let i = 0; i < arr.length; i++) {
                const cleaned = cleanSearchableText(arr[i]);
                if (cleaned) tokens.push(...cleaned.split(" ").filter(Boolean));
            }
            return tokens;
        };

        function matchesTerms(productCleanText, keywordTokens, excludeTokens = []) {
            if (excludeTokens && excludeTokens.length > 0) {
                for (let i = 0; i < excludeTokens.length; i++) {
                    if (productCleanText.includes(excludeTokens[i])) return false;
                }
            }
            if (!keywordTokens || keywordTokens.length === 0) return true;
            for (let i = 0; i < keywordTokens.length; i++) {
                if (!productCleanText.includes(keywordTokens[i])) return false;
            }
            return true;
        }

        function parseProductMetrics(itemName, rawUnitStr = "") {
            const text = normText(`${itemName} ${rawUnitStr}`).toLowerCase();
            const multiMatch = text.match(/(\d+)\s*(?:[x×*]|כפול)\s*(\d+(?:[.,]\d+)?)\s*(ק"ג|קג|קילוגרם|קילו|ליטר|ל'|גרם|גר'|גר|ג'|מ"ל|מל|ג|ל)(?!\w)/i);
            if (multiMatch) {
                const packCount = parseFloat(multiMatch[1]);
                const innerVal = parseFloat(multiMatch[2].replace(",", "."));
                const unit = multiMatch[3];
                const isKgOrL = /^(ק"ג|קג|קילוגרם|קילו|ליטר|ל'|ל)$/.test(unit);
                const totalGramsOrMl = packCount * innerVal * (isKgOrL ? 1000 : 1);
                if (totalGramsOrMl > 0) return { hasWeightVolume: true, totalGramsOrMl, packCount, sizeLabel: `מארז ${packCount}×${innerVal} ${unit}` };
            }
            const singleMatch = text.match(/(?:^|\s|[^\d.])(\d+(?:[.,]\d+)?)\s*(ק"ג|קג|קילוגרם|קילו|ליטר|ל'|גרם|גר'|גר|ג'|מ"ל|מל|kg|ml|gr|g)(?=$|\s|[^\wא-ת])/i);
            if (singleMatch) {
                const val = parseFloat(singleMatch[1].replace(",", "."));
                const unit = singleMatch[2].toLowerCase();
                const isKgOrL = /^(ק"ג|קג|קילוגרם|קילו|ליטר|ל'|kg)$/.test(unit);
                const totalGramsOrMl = val * (isKgOrL ? 1000 : 1);
                if (totalGramsOrMl > 0 && totalGramsOrMl <= 100000) return { hasWeightVolume: true, totalGramsOrMl, packCount: 1, sizeLabel: `${val} ${singleMatch[2]}` };
            }
            if (/לק"ג|לקג|שקיל|1 ק"ג|1 קג/.test(text)) return { hasWeightVolume: true, totalGramsOrMl: 1000, packCount: 1, sizeLabel: '1 ק"ג / ליטר' };
            return { hasWeightVolume: false, totalGramsOrMl: 0, packCount: 1, sizeLabel: "יחידה בודדת" };
        }

        const ISRAELI_CHAIN_SIGNATURES = [
            { id: "rami_levy", patterns: ["רמי לוי", "רמילוי", "השקמה"] },
            { id: "shufersal", patterns: ["שופרסל", "shufersal", "יוניברס", "יש חסד"] },
            { id: "yochananof", patterns: ["יוחננוף"] },
            { id: "osher_ad", patterns: ["אושר עד"] },
            { id: "carrefour", patterns: ["קרפור", "carrefour", "מגה בעיר"] },
            { id: "hatzi_hinam", patterns: ["חצי חינם"] }
        ];

        function detectChainIdsInText(text) {
            const lower = cleanSearchableText(text);
            if (!lower) return [];
            const matched = [];
            for (const sig of ISRAELI_CHAIN_SIGNATURES) {
                for (const pat of sig.patterns) {
                    if (lower.includes(cleanSearchableText(pat))) { matched.push(sig.id); break; }
                }
            }
            return matched;
        }

        function isProductAllowedInChain(productOwnerChainIds, targetChainId, targetChainRawName, productRawText) {
            if (!productOwnerChainIds || productOwnerChainIds.length === 0) return true;
            if (targetChainId && productOwnerChainIds.includes(targetChainId)) return true;
            const cleanChain = cleanSearchableText(targetChainRawName);
            const cleanProd = cleanSearchableText(productRawText);
            return Boolean(cleanChain && cleanProd.includes(cleanChain));
        }

        const fmtMoney = (n) => `₪${Number(n || 0).toFixed(2)}`;

        function calculateDiscreteShelfPrice(prod, priceObj, measureMode, targetQty, plFactor = 1.0) {
            const rawPrice = priceObj.finalPrice;
            const metrics = prod.metrics;
            const isPL = prod.ownerChainIds && prod.ownerChainIds.length > 0;
            const effectiveFactor = isPL ? Number(plFactor || 1.0) : 1.0;

            if (measureMode === "weight") {
                const targetGrams = targetQty * 1000;
                const packGrams = metrics.hasWeightVolume && metrics.totalGramsOrMl > 0 ? metrics.totalGramsOrMl : 1000;
                const pricePerKgOrLiter = (rawPrice / packGrams) * 1000;
                const isPrePackaged = metrics.hasWeightVolume && metrics.totalGramsOrMl !== 1000;
                const packagesToBuy = isPrePackaged ? Math.max(1, Math.ceil(targetGrams / packGrams)) : targetQty;
                const totalCost = isPrePackaged ? packagesToBuy * rawPrice : pricePerKgOrLiter * targetQty;
                return {
                    packagePrice: rawPrice,
                    packagesToBuy,
                    totalCost,
                    normalizedSortValue: pricePerKgOrLiter * effectiveFactor,
                    normalizedBadge: `₪${pricePerKgOrLiter.toFixed(2)} לק"ג/ל'`,
                    isPromo: priceObj.isPromo,
                    regularPrice: priceObj.regularPrice,
                    promoDesc: priceObj.promoDesc
                };
            } else {
                const packagesToBuy = Math.max(1, Math.round(targetQty));
                const totalCost = packagesToBuy * rawPrice;
                let normalizedSortValue = rawPrice * effectiveFactor;
                let normalizedBadge = `₪${rawPrice.toFixed(2)} ליח'`;
                if (metrics.hasWeightVolume && metrics.totalGramsOrMl > 0) {
                    const pricePer100g = (rawPrice / metrics.totalGramsOrMl) * 100;
                    normalizedSortValue = pricePer100g * effectiveFactor;
                    normalizedBadge = `₪${pricePer100g.toFixed(2)} ל-100 ג'/מ"ל`;
                }
                return {
                    packagePrice: rawPrice,
                    packagesToBuy,
                    totalCost,
                    normalizedSortValue,
                    normalizedBadge,
                    isPromo: priceObj.isPromo,
                    regularPrice: priceObj.regularPrice,
                    promoDesc: priceObj.promoDesc
                };
            }
        }

        function optimizeBasketAcrossChains(rules, enrichedCatalog, activeChains, factor, formulas) {
            const chainIdentityMap = {};
            activeChains.forEach((c) => {
                const ids = detectChainIdsInText(c);
                chainIdentityMap[c] = ids.length > 0 ? ids[0] : null;
            });

            const missingStrategy = formulas?.missingItemStrategy || "avg";
            const rankingPriority = formulas?.rankingPriority || "coverage_first";
            const plFactor = Number(formulas?.privateLabelDiscountFactor || 1.0);

            const itemResults = rules.map((rule) => {
                const adjustedQty = rule.measureMode === "weight" ? +(rule.weeklyQty * factor).toFixed(2) : Math.max(1, Math.round(rule.weeklyQty * factor));
                const kwTokens = extractTokens(rule.keywords);
                const exTokens = extractTokens(rule.excludeWords);

                let candidates = enrichedCatalog.filter((pr) => matchesTerms(pr.searchClean, kwTokens, exTokens));
                if (candidates.length === 0 && rule.subCategory) {
                    candidates = enrichedCatalog.filter((pr) => pr.subCategory === rule.subCategory);
                }

                const chainChoices = {};
                let minTotalCost = Infinity;
                let maxTotalCost = 0;

                activeChains.forEach((chain) => {
                    const targetChainId = chainIdentityMap[chain];
                    let winnerProd = null, winnerCalc = null, bestSortScore = Infinity;

                    for (let i = 0; i < candidates.length; i++) {
                        const pr = candidates[i];
                        const priceObj = pr.prices[chain];
                        if (!priceObj || !(priceObj.finalPrice > 0)) continue;
                        if (!isProductAllowedInChain(pr.ownerChainIds, targetChainId, chain, pr.nameAndSupplier)) continue;

                        const calc = calculateDiscreteShelfPrice(pr, priceObj, rule.measureMode, adjustedQty, plFactor);
                        if (calc.normalizedSortValue < bestSortScore - 1e-7 || (Math.abs(calc.normalizedSortValue - bestSortScore) <= 1e-7 && calc.totalCost < (winnerCalc?.totalCost ?? Infinity))) {
                            bestSortScore = calc.normalizedSortValue;
                            winnerProd = pr;
                            winnerCalc = calc;
                        }
                    }

                    if (winnerProd && winnerCalc) {
                        if (winnerCalc.totalCost < minTotalCost) minTotalCost = winnerCalc.totalCost;
                        if (winnerCalc.totalCost > maxTotalCost) maxTotalCost = winnerCalc.totalCost;
                        chainChoices[chain] = {
                            isVerified: true, barcode: winnerProd.barcode, productName: winnerProd.name,
                            supplier: winnerProd.supplier || "", sizeLabel: winnerProd.metrics.sizeLabel,
                            isPrivateLabel: winnerProd.ownerChainIds.length > 0, ...winnerCalc
                        };
                    } else {
                        chainChoices[chain] = null;
                    }
                });

                const verifiedList = activeChains.map((c) => chainChoices[c]).filter(Boolean);
                const avgCost = verifiedList.length > 0 ? verifiedList.reduce((s, x) => s + x.totalCost, 0) / verifiedList.length : 0;
                const fallbackCost = missingStrategy === "max" ? maxTotalCost : (missingStrategy === "zero" ? 0 : avgCost);
                const fallbackLabel = missingStrategy === "max" ? "אומדן מחיר מקסימלי (חסר)" : (missingStrategy === "zero" ? "₪0 (התעלמות מחסר)" : "אומדן ממוצע (חסר במדף)");

                activeChains.forEach((chain) => {
                    if (!chainChoices[chain] && verifiedList.length > 0 && missingStrategy !== "zero") {
                        chainChoices[chain] = {
                            isVerified: false, isImputed: true, productName: fallbackLabel,
                            sizeLabel: "-", packagePrice: fallbackCost, packagesToBuy: 1, totalCost: fallbackCost, normalizedBadge: "אומדן משוער"
                        };
                    }
                });

                return {
                    ...rule, adjustedQty, candidatesCount: candidates.length, chainChoices,
                    minTotalCost: minTotalCost === Infinity ? 0 : minTotalCost,
                    avgCost, fallbackCost, availableAnywhere: verifiedList.length > 0
                };
            });

            const validItems = itemResults.filter((i) => i.availableAnywhere);
            const chainTotals = activeChains.map((chain) => {
                let verifiedSum = 0, imputedSum = 0, verifiedCount = 0, cheapestWins = 0;
                validItems.forEach((item) => {
                    const ch = item.chainChoices[chain];
                    if (ch && ch.isVerified) {
                        verifiedSum += ch.totalCost;
                        verifiedCount++;
                        if (Math.abs(ch.totalCost - item.minTotalCost) < 0.01) cheapestWins++;
                    } else {
                        imputedSum += item.fallbackCost;
                    }
                });
                const totalEstimated = verifiedSum + imputedSum;
                const completenessPct = validItems.length > 0 ? Math.round((verifiedCount / validItems.length) * 100) : 0;
                return { chain, verifiedSum, imputedSum, totalEstimated, verifiedCount, totalItemsCount: validItems.length, completenessPct, cheapestWins };
            });

            chainTotals.sort((a, b) => {
                if (rankingPriority === "lowest_price_only") {
                    return (a.totalEstimated - b.totalEstimated) || (b.completenessPct - a.completenessPct);
                }
                return (b.completenessPct - a.completenessPct) || (a.totalEstimated - b.totalEstimated);
            });

            const winner = chainTotals[0] || null;
            const allEstimates = chainTotals.map((c) => c.totalEstimated);
            const avgBasket = allEstimates.length ? allEstimates.reduce((a, b) => a + b, 0) / allEstimates.length : 0;
            const maxBasket = allEstimates.length ? Math.max(...allEstimates) : 0;

            return {
                itemResults, chainTotals, winner, comparableCount: validItems.length,
                savingsVsAvg: winner ? avgBasket - winner.totalEstimated : 0,
                savingsVsMax: winner ? maxBasket - winner.totalEstimated : 0
            };
        }

        function App() {
            const [siteConfig, setSiteConfig] = useState(INITIAL_SITE_CONFIG);
            const [currentScreen, setCurrentScreen] = useState(INITIAL_SITE_CONFIG.design?.requireLoginScreen ? "login" : "dashboard");
            const [usernameInput, setUsernameInput] = useState("אורח");
            const [passwordInput, setPasswordInput] = useState("");

            const [chains, setChains] = useState(EMBEDDED_CHAINS);
            const [catalog, setCatalog] = useState(EMBEDDED_CATALOG);
            const [basketRules, setBasketRules] = useState(INITIAL_SITE_CONFIG.defaultBasketRules || []);
            const [setupMode, setSetupMode] = useState("recommended");

            const [disabledChains, setDisabledChains] = useState([]);
            const [household, setHousehold] = useState("family");
            const [selectedSuperCategory, setSelectedSuperCategory] = useState("הכל");
            const [globalSearchQuery, setGlobalSearchQuery] = useState("");

            const [isAddModalOpen, setIsAddModalOpen] = useState(false);
            const [modalSuperCat, setModalSuperCat] = useState("מכולת, יבשים ומזווה");
            const [modalSubCat, setModalSubCat] = useState("פסטה");
            const [modalProductName, setModalProductName] = useState("");
            const [modalMeasureMode, setModalMeasureMode] = useState("units");
            const [modalQty, setModalQty] = useState(1);

            // מצבי מנהל מערכת (Super-Admin Studio)
            const [isAdminModalOpen, setIsAdminModalOpen] = useState(false);
            const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
            const [adminPasswordInput, setAdminPasswordInput] = useState("");
            const [adminActiveTab, setAdminActiveTab] = useState("design"); // design | formulas | basket | excel
            const [adminStatusMsg, setAdminStatusMsg] = useState(null);
            const [isUploading, setIsUploading] = useState(false);
            const [newAdminPinInput, setNewAdminPinInput] = useState("");
            const [newDefaultItemName, setNewDefaultItemName] = useState("");
            const [newDefaultItemQty, setNewDefaultItemQty] = useState(1);
            const [newDefaultItemMode, setNewDefaultItemMode] = useState("units");
            const adminFileRef = useRef(null);

            const design = siteConfig.design || {};
            const formulas = siteConfig.formulas || {};
            const palette = THEME_PALETTES[design.accentTheme] || THEME_PALETTES.emerald;

            const householdProfiles = useMemo(() => {
                const hf = formulas.householdFactors || { single: 0.5, couple: 0.75, family: 1.0, large: 1.5 };
                return {
                    single: { label: `יחיד (×${hf.single})`, factor: Number(hf.single || 0.5) },
                    couple: { label: `זוג (×${hf.couple})`, factor: Number(hf.couple || 0.75) },
                    family: { label: `משפחה (×${hf.family})`, factor: Number(hf.family || 1.0) },
                    large: { label: `משפחה מורחבת (×${hf.large})`, factor: Number(hf.large || 1.5) }
                };
            }, [formulas.householdFactors]);

            const enrichedCatalog = useMemo(() => {
                return catalog.map((item) => {
                    const nameNorm = normText(item.name);
                    const nameAndSupplier = `${item.name} ${item.supplier || ""}`;
                    const superCat = item.superCategory || resolveSuperCategory(item.subCategory, item.name);
                    return {
                        ...item, superCategory: superCat, subCategory: item.subCategory || "כללי",
                        nameNorm, nameAndSupplier,
                        searchClean: cleanSearchableText(`${item.name} ${item.subCategory || ""} ${superCat} ${item.supplier || ""}`),
                        metrics: parseProductMetrics(item.name, item.unitStr || ""),
                        ownerChainIds: detectChainIdsInText(nameAndSupplier)
                    };
                });
            }, [catalog]);

            const activeChains = useMemo(() => chains.filter((c) => !disabledChains.includes(c)), [chains, disabledChains]);

            const analysis = useMemo(
                () => optimizeBasketAcrossChains(basketRules, enrichedCatalog, activeChains, householdProfiles[household]?.factor || 1.0, formulas),
                [basketRules, enrichedCatalog, activeChains, household, householdProfiles, formulas]
            );

            const { winner } = analysis;

            const basketSuperCategories = useMemo(() => {
                const set = new Set(basketRules.map((r) => r.superCategory || "מכולת, יבשים ומזווה"));
                return ["הכל", ...Array.from(set)];
            }, [basketRules]);

            const filteredBasketItems = useMemo(() => {
                const qTokens = extractTokens(globalSearchQuery);
                return analysis.itemResults.filter((item) => {
                    const okCat = selectedSuperCategory === "הכל" || item.superCategory === selectedSuperCategory;
                    if (!okCat) return false;
                    if (qTokens.length === 0) return true;
                    const text = cleanSearchableText(`${item.name} ${item.subCategory || ""} ${item.superCategory || ""} ${(item.keywords || []).join(" ")}`);
                    return matchesTerms(text, qTokens);
                });
            }, [analysis.itemResults, selectedSuperCategory, globalSearchQuery]);

            const handleUserTypedProductName = (val) => {
                setModalProductName(val);
                const cleanVal = cleanSearchableText(val);
                if (!cleanVal) return;
                const matchedProd = enrichedCatalog.find(p => p.searchClean.includes(cleanVal));
                if (matchedProd) {
                    setModalSuperCat(matchedProd.superCategory);
                    setModalSubCat(matchedProd.subCategory);
                    const isWeight = /פירות וירקות|קצביה|דגים/.test(matchedProd.superCategory) || /ק"ג|גרם|שקיל|ליטר/.test(matchedProd.name);
                    setModalMeasureMode(isWeight ? "weight" : "units");
                }
            };

            const handleAddProductSubmit = (e) => {
                e.preventDefault();
                const cleanName = modalProductName.trim();
                if (!cleanName) return;

                const kwList = extractTokens(cleanName);
                const isWeight = modalMeasureMode === "weight" || /ירקות|פירות|בשר|עוף|ק"ג|ליטר/.test(cleanName);

                setBasketRules((prev) => [{
                    id: "rule_" + Date.now(),
                    name: cleanName,
                    superCategory: modalSuperCat,
                    subCategory: modalSubCat,
                    keywords: kwList,
                    excludeWords: [],
                    weeklyQty: parseFloat(modalQty) || 1,
                    measureMode: isWeight ? "weight" : "units"
                }, ...prev]);

                setIsAddModalOpen(false);
                setModalProductName("");
            };

            const handleUpdateQty = (id, delta) => {
                setBasketRules((prev) => prev.map((r) => {
                    if (r.id !== id) return r;
                    const step = r.measureMode === "weight" ? 0.5 : 1;
                    return { ...r, weeklyQty: Math.max(step, +(r.weeklyQty + delta * step).toFixed(2)) };
                }));
            };

            const handleSwitchMeasureMode = (id, mode) => {
                setBasketRules((prev) => prev.map((r) => (r.id === id ? { ...r, measureMode: mode } : r)));
            };

            const handleAdminLoginSubmit = async (e) => {
                e.preventDefault();
                try {
                    const res = await fetch("/api/admin/verify-pin", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ pin: adminPasswordInput })
                    });
                    if (!res.ok) throw new Error("סיסמת מנהל שגויה");
                    setIsAdminAuthenticated(true);
                    setAdminStatusMsg(null);
                } catch (err) {
                    alert("סיסמת מנהל שגויה!");
                }
            };

            const handleSaveAdminSettingsToServer = async () => {
                setAdminStatusMsg(null);
                try {
                    const res = await fetch("/api/admin/save-config", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            pin: adminPasswordInput,
                            newPin: newAdminPinInput,
                            config: siteConfig
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "שגיאה בשמירת הגדרות");
                    if (newAdminPinInput.trim()) {
                        setAdminPasswordInput(newAdminPinInput.trim());
                        setNewAdminPinInput("");
                    }
                    setAdminStatusMsg({ type: "ok", text: "✅ כל העיצובים, הנוסחאות והסל המומלץ נשמרו בשרת לכל המשתמשים!" });
                } catch (err) {
                    setAdminStatusMsg({ type: "error", text: `❌ ${err.message}` });
                }
            };

            const handleAdminFileUpload = async (file) => {
                if (!file) return;
                setIsUploading(true);
                setAdminStatusMsg(null);
                const formData = new FormData();
                formData.append("file", file);
                formData.append("pin", adminPasswordInput);
                try {
                    const res = await fetch("/api/upload-excel", { method: "POST", body: formData });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "שגיאה בשרת");
                    setCatalog(data.catalog);
                    setChains(data.chains);
                    setDisabledChains([]);
                    setAdminStatusMsg({ type: "ok", text: `✅ הקטלוג עודכן ונשמר בשרת! נטענו ${data.catalog.length.toLocaleString()} מוצרים ב-${data.chains.length} רשתות.` });
                } catch (err) {
                    setAdminStatusMsg({ type: "error", text: `❌ שגיאה: ${err.message}` });
                } finally {
                    setIsUploading(false);
                }
            };

            const handleResetEmbeddedCatalog = async () => {
                try {
                    const res = await fetch("/api/admin/reset-catalog", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ pin: adminPasswordInput })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "שגיאה באיפוס");
                    setCatalog(data.catalog);
                    setChains(data.chains);
                    setAdminStatusMsg({ type: "ok", text: "✅ הקטלוג אופס ל-32 מוצרי היסוד המובנים." });
                } catch (err) {
                    setAdminStatusMsg({ type: "error", text: `❌ ${err.message}` });
                }
            };

            const updateDesignField = (key, val) => {
                setSiteConfig((prev) => ({
                    ...prev,
                    design: { ...prev.design, [key]: val }
                }));
            };

            const updateFormulaField = (key, val) => {
                setSiteConfig((prev) => ({
                    ...prev,
                    formulas: { ...prev.formulas, [key]: val }
                }));
            };

            const updateHouseholdFactor = (profileKey, val) => {
                setSiteConfig((prev) => ({
                    ...prev,
                    formulas: {
                        ...prev.formulas,
                        householdFactors: {
                            ...prev.formulas.householdFactors,
                            [profileKey]: parseFloat(val) || 1.0
                        }
                    }
                }));
            };

            const handleAddDefaultBasketRule = (e) => {
                e.preventDefault();
                const clean = newDefaultItemName.trim();
                if (!clean) return;
                const matched = enrichedCatalog.find(p => p.searchClean.includes(cleanSearchableText(clean)));
                const supCat = matched ? matched.superCategory : resolveSuperCategory("", clean);
                const subCat = matched ? matched.subCategory : "כללי";
                const newRule = {
                    id: "def_" + Date.now(),
                    name: clean,
                    superCategory: supCat,
                    subCategory: subCat,
                    keywords: extractTokens(clean),
                    excludeWords: [],
                    weeklyQty: parseFloat(newDefaultItemQty) || 1,
                    measureMode: newDefaultItemMode
                };
                const updatedRules = [newRule, ...(siteConfig.defaultBasketRules || [])];
                setSiteConfig((prev) => ({ ...prev, defaultBasketRules: updatedRules }));
                setBasketRules(updatedRules);
                setNewDefaultItemName("");
            };

            const handleRemoveDefaultBasketRule = (id) => {
                const updatedRules = (siteConfig.defaultBasketRules || []).filter(r => r.id !== id);
                setSiteConfig((prev) => ({ ...prev, defaultBasketRules: updatedRules }));
                setBasketRules(updatedRules);
            };

            const handleExportReportToExcel = () => {
                if (!window.XLSX || analysis.itemResults.length === 0) return;
                const rows = analysis.itemResults.map((item) => {
                    const unitTitle = item.measureMode === "weight" ? 'ק"ג/ל\'' : "יח'";
                    const rowObj = {
                        "מוצר מבוקש": item.name,
                        "מחלקה": item.superCategory,
                        "תת-קטגוריה": item.subCategory,
                        "כמות בסל": `${item.adjustedQty} ${unitTitle}`
                    };
                    activeChains.forEach((chain) => {
                        const ch = item.chainChoices[chain];
                        rowObj[`${chain} - סה"כ (₪)`] = ch ? Number(ch.totalCost.toFixed(2)) : "חסר";
                        rowObj[`${chain} - מוצר נבחר`] = ch ? ch.productName : "-";
                    });
                    return rowObj;
                });

                const summaryRow = {
                    "מוצר מבוקש": 'סה"כ עלות סל משוערת',
                    "מחלקה": "",
                    "תת-קטגוריה": "",
                    "כמות בסל": ""
                };
                analysis.chainTotals.forEach((ct) => {
                    summaryRow[`${ct.chain} - סה"כ (₪)`] = Number(ct.totalEstimated.toFixed(2));
                    summaryRow[`${ct.chain} - מוצר נבחר`] = `כיסוי: ${ct.completenessPct}%`;
                });
                rows.push(summaryRow);

                const ws = window.XLSX.utils.json_to_sheet(rows);
                const wb = window.XLSX.utils.book_new();
                window.XLSX.utils.book_append_sheet(wb, ws, "השוואת סל קניות");
                window.XLSX.writeFile(wb, "SmartBasket_IL_Report.xlsx");
            };

            // רינדור פאנל הסטודיו של מנהל המערכת (נגיש מכל מסך)
            const renderAdminStudioModal = () => {
                if (!isAdminModalOpen) return null;
                return (
                    <div className="fixed inset-0 frosted-backdrop z-50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setIsAdminModalOpen(false); }}>
                        <div className="bg-slate-900 text-white rounded-3xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-700 overflow-hidden">
                            <div className="flex justify-between items-center border-b border-slate-800 px-6 py-4 bg-slate-950">
                                <div className="flex items-center gap-2.5">
                                    <span className="text-xl">🎛️</span>
                                    <div>
                                        <h3 className="text-lg font-black">סטודיו מנהל מערכת ראשי (Super-Admin)</h3>
                                        <p className="text-xs text-slate-400">שליטה מלאה בעיצוב האתר, בנוסחאות החישוב, בסל המומלץ ובקובץ האקסל</p>
                                    </div>
                                </div>
                                <button onClick={() => setIsAdminModalOpen(false)} className="text-slate-400 hover:text-white text-lg font-bold">✕</button>
                            </div>

                            {!isAdminAuthenticated ? (
                                <form onSubmit={handleAdminLoginSubmit} className="p-8 max-w-sm mx-auto w-full space-y-4">
                                    <div className="text-center space-y-1">
                                        <div className="text-3xl">🔒</div>
                                        <div className="font-bold text-base">הזדהות מנהל מערכת</div>
                                        <div className="text-xs text-slate-400">רק מנהל המערכת מורשה לערוך עיצובים, נוסחאות וקטלוג</div>
                                    </div>
                                    <input
                                        type="password"
                                        required
                                        value={adminPasswordInput}
                                        onChange={(e) => setAdminPasswordInput(e.target.value)}
                                        placeholder="הזן סיסמת מנהל (ברירת מחדל: 1234)..."
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    />
                                    <button type="submit" className={`w-full font-black py-3 rounded-xl text-sm ${palette.btnPrimary}`}>
                                        כניסה לסטודיו הניהול ➔
                                    </button>
                                </form>
                            ) : (
                                <div className="flex flex-col flex-1 overflow-hidden">
                                    <div className="flex flex-wrap gap-2 px-6 pt-3 pb-3 bg-slate-900 border-b border-slate-800">
                                        {[
                                            { id: "design", label: "🎨 עיצוב ונראות האתר" },
                                            { id: "formulas", label: "🧮 נוסחאות ומנוע חישוב" },
                                            { id: "basket", label: `🛒 עריכת הסל המומלץ (${(siteConfig.defaultBasketRules || []).length})` },
                                            { id: "excel", label: "📂 טעינת אקסל וסיסמה" }
                                        ].map((t) => (
                                            <button
                                                key={t.id}
                                                onClick={() => setAdminActiveTab(t.id)}
                                                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${adminActiveTab === t.id ? palette.btnPrimary : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}
                                            >
                                                {t.label}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="p-6 overflow-y-auto flex-1 space-y-5 text-xs">
                                        {adminStatusMsg && (
                                            <div className={`p-3.5 rounded-xl font-bold ${adminStatusMsg.type === "error" ? "bg-rose-500/20 text-rose-300 border border-rose-500/40" : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"}`}>
                                                {adminStatusMsg.text}
                                            </div>
                                        )}

                                        {adminActiveTab === "design" && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">טקסטים ומיתוג ראשי</div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">שם המערכת / כותרת האתר:</label>
                                                        <input type="text" value={design.brandTitle || ""} onChange={(e) => updateDesignField("brandTitle", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                    </div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">כותרת משנה מתחת ללוגו:</label>
                                                        <input type="text" value={design.brandSubtitle || ""} onChange={(e) => updateDesignField("brandSubtitle", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                    </div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">טקסט תגית הרשת המנצחת:</label>
                                                        <input type="text" value={design.winnerBadgeText || ""} onChange={(e) => updateDesignField("winnerBadgeText", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                    </div>
                                                </div>

                                                <div className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">צבעים, ערכת נושא ומבנה</div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">ערכת צבעים ראשית:</label>
                                                        <select value={design.accentTheme || "emerald"} onChange={(e) => updateDesignField("accentTheme", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                            {Object.entries(THEME_PALETTES).map(([k, v]) => (
                                                                <option key={k} value={k}>{v.name}</option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <div>
                                                            <label className="block text-slate-300 mb-1">עיגול פינות כרטיסים:</label>
                                                            <select value={design.cardRadius || "rounded-3xl"} onChange={(e) => updateDesignField("cardRadius", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                                <option value="rounded-xl">חד ומודרני (XL)</option>
                                                                <option value="rounded-2xl">בינוני (2XL)</option>
                                                                <option value="rounded-3xl">עגול ורך (3XL)</option>
                                                            </select>
                                                        </div>
                                                        <div>
                                                            <label className="block text-slate-300 mb-1">גודל טקסט בדוח:</label>
                                                            <select value={design.fontScale || "normal"} onChange={(e) => updateDesignField("fontScale", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                                <option value="compact">קומפקטי (צפוף)</option>
                                                                <option value="normal">רגיל (מומלץ)</option>
                                                                <option value="large">מוגדל ונגיש</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="md:col-span-2 bg-slate-800/70 p-4 rounded-2xl border border-slate-700">
                                                    <div className="font-black text-sm text-emerald-400 mb-3">שליטה ברכיבי הדוח והמסכים (הצגה / הסתרה)</div>
                                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                                        {[
                                                            { key: "darkMode", label: "🌙 מצב לילה כהה (Dark Mode) לדשבורד" },
                                                            { key: "showWinnerBanner", label: "🏆 הצג כרטיס רשת מנצחת בראש הדף" },
                                                            { key: "showAnnualSavings", label: "💰 הצג חישוב חיסכון שנתי (×52)" },
                                                            { key: "showNormalizedBadges", label: "⚖️ הצג תגיות מחיר ל-100 גרם / ק\"ג" },
                                                            { key: "showTableFooter", label: "📊 הצג שורת סיכום סה\"כ בתחתית הטבלה" },
                                                            { key: "requireLoginScreen", label: "🔑 דרוש מסך כניסה לפני הדשבורד" }
                                                        ].map((item) => (
                                                            <label key={item.key} className="flex items-center gap-2 bg-slate-900 p-3 rounded-xl border border-slate-700 cursor-pointer">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={Boolean(design[item.key])}
                                                                    onChange={(e) => updateDesignField(item.key, e.target.checked)}
                                                                    className="w-4 h-4 accent-emerald-500"
                                                                />
                                                                <span className="font-bold text-slate-200">{item.label}</span>
                                                            </label>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {adminActiveTab === "formulas" && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">נוסחאות השוואה וטיפול בחוסרים</div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">נוסחת השלמת מחיר למוצר שחסר ברשת ספציפית:</label>
                                                        <select value={formulas.missingItemStrategy || "avg"} onChange={(e) => updateFormulaField("missingItemStrategy", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                            <option value="avg">אומדן לפי המחיר הממוצע בשאר הרשתות (הוגן ומומלץ)</option>
                                                            <option value="max">קנס: השלם לפי המחיר היקר ביותר בשוק לאותו מוצר</option>
                                                            <option value="zero">התעלם מהמוצר החסר (₪0 - עלול להטות לטובת רשת חסרה)</option>
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">נוסחת קביעת הרשת המנצחת:</label>
                                                        <select value={formulas.rankingPriority || "coverage_first"} onChange={(e) => updateFormulaField("rankingPriority", e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                            <option value="coverage_first">כיסוי סל מלא קודם, ואז המחיר הזול ביותר</option>
                                                            <option value="lowest_price_only">המחיר הכולל הנמוך ביותר בלבד (ללא תלות באחוז כיסוי)</option>
                                                        </select>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2">
                                                        <div>
                                                            <label className="block text-slate-300 mb-1">מספר שבועות לחישוב חיסכון שנתי:</label>
                                                            <input type="number" min="1" max="100" value={formulas.annualWeeksMultiplier || 52} onChange={(e) => updateFormulaField("annualWeeksMultiplier", parseFloat(e.target.value) || 52)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                        </div>
                                                        <div>
                                                            <label className="block text-slate-300 mb-1">פקטור שקלול מותג פרטי (1.0 = רגיל):</label>
                                                            <input type="number" step="0.05" min="0.5" max="1.5" value={formulas.privateLabelDiscountFactor || 1.0} onChange={(e) => updateFormulaField("privateLabelDiscountFactor", parseFloat(e.target.value) || 1.0)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">מכפילי כמות אוטומטיים לפי גודל משק בית</div>
                                                    <p className="text-slate-400 text-[11px]">כאשר משתמש בוחר פרופיל משק בית, כל הכמויות בסל מוכפלות בפקטור הבא:</p>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {[
                                                            { k: "single", title: "יחיד (1 נפש)" },
                                                            { k: "couple", title: "זוג (2 נפשות)" },
                                                            { k: "family", title: "משפחה (4 נפשות)" },
                                                            { k: "large", title: "משפחה מורחבת (6+)" }
                                                        ].map((prof) => (
                                                            <div key={prof.k}>
                                                                <label className="block text-slate-300 mb-1">{prof.title}:</label>
                                                                <input
                                                                    type="number"
                                                                    step="0.05"
                                                                    min="0.1"
                                                                    max="5"
                                                                    value={formulas.householdFactors?.[prof.k] ?? 1.0}
                                                                    onChange={(e) => updateHouseholdFactor(prof.k, e.target.value)}
                                                                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white"
                                                                />
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {adminActiveTab === "basket" && (
                                            <div className="space-y-4">
                                                <form onSubmit={handleAddDefaultBasketRule} className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 flex flex-wrap gap-3 items-end">
                                                    <div className="flex-1 min-w-[180px]">
                                                        <label className="block text-slate-300 mb-1 font-bold">הוסף מוצר חדש לסל המומלץ הקבוע:</label>
                                                        <input type="text" value={newDefaultItemName} onChange={(e) => setNewDefaultItemName(e.target.value)} placeholder="למשל: טחינה גולמית, שניצל תירס..." className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                    </div>
                                                    <div>
                                                        <label className="block text-slate-300 mb-1">יחידת מידה:</label>
                                                        <select value={newDefaultItemMode} onChange={(e) => setNewDefaultItemMode(e.target.value)} className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white">
                                                            <option value="units">יחידות</option>
                                                            <option value="weight">ק"ג / ליטר</option>
                                                        </select>
                                                    </div>
                                                    <div className="w-24">
                                                        <label className="block text-slate-300 mb-1">כמות:</label>
                                                        <input type="number" step="0.5" min="0.5" value={newDefaultItemQty} onChange={(e) => setNewDefaultItemQty(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white" />
                                                    </div>
                                                    <button type="submit" className={`px-4 py-2 rounded-xl font-black ${palette.btnPrimary}`}>➕ הוסף לסל המומלץ</button>
                                                </form>

                                                <div className="bg-slate-800/70 p-4 rounded-2xl border border-slate-700 max-h-64 overflow-y-auto">
                                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                                        {(siteConfig.defaultBasketRules || []).map((r, i) => (
                                                            <div key={r.id} className="flex justify-between items-center bg-slate-900 px-3 py-2 rounded-xl border border-slate-700">
                                                                <div>
                                                                    <span className="text-slate-500 ml-1">{i + 1}.</span>
                                                                    <span className="font-bold text-white">{r.name}</span>
                                                                    <span className="text-[10px] text-slate-400 mr-1.5">({r.weeklyQty} {r.measureMode === "weight" ? 'ק"ג' : "יח'"})</span>
                                                                </div>
                                                                <button onClick={() => handleRemoveDefaultBasketRule(r.id)} className="text-rose-400 hover:text-rose-300 font-bold">✕</button>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {adminActiveTab === "excel" && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div className="bg-slate-800/70 p-5 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">📂 העלאת קובץ אקסל (CHP / מחירונים)</div>
                                                    <p className="text-slate-300">טען קובץ אקסל חדש מהמחשב שלך. הקובץ ינותח אוטומטית ויישמר בשרת עבור כל המשתמשים.</p>
                                                    <button disabled={isUploading} onClick={() => adminFileRef.current?.click()} className={`w-full font-black py-3.5 rounded-xl text-sm transition-all ${palette.btnPrimary}`}>
                                                        {isUploading ? "⏳ מעבד קובץ אקסל..." : "📂 בחר קובץ אקסל (.xlsx / .xlsm / .csv)"}
                                                    </button>
                                                    <input type="file" ref={adminFileRef} onChange={(e) => handleAdminFileUpload(e.target.files[0])} accept=".xlsx,.xlsm,.xls,.csv" className="hidden" />
                                                    <button onClick={handleResetEmbeddedCatalog} className="w-full bg-slate-900 hover:bg-slate-700 text-slate-300 border border-slate-700 py-2.5 rounded-xl font-bold">
                                                        🔄 אפס לקטלוג 32 המוצרים המובנה
                                                    </button>
                                                </div>

                                                <div className="bg-slate-800/70 p-5 rounded-2xl border border-slate-700 space-y-3">
                                                    <div className="font-black text-sm text-emerald-400">🔑 שינוי סיסמת מנהל המערכת</div>
                                                    <p className="text-slate-300">כדי שאף אחד מלבדך לא יוכל להיכנס לסטודיו הניהול באתר הציבורי, הגדר כאן סיסמה אישית משלך:</p>
                                                    <input
                                                        type="password"
                                                        value={newAdminPinInput}
                                                        onChange={(e) => setNewAdminPinInput(e.target.value)}
                                                        placeholder="הקלד סיסמת מנהל חדשה..."
                                                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-white"
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex justify-between items-center px-6 py-4 bg-slate-950 border-t border-slate-800">
                                        <span className="text-xs text-slate-400">שינויים שתבצע מתעדכנים בלייב על המסך שלך, ולחיצה על שמירה מקבעת אותם בשרת לכולם.</span>
                                        <div className="flex gap-3">
                                            <button onClick={() => setIsAdminModalOpen(false)} className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">סגור חלון</button>
                                            <button onClick={handleSaveAdminSettingsToServer} className={`px-6 py-2.5 rounded-xl text-xs font-black shadow-lg ${palette.btnPrimary}`}>
                                                💾 שמור הגדרות ועיצוב בשרת לכולם
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                );
            };

            if (currentScreen === "login") {
                return (
                    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
                        <div className={`bg-slate-800 border border-slate-700 ${design.cardRadius || "rounded-3xl"} max-w-md w-full p-8 shadow-2xl text-white space-y-6`}>
                            <div className="text-center">
                                <div className={`w-16 h-16 mx-auto rounded-2xl text-3xl font-black flex items-center justify-center shadow-lg mb-4 ${palette.btnPrimary}`}>🛒</div>
                                <h1 className="text-2xl font-black">{design.brandTitle}</h1>
                                <p className="text-xs text-slate-400 mt-1">{design.brandSubtitle} ({catalog.length.toLocaleString()} מוצרים בקטלוג)</p>
                            </div>
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                if (usernameInput.trim()) setCurrentScreen("setup");
                            }} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1">שם משתמש:</label>
                                    <input type="text" required value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)} placeholder="למשל: גיגי" className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1">סיסמה (אופציונלי לאורחים):</label>
                                    <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} placeholder="••••••••" className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none" />
                                </div>
                                <button type="submit" className={`w-full font-black py-3.5 rounded-xl text-sm shadow-lg transition-all ${palette.btnPrimary}`}>
                                    כניסה למערכת ההשוואה ➔
                                </button>
                            </form>
                            <div className="text-center pt-2">
                                <button onClick={() => setIsAdminModalOpen(true)} className="text-xs text-slate-400 hover:text-white underline">
                                    🎛️ כניסת מנהל מערכת (עיצוב, נוסחאות והעלאת אקסל)
                                </button>
                            </div>
                        </div>
                        {renderAdminStudioModal()}
                    </div>
                );
            }

            if (currentScreen === "setup") {
                return (
                    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                        <div className={`bg-white ${design.cardRadius || "rounded-3xl"} max-w-xl w-full p-8 shadow-2xl space-y-6`}>
                            <div>
                                <span className={`${palette.badgeBg} text-xs font-bold px-3 py-1 rounded-full`}>שלום, {usernameInput} 👋</span>
                                <h2 className="text-2xl font-black text-slate-900 mt-3">איך תרצה להרכיב את הסל השבועי שלך?</h2>
                                <p className="text-xs text-slate-500 mt-1">בחר בסל המלא המומלץ ({(siteConfig.defaultBasketRules || []).length} מוצרים) או הרכיב סל אישי מאפס</p>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div onClick={() => setSetupMode("recommended")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${setupMode === "recommended" ? "border-emerald-600 bg-emerald-50/50" : "border-slate-200"}`}>
                                    <div className="text-2xl mb-2">⭐</div>
                                    <div className="font-bold text-slate-900">סל 30 מוצרי יסוד מומלץ</div>
                                    <div className="text-xs text-slate-500 mt-1">טען סל קניות ישראלי מקיף של {(siteConfig.defaultBasketRules || []).length} מוצרים והשווה אוטומטית.</div>
                                </div>
                                <div onClick={() => setSetupMode("custom")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${setupMode === "custom" ? "border-emerald-600 bg-emerald-50/50" : "border-slate-200"}`}>
                                    <div className="text-2xl mb-2">🛠️</div>
                                    <div className="font-bold text-slate-900">התחל מסל ריק</div>
                                    <div className="text-xs text-slate-500 mt-1">צור סל אישי והזן חופשי כל מוצר שתרצה.</div>
                                </div>
                            </div>

                            <button onClick={() => {
                                setBasketRules(setupMode === "recommended" ? (siteConfig.defaultBasketRules || []) : []);
                                setCurrentScreen("dashboard");
                            }} className={`w-full font-black py-3.5 rounded-xl text-sm shadow-lg transition-all ${palette.btnSolid}`}>
                                המשך לדשבורד ההשוואה ➔
                            </button>
                        </div>
                        {renderAdminStudioModal()}
                    </div>
                );
            }

            const fontScaleClass = design.fontScale === "compact" ? "text-xs" : (design.fontScale === "large" ? "text-base" : "text-sm");
            const pageBgClass = design.darkMode ? "bg-slate-950 text-slate-100" : "bg-slate-100 text-slate-900";
            const cardBgClass = design.darkMode ? "bg-slate-900 border border-slate-800 text-slate-100" : "bg-white border border-slate-200/90 text-slate-900";
            const weeksMult = Number(formulas.annualWeeksMultiplier || 52);

            return (
                <div className={`min-h-screen flex flex-col justify-between ${pageBgClass} ${fontScaleClass}`}>
                    <div>
                        <header className="bg-slate-900 text-white shadow-lg sticky top-0 z-30 border-b border-slate-800">
                            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-wrap justify-between items-center gap-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2.5 rounded-2xl text-xl font-black shadow-md ${palette.btnPrimary}`}>🛒</div>
                                    <div>
                                        <div className="flex items-center gap-2.5">
                                            <h1 className="text-xl font-black tracking-tight">{design.brandTitle}</h1>
                                            <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-bold px-2.5 py-0.5 rounded-full">
                                                {usernameInput} • {enrichedCatalog.length.toLocaleString()} מוצרים בקטלוג
                                            </span>
                                        </div>
                                        <p className="text-xs text-slate-400 mt-0.5">{design.brandSubtitle}</p>
                                    </div>
                                </div>
                                <div className="flex flex-wrap items-center gap-2">
                                    <button onClick={() => setIsAddModalOpen(true)} className={`font-black px-4 py-2.5 rounded-xl text-sm shadow-md transition-all flex items-center gap-1.5 ${palette.btnPrimary}`}>
                                        <span>➕</span><span>הוסף מוצר לסל</span>
                                    </button>
                                    <button onClick={handleExportReportToExcel} className="bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-500/30 px-3 py-2 rounded-xl text-xs font-bold">
                                        📥 ייצוא לאקסל
                                    </button>
                                    <button onClick={() => setIsAdminModalOpen(true)} className="bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 px-3 py-2 rounded-xl text-xs font-bold">
                                        🎛️ סטודיו מנהל
                                    </button>
                                    <button onClick={() => setCurrentScreen("setup")} className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded-xl text-xs font-bold">
                                        ⚙️ החלף סל
                                    </button>
                                </div>
                            </div>
                        </header>

                        <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-5">
                            <div className={`${cardBgClass} ${design.cardRadius || "rounded-3xl"} p-5 shadow-sm space-y-4`}>
                                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                                    <div className="lg:col-span-5 relative">
                                        <input type="text" value={globalSearchQuery} onChange={(e) => setGlobalSearchQuery(e.target.value)} placeholder={`🔍 חיפוש חופשי מתוך ${basketRules.length} מוצרי הסל...`} className="w-full bg-slate-50 text-slate-900 border border-slate-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium" />
                                    </div>
                                    <div className="lg:col-span-7 flex flex-wrap items-center justify-end gap-2">
                                        <span className="text-xs font-bold text-slate-400 ml-1">גודל משק בית:</span>
                                        {Object.entries(householdProfiles).map(([key, prof]) => (
                                            <button key={key} onClick={() => setHousehold(key)} className={`px-3 py-2 rounded-xl text-xs font-bold transition-all ${household === key ? palette.btnSolid + " shadow-md" : "bg-slate-200/70 text-slate-700 hover:bg-slate-300"}`}>{prof.label}</button>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200/60">
                                    <div className="flex flex-wrap gap-1.5">
                                        {basketSuperCategories.map((cat) => (
                                            <button key={cat} onClick={() => setSelectedSuperCategory(cat)} className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${selectedSuperCategory === cat ? palette.btnSolid + " shadow-sm" : "bg-slate-200/70 text-slate-700 hover:bg-slate-300"}`}>{cat}</button>
                                        ))}
                                    </div>
                                    <div className="flex flex-wrap items-center gap-1.5">
                                        <span className="text-xs font-bold text-slate-400 ml-1">רשתות פעילות:</span>
                                        {chains.map((c) => {
                                            const active = !disabledChains.includes(c);
                                            return (
                                                <button key={c} onClick={() => setDisabledChains((prev) => active ? (chains.length - prev.length > 2 ? [...prev, c] : prev) : prev.filter((x) => x !== c))} className={`px-2.5 py-1 rounded-lg text-xs font-bold border transition-all ${active ? "bg-slate-900 text-white border-slate-900" : "bg-slate-100 text-slate-400 border-slate-200 line-through"}`}>{c}</button>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
                            {winner && design.showWinnerBanner !== false && (
                                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                                    <div className={`lg:col-span-5 bg-gradient-to-br ${palette.winnerGradient} text-white ${design.cardRadius || "rounded-3xl"} p-6 shadow-xl flex flex-col justify-between`}>
                                        <div>
                                            <div className="inline-flex bg-white/15 px-3 py-1 rounded-full text-xs font-bold mb-4">{design.winnerBadgeText || "🏆 הרשת המשתלמת ביותר"}</div>
                                            <h2 className="text-4xl font-black tracking-tight mb-1">{winner.chain}</h2>
                                            <p className="text-white/80 text-xs mb-5">השוואת מחירים אוטומטית לפי יחידות מידה ({winner.verifiedCount} מתוך {winner.totalItemsCount} פריטים מאומתים במדף)</p>
                                            <div className="bg-black/25 rounded-2xl p-5 border border-white/10">
                                                <div className="text-xs text-white/80 mb-1">עלות קנייה שבועית משוערת בקופה:</div>
                                                <div className="text-5xl font-black tracking-tight">{fmtMoney(winner.totalEstimated)}</div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 mt-5 pt-4 border-t border-white/15">
                                            <div className="bg-white/10 rounded-2xl p-3">
                                                <div className="text-xs text-white/80">חיסכון שבועי מול הממוצע:</div>
                                                <div className="text-xl font-black mt-0.5">{fmtMoney(analysis.savingsVsAvg)}</div>
                                            </div>
                                            {design.showAnnualSavings !== false && (
                                                <div className="bg-white/10 rounded-2xl p-3">
                                                    <div className="text-xs text-white/80">חיסכון שנתי (×{weeksMult}) מול היקרה:</div>
                                                    <div className="text-xl font-black text-amber-300 mt-0.5">₪{(analysis.savingsVsMax * weeksMult).toFixed(0)}</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className={`lg:col-span-7 ${cardBgClass} ${design.cardRadius || "rounded-3xl"} p-6 shadow-sm flex flex-col justify-between`}>
                                        <div>
                                            <div className="flex justify-between items-center mb-4">
                                                <h3 className="text-lg font-black">דירוג עגלות הקנייה ברשתות ({analysis.comparableCount} מוצרים בסל)</h3>
                                            </div>
                                            <div className="space-y-2.5">
                                                {analysis.chainTotals.map((c, idx) => {
                                                    const diff = c.totalEstimated - winner.totalEstimated;
                                                    return (
                                                        <div key={c.chain} className={`p-3 rounded-2xl border transition-all ${idx === 0 ? palette.winnerRow + " text-slate-900" : (design.darkMode ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200")}`}>
                                                            <div className="flex justify-between items-center">
                                                                <div className="flex items-center gap-2.5">
                                                                    <span className={`w-6 h-6 rounded-full text-xs font-black flex items-center justify-center ${idx === 0 ? palette.btnSolid : "bg-slate-200 text-slate-700"}`}>{idx + 1}</span>
                                                                    <span className="font-bold">{c.chain}</span>
                                                                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${c.completenessPct === 100 ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{c.completenessPct}% כיסוי</span>
                                                                    <span className="text-[11px] text-slate-400 hidden sm:inline">• {c.cheapestWins} מוצרים הכי זולים</span>
                                                                </div>
                                                                <div className="flex items-baseline gap-2.5">
                                                                    {idx > 0 && <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md">+{fmtMoney(diff)}</span>}
                                                                    <span className="text-xl font-black">{fmtMoney(c.totalEstimated)}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className={`${cardBgClass} ${design.cardRadius || "rounded-3xl"} p-6 shadow-sm`}>
                                <div className="flex flex-wrap justify-between items-center gap-4 mb-5">
                                    <div>
                                        <h3 className="text-lg font-black">פירוט מלא של שורות הסל ({filteredBasketItems.length} מוצרים מוצגים)</h3>
                                        <p className="text-xs text-slate-400 mt-0.5">המערכת בוחרת אוטומטית בכל רשת את המוצר המשתלם ביותר לפי יחידת מידה.</p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button onClick={() => setBasketRules([])} className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 px-3.5 py-2 rounded-xl text-xs font-bold">🗑️ רוקן סל</button>
                                        <button onClick={() => setBasketRules(siteConfig.defaultBasketRules || [])} className="bg-slate-200 hover:bg-slate-300 text-slate-800 px-3.5 py-2 rounded-xl text-xs font-bold">🔄 טען סל {(siteConfig.defaultBasketRules || []).length} מוצרים מומלץ</button>
                                    </div>
                                </div>

                                <div className="overflow-x-auto pb-6">
                                    <table className="w-full text-right border-collapse">
                                        <thead>
                                            <tr className="border-b-2 border-slate-200 text-slate-500 text-xs bg-slate-50/90">
                                                <th className="py-3.5 px-4 font-bold rounded-tr-xl">מוצר בסל ומחלקה</th>
                                                <th className="py-3.5 px-3 font-bold text-center">אופן חישוב</th>
                                                <th className="py-3.5 px-3 font-bold text-center">כמות בסל</th>
                                                {activeChains.map((c) => (
                                                    <th key={c} className="py-3.5 px-3 font-bold text-center">{c}<div className="text-[10px] font-normal text-slate-400">המוצר הזול במדף</div></th>
                                                ))}
                                                <th className="py-3.5 px-2 font-bold text-center rounded-tl-xl">הסר</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-200/60">
                                            {filteredBasketItems.map((item) => {
                                                const isWeight = item.measureMode === "weight";
                                                const unitLabel = isWeight ? `ק"ג/ל'` : `יח'`;
                                                return (
                                                    <tr key={item.id} className="hover:bg-slate-500/5 transition-colors">
                                                        <td className="py-3.5 px-4 max-w-[210px]">
                                                            <div className="font-bold">{item.name}</div>
                                                            <div className="text-[11px] text-slate-400 flex flex-wrap gap-1 mt-1">
                                                                <span className="bg-slate-500/10 px-1.5 py-0.5 rounded font-medium">{item.subCategory || item.superCategory}</span>
                                                                <span>• {item.candidatesCount} חלופות</span>
                                                            </div>
                                                        </td>
                                                        <td className="py-3.5 px-3 text-center">
                                                            <div className="inline-flex bg-slate-200/80 p-1 rounded-xl">
                                                                <button onClick={() => handleSwitchMeasureMode(item.id, "units")} className={`px-2 py-1 rounded-lg text-xs font-bold ${!isWeight ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}>📦 יח'</button>
                                                                <button onClick={() => handleSwitchMeasureMode(item.id, "weight")} className={`px-2 py-1 rounded-lg text-xs font-bold ${isWeight ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}>⚖️ ק"ג/ל'</button>
                                                            </div>
                                                        </td>
                                                        <td className="py-3.5 px-3 text-center">
                                                            <div className="inline-flex items-center gap-1.5 bg-slate-200/70 rounded-xl px-2 py-1">
                                                                <button onClick={() => handleUpdateQty(item.id, -1)} className="w-5 h-5 rounded-lg bg-white text-slate-700 font-bold text-xs shadow-sm">-</button>
                                                                <span className="font-black text-slate-900 min-w-[55px] text-center text-xs">{item.adjustedQty} {unitLabel}</span>
                                                                <button onClick={() => handleUpdateQty(item.id, 1)} className="w-5 h-5 rounded-lg bg-white text-slate-700 font-bold text-xs shadow-sm">+</button>
                                                            </div>
                                                        </td>
                                                        {activeChains.map((chain) => {
                                                            const ch = item.chainChoices[chain];
                                                            if (!ch) return <td key={chain} className="py-3.5 px-3 text-center text-xs text-slate-400">לא נמצא</td>;
                                                            const isCheapest = !ch.isImputed && Math.abs(ch.totalCost - item.minTotalCost) < 0.01;
                                                            return (
                                                                <td key={chain} className={`py-3 px-3 text-center ${isCheapest ? palette.cheapestCell : ""}`}>
                                                                    <div className="text-base font-black">{fmtMoney(ch.totalCost)}</div>
                                                                    <div className="text-[11px] opacity-80 font-medium line-clamp-2 max-w-[145px] mx-auto leading-tight mt-0.5">{ch.productName}</div>
                                                                    {design.showNormalizedBadges !== false && (
                                                                        <div className={`text-[10px] font-bold ${palette.badgeBg} inline-block px-1.5 py-0.5 rounded mt-1`}>{ch.normalizedBadge}</div>
                                                                    )}
                                                                </td>
                                                            );
                                                        })}
                                                        <td className="py-3.5 px-2 text-center">
                                                            <button onClick={() => setBasketRules((prev) => prev.filter((r) => r.id !== item.id))} className="text-slate-400 hover:text-rose-500 p-1 font-bold">🗑️</button>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                        {design.showTableFooter !== false && analysis.chainTotals.length > 0 && (
                                            <tfoot>
                                                <tr className="border-t-2 border-slate-300 bg-slate-900 text-white font-black">
                                                    <td colSpan="3" className="py-4 px-4 text-sm rounded-br-xl">סה"כ עלות סל משוערת בקופה:</td>
                                                    {activeChains.map((chain) => {
                                                        const ct = analysis.chainTotals.find((x) => x.chain === chain);
                                                        const isWin = winner && winner.chain === chain;
                                                        return (
                                                            <td key={chain} className={`py-4 px-3 text-center ${isWin ? "text-emerald-400 text-lg" : "text-sm"}`}>
                                                                <div>{ct ? fmtMoney(ct.totalEstimated) : "-"}</div>
                                                                <div className="text-[10px] font-normal text-slate-400">{ct ? `${ct.completenessPct}% כיסוי` : ""}</div>
                                                            </td>
                                                        );
                                                    })}
                                                    <td className="rounded-bl-xl"></td>
                                                </tr>
                                            </tfoot>
                                        )}
                                    </table>
                                </div>
                            </div>
                        </main>
                    </div>

                    {isAddModalOpen && (
                        <div className="fixed inset-0 frosted-backdrop z-50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setIsAddModalOpen(false); }}>
                            <div className="bg-white text-slate-900 rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-200">
                                <div className="flex justify-between items-center mb-4 border-b border-slate-100 pb-3">
                                    <div className="flex items-center gap-2">
                                        <span className="text-emerald-600 text-xl font-black">➕</span>
                                        <h3 className="text-lg font-black">הוספת מוצר חופשי לסל</h3>
                                    </div>
                                    <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg">✕</button>
                                </div>
                                <form onSubmit={handleAddProductSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-bold text-slate-700 mb-1">הקלד שם מוצר חופשי (למשל: נוזל כלים, עגבנייה, פסטה) *</label>
                                        <input
                                            type="text"
                                            required
                                            placeholder="הקלד חופשי... המערכת תבחר אוטומטית את הזול ביותר"
                                            value={modalProductName}
                                            onChange={(e) => handleUserTypedProductName(e.target.value)}
                                            className="w-full border-2 border-emerald-500 bg-emerald-50/20 rounded-xl px-3.5 py-3 text-sm font-bold text-slate-900 focus:outline-none"
                                        />
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-slate-50 p-3 rounded-2xl border border-slate-200">
                                        <div>
                                            <label className="block text-[11px] font-bold text-slate-500 mb-1">מחלקת על שזוהתה:</label>
                                            <input type="text" readOnly value={modalSuperCat} className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800" />
                                        </div>
                                        <div>
                                            <label className="block text-[11px] font-bold text-slate-500 mb-1">תת-קטגוריה שזוהתה:</label>
                                            <input type="text" readOnly value={modalSubCat} className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs font-bold text-slate-800" />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1">אופן חישוב (יחידת מידה)</label>
                                            <select value={modalMeasureMode} onChange={(e) => setModalMeasureMode(e.target.value)} className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-slate-50">
                                                <option value="units">אריזות / יחידות</option>
                                                <option value="weight">משקל או נפח (ק"ג / ליטר)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1">כמות נדרשת</label>
                                            <input type="number" min="0.5" step="any" required value={modalQty} onChange={(e) => setModalQty(e.target.value)} className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm" />
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                                        <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-4 py-2 text-sm font-bold text-slate-500">ביטול</button>
                                        <button type="submit" className={`font-black px-6 py-2 rounded-xl text-sm shadow-md ${palette.btnSolid}`}>הוסף לסל והשווה מחירים</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}

                    {renderAdminStudioModal()}
                </div>
            );
        }

        ReactDOM.createRoot(document.getElementById("root")).render(<App />);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    public_cfg = {k: v for k, v in SITE_CONFIG.items() if k != "adminPin"}
    rendered = (
        HTML_TEMPLATE
        .replace("__SUPER_CATEGORIES_JSON__", json.dumps(SUPER_CATEGORIES_TREE, ensure_ascii=False))
        .replace("__CHAINS_JSON__", json.dumps(STATE["chains"], ensure_ascii=False))
        .replace("__CATALOG_JSON__", json.dumps(STATE["catalog"], ensure_ascii=False))
        .replace("__SITE_CONFIG_JSON__", json.dumps(public_cfg, ensure_ascii=False))
    )
    return HTMLResponse(content=rendered)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    is_cloud = "RENDER" in os.environ or "SPACE_ID" in os.environ or "RAILWAY_ENVIRONMENT" in os.environ
    host = "0.0.0.0" if is_cloud else "127.0.0.1"
    if not is_cloud:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    uvicorn.run(app, host=host, port=port)