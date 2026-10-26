# 🌲 Reveal the Hidden Forest — 3D Educational Expedition

An interactive, realistic, and spacious 3D Forest Exploration Web World. Students explore an ancient woodland sanctuary to discover native wildlife species and uncover concealed ecological threats.

---

## 🚀 How to Run on Hostinger (.php / static)

1. Log into your **Hostinger hPanel**.
2. Go to **File Manager** -> Open `public_html`.
3. Upload the contents of this folder (`d:\tecplore`):
   - `index.php` (or `index.html`)
   - `css/`
   - `js/`
   - `assets/`
4. Visit your domain (e.g. `https://yourdomain.com/` or `https://yourdomain.com/forest/`).
5. The 3D world loads immediately in any modern browser on desktop or mobile!

---

## 💻 How to Test Locally on your Computer

You can test this locally in two simple ways:

### Option 1: Double Click
Double click [index.html](file:///d:/tecplore/index.html) to open directly in Google Chrome, Microsoft Edge, or Firefox.

### Option 2: Local Test Server
Open PowerShell or Command Prompt in this folder and run:
```bash
node server.js
```
Then visit: `http://localhost:3000` in your web browser.

---

## 🌲 3D Models Overview (10 Real GLB Models)

All 5 Species and 5 Threats are real, life-size 3D mesh models with PBR textures, embedded directly to ensure zero CORS errors whether running locally via `file://` or hosted on Hostinger:

### 🦌 5 Wildlife Species:
1. **Spotted Deer (Chital)**: Full anatomical 1MB PBR deer model (`assets/models/realistic_deer.glb`).
2. **Royal Bengal Tiger**: Muscular feline predator model with tiger stripes, amber eyes, and paw pads (`assets/models/tiger.glb`).
3. **Indian Peacock**: Iridescent cobalt plumage, slender S-neck, crown fan crest, and cascading emerald-gold ocelli train (`assets/models/peacock.glb`).
4. **Indian Wild Boar**: Stocky forest boar with bristly dorsal ridge and upward curved ivory tusks (`assets/models/boar.glb`).
5. **Indian Giant Flying Squirrel**: Arboreal gliding mammal with wide patagium flaps, big nocturnal eyes, and bushy tail high in the elder oak canopy (`assets/models/squirrel.glb`).

### ⚠️ 5 Ecological Threats:
1. **Forest Fire**: Stone ring campfire hazard with charred logs and glowing orange embers (`assets/models/forest_fire.glb`).
2. **Wire Snare**: High-tensile poacher wire snare loop anchored to a bent sapling (`assets/models/wire_snare.glb`).
3. **Plastic Trash**: Discarded tourist trash pile with crushed aluminum cans and plastic bottles (`assets/models/plastic_trash.glb`).
4. **Illegal Logging**: Ancient hardwood stump with annual rings and an iron woodcutter axe embedded in timber (`assets/models/illegal_logging.glb`).
5. **Chemical Waste**: Corroded biohazard steel drum leaking a toxic green puddle (`assets/models/chemical_waste.glb`).

---

## 🎮 Controls

### Desktop:
- **W / A / S / D** or **Arrow Keys**: Walk through the forest
- **Shift**: Sprint / Run
- **Mouse**: Look around (Click canvas to lock cursor, Esc to unlock)
- **E**: Inspect / Scan nearby species or threat
- **T**: Quick-launch **Royal Bengal Tiger AR Experience**
- **B**: Toggle 12x50 Binoculars zoom
- **J**: Open Field Expedition Journal & Checklist
- **R**: Reset orientation forward

### Mobile / Smartphone (QR Code Scanner):
- **📱🐅 AR Tiger Button**: One-tap to open the Augmented Reality viewer
- **Left Virtual Touch Joystick**: Move & walk
- **Right Screen Drag**: Rotate camera & look around
- **🔍 Action Button**: Tap to inspect spotted wildlife or threats
- **Binoculars Button**: Zoom into the distance

---

## 📱 Google ARCore — View Bengal Tiger & Forest in Your Physical Space

You can now view the **Royal Bengal Tiger** directly on your floor in Augmented Reality (AR) using **Google ARCore** and **WebXR**:

1. **How to Launch AR**:
   - **From HUD**: Click or tap the **`[ 📱🐅 AR Tiger ]`** button on the bottom bar (or press **T** on desktop).
   - **From Field Journal**: Inspect the Tiger in the forest and click **"View Royal Bengal Tiger in AR"**.
   - **From Checklist**: Tap the **`📱 AR`** pill next to the Bengal Tiger in the Journal checklist.
2. **Key AR Features**:
   - **1:1 Life-Size Scale**: True-to-life ~2.9-meter adult Bengal Tiger anchored to your room's floor.
   - **🌲 Forest Trees Toggle (`ON / OFF`)**: Easily switch between full forest canopy framing and an open clearing mode with no trees blocking your view.
   - **📐 Scale Toggle (`1:1 Life Size / Tabletop`)**: Switch between floor-sized life scale and a miniature desk-sized model.
   - **Contact Shadows & Room Lighting**: ARCore calculates real room lighting and casts realistic shadows under the tiger's paws.
   - **Desktop-to-Mobile Handover**: If testing on a PC/Mac, a dynamic QR code appears—simply scan it with your smartphone or tablet camera to open the tiger in AR immediately!


---

## 📝 How to Add or Customize Species & Threats

Open [js/content-data.js](file:///d:/tecplore/js/content-data.js). You will find the `FOREST_DATA` object:

### To add a new species:
```javascript
{
  id: "tiger",
  name: "Royal Bengal Tiger",
  scientificName: "Panthera tigris",
  type: "species",
  icon: "🐅",
  rarity: "Apex Predator",
  badge: "Endangered Keystone",
  position: { x: 45, z: -50 },
  description: "Description of the tiger...",
  ecologicalRole: "Maintains balanced herbivore populations.",
  conservationStatus: "Endangered (IUCN)",
  discoveryClue: "Hidden near the deep bamboo thickets."
}
```

### To add a new ecological threat:
```javascript
{
  id: "toxic_waste",
  name: "Chemical Waste Barrel",
  type: "threat",
  severity: "TOXIC HAZARD",
  icon: "☣️",
  position: { x: -25, z: 40 },
  description: "Corroded barrel leaking industrial effluent into the stream.",
  impact: "Poisons water supply for all forest wildlife.",
  remedy: "Hazardous containment team dispatch and soil neutralization.",
  discoveryClue: "Found near the discolored stream bank."
}
```
