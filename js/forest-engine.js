/**
 * REVEAL THE HIDDEN FOREST - 3D REALISTIC ENGINE (v3.0)
 * High-Fidelity Organic Environment & Direct Raycaster Selection
 */

class ForestWorld {
  constructor() {
    this.container = document.getElementById("canvas-container");
    this.discoveredSpecies = new Set();
    this.discoveredThreats = new Set();
    
    // Player & movement state
    // Spawn 14 units away facing directly North toward the Spotted Deer
    this.player = {
      position: new THREE.Vector3(0, 1.9, 14),
      velocity: new THREE.Vector3(),
      direction: new THREE.Vector3(),
      speed: 15.0,
      sprintMultiplier: 1.8,
      height: 1.9,
      pitch: 0,
      yaw: 0,
      headBobTimer: 0
    };

    this.keys = {
      forward: false,
      backward: false,
      left: false,
      right: false,
      turnLeft: false,
      turnRight: false,
      turnUp: false,
      turnDown: false,
      sprint: false
    };

    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.lastPointer = { x: 0, y: 0 };

    this.mouseCoords = new THREE.Vector2(0, 0);
    this.screenMouse = { x: 0, y: 0 };
    this.raycaster = new THREE.Raycaster();
    this.raycaster.far = 150;

    this.isPointerLocked = false;
    this.isBinocularActive = false;
    this.interactiveObjects = [];
    this.raycastHitList = [];
    this.nearbyTarget = null;
    this.hoveredObject = null;
    this.animatedCreatures = [];
    
    this.clock = new THREE.Clock();

    this.initThree();
    this.initRealisticTextures();
    this.buildTerrain();
    this.buildRealisticForestCanopy();
    this.buildAtmosphericEffects();
    this.spawnAllEntities();
    this.initAudioEngine();
    this.setupEvents();
    this.updateHUDTrackers();

    // Start loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  // -------------------------------------------------------------
  // THREE.JS CORE SETUP
  // -------------------------------------------------------------
  initThree() {
    this.scene = new THREE.Scene();
    // Gentle distant horizon fog: 0 to 120 meters is 100% crystal clear and sharp!
    this.scene.fog = new THREE.Fog(0xd8efff, 130, 460);

    this.camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      600
    );
    this.camera.position.copy(this.player.position);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.02; // Balanced, natural, glare-free exposure
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // Realistic Daytime Sky Dome with Cloudscapes & Horizon Glow
    this.buildDaySkyEnvironment();

    // Natural Daytime Skylight
    this.hemiLight = new THREE.HemisphereLight(0xe0f2fe, 0x2e4222, 1.0);
    this.scene.add(this.hemiLight);

    // Clean, Crisp Daytime Sunlight
    this.sunLight = new THREE.DirectionalLight(0xfffef7, 2.2);
    this.sunLight.position.set(75, 125, -45);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 10;
    this.sunLight.shadow.camera.far = 320;
    const shadowDist = 95;
    this.sunLight.shadow.camera.left = -shadowDist;
    this.sunLight.shadow.camera.right = shadowDist;
    this.sunLight.shadow.camera.top = shadowDist;
    this.sunLight.shadow.camera.bottom = -shadowDist;
    this.sunLight.shadow.bias = -0.0005;
    this.scene.add(this.sunLight);
  }

  // -------------------------------------------------------------
  // REALISTIC DAY SKY ENVIRONMENT (Azure Blue Sky, Clouds & Sun)
  // -------------------------------------------------------------
  buildDaySkyEnvironment() {
    const skyCanvas = document.createElement("canvas");
    skyCanvas.width = 2048;
    skyCanvas.height = 1024;
    const sCtx = skyCanvas.getContext("2d");

    // 1. Natural Day Sky Atmosphere Gradient
    const skyGrad = sCtx.createLinearGradient(0, 0, 0, 1024);
    skyGrad.addColorStop(0.00, "#1565c0"); // Deep Zenith Azure
    skyGrad.addColorStop(0.22, "#1e88e5"); // Rich Sky Blue
    skyGrad.addColorStop(0.48, "#42a5f5"); // Clear Daytime Blue
    skyGrad.addColorStop(0.72, "#90caf9"); // Soft Atmospheric Cyan
    skyGrad.addColorStop(0.88, "#cbe7fc"); // Horizon Daylight Haze
    skyGrad.addColorStop(1.00, "#eef7fe"); // Warm Horizon Light
    sCtx.fillStyle = skyGrad;
    sCtx.fillRect(0, 0, 2048, 1024);

    // 2. Brilliant Daytime Sun Disc & Corona Halo
    const sunX = 1420;
    const sunY = 320;
    const sunGlow = sCtx.createRadialGradient(sunX, sunY, 15, sunX, sunY, 320);
    sunGlow.addColorStop(0.0, "rgba(255, 255, 255, 1.0)");
    sunGlow.addColorStop(0.08, "rgba(255, 250, 220, 0.95)");
    sunGlow.addColorStop(0.25, "rgba(255, 240, 180, 0.45)");
    sunGlow.addColorStop(0.60, "rgba(255, 245, 200, 0.15)");
    sunGlow.addColorStop(1.0, "rgba(255, 255, 255, 0.0)");
    sCtx.fillStyle = sunGlow;
    sCtx.beginPath();
    sCtx.arc(sunX, sunY, 320, 0, Math.PI * 2);
    sCtx.fill();

    // 3. Very Minimal, Faint Wispy Cirrus Clouds (Crisp Open Blue Sky)
    const drawWispyCloud = (startX, startY, width, height) => {
      for (let c = 0; c < 12; c++) {
        const cx = startX + (Math.random() - 0.5) * width;
        const cy = startY + (Math.random() - 0.5) * height;
        const cr = 25 + Math.random() * 45;

        const puffGrad = sCtx.createRadialGradient(cx, cy, 2, cx, cy, cr);
        puffGrad.addColorStop(0.0, "rgba(255, 255, 255, 0.40)");
        puffGrad.addColorStop(0.6, "rgba(240, 248, 255, 0.20)");
        puffGrad.addColorStop(1.0, "rgba(220, 240, 255, 0.0)");

        sCtx.fillStyle = puffGrad;
        sCtx.beginPath();
        sCtx.arc(cx, cy, cr, 0, Math.PI * 2);
        sCtx.fill();
      }
    };

    // Just two faint, delicate wisps in the far distance
    drawWispyCloud(500, 360, 280, 40);
    drawWispyCloud(1650, 380, 260, 35);

    const skyTexture = new THREE.CanvasTexture(skyCanvas);
    const skyGeo = new THREE.SphereGeometry(480, 40, 24);
    const skyMat = new THREE.MeshBasicMaterial({
      map: skyTexture,
      side: THREE.BackSide,
      fog: false // The sky itself stays crisp and clear behind the depth fog
    });

    this.skyMesh = new THREE.Mesh(skyGeo, skyMat);
    this.scene.add(this.skyMesh);
  }

  // -------------------------------------------------------------
  // HIGH-RESOLUTION ORGANIC TEXTURES (Zero CORS risk)
  // -------------------------------------------------------------
  initRealisticTextures() {
    this.textures = {};

    // 1. Organic Forest Floor (Lush moss, rich loam soil, scattered fallen leaves)
    const groundCanvas = document.createElement("canvas");
    groundCanvas.width = 1024;
    groundCanvas.height = 1024;
    const gCtx = groundCanvas.getContext("2d");

    // Base rich woodland loam
    gCtx.fillStyle = "#261a11";
    gCtx.fillRect(0, 0, 1024, 1024);

    // Deep humus variation
    for (let i = 0; i < 4000; i++) {
      const x = Math.random() * 1024;
      const y = Math.random() * 1024;
      const r = 4 + Math.random() * 16;
      gCtx.fillStyle = Math.random() > 0.5 ? "#1c130c" : "#322316";
      gCtx.beginPath();
      gCtx.arc(x, y, r, 0, Math.PI * 2);
      gCtx.fill();
    }

    // Organic Leaf Litter
    const leafTones = ["#4a331c", "#5c4023", "#3d4a22", "#2e3b1a", "#634729", "#38451c"];
    for (let i = 0; i < 12000; i++) {
      const x = Math.random() * 1024;
      const y = Math.random() * 1024;
      const len = 3 + Math.random() * 8;
      const wid = len * 0.55;
      const rot = Math.random() * Math.PI;
      gCtx.fillStyle = leafTones[Math.floor(Math.random() * leafTones.length)];
      gCtx.beginPath();
      gCtx.ellipse(x, y, len, wid, rot, 0, Math.PI * 2);
      gCtx.fill();
    }

    // Lush Emerald Moss Veins
    for (let m = 0; m < 900; m++) {
      const x = Math.random() * 1024;
      const y = Math.random() * 1024;
      const r = 14 + Math.random() * 32;
      const grad = gCtx.createRadialGradient(x, y, 2, x, y, r);
      grad.addColorStop(0, "rgba(46, 92, 38, 0.75)");
      grad.addColorStop(0.6, "rgba(35, 75, 29, 0.45)");
      grad.addColorStop(1, "rgba(35, 75, 29, 0)");
      gCtx.fillStyle = grad;
      gCtx.beginPath();
      gCtx.arc(x, y, r, 0, Math.PI * 2);
      gCtx.fill();
    }

    this.textures.ground = new THREE.CanvasTexture(groundCanvas);
    this.textures.ground.wrapS = THREE.RepeatWrapping;
    this.textures.ground.wrapT = THREE.RepeatWrapping;
    this.textures.ground.repeat.set(36, 36);

    // 2. Realistic Tree Bark Texture
    const barkCanvas = document.createElement("canvas");
    barkCanvas.width = 512;
    barkCanvas.height = 512;
    const bCtx = barkCanvas.getContext("2d");
    bCtx.fillStyle = "#332217";
    bCtx.fillRect(0, 0, 512, 512);

    for (let i = 0; i < 600; i++) {
      bCtx.fillStyle = Math.random() > 0.4 ? "#20150e" : "#443021";
      const x = Math.random() * 512;
      const w = 3 + Math.random() * 10;
      bCtx.fillRect(x, 0, w, 512);
    }
    // Moss stains along bark base
    for (let i = 0; i < 80; i++) {
      bCtx.fillStyle = "rgba(42, 78, 35, 0.4)";
      bCtx.fillRect(Math.random() * 512, Math.random() * 512, 40 + Math.random() * 60, 25 + Math.random() * 35);
    }
    this.textures.bark = new THREE.CanvasTexture(barkCanvas);
    this.textures.bark.wrapS = THREE.RepeatWrapping;
    this.textures.bark.wrapT = THREE.RepeatWrapping;
    this.textures.bark.repeat.set(2, 6);

    // 3. Realistic Botanical Fern Texture (Replaces pyramids!)
    const fernCanvas = document.createElement("canvas");
    fernCanvas.width = 256;
    fernCanvas.height = 512;
    const fCtx = fernCanvas.getContext("2d");
    fCtx.clearRect(0, 0, 256, 512);

    // Central rachis stem
    fCtx.strokeStyle = "#1b4d24";
    fCtx.lineWidth = 6;
    fCtx.beginPath();
    fCtx.moveTo(128, 500);
    fCtx.quadraticCurveTo(128, 250, 138, 20);
    fCtx.stroke();

    // Botanical pinnae leaflets
    for (let y = 460; y > 40; y -= 16) {
      const progress = (500 - y) / 480;
      const leafletLen = Math.sin(progress * Math.PI) * 95 + 15;
      const leafletColor = progress > 0.7 ? "#34a853" : "#247334";
      fCtx.fillStyle = leafletColor;

      // Right leaflet
      fCtx.beginPath();
      fCtx.ellipse(128 + leafletLen * 0.45, y - 8, leafletLen * 0.5, 6, -0.3, 0, Math.PI * 2);
      fCtx.fill();

      // Left leaflet
      fCtx.beginPath();
      fCtx.ellipse(128 - leafletLen * 0.45, y - 8, leafletLen * 0.5, 6, 0.3, 0, Math.PI * 2);
      fCtx.fill();
    }

    this.textures.fern = new THREE.CanvasTexture(fernCanvas);

    // 4. Realistic Leafy Tree Foliage Cluster (Replaces dodecahedrons!)
    const leafClusterCanvas = document.createElement("canvas");
    leafClusterCanvas.width = 512;
    leafClusterCanvas.height = 512;
    const lcCtx = leafClusterCanvas.getContext("2d");
    lcCtx.clearRect(0, 0, 512, 512);

    for (let i = 0; i < 700; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = Math.pow(Math.random(), 0.6) * 220;
      const lx = 256 + Math.cos(angle) * dist;
      const ly = 256 + Math.sin(angle) * dist;
      const lHue = ["#2e6b37", "#3b8046", "#205228", "#499656", "#1c4723"];
      lcCtx.fillStyle = lHue[Math.floor(Math.random() * lHue.length)];
      lcCtx.beginPath();
      lcCtx.ellipse(lx, ly, 10 + Math.random() * 12, 6 + Math.random() * 8, Math.random() * Math.PI, 0, Math.PI * 2);
      lcCtx.fill();
    }
    this.textures.leafCluster = new THREE.CanvasTexture(leafClusterCanvas);
  }

