/* =====================================================================
   ECHOES IN THE DARK — TikTok site config
   ---------------------------------------------------------------------
   THIS IS THE ONLY FILE YOU NEED TO TOUCH.

   1. PROFILE  -> put your @handle, your name, your bio, your numbers.
                  Drop your profile picture at  assets/profile.jpg
                  (or set `avatar` to any image URL).
   2. CATEGORIES -> rename / add / delete categories. Each video below
                  points at a category by its `id`.
   3. VIDEOS   -> one entry per TikTok. Paste the video link from the
                  TikTok share button. The site auto-fetches the cover
                  image and plays the video in a popup when clicked.
                  Give every video a proper `title` (the "name").
   ===================================================================== */

window.SITE = {
  profile: {
    handle: "yourhandle",            // <-- your TikTok @ WITHOUT the @
    name: "Brandon Molina",
    studio: "Echoes in the Dark",
    tagline: "Music. Visuals. Cosmic destiny stories.",
    bio: "Founder of Echoes in the Dark — a creative studio making cinematic music, ultra-real cosmic visuals and stories about destiny. New drops every week.",
    avatar: "assets/profile.jpg",    // put your profile pic here
    logo: "assets/logo.png",         // studio logo (falls back to built-in mark if missing)
    location: "Lismore, NSW, Australia",
    stats: {
      followers: 0,                  // <-- update these from your TikTok profile
      likes: 0,
      videos: 0                      // 0 = count the list below automatically
    },
    links: {
      tiktok: "",                    // leave blank = built from handle
      instagram: "",
      youtube: "",
      spotify: "",
      email: "brandonmolin106@gmail.com"
    }
  },

  categories: [
    { id: "music",   name: "Music Drops",      emoji: "🎧", color: "#8b5cf6", blurb: "Beats, hooks and full tracks straight out of the studio." },
    { id: "cosmic",  name: "Cosmic Visuals",   emoji: "🌌", color: "#06b6d4", blurb: "Ultra-realistic AI cinematics. Space, light, destiny." },
    { id: "stories", name: "Destiny Stories",  emoji: "📖", color: "#f59e0b", blurb: "Short cosmic tales about fate, echoes and the dark." },
    { id: "bts",     name: "Behind the Scenes", emoji: "🎬", color: "#ec4899", blurb: "How the studio actually gets built, day by day." },
    { id: "trends",  name: "Trends & Fun",     emoji: "🔥", color: "#22c55e", blurb: "Sounds, challenges and whatever's blowing up this week." }
  ],

  /* ------------------------------------------------------------------
     VIDEOS
     url      : full TikTok link, e.g. https://www.tiktok.com/@you/video/7301234567890123456
     title    : the name shown under the video
     category : one of the category ids above
     tags     : optional, used by the search bar
     date     : optional, YYYY-MM-DD, used by "Newest" sorting
     pinned   : optional, true = shows a PINNED badge and sorts first
     demo     : DELETE these demo entries once you add your real ones.
  ------------------------------------------------------------------ */
  videos: [
    { demo: true, url: "", title: "Midnight Echo — full track preview",   category: "music",   tags: ["beat","preview"],        date: "2026-09-28", pinned: true },
    { demo: true, url: "", title: "Birth of a star, rendered in 4K",      category: "cosmic",  tags: ["ai","space","cinematic"], date: "2026-09-25" },
    { demo: true, url: "", title: "The night the sky answered back",      category: "stories", tags: ["destiny","short story"],  date: "2026-09-22" },
    { demo: true, url: "", title: "Building the studio from zero",        category: "bts",     tags: ["studio","grind"],         date: "2026-09-20" },
    { demo: true, url: "", title: "Cloning my own voice for the chorus",  category: "music",   tags: ["voice clone","vocals"],   date: "2026-09-18" },
    { demo: true, url: "", title: "Nebula flythrough — prompt breakdown", category: "cosmic",  tags: ["prompt","tutorial"],      date: "2026-09-15" },
    { demo: true, url: "", title: "Echoes pt. 1 — the signal",            category: "stories", tags: ["series","echoes"],        date: "2026-09-12" },
    { demo: true, url: "", title: "That trending sound but cosmic",       category: "trends",  tags: ["trend","remix"],          date: "2026-09-10" },
    { demo: true, url: "", title: "Studio desk setup tour",               category: "bts",     tags: ["setup","gear"],           date: "2026-09-08" },
    { demo: true, url: "", title: "Dark ambient loop — rain + synths",    category: "music",   tags: ["ambient","loop"],         date: "2026-09-05" }
  ]
};
