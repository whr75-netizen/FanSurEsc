-- One isolated capability check. Never writes the source sprite or user settings.
local source = app.params["source"]
local output = app.params["output"]
assert(source and output, "source and output parameters required")
local sprite = app.open(source)
assert(sprite, "source could not be opened")
local oldWidth, oldHeight = sprite.width, sprite.height
app.command.Rotate { ui=false, target="default", angle="90" }
assert(sprite.width == oldHeight and sprite.height == oldWidth,
       "90 degree rotation did not swap canvas dimensions")
sprite:saveCopyAs(output)
print("ASEPRITE_ROTATE_90: " .. oldWidth .. "x" .. oldHeight .. " -> " ..
      sprite.width .. "x" .. sprite.height .. "; " .. output)
sprite:close()
