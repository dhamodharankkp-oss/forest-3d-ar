const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const distDir = path.join(rootDir, 'dist');

if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

console.log('Building standalone single-file HTML...');

// Read base files
let html = fs.readFileSync(path.join(rootDir, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(rootDir, 'css', 'style.css'), 'utf8');
const threeJs = fs.readFileSync(path.join(rootDir, 'js', 'vendor', 'three.min.js'), 'utf8');
const gltfLoader = fs.readFileSync(path.join(rootDir, 'js', 'vendor', 'GLTFLoader.js'), 'utf8');
let contentData = fs.readFileSync(path.join(rootDir, 'js', 'content-data.js'), 'utf8');
const deerModelData = fs.readFileSync(path.join(rootDir, 'js', 'deer-model-data.js'), 'utf8');
const speciesModelData = fs.readFileSync(path.join(rootDir, 'js', 'species-model-data.js'), 'utf8');
const threatsModelData = fs.readFileSync(path.join(rootDir, 'js', 'threats-model-data.js'), 'utf8');
const forestEngine = fs.readFileSync(path.join(rootDir, 'js', 'forest-engine.js'), 'utf8');

// Base64 encode deer_sample.jpg so image is 100% embedded
const deerImgPath = path.join(rootDir, 'assets', 'deer_sample.jpg');
if (fs.existsSync(deerImgPath)) {
  const deerImgB64 = fs.readFileSync(deerImgPath).toString('base64');
  contentData = contentData.replace(
    'image: "assets/deer_sample.jpg"',
    `image: "data:image/jpeg;base64,${deerImgB64}"`
  );
  console.log('✓ Embedded deer_sample.jpg as base64');
}

// 1. In-line CSS into <style>
html = html.replace(
  '<link rel="stylesheet" href="css/style.css">',
  `<style>\n${css}\n</style>`
);

// 2. Remove external script tags and inline everything into single file
const scriptsRegex = /<!-- Scripts -->[\s\S]*?<\/body>/;

const combinedScripts = `<!-- Inlined Standalone Scripts (100% Zero-Dependency & Offline) -->
  <script>
${threeJs}
  </script>
  <script>
${gltfLoader}
  </script>
  <script>
${contentData}
  </script>
  <script>
${deerModelData}
  </script>
  <script>
${speciesModelData}
  </script>
  <script>
${threatsModelData}
  </script>
  <script>
${forestEngine}
  </script>
</body>`;

html = html.replace(scriptsRegex, combinedScripts);

// Save single-file HTML in dist
const singleFilePath = path.join(distDir, 'reveal_hidden_forest_standalone.html');
fs.writeFileSync(singleFilePath, html, 'utf8');
const singleFileSizeMB = (fs.statSync(singleFilePath).size / (1024 * 1024)).toFixed(2);
console.log(`✓ Created single-file HTML: ${singleFilePath} (${singleFileSizeMB} MB)`);

// Also save it at the project root as easy-access option: 'reveal_hidden_forest.html'
const rootSingleFilePath = path.join(rootDir, 'reveal_hidden_forest.html');
fs.writeFileSync(rootSingleFilePath, html, 'utf8');
console.log(`✓ Created root easy-access file: ${rootSingleFilePath}`);

// Create a friendly launcher batch file for colleagues
const launcherBat = `@echo off
title Reveal the Hidden Forest - 3D Expedition
echo ========================================================
echo   Launching Reveal the Hidden Forest 3D Expedition...
echo ========================================================
echo.
echo Opening in your default web browser...
start "" "%~dp0reveal_hidden_forest.html"
exit
`;
fs.writeFileSync(path.join(rootDir, 'DOUBLE_CLICK_TO_PLAY.bat'), launcherBat, 'utf8');
console.log('✓ Created DOUBLE_CLICK_TO_PLAY.bat');

// Create a README for colleagues
const readme = `========================================================================
  REVEAL THE HIDDEN FOREST — 3D ECOLOGICAL FIELD EXPEDITION
========================================================================

HOW TO OPEN & PLAY:
-------------------
OPTION 1 (Easiest - Single File):
  Simply double-click "reveal_hidden_forest.html".
  It will immediately launch in your default web browser (Chrome, Edge,
  Firefox, Safari, Brave, etc.). No internet or server setup needed!

OPTION 2 (Windows Quick Launcher):
  Double-click "DOUBLE_CLICK_TO_PLAY.bat".

CONTROLS:
---------
  - Movement:        W, A, S, D  or  Arrow Keys (▲ ▼ ◄ ►)
  - Look Around:     Move Mouse  or  2-Finger Swipe on Trackpad
  - Inspect Object:  Click directly on any Animal / Threat  or  Press E
  - Binoculars:      Press B  or  click Binoculars button in HUD
  - Field Journal:   Press J  or  click Field Journal button in HUD
  - Reset View:      Press R  or  click "Reset Orientation" top ribbon
  - Mobile:          On-screen virtual joystick + tap to inspect

Enjoy your expedition!
========================================================================
`;
fs.writeFileSync(path.join(rootDir, 'HOW_TO_PLAY_README.txt'), readme, 'utf8');
console.log('✓ Created HOW_TO_PLAY_README.txt');

console.log('\nDistribution build completed successfully!');
