from kuang.generator import generate
from kuang.schema import BAR, AutomationLane, AutomationPoint, Note, validate
from kuang.transactions import Scope


def small_project():
    project = generate(7)
    project.tracks = project.tracks[:2]
    project.tracks[0].clips = project.tracks[0].clips[:1]
    project.tracks[0].clips[0].notes = [
        Note("test-note-a", 0, 240, 36, 100, 9),
        Note("test-note-b", 960, 240, 36, 90, 9),
        Note("test-note-c", 1920, 480, 38, 80, 9),
    ]
    project.tracks[1].clips = project.tracks[1].clips[:1]
    project.automation = [AutomationLane("test-lane", "track-kick", "mixer.pan", [
        AutomationPoint("test-point-a", 0, 0, "linear"),
        AutomationPoint("test-point-b", BAR, 0.5, "linear"),
    ])]
    validate(project)
    return project


def full_scope(project):
    return Scope([t.id for t in project.tracks], [c.id for t in project.tracks for c in t.clips],
                 [p.id for p in project.parameters], None, None)
