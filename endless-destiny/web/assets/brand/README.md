# The official logo

The game draws the Echoes in the Dark leaf as a vector so it can animate: it draws itself on the
title screen, fills with gold as echoes are gathered, and gathers from golden sparks at the end.

To show the exact official artwork as well:

1. Export the leaf logo as a PNG with a **transparent background** and **light (white) lines**.
   The game is dark, so black lines on white won't read.
2. Save it here as `logo.png`.
3. In `brand.json` next to it, set `"logo": "logo.png"`.

The title and ending screens fade the real artwork in over the drawn leaf once it has finished drawing.
