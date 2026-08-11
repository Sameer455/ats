import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


_MAX_SINGLE_RANGE_YEARS = 15
_MAX_TOTAL_YEARS        = 45
_MIN_CAREER_YEAR        = 1990

_MONTH_MAP = {
    "jan": 1,  "feb": 2,  "mar": 3,  "apr": 4,  "may": 5,  "jun": 6,
    "jul": 7,  "aug": 8,  "sep": 9,  "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3,    "april": 4,
    "june":    6, "july":    7,  "august":   8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

_PRESENT_WORDS = {"present", "current", "now", "till date", "ongoing", "today", "date"}

_MONTH_PAT = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\.?"
)

_YEAR_PAT       = r"(?:19[89]\d|20[0-3]\d)"
_YEAR_SHORT_PAT = r"'?\d{2}"
_SEP_PAT        = r"\s*(?:[-–—]|to|till|through|until)\s*"
_PRESENT_PAT    = r"(?:present|current|now|till\s+date|ongoing|today)"

_DATE_RANGE_RE = re.compile(
    r"(?:" + _MONTH_PAT + r"[,\s]*)?"
    r"(" + _YEAR_PAT + r")"
    r"\s*" + _SEP_PAT +
    r"(?:" + _MONTH_PAT + r"[,\s]*)?"
    r"(" + _YEAR_PAT + r"|" + _PRESENT_PAT + r")",
    re.IGNORECASE,
)

_MONTH_YEAR_RANGE_RE = re.compile(
    r"(" + _MONTH_PAT + r")\s*[,]?\s*(" + _YEAR_PAT + r")"
    r"\s*" + _SEP_PAT +
    r"(" + _MONTH_PAT + r"|" + _PRESENT_PAT + r")"
    r"(?:\s*[,]?\s*(" + _YEAR_PAT + r"))?",
    re.IGNORECASE,
)

_EXPLICIT_YEARS_RE = re.compile(
    r"\b(\d{1,2})\+?\s*(?:years?|yrs?)(?:\s+and\s+(\d{1,2})\s+months?)?"
    r"(?:\s+of)?(?:\s+(?:professional\s+|work\s+|industry\s+)?experience)?\b",
    re.IGNORECASE,
)

_EXPLICIT_MONTHS_RE = re.compile(
    r"\b(\d{1,2})\s+months?\s+(?:of\s+)?(?:professional\s+)?experience\b",
    re.IGNORECASE,
)

_EDU_KEYWORDS = {
    "university", "college", "institute", "school", "academy",
    "bachelor", "master", "b.tech", "m.tech", "be ", "me ", "bsc",
    "msc", "mba", "phd", "ph.d", "degree", "gpa", "cgpa",
    "graduation", "undergraduate", "postgraduate", "diploma",
    "b.e", "m.e", "b.sc", "m.sc", "b.a", "m.a",
}

_JOB_KEYWORDS = {
    "engineer", "developer", "analyst", "manager", "scientist",
    "associate", "intern", "consultant", "architect", "lead",
    "director", "officer", "specialist", "coordinator", "designer",
    "programmer", "administrator", "executive", "head", "vp",
    "vice president", "cto", "ceo", "principal", "staff",
    "senior", "junior", "technology", "software",
}


def _parse_month(s: str) -> int:
    if not s:
        return 1
    key = s.strip().rstrip(".").lower()
    return _MONTH_MAP.get(key, _MONTH_MAP.get(key[:9], 1))


def _parse_year(s: str) -> int:
    s = s.strip().lstrip("'")
    y = int(s)
    if y < 100:
        current_year = datetime.now().year
        y = 2000 + y if y <= current_year % 100 + 5 else 1900 + y
    return y


def _to_dt(year: int, month: int = 1) -> datetime:
    return datetime(year, max(1, min(month, 12)), 1)


