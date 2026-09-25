// ENDLESS DESTINY — world layout, story text and quality presets.
// Units are metres. +Y is up and north is -Z. The river lies to the west
// and the north; the one golden star hangs over it to the north-west.

export const WATER_Y = 0;
export const PLATEAU = 26;           // height of the canyon rims and the platform
export const BRIDGE_X = 10;          // the bridge runs north along this line
export const RIM_SOUTH_Z = -140;     // cliff edge where the first plank appears
export const RIM_NORTH_Z = -230;     // far side of the canyon
export const PLATFORM = { x: 10, z: -290, radius: 11, steps: 7, rise: 0.22, tread: 0.8 };

// Walkable route, start shore -> the dark -> canyon -> platform -> road -> river again.
export const PATH = [
  [-16, 2],        // 0  start: sitting beside the river
  [-10, -6],
  [0, -22],
  [8, -44],        //    the dark begins
  [4, -66],
  [12, -90],
  [8, -114],
  [10, -130],
  [BRIDGE_X, RIM_SOUTH_Z],   // 8  cliff edge
  [BRIDGE_X, RIM_NORTH_Z],   // 9  far rim
  [10, -262],
  [PLATFORM.x, PLATFORM.z],  // 11 the platform and the leaf cauldron
  [4, -314],
  [-8, -338],
  [-20, -362],
  [-30, -384],
  [-37, -398],     // 16 back at the river
];

// Cumulative arc length at each path point.
export const PATH_S = (() => {
  const s = [0];
  for (let i = 1; i < PATH.length; i++) {
    const dx = PATH[i][0] - PATH[i - 1][0];
    const dz = PATH[i][1] - PATH[i - 1][1];
    s.push(s[i - 1] + Math.hypot(dx, dz));
  }
  return s;
})();

export const S_RIM_SOUTH = PATH_S[8];
export const S_RIM_NORTH = PATH_S[9];
export const S_PLATFORM = PATH_S[11];
export const S_END = PATH_S[PATH_S.length - 1];

export const START = { x: PATH[0][0], z: PATH[0][1] };
export const END = { x: PATH[16][0], z: PATH[16][1] };

// The golden star: north-west, 24 degrees above the horizon.
export const STAR_DIR = (() => {
  const az = (-35 * Math.PI) / 180;           // 35 degrees west of north
  const el = (24 * Math.PI) / 180;
  const x = Math.sin(az) * Math.cos(el);
  const z = -Math.cos(az) * Math.cos(el);
  return [x, Math.sin(el), z];
})();

// Yaw (radians, 0 = facing -Z) that looks toward the star across the water.
export const STAR_YAW = Math.atan2(-STAR_DIR[0], -STAR_DIR[2]);

// Coastline polygon (clockwise, x/z). Inside is land.
export const COAST = [
  [-24, 120], [-21, 30], [-21.5, -20], [-26, -80], [-24, -150], [-26, -240],
  [-30, -320], [-40, -372], [-47, -392], [-34, -420], [30, -432], [140, -444],
  [320, -444], [320, 120],
];

// Echoes: one for each word in the chain the song walks through.
// Questions come from the studio's own announcement — never lyrics.
export const ECHOES = [
  { id: 'sit', word: 'Sit', pos: [-11, 5.5],
    lines: ['Would you sit?', 'And if you sat down next to something that never stops — would you be giving up?', 'And if it isn’t giving up… then what is it?'] },
  { id: 'listen', word: 'Listen', pos: [-21, -9],
    lines: ['What still sings to you?', 'Is it something you lost?', 'Or something that never left — you just stopped being quiet enough to hear it?'] },
  { id: 'dark', word: 'Dark', pos: [7.5, -67],
    lines: ['Why does it only sing when the space is empty?', 'And what does that say about all the noise we fill our lives with —', 'so we never have to hear it?'] },
  { id: 'bridge', word: 'Bridge', pos: [6, -134],
    lines: ['Does the bridge show up when you’re ready?', 'Or is “ready” just the word we use afterwards —', 'for the moment we stepped anyway?'] },
  { id: 'side', word: 'Side', pos: [30, -250.5],
    lines: ['So did you fail?', 'Or did you finally arrive at the only place worth arriving —', 'the place where you stop needing to know?'] },
  { id: 'light', word: 'Light', pos: [10, -279.5],
    lines: ['What’s pulling you right now?', 'And are you brave enough to stop steering', 'long enough to find out?'] },
  { id: 'step', word: 'Step', pos: [7.3, -315.5],
    lines: ['When did you stop stepping?', 'When did you decide you needed to see the whole road before you’d take one more?', 'And who told you that was wisdom and not fear?'] },
  { id: 'road', word: 'Road', pos: [-22.3, -358.3],
    lines: ['If your part was already written —', 'what would change about how you played it tomorrow?'] },
  { id: 'river', word: 'River', pos: [-44, -382],
    lines: ['If it never ends —', 'is that the curse?', 'Or is that the gift?'] },
];

// Story beats. Spoken-style lines from the Endless Destiny announcement and film scripts.
export const LINES = {
  openFirst: 'Somebody sat down beside something that doesn’t stop.',
  openLoop: 'You sat down beside something that doesn’t stop.',
  rise: 'Sit, and you start to listen.',
  listenHint: 'Listen, and you hear something that should have gone quiet by now.',
  flame: 'And a flame, gathered from one golden star.',
  dark: 'Dark, and you keep walking.',
  rim: 'Walk far enough into the dark, and there’s a bridge.',
  midBridge: 'Are you crossing it? Or are you it?',
  otherSide: 'And on the other side: it’s still unknown.',
  pull: 'Bridge, and there’s a light. Not one you chase. One that pulls.',
  letItBeLit: 'Let the flame be lit.',
  step: 'Light, and you take a step.',
  road: 'Step, and it’s a road. Road, and it runs down to water.',
  back: 'And you’re back at the river. Same river. It never stopped.',
  never: 'And it never needed to.',
  closing: 'So sit down beside something that doesn’t stop.',
};

export const QUALITY = {
  high:   { label: 'High',     terrain: 1.0,  pixelRatio: 1.5, shadows: 1024, props: 1.0,  bloomScale: 0.5 },
  medium: { label: 'Balanced', terrain: 0.75, pixelRatio: 1.0, shadows: 512,  props: 0.75, bloomScale: 0.5 },
  low:    { label: 'Light',    terrain: 0.5,  pixelRatio: 0.85, shadows: 0,   props: 0.45, bloomScale: 0.35 },
};
