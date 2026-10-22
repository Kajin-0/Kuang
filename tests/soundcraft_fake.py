"""Mock process transport based on recorded 0.11.0 contracts, not an audio engine."""

import json
import subprocess
from copy import deepcopy
from pathlib import Path

FIXTURES = Path(__file__).with_name("fixtures")
CONTRACT = json.loads((FIXTURES / "soundcraft-contract.json").read_text())
NATIVE = json.loads((FIXTURES / "soundcraft-small-native.json").read_text())


def native_param(text):
    if text == "volume": return "Volume"
    if text == "mute": return "Mute"
    if text in ("pan", "pan2"): return {"Pan": int(text == "pan2")}
    _, slot, param = text.split(":")
    return {"Plugin": {"slot": int(slot), "param": param}}


class FakeCLI:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.collateral = None
        self.reopen_drift = False

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if self.failure == "timeout": raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        if self.failure == "exit": return subprocess.CompletedProcess(argv, 9, "", "failed")
        if self.failure == "warning": return subprocess.CompletedProcess(argv, 0, "", "warning: missing media")
        if self.failure == "json": return subprocess.CompletedProcess(argv, 0, "broken report", "")
        if argv[1] == "--version":
            return subprocess.CompletedProcess(argv, 0, "SoundCraft CLI 0.11.0\n", "")
        if argv[1] == "describe":
            return subprocess.CompletedProcess(argv, 0, json.dumps(CONTRACT["commands"][argv[2]]), "")
        assert argv[1] == "run"
        doc = json.loads(Path(argv[argv.index("--in")+1]).read_text()) if "--in" in argv else deepcopy(NATIVE)
        lines = []
        for index, item in enumerate(argv):
            if item != "--cmd": continue
            command, text = argv[index+1].split("=", 1)
            p = json.loads(text)
            result = {}
            track = next((t for t in doc["tracks"] if t["id"] == p.get("track")), None)
            if command == "engine.plugins": result = list(CONTRACT["plugins"].values())
            elif command == "file.import_midi":
                assert Path(p["path"]).read_bytes().startswith(b"MThd")
                doc = deepcopy(NATIVE)
                doc["markers"] = []
                doc["next_id"] = 5
                for t in doc["tracks"]:
                    t["automation"] = []
                    t["comments"] = ""
                    t["mixer"].update(volume_db=0.0, pan=[-1.0, 1.0], mute=False)
                result = {"tracks": [t["id"] for t in doc["tracks"]]}
            elif command == "event.tempo": doc["tempo"]["tempos"] = [{"tick": 0, "bpm": p["bpm"]}]
            elif command == "mix.volume": track["mixer"]["volume_db"] = p["db"]
            elif command == "mix.pan": track["mixer"]["pan"][p["index"]] = p["pan"]
            elif command == "mix.mute": track["mixer"]["mute"] = p["value"]
            elif command == "track.comments": track["comments"] = p["comments"]
            elif command == "mix.instrument":
                track["instrument"] = {"plugin": p["plugin"], "params": p["params"], "active": True, "bypass": False, "preset": "<factory default>"}
            elif command == "mix.insert":
                params = {x["id"]: x["default"] for x in CONTRACT["plugins"][p["plugin"]]["params"]}
                params.update(p.get("params", {}))
                track["mixer"]["inserts"][p["slot"]] = {"plugin": p["plugin"], "params": params, "active": True, "bypass": False, "preset": "<factory default>"}
            elif command == "mix.insert_bypass": track["mixer"]["inserts"][p["slot"]]["bypass"] = p["value"]
            elif command == "mix.insert_params": track["mixer"]["inserts"][p["slot"]]["params"].update(p["params"])
            elif command in ("automation.clear", "automation.set_point"):
                param = native_param(p["param"])
                lane = next((a for a in track["automation"] if a["param"] == param), None)
                if command == "automation.clear":
                    if lane: lane["points"] = []
                else:
                    if lane is None:
                        lane = {"param": param, "points": [], "enabled": True}
                        track["automation"].append(lane)
                    lane["points"] = [x for x in lane["points"] if x["at"] != p["at"]] + [{"at": p["at"], "value": p["value"]}]
                    lane["points"].sort(key=lambda x: x["at"])
            elif command == "markers.add":
                doc["markers"].append({"id": doc["next_id"], "number": len(doc["markers"])+1, "name": p["name"],
                                       "kind": "Selection", "start": p["start"], "end": p["end"], "comments": "", "color": None, "ruler": 1, "track": None})
                doc["next_id"] += 1
            elif command == "session.inspect":
                result = {"sample_rate": doc["sample_rate"], "tracks": [
                    {"id": t["id"], "clips": [{"notes": len(c["content"]["Midi"]["sequence"]["notes"])}
                                              for c in t["playlists"][0]["clips"]]} for t in doc["tracks"]]}
            elif command not in ("session.new", "mix.automation_mode"):
                raise AssertionError("unimplemented fake command: " + command)
            lines.append(command + ": " + json.dumps(result))
        if "--save" in argv:
            destination = Path(argv[argv.index("--save")+1])
            if self.collateral:
                self.collateral(doc)
                self.collateral = None
            if self.reopen_drift and destination.parent.name == "reopen":
                doc["tracks"][1]["comments"] = "unrequested reopen mutation"
            destination.write_text(json.dumps(doc))
            lines.append(json.dumps({"path": str(destination), "audio_files_written": 0}))
        return subprocess.CompletedProcess(argv, 0, "\n".join(lines)+"\n", "")