def _range_months(start_dt: datetime, end_dt: datetime) -> int:
    if end_dt <= start_dt:
        return 0
    delta = relativedelta(end_dt, start_dt)
    return min(delta.years * 12 + delta.months, _MAX_SINGLE_RANGE_YEARS * 12)


def _merge_intervals(intervals: list) -> list:
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(m) for m in merged]


def _looks_like_edu_year_only(
    start_year: int,
    end_year: int,
    surrounding_text: str = "",
) -> bool:
    span = end_year - start_year
    if not (2 <= span <= 6):
        return False

    text_lower = surrounding_text.lower()

    has_job_signal = any(kw in text_lower for kw in _JOB_KEYWORDS)
    has_edu_signal = any(kw in text_lower for kw in _EDU_KEYWORDS)

    if has_job_signal and not has_edu_signal:
        return False

    if has_edu_signal and not has_job_signal:
        return True

    if has_edu_signal and has_job_signal:
        return False

    return span <= 4


def _guess_month_from_context(text_before: str) -> int:
    snippet = text_before[-60:].lower()
    for name in sorted(_MONTH_MAP.keys(), key=len, reverse=True):
        if name in snippet:
            return _MONTH_MAP[name]
    return 1


def extract_experience(text: str, is_education_section: bool = False) -> float:
    if not text or not text.strip():
        return 0.0

    now = datetime.now()

    best_explicit_months = 0

    for m in _EXPLICIT_YEARS_RE.finditer(text):
        years  = int(m.group(1))
        months = int(m.group(2)) if m.group(2) else 0
        total  = years * 12 + months
        if 0 < total <= _MAX_TOTAL_YEARS * 12:
            best_explicit_months = max(best_explicit_months, total)

    for m in _EXPLICIT_MONTHS_RE.finditer(text):
        months = int(m.group(1))
        if 0 < months < 24:
            best_explicit_months = max(best_explicit_months, months)

    if best_explicit_months > 0:
        return round(min(best_explicit_months / 12, _MAX_TOTAL_YEARS), 1)

    intervals = []

    month_year_positions = set()

    for m in _MONTH_YEAR_RANGE_RE.finditer(text):
        start_mon_str, start_yr_str, end_part, end_yr_str = m.groups()
        month_year_positions.add(m.start())

        try:
            start_year  = int(start_yr_str)
            start_month = _parse_month(start_mon_str)

            if end_part and (
                end_part.lower().strip() in _PRESENT_WORDS
                or re.match(_PRESENT_PAT, end_part.strip(), re.IGNORECASE)
            ):
                end_year  = now.year
                end_month = now.month
            else:
                end_month = _parse_month(end_part)
                end_year  = int(end_yr_str) if end_yr_str else start_year + 1

            if start_year < _MIN_CAREER_YEAR or end_year < _MIN_CAREER_YEAR:
                continue
            if start_year > now.year or end_year > now.year + 1:
                continue

            start_dt = _to_dt(start_year, start_month)
            end_dt   = _to_dt(end_year, end_month)

            if end_dt > start_dt:
                intervals.append((start_dt, min(end_dt, _to_dt(now.year, now.month))))

        except (ValueError, TypeError):
            continue

    for m in _DATE_RANGE_RE.finditer(text):
        if m.start() in month_year_positions:
            continue

        start_yr_str, end_part = m.group(1), m.group(2)

        try:
            start_year = int(start_yr_str)

            if re.match(_PRESENT_PAT, end_part.strip(), re.IGNORECASE):
                end_year  = now.year
                end_month = now.month
            else:
                end_year  = int(end_part)
                end_month = 6

            if start_year < _MIN_CAREER_YEAR or end_year < _MIN_CAREER_YEAR:
                continue
            if start_year > now.year or end_year > now.year + 1:
                continue
            if end_year < start_year:
                continue

            ctx_start   = max(0, m.start() - 120)
            ctx_end     = min(len(text), m.end() + 40)
            surrounding = text[ctx_start:ctx_end]

            if _looks_like_edu_year_only(start_year, end_year, surrounding):
                continue

            text_before  = text[max(0, m.start() - 60): m.start()]
            start_month  = _guess_month_from_context(text_before)

            start_dt = _to_dt(start_year, start_month)
            end_dt   = _to_dt(end_year, end_month)

            if end_dt > start_dt:
                intervals.append((start_dt, min(end_dt, _to_dt(now.year, now.month))))

        except (ValueError, TypeError):
            continue

    if not intervals:
        return 0.0

    merged      = _merge_intervals(intervals)
    total_months = sum(_range_months(s, e) for s, e in merged)
    total_years  = round(min(total_months / 12, _MAX_TOTAL_YEARS), 1)

    return total_years


