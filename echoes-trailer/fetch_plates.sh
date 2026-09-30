#!/usr/bin/env bash
# Download the photographic plates used by the v2 cut (not stored in git).
#   weic2205a  "Cosmic Cliffs" - NASA, ESA, CSA, STScI (ESA/Webb, CC BY 4.0)
#   ocean_b    Anthony Cantin / Unsplash (Unsplash License)
#   mount_a    Gantavya Bhatt / Unsplash (Unsplash License)
#   forest_a   Wolfgang Hasselmann / Unsplash (Unsplash License)
#   aurora_a   Jonny Gios / Unsplash (Unsplash License)                (v3)
#   volc_b     Wolfgang Hasselmann / Unsplash (Unsplash License)       (v3)
set -euo pipefail
cd "$(dirname "$0")/assets/plates" 2>/dev/null || { mkdir -p "$(dirname "$0")/assets/plates"; cd "$(dirname "$0")/assets/plates"; }
curl -sSfL -o weic2205a.jpg "https://cdn.esawebb.org/archives/images/large/weic2205a.jpg"
curl -sSfL -o ocean_b.jpg  "https://images.unsplash.com/photo-1644955770652-2afd6c313722?fm=jpg&q=92&w=5200"
curl -sSfL -o mount_a.jpg  "https://images.unsplash.com/photo-1691539706978-3cb89d88915f?fm=jpg&q=92&w=5200"
curl -sSfL -o forest_a.jpg "https://images.unsplash.com/photo-1757412741742-288712226fde?fm=jpg&q=92&w=5200"
curl -sSfL -o aurora_a.jpg "https://images.unsplash.com/photo-1759675739458-6e5a4a60a117?fm=jpg&q=92&w=5200"
curl -sSfL -o volc_b.jpg   "https://images.unsplash.com/photo-1761133135231-2f2fe70907e7?fm=jpg&q=92&w=5200"
# v4 places
curl -sSfL -o weic2216a_big.jpg "https://cdn.esawebb.org/archives/images/publicationjpg/weic2216a.jpg"
while read -r n id; do
  curl -sSfL -o "$n.jpg" "https://images.unsplash.com/photo-$id?fm=jpg&q=92&w=5200"
done <<'LIST'
desert_a 1781978604675-9e955e007ee5
desert_b 1763793931147-ef1a57367c4a
canyon_a 1790309344212-64a49efa7ce1
city_a 1559094522-79422598840f
city_b 1664353655151-9d94a9170eb0
icecave_a 1701143917332-4639dbfeaa29
ruins_a 1697663582045-3a7eadcb5a9a
fall_a 1520637102912-2df6bb2aec6d
mount_b 1719425621664-1b891c114f6d
aurora_b 1531366936337-7c912a4589a7
forest_b 1759172724716-9a034e456bf3
ocean_a 1760627529541-b7f2a79fa283
LIST
ls -la
