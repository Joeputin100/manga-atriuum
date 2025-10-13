#!/bin/bash

# --- Configuration ---
INPUT_FILE="frames.jpg"
OUTPUT_GIF="duck_coffee.gif"

# Number of frames in the grid (e.g., if it's a 4x3 grid, we want 10 frames)
# Assuming your image is a grid that needs to be sliced into 10 frames
# Adjust this geometry based on how the frames are tiled in your single JPG.
FRAME_GEOMETRY="4x3@10" 

# Delay between frames in 1/100ths of a second (e.g., 20 = 0.2 seconds)
FRAME_DELAY=20 

# --- Script Execution ---

echo "Starting frame extraction and GIF creation..."

# 1. Extract frames from the grid and save them as frame-00.png, frame-01.png, etc.
# The '+adjoin' option ensures each slice is saved as a separate file.
# The '+append' part is generally for stitching, but here we use -crop to slice the grid.
convert "$INPUT_FILE" -crop "$FRAME_GEOMETRY" +adjoin frame-%02d.png

# Check if frame files were created (we expect at least 10)
if [ ! -f frame-09.png ]; then
    echo "ERROR: Could not generate all 10 individual frame files."
    echo "Please check the '$INPUT_FILE' arrangement and the FRAME_GEOMETRY setting."
    exit 1
fi

# 2. Combine all the generated frames into an animated GIF
convert -delay $FRAME_DELAY -loop 0 frame-*.png "$OUTPUT_GIF"

# 3. Clean up the individual frame files
rm frame-*.png

echo "✅ Success! Animated GIF created: $OUTPUT_GIF"
