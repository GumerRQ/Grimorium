// Optional import tool: node tools/prepare_tower_assets.cjs (requires sharp).
// The game only needs pygame and the exported PNGs, never this build dependency.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');

const root = path.resolve(__dirname, '..');
const destination = path.join(root, 'assets/images/backgrounds/tower');
const definitions = [
  ['ground_moss', 64, 64, 8],
  ['tree_oak', 56, 56, 12],
  ['tree_pine', 48, 48, 12],
  ['tree_birch', 44, 44, 12],
  ['rock_large', 24, 20, 8],
  ['rock_small', 18, 16, 8],
  ['cloud_wide', 112, 56, 8],
  ['cloud_round', 80, 60, 8],
];

async function exportSprite(name, width, height, colours) {
  const input = path.join(destination, 'source', name + '.png');
  const { data, info } = await sharp(input).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left = info.width, top = info.height, right = -1, bottom = -1, transparent = 0;
  for (let y = 0; y < info.height; y++) {
    for (let x = 0; x < info.width; x++) {
      const alpha = data[(y * info.width + x) * 4 + 3];
      if (alpha < 64) transparent++;
      else {
        left = Math.min(left, x); top = Math.min(top, y);
        right = Math.max(right, x); bottom = Math.max(bottom, y);
      }
    }
  }
  let image = sharp(input);
  if (name !== 'ground_moss') {
    if (!transparent || right < left) throw new Error(name + ': expected a visible sprite with real alpha');
    image = image.extract({ left, top, width: right - left + 1, height: bottom - top + 1 })
      .resize(width - 2, height - 2, { fit: 'contain', kernel: 'nearest', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .extend({ top: 1, bottom: 1, left: 1, right: 1, background: { r: 0, g: 0, b: 0, alpha: 0 } });
  } else {
    image = image.removeAlpha().resize(width, height, { fit: 'fill', kernel: 'nearest' });
  }
  const resized = await image.ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  // Pixel sprites use a clean binary silhouette; discard residual soft alpha
  // from the generated source before palette reduction (no faint square halo).
  for (let offset = 0; offset < resized.data.length; offset += 4) {
    resized.data[offset + 3] = resized.data[offset + 3] < 128 ? 0 : 255;
    if (resized.data[offset + 3] === 0) resized.data.fill(0, offset, offset + 3);
  }
  await sharp(resized.data, { raw: { width: resized.info.width, height: resized.info.height, channels: 4 } })
    .png({ palette: true, colours, dither: 0 }).toFile(path.join(destination, name + '.png'));
  return { name, width, height, colours };
}

async function exportHud() {
  // Remove only the connected exterior grey, preserving the enclosed panels.
  // The original combat_screen.png and its Krita document are left untouched.
  const { data, info } = await sharp(path.join(root, 'assets/images/combat_screen.png'))
    .ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const size = info.width * info.height;
  const seen = new Uint8Array(size), queue = new Int32Array(size);
  const grey = [...data.subarray(0, 3)];
  let head = 0, tail = 1;
  seen[0] = 1;
  function enqueue(index) {
    if (seen[index]) return;
    seen[index] = 1;
    const offset = index * 4;
    if (grey.every((channel, i) => data[offset + i] === channel)) queue[tail++] = index;
  }
  while (head < tail) {
    const index = queue[head++], x = index % info.width, y = Math.floor(index / info.width);
    data[index * 4 + 3] = 0;
    if (x > 0) enqueue(index - 1);
    if (x + 1 < info.width) enqueue(index + 1);
    if (y > 0) enqueue(index - info.width);
    if (y + 1 < info.height) enqueue(index + info.width);
  }
  // Translucent backing keeps the existing stats readable over trees and clouds.
  for (const [left, top, width, height] of [[20, 83, 61, 134], [20, 43, 61, 25]]) {
    for (let y = top; y < top + height; y++) {
      for (let x = left; x < left + width; x++) {
        const offset = (y * info.width + x) * 4;
        if (data[offset + 3] === 0) {
          data[offset] = 18; data[offset + 1] = 25; data[offset + 2] = 29; data[offset + 3] = 180;
        }
      }
    }
  }
  await sharp(data, { raw: { width: info.width, height: info.height, channels: 4 } })
    .png().toFile(path.join(destination, 'combat_hud.png'));
}

async function exportOverview() {
  const layers = [];
  const manifest = {};
  for (const [index, [name, width, height]] of definitions.entries()) {
    const col = index % 4, row = Math.floor(index / 4);
    const tile = await sharp(path.join(destination, name + '.png'))
      .resize(160, 130, { fit: 'inside', kernel: 'nearest' }).png().toBuffer({ resolveWithObject: true });
    layers.push({ input: tile.data, left: col * 192 + Math.floor((192 - tile.info.width) / 2), top: row * 184 + 12 + Math.floor((130 - tile.info.height) / 2) });
    const label = Buffer.from(`<svg width="192" height="40"><text x="96" y="16" text-anchor="middle" fill="#e0e7dc" font-family="monospace" font-size="13">${name}</text><text x="96" y="33" text-anchor="middle" fill="#a2b3ad" font-family="monospace" font-size="11">${width} x ${height} px</text></svg>`);
    layers.push({ input: label, left: col * 192, top: row * 184 + 142 });
    manifest[name] = { file: name + '.png', width, height, source: 'source/' + name + '.png' };
  }
  await sharp({ create: { width: 768, height: 368, channels: 4, background: '#1e2529' } })
    .composite(layers).png().toFile(path.join(destination, 'preview.png'));
  await fs.writeFile(path.join(destination, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
}

(async () => {
  await fs.mkdir(destination, { recursive: true });
  for (const args of definitions) console.log(await exportSprite(...args));
  if (!process.argv.includes('--sprites-only')) await exportHud();
  await exportOverview();
})().catch(error => { console.error(error); process.exitCode = 1; });