  // -------------------------------------------------------------
  // TERRAIN GENERATION
  // -------------------------------------------------------------
  getTerrainHeight(x, z) {
    const distFromCenter = Math.sqrt(x * x + z * z);
    const clearFlatFactor = Math.min(1.0, Math.max(0.0, (distFromCenter - 14) / 40));

    const h1 = Math.sin(x * 0.02) * Math.cos(z * 0.02) * 4.5;
    const h2 = Math.sin(x * 0.06 + 1.2) * Math.cos(z * 0.05 + 0.8) * 2.0;
    const h3 = Math.cos(x * 0.1) * Math.sin(z * 0.1) * 0.8;
    
    return (h1 + h2 + h3) * clearFlatFactor;
  }

  buildTerrain() {
    const size = 380;
    const segments = 160;
    const geo = new THREE.PlaneGeometry(size, size, segments, segments);
    geo.rotateX(-Math.PI / 2);

    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      pos.setY(i, this.getTerrainHeight(x, z));
    }
    geo.computeVertexNormals();

    const mat = new THREE.MeshStandardMaterial({
      map: this.textures.ground,
      roughness: 0.92,
      metalness: 0.05
    });

    this.terrain = new THREE.Mesh(geo, mat);
    this.terrain.receiveShadow = true;
    this.scene.add(this.terrain);
  }

  // -------------------------------------------------------------
  // REALISTIC BOTANICAL TREES, FERNS & HOLLOW LOGS
  // -------------------------------------------------------------
  buildRealisticForestCanopy() {
    // 1. Organic Branching Trees (No dodecahedrons!)
    const trunkMat = new THREE.MeshStandardMaterial({
      map: this.textures.bark,
      roughness: 0.92
    });

    const leafBranchMat = new THREE.MeshStandardMaterial({
      map: this.textures.leafCluster,
      transparent: true,
      alphaTest: 0.25,
      roughness: 0.75,
      side: THREE.DoubleSide
    });

    const leafCrossGeo = new THREE.PlaneGeometry(9.0, 9.0);

    const treeGroup = new THREE.Group();
    const treeCount = 180;

    for (let i = 0; i < treeCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 12 + Math.sqrt(Math.random()) * 165;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      // Keep viewing clearing open
      if (Math.abs(x) < 8 && Math.abs(z + 18) < 10) continue;
      if (Math.abs(x + 28) < 6 && Math.abs(z + 12) < 6) continue;
      if (Math.abs(x - 42) < 6 && Math.abs(z + 35) < 6) continue;

      const y = this.getTerrainHeight(x, z);
      const scaleH = 0.85 + Math.random() * 0.65;

      const tree = new THREE.Group();
      tree.position.set(x, y, z);
      tree.scale.set(scaleH, scaleH, scaleH);

      // Root flared organic trunk
      const trunkGeo = new THREE.CylinderGeometry(0.55, 1.3, 15, 8);
      trunkGeo.translate(0, 7.5, 0);
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.castShadow = true;
      trunk.receiveShadow = true;
      tree.add(trunk);

      // Layered Organic Leaf Boughs (3 Cross-Planes per tier)
      for (let tier = 0; tier < 4; tier++) {
        const tierY = 10 + tier * 3.2;
        const boughCount = 3;
        for (let b = 0; b < boughCount; b++) {
          const bough = new THREE.Mesh(leafCrossGeo, leafBranchMat);
          bough.position.set(
            (Math.random() - 0.5) * 1.8,
            tierY + (Math.random() - 0.5) * 0.8,
            (Math.random() - 0.5) * 1.8
          );
          bough.rotation.y = (b * Math.PI) / boughCount + (Math.random() - 0.5) * 0.3;
          bough.rotation.x = 0.25 * (b % 2 === 0 ? 1 : -1);
          bough.scale.setScalar(1.0 - tier * 0.16 + Math.random() * 0.2);
          bough.castShadow = true;
          bough.receiveShadow = true;
          tree.add(bough);
        }
      }

      treeGroup.add(tree);
    }
    this.scene.add(treeGroup);

    // 2. Signature Mossy Hollow Fallen Logs (Recreated from user's photo)
    this.spawnFallenHollowLog(4, -12, Math.PI / 4.2, 1.35);
    this.spawnFallenHollowLog(-18, 14, -Math.PI / 5.5, 1.15);
    this.spawnFallenHollowLog(22, -26, Math.PI / 2.8, 1.4);

    // 3. Smooth Mossy Woodland Boulders
    this.spawnRealisticRocks();

    // 4. Botanical Ferns & Wild Woodland Blossom Clusters
    this.spawnRealisticFernsAndCover();
  }

  spawnFallenHollowLog(x, z, rotation, scale = 1.0) {
    const y = this.getTerrainHeight(x, z);
    const logGroup = new THREE.Group();
    logGroup.position.set(x, y + 0.6 * scale, z);
    logGroup.rotation.y = rotation;
    logGroup.scale.setScalar(scale);

    const outerGeo = new THREE.CylinderGeometry(0.85, 0.95, 9, 12, 1, true);
    outerGeo.rotateZ(Math.PI / 2);
    const outerMat = new THREE.MeshStandardMaterial({
      map: this.textures.bark,
      color: 0x483a2d,
      roughness: 0.95,
      side: THREE.DoubleSide
    });
    const logMesh = new THREE.Mesh(outerGeo, outerMat);
    logMesh.castShadow = true;
    logMesh.receiveShadow = true;
    logGroup.add(logMesh);

    const innerGeo = new THREE.CylinderGeometry(0.55, 0.65, 8.8, 10, 1, true);
    innerGeo.rotateZ(Math.PI / 2);
    const innerMat = new THREE.MeshBasicMaterial({ color: 0x0f0b08, side: THREE.BackSide });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    logGroup.add(innerMesh);

    // Moss layer along upper curve
    const mossGeo = new THREE.BoxGeometry(7.6, 0.35, 1.25);
    mossGeo.translate(0, 0.72, 0);
    const mossMat = new THREE.MeshStandardMaterial({ color: 0x3d702d, roughness: 0.98 });
    const mossMesh = new THREE.Mesh(mossGeo, mossMat);
    mossMesh.castShadow = true;
    logGroup.add(mossMesh);

    this.scene.add(logGroup);
  }

  spawnRealisticRocks() {
    // Smooth weathered rocks (high segment sphere deformed naturally)
    const rockMat = new THREE.MeshStandardMaterial({ color: 0x5a6157, roughness: 0.88 });

    // Elevated rock platform for Peacock
    const peacockRock = new THREE.Mesh(new THREE.SphereGeometry(1.6, 16, 12), rockMat);
    const py = this.getTerrainHeight(-28, -12);
    peacockRock.position.set(-28, py + 0.6, -12);
    peacockRock.scale.set(2.4, 0.9, 2.0);
    peacockRock.castShadow = true;
    peacockRock.receiveShadow = true;
    this.scene.add(peacockRock);

    const rockCount = 45;
    for (let i = 0; i < rockCount; i++) {
      const x = (Math.random() - 0.5) * 210;
      const z = (Math.random() - 0.5) * 210;
      const y = this.getTerrainHeight(x, z) + 0.3;

      const rock = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 10), rockMat);
      rock.position.set(x, y, z);
      const sc = 0.6 + Math.random() * 1.3;
      rock.scale.set(sc * 1.3, sc * 0.7, sc);
      rock.rotation.set(Math.random(), Math.random(), Math.random());
      rock.castShadow = true;
      rock.receiveShadow = true;
      this.scene.add(rock);
    }
  }

  // Botanical Ferns (Cross-billboard botanical alpha fronds - NO pyramids!)
  spawnRealisticFernsAndCover() {
    const fernMat = new THREE.MeshStandardMaterial({
      map: this.textures.fern,
      transparent: true,
      alphaTest: 0.25,
      roughness: 0.8,
      side: THREE.DoubleSide
    });

    const fernFrondGeo = new THREE.PlaneGeometry(1.4, 2.4);
    fernFrondGeo.translate(0, 1.2, 0);

    const flowerGeo = new THREE.SphereGeometry(0.18, 6, 6);
    const pinkFlowerMat = new THREE.MeshBasicMaterial({ color: 0xec4899 });

    for (let i = 0; i < 220; i++) {
      const x = (Math.random() - 0.5) * 170;
      const z = (Math.random() - 0.5) * 170;
      const y = this.getTerrainHeight(x, z);

      // Multi-frond fern rosette
      const fernClump = new THREE.Group();
      fernClump.position.set(x, y, z);
      const frondCount = 4;
      for (let f = 0; f < frondCount; f++) {
        const frond = new THREE.Mesh(fernFrondGeo, fernMat);
        frond.rotation.y = (f * Math.PI * 2) / frondCount + (Math.random() - 0.5) * 0.3;
        frond.rotation.x = 0.35 + Math.random() * 0.2;
        frond.scale.setScalar(0.7 + Math.random() * 0.6);
        fernClump.add(frond);
      }
      this.scene.add(fernClump);

      // Wild pink florets
      if (Math.random() > 0.65) {
        for (let fl = 0; fl < 3; fl++) {
          const blossom = new THREE.Mesh(flowerGeo, pinkFlowerMat);
          blossom.position.set(
            x + (Math.random() - 0.5) * 1.2,
            y + 0.35 + Math.random() * 0.2,
            z + (Math.random() - 0.5) * 1.2
          );
          this.scene.add(blossom);
        }
      }
    }
  }

  // -------------------------------------------------------------
  // VOLUMETRIC SUN SHAFTS & GLOWING POLLEN PARTICLES
  // -------------------------------------------------------------
  // -------------------------------------------------------------
  // ATMOSPHERIC EFFECTS (Crystal Clear View - No Blinding Light Beams)
  // -------------------------------------------------------------
  buildAtmosphericEffects() {
    // Blinding volumetric light beam cylinders and particle squares removed!
    // Ensures a 100% crystal clear, vivid, unobstructed view of the 3D environment.
  }

  // -------------------------------------------------------------
  // ENTITY SPAWNING (Real 3D GLB/GLTF Models + Fallbacks)
  // -------------------------------------------------------------
  spawnAllEntities() {
    // 3D GLTF Loader ready
    this.gltfLoader = (typeof THREE.GLTFLoader !== "undefined") ? new THREE.GLTFLoader() : null;

    // 1. Spotted Deer (Embedded Real 3D Model with Zero CORS risk)
    this.spawnReal3DDeer(FOREST_DATA.species.find(s => s.id === "spotted_deer"));

    // 2. Peacock
    this.spawnEntityWithGLBFallback(
      FOREST_DATA.species.find(s => s.id === "peacock"),
      (data) => this.spawnPeacock(data)
    );

    // 3. Royal Bengal Tiger
    this.spawnEntityWithGLBFallback(
      FOREST_DATA.species.find(s => s.id === "tiger"),
      (data) => this.spawnBengalTiger(data)
    );

    // 4. Wild Boar
    this.spawnEntityWithGLBFallback(
      FOREST_DATA.species.find(s => s.id === "wild_boar"),
      (data) => this.spawnWildBoar(data)
    );

    // 5. Flying Squirrel
    this.spawnEntityWithGLBFallback(
      FOREST_DATA.species.find(s => s.id === "flying_squirrel"),
      (data) => this.spawnFlyingSquirrel(data)
    );

    // Threats
    this.spawnEntityWithGLBFallback(
      FOREST_DATA.threats.find(t => t.id === "forest_fire"),
      (data) => this.spawnForestFire(data)
    );

    this.spawnEntityWithGLBFallback(
      FOREST_DATA.threats.find(t => t.id === "wire_snare"),
      (data) => this.spawnWireSnare(data)
    );

    this.spawnEntityWithGLBFallback(
      FOREST_DATA.threats.find(t => t.id === "plastic_trash"),
      (data) => this.spawnPlasticTrash(data)
    );

    this.spawnEntityWithGLBFallback(
      FOREST_DATA.threats.find(t => t.id === "illegal_logging"),
      (data) => this.spawnIllegalLogging(data)
    );

    this.spawnEntityWithGLBFallback(
      FOREST_DATA.threats.find(t => t.id === "chemical_waste"),
      (data) => this.spawnChemicalWaste(data)
    );
  }

  spawnEntityWithGLBFallback(data, fallbackFn) {
    if (!data) return;

    const x = data.position.x;
    const z = data.position.z;
    const groundY = this.getTerrainHeight(x, z);
    const y = (data.position.y !== undefined) ? data.position.y : groundY;

    const setupModel = (gltf) => {
      const model = gltf.scene;

      // Compute raw bounding box to auto-normalize size
      const rawBox = new THREE.Box3().setFromObject(model);
      const rawSize = new THREE.Vector3();
      rawBox.getSize(rawSize);

      let targetHeight = data.targetHeight || 2.2;
      if (data.modelScale && (!data.targetHeight)) {
        targetHeight = 2.0 * data.modelScale;
      }
      if (rawSize.y > 0) {
        const scaleFactor = targetHeight / rawSize.y;
        model.scale.set(scaleFactor, scaleFactor, scaleFactor);
      }

      // Center horizontally and align feet with terrain/given elevation
      const scaledBox = new THREE.Box3().setFromObject(model);
      const scaledCenter = new THREE.Vector3();
      scaledBox.getCenter(scaledCenter);

      model.position.x = x - (scaledCenter.x - model.position.x);
      model.position.z = z - (scaledCenter.z - model.position.z);
      model.position.y = y - scaledBox.min.y;

      // Orientation angles
      if (data.rotationY !== undefined) {
        model.rotation.y = data.rotationY;
      } else {
        if (data.id === "tiger") model.rotation.y = -Math.PI * 0.35;
        else if (data.id === "peacock") model.rotation.y = Math.PI * 0.7;
        else if (data.id === "wild_boar") model.rotation.y = Math.PI * 0.35;
        else if (data.id === "flying_squirrel") model.rotation.y = Math.PI * 0.25;
        else if (data.id === "chemical_waste") model.rotation.y = Math.PI * 0.2;
        else if (data.id === "forest_fire") model.rotation.y = 0;
        else if (data.id === "wire_snare") model.rotation.y = Math.PI * 0.45;
        else if (data.id === "illegal_logging") model.rotation.y = Math.PI * 0.15;
      }

      // Enable shadows and configure PBR materials on all child meshes
      model.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          if (child.material) {
            child.material.needsUpdate = true;
            child.material.roughness = Math.min(child.material.roughness !== undefined ? child.material.roughness : 0.8, 0.9);
            child.material.metalness = Math.max(child.material.metalness !== undefined ? child.material.metalness : 0.05, 0.05);
          }
        }
      });

      // Soft ground contact shadow for grounded entities
      if (data.position.y === undefined || Math.abs(data.position.y - groundY) < 1.0) {
        const shadowGeo = new THREE.CircleGeometry(1.6, 20);
        shadowGeo.rotateX(-Math.PI / 2);
        const shadowMesh = new THREE.Mesh(
          shadowGeo,
          new THREE.MeshBasicMaterial({ color: 0x08130a, transparent: true, opacity: 0.7 })
        );
        shadowMesh.position.set(x, groundY + 0.04, z);
        this.scene.add(shadowMesh);
      }

      // Ambient FX for special hazards
      if (data.id === "forest_fire") {
        const fireLight = new THREE.PointLight(0xff5500, 2.2, 18);
        fireLight.position.set(x, groundY + 0.9, z);
        this.scene.add(fireLight);
      } else if (data.id === "chemical_waste") {
        const toxicLight = new THREE.PointLight(0x10b981, 1.4, 10);
        toxicLight.position.set(x, groundY + 0.6, z);
        this.scene.add(toxicLight);
      }

      // Bounding hitbox for raycasting / click selection
      const hitBoxSize = Math.max(targetHeight * 1.4, 3.2);
      const hitBox = new THREE.Mesh(
        new THREE.BoxGeometry(hitBoxSize, targetHeight * 1.2, hitBoxSize),
        new THREE.MeshBasicMaterial({ visible: false })
      );
      hitBox.position.set(0, targetHeight * 0.5, 0);
      model.add(hitBox);

      this.registerInteractiveObject(model, hitBox, data, 18.0);
      this.scene.add(model);
      console.log(`✓ Real 3D GLB Model loaded for: ${data.name}`);
    };

    // Check if embedded Base64 exists in SPECIES_MODELS_BASE64 or THREATS_MODELS_BASE64
    let b64 = null;
    if (typeof SPECIES_MODELS_BASE64 !== "undefined" && (SPECIES_MODELS_BASE64[data.id] || SPECIES_MODELS_BASE64[data.id.replace("wild_", "").replace("flying_", "")])) {
      b64 = SPECIES_MODELS_BASE64[data.id] || SPECIES_MODELS_BASE64[data.id.replace("wild_", "").replace("flying_", "")];
    } else if (typeof THREATS_MODELS_BASE64 !== "undefined" && THREATS_MODELS_BASE64[data.id]) {
      b64 = THREATS_MODELS_BASE64[data.id];
    }

    if (b64 && this.gltfLoader) {
      try {
        const binaryString = window.atob(b64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        this.gltfLoader.parse(
          bytes.buffer,
          "",
          (gltf) => {
            setupModel(gltf);
          },
          (err) => {
            console.warn(`Could not parse embedded GLB for ${data.name}, trying file load.`, err);
            loadFile();
          }
        );
        return;
      } catch (e) {
        console.warn("Base64 parse exception:", e);
      }
    }

    const loadFile = () => {
      if (this.gltfLoader && data.model) {
        this.gltfLoader.load(
          data.model,
          (gltf) => {
            setupModel(gltf);
          },
          undefined,
          (err) => {
            console.warn(`Could not load GLB file for ${data.name}, using procedural fallback.`, err);
            fallbackFn(data);
          }
        );
      } else {
        fallbackFn(data);
      }
    };

    loadFile();
  }

  // -------------------------------------------------------------
  // 1. REAL 3D SCULPTED DEER MODEL (Zero CORS Risk, In-Memory Parse)
  // -------------------------------------------------------------
  spawnReal3DDeer(data) {
    if (!data) return;
    const x = data.position.x;
    const z = data.position.z;
    const groundY = this.getTerrainHeight(x, z);

    // If base64 embedded model exists, parse directly without network/CORS!
    if (typeof DEER_MODEL_BASE64 !== "undefined" && this.gltfLoader) {
      try {
        const binaryString = window.atob(DEER_MODEL_BASE64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        this.gltfLoader.parse(
          bytes.buffer,
          "",
          (gltf) => {
            const model = gltf.scene;

            // Auto-scale to life-size height (2.3m with antlers)
            const rawBox = new THREE.Box3().setFromObject(model);
            const rawSize = new THREE.Vector3();
            rawBox.getSize(rawSize);

            const targetHeight = data.targetHeight || 2.3;
            if (rawSize.y > 0) {
              const scaleFactor = targetHeight / rawSize.y;
              model.scale.set(scaleFactor, scaleFactor, scaleFactor);
            }

            const scaledBox = new THREE.Box3().setFromObject(model);
            const scaledCenter = new THREE.Vector3();
            scaledBox.getCenter(scaledCenter);

            model.position.x = x - (scaledCenter.x - model.position.x);
            model.position.z = z - (scaledCenter.z - model.position.z);
            model.position.y = groundY - scaledBox.min.y;

            // Face slightly toward the player trail
            model.rotation.y = Math.PI * 0.15;

            // Enable PBR shadows and material settings
            model.traverse((child) => {
              if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.material) {
                  child.material.needsUpdate = true;
                  child.material.roughness = Math.min(child.material.roughness || 0.8, 0.85);
                  child.material.metalness = Math.max(child.material.metalness || 0.05, 0.05);
                }
              }
            });

            // Soft contact shadow
            const shadowGeo = new THREE.CircleGeometry(1.6, 20);
            shadowGeo.rotateX(-Math.PI / 2);
            const shadowMesh = new THREE.Mesh(
              shadowGeo,
              new THREE.MeshBasicMaterial({ color: 0x08130a, transparent: true, opacity: 0.7 })
            );
            shadowMesh.position.set(x, groundY + 0.04, z);
            this.scene.add(shadowMesh);

            // Bounding hitbox for raycasting / click selection
            const hitBox = new THREE.Mesh(
              new THREE.BoxGeometry(3.5, 3.8, 3.5),
              new THREE.MeshBasicMaterial({ visible: false })
            );
            hitBox.position.set(0, targetHeight * 0.5, 0);
            model.add(hitBox);

            this.registerInteractiveObject(model, hitBox, data, 18.0);
            this.scene.add(model);
            console.log("✓ Real 3D Sculpted Deer loaded successfully from embedded GLB!");
          },
          (err) => {
            console.error("Error parsing embedded GLB:", err);
          }
        );
        return;
      } catch (e) {
        console.warn("Base64 parse exception:", e);
      }
    }

    // Secondary fallback: GLTF loader from file
    this.spawnEntityWithGLBFallback(data, (d) => {
      console.log("Using secondary fallback for deer");
    });
  }

  // -------------------------------------------------------------
  // 2. INDIAN PEACOCK
  // -------------------------------------------------------------
  spawnPeacock(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z) + 1.2;
    group.position.set(x, y, z);
    group.rotation.y = Math.PI * 0.7;

    const blueMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.5, roughness: 0.3 });
    const bodyGeo = new THREE.ConeGeometry(0.55, 1.6, 8);
    bodyGeo.rotateZ(Math.PI / 2.4);
    const body = new THREE.Mesh(bodyGeo, blueMat);
    body.position.set(0, 0.7, 0);
    body.castShadow = true;
    group.add(body);

    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.26, 1.1, 8), blueMat);
    neck.position.set(-0.7, 1.25, 0);
    neck.rotation.z = -0.35;
    group.add(neck);

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), blueMat);
    head.position.set(-0.95, 1.75, 0);
    group.add(head);

    const trainMat = new THREE.MeshStandardMaterial({ color: 0x059669, roughness: 0.5, metalness: 0.3, side: THREE.DoubleSide });
    const trainGeo = new THREE.ConeGeometry(1.2, 3.8, 6);
    trainGeo.rotateZ(-Math.PI / 2.2);
    trainGeo.scale(1.0, 0.3, 1.6);
    const train = new THREE.Mesh(trainGeo, trainMat);
    train.position.set(2.0, 0.6, 0);
    train.castShadow = true;
    group.add(train);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(4.0, 3.2, 3.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(0.5, 1.2, 0);
    group.add(hitBox);

    this.registerInteractiveObject(group, hitBox, data, 16.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 3. ROYAL BENGAL TIGER
  // -------------------------------------------------------------
  spawnBengalTiger(data) {
    if (!data) return;
    const tigerGroup = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    tigerGroup.position.set(x, y, z);
    tigerGroup.rotation.y = -Math.PI * 0.4;

    const tigerMat = new THREE.MeshStandardMaterial({ color: 0xd96e24, roughness: 0.7 });
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xfefce8, roughness: 0.8 });

    const torsoGeo = new THREE.CylinderGeometry(0.75, 0.9, 3.2, 12);
    torsoGeo.rotateZ(Math.PI / 2);
    const torso = new THREE.Mesh(torsoGeo, tigerMat);
    torso.position.y = 1.35;
    torso.castShadow = true;
    tigerGroup.add(torso);

    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.65, 1.2, 8), tigerMat);
    neck.position.set(-1.5, 1.6, 0);
    neck.rotation.z = -0.5;
    tigerGroup.add(neck);

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.52, 8, 8), tigerMat);
    head.position.set(-2.2, 1.9, 0);
    tigerGroup.add(head);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(5.0, 3.0, 3.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(-0.5, 1.4, 0);
    tigerGroup.add(hitBox);

    this.registerInteractiveObject(tigerGroup, hitBox, data, 18.0);
    this.scene.add(tigerGroup);
  }

  // -------------------------------------------------------------
  // 4. INDIAN WILD BOAR
  // -------------------------------------------------------------
  spawnWildBoar(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y, z);
    group.rotation.y = Math.PI * 0.35;

    const boarMat = new THREE.MeshStandardMaterial({ color: 0x3b2a20, roughness: 0.95 });
    const bodyGeo = new THREE.CylinderGeometry(0.7, 0.85, 2.2, 10);
    bodyGeo.rotateZ(Math.PI / 2);
    const body = new THREE.Mesh(bodyGeo, boarMat);
    body.position.y = 1.0;
    body.castShadow = true;
    group.add(body);

    const headGeo = new THREE.ConeGeometry(0.55, 1.4, 7);
    headGeo.rotateZ(Math.PI / 2.3);
    const head = new THREE.Mesh(headGeo, boarMat);
    head.position.set(-1.4, 0.9, 0);
    group.add(head);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(3.5, 2.5, 2.5), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(-0.5, 1.0, 0);
    group.add(hitBox);

    this.registerInteractiveObject(group, hitBox, data, 14.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 5. FLYING SQUIRREL
  // -------------------------------------------------------------
  spawnFlyingSquirrel(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = data.position.y || (this.getTerrainHeight(x, z) + 11.5);
    group.position.set(x, y, z);

    const furMat = new THREE.MeshStandardMaterial({ color: 0x854d0e, roughness: 0.8 });
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.45, 8, 8), furMat);
    body.scale.set(1.4, 0.7, 0.9);
    body.position.set(1.4, 0, 0);
    group.add(body);

    const wingPlane = new THREE.PlaneGeometry(1.6, 1.2);
    const wing = new THREE.Mesh(wingPlane, new THREE.MeshStandardMaterial({ color: 0xa16207, side: THREE.DoubleSide }));
    wing.rotation.x = Math.PI / 2;
    wing.position.set(1.4, 0, 0);
    group.add(wing);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(4.0, 4.0, 4.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(1.4, 0, 0);
    group.add(hitBox);

    this.registerInteractiveObject(group, hitBox, data, 24.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 6. THREAT: FOREST FIRE
  // -------------------------------------------------------------
  spawnForestFire(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y, z);

    const fireLight = new THREE.PointLight(0xff4500, 2.5, 16);
    fireLight.position.set(0, 0.8, 0);
    group.add(fireLight);

    const smokePlume = [];
    const smokeGeo = new THREE.DodecahedronGeometry(0.2, 0);
    const smokeMat = new THREE.MeshBasicMaterial({ color: 0x9ca3af, transparent: true, opacity: 0.45 });
    for (let s = 0; s < 30; s++) {
      const sm = new THREE.Mesh(smokeGeo, smokeMat);
      sm.position.set((Math.random() - 0.5) * 0.5, 0.4 + (s * 0.16), (Math.random() - 0.5) * 0.5);
      group.add(sm);
      smokePlume.push(sm);
    }

    this.animatedCreatures.push({
      group: group,
      update: (time) => {
        fireLight.intensity = 2.0 + Math.sin(time * 8.0) * 0.8;
        smokePlume.forEach((sm, idx) => {
          sm.position.y += 0.024;
          if (sm.position.y > 5.5) sm.position.y = 0.4;
        });
      }
    });

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(3.5, 3.5, 3.5), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(0, 1.5, 0);
    group.add(hitBox);

    this.addThreatGlowBeacon(group, 0, 1.0, 0);
    this.registerInteractiveObject(group, hitBox, data, 16.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 7. THREAT: POACHING WIRE SNARE
  // -------------------------------------------------------------
  spawnWireSnare(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y, z);

    const saplingGeo = new THREE.CylinderGeometry(0.06, 0.1, 3.4, 6);
    saplingGeo.translate(0, 1.7, 0);
    const sapling = new THREE.Mesh(saplingGeo, new THREE.MeshStandardMaterial({ color: 0x422a18 }));
    sapling.rotation.z = -0.7;
    group.add(sapling);

    const loopGeo = new THREE.TorusGeometry(0.5, 0.025, 6, 20);
    loopGeo.rotateX(Math.PI / 2);
    const snareLoop = new THREE.Mesh(loopGeo, new THREE.MeshStandardMaterial({ color: 0xd4d4d8, metalness: 0.95 }));
    snareLoop.position.set(1.6, 0.2, 0);
    group.add(snareLoop);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(3.0, 3.0, 3.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(1.2, 1.0, 0);
    group.add(hitBox);

    this.addThreatGlowBeacon(group, 1.6, 0.6, 0);
    this.registerInteractiveObject(group, hitBox, data, 14.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 8. THREAT: PLASTIC TRASH DUMP
  // -------------------------------------------------------------
  spawnPlasticTrash(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y + 0.1, z);

    const bottleMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.75 });
    const bottleGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 8);
    for (let i = 0; i < 11; i++) {
      const bottle = new THREE.Mesh(bottleGeo, bottleMat);
      bottle.position.set((Math.random() - 0.5) * 2.2, 0.1, (Math.random() - 0.5) * 2.2);
      bottle.rotation.set(Math.PI / 2, Math.random() * Math.PI, Math.random());
      group.add(bottle);
    }

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(3.5, 2.0, 3.5), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(0, 0.8, 0);
    group.add(hitBox);

    this.addThreatGlowBeacon(group, 0, 0.6, 0);
    this.registerInteractiveObject(group, hitBox, data, 14.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 9. THREAT: ILLEGAL LOGGING
  // -------------------------------------------------------------
  spawnIllegalLogging(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y, z);

    const stumpGeo = new THREE.CylinderGeometry(1.4, 1.6, 1.4, 10);
    stumpGeo.translate(0, 0.7, 0);
    const stump = new THREE.Mesh(stumpGeo, new THREE.MeshStandardMaterial({ map: this.textures.bark }));
    group.add(stump);

    const fallenTrunk = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.2, 8, 8), new THREE.MeshStandardMaterial({ map: this.textures.bark }));
    fallenTrunk.rotation.z = Math.PI / 2;
    fallenTrunk.position.set(4.5, 0.6, 0.8);
    group.add(fallenTrunk);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(7.0, 3.5, 5.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(2.0, 1.2, 0);
    group.add(hitBox);

    this.addThreatGlowBeacon(group, 0, 1.5, 0);
    this.registerInteractiveObject(group, hitBox, data, 16.0);
    this.scene.add(group);
  }

  // -------------------------------------------------------------
  // 10. THREAT: CHEMICAL WASTE DRUM
  // -------------------------------------------------------------
  spawnChemicalWaste(data) {
    if (!data) return;
    const group = new THREE.Group();
    const x = data.position.x;
    const z = data.position.z;
    const y = this.getTerrainHeight(x, z);
    group.position.set(x, y, z);

    const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 1.8, 12), new THREE.MeshStandardMaterial({ color: 0xeab308, roughness: 0.8 }));
    barrel.position.set(0, 0.65, 0);
    barrel.rotation.z = 0.45;
    group.add(barrel);

    const puddleGeo = new THREE.CircleGeometry(2.4, 20);
    puddleGeo.rotateX(-Math.PI / 2);
    const puddleMat = new THREE.MeshStandardMaterial({
      color: 0x22c55e,
      emissive: 0x15803d,
      emissiveIntensity: 0.7,
      roughness: 0.1
    });
    const puddle = new THREE.Mesh(puddleGeo, puddleMat);
    puddle.position.set(0.6, 0.05, 0);
    group.add(puddle);

    const hitBox = new THREE.Mesh(new THREE.BoxGeometry(4.0, 3.0, 4.0), new THREE.MeshBasicMaterial({ visible: false }));
    hitBox.position.set(0.4, 1.0, 0);
    group.add(hitBox);

    this.addThreatGlowBeacon(group, 0.6, 0.8, 0);
    this.registerInteractiveObject(group, hitBox, data, 16.0);
    this.scene.add(group);
  }

  addThreatGlowBeacon(parent, ox, oy, oz) {
    const beaconGeo = new THREE.RingGeometry(0.35, 0.48, 16);
    beaconGeo.rotateX(-Math.PI / 2);
    const beaconMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.8
    });
    const beacon = new THREE.Mesh(beaconGeo, beaconMat);
    beacon.position.set(ox, oy, oz);
    parent.add(beacon);

    this.animatedCreatures.push({
      group: beacon,
      update: (time) => {
        beacon.scale.setScalar(0.9 + Math.sin(time * 4) * 0.2);
      }
    });
  }

  registerInteractiveObject(groupMesh, hitMesh, data, triggerDistance = 16.0) {
    hitMesh.userData = { parentGroup: groupMesh, data: data };
    this.interactiveObjects.push({
      group: groupMesh,
      hitMesh: hitMesh,
      data: data,
      distanceThreshold: triggerDistance,
      position: groupMesh.position
    });
    this.raycastHitList.push(hitMesh);
  }

  // -------------------------------------------------------------
  // ORIENTATION RESET & COMPASS
  // -------------------------------------------------------------
  resetOrientation() {
    this.player.pitch = 0;
    this.player.yaw = 0; // Look straight North down the path toward the deer
    const btn = document.getElementById("reset-orientation-btn");
    if (btn) {
      btn.style.transform = "scale(0.92)";
      setTimeout(() => { btn.style.transform = "scale(1)"; }, 150);
    }
  }

  updateCompass() {
    let deg = Math.round((-this.player.yaw * (180 / Math.PI)) % 360);
    if (deg < 0) deg += 360;

    const cardinalPoints = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    const idx = Math.round(deg / 45) % 8;
    const cardinal = cardinalPoints[idx];

    const compassEl = document.getElementById("compass-heading");
    if (compassEl) {
      compassEl.textContent = `${String(deg).padStart(3, "0")}° ${cardinal}`;
    }
  }

  // -------------------------------------------------------------
  // DIRECT MOUSE RAYCASTING & CLICK SELECTION
  // -------------------------------------------------------------
  updateRaycasting() {
    if (this.isPointerLocked) {
      this.raycaster.setFromCamera(new THREE.Vector2(0, 0), this.camera);
    } else {
      this.raycaster.setFromCamera(this.mouseCoords, this.camera);
    }

    const intersects = this.raycaster.intersectObjects(this.raycastHitList, false);

    const tooltip = document.getElementById("hover-tooltip");
    const prompt = document.getElementById("inspect-prompt");
    const crosshair = document.querySelector(".crosshair");

    if (intersects.length > 0) {
      const hit = intersects[0];
      const data = hit.object.userData.data;

      this.hoveredObject = hit.object.userData;
      this.container.style.cursor = "pointer";

      if (crosshair) {
        crosshair.className = "crosshair " + (data.type === "threat" ? "hovered-threat" : "hovered");
      }

      if (tooltip) {
        tooltip.style.display = "block";
        tooltip.className = (data.type === "threat") ? "threat" : "";
        tooltip.innerHTML = `<strong>${data.icon} ${data.name}</strong><br><span style="font-size:0.75rem; color:#a7f3d0;">Click to Select & Inspect</span>`;
        if (!this.isPointerLocked) {
          tooltip.style.left = `${this.screenMouse.x}px`;
          tooltip.style.top = `${this.screenMouse.y}px`;
        } else {
          tooltip.style.left = `50%`;
          tooltip.style.top = `56%`;
        }
      }

      if (prompt) {
        prompt.style.display = "flex";
        prompt.className = (data.type === "threat") ? "threat-prompt" : "";
        prompt.innerHTML = `<span>${data.icon}</span> Click to Select ${data.name} [or Press E]`;
      }
    } else {
      this.hoveredObject = null;
      this.container.style.cursor = "default";
      if (tooltip) tooltip.style.display = "none";
      if (crosshair) crosshair.className = "crosshair";

      this.checkNearbyTargets();
    }
  }

  checkNearbyTargets() {
    let closestObj = null;
    let minDistance = Infinity;
    const playerPos = this.player.position;

    for (let item of this.interactiveObjects) {
      const d = playerPos.distanceTo(item.position);
      if (d < item.distanceThreshold && d < minDistance) {
        minDistance = d;
        closestObj = item;
      }
    }

    this.nearbyTarget = closestObj;
    const prompt = document.getElementById("inspect-prompt");

    if (closestObj) {
      prompt.style.display = "flex";
      const isThreat = (closestObj.data.type === "threat");
      prompt.className = isThreat ? "threat-prompt" : "";
      prompt.innerHTML = `<span>${closestObj.data.icon}</span> ${closestObj.data.name} [Click / Press E]`;
    } else {
      if (!this.hoveredObject && prompt) {
        prompt.style.display = "none";
      }
    }
  }

  selectCurrentTarget() {
    let targetData = null;
    if (this.hoveredObject) {
      targetData = this.hoveredObject.data;
    } else if (this.nearbyTarget) {
      targetData = this.nearbyTarget.data;
    }

    if (!targetData) return;

    const isThreat = (targetData.type === "threat");
    if (isThreat) {
      if (!this.discoveredThreats.has(targetData.id)) {
        this.discoveredThreats.add(targetData.id);
        this.playDiscoveryChime(true);
      }
    } else {
      if (!this.discoveredSpecies.has(targetData.id)) {
        this.discoveredSpecies.add(targetData.id);
        this.playDiscoveryChime(false);
      }
    }

    this.updateHUDTrackers();
    this.openDetailsModal(targetData);
  }

  // -------------------------------------------------------------
  // CONTROLS & EVENT LISTENERS (Laptop Trackpad & Keyboard Optimized)
  // -------------------------------------------------------------
  setupEvents() {
    window.addEventListener("resize", () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // 1. Laptop Trackpad Two-Finger Pan (Wheel Event)
    window.addEventListener("wheel", (e) => {
      // Allow scrolling inside open Field Journal modal
      if (document.getElementById("journal-modal")?.classList.contains("open")) {
        return;
      }
      e.preventDefault();
      const trackpadSens = 0.0024;
      this.player.yaw -= e.deltaX * trackpadSens;
      this.player.pitch -= e.deltaY * trackpadSens;
      this.player.pitch = Math.max(-Math.PI / 2.3, Math.min(Math.PI / 2.3, this.player.pitch));
    }, { passive: false });

    // 2. Mouse & Trackpad Movement Tracking
    window.addEventListener("mousemove", (e) => {
      this.screenMouse.x = e.clientX;
      this.screenMouse.y = e.clientY;
      this.mouseCoords.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouseCoords.y = -(e.clientY / window.innerHeight) * 2 + 1;

      // Pointer lock mode look
      if (this.isPointerLocked) {
        const sensitivity = 0.0022;
        this.player.yaw -= e.movementX * sensitivity;
        this.player.pitch -= e.movementY * sensitivity;
        this.player.pitch = Math.max(-Math.PI / 2.3, Math.min(Math.PI / 2.3, this.player.pitch));
      } else if (this.isDragging) {
        // Trackpad one-finger hold & drag to look
        const deltaX = e.clientX - this.lastPointer.x;
        const deltaY = e.clientY - this.lastPointer.y;
        this.lastPointer.x = e.clientX;
        this.lastPointer.y = e.clientY;

        const dragSens = 0.0035;
        this.player.yaw -= deltaX * dragSens;
        this.player.pitch -= deltaY * dragSens;
        this.player.pitch = Math.max(-Math.PI / 2.3, Math.min(Math.PI / 2.3, this.player.pitch));
      }
    });

    // 3. Trackpad / Mouse Press & Drag or Click Select
    this.container.addEventListener("pointerdown", (e) => {
      this.isDragging = true;
      this.dragStart.x = e.clientX;
      this.dragStart.y = e.clientY;
      this.lastPointer.x = e.clientX;
      this.lastPointer.y = e.clientY;
    });

    window.addEventListener("pointerup", (e) => {
      if (this.isDragging) {
        const dx = e.clientX - this.dragStart.x;
        const dy = e.clientY - this.dragStart.y;
        const dragDist = Math.sqrt(dx * dx + dy * dy);

        // If tap or small click without dragging, trigger selection!
        if (dragDist < 6) {
          if (this.hoveredObject || this.nearbyTarget) {
            this.selectCurrentTarget();
          }
        }
      }
      this.isDragging = false;
    });

    window.addEventListener("pointercancel", () => {
      this.isDragging = false;
    });

    // Proximity prompt directly clickable
    document.getElementById("inspect-prompt")?.addEventListener("click", (e) => {
      e.stopPropagation();
      this.selectCurrentTarget();
    });

    document.addEventListener("pointerlockchange", () => {
      this.isPointerLocked = (document.pointerLockElement === this.container);
    });

    // Reset Orientation button & hotkey
    document.getElementById("reset-orientation-btn")?.addEventListener("click", () => {
      this.resetOrientation();
    });

    // 4. Keyboard Navigation: WASD / Arrow Keys (Seamless movement and turning)
    window.addEventListener("keydown", (e) => {
      switch (e.code) {
        case "KeyW":
        case "ArrowUp":
          this.keys.forward = true;
          break;
        case "KeyS":
        case "ArrowDown":
          this.keys.backward = true;
          break;
        case "KeyA":
          this.keys.left = true;
          break;
        case "KeyD":
          this.keys.right = true;
          break;
        case "ArrowLeft":
        case "KeyQ":
          this.keys.turnLeft = true;
          break;
        case "ArrowRight":
          this.keys.turnRight = true;
          break;
        case "ShiftLeft":
        case "ShiftRight":
          this.keys.sprint = true;
          break;
        case "KeyE":
        case "Space":
        case "Enter":
          this.selectCurrentTarget();
          break;
        case "KeyR":
          this.resetOrientation();
          break;
        case "KeyB":
          this.toggleBinoculars();
          break;
        case "KeyJ":
          this.openGeneralJournal();
          break;
        case "KeyT":
          this.openARExperience(FOREST_DATA.species.find(s => s.id === "tiger"));
          break;
      }
    });

    window.addEventListener("keyup", (e) => {
      switch (e.code) {
        case "KeyW":
        case "ArrowUp":
          this.keys.forward = false;
          break;
        case "KeyS":
        case "ArrowDown":
          this.keys.backward = false;
          break;
        case "KeyA":
          this.keys.left = false;
          break;
        case "KeyD":
          this.keys.right = false;
          break;
        case "ArrowLeft":
        case "KeyQ":
          this.keys.turnLeft = false;
          break;
        case "ArrowRight":
          this.keys.turnRight = false;
          break;
        case "ShiftLeft":
        case "ShiftRight":
          this.keys.sprint = false;
          break;
      }
    });

    document.getElementById("start-btn")?.addEventListener("click", () => {
      this.startAudio();
      document.getElementById("start-screen").style.display = "none";
      this.resetOrientation();
    });

    document.getElementById("binocular-btn")?.addEventListener("click", () => {
      this.toggleBinoculars();
    });

    document.getElementById("journal-btn")?.addEventListener("click", () => {
      this.openGeneralJournal();
    });

    document.getElementById("hud-ar-btn")?.addEventListener("click", () => {
      this.openARExperience(FOREST_DATA.species.find(s => s.id === "tiger"));
    });

    document.getElementById("close-journal")?.addEventListener("click", () => {
      document.getElementById("journal-modal").classList.remove("open");
    });

    this.setupMobileControls();
    this.setupARListeners();
  }

  setupMobileControls() {
    const base = document.getElementById("joystick-base");
    const knob = document.getElementById("joystick-knob");
    const actionBtn = document.getElementById("mobile-action-btn");
    if (!base || !knob) return;

    let touchId = null;
    let baseRect = null;

    base.addEventListener("touchstart", (e) => {
      const touch = e.changedTouches[0];
      touchId = touch.identifier;
      baseRect = base.getBoundingClientRect();
      this.handleJoystickMove(touch.clientX, touch.clientY, baseRect, knob);
    }, { passive: false });

    base.addEventListener("touchmove", (e) => {
      e.preventDefault();
      for (let i = 0; i < e.changedTouches.length; i++) {
        if (e.changedTouches[i].identifier === touchId) {
          this.handleJoystickMove(e.changedTouches[i].clientX, e.changedTouches[i].clientY, baseRect, knob);
        }
      }
    }, { passive: false });

    const resetJoystick = (e) => {
      for (let i = 0; i < e.changedTouches.length; i++) {
        if (e.changedTouches[i].identifier === touchId) {
          touchId = null;
          knob.style.transform = `translate(0px, 0px)`;
          this.joystickVector = { x: 0, y: 0 };
        }
      }
    };
    base.addEventListener("touchend", resetJoystick);
    base.addEventListener("touchcancel", resetJoystick);

    let lastTouchX = 0;
    let lastTouchY = 0;
    window.addEventListener("touchstart", (e) => {
      if (e.target !== base && !base.contains(e.target)) {
        lastTouchX = e.touches[0].clientX;
        lastTouchY = e.touches[0].clientY;
      }
    });

    window.addEventListener("touchmove", (e) => {
      if (e.target !== base && !base.contains(e.target) && e.touches.length === 1) {
        const deltaX = e.touches[0].clientX - lastTouchX;
        const deltaY = e.touches[0].clientY - lastTouchY;
        lastTouchX = e.touches[0].clientX;
        lastTouchY = e.touches[0].clientY;

        const sens = 0.005;
        this.player.yaw -= deltaX * sens;
        this.player.pitch -= deltaY * sens;
        this.player.pitch = Math.max(-Math.PI / 2.3, Math.min(Math.PI / 2.3, this.player.pitch));
      }
    });

    actionBtn?.addEventListener("touchstart", (e) => {
      e.preventDefault();
      this.selectCurrentTarget();
    });
  }

  handleJoystickMove(cx, cy, rect, knob) {
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    let dx = cx - centerX;
    let dy = cy - centerY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const maxRadius = 45;

    if (dist > maxRadius) {
      dx = (dx / dist) * maxRadius;
      dy = (dy / dist) * maxRadius;
    }

    knob.style.transform = `translate(${dx}px, ${dy}px)`;
    this.joystickVector = { x: 0, y: 0 };
    this.joystickVector.x = dx / maxRadius;
    this.joystickVector.y = dy / maxRadius;
  }

  toggleBinoculars() {
    this.isBinocularActive = !this.isBinocularActive;
    const overlay = document.getElementById("binocular-overlay");
    if (this.isBinocularActive) {
      overlay.classList.add("active");
      this.camera.fov = 22;
    } else {
      overlay.classList.remove("active");
      this.camera.fov = 60;
    }
    this.camera.updateProjectionMatrix();
  }

  // -------------------------------------------------------------
  // AUDIO & HUD HELPERS
  // -------------------------------------------------------------
  initAudioEngine() {
    this.audioCtx = null;
    this.isMuted = false;
  }

  startAudio() {
    if (this.audioCtx) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    this.audioCtx = new AudioContext();

    const bufferSize = this.audioCtx.sampleRate * 2;
    const noiseBuffer = this.audioCtx.createBuffer(1, bufferSize, this.audioCtx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      output[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = output[i];
      output[i] *= 3.5;
    }

    const whiteNoise = this.audioCtx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    const windFilter = this.audioCtx.createBiquadFilter();
    windFilter.type = "lowpass";
    windFilter.frequency.value = 320;

    const windGain = this.audioCtx.createGain();
    windGain.gain.value = 0.08;

    whiteNoise.connect(windFilter);
    windFilter.connect(windGain);
    windGain.connect(this.audioCtx.destination);
    whiteNoise.start();

    this.scheduleBirdSong();
  }

  scheduleBirdSong() {
    if (!this.audioCtx || this.isMuted) return;
    const delay = 4000 + Math.random() * 6000;
    setTimeout(() => {
      this.playBirdChirp();
      this.scheduleBirdSong();
    }, delay);
  }

  playBirdChirp() {
    if (!this.audioCtx || this.isMuted) return;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();

    osc.type = "sine";
    const baseFreq = 2200 + Math.random() * 900;
    osc.frequency.setValueAtTime(baseFreq, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(baseFreq + 600, this.audioCtx.currentTime + 0.08);
    osc.frequency.exponentialRampToValueAtTime(baseFreq - 300, this.audioCtx.currentTime + 0.18);

    gain.gain.setValueAtTime(0.04, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + 0.22);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.25);
  }

  playDiscoveryChime(isThreat) {
    if (!this.audioCtx || this.isMuted) return;
    const now = this.audioCtx.currentTime;
    const freqs = isThreat ? [440, 370, 311] : [523.25, 659.25, 783.99, 1046.5];

    freqs.forEach((f, idx) => {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = isThreat ? "sawtooth" : "triangle";
      osc.frequency.setValueAtTime(f, now + idx * 0.1);

      gain.gain.setValueAtTime(0.08, now + idx * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.1 + 0.45);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start(now + idx * 0.1);
      osc.stop(now + idx * 0.1 + 0.5);
    });
  }

  playStepSound() {
    if (!this.audioCtx || this.isMuted) return;
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = "triangle";
    osc.frequency.setValueAtTime(90 + Math.random() * 40, this.audioCtx.currentTime);
    gain.gain.setValueAtTime(0.03, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.08);
    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.09);
  }

  updateHUDTrackers() {
    const sFound = this.discoveredSpecies.size;
    const sTotal = FOREST_DATA.species.length;
    const tFound = this.discoveredThreats.size;
    const tTotal = FOREST_DATA.threats.length;

    const sEl = document.getElementById("species-count");
    const tEl = document.getElementById("threats-count");
    if (sEl) sEl.textContent = `${sFound} / ${sTotal}`;
    if (tEl) tEl.textContent = `${tFound} / ${tTotal}`;

    const sProg = document.getElementById("species-progress");
    const tProg = document.getElementById("threats-progress");
    if (sProg) sProg.style.width = `${(sFound / sTotal) * 100}%`;
    if (tProg) tProg.style.width = `${(tFound / tTotal) * 100}%`;
  }

  openDetailsModal(item) {
    // Release pointer lock so user can interact with the card
    if (document.exitPointerLock) {
      document.exitPointerLock();
    }

    const modal = document.getElementById("journal-modal");
    const card = document.getElementById("journal-card-content");
    const isThreat = (item.type === "threat");

    card.className = "journal-card" + (isThreat ? " threat-mode" : "");

    let html = `
      <div class="journal-header">
        <button class="journal-close-btn" id="modal-close-x">✕</button>
        <div class="badge-row">
          <span class="badge ${isThreat ? 'threat' : ''}">${isThreat ? item.severity : item.badge}</span>
          <span class="badge ${isThreat ? 'threat' : ''}">${isThreat ? 'CRITICAL THREAT' : item.conservationStatus}</span>
        </div>
        <h2 class="journal-title">${item.icon} ${item.name}</h2>
        <div class="journal-subtitle">${item.scientificName || "Ecological Hazard Record"}</div>
      </div>
      <div class="journal-body">
    `;

    if (item.image) {
      html += `
        <div class="journal-image-box">
          <img src="${item.image}" alt="${item.name}" />
        </div>
      `;
    }

    html += `
        <div>
          <div class="journal-section-title">Overview & Field Identification</div>
          <p class="journal-text">${item.description}</p>
        </div>
    `;

    if (isThreat) {
      html += `
        <div>
          <div class="journal-section-title">Environmental Damage & Ecological Impact</div>
          <p class="journal-text">${item.impact}</p>
        </div>
        <div>
          <div class="journal-section-title">Remediation & Ranger Protocol</div>
          <p class="journal-text">${item.remedy}</p>
        </div>
      `;
    } else {
      html += `
        <div>
          <div class="journal-section-title">Ecological Role & Forest Function</div>
          <p class="journal-text">${item.ecologicalRole}</p>
        </div>
      `;
    }

    // AR Placement Action CTA in Dossier
    html += `
      <div class="journal-ar-cta">
        <button class="ar-launch-btn" id="modal-launch-ar-btn" data-id="${item.id}">
          <span class="ar-btn-icon">📱✨</span>
          <span>View ${item.name} in AR (Living Forest Habitat)</span>
        </button>
      </div>
    `;

    html += `</div>`;
    card.innerHTML = html;
    modal.classList.add("open");

    document.getElementById("modal-close-x")?.addEventListener("click", () => {
      modal.classList.remove("open");
    });

    document.getElementById("modal-launch-ar-btn")?.addEventListener("click", () => {
      modal.classList.remove("open");
      this.openARExperience(item);
    });
  }

  openGeneralJournal() {
    if (document.exitPointerLock) {
      document.exitPointerLock();
    }

    const modal = document.getElementById("journal-modal");
    const card = document.getElementById("journal-card-content");
    card.className = "journal-card";

    let html = `
      <div class="journal-header">
        <button class="journal-close-btn" id="modal-close-x">✕</button>
        <div class="badge-row">
          <span class="badge">FIELD EXPEDITION LOG</span>
        </div>
        <h2 class="journal-title">🌿 Student Forest Expedition Journal</h2>
        <div class="journal-subtitle">Species Discovered: ${this.discoveredSpecies.size}/${FOREST_DATA.species.length} • Threats Identified: ${this.discoveredThreats.size}/${FOREST_DATA.threats.length}</div>
      </div>
      <div class="journal-body">
        <div class="journal-section-title">Native Wildlife Species Checklist</div>
        <div class="journal-checklist-grid">
    `;

    FOREST_DATA.species.forEach(sp => {
      const found = this.discoveredSpecies.has(sp.id);
      html += `
        <div class="checklist-item ${found ? 'found' : ''}">
          <span style="font-size: 1.5rem;">${sp.icon}</span>
          <div style="flex: 1;">
            <div style="font-weight: 700; font-size: 0.9rem;">${sp.name}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">${found ? '✓ Identified & Logged' : sp.discoveryClue}</div>
          </div>
          <button class="checklist-ar-pill" data-id="${sp.id}" title="View ${sp.name} in AR">📱 AR</button>
        </div>
      `;
    });

    html += `
        </div>
        <div class="journal-section-title" style="margin-top: 14px; color: #f87171;">Ecological Hazards & Threats Checklist</div>
        <div class="journal-checklist-grid">
    `;

    FOREST_DATA.threats.forEach(th => {
      const found = this.discoveredThreats.has(th.id);
      html += `
        <div class="checklist-item ${found ? 'threat-found' : ''}">
          <span style="font-size: 1.5rem;">${th.icon}</span>
          <div style="flex: 1;">
            <div style="font-weight: 700; font-size: 0.9rem;">${th.name}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">${found ? '⚠️ Deactivated / Logged' : th.discoveryClue}</div>
          </div>
          <button class="checklist-ar-pill threat" data-id="${th.id}" title="View ${th.name} in AR">📱 AR</button>
        </div>
      `;
    });

    html += `</div></div>`;
    card.innerHTML = html;
    modal.classList.add("open");

    document.getElementById("modal-close-x")?.addEventListener("click", () => {
      modal.classList.remove("open");
    });

    card.querySelectorAll(".checklist-ar-pill").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        const found = FOREST_DATA.species.find(s => s.id === id) || FOREST_DATA.threats.find(t => t.id === id);
        if (found) {
          modal.classList.remove("open");
          this.openARExperience(found);
        }
      });
    });
  }

  // -------------------------------------------------------------
  // GOOGLE ARCORE & WEBXR AR INTEGRATION
  // -------------------------------------------------------------
  openARExperience(item) {
    if (!item) {
      item = FOREST_DATA.species.find(s => s.id === "tiger") || FOREST_DATA.species[0];
    }

    if (document.exitPointerLock) {
      document.exitPointerLock();
    }

    this.currentARItem = item;

    // Check if on mobile phone or tablet
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (window.innerWidth <= 800) || ('ontouchstart' in window);

    // DEFAULT MODE ON MOBILE: Directly launch Live Camera Passthrough AR (zero Google app crash!)
    if (isMobile && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      this.startBrowserCameraAR(item);
      return;
    }

    const modal = document.getElementById("ar-experience-modal");
    const viewer = document.getElementById("ar-viewer");
    const title = document.getElementById("ar-title");
    const subtitle = document.getElementById("ar-subtitle");
    const treeBtn = document.getElementById("ar-tree-toggle-btn");
    const treeStatus = document.getElementById("ar-tree-status");
    const scaleBtn = document.getElementById("ar-scale-toggle-btn");
    const scaleStatus = document.getElementById("ar-scale-status");
    const qrImg = document.getElementById("ar-qr-img");
    const habitatOverlay = document.getElementById("ar-habitat-overlay");

    if (!modal || !viewer) return;

    this.arTreesEnabled = true;
    this.arScaleMode = "1:1";

    if (title) title.textContent = `${item.icon || '🌲'} ${item.name} in AR`;
    if (subtitle) {
      subtitle.textContent = item.id === "tiger"
        ? "Place the 1:1 life-size Royal Bengal Tiger & its living forest habitat on your physical floor"
        : `Place the 1:1 life-size ${item.name} and forest environment on your physical floor`;
    }

    let modelPath = item.model || "assets/models/tiger.glb";

    // Convert embedded base64 to Blob URL for 100% zero-CORS offline & mobile file:// compatibility
    try {
      let b64 = null;
      if (item.id === "spotted_deer" && typeof DEER_MODEL_BASE64 !== "undefined") {
        b64 = DEER_MODEL_BASE64;
      } else if (typeof SPECIES_MODELS_BASE64 !== "undefined" && SPECIES_MODELS_BASE64[item.id]) {
        b64 = SPECIES_MODELS_BASE64[item.id];
      } else if (typeof THREATS_MODELS_BASE64 !== "undefined" && THREATS_MODELS_BASE64[item.id]) {
        b64 = THREATS_MODELS_BASE64[item.id];
      }

      if (b64) {
        const byteCharacters = atob(b64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "model/gltf-binary" });
        modelPath = URL.createObjectURL(blob);
      }
    } catch (e) {
      console.warn("Base64 to Blob URL fallback for AR", e);
    }

    viewer.setAttribute("src", modelPath);
    viewer.setAttribute("alt", `${item.name} in AR`);

    if (treeBtn && treeStatus) {
      treeBtn.classList.add("active");
      treeStatus.textContent = "ON";
    }
    if (habitatOverlay) {
      habitatOverlay.classList.add("active");
      const tag = habitatOverlay.querySelector(".ar-habitat-tag");
      if (tag) tag.textContent = "🌲 Living Forest Trees & Bamboo Active";
    }

    if (scaleBtn && scaleStatus) {
      scaleStatus.textContent = "1:1 Life Size";
      viewer.setAttribute("ar-scale", "fixed");
      scaleBtn.classList.remove("tabletop-mode");
    }

    // Generate dynamic QR code for desktop-to-mobile AR handover
    if (qrImg) {
      const currentUrl = window.location.href.split('#')[0];
      const mobileTargetUrl = `${currentUrl}#ar-${item.id}`;
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(mobileTargetUrl)}&color=052e16&bgcolor=f0fdf4`;
    }

    modal.classList.add("open");
  }

  setupARListeners() {
    const modal = document.getElementById("ar-experience-modal");
    const viewer = document.getElementById("ar-viewer");
    const closeBtn = document.getElementById("close-ar-modal");
    const treeBtn = document.getElementById("ar-tree-toggle-btn");
    const treeStatus = document.getElementById("ar-tree-status");
    const scaleBtn = document.getElementById("ar-scale-toggle-btn");
    const scaleStatus = document.getElementById("ar-scale-status");
    const directBtn = document.getElementById("ar-direct-scene-btn");
    const habitatOverlay = document.getElementById("ar-habitat-overlay");

    closeBtn?.addEventListener("click", () => {
      modal?.classList.remove("open");
    });

    modal?.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("open");
      }
    });

    // Toggle Trees ON / OFF
    treeBtn?.addEventListener("click", () => {
      this.arTreesEnabled = !this.arTreesEnabled;
      const tag = habitatOverlay?.querySelector(".ar-habitat-tag");
      if (this.arTreesEnabled) {
        treeBtn.classList.add("active");
        if (treeStatus) treeStatus.textContent = "ON";
        if (habitatOverlay) habitatOverlay.classList.add("active");
        if (tag) tag.textContent = "🌲 Living Forest Trees & Bamboo Active";
        viewer?.setAttribute("shadow-intensity", "1.6");
        viewer?.setAttribute("exposure", "1.05");
      } else {
        treeBtn.classList.remove("active");
        if (treeStatus) treeStatus.textContent = "OFF";
        if (habitatOverlay) habitatOverlay.classList.remove("active");
        if (tag) tag.textContent = "🌾 Open Clearing Mode (No Trees)";
        viewer?.setAttribute("shadow-intensity", "1.0");
        viewer?.setAttribute("exposure", "1.0");
      }
    });

    // Toggle Scale: 1:1 Life Size vs Tabletop
    scaleBtn?.addEventListener("click", () => {
      if (this.arScaleMode === "1:1") {
        this.arScaleMode = "tabletop";
        if (scaleStatus) scaleStatus.textContent = "Tabletop Miniature";
        viewer?.setAttribute("ar-scale", "auto");
        scaleBtn.classList.add("tabletop-mode");
      } else {
        this.arScaleMode = "1:1";
        if (scaleStatus) scaleStatus.textContent = "1:1 Life Size";
        viewer?.setAttribute("ar-scale", "fixed");
        scaleBtn.classList.remove("tabletop-mode");
      }
    });

    // Live Browser Camera AR Button (Failsafe for devices where Google app crashes)
    document.getElementById("ar-browser-camera-btn")?.addEventListener("click", () => {
      this.startBrowserCameraAR(this.currentARItem);
    });

    // Direct ARCore Launch Button
    directBtn?.addEventListener("click", () => {
      const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
      if (isMobile && viewer && typeof viewer.activateAR === "function") {
        try {
          viewer.activateAR();
          return;
        } catch (err) {
          console.warn("viewer.activateAR() call issue, trying intent", err);
        }
      }

      // Android ARCore Scene Viewer Intent fallback
      const isAndroid = /Android/i.test(navigator.userAgent);
      if (isAndroid) {
        const item = this.currentARItem || FOREST_DATA.species.find(s => s.id === "tiger");
        const fullGlbUrl = new URL(item.model || "assets/models/tiger.glb", window.location.href).href;
        const titleParam = encodeURIComponent(item.name || "Royal Bengal Tiger");
        const intentUri = `intent://arvr.google.com/scene-viewer/1.0?file=${encodeURIComponent(fullGlbUrl)}&mode=ar_preferred&title=${titleParam}&resizable=true#Intent;scheme=https;package=com.google.ar.core;action=android.intent.action.VIEW;end;`;
        window.location.href = intentUri;
      } else {
        const arBtn = document.getElementById("ar-camera-btn");
        if (arBtn) {
          arBtn.click();
        } else {
          document.getElementById("ar-desktop-qr-box")?.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });

    // Check URL Hash for deep-link AR on mobile load
    if (window.location.hash.startsWith("#ar-")) {
      const targetId = window.location.hash.replace("#ar-", "");
      const foundItem = FOREST_DATA.species.find(s => s.id === targetId) || FOREST_DATA.threats.find(t => t.id === targetId);
      if (foundItem) {
        setTimeout(() => this.openARExperience(foundItem), 800);
      }
    }
  }

  // -------------------------------------------------------------
  // DIRECT IN-BROWSER CAMERA AR (FAILSAFE - NO GOOGLE APP NEEDED)
  // -------------------------------------------------------------
  startBrowserCameraAR(item) {
    if (!item) item = FOREST_DATA.species.find(s => s.id === "tiger") || FOREST_DATA.species[0];
    const modal = document.getElementById("ar-experience-modal");
    if (modal) modal.classList.remove("open");

    const video = document.getElementById("ar-camera-video");
    const hud = document.getElementById("browser-ar-hud");
    const mainHud = document.getElementById("hud");
    const vignette = document.querySelector(".atmospheric-vignette");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("Camera API is not supported in this browser. Please use Chrome or Safari.");
      return;
    }

    navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    }).then(stream => {
      this.isBrowserARActive = true;
      this.arCameraStream = stream;
      if (video) {
        video.srcObject = stream;
        video.style.display = "block";
      }

      // Hide standard exploration HUD & vignette
      if (mainHud) mainHud.style.display = "none";
      if (vignette) vignette.style.display = "none";
      if (hud) hud.style.display = "flex";

      // Make WebGL canvas background transparent so camera video shows behind
      this.renderer.setClearColor(0x000000, 0);

      // Hide full 3D terrain and sky in exploration scene
      if (this.terrainMesh) this.terrainMesh.visible = false;
      if (this.canopyGroup) this.canopyGroup.visible = false;
      if (this.atmosphericGroup) this.atmosphericGroup.visible = false;
      if (this.scene.fog) {
        this.savedFog = this.scene.fog;
        this.scene.fog = null;
      }

      // Save exploration camera & set AR camera pose
      this.savedPlayerPos = this.player.position.clone();
      this.savedPlayerYaw = this.player.yaw;
      this.savedPlayerPitch = this.player.pitch;

      this.camera.position.set(0, 0, 0);
      this.camera.rotation.set(0, 0, 0);

      // Create AR composite habitat group
      this.setupBrowserARHabitat(item);
      this.setupBrowserARGestures();

    }).catch(err => {
      console.error("Camera access failed", err);
      alert("Camera access was blocked. Please tap the lock icon in Chrome's address bar and set Camera to Allow.");
    });
  }

  setupBrowserARHabitat(item) {
    if (this.browserARGroup) {
      this.scene.remove(this.browserARGroup);
    }

    this.browserARGroup = new THREE.Group();
    this.browserARGroup.position.set(0, -0.65, -2.5);

    // 1. Mossy clearing ground disk
    const groundGeo = new THREE.CircleGeometry(1.8, 32);
    groundGeo.rotateX(-Math.PI / 2);
    const groundMat = new THREE.MeshStandardMaterial({
      map: this.textures.ground,
      roughness: 0.9,
      transparent: true,
      opacity: 0.85
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.receiveShadow = true;
    this.browserARGroup.add(ground);

    // 2. Soft shadow receiver plane
    const shadowGeo = new THREE.PlaneGeometry(3.5, 3.5);
    shadowGeo.rotateX(-Math.PI / 2);
    const shadowMat = new THREE.ShadowMaterial({ opacity: 0.55 });
    const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
    shadowMesh.position.y = 0.005;
    shadowMesh.receiveShadow = true;
    this.browserARGroup.add(shadowMesh);

    // 3. Surrounding bamboo & ferns
    this.arFoliageGroup = new THREE.Group();
    const bMat = new THREE.MeshStandardMaterial({ map: this.textures.bark, roughness: 0.8 });
    [-1.0, 1.0].forEach((bx, idx) => {
      const bamboo = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.06, 2.2, 6), bMat);
      bamboo.position.set(bx, 1.1, -0.3 + idx * 0.2);
      this.arFoliageGroup.add(bamboo);
    });
    this.browserARGroup.add(this.arFoliageGroup);

    // 4. Load 3D model (using base64 Blob URL for 100% offline & local file:// support)
    let modelSrc = item.model || "assets/models/tiger.glb";
    try {
      let b64 = null;
      if (item.id === "spotted_deer" && typeof DEER_MODEL_BASE64 !== "undefined") {
        b64 = DEER_MODEL_BASE64;
      } else if (typeof SPECIES_MODELS_BASE64 !== "undefined" && SPECIES_MODELS_BASE64[item.id]) {
        b64 = SPECIES_MODELS_BASE64[item.id];
      } else if (typeof THREATS_MODELS_BASE64 !== "undefined" && THREATS_MODELS_BASE64[item.id]) {
        b64 = THREATS_MODELS_BASE64[item.id];
      }

      if (b64) {
        const byteCharacters = atob(b64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "model/gltf-binary" });
        modelSrc = URL.createObjectURL(blob);
      }
    } catch (e) {
      console.warn("Base64 to blob error in AR habitat", e);
    }

    const loader = new THREE.GLTFLoader();
    loader.load(modelSrc, (gltf) => {
      const tiger = gltf.scene;
      tiger.scale.set(0.7, 0.7, 0.7);
      tiger.position.set(0, 0, 0);
      tiger.traverse(c => {
        if (c.isMesh) {
          c.castShadow = true;
          c.receiveShadow = true;
        }
      });
      this.browserARTiger = tiger;
      this.browserARGroup.add(tiger);
    }, undefined, (err) => {
      console.warn("AR GLB fallback", err);
      const box = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.7, 1.8), new THREE.MeshStandardMaterial({ color: 0xd97706 }));
      box.position.y = 0.35;
      this.browserARTiger = box;
      this.browserARGroup.add(box);
    });

    this.scene.add(this.browserARGroup);

    // 5. Directional sun light for floor shadow
    if (!this.arLight) {
      this.arLight = new THREE.DirectionalLight(0xfff5e6, 1.4);
      this.arLight.position.set(1.5, 4.0, 1.5);
      this.arLight.castShadow = true;
      this.scene.add(this.arLight);
    }
  }

  setupBrowserARGestures() {
    const exitBtn = document.getElementById("exit-browser-ar-btn");
    const treeBtn = document.getElementById("bar-tree-btn");
    const treeTxt = document.getElementById("bar-tree-txt");
    const scaleBtn = document.getElementById("bar-scale-btn");
    const scaleTxt = document.getElementById("bar-scale-txt");
    const recenterBtn = document.getElementById("bar-recenter-btn");

    if (exitBtn) exitBtn.onclick = () => this.stopBrowserCameraAR();

    let treesOn = true;
    if (treeBtn) {
      treeBtn.onclick = () => {
        treesOn = !treesOn;
        if (treeTxt) treeTxt.textContent = treesOn ? "ON" : "OFF";
        if (this.arFoliageGroup) this.arFoliageGroup.visible = treesOn;
      };
    }

    let scale1x = true;
    if (scaleBtn) {
      scaleBtn.onclick = () => {
        scale1x = !scale1x;
        if (scaleTxt) scaleTxt.textContent = scale1x ? "1:1" : "0.3x";
        if (this.browserARGroup) {
          const s = scale1x ? 1.0 : 0.35;
          this.browserARGroup.scale.set(s, s, s);
        }
      };
    }

    if (recenterBtn) {
      recenterBtn.onclick = () => {
        if (this.browserARGroup) {
          this.browserARGroup.position.set(0, -0.65, -2.5);
          this.browserARGroup.rotation.set(0, 0, 0);
        }
      };
    }

    // Touch drag to reposition tiger on floor
    let touchStartX = 0;
    let touchStartY = 0;
    window.addEventListener("touchmove", (e) => {
      if (!this.isBrowserARActive || !this.browserARGroup) return;
      if (e.touches.length === 1) {
        const t = e.touches[0];
        if (touchStartX && touchStartY) {
          const dx = (t.clientX - touchStartX) * 0.005;
          const dy = (t.clientY - touchStartY) * 0.005;
          this.browserARGroup.position.x += dx;
          this.browserARGroup.position.z += dy;
        }
        touchStartX = t.clientX;
        touchStartY = t.clientY;
      }
    }, { passive: true });

    window.addEventListener("touchend", () => {
      touchStartX = 0;
      touchStartY = 0;
    }, { passive: true });
  }

  stopBrowserCameraAR() {
    this.isBrowserARActive = false;
    if (this.arCameraStream) {
      this.arCameraStream.getTracks().forEach(track => track.stop());
      this.arCameraStream = null;
    }

    const video = document.getElementById("ar-camera-video");
    const hud = document.getElementById("browser-ar-hud");
    const mainHud = document.getElementById("hud");
    const vignette = document.querySelector(".atmospheric-vignette");

    if (video) video.style.display = "none";
    if (hud) hud.style.display = "none";
    if (mainHud) mainHud.style.display = "flex";
    if (vignette) vignette.style.display = "block";

    if (this.browserARGroup) {
      this.scene.remove(this.browserARGroup);
      this.browserARGroup = null;
    }
    if (this.arLight) {
      this.scene.remove(this.arLight);
      this.arLight = null;
    }

    // Restore terrain, sky, fog
    if (this.terrainMesh) this.terrainMesh.visible = true;
    if (this.canopyGroup) this.canopyGroup.visible = true;
    if (this.atmosphericGroup) this.atmosphericGroup.visible = true;
    if (this.savedFog) {
      this.scene.fog = this.savedFog;
    }

    this.renderer.setClearColor(0x061009, 1);

    // Restore player camera
    if (this.savedPlayerPos) {
      this.player.position.copy(this.savedPlayerPos);
      this.player.yaw = this.savedPlayerYaw;
      this.player.pitch = this.savedPlayerPitch;
    }
  }

  // -------------------------------------------------------------
  // ANIMATION & PHYSICS TICK
  // -------------------------------------------------------------
  animate() {
    requestAnimationFrame(this.animate);

    const delta = Math.min(this.clock.getDelta(), 0.1);
    const time = this.clock.getElapsedTime();

    // If Live Browser Camera AR is active, update breathing animation and render
    if (this.isBrowserARActive) {
      if (this.browserARTiger) {
        const breath = Math.sin(time * 2.2) * 0.012;
        this.browserARTiger.scale.y = 0.7 + breath;
      }
      this.renderer.render(this.scene, this.camera);
      return;
    }

    let moveX = 0;
    let moveZ = 0;

    if (this.keys.forward) moveZ -= 1;
    if (this.keys.backward) moveZ += 1;
    if (this.keys.left) moveX -= 1;
    if (this.keys.right) moveX += 1;

    if (this.joystickVector && (Math.abs(this.joystickVector.x) > 0.05 || Math.abs(this.joystickVector.y) > 0.05)) {
      moveX += this.joystickVector.x;
      moveZ += this.joystickVector.y;
    }

    const moveLen = Math.sqrt(moveX * moveX + moveZ * moveZ);
    const isMoving = moveLen > 0.1;

    if (isMoving) {
      const normalizedX = moveX / Math.max(1.0, moveLen);
      const normalizedZ = moveZ / Math.max(1.0, moveLen);
      const actualSpeed = this.player.speed * (this.keys.sprint ? this.player.sprintMultiplier : 1.0);

      // Camera forward and right vectors based on yaw
      // Forward: (-sin(yaw), -cos(yaw)), Right: (cos(yaw), -sin(yaw))
      const fwdX = -Math.sin(this.player.yaw);
      const fwdZ = -Math.cos(this.player.yaw);
      const rgtX = Math.cos(this.player.yaw);
      const rgtZ = -Math.sin(this.player.yaw);

      // Move forward with -normalizedZ, move right with +normalizedX
      const worldDX = (-normalizedZ * fwdX + normalizedX * rgtX) * actualSpeed * delta;
      const worldDZ = (-normalizedZ * fwdZ + normalizedX * rgtZ) * actualSpeed * delta;

      this.player.position.x += worldDX;
      this.player.position.z += worldDZ;

      this.player.position.x = Math.max(-165, Math.min(165, this.player.position.x));
      this.player.position.z = Math.max(-165, Math.min(165, this.player.position.z));

      this.player.headBobTimer += delta * (this.keys.sprint ? 14 : 9);
      if (Math.sin(this.player.headBobTimer) > 0.95) {
        this.playStepSound();
      }
    }

    const groundY = this.getTerrainHeight(this.player.position.x, this.player.position.z);
    const headBobY = isMoving ? Math.sin(this.player.headBobTimer) * 0.07 : 0;
    this.player.position.y = groundY + this.player.height + headBobY;

    // Smooth camera turning via keyboard Arrow Keys (or Q)
    if (this.keys.turnLeft) {
      this.player.yaw += 2.0 * delta;
    }
    if (this.keys.turnRight) {
      this.player.yaw -= 2.0 * delta;
    }

    this.camera.position.copy(this.player.position);
    this.camera.rotation.set(0, 0, 0);
    this.camera.rotation.y = this.player.yaw;
    this.camera.rotation.x = this.player.pitch;

    // Animate creatures
    this.animatedCreatures.forEach(item => {
      if (item.update) item.update(time);
    });

    if (this.particleSystem) {
      this.particleSystem.rotation.y = time * 0.02;
    }

    // Slowly drift daytime clouds across the sky
    if (this.skyMesh) {
      this.skyMesh.rotation.y += delta * 0.003;
    }

    this.updateCompass();
    this.updateRaycasting();

    this.renderer.render(this.scene, this.camera);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  window.world = new ForestWorld();
});
