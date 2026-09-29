#!/usr/bin/env bash
# Download the photographic plates used by the v2 cut (not stored in git).
#   weic2205a  "Cosmic Cliffs" - NASA, ESA, CSA, STScI (ESA/Webb, CC BY 4.0)
#   ocean_b    Anthony Cantin / Unsplash (Unsplash License)
#   mount_a    Gantavya Bhatt / Unsplash (Unsplash License)
#   forest_a   Wolfgang Hasselmann / Unsplash (Unsplash License)
set -euo pipefail
cd "$(dirname "$0")/assets/plates" 2>/dev/null || { mkdir -p "$(dirname "$0")/assets/plates"; cd "$(dirname "$0")/assets/plates"; }
curl -sSfL -o weic2205a.jpg "https://cdn.esawebb.org/archives/images/large/weic2205a.jpg"
curl -sSfL -o ocean_b.jpg  "https://images.unsplash.com/photo-1644955770652-2afd6c313722?fm=jpg&q=92&w=5200"
curl -sSfL -o mount_a.jpg  "https://images.unsplash.com/photo-1691539706978-3cb89d88915f?fm=jpg&q=92&w=5200"
curl -sSfL -o forest_a.jpg "https://images.unsplash.com/photo-1757412741742-288712226fde?fm=jpg&q=92&w=5200"
ls -la
