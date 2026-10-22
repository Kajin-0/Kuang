-- Test double only. It checks adapter behavior, not actual REAPER compatibility.
K = {tracks={}, regions={}, ext={}, refresh=0, messages={}}
reaper = {}
local r = reaper
function r.CountProjectMarkers(_) return #K.regions, 0, #K.regions end
function r.CountTracks(_) return #K.tracks end
function r.CountMediaItems(_)
  local count = 0
  for _, t in ipairs(K.tracks) do count = count + #(t.items or {}) end
  return count
end
function r.CountTempoTimeSigMarkers(_) return K.tempo and 1 or 0 end
function r.ShowMessageBox(message, _, _) K.messages[#K.messages+1] = message end
function r.Undo_BeginBlock2(_) K.began = true end
function r.PreventUIRefresh(amount) K.refresh = K.refresh + amount end
function r.SetTempoTimeSigMarker(_, _, _, _, _, bpm, numerator, denominator, _)
  K.tempo = {bpm=bpm, numerator=numerator, denominator=denominator}
  return true
end
function r.InsertTrackAtIndex(index, _) table.insert(K.tracks, index+1, {items={}, fx={}, fields={}, strings={}, envelopes={}, sends={}}) end
function r.GetTrack(_, index) return K.tracks[index+1] end
function r.GetSetMediaTrackInfo_String(track, key, value, set)
  if set then track.strings[key] = value end
  return true, track.strings[key]
end
function r.SetMediaTrackInfo_Value(track, key, value) track.fields[key] = value return true end
function r.TrackFX_AddByName(track, name, _, instantiate)
  assert(instantiate == -1)
  if K.missing_plugin then return -1 end
  track.fx[#track.fx+1] = {name=name, parameters={}, envelopes={}}
  return #track.fx-1
end
function r.TrackFX_SetPreset(track, index, name)
  if K.missing_preset then return false end
  track.fx[index+1].preset = name
  return true
end
function r.TrackFX_GetParamFromIdent(_, _, ident)
  return ({[":wet"]=99, [":bypass"]=100, ["cutoff-id"]=7})[ident] or -1
end
function r.TrackFX_GetParamName(_, _, index)
  return true, K.changed_name and "Renamed" or (index == 7 and "Cutoff" or "Wrapper")
end
function r.TrackFX_SetParamNormalized(track, fx, parameter, value)
  track.fx[fx+1].parameters[parameter] = value
  return true
end
function r.CreateNewMIDIItemInProj(track, start, ending, qn)
  assert(qn == true and ending > start)
  local item = {start=start, ending=ending, strings={}, take={notes={}, cc={}, strings={}}}
  item.take.item = item
  track.items[#track.items+1] = item
  return item
end
function r.GetActiveTake(item) return item.take end
function r.GetSetMediaItemInfo_String(item, key, value, _) item.strings[key] = value return true, value end
function r.GetSetMediaItemTakeInfo_String(take, key, value, _) take.strings[key] = value return true, value end
function r.MIDI_DisableSort(take) take.sort_disabled = true end
function r.MIDI_GetPPQPosFromProjQN(take, qn) return (qn-take.item.start)*480 end
function r.MIDI_InsertNote(take, selected, muted, start, ending, channel, pitch, velocity, no_sort)
  assert(not selected and not muted and no_sort and ending > start)
  take.notes[#take.notes+1] = {start=start, ending=ending, channel=channel, pitch=pitch, velocity=velocity}
  return true
end
function r.MIDI_InsertCC(take, _, _, tick, status, channel, program, _)
  take.cc[#take.cc+1] = {tick=tick, status=status, channel=channel, program=program}
  return true
end
function r.MIDI_Sort(take) take.sorted = true end
function r.CreateTrackSend(track, target)
  track.sends[#track.sends+1] = {target=target}
  return #track.sends-1
end
function r.SetTrackSendInfo_Value(track, category, index, key, value)
  assert(category == 0)
  track.sends[index+1][key] = value
  return true
end
function r.GetTrackEnvelopeByChunkName(track, tag) return track.envelopes[tag] end
function r.GetTrackStateChunk(_, _, _) return true, "<TRACK\n>\n" end
function r.SetTrackStateChunk(track, chunk, _)
  for _, tag in ipairs({"VOLENV2", "PANENV2", "MUTEENV"}) do
    if chunk:find("<" .. tag, 1, true) then track.envelopes["<"..tag] = {points={}, scale=tag == "VOLENV2" and 1 or 0} end
  end
  return true
end
function r.GetFXEnvelope(track, fx, index, create)
  assert(create)
  local device = track.fx[fx+1]
  device.envelopes[index] = device.envelopes[index] or {points={}, scale=0}
  return device.envelopes[index]
end
function r.SetTrackAutomationMode(track, mode) track.automation_mode = mode end
function r.DeleteEnvelopePointRange(env, _, _) env.points = {} return true end
function r.GetEnvelopeScalingMode(env) return env.scale end
function r.ScaleToEnvelopeMode(mode, value) return mode == 1 and value*2 or value end
function r.InsertEnvelopePoint(env, time, value, shape, _, _, _)
  env.points[#env.points+1] = {time=time, value=value, shape=shape}
  return true
end
function r.Envelope_SortPoints(env) env.sorted = true end
function r.AddProjectMarker2(_, is_region, start, ending, name, _, _)
  assert(is_region)
  K.regions[#K.regions+1] = {start=start, ending=ending, name=name}
  return #K.regions-1
end
function r.SetProjExtState(_, namespace, key, value) K.ext[namespace..":"..key] = value return 1 end
function r.Undo_EndBlock2(_, _, _) K.ended = true end
function r.Undo_DoUndo2(_) K.undo_called = true K.tracks = {} K.regions = {} K.ext = {} K.tempo = nil end
function r.TrackList_AdjustWindows(_) K.adjusted = true end
function r.UpdateArrange() K.updated = true end