if __name__ == "__main__":
    import sys

    PASS = "\033[92mPASS\033[0m"
    FAIL = "\033[91mFAIL\033[0m"
    errors = 0

    def check(name, text, expected_min, expected_max):
        global errors
        result = extract_experience(text)
        ok = expected_min <= result <= expected_max
        status = PASS if ok else FAIL
        print(f"  [{status}] {name}: got {result} yrs  (expected {expected_min}–{expected_max})")
        if not ok:
            errors += 1

    print("\n=== experience_extractor.py unit tests ===\n")

    adobe_amazon_morgan = """
    Adobe, Bangalore Mar 2021 - Present
    Computer Scientist
    Led the migration of Hive and Presto jobs from Qubole to AWS EMR.
    AWS, EC2, S3, EMR, Hive, Presto

    Amazon, Bangalore Sept 2019 - Mar 2021
    Software Development Engineer
    Worked on migrating ML workflows to Native AWS.
    Java, Python, TypeScript, AWS Step Functions

    Morgan Stanley, Bangalore Aug 2017 - Aug 2019
    Technology Associate
    Built a visualization tool to group contextually related infrastructure alerts.
    Python, Flask, ReactJS
    """
    check("Adobe+Amazon+Morgan (bug report)", adobe_amazon_morgan, 8.4, 8.8)

    sept_test = "Company X Sept 2020 - Sept 2022 Senior Engineer Python Java"
    check("'Sept' abbreviation", sept_test, 1.9, 2.1)

    overlap_test = """
    Company A Jan 2020 - Dec 2022  Software Engineer
    Company B Jun 2021 - Jun 2023  Consultant
    """
    check("Overlapping roles merged", overlap_test, 3.3, 3.6)

    edu_test = """
    B.Tech Computer Science
    IIT Bombay University 2014 - 2018
    GPA 8.5
    """
    check("Education range filtered", edu_test, 0.0, 0.5)

    two_year_job = """
    Morgan Stanley, Bangalore Aug 2017 - Aug 2019
    Technology Associate
    Built ML-powered solutions. Python, Flask, scikit-learn
    """
    check("2-year job NOT filtered", two_year_job, 1.9, 2.1)

    explicit_test = "I have 6 years and 3 months of professional experience in software development."
    check("Explicit mention (6y 3m)", explicit_test, 6.2, 6.3)

    present_test = "Google, Mountain View Jun 2022 - Present Staff Engineer"
    result = extract_experience(present_test)
    expected_min = (datetime.now().year - 2022) + (datetime.now().month - 6) / 12 - 0.2
    check("Present-day role", present_test, max(0, expected_min), expected_min + 0.5)

    check("Empty text → 0", "", 0.0, 0.0)
    check("No dates → 0", "Skilled in Python and FastAPI.", 0.0, 0.0)

    mixed_test = """
    B.Tech, NIT Trichy University 2014 - 2018

    Infosys, Chennai Jul 2018 - Mar 2021
    Software Engineer Python Django MySQL

    TCS, Pune Apr 2021 - Present
    Senior Developer React Node.js
    """
    check("Mixed edu+job (edu filtered)", mixed_test, 7.4, 8.2)

    print(f"\n{'All tests passed!' if errors == 0 else f'{errors} test(s) failed.'}\n")
    sys.exit(0 if errors == 0 else 1)