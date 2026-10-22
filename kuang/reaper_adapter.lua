-- This adapter is exercised against a mock API; real REAPER validation is pending.
local r, project = reaper, plan.project
local proj = 0
local _, marker_count, region_count = r.CountProjectMarkers(proj)
if r.CountTracks(proj) ~= 0 or r.CountMediaItems(proj) ~= 0 or
   marker_count ~= 0 or region_count ~= 0 or r.CountTempoTimeSigMarkers(proj) ~= 0 then
  r.ShowMessageBox("Open a new empty project tab with no tempo markers before importing Kuang.", "Kuang", 0)
  return
end

local tracks, devices = {}, {}
local function check(ok, message)
  if not ok then error(message, 0) end
  return ok
end
local function seconds(tick) return tick / project.ppq * 60 / project.tempo_bpm end
local function gain(db) return 10 ^ (db / 20) end
local function normalized(mapping, value)
  for i = 1, #mapping.calibration - 1 do
    local a, b = mapping.calibration[i], mapping.calibration[i+1]
    if value >= a.value and value <= b.value then
      return a.normalized + (b.normalized - a.normalized) * (value - a.value) / (b.value - a.value)
    end
  end
  error("Value outside local plugin calibration", 0)
end
local function resolve(device, parameter)
  if parameter == "effect.wet" then
    local index = r.TrackFX_GetParamFromIdent(device.track, device.fx, ":wet")
    check(index >= 0, "Missing FX wet control")
    return index, function(v) return v end
  end
  if parameter == "effect.bypass" then
    local index = r.TrackFX_GetParamFromIdent(device.track, device.fx, ":bypass")
    check(index >= 0, "Missing FX bypass control")
    return index, function(v) return v end
  end
  local mapping = device.binding.parameters[parameter]
  check(mapping, "No binding for " .. parameter)
  local index = r.TrackFX_GetParamFromIdent(device.track, device.fx, mapping.ident)
  check(index >= 0, "Plugin parameter identifier no longer exists: " .. mapping.ident)
  local ok, name = r.TrackFX_GetParamName(device.track, device.fx, index)
  check(ok and name == mapping.name, "Plugin parameter name changed; inspect and recalibrate " .. parameter)
  return index, function(v) return normalized(mapping, v) end
end
local function add_device(track, config)
  local binding = plan.plugins[config.plugin_ref]
  local fx = r.TrackFX_AddByName(track, binding.fx_name, false, -1)
  check(fx >= 0, "Install/bind local plugin: " .. binding.fx_name)
  local device = {track=track, fx=fx, binding=binding}
  devices[config.id] = device
  if config.preset_ref then
    check(r.TrackFX_SetPreset(track, fx, binding.presets[config.preset_ref]), "Local REAPER preset was not found")
  end
  for parameter, value in pairs(config.parameters) do
    local index, convert = resolve(device, parameter)
    check(r.TrackFX_SetParamNormalized(track, fx, index, convert(value)), "Could not set plugin parameter")
  end
end
local function track_envelope(track, parameter)
  local chunks = { ["mixer.gain_db"]="VOLENV2", ["mixer.pan"]="PANENV2", ["mixer.mute"]="MUTEENV" }
  local tag = chunks[parameter]
  check(tag, "Unsupported mixer automation parameter")
  local envelope = r.GetTrackEnvelopeByChunkName(track, "<" .. tag)
  if not envelope then
    local ok, chunk = r.GetTrackStateChunk(track, "", false)
    check(ok, "Cannot read new track state")
    local definition = "<" .. tag .. "\nACT 1 -1\nVIS 1 1 1\nARM 0\nDEFSHAPE 0 -1 -1\n>\n"
    local modified, count = chunk:gsub(">%s*$", function() return definition .. ">\n" end, 1)
    check(count == 1 and r.SetTrackStateChunk(track, modified, false), "Cannot create native mixer envelope")
    envelope = r.GetTrackEnvelopeByChunkName(track, "<" .. tag)
  end
  return check(envelope, "Native mixer envelope unavailable")
end

