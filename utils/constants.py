MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

BLOCKLIST = {
    "Sensitive Information": [
        r"\bAPI\s*KEY\b",
        r"\bCREDIT\s*CARD\b",
        r"\bPASSWORD\b",
        r"\bSSN\b",
    ],
    "Violence / Harm": [
        r"\bKILL\b",
        r"\bHACK\b",
        r"\bINJURE\b",
        r"\bATTACK\b",
    ],
}
