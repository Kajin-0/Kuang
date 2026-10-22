import unittest
from copy import deepcopy
from pathlib import Path

from kuang.generator import generate
from kuang.reaper import (Bindings, CalibrationPoint, ParameterBinding, PluginBinding,
                          import_plan, script)
from kuang.schema import (BAR, AutomationLane, AutomationPoint, Clip, Send, Track,
                          ValidationError, state_hash)
from lua_runtime import execute

MOCK = Path(__file__).with_name("mock_reaper.lua").read_text(encoding="utf-8")


def plugin_fixture():
    p = generate(7)
    inst = p.tracks[4].instrument
    inst.kind, inst.plugin_ref, inst.preset_ref = "plugin", "user:test-synth", "user:test-preset"
    inst.parameters = {"synth.cutoff_hz": 1800}
    binding = Bindings("0.1", {"user:test-synth": PluginBinding("Test Synth", {"user:test-preset": "My local preset"}, {
        "synth.cutoff_hz": ParameterBinding("cutoff-id", "Cutoff", [CalibrationPoint(20, 0), CalibrationPoint(1800, 0.5), CalibrationPoint(20000, 1)])})})
    p.automation.append(AutomationLane("lane-cutoff", inst.id, "synth.cutoff_hz", [
        AutomationPoint("point-cutoff-a", 0, 20, "linear"),
        AutomationPoint("point-cutoff-b", BAR, 1800, "linear"),
        AutomationPoint("point-cutoff-c", 2*BAR, 20000, "linear")]))
    return p, binding


