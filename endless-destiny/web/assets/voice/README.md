# Narrator recordings

Every line in the game is spoken by the browser's text-to-speech. Real recordings replace it line by
line: the same deep, warm, slow voice as the films ("every sentence falls at the end").

1. Record a line and save it here as an `.mp3` (for example `open.mp3`).
2. Add it to `manifest.json`, mapping the line's id to the file name:

```json
{
  "open": "open.mp3",
  "flame": "flame.mp3"
}
```

Any line without a recording keeps the text-to-speech.

## Line ids

| id | Line |
| --- | --- |
| `open` | Somebody sat down beside something that doesn't stop. |
| `open-loop` | You sat down beside something that doesn't stop. (second journey onward) |
| `rise` | Sit, and you start to listen. |
| `flame` | And a flame, gathered from one golden star. |
| `dark` | Dark, and you keep walking. |
| `rim` | Walk far enough into the dark, and there's a bridge. |
| `mid-bridge` | Are you crossing it? Or are you it? |
| `other-side` | And on the other side: it's still unknown. |
| `pull` | Bridge, and there's a light. Not one you chase. One that pulls. |
| `let-it-be-lit` | Let the flame be lit. |
| `step` | Light, and you take a step. |
| `road` | Step, and it's a road. Road, and it runs down to water. |
| `back` | And you're back at the river. Same river. It never stopped. |
| `never` | And it never needed to. |
| `ident` | Endless Destiny. From Echoes in the Dark Studio. |
| `closing` | So sit down beside something that doesn't stop. |

Echo questions use `echo-<word>-<n>`, where `<n>` is the line number within that echo, starting at 1.
For example, the three lines of the Sit echo are `echo-sit-1`, `echo-sit-2` and `echo-sit-3`.
The words are sit, listen, dark, bridge, side, light, step, road and river. The lines are in `src/config.js`.
