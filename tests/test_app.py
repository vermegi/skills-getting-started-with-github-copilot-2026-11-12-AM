from copy import deepcopy


def test_root_redirects_to_homepage(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_details_and_participants(client, activities):
    # Arrange
    expected = deepcopy(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected
    for activity in response.json().values():
        assert set(activity) == {
            "description", "schedule", "max_participants", "participants"
        }
        assert isinstance(activity["description"], str)
        assert isinstance(activity["schedule"], str)
        assert isinstance(activity["max_participants"], int)
        assert isinstance(activity["participants"], list)


def test_signup_adds_participant_and_preserves_other_activities(client, activities):
    # Arrange
    email = "new.student@mergington.edu"
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].append(email)

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    listing = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert listing.status_code == 200
    assert listing.json() == expected
    assert activities == expected


def test_signup_accepts_last_spot_then_rejects_next_participant(client, activities):
    # Arrange
    activity = activities["Chess Club"]
    activity["max_participants"] = len(activity["participants"]) + 1
    email = "last.spot@mergington.edu"
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].append(email)

    # Act
    accepted = client.post("/activities/Chess Club/signup", params={"email": email})
    rejected = client.post(
        "/activities/Chess Club/signup",
        params={"email": "too.late@mergington.edu"},
    )

    # Assert
    assert accepted.status_code == 200
    assert accepted.json() == {"message": f"Signed up {email} for Chess Club"}
    assert rejected.status_code == 400
    assert rejected.json() == {"detail": "Activity is full"}
    assert activities == expected


def test_duplicate_signup_does_not_change_activities(client, activities):
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    expected = deepcopy(activities)

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities == expected


def test_full_activity_signup_does_not_change_activities(client, activities):
    # Arrange
    activity = activities["Chess Club"]
    activity["max_participants"] = len(activity["participants"])
    expected = deepcopy(activities)

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activities == expected


def test_unknown_activity_signup_does_not_change_activities(client, activities):
    # Arrange
    expected = deepcopy(activities)
    url = "/activities/Unknown Club/signup"

    # Act
    response = client.post(url, params={"email": "new.student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == expected


def test_signup_requires_email_without_changing_activities(client, activities):
    # Arrange
    expected = deepcopy(activities)

    # Act
    response = client.post("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert activities == expected