r.Undo_BeginBlock2(proj)
r.PreventUIRefresh(1)
local ok, err = xpcall(function()
  check(r.SetTempoTimeSigMarker(proj, -1, 0, -1, -1, project.tempo_bpm, 4, 4, false), "Could not set tempo")
  for _, config in ipairs(project.tracks) do
    r.InsertTrackAtIndex(r.CountTracks(proj), false)
    local track = check(r.GetTrack(proj, r.CountTracks(proj)-1), "Could not create track")
    tracks[config.id] = track
    r.GetSetMediaTrackInfo_String(track, "P_NAME", config.name, true)
    r.GetSetMediaTrackInfo_String(track, "P_EXT:KUANG_ID", config.id, true)
    check(r.SetMediaTrackInfo_Value(track, "D_VOL", gain(config.controls["mixer.gain_db"])), "Could not set gain")
    check(r.SetMediaTrackInfo_Value(track, "D_PAN", config.controls["mixer.pan"]), "Could not set pan")
    check(r.SetMediaTrackInfo_Value(track, "B_MUTE", config.controls["mixer.mute"]), "Could not set mute")
    check(r.SetMediaTrackInfo_Value(track, "B_MAINSEND", config.output_master and 1 or 0), "Could not set master routing")
    if config.instrument and config.instrument.kind == "plugin" then add_device(track, config.instrument) end
    for _, effect in ipairs(config.effects) do add_device(track, effect) end
    for _, clip in ipairs(config.clips) do
      local item = check(r.CreateNewMIDIItemInProj(track, clip.start / project.ppq,
                         (clip.start + clip.length) / project.ppq, true), "Could not create MIDI item")
      local take = check(r.GetActiveTake(item), "Missing MIDI take")
      r.GetSetMediaItemInfo_String(item, "P_EXT:KUANG_ID", clip.id, true)
      r.GetSetMediaItemTakeInfo_String(take, "P_NAME", clip.name, true)
      r.MIDI_DisableSort(take)
      local channels = {}
      for _, note in ipairs(clip.notes) do
        local start = r.MIDI_GetPPQPosFromProjQN(take, (clip.start + note.start) / project.ppq)
        local ending = r.MIDI_GetPPQPosFromProjQN(take, (clip.start + note.start + note.duration) / project.ppq)
        check(r.MIDI_InsertNote(take, false, false, start, ending, note.channel, note.pitch, note.velocity, true), "Could not insert note")
        channels[note.channel] = true
      end
      if config.instrument and config.instrument.midi_program then
        local tick = r.MIDI_GetPPQPosFromProjQN(take, clip.start / project.ppq)
        for channel in pairs(channels) do
          check(r.MIDI_InsertCC(take, false, false, tick, 0xC0, channel, config.instrument.midi_program, 0), "Could not insert program change")
        end
      end
      r.MIDI_Sort(take)
    end
  end
  for _, config in ipairs(project.tracks) do
    for _, send in ipairs(config.sends) do
      local index = r.CreateTrackSend(tracks[config.id], tracks[send.target_track_id])
      check(index >= 0, "Could not create send")
      for field, value in pairs({D_VOL=gain(send.gain_db), D_PAN=send.pan, I_MIDIFLAGS=31, I_SRCCHAN=0, I_DSTCHAN=0,
                                 I_SENDMODE=send.mode == "post_fader" and 0 or 3}) do
        check(r.SetTrackSendInfo_Value(tracks[config.id], 0, index, field, value), "Could not configure send")
      end
    end
  end
  for _, lane in ipairs(project.automation) do
    local envelope, convert, base, owner
    if tracks[lane.target_id] then
      owner = tracks[lane.target_id]
      envelope = track_envelope(owner, lane.parameter_id)
      -- REAPER mute envelopes use 1=audible, while Kuang uses 1=muted.
      convert = lane.parameter_id == "mixer.gain_db" and gain or
                (lane.parameter_id == "mixer.mute" and function(v) return 1-v end or function(v) return v end)
      for _, config in ipairs(project.tracks) do
        if config.id == lane.target_id then base = config.controls[lane.parameter_id] end
      end
    else
      local device = check(devices[lane.target_id], "Automation target plugin not loaded")
      local index
      index, convert = resolve(device, lane.parameter_id)
      envelope = check(r.GetFXEnvelope(device.track, device.fx, index, true), "Could not create FX envelope")
      owner = device.track
      for _, config in ipairs(project.tracks) do
        local configs = {}
        if config.instrument then configs[#configs+1] = config.instrument end
        for _, effect in ipairs(config.effects) do configs[#configs+1] = effect end
        for _, candidate in ipairs(configs) do
          if candidate.id == lane.target_id then base = candidate.parameters[lane.parameter_id] end
        end
      end
    end
    r.SetTrackAutomationMode(owner, 1)
    r.DeleteEnvelopePointRange(envelope, -1e100, 1e100)
    local points = {}
    for _, point in ipairs(lane.points) do points[#points+1] = point end
    table.sort(points, function(a,b) return a.tick < b.tick end)
    if #points == 0 or points[1].tick > 0 then
      table.insert(points, 1, {tick=0, value=base, shape="step"})
    end
    local mode = r.GetEnvelopeScalingMode(envelope)
    for _, point in ipairs(points) do
      check(r.InsertEnvelopePoint(envelope, seconds(point.tick), r.ScaleToEnvelopeMode(mode, convert(point.value)),
                                 point.shape == "step" and 1 or 0, 0, false, true), "Could not insert envelope point")
    end
    r.Envelope_SortPoints(envelope)
  end
  for _, section in ipairs(project.sections) do
    check(r.AddProjectMarker2(proj, true, seconds(section.start), seconds(section.start + section.length),
                             section.name, -1, 0) >= 0, "Could not create section region")
  end
  r.SetProjExtState(proj, "Kuang", "canonical_json", plan.canonical_json)
  r.SetProjExtState(proj, "Kuang", "source_hash", plan.project_hash)
end, debug.traceback)
r.PreventUIRefresh(-1)
r.Undo_EndBlock2(proj, "Import Kuang structured session", -1)
if not ok then
  r.Undo_DoUndo2(proj)
  r.ShowMessageBox("Import failed; REAPER undo requested. Inspect the empty tab before retrying.\n" .. tostring(err), "Kuang", 0)
else
  r.TrackList_AdjustWindows(false)
  r.UpdateArrange()
  r.ShowMessageBox("Imported editable tracks, MIDI, routing and automation. Save this tab as an .RPP.\n" ..
                  table.concat(plan.warnings, "\n"), "Kuang", 0)
end
