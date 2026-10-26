const fs = require('fs');
const path = require('path');
const modelsDir = 'd:/tecplore/assets/models';

const threats = ['chemical_waste', 'forest_fire', 'illegal_logging', 'plastic_trash', 'wire_snare'];
const obj = {};

threats.forEach(t => {
  const p = path.join(modelsDir, t + '.glb');
  if (fs.existsSync(p)) {
    obj[t] = fs.readFileSync(p).toString('base64');
    console.log('Bundled ' + t + '.glb, size: ' + obj[t].length);
  }
});

const out = 'const THREATS_MODELS_BASE64 = ' + JSON.stringify(obj, null, 2) + ';\n';
fs.writeFileSync('d:/tecplore/js/threats-model-data.js', out);
console.log('Saved d:/tecplore/js/threats-model-data.js successfully');
