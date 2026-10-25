from datetime import date, timedelta

from tests.test_clinician_insights import base
from tests.test_practice import care  # noqa: F401

URL = "/api/v1/practice/mood"


async def test_one_mood_a_day_seen_by_the_clinician(care):  # noqa: F811
    patient, clinician, pid = care
    today = date.today().isoformat()
    assert (await patient.get(URL, params={"day": today})).json() is None
    assert (await patient.put(URL, json={"mood": "low", "day": today})).status_code == 200
    assert (await patient.put(URL, json={"mood": "good", "day": today})).json()["mood"] == "good"
    assert (await patient.get(URL, params={"day": today})).json()["mood"] == "good"

    long_ago = (date.today() - timedelta(days=30)).isoformat()
    assert (await patient.put(URL, json={"mood": "low", "day": long_ago})).status_code == 422
    assert (await patient.put(URL, json={"mood": "meh", "day": today})).status_code == 422

    assert (await clinician.get(f"{base(pid)}/moods")).json() == [{"day": today, "mood": "good"}]
    assert (await clinician.put(URL, json={"mood": "good", "day": today})).status_code == 403