class ReaperContractTests(unittest.TestCase):
    def test_plan_preserves_canonical_project_identity_and_data(self):
        p = generate(7)
        plan = import_plan(p)
        self.assertEqual(plan["project_hash"], state_hash(p))
        self.assertEqual(plan["contract_version"], "0.1")
        self.assertEqual(sum(len(c["notes"]) for t in plan["project"]["tracks"] for c in t["clips"]), 1083)
        self.assertEqual(len(plan["warnings"]), 8)
        self.assertIn("reaper:ReaVerbate", plan["plugins"])
        self.assertEqual(script(p), script(p))

    def test_missing_plugin_binding_or_preset_fails_before_export(self):
        p, binding = plugin_fixture()
        with self.assertRaisesRegex(ValidationError, "missing local plugin"): import_plan(p)
        binding.plugins["user:test-synth"].presets = {}
        with self.assertRaisesRegex(ValidationError, "preset"): import_plan(p, binding)

    def test_binding_requires_identifier_name_and_full_calibration(self):
        for change in ("ident", "name", "calibration", "range", "normalized", "order"):
            p, binding = plugin_fixture()
            mapping = binding.plugins["user:test-synth"].parameters["synth.cutoff_hz"]
            if change == "ident": mapping.ident = ""
            if change == "name": mapping.name = ""
            if change == "calibration": mapping.calibration = []
            if change == "range": mapping.calibration[0].value = 0
            if change == "normalized": mapping.calibration[0].normalized = -1
            if change == "order": mapping.calibration[1].value = 20001
            with self.subTest(change=change), self.assertRaises(ValidationError): import_plan(p, binding)

    def test_unmapped_parameters_audio_and_extra_track_controls_fail_explicitly(self):
        p, binding = plugin_fixture()
        binding.plugins["user:test-synth"].parameters = {}
        with self.assertRaisesRegex(ValidationError, "calibrated"): import_plan(p, binding)
        p = generate()
        p.tracks.append(Track("audio", "Audio", "audio", None, {"mixer.gain_db": 0, "mixer.pan": 0, "mixer.mute": 0},
                              [], [Clip("audio-clip", "Recording", "audio", 0, 960, [], "user:recording")], [], True))
        with self.assertRaisesRegex(ValidationError, "audio tracks"): import_plan(p)

    def test_generated_lua_executes_complete_midi_mixer_fx_and_automation_contract(self):
        p = generate()
        p.tracks[0].sends = [Send("send-test", "track-pad", -6, -0.2, "pre_fader")]
        code = script(p)
        execute(MOCK + "\n" + code + "\n" + r'''
assert(#K.tracks == 8 and #K.regions == 5 and K.tempo.bpm == 124)
assert(K.refresh == 0 and K.began and K.ended and K.updated and not K.undo_called)
local count = 0
for _, track in ipairs(K.tracks) do
  assert(track.strings["P_EXT:KUANG_ID"])
  for _, item in ipairs(track.items) do
    count = count + #item.take.notes
    assert(item.take.sorted and item.strings["P_EXT:KUANG_ID"])
  end
end
assert(count == 1083)
assert(K.tracks[1].items[1].take.notes[1].ending == 60) -- 120 Kuang ticks, host PPQ=480
assert(math.abs(K.tracks[1].fields.D_VOL - 10^(-9/20)) < 1e-12)
assert(K.tracks[3].fields.D_PAN == 0.16)
assert(K.tracks[1].sends[1].target == K.tracks[6] and K.tracks[1].sends[1].I_SENDMODE == 3)
assert(K.tracks[1].sends[1].I_MIDIFLAGS == 31) -- audio-only send, no duplicated MIDI triggers
assert(K.tracks[6].fx[1].parameters[99] == 0.18 and K.tracks[6].fx[1].parameters[100] == 0)
local env = K.tracks[6].envelopes["<VOLENV2"]
assert(#env.points == 5 and env.sorted and K.tracks[6].automation_mode == 1)
assert(math.abs(env.points[1].value - 2*10^(-30/20)) < 1e-12)
assert(math.abs(env.points[2].time - 16*60/124) < 1e-12)
assert(#K.ext["Kuang:source_hash"] == 64 and K.ext["Kuang:canonical_json"]:find('"not rendered"'))
''')

    def test_generated_lua_plugin_identifier_calibration_preset_and_fx_envelope(self):
        p, binding = plugin_fixture()
        execute(MOCK + "\n" + script(p, binding) + "\n" + r'''
assert(not K.undo_called)
local synth = K.tracks[5].fx[1]
assert(synth.preset == "My local preset" and synth.parameters[7] == 0.5)
assert(#synth.envelopes[7].points == 3)
assert(synth.envelopes[7].points[1].value == 0)
assert(synth.envelopes[7].points[2].value == 0.5)
assert(synth.envelopes[7].points[3].value == 1)
''')

    def test_generated_lua_refuses_nonempty_projects_and_rolls_back_missing_plugins(self):
        code = script(generate())
        execute(MOCK + "\nK.tracks={{}}\n" + code + "\nassert(not K.began and #K.tracks==1 and #K.messages==1)")
        execute(MOCK + "\nK.missing_plugin=true\n" + code + "\nassert(K.undo_called and #K.tracks==0 and K.refresh==0 and not K.updated)")

    def test_generated_lua_detects_changed_plugin_names_and_missing_presets(self):
        p, binding = plugin_fixture()
        for setting in ("K.changed_name=true", "K.missing_preset=true"):
            execute(MOCK + "\n" + setting + "\n" + script(p, binding) + "\nassert(K.undo_called and #K.tracks==0 and K.refresh==0)")

    def test_lua_strings_are_inert_and_utf8_survives(self):
        p = generate()
        p.tracks[0].name = '"; KUANG_INJECTED=true; -- café 音\n\\123'
        execute(MOCK + "\n" + script(p) + "\nassert(not KUANG_INJECTED)\nassert(K.tracks[1].strings.P_NAME:find('café 音',1,true))")

    def test_mute_envelope_inverts_canonical_mute_values_and_uses_step(self):
        p = generate()
        p.automation.append(AutomationLane("lane-mute", "track-kick", "mixer.mute", [
            AutomationPoint("point-mute-a", 0, 0, "step"), AutomationPoint("point-mute-b", BAR, 1, "step")]))
        execute(MOCK + "\n" + script(p) + "\n" + r'''
local env = K.tracks[1].envelopes["<MUTEENV"]
assert(env.points[1].value == 1 and env.points[2].value == 0)
assert(env.points[1].shape == 1 and env.points[2].shape == 1)
''')
