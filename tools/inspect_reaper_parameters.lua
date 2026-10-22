-- Run inside REAPER with the user's installed instrument on a selected track.
local r = reaper
local track = r.GetSelectedTrack(0, 0)
if not track then r.ShowMessageBox("Select a track with your local plugin first.", "Kuang", 0) return end
r.ShowConsoleMsg("Kuang local plugin inspection (no parameters changed)\n")
for fx = 0, r.TrackFX_GetCount(track)-1 do
  local _, name = r.TrackFX_GetFXName(track, fx, "")
  r.ShowConsoleMsg("FX " .. fx .. ": " .. name .. "\n")
  for parameter = 0, r.TrackFX_GetNumParams(track, fx)-1 do
    local ok, ident = r.TrackFX_GetParamIdent(track, fx, parameter)
    local _, label = r.TrackFX_GetParamName(track, fx, parameter)
    if ok then
      r.ShowConsoleMsg(ident .. "\t" .. label .. "\t" .. r.TrackFX_GetParamNormalized(track, fx, parameter) .. "\n")
    end
  end
end
