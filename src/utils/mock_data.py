"""
Mock data for ECHO application.
Static draft data for demonstration.
"""

from src.models.song import Song


def get_mock_drafts() -> list:
    """
    Returns a list of 3 mock song drafts.
    These are static examples for the sidebar.
    """
    drafts = [
        {
            "id": "draft_1",
            "name": "Summer Nights",
            "song": Song(title="Summer Nights", intent="A nostalgic song about warm summer evenings")
        },
        {
            "id": "draft_2",
            "name": "City Lights",
            "song": Song(title="City Lights", intent="An upbeat track about urban life")
        },
        {
            "id": "draft_3",
            "name": "Ocean Dreams",
            "song": Song(title="Ocean Dreams", intent="A calming melody inspired by the sea")
        }
    ]
    return drafts
