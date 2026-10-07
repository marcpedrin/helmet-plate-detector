"""Rider association rules (Prompt 2 §6.2)."""

from __future__ import annotations

from app.core.types import Track
from app.pipeline.association import associate_riders

W, H = 1280, 720


def moto(tid, box):
    return Track(tid, box, 0.9, "motorcycle")


def person(tid, box):
    return Track(tid, box, 0.9, "person")


def test_two_bikes_three_persons_one_pedestrian():
    tracks = [
        moto(1, (100, 400, 260, 600)),
        person(11, (130, 250, 230, 520)),  # rider on bike 1
        moto(2, (700, 380, 860, 580)),
        person(21, (720, 230, 820, 500)),  # rider on bike 2
        person(22, (760, 220, 850, 480)),  # pillion on bike 2
        person(99, (1000, 200, 1080, 600)),  # pedestrian far away
    ]
    riders = {r.rider_id: r for r in associate_riders(tracks, W, H)}
    assert set(riders) == {1, 2}
    assert [p.track_id for p in riders[1].persons] == [11]
    assert sorted(p.track_id for p in riders[2].persons) == [21, 22]
    assert riders[2].bbox == (700, 220, 860, 580)  # union of bike + both persons


def test_pedestrian_standing_next_to_bike_is_not_a_rider():
    tracks = [moto(1, (100, 400, 260, 600)), person(5, (300, 250, 380, 650))]
    (rider,) = associate_riders(tracks, W, H)
    assert rider.persons == ()


def test_person_goes_to_bike_with_highest_ioa():
    tracks = [
        moto(1, (100, 400, 300, 600)),
        moto(2, (250, 400, 450, 600)),
        person(7, (280, 250, 380, 520)),  # mostly over bike 2
    ]
    riders = {r.rider_id: r for r in associate_riders(tracks, W, H)}
    assert riders[1].persons == ()
    assert [p.track_id for p in riders[2].persons] == [7]


def test_bike_without_person_gets_upward_expanded_bbox():
    (rider,) = associate_riders([moto(3, (500, 400, 600, 500))], W, H)
    # expand(fx=0.05, fy_top=0.8, fy_bottom=0): 100x100 box -> x +-5, y1 - 80
    assert rider.bbox == (495, 320, 605, 500)
    assert rider.persons == ()


def test_bbox_is_clipped_to_frame():
    (rider,) = associate_riders([moto(4, (0, 10, 100, 110))], W, H)
    assert rider.bbox[0] == 0 and rider.bbox[1] == 0


def test_no_motorcycles_no_riders():
    assert associate_riders([person(1, (0, 0, 50, 100))], W, H) == []
