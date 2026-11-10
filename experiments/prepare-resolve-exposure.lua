-- One-shot preparation in the manually created, selected research library.
local LIBRARY = "OC_COLOR_001_TEST"
local PROJECT = "EXPO_001_HDR_GLOBAL"
local ROOT = "E:/projects/逆向工程/capcut+达芬奇"
local INPUT = ROOT .. "/experiments/output/exposure-inputs/opaque-srgb16-patches.png"

local function json(value)
    local kind = type(value)
    if kind == "nil" then return "null" end
    if kind == "boolean" or kind == "number" then return tostring(value) end
    if kind == "string" then
        local escaped = value:gsub("\\", "\\\\"):gsub('"', '\\"'):gsub("%c", function(c)
            return string.format("\\u%04x", string.byte(c))
        end)
        return '"' .. escaped .. '"'
    end
    assert(kind == "table", "Unsupported snapshot value type")
    local keys, array = {}, true
    for key in pairs(value) do
        keys[#keys + 1] = key
        if type(key) ~= "number" then array = false end
    end
    if #keys == 0 then return "{}" end
    table.sort(keys)
    local parts = {}
    for index, key in ipairs(keys) do
        if array then
            assert(key == index, "Non-contiguous snapshot array")
            parts[#parts + 1] = json(value[key])
        else
            parts[#parts + 1] = json(key) .. ":" .. json(value[key])
        end
    end
    return (array and "[" or "{") .. table.concat(parts, ",") .. (array and "]" or "}")
end

local resolve = assert(bmd.scriptapp("Resolve"), "Resolve is not connected")
assert(resolve:GetVersionString() == "21.0.0.47", "Unexpected Resolve version")
local manager = assert(resolve:GetProjectManager())
local database = assert(manager:GetCurrentDatabase())
assert(database.DbType == "Disk" and database.DbName == LIBRARY, "Research library is not selected")
assert(#manager:GetProjectListInCurrentFolder() == 0, "Research project folder is not empty")
assert(#manager:GetFolderListInCurrentFolder() == 0, "Research folder contains existing subfolders")
local previous = manager:GetCurrentProject()
assert(not previous or previous:GetName() == "Untitled Project" or previous:GetName() == "Untitled",
       "A named project is already open")
if previous then
    assert(previous:GetTimelineCount() == 0, "Default project contains timelines")
    local previousRoot = assert(previous:GetMediaPool():GetRootFolder())
    assert(#previousRoot:GetClipList() == 0 and #previousRoot:GetSubFolderList() == 0,
           "Default project contains media or folders")
end

print("stage=before_create_research_project")
local project = assert(manager:CreateProject(PROJECT), "Project creation failed")
local projectId = project:GetUniqueId()
assert(project:GetName() == PROJECT and type(projectId) == "string" and projectId ~= "",
       "Created project identity is invalid")
local function guard()
    local currentDatabase = manager:GetCurrentDatabase()
    local currentProject = manager:GetCurrentProject()
    assert(currentDatabase.DbType == "Disk" and currentDatabase.DbName == LIBRARY,
           "Current library changed")
    assert(currentProject and currentProject:GetUniqueId() == projectId, "Current project changed")
end
guard()
assert(manager:SaveProject(), "Initial project save failed")
print("stage=research_project_created_and_saved")
local originalSettings = project:GetSetting()
for _, setting in ipairs({{"timelineResolutionWidth", "1920"},
                         {"timelineResolutionHeight", "1080"}, {"timelineFrameRate", "30"}}) do
    guard()
    assert(originalSettings[setting[1]] ~= nil, "Missing documented project setting")
    assert(project:SetSetting(setting[1], setting[2]), "Project setting rejected: " .. setting[1])
    assert(tonumber(project:GetSetting(setting[1])) == tonumber(setting[2]), "Project setting readback differs")
end
guard()
local pool = assert(project:GetMediaPool())
local clips = assert(pool:ImportMedia({INPUT}), "Media import failed")
assert(#clips == 1, "Expected exactly one imported image")
assert(clips[1]:GetClipProperty("File Path"):gsub("\\", "/") == INPUT, "Imported source path differs")
print("stage=single_patch_image_imported")
guard()
local timeline = assert(pool:CreateTimelineFromClips("PATCHES_1080P30", clips), "Timeline creation failed")
assert(project:SetCurrentTimeline(timeline), "Timeline selection failed")
local timelineId = timeline:GetUniqueId()
assert(type(timelineId) == "string" and timelineId ~= "", "Timeline identity is invalid")
assert(project:GetTimelineCount() == 1 and project:GetCurrentTimeline():GetUniqueId() == timelineId,
       "Current timeline readback differs")
for _, setting in ipairs({{"timelineResolutionWidth", 1920},
                         {"timelineResolutionHeight", 1080}, {"timelineFrameRate", 30}}) do
    assert(tonumber(timeline:GetSetting(setting[1])) == setting[2], "Timeline setting readback differs")
end
local items = timeline:GetItemListInTrack("video", 1)
assert(#items == 1, "Expected exactly one timeline item")
assert(resolve:OpenPage("color"), "Color page selection failed")
assert(resolve:GetCurrentPage() == "color", "Color page readback differs")
local graph = assert(items[1]:GetNodeGraph(), "Clip graph unavailable")
assert(timeline:SetCurrentTimecode(timeline:GetStartTimecode()), "Playhead selection failed")
assert(timeline:GetCurrentTimecode() == timeline:GetStartTimecode(), "Playhead readback differs")
guard()
assert(manager:SaveProject(), "Prepared project save failed")

local formats, codecs = project:GetRenderFormats(), {}
for format, description in pairs(formats) do
    local text = (tostring(format) .. " " .. tostring(description)):lower()
    if text:find("exr") or text:find("tif") or text:find("dpx") or text:find("png") then
        codecs[format] = project:GetRenderCodecs(format)
    end
end
local record = {
    scope = "isolated_project_preparation_no_scripted_hdr_change_or_measurement_export",
    runtime_version = resolve:GetVersionString(), library = LIBRARY,
    project_name = project:GetName(), project_id = projectId,
    settings_before = originalSettings, settings_after = project:GetSetting(),
    clip_properties = clips[1]:GetClipProperty(), timeline_name = timeline:GetName(),
    timeline_id = timelineId, timeline_settings = timeline:GetSetting(),
    timeline_start_frame = timeline:GetStartFrame(), timeline_start_timecode = timeline:GetStartTimecode(),
    timeline_end_frame = timeline:GetEndFrame(), timeline_item_count = #items,
    graph_node_count = graph:GetNumNodes(), render_formats = formats, image_codecs = codecs,
    current_page = resolve:GetCurrentPage(), project_saved = true,
    input_sha256 = "2daa68135e4ac8c0585fb33630ce5d69a735640799b82a8173caafbfc8d9f09f",
    hdr_exposure_set = false, measurement_frames_exported = 0,
}
print("record_json=" .. json(record))
print("stage=preparation_finished")
